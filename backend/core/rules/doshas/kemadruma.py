"""
Kemadruma Dosha Engine — Astrolife V2 Phase 5C

Classical Parashari dosha — separate from the Phase 5B Kemadruma YOGA.

Formation (strict classical):
  1. No planet in 2nd house from Moon
  2. No planet in 12th house from Moon
  3. No planet in any kendra (1,4,7,10) from Moon (excluding Moon itself)

Cancellation:
  - Jupiter aspect on Moon (widely cited)
  - Sun conjunction with Moon (Amavasya — debated, included as partial)

NOTE: The simplistic "no planets beside Moon" definition is NOT used.
The kendra-from-Moon condition is part of the classical definition.

Source attribution: BPHS (attributed). Exact verse unverified.
"""
from __future__ import annotations
from typing import List, Tuple, Optional

from ..enums import (
    RuleCategory, RuleTradition, RuleStatus, ConfidenceLevel,
    SourceType, EvidenceType,
)
from ..models import (
    RuleDefinition, RuleMetadata, Provenance, Evidence,
    CancellationRule, MitigationRule, Condition,
)
from .enums import (
    DoshaCategory, DoshaSeverity, DoshaFormationStatus,
    DoshaCancellationStatus, DoshaMitigationStatus,
    DoshaTradition, DoshaConfidence, DoshaSourceType,
)
from .models import DoshaResult, DoshaProvenance

SEVEN_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
KENDRA_OFFSETS = (0, 3, 6, 9)  # kendra from Moon: 1st, 4th, 7th, 10th

# Parashari special aspects
PARASHARI_ASPECTS = {
    "Mars": [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn": [3, 7, 10],
}


def _house_from_moon(ctx, planet: str) -> Optional[int]:
    """House of planet counted from Moon."""
    moon_house = ctx.get_planet_house("Moon")
    planet_house = ctx.get_planet_house(planet)
    if moon_house is None or planet_house is None:
        return None
    return ((planet_house - moon_house) % 12) + 1


def _check_parashari_aspect(ctx, from_planet: str, to_house: int) -> bool:
    from_house = ctx.get_planet_house(from_planet)
    if from_house is None:
        return False
    if ((from_house + 6 - 1) % 12) + 1 == to_house:
        return True
    for offset in PARASHARI_ASPECTS.get(from_planet, []):
        if ((from_house + offset - 2) % 12) + 1 == to_house:
            return True
    return False


# ============================================================
# FORMATION
# ============================================================

def kemadruma_formation(ctx, params=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate Kemadruma dosha formation.
    
    Classical conditions (ALL must be true):
    1. No planet (excl. Moon) in 2nd from Moon
    2. No planet (excl. Moon) in 12th from Moon
    3. No planet (excl. Moon) in kendra (1,4,7,10) from Moon
    """
    evidence: List[Evidence] = []
    moon_house = ctx.get_planet_house("Moon")

    if moon_house is None:
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject="Moon",
            value=None,
            expected="Moon present",
            actual="Moon not found",
            source="ChartFacts",
            significance="Moon missing — cannot evaluate Kemadruma",
        ))
        return False, evidence

    # Condition 1: planets in 2nd from Moon
    house_2 = ((moon_house + 2 - 2) % 12) + 1  # 2nd from Moon = (moon_house % 12) + 1
    planets_in_2 = [p for p in SEVEN_PLANETS if p != "Moon"
                    and ctx.get_planet_house(p) == house_2]

    evidence.append(Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject="Planets in 2nd from Moon",
        value={"house": house_2, "planets": planets_in_2},
        expected="No planets in 2nd from Moon",
        actual=f"Planets: {planets_in_2 or 'none'}",
        source="ChartFacts",
        significance="2nd from Moon" + (" EMPTY" if not planets_in_2 else f" has {planets_in_2}"),
    ))

    # Condition 2: planets in 12th from Moon
    house_12 = ((moon_house + 12 - 2) % 12) + 1  # 12th from Moon
    planets_in_12 = [p for p in SEVEN_PLANETS if p != "Moon"
                     and ctx.get_planet_house(p) == house_12]

    evidence.append(Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject="Planets in 12th from Moon",
        value={"house": house_12, "planets": planets_in_12},
        expected="No planets in 12th from Moon",
        actual=f"Planets: {planets_in_12 or 'none'}",
        source="ChartFacts",
        significance="12th from Moon" + (" EMPTY" if not planets_in_12 else f" has {planets_in_12}"),
    ))

    # Condition 3: planets in kendra from Moon
    kendra_planets = []
    for offset in KENDRA_OFFSETS:
        target = ((moon_house + offset - 1) % 12) + 1
        for p in SEVEN_PLANETS:
            if p == "Moon":
                continue
            if ctx.get_planet_house(p) == target and p not in kendra_planets:
                kendra_planets.append(p)

    evidence.append(Evidence(
        evidence_type=EvidenceType.KENDRA_TRIKONA,
        subject="Planets in kendra from Moon",
        value={"kendra_planets": kendra_planets},
        expected="No planets in kendra from Moon",
        actual=f"Kendra planets: {kendra_planets or 'none'}",
        source="ChartFacts",
        significance="Kendra from Moon" + (" EMPTY" if not kendra_planets else f" has {kendra_planets}"),
    ))

    formed = (not planets_in_2) and (not planets_in_12) and (not kendra_planets)
    return formed, evidence


# ============================================================
# CANCELLATION
# ============================================================

def kemadruma_cancellation(ctx, result, cancel_rule=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate cancellation for Kemadruma dosha.
    
    Cancellation conditions:
    1. Jupiter aspects Moon (Parashari 5th/7th/9th) — widely cited
    2. Sun conjunct Moon (Amavasya) — debated, included as partial
    """
    evidence: List[Evidence] = []
    moon_house = ctx.get_planet_house("Moon")
    if moon_house is None:
        return False, evidence

    cancelled = False

    # C1: Jupiter aspects Moon
    jup_house = ctx.get_planet_house("Jupiter")
    if jup_house is not None:
        if _check_parashari_aspect(ctx, "Jupiter", moon_house):
            cancelled = True
            evidence.append(Evidence(
                evidence_type=EvidenceType.ASPECT,
                subject="Jupiter aspects Moon",
                value={"jupiter_house": jup_house, "moon_house": moon_house},
                expected="No Jupiter aspect for cancellation",
                actual=f"Jupiter in house {jup_house} aspects Moon in house {moon_house}",
                source="ChartFacts",
                significance="Jupiter aspect on Moon — widely cited cancellation",
                details={"cancellation_type": "aspect_jupiter"},
            ))

    # C2: Sun conjunct Moon (Amavasya) — partial cancellation
    sun_house = ctx.get_planet_house("Sun")
    if sun_house is not None and sun_house == moon_house:
        evidence.append(Evidence(
            evidence_type=EvidenceType.CONJUNCTION,
            subject="Sun-Moon conjunction (Amavasya)",
            value={"sun_house": sun_house, "moon_house": moon_house},
            expected="No Sun-Moon conjunction",
            actual="Sun and Moon in same house",
            source="ChartFacts",
            significance="Amavasya — debated cancellation, treated as partial",
            details={"cancellation_type": "amavasya_partial", "is_full": False},
        ))
        # This is partial, not full cancellation — don't set cancelled = True
        # for full cancellation, but evidence is recorded

    return cancelled, evidence


# ============================================================
# MITIGATION
# ============================================================

def kemadruma_mitigation(ctx, result, mit_rule=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate mitigation for Kemadruma dosha.
    
    Mitigation factors:
    1. Venus conjunct Moon — some traditions
    2. Strong Moon (exalted/own sign)
    """
    evidence: List[Evidence] = []
    moon_house = ctx.get_planet_house("Moon")
    if moon_house is None:
        return False, evidence

    mitigated = False

    # M1: Moon exalted or own sign
    if ctx.is_exalted("Moon") or ctx.is_own_sign("Moon"):
        mitigated = True
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_DIGNITY,
            subject="Moon dignity",
            value={
                "sign": ctx.get_planet_sign("Moon"),
                "exalted": ctx.is_exalted("Moon"),
                "own_sign": ctx.is_own_sign("Moon"),
            },
            expected="Moon not strong",
            actual=f"Moon in {ctx.get_dignity_category('Moon')}",
            source="StrengthReport",
            significance="Strong Moon mitigates Kemadruma isolation",
            details={"mitigation_type": "moon_strength"},
        ))

    # M2: Venus conjunct Moon
    venus_house = ctx.get_planet_house("Venus")
    if venus_house is not None and venus_house == moon_house:
        mitigated = True
        evidence.append(Evidence(
            evidence_type=EvidenceType.CONJUNCTION,
            subject="Venus-Moon conjunction",
            value={"venus_house": venus_house, "moon_house": moon_house},
            expected="No Venus-Moon conjunction",
            actual="Venus conjunct Moon",
            source="ChartFacts",
            significance="Venus conjunction mitigates Kemadruma",
            details={"mitigation_type": "venus_conjunction"},
        ))

    return mitigated, evidence


# ============================================================
# SEVERITY
# ============================================================

def kemadruma_severity(ctx, formed: bool, evidence: List[Evidence]) -> DoshaSeverity:
    """Categorical severity for Kemadruma dosha."""
    if not formed:
        return DoshaSeverity.NONE

    # Moon dignity affects severity
    if ctx.is_exalted("Moon") or ctx.is_own_sign("Moon"):
        return DoshaSeverity.LOW
    if ctx.is_debilitated("Moon"):
        return DoshaSeverity.HIGH

    return DoshaSeverity.MODERATE


# ============================================================
# RULE DEFINITION
# ============================================================

def build_kemadruma_dosha() -> RuleDefinition:
    provenance_notes = (
        "Classical Parashari dosha. Attributed to BPHS. Exact verse unverified. "
        "Formation: no planets in 2nd/12th from Moon AND no planets in kendra from Moon. "
        "Simplistic 'no planets beside Moon' definition NOT used. "
        "Separate from Phase 5B Kemadruma YOGA — this version adds "
        "severity/cancellation/mitigation analysis."
    )

    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id="DOSHA.KEMADRUMA.CLASSICAL",
            rule_version="1.0.0",
            name="Kemadruma Dosha (Classical)",
            category=RuleCategory.DOSHA,
            tradition=RuleTradition.PARASHARI_CLASSICAL,
            school_method="CLASSICAL",
            status=RuleStatus.ENABLED,
            description=(
                "No planets in 2nd or 12th from Moon, and no planets in any kendra "
                "from Moon (classical Parashari definition)."
            ),
            provenance=Provenance(
                source_type=SourceType.CLASSICAL_TEXT,
                source_name="Brihat Parashara Hora Shastra",
                source_reference="UNVERIFIED",
                tradition=RuleTradition.PARASHARI_CLASSICAL,
                method="CLASSICAL",
                implementation_version="1.0.0",
                notes=provenance_notes,
            ),
            confidence=ConfidenceLevel.HIGH,
            tags=["kemadruma", "moon", "isolation"],
            enabled=True,
        ),
        formation_conditions=[
            Condition(type="kemadruma_formation", params={})
        ],
        strength_conditions=[],
        activation_rules=[],
        cancellation_rules=[
            CancellationRule(
                rule_id="DOSHA.KEMADRUMA.CLASSICAL.CANCEL",
                description="Jupiter aspect on Moon, Amavasya (partial)",
                evaluator="kemadruma_cancellation",
                is_partial=True,
            )
        ],
        mitigation_rules=[
            MitigationRule(
                rule_id="DOSHA.KEMADRUMA.CLASSICAL.MITIG",
                description="Moon strength, Venus conjunction",
                evaluator="kemadruma_mitigation",
                strength_impact="partial",
            )
        ],
        required_evidence=[
            EvidenceType.PLANET_IN_HOUSE,
            EvidenceType.KENDRA_TRIKONA,
            EvidenceType.PLANET_DIGNITY,
            EvidenceType.ASPECT,
            EvidenceType.CONJUNCTION,
        ],
    )


KEMADRUMA_RULES: List[RuleDefinition] = [build_kemadruma_dosha()]

KEMADRUMA_FORMATION_EVALUATORS = {
    "kemadruma_formation": kemadruma_formation,
}
