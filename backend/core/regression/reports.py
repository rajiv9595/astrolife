"""
Phase 10 — reports + manifest + public pipeline API.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .runner import SuiteReport

MANIFEST = [
    ("d1_golden", "CANONICAL"), ("d1_invariants", "CANONICAL"),
    ("synthetic_ascendants", "CANONICAL"), ("varga_suite", "CANONICAL"),
    ("varga_boundaries", "CANONICAL"), ("d9_exhaustive", "CANONICAL"),
    ("d10_exhaustive", "CANONICAL"), ("d60_full", "CANONICAL"),
    ("panchanga", "CANONICAL"), ("vimshottari", "CANONICAL"),
    ("chara_dasha", "CANONICAL"), ("strength", "CANONICAL"),
    ("yoga", "CANONICAL"), ("dosha", "CANONICAL"), ("jaimini", "CANONICAL"),
    ("jaimini_rules", "CANONICAL"), ("dynamic_rules", "CANONICAL"),
    ("evidence", "CANONICAL"), ("research", "CANONICAL"), ("agents", "CANONICAL"),
    ("prediction", "CANONICAL"), ("metamorphic", "CANONICAL"),
    ("cross_layer", "CANONICAL"), ("fingerprints", "CANONICAL"),
    ("mutation", "CANONICAL"), ("security", "CANONICAL"),
    ("api_contracts", "CANONICAL"), ("snapshots", "CANONICAL"),
    ("determinism", "CANONICAL"), ("unknown_invalid", "CANONICAL"),
    ("tradition_firewall", "CANONICAL"), ("profile_firewall", "CANONICAL"),
    ("immutability", "CANONICAL"),
]


def build_report(report: SuiteReport, layer_of: Dict[str, str]) -> Dict[str, Any]:
    rd = report.root_vs_derived(layer_of)
    return {"total": len(report.results), "passed": report.passed,
            "failed": report.failed,
            "failures": [{"golden_id": r.golden_id, "expected": r.expected,
                          "actual": r.actual, "difference": r.difference,
                          "class": r.failure_class} for r in report.failures()],
            "first_divergent_layer": rd["first_divergent_layer"],
            "root_count": len(rd["roots"]), "derived_count": len(rd["derived"])}


def manifest() -> List[Dict[str, str]]:
    return [{"suite": s, "layer": l} for s, l in MANIFEST]
