"""
Phase 5G — Dasha evidence (DASHA_DERIVED tier, stable deterministic IDs).
Complements (never rewrites) the 5F yoga RULE_DERIVED tier.
"""
from __future__ import annotations
from typing import Any, Dict, List

DASHA_DERIVED = "DASHA_DERIVED"


def dasha_evidence_nodes(result: Any) -> List[Dict[str, Any]]:
    nodes: List[Dict[str, Any]] = [
        {"node_id": "dasha:start", "tier": DASHA_DERIVED,
         "label": f"Starting sign = {result.starting_sign} ({result.direction})",
         "source": "JaiminiDashaResult.starting_sign_evidence"},
    ]
    for p in result.periods:
        nodes.append({
            "node_id": f"dasha:period:{p.period_id}", "tier": DASHA_DERIVED,
            "label": f"{p.sign} {p.duration_years}g {p.start_utc_iso}->{p.end_utc_iso}",
            "source": "JaiminiDashaResult.periods",
        })
        for c in p.antardashas:
            nodes.append({
                "node_id": f"dasha:period:{c.period_id}", "tier": DASHA_DERIVED,
                "label": f"{c.sign} {c.duration_years:.4f}g in {p.sign}",
                "source": "JaiminiDashaResult.periods.antardashas",
            })
    return sorted(nodes, key=lambda n: n["node_id"])


def dasha_evidence_edges(result: Any) -> List[Dict[str, str]]:
    edges = [{"from_id": "d1:lagna", "to_id": "dasha:start", "relation": "derives"}]
    for p in result.periods:
        edges.append({"from_id": "dasha:start", "to_id": f"dasha:period:{p.period_id}",
                      "relation": "sequences"})
        for c in p.antardashas:
            edges.append({"from_id": f"dasha:period:{p.period_id}",
                          "to_id": f"dasha:period:{c.period_id}", "relation": "subdivides"})
    return sorted(edges, key=lambda e: (e["from_id"], e["to_id"]))
