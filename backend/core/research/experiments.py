"""
Phase 9 — deterministic experiment runner.

Evaluates research-rule DSL conditions against declarative fixture facts
using the Phase 6A evaluator (no recalculation, no statistics, no LLM).
Reports raw OBSERVED_MATCH/MISMATCH counts — never accuracy %.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..rules.dynamic.evaluator import evaluate_rule
from ..rules.dynamic.schema import ConditionNode, DynamicRuleDefinition, RuleClassification, \
    RuleDependencies, RuleEvidenceSpec, RuleIdentity, RuleLifecycle, RuleProvenance, RuleSemantics, RuleValidationInfo, SourceReference
from .models import fingerprint_of


def _to_dynamic(rule: Dict[str, Any]) -> DynamicRuleDefinition:
    def cn(n: Dict[str, Any] | None) -> ConditionNode | None:
        if not n:
            return None
        return ConditionNode(op=n.get("op", "ANY"),
                             params=dict(n.get("params", {})),
                             children=[cn(c) for c in (n.get("children", []) or [])])
    deps = rule.get("dependencies", {}) or {}
    return DynamicRuleDefinition(
        identity=RuleIdentity(rule_id=rule.get("rule_id", ""), rule_version=rule.get("rule_version", "")),
        classification=RuleClassification(system="RESEARCH", tradition=rule.get("tradition", "EXPERIMENTAL"),
                                          category=rule.get("category", "CUSTOM")),
        provenance=RuleProvenance(source_reference=SourceReference(verification_status="UNVERIFIED")),
        semantics=RuleSemantics(formation=cn(rule.get("formation")),
                                cancellation=cn(rule.get("cancellation")),
                                mitigation=cn(rule.get("mitigation"))),
        dependencies=RuleDependencies(
            input_facts=list(deps.get("input_facts", [])),
            rule_dependencies=list(deps.get("rule_dependencies", [])),
            varga_dependencies=list(deps.get("varga_dependencies", [])),
            dasha_dependencies=list(deps.get("dasha_dependencies", [])),
            transit_dependencies=list(deps.get("transit_dependencies", [])),
            strength_dependencies=list(deps.get("strength_dependencies", []))),
        evidence=RuleEvidenceSpec(),
        lifecycle=RuleLifecycle(status="DRAFT"),
        validation=RuleValidationInfo(validation_status="UNVALIDATED"),
    )


def evaluate_fixture(rule: Dict[str, Any], fixture: Dict[str, Any]) -> Dict[str, Any]:
    facts = dict(fixture.get("facts", {}))
    dyn = _to_dynamic(rule)
    def resolver(path: str) -> Any:
        return facts.get(path)
    try:
        outcome = evaluate_rule(dyn, resolver)
        raw = (outcome.formation or "UNKNOWN").upper()
        formation = {"TRUE": "FORMED", "FALSE": "NOT_FORMED",
                     "FORMED": "FORMED", "NOT_FORMED": "NOT_FORMED"}.get(raw, "UNKNOWN")
    except Exception as e:  # noqa: BLE001 - unknown recorded, never raised
        return {"fixture_id": fixture.get("fixture_id"), "outcome": "UNKNOWN",
                "formation": "UNKNOWN", "expected": fixture.get("expected_formation"),
                "diagnostics": [str(e)]}
    expected = fixture.get("expected_formation", "FORMED")
    if formation == "UNKNOWN":
        result = "UNKNOWN"
    elif formation == expected:
        result = "PASS"
    else:
        result = "FAIL"
    return {"fixture_id": fixture.get("fixture_id"), "outcome": result,
            "formation": formation, "expected": expected, "diagnostics": []}


def run_research_experiment(experiment_id: str, package: Dict[str, Any],
                            rule: Dict[str, Any], fixtures: List[Dict[str, Any]],
                            profile: str = "PARASHARI_CLASSICAL") -> Dict[str, Any]:
    outcomes = [evaluate_fixture(rule, fx) for fx in sorted(fixtures, key=lambda f: f.get("fixture_id", ""))]
    matched = sum(1 for o in outcomes if o["outcome"] == "PASS")
    mismatched = sum(1 for o in outcomes if o["outcome"] == "FAIL")
    unknowns = sum(1 for o in outcomes if o["outcome"] == "UNKNOWN")
    result = {
        "experiment_id": experiment_id,
        "package_id": package.get("package_id", ""),
        "package_version": package.get("package_version", ""),
        "rule_id": rule.get("rule_id", ""),
        "rule_version": rule.get("rule_version", ""),
        "profile": profile,
        "fixtures_tested": len(outcomes),
        "observed_match_count": matched,
        "observed_mismatch_count": mismatched,
        "unknown_count": unknowns,
        "conflict_count": 0,
        "outcomes": outcomes,
        "unknowns": sorted([o["fixture_id"] for o in outcomes if o["outcome"] == "UNKNOWN"]),
        "conflicts": [],
        "evidence": [],
        "provenance": {"package_fingerprint": package.get("fingerprint", ""),
                       "rule_fingerprint": fingerprint_of(rule), "profile": profile},
        "summary": {"fixtures_tested": len(outcomes), "matches": matched,
                    "mismatches": mismatched, "unknowns": unknowns},
    }
    result["fingerprint"] = fingerprint_of({k: v for k, v in result.items() if k != "fingerprint"})
    return result
