"""
Phase 5F — structured Jaimini evidence graph.

Chain: ChartFact (DIRECT_FACT) → JaiminiFact (DERIVED_FACT) → RuleCondition →
RuleResult (RULE_DERIVED). Node IDs are stable deterministic strings (no
timestamps, no random IDs); nodes/edges are emitted in sorted order so
serialization is byte-stable.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

DIRECT_FACT = "DIRECT_FACT"
DERIVED_FACT = "DERIVED_FACT"
RULE_DERIVED = "RULE_DERIVED"


class EvidenceNode(BaseModel):
    node_id: str
    tier: str
    label: str
    value: Any = None
    source: str = ""


class EvidenceEdge(BaseModel):
    from_id: str
    to_id: str
    relation: str = "supports"


class JaiminiEvidenceGraph(BaseModel):
    nodes: List[EvidenceNode] = Field(default_factory=list)
    edges: List[EvidenceEdge] = Field(default_factory=list)

    def node_ids(self) -> List[str]:
        return [n.node_id for n in self.nodes]


def _d1_sign(chart_facts: Any, planet: str) -> Optional[str]:
    pdata = chart_facts.planets.get(planet)
    return pdata.sign.name if pdata is not None else None


def _d9_sign(varga_facts: Dict[str, Any], planet: str) -> Optional[str]:
    entry = ((varga_facts or {}).get("planets", {}).get(planet) or {}).get("D9")
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry.get("sign")
    return getattr(entry, "sign", None)


def build_evidence_graph(
    chart_facts: Any,
    jaimini_facts: Any,
    varga_facts: Dict[str, Any],
    rule_results: List[Any],
) -> JaiminiEvidenceGraph:
    """Build the full evidence graph from canonical facts + rule outcomes."""
    nodes: Dict[str, EvidenceNode] = {}
    edges: List[Tuple[str, str, str]] = []

    def add(node: EvidenceNode) -> None:
        nodes[node.node_id] = node

    def link(a: str, b: str, rel: str = "supports") -> None:
        edges.append((a, b, rel))

    # Tier 1: D1 chart facts (DIRECT_FACT)
    asc_sign = chart_facts.ascendant.sign.name
    add(EvidenceNode(node_id="d1:lagna", tier=DIRECT_FACT, label="D1 Lagna sign",
                     value=asc_sign, source="ChartFacts.ascendant"))
    for pname in sorted(chart_facts.planets.keys()):
        sign = _d1_sign(chart_facts, pname)
        nid = f"d1:planet:{pname}:sign"
        add(EvidenceNode(node_id=nid, tier=DIRECT_FACT, label=f"D1 sign of {pname}",
                         value=sign, source="ChartFacts.planets"))
        link("d1:lagna", nid, "co-chart-fact")

    # Tier 2: Jaimini derived facts (DERIVED_FACT)
    for code in sorted(jaimini_facts.chara_karakas.karakas.keys()):
        item = jaimini_facts.chara_karakas.karakas[code]
        nid = f"karaka:{code}"
        add(EvidenceNode(node_id=nid, tier=DERIVED_FACT,
                         label=f"{code} = {item.planet} ({item.degree_in_sign:.4f}° in {item.sign})",
                         value={"planet": item.planet, "sign": item.sign,
                                "degree": item.degree_in_sign},
                         source="JaiminiFacts.chara_karakas"))
        link(f"d1:planet:{item.planet}:sign", nid, "derives")
    for h in sorted(jaimini_facts.arudha_padas.keys()):
        pada = jaimini_facts.arudha_padas[h]
        nid = f"pada:{pada.pada_code}:final"
        add(EvidenceNode(node_id=nid, tier=DERIVED_FACT,
                         label=f"{pada.pada_code} = {pada.final_sign} "
                               f"(src {pada.source_sign}/{pada.house_lord} in {pada.lord_sign}, "
                               f"raw {pada.raw_projected_sign}, exc={pada.exception_applied is not None})",
                         value={"final": pada.final_sign, "source": pada.source_sign,
                                "lord": pada.house_lord, "lord_sign": pada.lord_sign,
                                "raw": pada.raw_projected_sign,
                                "exception": pada.exception_applied},
                         source="JaiminiFacts.arudha_padas"))
        link(f"d1:planet:{pada.house_lord}:sign", nid, "derives")
    kak = jaimini_facts.karakamsha
    add(EvidenceNode(node_id="karakamsha:sign", tier=DERIVED_FACT,
                     label=f"Karakamsha = {kak.karakamsha_sign} (AK {kak.atmakaraka_planet} D9)",
                     value=kak.karakamsha_sign, source="JaiminiFacts.karakamsha"))
    add(EvidenceNode(node_id="swamsa:lagna", tier=DERIVED_FACT,
                     label=f"Swamsa = {kak.swamsa_navamsha_lagna_sign} (D9 Lagna)",
                     value=kak.swamsa_navamsha_lagna_sign, source="JaiminiFacts.karakamsha"))
    link("karakamsha:sign", "swamsa:lagna", "tracked-separately")
    for pname in sorted(chart_facts.planets.keys()):
        d9s = _d9_sign(varga_facts, pname)
        if d9s is not None:
            add(EvidenceNode(node_id=f"d9:planet:{pname}:sign", tier=DIRECT_FACT,
                             label=f"D9 sign of {pname}", value=d9s,
                             source="varga_facts.D9"))

    # Tier 3: rule conditions + results (RULE_DERIVED)
    for res in sorted(rule_results, key=lambda r: r.rule_id):
        cond_id = f"rule:{res.rule_id}:formation"
        res_id = f"rule:{res.rule_id}:result"
        conds = "; ".join(e.condition for e in (res.formation_evidence or []))
        add(EvidenceNode(node_id=cond_id, tier=RULE_DERIVED,
                         label=f"{res.rule_id} conditions: {conds}",
                         value={"passed": [e.passed for e in (res.formation_evidence or [])]},
                         source="JaiminiRuleResult.formation_evidence"))
        add(EvidenceNode(node_id=res_id, tier=RULE_DERIVED,
                         label=f"{res.rule_id} = {'FORMED' if res.formed else 'NOT_FORMED'}"
                               + ("" if res.formation_status else ""),
                         value={"formed": res.formed,
                                "formation_status": res.formation_status.value
                                if hasattr(res.formation_status, "value") else str(res.formation_status),
                                "cancellation": res.cancellation_status.value
                                if hasattr(res.cancellation_status, "value") else str(res.cancellation_status),
                                "mitigation": res.mitigation_status.value
                                if hasattr(res.mitigation_status, "value") else str(res.mitigation_status)},
                         source="JaiminiRuleResult"))
        link(cond_id, res_id, "evaluates-to")
        for dep in sorted(res.dependencies or []):
            if dep == "JaiminiFacts.chara_karakas":
                for code in sorted(jaimini_facts.chara_karakas.karakas.keys()):
                    link(f"karaka:{code}", cond_id, "feeds")
            elif dep == "JaiminiFacts.arudha_padas":
                for h in sorted(jaimini_facts.arudha_padas.keys()):
                    link(f"pada:{jaimini_facts.arudha_padas[h].pada_code}:final", cond_id, "feeds")
            elif dep == "JaiminiFacts.upapada":
                link("pada:A12:final", cond_id, "feeds")
            elif dep == "JaiminiFacts.karakamsha":
                link("karakamsha:sign", cond_id, "feeds")
                link("swamsa:lagna", cond_id, "feeds")
            elif dep == "varga_facts.D9":
                for pname in sorted(chart_facts.planets.keys()):
                    if f"d9:planet:{pname}:sign" in nodes:
                        link(f"d9:planet:{pname}:sign", cond_id, "feeds")
            elif dep == "ChartFacts.planets":
                for pname in sorted(chart_facts.planets.keys()):
                    link(f"d1:planet:{pname}:sign", cond_id, "feeds")
            elif dep == "JaiminiFacts.rashi_drishti":
                link("d1:lagna", cond_id, "context")

    ordered_nodes = [nodes[k] for k in sorted(nodes)]
    ordered_edges = sorted(edges)
    return JaiminiEvidenceGraph(
        nodes=ordered_nodes,
        edges=[EvidenceEdge(from_id=a, to_id=b, relation=r) for (a, b, r) in ordered_edges],
    )
