"""
Kala Sarpa Dosha Engine — Astrolife V2 Phase 5C

TRADITION-DEPENDENT — NOT universally accepted as Parashari Classical.

Primary rule: All seven classical planets (Sun, Moon, Mars, Mercury,
Jupiter, Venus, Saturn) are hemmed between Rahu and Ketu on one side
of the nodal axis.

Method: Sign-based containment (most common definition).

Partial cases:
  - All 7 inside → FORMED
  - 6 or fewer inside → NOT_FORMED
  - Exactly 7 inside → FORMED
  - Planet on Rahu/Ketu sign boundary → UNCERTAIN (method-dependent)

Boundary handling:
  - Sign-based: a planet is "inside" if its sign is between Rahu sign
    and Ketu sign (exclusive of endpoints in the canonical direction)
  - Rahu/Ketu signs themselves are the boundaries

Source: NOT found in BPHS, Phaladeepika, or Saravali.
Origin uncertain — possibly medieval or regional tradition.
"""
from __future__ import annotations
from typing import List, Tuple, Optional, Set

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
    KalaSarpaMethod,
)
from .models import DoshaResult, DoshaProvenance

SEVEN_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

SIGN_IDS = {
    "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4,
    "Leo": 5, "Virgo": 6, "Libra": 7, "Scorpio": 8,
    "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12,
}

PARASHARI_ASPECTS = {
    "Mars": [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn": [3, 7, 10],
}


def _signs_between_cw(start_id: int, end_id: int) -> Set[int]:
    """Get sign IDs strictly between start and end (clockwise, exclusive)."""
    signs = set()
    curr = start_id
    while True:
        curr = (curr % 12) + 1
        if curr == end_id:
            break
        signs.add(curr)
    return signs


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
# FORMATION — METHOD A: SIGN-BASED
# ============================================================

def kala_sarpa_formation_sign(ctx, params=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate Kala Sarpa using sign-based containment.
    
    Rule: All 7 classical planets must have their signs between Rahu sign
    and Ketu sign (one direction). Two arcs exist; if either arc contains
    all 7, the dosha forms.
    """
    evidence: List[Evidence] = []

    rahu = ctx.get_planet("Rahu")
    ketu = ctx.get_planet("Ketu")
    if rahu is None or ketu is None:
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject="Nodes",
            value=None,
            expected="Rahu and Ketu present",
            actual="Missing nodes",
            source="ChartFacts",
            significance="Cannot evaluate Kala Sarpa without nodes",
        ))
        return False, evidence

    rahu_sign_id = rahu.sign_num
    ketu_sign_id = ketu.sign_num

    evidence.append(Evidence(
        evidence_type=EvidenceType.PLANET_IN_SIGN,
        subject="Nodal axis",
        value={
            "rahu_sign": rahu.sign,
            "rahu_sign_id": rahu_sign_id,
            "ketu_sign": ketu.sign,
            "ketu_sign_id": ketu_sign_id,
        },
        expected="Nodal axis defined",
        actual=f"Rahu in {rahu.sign}, Ketu in {ketu.sign}",
        source="ChartFacts",
        significance="Nodal axis determines containment arcs",
    ))

    # Two arcs: Rahu→Ketu (CW) and Ketu→Rahu (CW)
    arc_rk = _signs_between_cw(rahu_sign_id, ketu_sign_id)
    arc_kr = _signs_between_cw(ketu_sign_id, rahu_sign_id)

    # Get planet sign IDs
    planet_signs = {}
    for p in SEVEN_PLANETS:
        pdata = ctx.get_planet(p)
        if pdata:
            planet_signs[p] = pdata.sign_num

    # Count planets in each arc
    in_rk = [p for p, sid in planet_signs.items() if sid in arc_rk]
    in_kr = [p for p, sid in planet_signs.items() if sid in arc_kr]

    # Planets exactly on Rahu or Ketu sign (boundary)
    on_rahu = [p for p, sid in planet_signs.items() if sid == rahu_sign_id]
    on_ketu = [p for p, sid in planet_signs.items() if sid == ketu_sign_id]
    boundary = on_rahu + on_ketu

    all_in_rk = len(in_rk) == 7
    all_in_kr = len(in_kr) == 7

    evidence.append(Evidence(
        evidence_type=EvidenceType.PLANET_IN_SIGN,
        subject="Sign containment analysis",
        value={
            "arc_rahu_to_ketu": {"planets": in_rk, "count": len(in_rk)},
            "arc_ketu_to_rahu": {"planets": in_kr, "count": len(in_kr)},
            "on_boundary": {"planets": boundary, "count": len(boundary)},
        },
        expected="All 7 planets in one arc",
        actual=(
            f"Rahu→Ketu: {len(in_rk)} planets, "
            f"Ketu→Rahu: {len(in_kr)} planets, "
            f"Boundary: {len(boundary)} planets"
        ),
        source="ChartFacts",
        significance=(
            "FORMED" if (all_in_rk or all_in_kr)
            else f"Not all 7 planets contained"
        ),
        details={
            "method": "kala_sarpa_sign_based",
            "arc_rahu_to_ketu": sorted(in_rk),
            "arc_ketu_to_rahu": sorted(in_kr),
        },
    ))

    if all_in_rk or all_in_kr:
        return True, evidence
    elif len(in_rk) >= 5 or len(in_kr) >= 5:
        # Partial — close but not formed
        evidence.append(Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Partial containment",
            value={"max_contained": max(len(in_rk), len(in_kr))},
            expected="7 planets contained",
            actual=f"Only {max(len(in_rk), len(in_kr))} contained",
            source="ChartFacts",
            significance="Partial — not formed",
        ))

    return False, evidence


# ============================================================
# CANCELLATION
# ============================================================

def kala_sarpa_cancellation(ctx, result, cancel_rule=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate cancellation for Kala Sarpa dosha.
    
    Cancellation conditions (tradition-dependent):
    1. Jupiter in Ascendant — widely cited
    2. Jupiter aspects Rahu — widely cited
    """
    evidence: List[Evidence] = []
    cancelled = False

    # C1: Jupiter in Ascendant (1st house)
    jup_house = ctx.get_planet_house("Jupiter")
    if jup_house == 1:
        cancelled = True
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject="Jupiter in Ascendant",
            value={"jupiter_house": 1},
            expected="Jupiter not in 1st",
            actual="Jupiter in 1st house",
            source="ChartFacts",
            significance="Jupiter in Ascendant — widely cited cancellation",
            details={"cancellation_type": "jupiter_ascendant"},
        ))

    # C2: Jupiter aspects Rahu
    if not cancelled:
        rahu_house = ctx.get_planet_house("Rahu")
        if rahu_house is not None and jup_house is not None:
            if _check_parashari_aspect(ctx, "Jupiter", rahu_house):
                cancelled = True
                evidence.append(Evidence(
                    evidence_type=EvidenceType.ASPECT,
                    subject="Jupiter aspects Rahu",
                    value={"jupiter_house": jup_house, "rahu_house": rahu_house},
                    expected="No Jupiter aspect on Rahu",
                    actual=f"Jupiter aspects Rahu",
                    source="ChartFacts",
                    significance="Jupiter aspect on Rahu — widely cited cancellation",
                    details={"cancellation_type": "jupiter_aspect_rahu"},
                ))

    return cancelled, evidence


# ============================================================
# MITIGATION
# ============================================================

def kala_sarpa_mitigation(ctx, result, mit_rule=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate mitigation for Kala Sarpa dosha.
    
    Mitigation factors:
    1. Multiple benefic aspects on nodes
    2. Strong Ascendant lord
    """
    evidence: List[Evidence] = []
    mitigated = False

    # M1: Strong ascendant lord
    lagna_lord = ctx.get_house_lord(1)
    if lagna_lord:
        lagna_strong = (
            ctx.is_exalted(lagna_lord)
            or ctx.is_own_sign(lagna_lord)
            or ctx.is_moolatrikona(lagna_lord)
        )
        if lagna_strong:
            mitigated = True
            evidence.append(Evidence(
                evidence_type=EvidenceType.PLANET_DIGNITY,
                subject=f"Lagna lord {lagna_lord} strength",
                value={
                    "planet": lagna_lord,
                    "dignity": ctx.get_dignity_category(lagna_lord),
                },
                expected="Strong Lagna lord",
                actual=f"Lagna lord {lagna_lord} is {ctx.get_dignity_category(lagna_lord)}",
                source="StrengthReport",
                significance="Strong Lagna lord mitigates",
                details={"mitigation_type": "lagna_lord_strength"},
            ))

    return mitigated, evidence


# ============================================================
# SEVERITY
# ============================================================

def kala_sarpa_severity(ctx, formed: bool, evidence: List[Evidence]) -> DoshaSeverity:
    """
    Categorical severity for Kala Sarpa.
    
    NOTE: No validated classical severity scale exists for Kala Sarpa.
    We use a conservative categorical approach.
    """
    if not formed:
        return DoshaSeverity.NONE
    # No defensible way to assign severity beyond FORMED/NOT_FORMED
    return DoshaSeverity.UNKNOWN


# ============================================================
# RULE DEFINITION
# ============================================================

def build_kala_sarpa_sign() -> RuleDefinition:
    provenance_notes = (
        "TRADITION-DEPENDENT. NOT found in BPHS, Phaladeepika, or Saravali. "
        "Origin uncertain — possibly medieval or regional tradition. "
        "Method: sign-based containment of all 7 classical planets "
        "between Rahu and Ketu. Boundary handling: planets on node signs "
        "count as boundary (UNCERTAIN). Outer planets ignored (not Vedic). "
        "Cancellation: Jupiter in Ascendant or aspecting Rahu."
    )

    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id="DOSHA.KALA_SARPA.SIGN_BASED",
            rule_version="1.0.0",
            name="Kala Sarpa Dosha (Sign-Based)",
            category=RuleCategory.DOSHA,
            tradition=RuleTradition.TRADITION_DEPENDENT,
            school_method="SIGN_BASED",
            status=RuleStatus.ENABLED,
            description=(
                "All 7 classical planets hemmed between Rahu and Ketu "
                "on one side of the nodal axis (sign-based containment)."
            ),
            provenance=Provenance(
                source_type=SourceType.UNVERIFIED,
                source_name="Traditional Practice (unverified classical source)",
                source_reference="UNVERIFIED",
                tradition=RuleTradition.TRADITION_DEPENDENT,
                method="SIGN_BASED",
                implementation_version="1.0.0",
                notes=provenance_notes,
            ),
            confidence=ConfidenceLevel.TRADITION_DEPENDENT,
            tags=["kala_sarpa", "rahu", "ketu", "nodes", "tradition_dependent"],
            enabled=True,
        ),
        formation_conditions=[
            Condition(type="kala_sarpa_formation_sign", params={})
        ],
        strength_conditions=[],
        activation_rules=[],
        cancellation_rules=[
            CancellationRule(
                rule_id="DOSHA.KALA_SARPA.SIGN_BASED.CANCEL",
                description="Jupiter in Ascendant or aspecting Rahu",
                evaluator="kala_sarpa_cancellation",
                is_partial=False,
            )
        ],
        mitigation_rules=[
            MitigationRule(
                rule_id="DOSHA.KALA_SARPA.SIGN_BASED.MITIG",
                description="Strong Lagna lord",
                evaluator="kala_sarpa_mitigation",
                strength_impact="partial",
            )
        ],
        required_evidence=[
            EvidenceType.PLANET_IN_SIGN,
            EvidenceType.PLANET_IN_HOUSE,
        ],
    )


KALA_SARPA_RULES: List[RuleDefinition] = [build_kala_sarpa_sign()]

KALA_SARPA_FORMATION_EVALUATORS = {
    "kala_sarpa_formation_sign": kala_sarpa_formation_sign,
}
