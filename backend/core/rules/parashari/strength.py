"""
Phase 5B — Yoga strength evaluation (separate from formation).

Uses the validated Phase 4 strength engine via RuleContext:
dignity, Shadbala ratio, Kendra/Trikona placement, D9 dignity as a
strength modifier ONLY (never formation). No weighted YogaScore.

Rule (documented, no hidden weights):
  For each relevant planet count explicit factors:
    DIGNITY_STRONG: exalted / own sign / moolatrikona
    SHADBALA_STRONG: ratio >= 1.0
    HOUSE_STRONG: in Kendra or Trikona from Lagna
    D9_STRONG: D9 sign dignity own/exalted (modifier, recorded separately)
  Yoga strength:
    STRONG: >=2 planets strong OR 1 planet with all three D1 factors,
            where "planet strong" = >=2 of the three D1 factors.
    MODERATE: at least one D1 factor present on a relevant planet.
    WEAK: none of the D1 factors.
D9 strength is reported in evidence but NEVER promotes WEAK to STRONG
on its own (anti-shortcut rule).
"""
from __future__ import annotations
from typing import Dict, List, Tuple

from ..models import Evidence
from ..enums import EvidenceType, StrengthStatus
from .structural import house_of


def _planet_factors(ctx, planet: str) -> Dict[str, bool]:
    dignity_strong = bool(
        ctx.is_exalted(planet) or ctx.is_own_sign(planet) or ctx.is_moolatrikona(planet)
    )
    ratio = ctx.get_shadbala_ratio(planet)
    shadbala_strong = bool(ratio is not None and ratio >= 1.0)
    h = house_of(ctx, planet)
    house_strong = bool(h is not None and h in (1, 4, 7, 10, 5, 9))
    d9_sign = None
    d9_strong = False
    try:
        d9_sign = ctx.get_varga_sign(planet, 9)
    except Exception:
        d9_sign = None
    if d9_sign:
        lord_map = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
            "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
            "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
        }
        exalt = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
                 "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
                 "Saturn": "Libra"}
        d9_strong = bool(lord_map.get(d9_sign) == planet or exalt.get(planet) == d9_sign)
    return {
        "DIGNITY_STRONG": dignity_strong,
        "SHADBALA_STRONG": shadbala_strong,
        "HOUSE_STRONG": house_strong,
        "D9_STRONG": d9_strong,
        "D9_SIGN": d9_sign,
        "SHADBALA_RATIO": ratio,
    }


def evaluate_yoga_strength(ctx, relevant_planets: List[str],
                           yoga_name: str = "") -> Tuple[StrengthStatus, List[Evidence]]:
    """Grade yoga strength. Returns (status, evidence). Deterministic."""
    evidence: List[Evidence] = []
    if not relevant_planets:
        return StrengthStatus.WEAK, evidence
    strong_planets = 0
    any_factor = False
    fully_strong_single = False
    for planet in relevant_planets:
        f = _planet_factors(ctx, planet)
        d1_count = sum([f["DIGNITY_STRONG"], f["SHADBALA_STRONG"], f["HOUSE_STRONG"]])
        if d1_count >= 2:
            strong_planets += 1
        if d1_count >= 1:
            any_factor = True
        if d1_count == 3:
            fully_strong_single = True
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_STRENGTH,
            subject=f"{planet} strength for {yoga_name}" if yoga_name else f"{planet} strength",
            value={"dignity_strong": f["DIGNITY_STRONG"],
                   "shadbala_ratio": f["SHADBALA_RATIO"],
                   "shadbala_strong": f["SHADBALA_STRONG"],
                   "house": house_of(ctx, planet),
                   "house_strong": f["HOUSE_STRONG"]},
            expected="D1 factors: dignity/shadbala/house",
            actual=f"{d1_count}/3 D1 factors",
            source="StrengthReport",
            significance=f"{planet}: {d1_count}/3 strength factors",
            details={"dignity": ctx.get_dignity_category(planet),
                     "d9_sign": f["D9_SIGN"], "d9_strong_modifier_only": f["D9_STRONG"]},
        ))
    if strong_planets >= 2 or fully_strong_single:
        return StrengthStatus.STRONG, evidence
    if any_factor:
        return StrengthStatus.MODERATE, evidence
    return StrengthStatus.WEAK, evidence
