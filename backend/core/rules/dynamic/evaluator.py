"""
Phase 6A — data-only evaluator for dynamic rules.

A caller-supplied FactResolver maps declared fact paths to values; anything
undeclared is rejected, anything missing yields UNKNOWN (never FALSE).
Formation / cancellation / mitigation trees evaluate independently to
TRUE | FALSE | UNKNOWN with per-node evidence. No code execution anywhere.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .dsl import LOGICAL_OPS, PRIMITIVES
from .schema import ConditionNode, DynamicRuleDefinition

MISSING = object()
TRUE, FALSE, UNKNOWN = "TRUE", "FALSE", "UNKNOWN"

FactResolver = Callable[[str], Any]


class EvidenceItem(BaseModel):
    node: str
    op: str
    detail: str
    outcome: str
    model_config = {"frozen": True}


class TreeOutcome(BaseModel):
    outcome: str
    evidence: List[EvidenceItem] = Field(default_factory=list)
    model_config = {"frozen": True}


class DynamicRuleOutcome(BaseModel):
    rule_id: str
    rule_version: str
    formation: str
    cancellation: str
    mitigation: str
    evidence: List[EvidenceItem] = Field(default_factory=list)
    diagnostics: List[str] = Field(default_factory=list)
    model_config = {"frozen": True}


def _resolve(resolver: FactResolver, path: str) -> Any:
    try:
        value = resolver(path)
    except Exception:
        return MISSING
    return MISSING if value is None else value


def _eval_primitive(op: str, params: Dict[str, Any], resolver: FactResolver) -> Tuple[str, str]:
    """Returns (outcome, detail). Each primitive documents its fact paths."""
    g = lambda p: _resolve(resolver, p)
    P = params
    if op == "planet_in_sign":
        v = g(f"natal.{P['planet']}.sign")
        return (UNKNOWN, "missing natal sign") if v is MISSING else (TRUE if v == P["sign"] else FALSE, f"{P['planet']} sign={v}")
    if op == "planet_in_house":
        v = g(f"natal.{P['planet']}.house")
        return (UNKNOWN, "missing natal house") if v is MISSING else (TRUE if v == P["house"] else FALSE, f"{P['planet']} house={v}")
    if op == "planet_in_varga_sign":
        v = g(f"varga.{P['varga']}.{P['planet']}")
        return (UNKNOWN, "missing varga fact") if v is MISSING else (TRUE if v == P["sign"] else FALSE, f"{P['planet']} {P['varga']}={v}")
    if op == "planet_owns_house":
        v = g(f"houses.{P['house']}.lord")
        return (UNKNOWN, "missing house lord") if v is MISSING else (TRUE if v == P["planet"] else FALSE, f"lord({P['house']})={v}")
    if op == "planets_conjunct":
        a, b = g(f"natal.{P['a']}.sign"), g(f"natal.{P['b']}.sign")
        if a is MISSING or b is MISSING:
            return UNKNOWN, "missing natal sign"
        return (TRUE if a == b else FALSE, f"{P['a']}={a} {P['b']}={b}")
    if op == "planets_aspect":
        v = g(f"aspects.{P['a']}")
        if v is MISSING:
            return UNKNOWN, "missing aspect map"
        return (TRUE if P["b"] in (v or []) else FALSE, f"{P['a']} aspects {v}")
    if op == "rashi_drishti":
        v = g("jaimini.drishti")
        if v is MISSING:
            return UNKNOWN, "missing drishti map"
        targets = (v or {}).get(P["from_sign"], [])
        return (TRUE if P["to_sign"] in targets else FALSE, f"{P['from_sign']}→{targets}")
    if op == "karaka_equals":
        v = g(f"jaimini.karaka.{P['karaka']}")
        return (UNKNOWN, "missing karaka") if v is MISSING else (TRUE if v == P["planet"] else FALSE, f"{P['karaka']}={v}")
    if op == "pada_equals":
        v = g(f"jaimini.pada.{P['house']}")
        return (UNKNOWN, "missing pada") if v is MISSING else (TRUE if v == P["sign"] else FALSE, f"A{P['house']}={v}")
    if op in ("planet_exalted", "planet_debilitated", "planet_in_own_sign", "planet_in_moolatrikona"):
        want = {"planet_exalted": "EXALTED", "planet_debilitated": "DEBILITATED",
                "planet_in_own_sign": "OWN", "planet_in_moolatrikona": "MOOLATRIKONA"}[op]
        v = g(f"dignity.{P['planet']}")
        return (UNKNOWN, "missing dignity") if v is MISSING else (TRUE if v == want else FALSE, f"{P['planet']} dignity={v}")
    if op == "house_is_kendra":
        return (TRUE if P["house"] in (1, 4, 7, 10) else FALSE, f"house {P['house']}")
    if op == "house_is_trikona":
        return (TRUE if P["house"] in (1, 5, 9) else FALSE, f"house {P['house']}")
    if op == "lord_in_house":
        lord = g(f"houses.{P['house']}.lord")
        if lord is MISSING:
            return UNKNOWN, "missing house lord"
        v = g(f"natal.{lord}.house")
        if v is MISSING:
            return UNKNOWN, "missing lord house"
        return (TRUE if v == P["target_house"] else FALSE, f"lord({P['house']})={lord} in {v}")
    if op == "lord_of_house":
        v = g(f"houses.{P['house']}.lord")
        return (UNKNOWN, "missing house lord") if v is MISSING else (TRUE if v == P["planet"] else FALSE, f"lord({P['house']})={v}")
    if op == "dasha_active":
        v = g(f"dasha.{P['system']}.active_sign")
        return (UNKNOWN, "missing dasha") if v is MISSING else (TRUE if v == P["sign"] else FALSE, f"{P['system']} active={v}")
    if op == "transit_in_sign":
        v = g(f"transit.{P['planet']}.sign")
        return (UNKNOWN, "missing transit") if v is MISSING else (TRUE if v == P["sign"] else FALSE, f"transit {P['planet']}={v}")
    if op == "transit_conjunct_natal":
        a, b = g(f"transit.{P['transit_planet']}.sign"), g(f"natal.{P['natal_planet']}.sign")
        if a is MISSING or b is MISSING:
            return UNKNOWN, "missing transit/natal sign"
        return (TRUE if a == b else FALSE, f"transit {P['transit_planet']}={a} natal {P['natal_planet']}={b}")
    if op == "strength_threshold":
        v = g(f"strength.{P['metric']}.{P['planet']}")
        if v is MISSING:
            return UNKNOWN, "missing strength"
        try:
            ok = float(v) >= float(P["min"])
        except (TypeError, ValueError):
            return UNKNOWN, "non-numeric strength"
        return (TRUE if ok else FALSE, f"{P['metric']}({P['planet']})={v} >= {P['min']}")
    if op == "rule_formed":
        v = _resolve(resolver, f"rule:{P['rule_id']}")
        if v is MISSING:
            return UNKNOWN, "missing rule result"
        return ({"FORMED": TRUE, "NOT_FORMED": FALSE}.get(v, UNKNOWN), f"{P['rule_id']}={v}")
    return UNKNOWN, f"unknown primitive {op}"


def evaluate_tree(node: ConditionNode, resolver: FactResolver, path: str = "root") -> TreeOutcome:
    ev: List[EvidenceItem] = []
    if node.op in LOGICAL_OPS:
        kids = [evaluate_tree(c, resolver, f"{path}.{i}") for i, c in enumerate(node.children)]
        for k in kids:
            ev.extend(k.evidence)
        outs = [k.outcome for k in kids]
        if node.op == "ALL":
            res = FALSE if FALSE in outs else (UNKNOWN if UNKNOWN in outs else TRUE)
        elif node.op == "ANY":
            res = TRUE if TRUE in outs else (UNKNOWN if UNKNOWN in outs else FALSE)
        elif node.op == "NOT":
            res = {TRUE: FALSE, FALSE: TRUE, UNKNOWN: UNKNOWN}[outs[0]] if outs else UNKNOWN
        else:
            need = node.n if node.n is not None else 0
            t, u = outs.count(TRUE), outs.count(UNKNOWN)
            if node.op == "EXACTLY_N":
                res = TRUE if t == need and u == 0 else (UNKNOWN if u > 0 else FALSE)
            elif node.op == "AT_LEAST_N":
                res = TRUE if t >= need else (UNKNOWN if t + u >= need else FALSE)
            else:  # AT_MOST_N
                res = TRUE if t <= need and u == 0 else (UNKNOWN if u > 0 and t <= need else FALSE)
        ev.append(EvidenceItem(node=path, op=node.op, detail=f"children={outs}", outcome=res))
        return TreeOutcome(outcome=res, evidence=ev)
    outcome, detail = _eval_primitive(node.op, node.params, resolver)
    ev.append(EvidenceItem(node=path, op=node.op, detail=detail, outcome=outcome))
    return TreeOutcome(outcome=outcome, evidence=ev)


def evaluate_rule(rule: DynamicRuleDefinition, resolver: FactResolver) -> DynamicRuleOutcome:
    diags: List[str] = []

    def guarded(path: str) -> Any:
        if path.startswith("rule:"):
            if path[len("rule:"):] not in (rule.dependencies.rule_dependencies or []):
                diags.append(f"UNDECLARED_ACCESS:{path}")
                return MISSING
            return resolver(path)
        # fact paths must be covered by a declared prefix
        if not any(path == d or path.startswith(d.rstrip("*")) for d in rule.dependencies.input_facts):
            diags.append(f"UNDECLARED_ACCESS:{path}")
            return MISSING
        return resolver(path)

    def run(tree, label):
        if tree is None:
            return None
        return evaluate_tree(tree, guarded, label)

    f_tree = run(rule.semantics.formation, "formation")
    c_tree = run(rule.semantics.cancellation, "cancellation")
    m_tree = run(rule.semantics.mitigation, "mitigation")

    formation = {"TRUE": "FORMED", "FALSE": "NOT_FORMED"}.get(
        f_tree.outcome if f_tree else "FALSE", "UNKNOWN")
    cancellation = {"TRUE": "CANCELLED", "FALSE": "NOT_CANCELLED"}.get(
        c_tree.outcome if c_tree else "FALSE", "UNKNOWN")
    mitigation = {"TRUE": "MITIGATED", "FALSE": "NOT_MITIGATED"}.get(
        m_tree.outcome if m_tree else "FALSE", "UNKNOWN")

    evidence: List[EvidenceItem] = []
    for t in (f_tree, c_tree, m_tree):
        if t is not None:
            evidence.extend(t.evidence)
    return DynamicRuleOutcome(
        rule_id=rule.identity.rule_id, rule_version=rule.identity.rule_version,
        formation=formation, cancellation=cancellation, mitigation=mitigation,
        evidence=evidence, diagnostics=sorted(set(diags)),
    )
