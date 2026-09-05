"""
Phase 6E — Knowledge / Rule Catalogue + Cross-System Applicability Engine.

Machine-readable catalogue answering WHAT rules exist, WHICH version is
active, WHICH tradition/category, WHAT facts each requires, WHAT evidence
supports it, WHAT conflicts/supersessions exist, and WHETHER it is applicable
to a chart context (APPLICABLE / NOT_APPLICABLE / UNKNOWN / INVALID).

NOT prediction. NOT interpretation. NOT new astronomy. NOT new astrology.

Reuses (never duplicates): DynamicRuleRegistry, RulePackage,
DynamicRuleDefinition, CanonicalFactResolver (+ status strings),
EvidenceBundle, EvidenceGraph, DEPENDENCY_SPECS, SAME_PROPOSITION_PAIRS /
RuleConflict, lifecycle tables, provenance/verification, fingerprint/diff,
namespace matching, required_paths bindings, dsl suspicious-text scan.

Applicability determines eligibility to evaluate; it never determines whether
the astrology rule itself forms (FORMED / NOT_FORMED / UNKNOWN is the
evaluator's job and is never collapsed into applicability).
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .bindings import required_paths
from .context import DynamicEvaluationContext
from .dsl import find_suspicious_text
from .namespace import match_namespace
from .resolver import CanonicalFactResolver, RESOLVED
from .schema import ConditionNode, DynamicRuleDefinition

# ---------------------------------------------------------------------------
# Taxonomy (§4, §5)
# ---------------------------------------------------------------------------

RULE_SYSTEMS = (
    "PARASHARI",
    "JAIMINI",
    "DOSHA",
    "STRENGTH",
    "PANCHANGA",
    "DASHA",
    "TRANSIT",
    "VARGA",
    "DYNAMIC_CUSTOM",
)

# Canonical query traditions (§12). Legacy aliases accepted and normalized.
TRADITIONS = (
    "PARASHARI_CLASSICAL",
    "JAIMINI_CLASSICAL",
    "TRADITION_DEPENDENT",
    "MODERN_COMMON",
    "WESTERN",
    "CUSTOM_DEVELOPER",
)
TRADITION_ALIASES = {
    "JAIMINI": "JAIMINI_CLASSICAL",
    "CUSTOM": "CUSTOM_DEVELOPER",
    "PARASHARI": "PARASHARI_CLASSICAL",
}
QUERY_TRADITIONS = ("ALL",) + TRADITIONS

CATEGORIES = (
    "YOGA",
    "DOSHA",
    "STRENGTH",
    "DIGNITY",
    "HOUSE",
    "SIGN",
    "VARGA",
    "KARAKA",
    "ARUDHA",
    "RASHI_DRISHTI",
    "DASHA",
    "TRANSIT",
    "PANCHANGA",
    "TIMING",
    "CUSTOM",
)

# Legacy RuleCategory -> 6E category mapping (existing enums reused, §4).
LEGACY_CATEGORY_MAP = {
    "YOGA": "YOGA",
    "DOSHA": "DOSHA",
    "STRENGTH": "STRENGTH",
    "DIGNITY": "DIGNITY",
    "HOUSE": "HOUSE",
    "LORDSHIP": "HOUSE",
    "ASPECT": "RASHI_DRISHTI",
    "TIMING": "TIMING",
    "CUSTOM": "CUSTOM",
    "JAIMINI": "KARAKA",  # refined by rule-id prefix below
    "TEST": "CUSTOM",
    "FIXTURE": "CUSTOM",
}

JAIMINI_CATEGORY_BY_PREFIX = (
    ("JAI.KARAKA.", "KARAKA"),
    ("JAI.DRISHTI.", "RASHI_DRISHTI"),
    ("JAI.ARUDHA.", "ARUDHA"),
    ("JAI.KARAKAMSHA.", "KARAKA"),
    ("JAI.SWAMSA.", "ARUDHA"),
)

VERIFICATION_STATES = (
    "VERIFIED",
    "UNVERIFIED",
    "CONTESTED",
    "SECONDARY",
    "TRADITIONAL",
    "USER_SUPPLIED",
    "CUSTOM",
)

# Chara Dasha profile methods usable as profile_constraints (§13).
JAIMINI_PROFILES = (
    "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL",
    "CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED",
    "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS",
)

# Applicability states (§7) and reasons (§8).
APPLICABLE, NOT_APPLICABLE, UNKNOWN, INVALID = (
    "APPLICABLE",
    "NOT_APPLICABLE",
    "UNKNOWN",
    "INVALID",
)

REASONS = (
    "MISSING_FACT",
    "MISSING_VARGA",
    "MISSING_DASHA",
    "MISSING_TRANSIT",
    "MISSING_STRENGTH",
    "MISSING_JAIMINI",
    "TRADITION_MISMATCH",
    "PROFILE_MISMATCH",
    "RULE_DISABLED",
    "RULE_DEPRECATED",
    "DEPENDENCY_INVALID",
    "DEPENDENCY_CONFLICT",
    "CONDITION_FALSE",
    "CONDITION_TRUE",
    "INVALID_RULE",
)

DISCOVERY_MODES = (
    "ACTIVE_ONLY",
    "ALL_VALIDATED",
    "ALL",
    "TRADITION_ONLY",
    "CATEGORY_ONLY",
    "PROFILE_ONLY",
)

ACTIVE_LIFECYCLES = ("ACTIVE", "ENABLED")
RETIRED_LIFECYCLES = ("DEPRECATED", "SUPERSEDED", "ARCHIVED", "REJECTED")


def normalize_tradition(value: str) -> str:
    """Map legacy aliases (JAIMINI, CUSTOM, PARASHARI) to canonical names."""
    v = (value or "").strip()
    return TRADITION_ALIASES.get(v, v)


def normalize_system(value: str) -> str:
    v = (value or "").strip()
    if v in RULE_SYSTEMS:
        return v
    alias = {"CUSTOM": "DYNAMIC_CUSTOM", "PARASHARI_CLASSICAL": "PARASHARI",
             "JAIMINI_CLASSICAL": "JAIMINI", "JAIMINI": "JAIMINI"}
    return alias.get(v, "DYNAMIC_CUSTOM")


def normalize_category(rule_id: str, value: str) -> str:
    v = (value or "").strip().upper()
    if v == "JAIMINI" or rule_id.startswith("JAI."):
        for prefix, cat in JAIMINI_CATEGORY_BY_PREFIX:
            if rule_id.startswith(prefix):
                return cat
        return "KARAKA"
    if v in CATEGORIES:
        return v
    return LEGACY_CATEGORY_MAP.get(v, "CUSTOM")


# ---------------------------------------------------------------------------
# Applicability spec (§6)
# ---------------------------------------------------------------------------

class RuleApplicabilitySpec(BaseModel):
    """Declares everything a rule needs before it may be evaluated."""

    required_facts: List[str] = Field(default_factory=list)
    optional_facts: List[str] = Field(default_factory=list)
    required_vargas: List[str] = Field(default_factory=list)
    required_dasha_systems: List[str] = Field(default_factory=list)
    required_transit_data: List[str] = Field(default_factory=list)
    required_strength_data: List[str] = Field(default_factory=list)
    required_jaimini_data: List[str] = Field(default_factory=list)
    required_rule_results: List[str] = Field(default_factory=list)
    tradition_constraints: List[str] = Field(default_factory=list)
    profile_constraints: List[str] = Field(default_factory=list)
    applicability_condition: Optional[ConditionNode] = Field(default=None)

    model_config = {"frozen": True}

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "required_facts": sorted(self.required_facts),
            "optional_facts": sorted(self.optional_facts),
            "required_vargas": sorted(self.required_vargas),
            "required_dasha_systems": sorted(self.required_dasha_systems),
            "required_transit_data": sorted(self.required_transit_data),
            "required_strength_data": sorted(self.required_strength_data),
            "required_jaimini_data": sorted(self.required_jaimini_data),
            "required_rule_results": sorted(self.required_rule_results),
            "tradition_constraints": sorted(self.tradition_constraints),
            "profile_constraints": sorted(self.profile_constraints),
        }


def _tree_paths(node: Optional[ConditionNode]) -> List[str]:
    if node is None:
        return []
    out: List[str] = list(required_paths(node.op, node.params))
    for child in node.children or []:
        out.extend(_tree_paths(child))
    return out


def derive_spec_from_definition(
    rule: DynamicRuleDefinition,
    tradition_constraints: Optional[List[str]] = None,
    profile_constraints: Optional[List[str]] = None,
    applicability_condition: Optional[ConditionNode] = None,
) -> RuleApplicabilitySpec:
    """Derive an applicability spec from a dynamic rule's condition trees.

    Needed fact paths come from the primitive bindings (the same source the
    6B engine uses), so declared dependencies and applicability never drift.
    """
    needed = sorted(set(
        _tree_paths(rule.semantics.formation)
        + _tree_paths(rule.semantics.cancellation)
        + _tree_paths(rule.semantics.mitigation)
    ))
    facts = sorted(p for p in needed if not p.startswith("rule:"))
    rule_results = sorted(
        set(rule.dependencies.rule_dependencies or [])
        | {p[len("rule:"):] for p in needed if p.startswith("rule:")}
    )
    vargas = sorted({p.split(".")[1] for p in facts if p.startswith("varga.")})
    dasha = sorted({p.split(".")[1] for p in facts if p.startswith("dasha.")})
    transit = sorted({p for p in facts if p.startswith("transit.")})
    strength = sorted({p for p in facts if p.startswith("strength.")})
    jaimini = sorted({p for p in facts if p.startswith("jaimini.")})
    return RuleApplicabilitySpec(
        required_facts=facts,
        required_vargas=vargas or sorted(set(rule.dependencies.varga_dependencies or [])),
        required_dasha_systems=dasha or sorted(set(rule.dependencies.dasha_dependencies or [])),
        required_transit_data=transit,
        required_strength_data=strength,
        required_jaimini_data=jaimini,
        required_rule_results=rule_results,
        tradition_constraints=list(tradition_constraints or []),
        profile_constraints=list(profile_constraints or []),
        applicability_condition=applicability_condition,
    )


# ---------------------------------------------------------------------------
# Catalogue entry (§3)
# ---------------------------------------------------------------------------

class RuleKnowledgeEntry(BaseModel):
    rule_id: str
    rule_version: str
    name: str = ""
    description: str = ""
    system: str = "DYNAMIC_CUSTOM"
    tradition: str = "CUSTOM_DEVELOPER"
    category: str = "CUSTOM"
    subcategory: str = ""
    lifecycle_status: str = "DRAFT"
    validation_status: str = "UNVALIDATED"
    provenance_status: str = ""
    source_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    dependency_manifest: Dict[str, List[str]] = Field(default_factory=dict)
    fingerprint: str = ""
    supersedes: str = ""
    superseded_by: str = ""
    conflicts: List[str] = Field(default_factory=list)
    applicability_spec: RuleApplicabilitySpec = Field(default_factory=RuleApplicabilitySpec)

    model_config = {"frozen": True}

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "name": self.name,
            "description": self.description,
            "system": self.system,
            "tradition": self.tradition,
            "category": self.category,
            "subcategory": self.subcategory,
            "lifecycle_status": self.lifecycle_status,
            "validation_status": self.validation_status,
            "provenance_status": self.provenance_status,
            "source_ids": sorted(self.source_ids),
            "evidence_ids": sorted(self.evidence_ids),
            "dependency_manifest": {k: sorted(v) for k, v in sorted(self.dependency_manifest.items())},
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
            "conflicts": sorted(self.conflicts),
            "applicability_spec": self.applicability_spec.to_canonical_dict(),
        }

    def compute_fingerprint(self) -> str:
        s = json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    # Evidence-aware visibility (§18): counts only, never a score.
    @property
    def source_count(self) -> int:
        return len(self.source_ids)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_ids)

    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)


def _manifest_for_dynamic(rule: DynamicRuleDefinition) -> Dict[str, List[str]]:
    return {
        "input_facts": sorted(set(rule.dependencies.input_facts or [])),
        "rule_dependencies": sorted(set(rule.dependencies.rule_dependencies or [])),
        "varga_dependencies": sorted(set(rule.dependencies.varga_dependencies or [])),
        "dasha_dependencies": sorted(set(rule.dependencies.dasha_dependencies or [])),
        "transit_dependencies": sorted(set(rule.dependencies.transit_dependencies or [])),
        "strength_dependencies": sorted(set(rule.dependencies.strength_dependencies or [])),
    }


def entry_from_dynamic_definition(
    rule: DynamicRuleDefinition,
    system: Optional[str] = None,
    conflicts: Optional[List[str]] = None,
    tradition_constraints: Optional[List[str]] = None,
    profile_constraints: Optional[List[str]] = None,
    applicability_condition: Optional[ConditionNode] = None,
) -> RuleKnowledgeEntry:
    tradition = normalize_tradition(rule.classification.tradition)
    entry = RuleKnowledgeEntry(
        rule_id=rule.identity.rule_id,
        rule_version=rule.identity.rule_version,
        name=rule.identity.rule_name,
        description=rule.identity.description or "",
        system=normalize_system(system or rule.classification.system),
        tradition=tradition,
        category=normalize_category(rule.identity.rule_id, rule.classification.category),
        subcategory=rule.classification.subcategory or "",
        lifecycle_status=rule.lifecycle.status,
        validation_status=rule.validation.validation_status,
        provenance_status=rule.provenance.provenance_status
        or rule.provenance.source_reference.verification_status,
        source_ids=[rule.provenance.source_reference.source_id]
        if rule.provenance.source_reference.source_id else [],
        evidence_ids=sorted(set(rule.evidence.evidence_requirements or [])
                            | set(rule.evidence.evidence_paths or [])),
        dependency_manifest=_manifest_for_dynamic(rule),
        supersedes=rule.lifecycle.supersedes or "",
        conflicts=sorted(conflicts or []),
        applicability_spec=derive_spec_from_definition(
            rule, tradition_constraints, profile_constraints, applicability_condition),
    )
    return entry.model_copy(update={"fingerprint": entry.compute_fingerprint()})


# ---------------------------------------------------------------------------
# Knowledge context + applicability result (§9)
# ---------------------------------------------------------------------------

class KnowledgeContext(BaseModel):
    """Chart data + the tradition/profile the caller queries under."""

    dynamic: DynamicEvaluationContext = Field(default_factory=DynamicEvaluationContext)
    tradition: str = "ALL"
    profile: str = ""

    model_config = {"arbitrary_types_allowed": True, "frozen": True}


class ApplicabilityReason(BaseModel):
    code: str
    detail: str = ""

    model_config = {"frozen": True}


class RuleApplicabilityResult(BaseModel):
    rule_id: str
    rule_version: str
    status: str
    reasons: List[ApplicabilityReason] = Field(default_factory=list)
    required_inputs: List[str] = Field(default_factory=list)
    resolved_inputs: Dict[str, Any] = Field(default_factory=dict)
    missing_inputs: List[str] = Field(default_factory=list)
    tradition: str = "ALL"
    profile: str = ""
    evidence: List[str] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    fingerprint: str = ""

    model_config = {"frozen": True}

    def reason_codes(self) -> List[str]:
        return sorted({r.code for r in self.reasons})


def classify_missing(path: str) -> str:
    """Map a missing fact path to its structured reason code."""
    if path.startswith("varga."):
        return "MISSING_VARGA"
    if path.startswith("dasha."):
        return "MISSING_DASHA"
    if path.startswith("transit."):
        return "MISSING_TRANSIT"
    if path.startswith("strength."):
        return "MISSING_STRENGTH"
    if path.startswith("jaimini."):
        return "MISSING_JAIMINI"
    return "MISSING_FACT"


# Jaimini catalogue-level requirements (§6 example) -> concrete resolver probes.
JAIMINI_PROBES = {
    "jaimini.rashi_drishti": ["jaimini.drishti"],
    "jaimini.karakamsha": ["jaimini.karakamsha"],
    "jaimini.swamsa": ["jaimini.swamsa"],
    "jaimini.AL": ["jaimini.pada.1"],
    "jaimini.A2": ["jaimini.pada.2"],
    "jaimini.A7": ["jaimini.pada.7"],
    "jaimini.A11": ["jaimini.pada.11"],
    "jaimini.UL": ["jaimini.pada.7"],  # UL shares pada machinery; object check below
}


def _resolve_probe(resolver: CanonicalFactResolver, path: str) -> Tuple[bool, Any, str]:
    res = resolver.resolve(path)
    if res.status == RESOLVED:
        return True, res.value, res.evidence_id
    return False, None, res.evidence_id


def _check_jaimini_requirement(
    resolver: CanonicalFactResolver, requirement: str, dynamic: DynamicEvaluationContext,
) -> Tuple[bool, List[str], Dict[str, Any], List[str]]:
    """Check one required_jaimini_data entry. Returns (ok, probes, resolved, missing)."""
    probes = JAIMINI_PROBES.get(requirement, [requirement])
    resolved: Dict[str, Any] = {}
    missing: List[str] = []
    evidence: List[str] = []
    for probe in probes:
        ok, value, ev_id = _resolve_probe(resolver, probe)
        if ok:
            resolved[requirement] = value
            evidence.append(ev_id)
        else:
            # UL / arudha object fallback: jaimini_facts present but resolver
            # has no UL path — inspect the canonical object directly.
            jf = dynamic.jaimini_facts
            if requirement == "jaimini.UL" and jf is not None and getattr(jf, "upapada", None) is not None:
                resolved[requirement] = str(getattr(jf, "upapada"))
            else:
                missing.append(requirement)
    if requirement in resolved:
        missing = [m for m in missing if m != requirement]
        return True, probes, resolved, []
    return False, probes, {}, sorted(set(missing) or {requirement})


def _check_varga(
    resolver: CanonicalFactResolver, varga: str,
) -> Tuple[bool, Dict[str, Any], List[str]]:
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        ok, value, _ = _resolve_probe(resolver, f"varga.{varga}.{planet}")
        if ok:
            return True, {f"varga.{varga}.{planet}": value}, []
    return False, {}, [f"varga.{varga}"]


def _check_dasha_system(
    resolver: CanonicalFactResolver, system: str,
) -> Tuple[bool, Dict[str, Any], List[str]]:
    ok, value, _ = _resolve_probe(resolver, f"dasha.{system}.active_sign")
    if ok:
        return True, {f"dasha.{system}.active_sign": value}, []
    return False, {}, [f"dasha.{system}.active_sign"]


def evaluate_rule_applicability(
    entry: RuleKnowledgeEntry,
    context: KnowledgeContext,
    catalogue: Optional["RuleKnowledgeCatalogue"] = None,
) -> RuleApplicabilityResult:
    """Determine eligibility to evaluate. Never determines formation. (§9, §10).

    Order: INVALID (broken rule) -> NOT_APPLICABLE (lifecycle / tradition /
    profile / false condition) -> UNKNOWN (missing info) -> APPLICABLE.
    UNKNOWN is never converted into NOT_APPLICABLE.
    """
    from .validators import validate_rule as _validate_rule  # local: reuse, no dup

    spec = entry.applicability_spec
    reasons: List[ApplicabilityReason] = []
    resolved: Dict[str, Any] = {}
    missing: List[str] = []
    evidence_ids: List[str] = []

    required_inputs = sorted(
        set(spec.required_facts)
        | set(spec.required_rule_results)
        | set(spec.required_transit_data)
        | set(spec.required_strength_data)
        | set(spec.required_jaimini_data)
        | {f"varga.{v}" for v in spec.required_vargas}
        | {f"dasha.{d}" for d in spec.required_dasha_systems}
    )

    # 0. Identity validity (rule/version identity preserved, §20).
    import re as _re
    if not _re.match(r"^[A-Z0-9_]+(\.[A-Z0-9_]+)+$", entry.rule_id or ""):
        reasons.append(ApplicabilityReason(code="INVALID_RULE",
                                           detail=f"malformed rule_id {entry.rule_id!r}"))
    if not _re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$", entry.rule_version or ""):
        reasons.append(ApplicabilityReason(code="INVALID_RULE",
                                           detail=f"malformed version {entry.rule_version!r}"))
    if reasons:
        return RuleApplicabilityResult(
            rule_id=entry.rule_id, rule_version=entry.rule_version, status=INVALID,
            reasons=sorted(reasons, key=lambda r: (r.code, r.detail)),
            required_inputs=required_inputs, resolved_inputs={}, missing_inputs=[],
            tradition=context.tradition, profile=context.profile, evidence=[],
            dependencies={k: sorted(v) for k, v in sorted((entry.dependency_manifest or {}).items())},
            fingerprint=entry.fingerprint)

    # 1. Rule validity. Rebuild a minimal definition for the shared validator
    #    when the entry carries dynamic dependency metadata.
    manifest = entry.dependency_manifest
    if manifest:
        from .schema import (RuleClassification, RuleDependencies, RuleIdentity,
                             RuleLifecycle, RuleProvenance, RuleSemantics,
                             RuleValidationInfo, SourceReference)
        probe = DynamicRuleDefinition(
            identity=RuleIdentity(rule_id=entry.rule_id, rule_version=entry.rule_version,
                                  rule_name=entry.name or entry.rule_id,
                                  description=entry.description or "6E catalogue probe"),
            classification=RuleClassification(system=entry.system, tradition=entry.tradition,
                                              category=entry.category or "CUSTOM"),
            provenance=RuleProvenance(
                source_reference=SourceReference(
                    source_id=entry.source_ids[0] if entry.source_ids else "6E-PROBE",
                    verification_status="UNVERIFIED"),
                confidence="CUSTOM"),
            semantics=RuleSemantics(),
            dependencies=RuleDependencies(
                input_facts=list(manifest.get("input_facts", [])),
                rule_dependencies=list(manifest.get("rule_dependencies", [])),
                varga_dependencies=list(manifest.get("varga_dependencies", [])),
                dasha_dependencies=list(manifest.get("dasha_dependencies", [])),
                transit_dependencies=list(manifest.get("transit_dependencies", [])),
                strength_dependencies=list(manifest.get("strength_dependencies", []))),
            lifecycle=RuleLifecycle(status="ACTIVE"
                                    if entry.lifecycle_status in ACTIVE_LIFECYCLES else "DRAFT"),
            validation=RuleValidationInfo(validation_status="VALID"),
        )
        diags = [d for d in _validate_rule(
            probe, set(catalogue.rule_ids() if catalogue is not None else set())
            | {entry.rule_id}) if d.severity == "ERROR" and d.code != "CONDITION"]
        # Drop "rule must exist" complaints about the entry itself; anything
        # else (bad rule deps, firewall breach, bad id/version) is INVALID.
        real = [d for d in diags
                if not (d.code == "DEPENDENCY" and entry.rule_id in d.message)]
        if real:
            for d in real:
                code = "DEPENDENCY_INVALID" if d.code in ("DEPENDENCY", "CYCLE", "FIREWALL") else "INVALID_RULE"
                reasons.append(ApplicabilityReason(code=code, detail=f"{d.code}:{d.path}:{d.message}"))
            if not any(r.code == "INVALID_RULE" for r in reasons):
                reasons.append(ApplicabilityReason(code="INVALID_RULE",
                                                   detail="dependency metadata invalid"))
            return RuleApplicabilityResult(
                rule_id=entry.rule_id, rule_version=entry.rule_version, status=INVALID,
                reasons=sorted(reasons, key=lambda r: (r.code, r.detail)),
                required_inputs=required_inputs, resolved_inputs={}, missing_inputs=[],
                tradition=context.tradition, profile=context.profile, evidence=[],
                dependencies={k: sorted(v) for k, v in sorted(manifest.items())},
                fingerprint=entry.fingerprint)
    # Unknown rule-dependency targets are INVALID even without a manifest probe.
    if catalogue is not None:
        unknown_deps = sorted(d for d in spec.required_rule_results if not catalogue.has_rule(d))
        if unknown_deps:
            reasons.append(ApplicabilityReason(code="DEPENDENCY_INVALID",
                                               detail=f"unknown rule dependencies: {unknown_deps}"))
            reasons.append(ApplicabilityReason(code="INVALID_RULE",
                                               detail="dependency itself is invalid"))
            return RuleApplicabilityResult(
                rule_id=entry.rule_id, rule_version=entry.rule_version, status=INVALID,
                reasons=sorted(reasons, key=lambda r: (r.code, r.detail)),
                required_inputs=required_inputs, resolved_inputs={}, missing_inputs=[],
                tradition=context.tradition, profile=context.profile, evidence=[],
                dependencies={k: sorted(v) for k, v in sorted(manifest.items())},
                fingerprint=entry.fingerprint)

    # 2. Lifecycle gates (NOT_APPLICABLE, never INVALID).
    if entry.lifecycle_status == "DISABLED":
        reasons.append(ApplicabilityReason(code="RULE_DISABLED", detail=entry.lifecycle_status))
        return _verdict(entry, context, NOT_APPLICABLE, reasons, required_inputs,
                        resolved, missing, evidence_ids, manifest)
    if entry.lifecycle_status in RETIRED_LIFECYCLES:
        reasons.append(ApplicabilityReason(code="RULE_DEPRECATED", detail=entry.lifecycle_status))
        return _verdict(entry, context, NOT_APPLICABLE, reasons, required_inputs,
                        resolved, missing, evidence_ids, manifest)
    if entry.lifecycle_status not in ACTIVE_LIFECYCLES:
        reasons.append(ApplicabilityReason(code="RULE_DISABLED",
                                           detail=f"lifecycle {entry.lifecycle_status} is not active"))
        return _verdict(entry, context, NOT_APPLICABLE, reasons, required_inputs,
                        resolved, missing, evidence_ids, manifest)

    # 3. Tradition isolation (§12): a JAIMINI query never silently matches Parashari.
    if context.tradition != "ALL":
        allowed = [normalize_tradition(t) for t in (spec.tradition_constraints or [entry.tradition])]
        if normalize_tradition(context.tradition) not in allowed:
            reasons.append(ApplicabilityReason(
                code="TRADITION_MISMATCH",
                detail=f"rule tradition {entry.tradition} not in query {context.tradition}"))
            return _verdict(entry, context, NOT_APPLICABLE, reasons, required_inputs,
                            resolved, missing, evidence_ids, manifest)

    # 4. Profile isolation (§13).
    if spec.profile_constraints and context.profile not in spec.profile_constraints:
        reasons.append(ApplicabilityReason(
            code="PROFILE_MISMATCH",
            detail=f"profile {context.profile!r} not in {sorted(spec.profile_constraints)}"))
        return _verdict(entry, context, NOT_APPLICABLE, reasons, required_inputs,
                        resolved, missing, evidence_ids, manifest)

    # 5. Prerequisite resolution via the canonical resolver.
    dynamic = context.dynamic
    resolver = CanonicalFactResolver(dynamic)
    for path in sorted(set(spec.required_facts) | set(spec.required_transit_data)
                       | set(spec.required_strength_data)):
        ok, value, ev_id = _resolve_probe(resolver, path)
        if ok:
            resolved[path] = value
            evidence_ids.append(ev_id)
        else:
            missing.append(path)
            reasons.append(ApplicabilityReason(code=classify_missing(path),
                                               detail=f"unresolved: {path}"))
    for varga in sorted(spec.required_vargas):
        ok, vals, miss = _check_varga(resolver, varga)
        if ok:
            resolved.update(vals)
        else:
            missing.extend(miss)
            reasons.append(ApplicabilityReason(code="MISSING_VARGA",
                                               detail=f"varga {varga} unavailable"))
    for system in sorted(spec.required_dasha_systems):
        ok, vals, miss = _check_dasha_system(resolver, system)
        if ok:
            resolved.update(vals)
        else:
            missing.extend(miss)
            reasons.append(ApplicabilityReason(code="MISSING_DASHA",
                                               detail=f"dasha system {system} unavailable"))
    for requirement in sorted(spec.required_jaimini_data):
        ok, _, res_map, miss = _check_jaimini_requirement(resolver, requirement, dynamic)
        if ok:
            resolved.update(res_map)
        else:
            missing.extend(miss)
            reasons.append(ApplicabilityReason(code="MISSING_JAIMINI",
                                               detail=f"unresolved: {requirement}"))
    for dep in sorted(spec.required_rule_results):
        outcome = (dynamic.rule_outcomes or {}).get(dep)
        if outcome is None:
            missing.append(f"rule:{dep}")
            reasons.append(ApplicabilityReason(code="DEPENDENCY_INVALID",
                                               detail=f"rule result unavailable: {dep}"))
        else:
            resolved[f"rule:{dep}"] = outcome

    if missing:
        # UNKNOWN: required information missing. Never NOT_APPLICABLE. (§7)
        return _verdict(entry, context, UNKNOWN, reasons, required_inputs,
                        resolved, sorted(set(missing)), sorted(set(evidence_ids)), manifest)

    # 6. Explicit applicability condition (availability-level only, never formation).
    if spec.applicability_condition is not None:
        from .evaluator import MISSING as _SENTINEL
        from .evaluator import evaluate_tree

        def bridge(path: str) -> Any:
            res = resolver.resolve(path)
            if res.status != RESOLVED:
                return _SENTINEL
            return res.value

        tree_outcome = evaluate_tree(spec.applicability_condition, bridge, "applicability")
        if tree_outcome.outcome == "FALSE":
            reasons.append(ApplicabilityReason(code="CONDITION_FALSE",
                                               detail="applicability condition false"))
            return _verdict(entry, context, NOT_APPLICABLE, reasons, required_inputs,
                            resolved, [], sorted(set(evidence_ids)), manifest)
        if tree_outcome.outcome == "UNKNOWN":
            reasons.append(ApplicabilityReason(code="MISSING_FACT",
                                               detail="applicability condition undecidable"))
            return _verdict(entry, context, UNKNOWN, reasons, required_inputs,
                            resolved, [], sorted(set(evidence_ids)), manifest)

    reasons.append(ApplicabilityReason(code="CONDITION_TRUE",
                                       detail="all prerequisites available"))
    return _verdict(entry, context, APPLICABLE, reasons, required_inputs,
                    resolved, [], sorted(set(evidence_ids)), manifest)


def _verdict(entry, context, status, reasons, required_inputs, resolved,
             missing, evidence_ids, manifest) -> RuleApplicabilityResult:
    return RuleApplicabilityResult(
        rule_id=entry.rule_id, rule_version=entry.rule_version, status=status,
        reasons=sorted(reasons, key=lambda r: (r.code, r.detail)),
        required_inputs=required_inputs, resolved_inputs=dict(sorted(resolved.items())),
        missing_inputs=sorted(set(missing)),
        tradition=context.tradition, profile=context.profile,
        evidence=evidence_ids,
        dependencies={k: sorted(v) for k, v in sorted((manifest or {}).items())},
        fingerprint=entry.fingerprint)


# ---------------------------------------------------------------------------
# Conflict record (§19)
# ---------------------------------------------------------------------------

class KnowledgeConflict(BaseModel):
    conflict_id: str
    rule_a: str
    rule_b: str
    tradition_a: str = ""
    tradition_b: str = ""
    version_a: str = ""
    version_b: str = ""
    conflict_type: str = "REPORTED_ONLY"
    status: str = "REPORTED_ONLY"

    model_config = {"frozen": True}


def _conflict_id(a: str, b: str) -> str:
    x, y = sorted((a, b))
    return "CONFLICT:" + hashlib.sha256(f"{x}|{y}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Unified catalogue (§3, §14–§17, §20–§22)
# ---------------------------------------------------------------------------

class RuleKnowledgeCatalogue(BaseModel):
    entries: Dict[str, RuleKnowledgeEntry] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True, "frozen": True}

    @staticmethod
    def _key(rule_id: str, version: str) -> str:
        return f"{rule_id}@{version}"

    def register(self, entry: RuleKnowledgeEntry) -> "RuleKnowledgeCatalogue":
        if not entry.fingerprint:
            entry = entry.model_copy(update={"fingerprint": entry.compute_fingerprint()})
        data = dict(self.entries)
        data[self._key(entry.rule_id, entry.rule_version)] = entry
        new = self.model_copy(update={"entries": data})
        object.__setattr__(new, "_rev_index_cache", None)
        return new

    def has_rule(self, rule_id: str) -> bool:
        return any(e.rule_id == rule_id for e in self.entries.values())

    def rule_ids(self) -> List[str]:
        return sorted({e.rule_id for e in self.entries.values()})

    def get_rule(self, rule_id: str, version: Optional[str] = None) -> Optional[RuleKnowledgeEntry]:
        """Exact version when given (§20). Without version, the latest ACTIVE
        version is returned explicitly (never silently substituted elsewhere)."""
        if version is not None:
            return self.entries.get(self._key(rule_id, version))
        cands = [e for e in self.entries.values() if e.rule_id == rule_id]
        active = [e for e in cands if e.lifecycle_status in ACTIVE_LIFECYCLES]
        pool = active or cands
        if not pool:
            return None
        return sorted(pool, key=lambda e: _version_tuple(e.rule_version))[-1]

    def get_rule_version(self, rule_id: str, version: str) -> Optional[RuleKnowledgeEntry]:
        return self.entries.get(self._key(rule_id, version))

    def list_versions(self, rule_id: str) -> List[str]:
        return sorted({e.rule_version for e in self.entries.values() if e.rule_id == rule_id},
                      key=_version_tuple)

    def latest_active_version(self, rule_id: str) -> Optional[str]:
        active = [e for e in self.entries.values()
                  if e.rule_id == rule_id and e.lifecycle_status in ACTIVE_LIFECYCLES]
        if not active:
            return None
        return sorted(active, key=lambda e: _version_tuple(e.rule_version))[-1].rule_version

    def list_all(self) -> List[RuleKnowledgeEntry]:
        return sorted(self.entries.values(),
                      key=lambda e: (e.tradition, e.system, e.category, e.rule_id, e.rule_version))

    # -- discovery ------------------------------------------------------
    def find_rules_for_context(
        self,
        context: KnowledgeContext,
        mode: str = "ACTIVE_ONLY",
        tradition: Optional[str] = None,
        category: Optional[str] = None,
        profile: Optional[str] = None,
    ) -> List[Tuple[RuleKnowledgeEntry, RuleApplicabilityResult]]:
        """Discovery with stable ordering (tradition, system, category, id, version)."""
        if mode not in DISCOVERY_MODES:
            raise ValueError(f"Unknown discovery mode {mode!r}; allowed {DISCOVERY_MODES}")
        entries = self.list_all()
        if mode == "ACTIVE_ONLY":
            entries = [e for e in entries
                       if e.lifecycle_status in ACTIVE_LIFECYCLES and e.validation_status == "VALID"]
        elif mode == "ALL_VALIDATED":
            entries = [e for e in entries if e.validation_status == "VALID"]
        elif mode == "TRADITION_ONLY":
            want = normalize_tradition(tradition or context.tradition)
            entries = [e for e in entries if e.tradition == want]
        elif mode == "CATEGORY_ONLY":
            entries = [e for e in entries if e.category == (category or "")]
        elif mode == "PROFILE_ONLY":
            want = profile if profile is not None else context.profile
            entries = [e for e in entries if want in (e.applicability_spec.profile_constraints or [])]
        # mode ALL: no lifecycle pre-filter; deprecated entries evaluate to
        # NOT_APPLICABLE via the evaluator (never exposed as ACTIVE).
        if tradition is not None and mode not in ("TRADITION_ONLY",):
            entries = [e for e in entries if e.tradition == normalize_tradition(tradition)]
        if category is not None and mode not in ("CATEGORY_ONLY",):
            entries = [e for e in entries if e.category == category]
        out = [(e, evaluate_rule_applicability(e, context, self)) for e in entries]
        out.sort(key=lambda pair: (pair[0].tradition, pair[0].system, pair[0].category,
                                   pair[0].rule_id, pair[0].rule_version))
        return out

    def find_rules(
        self,
        tradition: Optional[str] = None,
        category: Optional[str] = None,
        lifecycle_status: Optional[str] = None,
        validation_status: Optional[str] = None,
        source_id: Optional[str] = None,
        provenance_status: Optional[str] = None,
        verification_status: Optional[str] = None,
        system: Optional[str] = None,
    ) -> List[RuleKnowledgeEntry]:
        out = self.list_all()
        if tradition is not None:
            out = [e for e in out if e.tradition == normalize_tradition(tradition)]
        if category is not None:
            out = [e for e in out if e.category == category]
        if lifecycle_status is not None:
            out = [e for e in out if e.lifecycle_status == lifecycle_status]
        if validation_status is not None:
            out = [e for e in out if e.validation_status == validation_status]
        if source_id is not None:
            out = [e for e in out if source_id in e.source_ids]
        if provenance_status is not None:
            out = [e for e in out if e.provenance_status == provenance_status]
        if verification_status is not None:
            out = [e for e in out if e.provenance_status == verification_status]
        if system is not None:
            out = [e for e in out if e.system == system]
        return out

    # -- dependency-aware discovery (§16) + reverse index (§17) ---------
    def reverse_index(self) -> Dict[str, List[str]]:
        """fact -> rules (deterministic). Covers required facts and manifest inputs."""
        index: Dict[str, set] = {}
        for e in self.entries.values():
            facts = set(e.applicability_spec.required_facts)
            facts |= set(e.applicability_spec.required_transit_data)
            facts |= set(e.applicability_spec.required_strength_data)
            facts |= set(e.applicability_spec.required_jaimini_data)
            facts |= set((e.dependency_manifest or {}).get("input_facts", []))
            for fact in facts:
                index.setdefault(fact, set()).add(f"{e.rule_id}@{e.rule_version}")
        return {k: sorted(v) for k, v in sorted(index.items())}

    def dependencies_of(self, rule_id: str, version: str) -> Dict[str, List[str]]:
        """rule -> dependencies (inspection only)."""
        entry = self.get_rule_version(rule_id, version)
        if entry is None:
            raise KeyError(f"Unknown rule {rule_id}@{version}")
        return {k: sorted(v) for k, v in sorted((entry.dependency_manifest or {}).items())}

    def find_rules_by_fact(self, fact: str) -> List[str]:
        return self.reverse_index().get(fact, [])

    def find_rules_by_varga(self, varga: str) -> List[str]:
        out = [f"{e.rule_id}@{e.rule_version}" for e in self.entries.values()
               if varga in (e.applicability_spec.required_vargas or [])
               or any(f"varga.{varga}." in f for f in e.applicability_spec.required_facts)]
        return sorted(set(out))

    def find_rules_by_dasha(self, system: str) -> List[str]:
        out = [f"{e.rule_id}@{e.rule_version}" for e in self.entries.values()
               if system in (e.applicability_spec.required_dasha_systems or [])
               or any(f.startswith(f"dasha.{system}.") for f in e.applicability_spec.required_facts)]
        return sorted(set(out))

    def find_rules_by_transit(self, planet: Optional[str] = None) -> List[str]:
        out = []
        for e in self.entries.values():
            paths = list(e.applicability_spec.required_transit_data or []) + [
                f for f in e.applicability_spec.required_facts if f.startswith("transit.")]
            if planet is None and paths:
                out.append(f"{e.rule_id}@{e.rule_version}")
            elif planet is not None and any(f"transit.{planet}." in p for p in paths):
                out.append(f"{e.rule_id}@{e.rule_version}")
        return sorted(set(out))

    def find_rules_by_strength(self, metric: Optional[str] = None) -> List[str]:
        out = []
        for e in self.entries.values():
            paths = list(e.applicability_spec.required_strength_data or []) + [
                f for f in e.applicability_spec.required_facts if f.startswith("strength.")]
            if metric is None and paths:
                out.append(f"{e.rule_id}@{e.rule_version}")
            elif metric is not None and any(f"strength.{metric}." in p for p in paths):
                out.append(f"{e.rule_id}@{e.rule_version}")
        return sorted(set(out))

    def find_rules_by_jaimini_dependency(self, requirement: Optional[str] = None) -> List[str]:
        out = []
        for e in self.entries.values():
            reqs = list(e.applicability_spec.required_jaimini_data or []) + [
                f for f in e.applicability_spec.required_facts if f.startswith("jaimini.")]
            if requirement is None and reqs:
                out.append(f"{e.rule_id}@{e.rule_version}")
            elif requirement is not None and requirement in reqs:
                out.append(f"{e.rule_id}@{e.rule_version}")
        return sorted(set(out))

    def find_rules_by_source(self, source_id: str) -> List[str]:
        return sorted(f"{e.rule_id}@{e.rule_version}" for e in self.entries.values()
                      if source_id in e.source_ids)

    # -- conflicts (§19) -------------------------------------------------
    def find_conflicts(self) -> List[KnowledgeConflict]:
        by_id = {e.rule_id: e for e in self.entries.values()}
        conflicts: List[KnowledgeConflict] = []
        seen: set = set()
        declared: List[Tuple[str, str]] = []
        for e in self.entries.values():
            for other in e.conflicts:
                declared.append((e.rule_id, other))
        try:
            from core.jaimini.conflicts import SAME_PROPOSITION_PAIRS
            for a, b, _ in SAME_PROPOSITION_PAIRS:
                declared.append((a, b))
        except ImportError:
            pass
        for a, b in declared:
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            ea, eb = by_id.get(a), by_id.get(b)
            conflicts.append(KnowledgeConflict(
                conflict_id=_conflict_id(a, b), rule_a=a, rule_b=b,
                tradition_a=ea.tradition if ea else "",
                tradition_b=eb.tradition if eb else "",
                version_a=ea.rule_version if ea else "",
                version_b=eb.rule_version if eb else "",
                conflict_type="REPORTED_ONLY", status="REPORTED_ONLY"))
        return sorted(conflicts, key=lambda c: (c.rule_a, c.rule_b))

    # -- snapshot (§24) --------------------------------------------------
    def to_snapshot(self) -> "CatalogueSnapshot":
        return build_snapshot(self)


def _version_tuple(version: str) -> Tuple:
    core = (version or "0.0.0").split("-")[0]
    try:
        return tuple(int(x) for x in core.split("."))
    except ValueError:
        return (0, 0, 0)


# ---------------------------------------------------------------------------
# Health (§22)
# ---------------------------------------------------------------------------

class RuleKnowledgeHealth(BaseModel):
    rule_id: str
    rule_version: str
    schema_valid: bool
    security_valid: bool
    dependency_valid: bool
    provenance_valid: bool
    tests_valid: bool
    lifecycle_valid: bool
    catalogue_valid: bool
    applicability_valid: bool

    model_config = {"frozen": True}


LIFECYCLE_STATES_6E = ("DRAFT", "VALIDATED", "TESTED", "REVIEW_PENDING", "ACTIVE",
                       "ENABLED", "DISABLED", "DEPRECATED", "SUPERSEDED",
                       "ARCHIVED", "REJECTED", "EXPERIMENTAL")


def get_rule_health(
    entry: RuleKnowledgeEntry,
    catalogue: Optional[RuleKnowledgeCatalogue] = None,
) -> RuleKnowledgeHealth:
    manifest = entry.dependency_manifest or {}
    texts = [entry.name, entry.description] + list(entry.source_ids)
    suspicious = any(find_suspicious_text(t or "") for t in texts)
    fact_paths = (list(entry.applicability_spec.required_facts)
                  + list(entry.applicability_spec.required_transit_data)
                  + list(entry.applicability_spec.required_strength_data))
    ns_ok = all(match_namespace(p) is not None or p.startswith("rule:") for p in fact_paths)
    deps_known = all((catalogue.has_rule(d) if catalogue is not None else True)
                     for d in entry.applicability_spec.required_rule_results)
    return RuleKnowledgeHealth(
        rule_id=entry.rule_id,
        rule_version=entry.rule_version,
        schema_valid=bool(entry.rule_id and entry.rule_version and entry.tradition
                          and entry.system and entry.category),
        security_valid=not suspicious,
        dependency_valid=bool(ns_ok and deps_known),
        provenance_valid=entry.provenance_status in VERIFICATION_STATES or entry.provenance_status == "",
        tests_valid=entry.validation_status in ("VALID", "NEEDS_REVIEW"),
        lifecycle_valid=entry.lifecycle_status in LIFECYCLE_STATES_6E,
        catalogue_valid=bool(entry.fingerprint and entry.fingerprint == entry.compute_fingerprint()),
        applicability_valid=bool(entry.applicability_spec.required_facts
                                 or entry.applicability_spec.required_vargas
                                 or entry.applicability_spec.required_dasha_systems
                                 or entry.applicability_spec.required_transit_data
                                 or entry.applicability_spec.required_strength_data
                                 or entry.applicability_spec.required_jaimini_data
                                 or entry.applicability_spec.required_rule_results),
    )


# ---------------------------------------------------------------------------
# Knowledge graph view (§23)
# ---------------------------------------------------------------------------

GRAPH_NODE_TYPES = ("RULE", "RULE_VERSION", "SOURCE", "EVIDENCE", "CLAIM",
                    "FACT", "VARGA", "DASHA", "TRANSIT", "STRENGTH",
                    "JAIMINI", "CONFLICT", "PROFILE")
GRAPH_EDGE_TYPES = ("SUPPORTS", "DEPENDS_ON", "REQUIRES", "CONFLICTS_WITH",
                    "SUPERSEDES", "DERIVED_FROM", "EVALUATES", "APPLIES_TO")


class KnowledgeGraph(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = {"frozen": True}

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "nodes": sorted(self.nodes, key=lambda n: n["node_id"]),
            "edges": sorted(self.edges,
                            key=lambda e: (e["from_id"], e["to_id"], e["relation"])),
        }

    def fingerprint(self) -> str:
        s = json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _fact_node_type(path: str) -> str:
    if path.startswith("varga."):
        return "VARGA"
    if path.startswith("dasha."):
        return "DASHA"
    if path.startswith("transit."):
        return "TRANSIT"
    if path.startswith("strength."):
        return "STRENGTH"
    if path.startswith("jaimini."):
        return "JAIMINI"
    return "FACT"


def build_knowledge_graph(catalogue: RuleKnowledgeCatalogue) -> KnowledgeGraph:
    """Inspection view over catalogue entries. Complements (not duplicates)
    EvidenceGraph, which models a single evaluation's evidence trail."""
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: set = set()

    def add_node(node_id: str, node_type: str, label: str, **attrs: Any) -> None:
        nodes[node_id] = {"node_id": node_id, "node_type": node_type,
                          "label": label, **attrs}

    def add_edge(a: str, b: str, relation: str) -> None:
        edges.add((a, b, relation))

    for entry in catalogue.list_all():
        rule_node = f"rule:{entry.rule_id}"
        ver_node = f"rule_version:{entry.rule_id}@{entry.rule_version}"
        add_node(rule_node, "RULE", entry.name or entry.rule_id,
                 tradition=entry.tradition, system=entry.system, category=entry.category)
        add_node(ver_node, "RULE_VERSION", f"{entry.rule_id}@{entry.rule_version}",
                 lifecycle=entry.lifecycle_status, validation=entry.validation_status)
        add_edge(ver_node, rule_node, "DERIVED_FROM")
        for source_id in sorted(entry.source_ids):
            src_node = f"source:{source_id}"
            add_node(src_node, "SOURCE", source_id)
            add_edge(src_node, ver_node, "SUPPORTS")
        for ev_id in sorted(entry.evidence_ids):
            ev_node = f"evidence:{entry.rule_id}:{ev_id}"
            add_node(ev_node, "EVIDENCE", ev_id, rule_id=entry.rule_id)
            add_edge(ev_node, ver_node, "EVALUATES")
        spec = entry.applicability_spec
        for fact in sorted(set(spec.required_facts) | set(spec.required_transit_data)
                           | set(spec.required_strength_data) | set(spec.required_jaimini_data)):
            fact_node = f"fact:{fact}"
            add_node(fact_node, _fact_node_type(fact), fact)
            add_edge(ver_node, fact_node, "REQUIRES")
            add_edge(fact_node, ver_node, "APPLIES_TO")
        for varga in sorted(spec.required_vargas):
            v_node = f"varga:{varga}"
            add_node(v_node, "VARGA", varga)
            add_edge(ver_node, v_node, "REQUIRES")
        for system in sorted(spec.required_dasha_systems):
            d_node = f"dasha:{system}"
            add_node(d_node, "DASHA", system)
            add_edge(ver_node, d_node, "REQUIRES")
        for dep in sorted(spec.required_rule_results):
            dep_node = f"rule:{dep}"
            if dep_node not in nodes:
                add_node(dep_node, "RULE", dep)
            add_edge(ver_node, dep_node, "DEPENDS_ON")
        for profile in sorted(spec.profile_constraints):
            p_node = f"profile:{profile}"
            add_node(p_node, "PROFILE", profile)
            add_edge(ver_node, p_node, "APPLIES_TO")
        if entry.supersedes:
            add_edge(ver_node, f"rule_version:{entry.rule_id}@{entry.supersedes}", "SUPERSEDES")
    for conflict in catalogue.find_conflicts():
        c_node = f"conflict:{conflict.conflict_id}"
        add_node(c_node, "CONFLICT", f"{conflict.rule_a} vs {conflict.rule_b}",
                 conflict_type=conflict.conflict_type, status=conflict.status)
        add_edge(f"rule:{conflict.rule_a}", c_node, "CONFLICTS_WITH")
        add_edge(f"rule:{conflict.rule_b}", c_node, "CONFLICTS_WITH")
    edge_list = [{"from_id": a, "to_id": b, "relation": r}
                 for a, b, r in sorted(edges)]
    return KnowledgeGraph(nodes=[nodes[k] for k in sorted(nodes)],
                          edges=edge_list)


# ---------------------------------------------------------------------------
# Snapshot (§24)
# ---------------------------------------------------------------------------

class CatalogueSnapshot(BaseModel):
    entries: List[Dict[str, Any]] = Field(default_factory=list)
    active_rules: List[str] = Field(default_factory=list)
    versions: Dict[str, List[str]] = Field(default_factory=dict)
    dependencies: Dict[str, Dict[str, List[str]]] = Field(default_factory=dict)
    sources: List[str] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    fingerprints: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True}

    def to_canonical_json(self) -> str:
        return json.dumps({
            "entries": sorted(self.entries, key=lambda e: (e["rule_id"], e["rule_version"])),
            "active_rules": sorted(self.active_rules),
            "versions": {k: v for k, v in sorted(self.versions.items())},
            "dependencies": {k: v for k, v in sorted(self.dependencies.items())},
            "sources": sorted(self.sources),
            "evidence_references": sorted(self.evidence_references),
            "conflicts": sorted(self.conflicts, key=lambda c: (c["rule_a"], c["rule_b"])),
            "fingerprints": {k: v for k, v in sorted(self.fingerprints.items())},
        }, sort_keys=True, separators=(",", ":"))

    def fingerprint(self) -> str:
        return hashlib.sha256(self.to_canonical_json().encode("utf-8")).hexdigest()


def build_snapshot(catalogue: RuleKnowledgeCatalogue) -> CatalogueSnapshot:
    entries = catalogue.list_all()
    active = [f"{e.rule_id}@{e.rule_version}" for e in entries
              if e.lifecycle_status in ACTIVE_LIFECYCLES]
    versions: Dict[str, List[str]] = {}
    for e in entries:
        versions.setdefault(e.rule_id, []).append(e.rule_version)
    versions = {k: sorted(v, key=_version_tuple) for k, v in sorted(versions.items())}
    return CatalogueSnapshot(
        entries=[e.to_canonical_dict() for e in entries],
        active_rules=sorted(active),
        versions=versions,
        dependencies={f"{e.rule_id}@{e.rule_version}":
                      {k: sorted(v) for k, v in sorted((e.dependency_manifest or {}).items())}
                      for e in entries},
        sources=sorted({s for e in entries for s in e.source_ids}),
        evidence_references=sorted({s for e in entries for s in e.evidence_ids}),
        conflicts=[c.model_dump() for c in catalogue.find_conflicts()],
        fingerprints={f"{e.rule_id}@{e.rule_version}": e.fingerprint for e in entries},
    )


def snapshot_round_trip(snapshot: CatalogueSnapshot) -> bool:
    """Canonical serialization round-trip must be byte-equal."""
    payload = snapshot.to_canonical_json()
    revived = CatalogueSnapshot.model_validate_json(payload)
    return revived.to_canonical_json() == payload


# ---------------------------------------------------------------------------
# Classical ingestion (read-only; no astrology semantics added)
# ---------------------------------------------------------------------------

def _classical_entry(
    rule_id: str,
    version: str,
    name: str,
    description: str,
    system: str,
    tradition: str,
    category: str,
    subcategory: str,
    lifecycle_status: str,
    validation_status: str,
    provenance_status: str,
    source_ids: List[str],
    manifest: Dict[str, List[str]],
    spec: RuleApplicabilitySpec,
    conflicts: Optional[List[str]] = None,
) -> RuleKnowledgeEntry:
    entry = RuleKnowledgeEntry(
        rule_id=rule_id, rule_version=version, name=name, description=description,
        system=normalize_system(system), tradition=normalize_tradition(tradition),
        category=normalize_category(rule_id, category), subcategory=subcategory,
        lifecycle_status=lifecycle_status, validation_status=validation_status,
        provenance_status=provenance_status or "UNVERIFIED",
        source_ids=source_ids, evidence_ids=[],
        dependency_manifest={k: sorted(v) for k, v in manifest.items()},
        conflicts=sorted(conflicts or []), applicability_spec=spec)
    return entry.model_copy(update={"fingerprint": entry.compute_fingerprint()})


def _jaimini_spec_for(rule_id: str) -> RuleApplicabilitySpec:
    """Translate 5F DEPENDENCY_SPECS into 6E applicability requirements."""
    try:
        from core.jaimini.dependencies import get_dependency_spec
        spec5f = get_dependency_spec(rule_id)
    except (ImportError, KeyError):
        return RuleApplicabilitySpec(required_facts=["natal.Sun.sign"])
    facts = ["natal.Sun.sign"]
    vargas = list(spec5f.varga_dependencies or [])
    jaimini: List[str] = []
    for dep in spec5f.dependencies:
        path = dep.fact_path
        if path == "ChartFacts.planets[D1]":
            continue
        if path == "JaiminiFacts.chara_karakas":
            jaimini.extend(["jaimini.karaka.AK", "jaimini.karaka.AmK"])
        elif path == "JaiminiFacts.rashi_drishti":
            jaimini.append("jaimini.rashi_drishti")
        elif path == "JaiminiFacts.karakamsha":
            jaimini.append("jaimini.karakamsha")
        elif path == "JaiminiFacts.upapada":
            jaimini.append("jaimini.UL")
        elif path.startswith("JaiminiFacts.arudha_padas["):
            inner = path[len("JaiminiFacts.arudha_padas["):-1]
            try:
                house = int(inner)
                jaimini.append(f"jaimini.pada.{house}" if house != 1 else "jaimini.AL")
            except ValueError:
                jaimini.append("jaimini.AL")
        elif path == "varga_facts.D9":
            if "D9" not in vargas:
                vargas.append("D9")
    if rule_id.startswith("JAI.KARAKAMSHA."):
        vargas.append("D9")
    if rule_id.startswith("JAI.SWAMSA."):
        vargas.append("D9")
    return RuleApplicabilitySpec(
        required_facts=sorted(set(facts)),
        required_vargas=sorted(set(vargas)),
        required_jaimini_data=sorted(set(jaimini)),
    )


def ingest_parashari_catalogue(catalogue: RuleKnowledgeCatalogue) -> RuleKnowledgeCatalogue:
    from core.rules.parashari.catalog import build_manifest
    for item in build_manifest():
        spec = RuleApplicabilitySpec(required_facts=["natal.Sun.sign", "natal.Moon.sign"])
        entry = _classical_entry(
            rule_id=item["rule_id"], version=item.get("version") or "1.0.0",
            name=item.get("name") or "", description=f"Parashari yoga ({item.get('method') or ''})",
            system="PARASHARI", tradition=item.get("tradition") or "PARASHARI_CLASSICAL",
            category="YOGA", subcategory=item.get("method") or "",
            lifecycle_status="ACTIVE" if item.get("status") == "ENABLED" else item.get("status") or "ACTIVE",
            validation_status="VALID", provenance_status=item.get("source_reference") or "UNVERIFIED",
            source_ids=[item.get("source") or "BPHS"],
            manifest={"input_facts": ["natal.Sun.sign", "natal.Moon.sign"],
                      "rule_dependencies": [], "varga_dependencies": [],
                      "dasha_dependencies": [], "transit_dependencies": [],
                      "strength_dependencies": []},
            spec=spec)
        catalogue = catalogue.register(entry)
    return catalogue


def ingest_dosha_catalogue(catalogue: RuleKnowledgeCatalogue) -> RuleKnowledgeCatalogue:
    from core.rules.doshas.catalog import build_manifest
    for item in build_manifest():
        spec = RuleApplicabilitySpec(required_facts=["natal.Mars.sign", "natal.Moon.sign"])
        entry = _classical_entry(
            rule_id=item.get("dosha_id") or item.get("rule_id"), version=item.get("version") or "1.0.0",
            name=item.get("name") or "", description=f"Dosha ({item.get('method') or ''})",
            system="DOSHA", tradition=item.get("tradition") or "PARASHARI_CLASSICAL",
            category="DOSHA", subcategory=item.get("method") or "",
            lifecycle_status="ACTIVE" if item.get("status") == "ENABLED" else item.get("status") or "ACTIVE",
            validation_status="VALID", provenance_status=item.get("source_reference") or "UNVERIFIED",
            source_ids=[item.get("source") or "CLASSICAL"],
            manifest={"input_facts": ["natal.Mars.sign", "natal.Moon.sign"],
                      "rule_dependencies": [], "varga_dependencies": [],
                      "dasha_dependencies": [], "transit_dependencies": [],
                      "strength_dependencies": []},
            spec=spec)
        catalogue = catalogue.register(entry)
    return catalogue


def ingest_jaimini_catalogue(catalogue: RuleKnowledgeCatalogue) -> RuleKnowledgeCatalogue:
    from core.jaimini.rules.catalogue import describe_catalogue
    for item in describe_catalogue():
        entry = _classical_entry(
            rule_id=item["rule_id"], version=item.get("rule_version") or "1.0.0",
            name=item.get("name") or "", description=item.get("description") or "",
            system="JAIMINI", tradition="JAIMINI_CLASSICAL",
            category=normalize_category(item["rule_id"], "JAIMINI"),
            subcategory=item.get("origin_label") or "",
            lifecycle_status="ACTIVE", validation_status="VALID",
            provenance_status=item.get("source_reference") or "UNVERIFIED",
            source_ids=["JAIMINI_TRADITION"],
            manifest={"input_facts": sorted(set(
                _jaimini_spec_for(item["rule_id"]).required_facts
                + _jaimini_spec_for(item["rule_id"]).required_jaimini_data)),
                      "rule_dependencies": [], "varga_dependencies": [],
                      "dasha_dependencies": [], "transit_dependencies": [],
                      "strength_dependencies": []},
            spec=_jaimini_spec_for(item["rule_id"]))
        catalogue = catalogue.register(entry)
    return catalogue


# ---------------------------------------------------------------------------
# Synthetic custom fixtures (§28 — no classical claims)
# ---------------------------------------------------------------------------

def _custom_definition(
    rule_id: str,
    formation: ConditionNode,
    input_facts: List[str],
    category: str = "CUSTOM",
    lifecycle_status: str = "ACTIVE",
    varga: Optional[List[str]] = None,
    dasha: Optional[List[str]] = None,
    transit: Optional[List[str]] = None,
    strength: Optional[List[str]] = None,
    rule_deps: Optional[List[str]] = None,
) -> DynamicRuleDefinition:
    from .schema import (RuleClassification, RuleDependencies, RuleEvidenceSpec,
                         RuleIdentity, RuleLifecycle, RuleProvenance,
                         RuleSemantics, RuleValidationInfo, SourceReference)
    return DynamicRuleDefinition(
        identity=RuleIdentity(rule_id=rule_id, rule_version="1.0.0",
                              rule_name=rule_id,
                              description=f"6E synthetic fixture {rule_id}; no classical claim."),
        classification=RuleClassification(system="DYNAMIC_CUSTOM", tradition="CUSTOM_DEVELOPER",
                                          category=category, subcategory="SYNTHETIC"),
        provenance=RuleProvenance(
            source_reference=SourceReference(source_id="DEV-6E-SYNTHETIC",
                                             title="Phase 6E synthetic fixture",
                                             verification_status="USER_SUPPLIED"),
            provenance_status="USER_SUPPLIED", confidence="CUSTOM"),
        semantics=RuleSemantics(formation=formation),
        dependencies=RuleDependencies(
            input_facts=input_facts, rule_dependencies=rule_deps or [],
            varga_dependencies=varga or [], dasha_dependencies=dasha or [],
            transit_dependencies=transit or [], strength_dependencies=strength or []),
        evidence=RuleEvidenceSpec(evidence_requirements=["formation"]),
        lifecycle=RuleLifecycle(status=lifecycle_status),
        validation=RuleValidationInfo(validation_status="VALID"))


def build_custom_fixtures() -> List[DynamicRuleDefinition]:
    """The six required CUSTOM fixtures (§28), all USER_SUPPLIED/UNVERIFIED."""
    return [
        _custom_definition("CUSTOM.NATAL.TEST",
                           ConditionNode(op="planet_in_sign", params={"planet": "Mars", "sign": "Aries"}),
                           ["natal.Mars.sign"]),
        _custom_definition("CUSTOM.D9.TEST",
                           ConditionNode(op="planet_in_varga_sign",
                                         params={"planet": "Jupiter", "varga": "D9", "sign": "Cancer"}),
                           ["varga.D9.Jupiter"], varga=["D9"]),
        _custom_definition("CUSTOM.STRENGTH.TEST",
                           ConditionNode(op="strength_threshold",
                                         params={"planet": "Mars", "metric": "shadbala", "min": 3.0}),
                           ["strength.shadbala.Mars"], strength=["shadbala"]),
        _custom_definition("CUSTOM.DASHA.TEST",
                           ConditionNode(op="dasha_active",
                                         params={"system": "vimshottari", "sign": "Jupiter"}),
                           ["dasha.vimshottari.active_sign"], dasha=["vimshottari"]),
        _custom_definition("CUSTOM.TRANSIT.TEST",
                           ConditionNode(op="transit_in_sign",
                                         params={"planet": "Jupiter", "sign": "Cancer"}),
                           ["transit.Jupiter.sign"], transit=["transit.Jupiter.sign"]),
        _custom_definition("CUSTOM.JAIMINI.TEST",
                           ConditionNode(op="karaka_equals",
                                         params={"karaka": "AK", "planet": "Jupiter"}),
                           ["jaimini.karaka.AK", "jaimini.drishti"]),
    ]


def ingest_custom_fixtures(catalogue: RuleKnowledgeCatalogue) -> RuleKnowledgeCatalogue:
    for rule in build_custom_fixtures():
        catalogue = catalogue.register(entry_from_dynamic_definition(rule))
    deprecated = _custom_definition(
        "CUSTOM.DEPRECATED.TEST",
        ConditionNode(op="planet_in_sign", params={"planet": "Venus", "sign": "Taurus"}),
        ["natal.Venus.sign"], lifecycle_status="DEPRECATED")
    catalogue = catalogue.register(entry_from_dynamic_definition(deprecated))
    return catalogue


def build_golden_catalogue() -> RuleKnowledgeCatalogue:
    """Golden catalogue (§25): accepted classical rules + synthetic customs only."""
    catalogue = RuleKnowledgeCatalogue()
    catalogue = ingest_parashari_catalogue(catalogue)
    catalogue = ingest_dosha_catalogue(catalogue)
    catalogue = ingest_jaimini_catalogue(catalogue)
    catalogue = ingest_custom_fixtures(catalogue)
    return catalogue


# ---------------------------------------------------------------------------
# Internal API (§32 — no frontend endpoints)
# ---------------------------------------------------------------------------

_GOLDEN_CACHE: Optional[RuleKnowledgeCatalogue] = None


def get_rule_catalogue() -> RuleKnowledgeCatalogue:
    global _GOLDEN_CACHE
    if _GOLDEN_CACHE is None:
        _GOLDEN_CACHE = build_golden_catalogue()
    return _GOLDEN_CACHE


def find_rules(catalogue: Optional[RuleKnowledgeCatalogue] = None, **filters: Any) -> List[RuleKnowledgeEntry]:
    return (catalogue or get_rule_catalogue()).find_rules(**filters)


def get_rule(catalogue: RuleKnowledgeCatalogue, rule_id: str,
             version: Optional[str] = None) -> Optional[RuleKnowledgeEntry]:
    return catalogue.get_rule(rule_id, version)


def get_rule_version(catalogue: RuleKnowledgeCatalogue, rule_id: str,
                     version: str) -> Optional[RuleKnowledgeEntry]:
    return catalogue.get_rule_version(rule_id, version)


def find_rules_for_context(
    catalogue: RuleKnowledgeCatalogue,
    context: KnowledgeContext,
    mode: str = "ACTIVE_ONLY",
    **filters: Any,
) -> List[Tuple[RuleKnowledgeEntry, RuleApplicabilityResult]]:
    return catalogue.find_rules_for_context(context, mode=mode, **filters)


def find_rules_by_fact(catalogue: RuleKnowledgeCatalogue, fact: str) -> List[str]:
    return catalogue.find_rules_by_fact(fact)


def find_rules_by_varga(catalogue: RuleKnowledgeCatalogue, varga: str) -> List[str]:
    return catalogue.find_rules_by_varga(varga)


def find_rules_by_dasha(catalogue: RuleKnowledgeCatalogue, system: str) -> List[str]:
    return catalogue.find_rules_by_dasha(system)


def find_rules_by_transit(catalogue: RuleKnowledgeCatalogue,
                          planet: Optional[str] = None) -> List[str]:
    return catalogue.find_rules_by_transit(planet)


def find_rules_by_strength(catalogue: RuleKnowledgeCatalogue,
                           metric: Optional[str] = None) -> List[str]:
    return catalogue.find_rules_by_strength(metric)


def find_rules_by_jaimini_dependency(
    catalogue: RuleKnowledgeCatalogue, requirement: Optional[str] = None,
) -> List[str]:
    return catalogue.find_rules_by_jaimini_dependency(requirement)


def find_rules_by_source(catalogue: RuleKnowledgeCatalogue, source_id: str) -> List[str]:
    return catalogue.find_rules_by_source(source_id)


def find_conflicts(catalogue: RuleKnowledgeCatalogue) -> List[KnowledgeConflict]:
    return catalogue.find_conflicts()


def get_catalogue_snapshot(catalogue: RuleKnowledgeCatalogue) -> CatalogueSnapshot:
    return catalogue.to_snapshot()


def measure_performance(catalogue: RuleKnowledgeCatalogue,
                        context: KnowledgeContext) -> Dict[str, float]:
    """Record-only timings (§29). No optimization claims."""
    timings: Dict[str, float] = {}
    t0 = time.perf_counter()
    build_golden_catalogue()
    timings["catalogue_load_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    catalogue.get_rule("CUSTOM.NATAL.TEST", "1.0.0")
    timings["rule_lookup_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    catalogue.find_rules_by_varga("D9")
    timings["dependency_lookup_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    catalogue.reverse_index()
    timings["reverse_dependency_lookup_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    entry = catalogue.get_rule_version("CUSTOM.NATAL.TEST", "1.0.0")
    assert entry is not None
    evaluate_rule_applicability(entry, context, catalogue)
    timings["applicability_evaluation_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    catalogue.to_snapshot()
    timings["golden_catalogue_generation_s"] = time.perf_counter() - t0
    return timings
