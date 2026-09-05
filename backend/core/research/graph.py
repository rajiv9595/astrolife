"""
Phase 9 — research graph (extends concepts, never replaces Phase 6D
EvidenceGraph). Deterministic ordering + fingerprints.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .models import fingerprint_of

NODE_TYPES = ("RESEARCH_PACKAGE", "RESEARCH_RULE", "HYPOTHESIS", "EXPERIMENT",
              "FIXTURE", "OBSERVATION", "COMPARISON", "PROMOTION_REQUEST")
EDGE_TYPES = ("TESTS", "USES", "SUPPORTS", "CONTRADICTS", "COMPARES",
              "DEPENDS_ON", "DERIVED_FROM", "PROPOSES", "PROMOTES")


def build_research_graph(package: Dict[str, Any],
                         experiments: List[Dict[str, Any]] | None = None,
                         comparisons: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    nodes: List[Dict[str, str]] = [
        {"id": package.get("package_id", ""), "type": "RESEARCH_PACKAGE"}]
    for r in sorted(package.get("rules", []), key=lambda x: x.get("rule_id", "")):
        nodes.append({"id": r.get("rule_id", ""), "type": "RESEARCH_RULE"})
    for fx in sorted(package.get("fixtures", []), key=lambda x: x.get("fixture_id", "")):
        nodes.append({"id": fx.get("fixture_id", ""), "type": "FIXTURE"})
    for e in sorted(experiments or [], key=lambda x: x.get("experiment_id", "")):
        nodes.append({"id": e.get("experiment_id", ""), "type": "EXPERIMENT"})
    for c in sorted(comparisons or [], key=lambda x: x.get("comparison_id", "")):
        nodes.append({"id": c.get("comparison_id", ""), "type": "COMPARISON"})
    nodes = sorted(nodes, key=lambda n: (n["type"], n["id"]))
    edges: List[Dict[str, str]] = []
    for r in sorted(package.get("rules", []), key=lambda x: x.get("rule_id", "")):
        edges.append({"from": package.get("package_id", ""), "to": r.get("rule_id", ""), "type": "PROPOSES"})
        for dep in sorted((r.get("dependencies", {}) or {}).get("rule_dependencies", []) or []):
            edges.append({"from": r.get("rule_id", ""), "to": dep, "type": "DEPENDS_ON"})
    for e in sorted(experiments or [], key=lambda x: x.get("experiment_id", "")):
        edges.append({"from": e.get("experiment_id", ""), "to": e.get("rule_id", ""), "type": "TESTS"})
    edges = sorted(edges, key=lambda e: (e["from"], e["to"], e["type"]))
    g = {"nodes": nodes, "edges": edges}
    g["fingerprint"] = fingerprint_of(g)
    return g


def get_research_graph(package: Dict[str, Any], **kw: Any) -> Dict[str, Any]:
    return build_research_graph(package, kw.get("experiments"), kw.get("comparisons"))
