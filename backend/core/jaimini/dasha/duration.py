"""
Phase 5G — duration calculation with explicit per-period evidence.
Rule: inclusive house-count from the period sign to its single-classical
lord in sequence direction; OWN_SIGN_TWELVE exception (lord in own sign
yields 12 years). No dignity adjustments in this profile.
"""
from __future__ import annotations
from typing import Any, Dict, Optional

from ..arudha import CLASSICAL_SIGN_LORDS, SIGNS
from .models import DashaDurationEvidence
from .sequence import FORWARD


def d1_sign_of(chart_facts: Any, planet: str) -> Optional[str]:
    pdata = chart_facts.planets.get(planet)
    return pdata.sign.name if pdata is not None else None


def inclusive_distance(from_sign: str, to_sign: str, direction: str) -> int:
    a, b = SIGNS.index(from_sign), SIGNS.index(to_sign)
    if direction == FORWARD:
        return ((b - a) % 12) + 1
    return ((a - b) % 12) + 1


def duration_for_sign(
    period_sign: str,
    planet_sign_map: Dict[str, str],
    direction: str,
) -> DashaDurationEvidence:
    lord = CLASSICAL_SIGN_LORDS[period_sign]
    lord_sign = planet_sign_map[lord]
    if lord_sign == period_sign:
        return DashaDurationEvidence(
            reference_sign=period_sign, lord=lord, lord_sign=lord_sign,
            distance_houses=1, direction=direction,
            exception="OWN_SIGN_TWELVE", duration_years=12.0,
        )
    dist = inclusive_distance(period_sign, lord_sign, direction)
    return DashaDurationEvidence(
        reference_sign=period_sign, lord=lord, lord_sign=lord_sign,
        distance_houses=dist, direction=direction,
        exception="NONE", duration_years=float(dist),
    )


def planet_sign_map_from(chart_facts: Any) -> Dict[str, str]:
    return {p: pdata.sign.name for p, pdata in chart_facts.planets.items()
            if pdata.sign.name in SIGNS}
