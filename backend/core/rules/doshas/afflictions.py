"""
Generic Affliction Engine — Astrolife V2 Phase 5C

Reusable deterministic functions for evaluating planetary afflictions.
These are building blocks — NOT automatically named doshas.

Key principle: "Saturn aspects Moon" does NOT automatically mean
"Dosha X exists" unless a specific rule says so.

Components:
  1. Malefic conjunction
  2. Malefic aspect (Parashari)
  3. Combustion (planet near Sun)
  4. Debilitation
  5. Dusthana affliction
  6. Node affliction (Rahu/Ketu conjunction)
"""
from __future__ import annotations
from typing import List, Tuple, Optional

from ..enums import EvidenceType
from ..models import Evidence

SEVEN_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
NATURAL_MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
NATURAL_BENEFICS = ("Jupiter", "Venus", "Mercury", "Moon")

# Parashari special aspects
PARASHARI_ASPECTS = {
    "Mars": [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn": [3, 7, 10],
}

# Classical combustion orbs (approximate — based on traditional texts)
COMBUSTION_ORBS = {
    "Moon": 12.0,
    "Mercury": 14.0,
    "Venus": 10.0,
    "Mars": 17.0,
    "Jupiter": 11.0,
    "Saturn": 15.0,
}

# Classical debilitation signs
DEBILITATION_SIGNS = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mars": "Cancer",
    "Mercury": "Pisces",
    "Jupiter": "Capricorn",
    "Venus": "Virgo",
    "Saturn": "Aries",
}


def evaluate_malefic_conjunction(
    ctx, target_planet: str
) -> Tuple[bool, List[Evidence]]:
    """
    Check if target planet is conjunct a natural malefic.
    Returns (has_conjunction, evidence).
    """
    evidence: List[Evidence] = []
    target_house = ctx.get_planet_house(target_planet)
    if target_house is None:
        return False, evidence

    conjunctions = []
    for malefic in NATURAL_MALEFICS:
        if malefic == target_planet:
            continue
        mf_house = ctx.get_planet_house(malefic)
        if mf_house is not None and mf_house == target_house:
            conjunctions.append(malefic)

    if conjunctions:
        evidence.append(Evidence(
            evidence_type=EvidenceType.CONJUNCTION,
            subject=f"{target_planet} conjunct malefic",
            value={"planet": target_planet, "malefics": conjunctions},
            expected="No malefic conjunction",
            actual=f"{target_planet} conjunct {conjunctions}",
            source="ChartFacts",
            significance=f"Malefic conjunction: {target_planet} with {conjunctions}",
            details={"affliction_type": "malefic_conjunction"},
        ))

    return bool(conjunctions), evidence


def evaluate_malefic_aspect(
    ctx, target_planet: str
) -> Tuple[bool, List[Evidence]]:
    """
    Check if target planet receives aspect from a natural malefic.
    Uses Parashari aspect system.
    Returns (has_aspect, evidence).
    """
    evidence: List[Evidence] = []
    target_house = ctx.get_planet_house(target_planet)
    if target_house is None:
        return False, evidence

    aspects = []
    for malefic in NATURAL_MALEFICS:
        if malefic == target_planet:
            continue
        mf_house = ctx.get_planet_house(malefic)
        if mf_house is None:
            continue

        # Check 7th aspect (all planets)
        if ((mf_house + 6 - 1) % 12) + 1 == target_house:
            aspects.append((malefic, "7th"))
            continue

        # Special aspects
        for offset in PARASHARI_ASPECTS.get(malefic, []):
            if ((mf_house + offset - 2) % 12) + 1 == target_house:
                aspects.append((malefic, f"{offset}th"))
                break

    if aspects:
        evidence.append(Evidence(
            evidence_type=EvidenceType.ASPECT,
            subject=f"{target_planet} aspected by malefic",
            value={"planet": target_planet, "aspects": aspects},
            expected="No malefic aspect",
            actual=f"{target_planet} aspected by {[(a[0], a[1]) for a in aspects]}",
            source="ChartFacts",
            significance=f"Malefic aspect on {target_planet}",
            details={"affliction_type": "malefic_aspect"},
        ))

    return bool(aspects), evidence


def evaluate_combustion(
    ctx, planet: str
) -> Tuple[bool, List[Evidence]]:
    """
    Check if planet is combust (too close to Sun).
    Uses classical combustion orbs.
    Returns (is_combust, evidence).
    """
    evidence: List[Evidence] = []

    if planet not in COMBUSTION_ORBS:
        return False, evidence

    planet_lon = ctx.get_planet_longitude(planet)
    sun_lon = ctx.get_planet_longitude("Sun")

    if planet_lon is None or sun_lon is None:
        return False, evidence

    diff = abs(planet_lon - sun_lon)
    diff = min(diff, 360.0 - diff)
    orb = COMBUSTION_ORBS[planet]
    is_combust = diff <= orb

    if is_combust:
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_DIGNITY,
            subject=f"{planet} combustion",
            value={
                "planet": planet,
                "planet_longitude": planet_lon,
                "sun_longitude": sun_lon,
                "difference": diff,
                "orb": orb,
            },
            expected=f"{planet} not combust (orb {orb}°)",
            actual=f"{planet} at {diff:.1f}° from Sun (within {orb}° orb)",
            source="ChartFacts",
            significance=f"{planet} combust at {diff:.1f}° from Sun",
            details={"affliction_type": "combustion"},
        ))

    return is_combust, evidence


def evaluate_debilitation(
    ctx, planet: str
) -> Tuple[bool, List[Evidence]]:
    """
    Check if planet is debilitated.
    Returns (is_debilitated, evidence).
    """
    evidence: List[Evidence] = []

    is_deb = ctx.is_debilitated(planet)
    if is_deb:
        sign = ctx.get_planet_sign(planet)
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_DIGNITY,
            subject=f"{planet} debilitation",
            value={"planet": planet, "sign": sign},
            expected=f"{planet} not debilitated",
            actual=f"{planet} debilitated in {sign}",
            source="StrengthReport",
            significance=f"{planet} debilitated in {sign}",
            details={"affliction_type": "debilitation"},
        ))

    return is_deb, evidence


def evaluate_dusthana_affliction(
    ctx, planet: str
) -> Tuple[bool, List[Evidence]]:
    """
    Check if planet is in a dusthana house (6, 8, 12).
    Returns (in_dusthana, evidence).
    """
    evidence: List[Evidence] = []
    house = ctx.get_planet_house(planet)
    if house is None:
        return False, evidence

    if house in (6, 8, 12):
        evidence.append(Evidence(
            evidence_type=EvidenceType.DUSTHANA,
            subject=f"{planet} in dusthana",
            value={"planet": planet, "house": house},
            expected=f"{planet} not in dusthana",
            actual=f"{planet} in {house}th house (dusthana)",
            source="ChartFacts",
            significance=f"{planet} in dusthana house {house}",
            details={"affliction_type": "dusthana"},
        ))
        return True, evidence

    return False, evidence


def evaluate_node_affliction(
    ctx, target_planet: str
) -> Tuple[bool, List[Evidence]]:
    """
    Check if target planet is conjunct Rahu or Ketu.
    NOTE: Node conjunction is NOT automatically a named dosha.
    This is a generic affliction indicator.
    Returns (has_node_affliction, evidence).
    """
    evidence: List[Evidence] = []
    target_house = ctx.get_planet_house(target_planet)
    if target_house is None:
        return False, evidence

    afflictions = []
    for node in ("Rahu", "Ketu"):
        node_house = ctx.get_planet_house(node)
        if node_house is not None and node_house == target_house:
            afflictions.append(node)

    if afflictions:
        evidence.append(Evidence(
            evidence_type=EvidenceType.CONJUNCTION,
            subject=f"{target_planet} conjunct node",
            value={"planet": target_planet, "nodes": afflictions},
            expected="No node conjunction",
            actual=f"{target_planet} conjunct {afflictions}",
            source="ChartFacts",
            significance=f"Node conjunction: {target_planet} with {afflictions}",
            details={"affliction_type": "node_conjunction"},
        ))

    return bool(afflictions), evidence


def evaluate_all_afflictions(
    ctx, planet: str
) -> dict:
    """
    Evaluate all generic afflictions for a single planet.
    Returns a dictionary with each affliction type and its status.
    """
    conj, conj_ev = evaluate_malefic_conjunction(ctx, planet)
    asp, asp_ev = evaluate_malefic_aspect(ctx, planet)
    comb, comb_ev = evaluate_combustion(ctx, planet)
    deb, deb_ev = evaluate_debilitation(ctx, planet)
    dust, dust_ev = evaluate_dusthana_affliction(ctx, planet)
    node, node_ev = evaluate_node_affliction(ctx, planet)

    return {
        "malefic_conjunction": {"present": conj, "evidence": conj_ev},
        "malefic_aspect": {"present": asp, "evidence": asp_ev},
        "combustion": {"present": comb, "evidence": comb_ev},
        "debilitation": {"present": deb, "evidence": deb_ev},
        "dusthana": {"present": dust, "evidence": dust_ev},
        "node_affliction": {"present": node, "evidence": node_ev},
    }
