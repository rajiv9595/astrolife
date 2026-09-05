"""
Phase 5G — Dasha pipeline: calculate_jaimini_dasha(chart_facts,
jaimini_facts, profile) -> JaiminiDashaResult (validated, with evidence
nodes/edges attached under validation metadata).
"""
from __future__ import annotations
from typing import Any, Optional

from .calculator import calculate_jaimini_dasha as _calculate
from .evidence import dasha_evidence_nodes, dasha_evidence_edges
from .models import JaiminiDashaResult
from .profile import JaiminiDashaProfile
from .validators import validate_dasha_result


def calculate_jaimini_dasha(
    chart_facts: Any,
    jaimini_facts: Optional[Any] = None,
    profile: Optional[JaiminiDashaProfile] = None,
) -> JaiminiDashaResult:
    if profile is None:
        profile = JaiminiDashaProfile()
    result = _calculate(chart_facts, jaimini_facts, profile)
    violations = validate_dasha_result(result, profile.days_per_year)
    result.validation = {
        **result.validation,
        "violations": violations,
        "valid": len(violations) == 0,
        "evidence_nodes": dasha_evidence_nodes(result) if result.status == "COMPUTED" else [],
        "evidence_edges": dasha_evidence_edges(result) if result.status == "COMPUTED" else [],
    }
    return result
