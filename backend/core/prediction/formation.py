"""
Phase 8 — formation engine (§§6, 13).

Formation answers ONLY whether the event configuration exists in supplied
rule outcomes. Missing outcomes are UNKNOWN (never negative evidence).
Definitions with zero accepted-rule coverage yield INSUFFICIENT_RULE_COVERAGE.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .models import CONFLICTED, FORMED, NOT_FORMED, UNKNOWN, UNSUPPORTED


def evaluate_event_formation(definition: Any,
                             formation: List[Any]) -> Dict[str, Any]:
    """Returns {status, supporting, unknowns, conflicts, coverage}."""
    if not definition.required_rule_families:
        return {"status": UNSUPPORTED, "supporting": [], "unknowns": [],
                "conflicts": [],
                "coverage": "INSUFFICIENT_RULE_COVERAGE"}
    by_rule = {s.source_id: s for s in formation}
    supporting: List[str] = []
    unknowns: List[str] = []
    formed_count = 0
    not_formed_count = 0
    for rule_id in definition.required_rule_families:
        signal = by_rule.get(rule_id)
        if signal is None or signal.status == UNKNOWN:
            unknowns.append(rule_id)
            continue
        if signal.status == "FORMED":
            formed_count += 1
            supporting.append(rule_id)
        elif signal.status == CONFLICTED:
            unknowns.append(rule_id)
        else:
            not_formed_count += 1
    if definition.formation_policy == "ALL":
        if unknowns:
            status = UNKNOWN
        elif not_formed_count:
            status = NOT_FORMED
        else:
            status = FORMED
    else:
        if formed_count:
            status = FORMED
        elif unknowns:
            status = UNKNOWN
        else:
            status = NOT_FORMED
    return {"status": status, "supporting": sorted(supporting),
            "unknowns": sorted(unknowns), "conflicts": [],
            "coverage": "RULE_COVERAGE_OK"}
