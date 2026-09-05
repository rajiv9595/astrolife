"""
Phase 6C — RulePackage abstraction.

A RulePackage is a deterministic, serializable container that binds:
  - a DynamicRuleDefinition (the rule declaration)
  - test fixtures (RuleTestCase entries)
  - source references and provenance
  - validation and test reports
  - lifecycle state and version
  - activation metadata

Serialisation is canonical JSON: sorted keys, compact separators, no
timestamps, no random IDs, no machine-specific paths. Two identical
packages produce identical fingerprints.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

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
from .lifecycle import (
    LIFECYCLE_STATES,
    LifecycleTransitionError,
    is_valid_transition,
    validate_transition,
)
from .validators import Diagnostic, validate_rule


class TestOutcome(BaseModel):
    test_id: str
    outcome: str  # "PASS" | "FAIL" | "SKIP"
    final_rule_state: str
    diagnostics: List[str] = Field(default_factory=list)


class RuleTestCase(BaseModel):
    """A declarative test case for a RulePackage.

    No executable Python inside fixtures. All data is declarative.
    """
    test_id: str
    description: str
    input_fixture: Dict[str, Any]
    expected_formation: str  # "FORMED" | "NOT_FORMED" | "UNKNOWN"
    expected_cancellation: str = "NOT_CANCELLED"  # "CANCELLED" | "NOT_CANCELLED" | "UNKNOWN"
    expected_mitigation: str = "NOT_MITIGATED"    # "MITIGATED" | "NOT_MITIGATED" | "UNKNOWN"
    expected_final_state: str = "FORMED"          # "FORMED" | "NOT_FORMED" | "UNKNOWN" | "CANCELLED" | "INVALID"
    expected_unknown_invalid: Optional[str] = None  # "UNKNOWN" | "INVALID" | None
    expected_evidence: Optional[List[str]] = None
    expected_dependencies: Optional[List[str]] = None
    is_golden: bool = False

    model_config = {"frozen": True}


class RuleTestReport(BaseModel):
    """Result of running tests in a RulePackage."""
    total: int
    passed: int
    failed: int
    skipped: int
    diagnostics: List[str] = Field(default_factory=list)
    execution_fingerprint: str

    model_config = {"frozen": True}


class ValidationReport(BaseModel):
    """Structured diagnostics from validate_rule_package()."""
    errors: List[Diagnostic] = Field(default_factory=list)
    warnings: List[Diagnostic] = Field(default_factory=list)
    info: List[Diagnostic] = Field(default_factory=list)

    model_config = {"frozen": True}

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


class ActivationReport(BaseModel):
    """Result of activate_rule()."""
    activated: bool
    rule_id: str
    version: str
    activation_reason: str
    deterministic_record: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


class PackageFingerprint(BaseModel):
    """Deterministic fingerprint of a RulePackage."""
    fingerprint: str

    model_config = {"frozen": True}


class RuleHealth(BaseModel):
    """Structured health and status summary for a dynamic rule."""
    schema_valid: bool
    provenance_valid: bool
    dependencies_valid: bool
    security_valid: bool
    tests_passed: bool
    regression_status: str  # "STABLE" | "REGRESSION" | "NO_BASELINE"
    lifecycle_status: str   # "DRAFT" | "VALIDATED" | "ACTIVE" etc.
    activation_status: str  # "ACTIVE" | "INACTIVE"

    model_config = {"frozen": True}


class RuleDiffCategory:
    ADDED_CONDITION = "ADDED_CONDITION"
    REMOVED_CONDITION = "REMOVED_CONDITION"
    CHANGED_CONDITION = "CHANGED_CONDITION"
    ADDED_DEPENDENCY = "ADDED_DEPENDENCY"
    REMOVED_DEPENDENCY = "REMOVED_DEPENDENCY"
    CHANGED_PROVENANCE = "CHANGED_PROVENANCE"
    CHANGED_TRADITION = "CHANGED_TRADITION"
    CHANGED_CANCELLATION = "CHANGED_CANCELLATION"
    CHANGED_MITIGATION = "CHANGED_MITIGATION"
    CHANGED_METADATA = "CHANGED_METADATA"

    ALL_CATEGORIES: List[str] = [
        ADDED_CONDITION,
        REMOVED_CONDITION,
        CHANGED_CONDITION,
        ADDED_DEPENDENCY,
        REMOVED_DEPENDENCY,
        CHANGED_PROVENANCE,
        CHANGED_TRADITION,
        CHANGED_CANCELLATION,
        CHANGED_MITIGATION,
        CHANGED_METADATA,
    ]


class RuleDiff(BaseModel):
    """Structured semantic diff between two rule versions."""
    categories: Dict[str, List[str]] = Field(default_factory=lambda: {
        cat: [] for cat in RuleDiffCategory.ALL_CATEGORIES
    })
    base_version: str
    target_version: str
    base_rule_id: str
    target_rule_id: str

    model_config = {"frozen": True}


class RulePackage(BaseModel):
    """A deterministic, serializable rule package.

    Contains everything needed for the full lifecycle: rule definition,
    test fixtures, reports, metadata. Instances are frozen/immutable after
    creation; state changes go through explicit transitions.
    """

    rule_id: str
    version: str
    name: str
    description: str
    tradition: str
    category: str
    provenance: RuleProvenance
    semantics: RuleSemantics
    dependencies: RuleDependencies
    evidence: RuleEvidenceSpec = Field(default_factory=RuleEvidenceSpec)
    lifecycle: RuleLifecycle = Field(default_factory=RuleLifecycle)
    validation: RuleValidationInfo = Field(default_factory=RuleValidationInfo)
    test_cases: List[RuleTestCase] = Field(default_factory=list)
    validation_report: Optional[ValidationReport] = None
    test_report: Optional[RuleTestReport] = None
    activation_metadata: Optional[ActivationReport] = None

    model_config = {"frozen": True}

    @property
    def rule(self) -> DynamicRuleDefinition:
        """Derive the canonical DynamicRuleDefinition from this package."""
        return self.to_rule_definition()

    def to_rule_definition(self) -> DynamicRuleDefinition:
        """Convert this package to a DynamicRuleDefinition."""
        return DynamicRuleDefinition(
            identity=RuleIdentity(
                rule_id=self.rule_id,
                rule_version=self.version,
                rule_name=self.name,
                description=self.description,
            ),
            classification=RuleClassification(
                system=self.tradition,
                tradition=self.tradition,
                category=self.category,
                subcategory="",
            ),
            provenance=self.provenance,
            semantics=self.semantics,
            dependencies=self.dependencies,
            evidence=self.evidence,
            lifecycle=self.lifecycle,
            validation=self.validation,
            schema_version="6A/1.0.0",
        )

    @classmethod
    def from_rule_definition(
        cls,
        rule: DynamicRuleDefinition,
        test_cases: Optional[List[RuleTestCase]] = None,
        validation_report: Optional[ValidationReport] = None,
        test_report: Optional[RuleTestReport] = None,
        activation_metadata: Optional[ActivationReport] = None,
    ) -> "RulePackage":
        """Construct a RulePackage from a DynamicRuleDefinition."""
        return cls(
            rule_id=rule.identity.rule_id,
            version=rule.identity.rule_version,
            name=rule.identity.rule_name,
            description=rule.identity.description or "",
            tradition=rule.classification.tradition,
            category=rule.classification.category or "",
            provenance=rule.provenance,
            semantics=rule.semantics,
            dependencies=rule.dependencies,
            evidence=rule.evidence or RuleEvidenceSpec(),
            lifecycle=rule.lifecycle or RuleLifecycle(),
            validation=rule.validation or RuleValidationInfo(),
            test_cases=test_cases or [],
            validation_report=validation_report,
            test_report=test_report,
            activation_metadata=activation_metadata,
        )

    def fingerprint(self) -> str:
        """Deterministic fingerprint based on canonical semantic content.

        Excludes timestamps, random IDs, memory addresses, machine-specific paths.
        Same package → same fingerprint. Modified package → different fingerprint.
        """
        canonical = self.to_canonical_dict()
        s = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Produce a timestamp/random-free canonical dictionary for fingerprinting."""
        return {
            "rule_id": self.rule_id,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "tradition": self.tradition,
            "category": self.category,
            "provenance": {
                "source_reference": {
                    "source_id": self.provenance.source_reference.source_id,
                    "title": self.provenance.source_reference.title,
                    "author": self.provenance.source_reference.author,
                    "publication": self.provenance.source_reference.publication,
                    "locator": self.provenance.source_reference.locator,
                    "quotation": self.provenance.source_reference.quotation,
                    "verification_status": self.provenance.source_reference.verification_status,
                },
                "source_type": self.provenance.source_type,
                "source_author": self.provenance.source_author,
                "source_title": self.provenance.source_title,
                "source_locator": self.provenance.source_locator,
                "provenance_status": self.provenance.provenance_status,
                "confidence": self.provenance.confidence,
            },
            "semantics": {
                "prerequisites": self.semantics.prerequisites,
                "formation": self._canon_cond(self.semantics.formation),
                "cancellation": self._canon_cond(self.semantics.cancellation),
                "mitigation": self._canon_cond(self.semantics.mitigation),
                "derived_facts": sorted(self.semantics.derived_facts or []),
            },
            "dependencies": {
                "input_facts": sorted(self.dependencies.input_facts or []),
                "rule_dependencies": sorted(self.dependencies.rule_dependencies or []),
                "varga_dependencies": sorted(self.dependencies.varga_dependencies or []),
                "dasha_dependencies": sorted(self.dependencies.dasha_dependencies or []),
                "transit_dependencies": sorted(self.dependencies.transit_dependencies or []),
                "strength_dependencies": sorted(self.dependencies.strength_dependencies or []),
            },
            "evidence": {
                "evidence_requirements": sorted(self.evidence.evidence_requirements or []),
                "evidence_paths": sorted(self.evidence.evidence_paths or []),
            },
            "lifecycle": {
                "status": self.lifecycle.status,
                "effective_from": self.lifecycle.effective_from,
                "supersedes": self.lifecycle.supersedes,
                "deprecated_by": self.lifecycle.deprecated_by,
            },
            "validation": {
                "validation_status": self.validation.validation_status,
                "validation_notes": self.validation.validation_notes,
                "test_requirements": sorted(self.validation.test_requirements or []),
            },
        }

    def _canon_cond(self, node: Optional[ConditionNode]) -> Optional[Dict[str, Any]]:
        """Canonicalise a condition node (order-independent children)."""
        if node is None:
            return None
        children: List[Any] = []
        if node.children:
            children = sorted(
                [self._canon_cond(c) for c in node.children if c is not None],
                key=lambda x: json.dumps(x, sort_keys=True) if x else "",
            )
        return {
            "op": node.op,
            "params": dict(sorted(node.params.items())),
            "children": children,
            "n": node.n,
        }

    def with_test_case(self, test: RuleTestCase) -> "RulePackage":
        """Return a new RulePackage with the given test case added."""
        new_cases = list(self.test_cases) + [test]
        return self.model_copy(update={"test_cases": new_cases})

    def add_test_case(self, test: RuleTestCase) -> "RulePackage":
        """Backward-compatible alias for with_test_case."""
        return self.with_test_case(test)

    def validate(self, known_rule_ids: Optional[Set[str]] = None) -> ValidationReport:
        """Run validation workflow against this package."""
        rule_def = self.to_rule_definition()
        diags = validate_rule(rule_def, known_rule_ids=known_rule_ids or set())

        errors = sorted([d for d in diags if d.severity == "ERROR"], key=lambda d: (d.code, d.path, d.message))
        warnings = sorted([d for d in diags if d.severity == "WARNING"], key=lambda d: (d.code, d.path, d.message))
        info = sorted([d for d in diags if d.severity == "INFO"], key=lambda d: (d.code, d.path, d.message))

        return ValidationReport(errors=errors, warnings=warnings, info=info)

    def can_transition_to(self, to_state: str) -> bool:
        """Check whether current lifecycle state can transition to target."""
        return is_valid_transition(self.lifecycle.status, to_state)

    def transition_lifecycle(self, to_state: str) -> "RulePackage":
        """Return a new RulePackage with lifecycle transitioned to to_state."""
        if to_state not in LIFECYCLE_STATES:
            raise LifecycleTransitionError(f"Invalid lifecycle state: {to_state}")
        validate_transition(self.lifecycle.status, to_state)
        new_lifecycle = self.lifecycle.model_copy(update={"status": to_state})
        return self.model_copy(update={"lifecycle": new_lifecycle})


def create_rule_draft(
    rule_id: str,
    version: str,
    name: str,
    description: str,
    tradition: str,
    category: str,
    provenance: RuleProvenance,
    condition_tree: ConditionNode,
    dependencies: RuleDependencies,
    cancellation_tree: Optional[ConditionNode] = None,
    mitigation_tree: Optional[ConditionNode] = None,
    derived_facts: Optional[List[str]] = None,
    evidence: Optional[RuleEvidenceSpec] = None,
    test_cases: Optional[List[RuleTestCase]] = None,
) -> RulePackage:
    """Create a new rule package draft.

    Rejects incomplete drafts where mandatory schema fields are missing.
    Drafts are created in the DRAFT lifecycle state and cannot be evaluated
    as active production rules.
    """
    missing: List[str] = []
    if not rule_id or not rule_id.strip():
        missing.append("rule_id")
    if not version or not version.strip():
        missing.append("version")
    if not name or not name.strip():
        missing.append("name")
    if not description or not description.strip():
        missing.append("description")
    if not tradition or not tradition.strip():
        missing.append("tradition")
    if not category or not category.strip():
        missing.append("category")
    if provenance is None:
        missing.append("provenance")
    if condition_tree is None:
        missing.append("condition_tree")
    if dependencies is None:
        missing.append("dependencies")

    if missing:
        raise ValueError(
            f"Draft creation rejected: missing mandatory fields: {', '.join(missing)}"
        )

    semantics = RuleSemantics(
        formation=condition_tree,
        cancellation=cancellation_tree,
        mitigation=mitigation_tree,
        derived_facts=derived_facts or [],
    )

    lifecycle = RuleLifecycle(status="DRAFT")
    validation = RuleValidationInfo(validation_status="UNVALIDATED")

    return RulePackage(
        rule_id=rule_id.strip(),
        version=version.strip(),
        name=name.strip(),
        description=description.strip(),
        tradition=tradition.strip(),
        category=category.strip(),
        provenance=provenance,
        semantics=semantics,
        dependencies=dependencies,
        evidence=evidence or RuleEvidenceSpec(),
        lifecycle=lifecycle,
        validation=validation,
        test_cases=test_cases or [],
    )