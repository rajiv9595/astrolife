"""
Phase 9 — applicability matrix reusing Phase 6E semantics:
RULE x FIXTURE x TRADITION x PROFILE -> APPLICABLE/NOT_APPLICABLE/UNKNOWN/INVALID.
"""
from __future__ import annotations

from typing import Any, Dict, List


def rule_applicable(rule: Dict[str, Any], tradition: str, profile: str) -> str:
    appl = rule.get("applicability", {}) or {}
    trads = appl.get("traditions", [])
    profs = appl.get("profiles", [])
    if trads and tradition not in trads:
        return "NOT_APPLICABLE"
    if profs and profile not in profs:
        return "NOT_APPLICABLE"
    if rule.get("lifecycle_status") in ("REJECTED", "ARCHIVED"):
        return "INVALID"
    if not trads and not profs:
        return "UNKNOWN"
    return "APPLICABLE"


def applicability_matrix(rules: List[Dict[str, Any]], fixtures: List[Dict[str, Any]],
                         traditions: List[str], profiles: List[str]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for r in sorted(rules, key=lambda x: x.get("rule_id", "")):
        for fx in sorted(fixtures, key=lambda x: x.get("fixture_id", "")):
            for t in sorted(traditions):
                for p in sorted(profiles):
                    rows.append({
                        "rule_id": r.get("rule_id"),
                        "fixture_id": fx.get("fixture_id"),
                        "tradition": t,
                        "profile": p,
                        "state": rule_applicable(r, t, p),
                    })
    return {"rows": rows, "count": len(rows)}
