"""
Phase 5F — controlled Jaimini cross-system integration layer.

Boundary: consumes canonical ChartFacts + varga D9 + JaiminiFacts (read-only,
never modified, never recalculated). Emits a structured JaiminiEvaluation
aggregate (rules, evidence graph, conflicts, dependencies, provenance,
limitations). No strength inputs exist on this path by construction; Varga D9
flows only to rules declaring varga_dependencies == ["D9"].

UNKNOWN semantics: a required input that is unavailable yields
formation_status == UNCERTAIN (formed=False) with a missing-dependency
explanation — never NOT_FORMED. Source confidence never affects formation.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.rules.enums import (
    FormationStatus,
    StrengthStatus,
    CancellationStatus,
    MitigationStatus,
    ConfidenceLevel,
    SourceType,
    RuleCategory,
    RuleTradition,
)

from .rules import JaiminiYogaProfile
from .rules.catalogue import get_catalogue
from .rules.models import JaiminiRuleResult
from .dependencies import (
    FACT, DERIVED_FACT, get_dependency_spec, detect_dependency_cycles,
)
from .evidence import build_evidence_graph, JaiminiEvidenceGraph
from .conflicts import analyze_conflicts, RuleConflict
from .rule_validators import (
    validate_evidence_completeness,
    validate_rule_provenance,
)


class JaiminiIntegrationProfile(BaseModel):
    yoga_profile: JaiminiYogaProfile = Field(default_factory=JaiminiYogaProfile)
    origin_labels: Optional[List[str]] = Field(
        default=None,
        description="Tradition subset filter, e.g. ['CLASSICAL_JAIMINI']; None = all"
    )
    include_unknown: bool = Field(
        default=True,
        description="Keep UNKNOWN (UNCERTAIN) results in the aggregate"
    )
    version: str = "1.0.0"


class JaiminiEvaluation(BaseModel):
    """Structured 5F aggregate. Deterministic: sorted orderings, no timestamps."""

    profile: Dict[str, Any] = Field(default_factory=dict)
    rules: List[JaiminiRuleResult] = Field(default_factory=list)
    formed_rules: List[str] = Field(default_factory=list)
    not_formed_rules: List[str] = Field(default_factory=list)
    unknown_rules: List[str] = Field(default_factory=list)
    conflicts: List[RuleConflict] = Field(default_factory=list)
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_graph: JaiminiEvidenceGraph = Field(default=JaiminiEvidenceGraph())
    provenance_summary: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    total_rules: int = 0


# Required karaka codes per rule (mirrors evaluator needs; metadata-level).
REQUIRED_KARAKAS: Dict[str, List[str]] = {
    "JAI.KARAKA.AK_AMK_CONJUNCTION": ["AK", "AmK"],
    "JAI.KARAKA.AK_KENDRA_FROM_AL": ["AK"],
    "JAI.KARAKA.DK_UL_SAMBANDHA": ["DK"],
    "JAI.DRISHTI.AK_AMK_MUTUAL": ["AK", "AmK"],
    "JAI.DRISHTI.AMK_ON_AL": ["AmK"],
    "JAI.DRISHTI.AK_ON_AL": ["AK"],
    "JAI.ARUDHA.AL_BENEFIC_OCCUPANCY": [],
    "JAI.ARUDHA.AL_LORD_KENDRA_TRINE": [],
    "JAI.ARUDHA.DHANA_A2_A11": [],
    "JAI.ARUDHA.A7_UL_ALIGNMENT": [],
    "JAI.KARAKAMSHA.BENEFIC_OCCUPANCY": ["AK"],
    "JAI.SWAMSA.BENEFIC_OCCUPANCY": [],
}

# Required pada keys per rule (house numbers; 12 == UL/A12).
REQUIRED_PADAS: Dict[str, List[int]] = {
    "JAI.KARAKA.AK_KENDRA_FROM_AL": [1],
    "JAI.KARAKA.DK_UL_SAMBANDHA": [12],
    "JAI.DRISHTI.AMK_ON_AL": [1],
    "JAI.DRISHTI.AK_ON_AL": [1],
    "JAI.ARUDHA.AL_BENEFIC_OCCUPANCY": [1],
    "JAI.ARUDHA.AL_LORD_KENDRA_TRINE": [1],
    "JAI.ARUDHA.DHANA_A2_A11": [2, 11],
    "JAI.ARUDHA.A7_UL_ALIGNMENT": [7, 12],
}


def _d9_of(varga_facts: Dict[str, Any], planet: str) -> Optional[str]:
    entry = ((varga_facts or {}).get("planets", {}).get(planet) or {}).get("D9")
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry.get("sign")
    return getattr(entry, "sign", None)


def _d9_lagna(varga_facts: Dict[str, Any]) -> Optional[str]:
    entry = (varga_facts or {}).get("ascendant", {}).get("D9")
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry.get("sign")
    return getattr(entry, "sign", None)


def missing_inputs(rule_id: str, jaimini_facts: Any, varga_facts: Dict[str, Any]) -> List[str]:
    """List unavailable required inputs for a rule (empty = evaluable)."""
    missing: List[str] = []
    karakas = getattr(getattr(jaimini_facts, "chara_karakas", None), "karakas", {}) or {}
    for code in REQUIRED_KARAKAS.get(rule_id, []):
        if code not in karakas:
            missing.append(f"karaka:{code}")
    padas = getattr(jaimini_facts, "arudha_padas", {}) or {}
    for h in REQUIRED_PADAS.get(rule_id, []):
        if h not in padas:
            missing.append(f"pada:A{h}")
    spec = get_dependency_spec(rule_id)
    if "D9" in spec.varga_dependencies:
        if rule_id == "JAI.KARAKAMSHA.BENEFIC_OCCUPANCY":
            ak_item = karakas.get("AK")
            ak = ak_item.planet if ak_item is not None else None
            ak_d9 = _d9_of(varga_facts, ak) if ak else None
            planets = (varga_facts or {}).get("planets", {}) or {}
            any_d9 = any(_d9_of(varga_facts, p) is not None for p in planets)
            if ak_d9 is None and not any_d9:
                missing.append("varga:D9 (no D9 occupancy available)")
        elif rule_id == "JAI.SWAMSA.BENEFIC_OCCUPANCY":
            if _d9_lagna(varga_facts) is None:
                missing.append("varga:D9-lagna (Swamsa D9 ascendant unavailable)")
    return sorted(missing)


def unknown_result(rule_id: str, name: str, method: str, origin_label: str,
                   missing: List[str], dependencies: List[str]) -> JaiminiRuleResult:
    return JaiminiRuleResult(
        rule_id=rule_id, name=name, formed=False,
        formation_status=FormationStatus.UNCERTAIN,
        quality=StrengthStatus.UNKNOWN,
        cancellation_status=CancellationStatus.NONE,
        mitigation_status=MitigationStatus.NONE,
        category=RuleCategory.JAIMINI, tradition=RuleTradition.JAIMINI,
        origin_label=origin_label, method=method,
        confidence=ConfidenceLevel.TRADITION_DEPENDENT,
        source_type=SourceType.UNVERIFIED, source_reference="UNVERIFIED",
        formation_evidence=[],
        cancellation_evidence=[
            f"UNKNOWN: required input(s) unavailable — missing {sorted(missing)}. "
            f"Not evaluated; must not be read as NOT_FORMED."
        ],
        mitigation_evidence=[],
        strength_factors=[],
        relevant_planets=[], relevant_signs=[], relevant_houses=[],
        dependencies=sorted(dependencies),
        notes="UNKNOWN semantics: missing dependency explanation recorded; formation undecided.",
    )


def validate_dependency_policy() -> List[str]:
    """Varga/strength policy audit: every spec must declare explicit lists;
    no 5F spec may declare strength dependencies (none do)."""
    violations: List[str] = []
    for rid, spec in sorted(__import__(
            "core.jaimini.dependencies",
            fromlist=["DEPENDENCY_SPECS"]).DEPENDENCY_SPECS.items()):
        if spec.varga_dependencies is None or spec.strength_dependencies is None:
            violations.append(f"{rid}: dependency lists must be explicit (may be empty).")
        if spec.strength_dependencies:
            violations.append(f"{rid}: declares strength dependencies {spec.strength_dependencies}.")
        for dep in spec.dependencies:
            if dep.dependency_type not in (FACT, DERIVED_FACT, "RULE_RESULT"):
                violations.append(f"{rid}: unknown dependency type {dep.dependency_type}.")
    return sorted(violations)


def evaluate_jaimini(
    chart_facts: Any,
    jaimini_facts: Any,
    varga_facts: Dict[str, Any],
    profile: Optional[JaiminiIntegrationProfile] = None,
) -> JaiminiEvaluation:
    """Full 5F pipeline: 5E evaluation (with UNKNOWN synthesis) + evidence
    graph + conflicts + validators. Deterministic; read-only over inputs."""
    if profile is None:
        profile = JaiminiIntegrationProfile()
    yoga_profile = profile.yoga_profile

    facts_method = jaimini_facts.chara_karakas.method.value
    if yoga_profile.karaka_method != facts_method:
        raise ValueError(
            f"Karaka method mismatch: profile={yoga_profile.karaka_method} vs "
            f"JaiminiFacts={facts_method}."
        )

    if detect_dependency_cycles():
        raise ValueError("RULE_RESULT dependency cycle detected.")

    wanted = set(yoga_profile.enabled_rule_ids) if yoga_profile.enabled_rule_ids else None
    origins = set(profile.origin_labels) if profile.origin_labels else None

    from .rules.pipeline import evaluate_jaimini_yogas  # local import: boundary clarity

    results: List[JaiminiRuleResult] = []
    for spec in sorted(get_catalogue(), key=lambda s: s.rule_id):
        if wanted is not None and spec.rule_id not in wanted:
            continue
        dep_spec = get_dependency_spec(spec.rule_id)
        if origins is not None and dep_spec.origin_label not in origins:
            continue
        missing = missing_inputs(spec.rule_id, jaimini_facts, varga_facts or {})
        if missing:
            if profile.include_unknown:
                results.append(unknown_result(
                    spec.rule_id, spec.name, spec.method,
                    dep_spec.origin_label, missing,
                    [d.fact_path for d in dep_spec.dependencies]))
            continue
        sub = dict(yoga_profile.model_dump())
        sub["enabled_rule_ids"] = [spec.rule_id]
        single = evaluate_jaimini_yogas(
            chart_facts, jaimini_facts, varga_facts,
            JaiminiYogaProfile(**sub))
        got = single.get_by_id(spec.rule_id)
        if got is None:  # defensive: evaluator skipped (should not happen)
            if profile.include_unknown:
                results.append(unknown_result(
                    spec.rule_id, spec.name, spec.method,
                    dep_spec.origin_label, ["evaluator:skipped"],
                    [d.fact_path for d in dep_spec.dependencies]))
            continue
        results.append(got)

    graph = build_evidence_graph(chart_facts, jaimini_facts, varga_facts or {}, results)
    conflicts = analyze_conflicts(results)
    completeness = validate_evidence_completeness(results)
    provenance_violations = validate_rule_provenance(results)
    policy_violations = validate_dependency_policy()

    formed = sorted(r.rule_id for r in results if r.formation_status == FormationStatus.FORMED)
    unknown = sorted(r.rule_id for r in results if r.formation_status == FormationStatus.UNCERTAIN)
    not_formed = sorted(r.rule_id for r in results if r.formation_status == FormationStatus.NOT_FORMED)

    limitations = [
        "Quality (strength) intentionally UNASSESSED for all rules.",
        "Source confidence UNVERIFIED for all rules; confidence never affects formation.",
        "UNKNOWN results reflect unavailable inputs, never negative evidence.",
        "Conflicts are reported only; no precedence or auto-resolution.",
        "D9 consumed only by rules declaring varga_dependencies=['D9']; no strength inputs on this path.",
    ]
    if completeness or provenance_violations or policy_violations:
        limitations.append(
            f"VALIDATOR ALERTS: completeness={completeness}; "
            f"provenance={provenance_violations}; policy={policy_violations}."
        )

    return JaiminiEvaluation(
        profile={
            "karaka_method": yoga_profile.karaka_method,
            "origin_labels": sorted(origins) if origins else "ALL",
            "include_unknown": profile.include_unknown,
            "engine": "jaimini-integration/1.0.0",
            "source_reference": "UNVERIFIED",
        },
        rules=results,
        formed_rules=formed,
        not_formed_rules=not_formed,
        unknown_rules=unknown,
        conflicts=conflicts,
        dependencies=[
            {"rule_id": rid,
             "origin_label": get_dependency_spec(rid).origin_label,
             "dependencies": [
                 {"type": d.dependency_type, "fact_path": d.fact_path,
                  "required": d.required, "description": d.description}
                 for d in sorted(get_dependency_spec(rid).dependencies,
                                 key=lambda x: x.fact_path)],
             "varga_dependencies": get_dependency_spec(rid).varga_dependencies,
             "strength_dependencies": get_dependency_spec(rid).strength_dependencies}
            for rid in sorted(get_dependency_spec(r.rule_id).rule_id for r in results)
        ],
        evidence_graph=graph,
        provenance_summary={
            "tradition": "JAIMINI",
            "source_reference": "UNVERIFIED",
            "confidence": ConfidenceLevel.TRADITION_DEPENDENT.value,
            "completeness_violations": completeness,
            "provenance_violations": provenance_violations,
            "policy_violations": policy_violations,
        },
        limitations=limitations,
        total_rules=len(results),
    )
