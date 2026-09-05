"""
Phase 6C — Safe declarative import/export.

Export: RulePackage → canonical JSON
Import: JSON → RulePackage

Requirements:
  - schema validation before registration
  - security scan before parsing executable-like payloads
  - deterministic serialization
  - no executable content
  - no silent overwrite
  - Duplicate exact version: REJECT (unless explicit "identical package already exists" handling)
  - Different content with same rule_id/version: REJECT
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError

from .dsl import find_suspicious_text
from .fingerprint import compute_fingerprint, fingerprint_from_dict
from .registry import DynamicRuleRegistry
from .rule_package import (
    RulePackage,
    RuleTestCase,
    RuleTestReport,
    ValidationReport,
)
from .schema import (
    ConditionNode,
    DynamicRuleDefinition,
    RuleClassification,
    RuleDependencies,
    RuleEvidenceSpec,
    RuleIdentity,
    RuleLifecycle,
    RuleProvenance,
    RuleSemantics,
    RuleValidationInfo,
    SourceReference,
)
from .validators import Diagnostic, validate_rule


class ExportResult(BaseModel):
    """Result of exporting a RulePackage to canonical JSON."""
    json_payload: str
    fingerprint: str
    version: str
    rule_id: str

    model_config = {"frozen": True}

    @property
    def json(self) -> str:
        """Backward-compatible accessor for json string."""
        return self.json_payload


class ImportResult(BaseModel):
    """Result of importing RulePackage from JSON."""
    success: bool
    rule_package: Optional[RulePackage] = None
    errors: List[Diagnostic] = Field(default_factory=list)
    warnings: List[Diagnostic] = Field(default_factory=list)
    reject_reason: Optional[str] = None

    model_config = {"frozen": True}


def export_package(pkg: RulePackage) -> ExportResult:
    """Export a RulePackage to canonical JSON.

    Produces deterministic JSON with sorted keys, compact separators,
    no timestamps, no random IDs.
    """
    canonical_dict = pkg.to_canonical_dict()
    json_str = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
    fp = compute_fingerprint(pkg)
    return ExportResult(
        json_payload=json_str,
        fingerprint=fp,
        version=pkg.version,
        rule_id=pkg.rule_id,
    )


def import_package(
    json_str: str,
    existing_registry: Optional[DynamicRuleRegistry] = None,
    allow_identical: bool = False,
) -> ImportResult:
    """Import RulePackage from canonical JSON string.

    Validates schema before registration. Scans for security violations.
    Rejects duplicate versions unless explicit identical package handling applies.
    """
    try:
        data = json.loads(json_str)
    except Exception as e:
        return ImportResult(
            success=False,
            errors=[Diagnostic(code="SCHEMA", path="json", message=f"Invalid JSON syntax: {e}")],
            reject_reason="invalid_json",
        )

    # 1. Security scan
    raw_str = json.dumps(data)
    suspicious = find_suspicious_text(raw_str)
    if suspicious:
        diags = [
            Diagnostic(
                code="ARBITRARY_CODE",
                path="security",
                message=f"Suspicious payload pattern detected: {pat!r}",
            )
            for pat in suspicious
        ]
        return ImportResult(
            success=False,
            errors=diags,
            reject_reason="security_violation",
        )

    # 2. Reconstruct RulePackage
    try:
        if "identity" in data:
            # DynamicRuleDefinition shape
            rule_def = DynamicRuleDefinition.model_validate(data)
            pkg = RulePackage.from_rule_definition(rule_def)
        else:
            # RulePackage shape
            # Normalize semantics
            def _clean_node(d: Optional[Dict[str, Any]]) -> Optional[ConditionNode]:
                if not d:
                    return None
                raw_children = d.get("children") or []
                cleaned_children = [_clean_node(c) for c in raw_children if c]
                return ConditionNode(
                    op=d["op"],
                    params=d.get("params", {}),
                    children=[c for c in cleaned_children if c is not None],
                    n=d.get("n"),
                )

            semantics_dict = data.get("semantics", {})
            semantics = RuleSemantics(
                prerequisites=semantics_dict.get("prerequisites", []),
                formation=_clean_node(semantics_dict.get("formation")),
                cancellation=_clean_node(semantics_dict.get("cancellation")),
                mitigation=_clean_node(semantics_dict.get("mitigation")),
                derived_facts=semantics_dict.get("derived_facts", []),
            )

            prov_dict = data.get("provenance", {})
            src_dict = prov_dict.get("source_reference", {})
            provenance = RuleProvenance(
                source_reference=SourceReference.model_validate(src_dict) if src_dict else SourceReference(),
                source_type=prov_dict.get("source_type", "TRADITIONAL_TEXT"),
                source_author=prov_dict.get("source_author", ""),
                source_title=prov_dict.get("source_title", ""),
                source_locator=prov_dict.get("source_locator", ""),
                provenance_status=prov_dict.get("provenance_status", "UNVERIFIED"),
                confidence=prov_dict.get("confidence", "UNVERIFIED"),
            )

            deps_dict = data.get("dependencies", {})
            dependencies = RuleDependencies.model_validate(deps_dict)

            ev_dict = data.get("evidence", {})
            evidence = RuleEvidenceSpec.model_validate(ev_dict) if ev_dict else RuleEvidenceSpec()

            lc_dict = data.get("lifecycle", {})
            lifecycle = RuleLifecycle.model_validate(lc_dict) if lc_dict else RuleLifecycle(status="DRAFT")

            val_dict = data.get("validation", {})
            validation = RuleValidationInfo.model_validate(val_dict) if val_dict else RuleValidationInfo()

            test_cases = [RuleTestCase.model_validate(tc) for tc in data.get("test_cases", [])]

            pkg = RulePackage(
                rule_id=data["rule_id"],
                version=data["version"],
                name=data.get("name", data["rule_id"]),
                description=data.get("description", ""),
                tradition=data.get("tradition", "PARASHARI_CLASSICAL"),
                category=data.get("category", "UNCLASSIFIED"),
                provenance=provenance,
                semantics=semantics,
                dependencies=dependencies,
                evidence=evidence,
                lifecycle=lifecycle,
                validation=validation,
                test_cases=test_cases,
            )
    except Exception as e:
        return ImportResult(
            success=False,
            errors=[Diagnostic(code="SCHEMA", path="package", message=f"Failed to parse package: {e}")],
            reject_reason="schema_validation_failed",
        )

    # 3. Validate rule schema and DSL
    val_report = pkg.validate()
    if not val_report.is_valid:
        return ImportResult(
            success=False,
            errors=val_report.errors,
            warnings=val_report.warnings,
            reject_reason="validation_errors",
        )

    # 4. Check registry duplicates
    if existing_registry is not None:
        existing = existing_registry.get(pkg.rule_id, pkg.version)
        if existing is not None:
            existing_pkg = RulePackage.from_rule_definition(existing)
            same_fp = (existing_pkg.fingerprint() == pkg.fingerprint())
            if same_fp:
                if not allow_identical:
                    return ImportResult(
                        success=False,
                        errors=[
                            Diagnostic(
                                code="DUPLICATE",
                                path="identity.rule_version",
                                message=f"{pkg.rule_id}@{pkg.version} already registered with identical content.",
                            )
                        ],
                        reject_reason="duplicate_exact_version",
                    )
            else:
                return ImportResult(
                    success=False,
                    errors=[
                        Diagnostic(
                            code="DUPLICATE_CONFLICT",
                            path="identity.rule_version",
                            message=f"{pkg.rule_id}@{pkg.version} already exists with different content; mutation forbidden.",
                        )
                    ],
                    reject_reason="different_content_same_version",
                )

    return ImportResult(
        success=True,
        rule_package=pkg,
        warnings=val_report.warnings,
    )


export = export_package
import_ = import_package