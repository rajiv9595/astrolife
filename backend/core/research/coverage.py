"""
Phase 9 — coverage analysis: required vs available facts/Vargas/Dasha/
Transit/Strength/Jaimini/rule deps. Missing coverage is UNKNOWN, not failure.
"""
from __future__ import annotations

from typing import Any, Dict, List

COVERAGE_KEYS = ("input_facts", "varga_dependencies", "dasha_dependencies",
                 "transit_dependencies", "strength_dependencies",
                 "jaimini_dependencies", "rule_dependencies")


def coverage_report(rule: Dict[str, Any], available: Dict[str, List[str]]) -> Dict[str, Any]:
    deps = rule.get("dependencies", {}) or {}
    out: Dict[str, Any] = {"rule_id": rule.get("rule_id")}
    for k in COVERAGE_KEYS:
        req = sorted(deps.get(k, []) or [])
        av = set(available.get(k, []) or [])
        out[f"required_{k}"] = req
        out[f"available_{k}"] = sorted(av)
        out[f"missing_{k}"] = sorted([x for x in req if x not in av])
    out["coverage_complete"] = all(len(out[f"missing_{k}"]) == 0 for k in COVERAGE_KEYS)
    return out
