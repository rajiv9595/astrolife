"""
Phase 6B — canonical dynamic rule evaluation engine.

evaluate_dynamic_rule(rule, context) -> DynamicRuleResult
evaluate_dynamic_rule_by_id(rule_id, version, context, registry)
evaluate_many(rules, context, tradition=None)  (conflict-aware, report-only)
audit_dynamic_rule_evaluation(result, rule)    (undeclared/missing/violations)

No astronomy, no wall clock, no scores. UNKNOWN/INVALID never coerce to FALSE.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .bindings import required_paths
from .context import DynamicEvaluationContext
from .evaluator import evaluate_rule
from .evaluator import MISSING as _EVAL_MISSING
from .namespace import namespace_of
from .registry import DynamicRuleRegistry
from .resolver import CanonicalFactResolver, MISSING, INVALID, UNAVAILABLE, RESOLVED
from .results import DynamicRuleResult
from .schema import ConditionNode, DynamicRuleDefinition
from .validators import FIREWALL, validate_rule


def _tree_paths(node: Optional[ConditionNode]) -> List[str]:
    if node is None:
        return []
    out: List[str] = list(required_paths(node.op, node.params))
    for c in node.children or []:
        out.extend(_tree_paths(c))
    return out


def _needed_paths(rule: DynamicRuleDefinition) -> List[str]:
    paths: List[str] = []
    for tree in (rule.semantics.formation, rule.semantics.cancellation,
                 rule.semantics.mitigation):
        paths.extend(_tree_paths(tree))
    # deduplicate, deterministic order
    return sorted(set(paths))


def _declared_paths(rule: DynamicRuleDefinition) -> List[str]:
    return sorted(set(rule.dependencies.input_facts)
                  | {f"rule:{r}" for r in rule.dependencies.rule_dependencies})


def _covered(needed: str, declared: List[str]) -> bool:
    if needed in declared:
        return True
    return any(needed == d or needed.startswith(d.rstrip("*")) for d in declared)


def evaluate_dynamic_rule(rule: DynamicRuleDefinition,
                          context: DynamicEvaluationContext) -> DynamicRuleResult:
    # DEPENDENCY-code diagnostics (rule existence) are a registry-time concern:
    # the engine has no universe of rule IDs, so it enforces declaration
    # coverage itself and leaves existence checks to registry validation.
    diags = [f"{d.code}:{d.path}:{d.message}" for d in validate_rule(rule, set())
             if d.severity == "ERROR" and d.code != "DEPENDENCY"]
    needed = _needed_paths(rule)
    declared = _declared_paths(rule)
    uncovered = sorted(p for p in needed if not _covered(p, declared))
    if uncovered:
        return DynamicRuleResult(
            rule_id=rule.identity.rule_id, rule_version=rule.identity.rule_version,
            status="INVALID", formation="UNKNOWN", cancellation="UNKNOWN",
            mitigation="UNKNOWN", final_state="INVALID",
            diagnostics=sorted(diags + [f"UNDECLARED_DEPENDENCY:{p}" for p in uncovered]),
            evidence_paths=[], dependency_paths=declared,
            resolved_facts={}, unresolved_facts=needed,
            provenance=_provenance_of(rule), evaluation_profile="6B/1.0.0")

    resolver = CanonicalFactResolver(context)

    def bridge(path: str) -> Any:
        # Return the 6A MISSING sentinel for non-resolved facts so UNKNOWN
        # propagates per-tree (a FALSE sibling still decides ALL/ANY).
        res = resolver.resolve(path)
        if res.status != RESOLVED:
            return _EVAL_MISSING
        return res.value

    outcome = evaluate_rule(rule, bridge)

    # collect resolutions for evidence/dependency output (deterministic order)
    resolutions = {p: resolver.resolve(p) for p in needed}
    resolved = {p: r.value for p, r in sorted(resolutions.items()) if r.status == RESOLVED}
    unresolved = sorted(p for p, r in resolutions.items() if r.status != RESOLVED)
    status = {"FORMED": "FORMED", "NOT_FORMED": "NOT_FORMED"}.get(outcome.formation, "UNKNOWN")
    if outcome.cancellation == "CANCELLED":
        final_state = "FORMED_CANCELLED" if status == "FORMED" else status
    elif outcome.mitigation == "MITIGATED":
        final_state = "FORMED_MITIGATED" if status == "FORMED" else status
    else:
        final_state = status
    evidence_paths = sorted({e.node for e in outcome.evidence})
    return DynamicRuleResult(
        rule_id=rule.identity.rule_id, rule_version=rule.identity.rule_version,
        status=status, formation=outcome.formation, cancellation=outcome.cancellation,
        mitigation=outcome.mitigation, final_state=final_state,
        diagnostics=sorted(set(diags) | set(outcome.diagnostics)),
        evidence_paths=evidence_paths, dependency_paths=declared,
        resolved_facts=resolved, unresolved_facts=unresolved,
        provenance=_provenance_of(rule), evaluation_profile="6B/1.0.0")


def _provenance_of(rule: DynamicRuleDefinition) -> Dict[str, Any]:
    src = rule.provenance.source_reference
    return {"tradition": rule.classification.tradition,
            "system": rule.classification.system,
            "category": rule.classification.category,
            "source_reference": src.source_id or "UNVERIFIED",
            "verification_status": src.verification_status,
            "confidence": rule.provenance.confidence or "UNVERIFIED",
            "rule_version": rule.identity.rule_version,
            "schema_version": rule.schema_version}


def evaluate_dynamic_rule_by_id(rule_id: str, version: Optional[str],
                                context: DynamicEvaluationContext,
                                registry: DynamicRuleRegistry) -> DynamicRuleResult:
    rule = registry.get(rule_id, version)
    if rule is None:
        raise KeyError(f"Unknown rule {rule_id}@{version}")
    return evaluate_dynamic_rule(rule, context)


def evaluate_many(rules: List[DynamicRuleDefinition],
                  context: DynamicEvaluationContext,
                  tradition: Optional[str] = None) -> Tuple[List[DynamicRuleResult], List[Dict[str, Any]]]:
    """Evaluate optionally tradition-filtered rules; report conflicts without
    choosing winners. Conflict = same derived_facts key with differing
    FORMED/NOT_FORMED formation (UNKNOWN pairs excluded)."""
    selected = [r for r in sorted(rules, key=lambda r: (r.identity.rule_id, r.identity.rule_version))
                if tradition is None or r.classification.tradition == tradition]
    results = [evaluate_dynamic_rule(r, context) for r in selected]
    by_fact: Dict[str, List[DynamicRuleResult]] = {}
    for rule, res in zip(selected, results):
        for fact in rule.semantics.derived_facts or [f"rule:{rule.identity.rule_id}"]:
            by_fact.setdefault(fact, []).append(res)
    conflicts: List[Dict[str, Any]] = []
    for fact in sorted(by_fact):
        group = by_fact[fact]
        states = {r.formation for r in group if r.formation in ("FORMED", "NOT_FORMED")}
        if len(states) > 1:
            conflicts.append({"derived_fact": fact,
                              "parties": sorted(f"{r.rule_id}@{r.rule_version}={r.formation}" for r in group),
                              "traditions": sorted({r.provenance.get('tradition', '?') for r in group}),
                              "resolution": "REPORTED_ONLY"})
    return results, conflicts


def audit_dynamic_rule_evaluation(result: DynamicRuleResult,
                                  rule: DynamicRuleDefinition) -> List[str]:
    """Detect undeclared facts, missing deps, firewall breaches, inconsistencies."""
    findings: List[str] = []
    declared = _declared_paths(rule)
    needed = _needed_paths(rule)
    for p in needed:
        if not _covered(p, declared):
            findings.append(f"UNDECLARED_FACT:{p}")
    firewall = FIREWALL.get(rule.classification.tradition, set())
    ns_map = {"input_facts": None, "varga_dependencies": "varga",
              "dasha_dependencies": "dasha", "transit_dependencies": "transit",
              "strength_dependencies": "strength"}
    for lst_name, ns in ns_map.items():
        for dep in getattr(rule.dependencies, lst_name):
            check_ns = dep.split(".")[0] if ns is None else ns
            if check_ns not in firewall:
                findings.append(f"CROSS_SYSTEM_VIOLATION:{lst_name}:{dep}")
    for p in result.dependency_paths:
        if p not in declared:
            findings.append(f"DEPENDENCY_INCONSISTENCY:{p}")
    for p in declared:
        if p not in result.dependency_paths:
            findings.append(f"DEPENDENCY_DRIFT:{p}")
    if result.status == "UNKNOWN" and not result.unresolved_facts and not result.diagnostics:
        findings.append("UNKNOWN_WITHOUT_EXPLANATION")
    if result.status == "INVALID" and not result.diagnostics:
        findings.append("INVALID_WITHOUT_DIAGNOSTIC")
    return sorted(findings)
