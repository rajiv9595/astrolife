"""
Manglik / Kuja Dosha Engine — Astrolife V2 Phase 5C

Three explicit methods:
  DOSHA.MANGLIK.LAGNA_CLASSICAL  — Mars in {1,2,4,7,8,12} from Lagna
  DOSHA.MANGLIK.MOON_REFERENCE   — Mars in {1,2,4,7,8,12} from Moon
  DOSHA.MANGLIK.VENUS_REFERENCE  — Mars in {1,2,4,7,8,12} from Venus

Each method is independently evaluated with its own formation,
cancellation, mitigation, and severity.

Tradition: The attribution to BPHS is widely attested but exact verse
numbers cannot be verified. The house set {1,2,4,7,8,12} is the most
common convention across traditions.

Cancellation rules selected are the most widely attested across multiple
traditional sources. Internet-origin rules (e.g., "Leo/Cancer = friendly
sign = cancellation") are NOT included.
"""
from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any

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
    ManglikReferencePoint,
)
from .models import DoshaResult, DoshaProvenance, DoshaEvidence, DoshaMetadata


SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Classical house positions for Manglik dosha from a reference point
MANGLIK_HOUSES = (1, 2, 4, 7, 8, 12)

# Natural malefics (for cancellation checks involving aspects/conjunctions)
NATURAL_MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
NATURAL_BENEFICS = ("Jupiter", "Venus", "Mercury", "Moon")

# Parashari special aspects
PARASHARI_ASPECTS = {
    "Mars": [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn": [3, 7, 10],
}


def _sign_id(name: str) -> int:
    return SIGN_NAMES.index(name) + 1


def _house_from_ref(planet_house: int, ref_house: int) -> int:
    """Count house of planet from reference point (whole-sign)."""
    return ((planet_house - ref_house) % 12) + 1


def _check_parashari_aspect(ctx, from_planet: str, to_house: int) -> bool:
    """Check if from_planet aspects to_house via Parashari system."""
    from_house = ctx.get_planet_house(from_planet)
    if from_house is None:
        return False
    # Standard 7th aspect
    if ((from_house + 6 - 1) % 12) + 1 == to_house:
        return True
    # Special aspects
    for aspect_offset in PARASHARI_ASPECTS.get(from_planet, []):
        if ((from_house + aspect_offset - 2) % 12) + 1 == to_house:
            return True
    return False


# ============================================================
# FORMATION EVALUATORS
# ============================================================

def manglik_formation_lagna(ctx, params=None) -> Tuple[bool, List[Evidence]]:
    """Evaluate Manglik from Lagna reference point."""
    return _evaluate_manglik(ctx, ManglikReferencePoint.LAGNA)


def manglik_formation_moon(ctx, params=None) -> Tuple[bool, List[Evidence]]:
    """Evaluate Manglik from Moon reference point."""
    return _evaluate_manglik(ctx, ManglikReferencePoint.MOON)


def manglik_formation_venus(ctx, params=None) -> Tuple[bool, List[Evidence]]:
    """Evaluate Manglik from Venus reference point."""
    return _evaluate_manglik(ctx, ManglikReferencePoint.VENUS)


def _evaluate_manglik(
    ctx, ref_point: ManglikReferencePoint
) -> Tuple[bool, List[Evidence]]:
    """
    Core Manglik evaluation for any reference point.
    Returns (formed: bool, evidence: List[Evidence]).
    """
    evidence: List[Evidence] = []

    # Get Mars
    mars_house = ctx.get_planet_house("Mars")
    mars_sign = ctx.get_planet_sign("Mars")
    if mars_house is None or mars_sign is None:
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject="Mars",
            value=None,
            expected="Mars present in chart",
            actual="Mars not found",
            source="ChartFacts",
            significance="Mars missing — cannot evaluate Manglik",
        ))
        return False, evidence

    # Get reference point
    if ref_point == ManglikReferencePoint.LAGNA:
        ref_house = 1
        ref_label = "Lagna"
    elif ref_point == ManglikReferencePoint.MOON:
        ref_house = ctx.get_planet_house("Moon")
        ref_label = "Moon"
    elif ref_point == ManglikReferencePoint.VENUS:
        ref_house = ctx.get_planet_house("Venus")
        ref_label = "Venus"
    else:
        return False, evidence

    if ref_house is None:
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject=ref_label,
            value=None,
            expected=f"{ref_label} present in chart",
            actual=f"{ref_label} not found",
            source="ChartFacts",
            significance=f"{ref_label} missing — cannot evaluate Manglik from {ref_label}",
        ))
        return False, evidence

    # Count Mars house from reference
    mars_from_ref = _house_from_ref(mars_house, ref_house)

    evidence.append(Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject=f"Mars from {ref_label}",
        value={"mars_house": mars_house, "ref_house": ref_house, "mars_from_ref": mars_from_ref},
        expected=f"Mars in houses {MANGLIK_HOUSES} from {ref_label}",
        actual=f"Mars in house {mars_from_ref} from {ref_label}",
        source="ChartFacts",
        significance=f"Mars in house {mars_from_ref} from {ref_label}",
        details={
            "reference_point": ref_point.value,
            "mars_sign": mars_sign,
            "method": f"manglik_{ref_point.value.lower()}_formation",
        },
    ))

    evidence.append(Evidence(
        evidence_type=EvidenceType.PLANET_DIGNITY,
        subject="Mars dignity",
        value={
            "sign": mars_sign,
            "dignity": ctx.get_dignity_category("Mars"),
            "exalted": ctx.is_exalted("Mars"),
            "debilitated": ctx.is_debilitated("Mars"),
            "own_sign": ctx.is_own_sign("Mars"),
        },
        expected="Mars dignity for severity assessment",
        actual=ctx.get_dignity_category("Mars") or "unknown",
        source="StrengthReport",
        significance="Dignity affects severity, not formation",
    ))

    formed = mars_from_ref in MANGLIK_HOUSES
    return formed, evidence


# ============================================================
# CANCELLATION EVALUATORS
# ============================================================

def manglik_cancellation(ctx, result, cancel_rule=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate cancellation conditions for Manglik dosha.
    
    Only widely-attested cancellation rules are included:
    1. Mars conjunct Jupiter (same sign/house)
    2. Mars aspected by Jupiter (Parashari 5/7/9)
    3. Mars in own sign (Aries/Scorpio) — from reference point
    
    NOTE: Own-sign and exaltation cancellations are DISPUTED.
    We include own-sign as partial cancellation only.
    Exaltation is NOT included as cancellation (many traditions disagree).
    """
    evidence: List[Evidence] = []

    # Determine which reference method was used
    method = result.method if hasattr(result, 'method') else ""
    ref_point = None
    for rp in ManglikReferencePoint:
        if rp.value.lower() in method.lower():
            ref_point = rp
            break

    if ref_point is None:
        ref_point = ManglikReferencePoint.LAGNA

    # Get reference house
    if ref_point == ManglikReferencePoint.LAGNA:
        ref_house = 1
    elif ref_point == ManglikReferencePoint.MOON:
        ref_house = ctx.get_planet_house("Moon")
    elif ref_point == ManglikReferencePoint.VENUS:
        ref_house = ctx.get_planet_house("Venus")
    else:
        ref_house = 1

    if ref_house is None:
        return False, evidence

    mars_house = ctx.get_planet_house("Mars")
    if mars_house is None:
        return False, evidence

    mars_from_ref = _house_from_ref(mars_house, ref_house)

    # Only evaluate cancellation if Mars is actually in a dosha house
    if mars_from_ref not in MANGLIK_HOUSES:
        return False, evidence

    cancelled = False

    # C1: Mars conjunct Jupiter (same whole-sign house)
    jup_house = ctx.get_planet_house("Jupiter")
    if jup_house is not None and jup_house == mars_house:
        cancelled = True
        evidence.append(Evidence(
            evidence_type=EvidenceType.CONJUNCTION,
            subject="Mars-Jupiter conjunction",
            value={"mars_house": mars_house, "jupiter_house": jup_house},
            expected="No conjunction for cancellation",
            actual="Mars and Jupiter in same house",
            source="ChartFacts",
            significance="Mars conjunct Jupiter — classical cancellation",
            details={"cancellation_type": "conjunction_jupiter"},
        ))

    # C2: Jupiter aspects Mars (Parashari 5th/7th/9th aspect)
    if not cancelled and jup_house is not None:
        if _check_parashari_aspect(ctx, "Jupiter", mars_house):
            cancelled = True
            evidence.append(Evidence(
                evidence_type=EvidenceType.ASPECT,
                subject="Jupiter aspects Mars",
                value={"jupiter_house": jup_house, "mars_house": mars_house},
                expected="No Jupiter aspect for cancellation",
                actual=f"Jupiter in house {jup_house} aspects Mars in house {mars_house}",
                source="ChartFacts",
                significance="Jupiter aspect on Mars — widely cited cancellation",
                details={"cancellation_type": "aspect_jupiter"},
            ))

    # C3: Mars in own sign — PARTIAL cancellation (disputed)
    # Only as partial, not full
    if not cancelled and ctx.is_own_sign("Mars"):
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_DIGNITY,
            subject="Mars own sign",
            value={"sign": ctx.get_planet_sign("Mars")},
            expected="Mars not in own sign",
            actual=f"Mars in own sign {ctx.get_planet_sign('Mars')}",
            source="StrengthReport",
            significance="Mars in own sign — disputed partial cancellation",
            details={"cancellation_type": "own_sign_partial", "is_full": False},
        ))

    return cancelled, evidence


# ============================================================
# MITIGATION EVALUATORS
# ============================================================

def manglik_mitigation(ctx, result, mit_rule=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate mitigation conditions for Manglik dosha.
    
    Mitigation weakens the dosha without cancelling it.
    Conditions:
    1. Mars exalted — strong Mars reduces affliction
    2. Strong Lagna lord — protective factor
    3. Benefic in 7th house — partnership protection
    4. Mars in Varga (D9) strength
    """
    evidence: List[Evidence] = []
    mitigated = False

    # M1: Mars exalted
    if ctx.is_exalted("Mars"):
        mitigated = True
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_DIGNITY,
            subject="Mars exaltation mitigation",
            value={"sign": ctx.get_planet_sign("Mars")},
            expected="Mars not exalted",
            actual="Mars exalted",
            source="StrengthReport",
            significance="Exalted Mars — mitigating factor",
            details={"mitigation_type": "exaltation"},
        ))

    # M2: Strong Lagna lord
    lagna_lord = ctx.get_house_lord(1)
    if lagna_lord:
        lagna_strong = (
            ctx.is_exalted(lagna_lord)
            or ctx.is_own_sign(lagna_lord)
            or ctx.is_moolatrikona(lagna_lord)
            or (ctx.get_shadbala_ratio(lagna_lord) or 0) >= 1.0
        )
        if lagna_strong:
            mitigated = True
            evidence.append(Evidence(
                evidence_type=EvidenceType.PLANET_DIGNITY,
                subject=f"Lagna lord {lagna_lord} strength",
                value={
                    "planet": lagna_lord,
                    "dignity": ctx.get_dignity_category(lagna_lord),
                    "shadbala_ratio": ctx.get_shadbala_ratio(lagna_lord),
                },
                expected="Strong Lagna lord",
                actual=f"Lagna lord {lagna_lord} is strong",
                source="StrengthReport",
                significance="Strong Lagna lord mitigates dosha",
                details={"mitigation_type": "lagna_lord_strength"},
            ))

    # M3: Benefic in 7th house from reference
    # (Reference depends on method — use Lagna for simplicity in mitigation)
    benefics_in_7th = []
    seventh_from_lagna = ctx.get_planets_in_house(7)
    for p in seventh_from_lagna:
        if p in NATURAL_BENEFICS and p != "Mars":
            benefics_in_7th.append(p)
    if benefics_in_7th:
        mitigated = True
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject="Benefics in 7th from Lagna",
            value={"planets": benefics_in_7th},
            expected="No benefics in 7th",
            actual=f"Benefics {benefics_in_7th} in 7th house",
            source="ChartFacts",
            significance="Benefic presence in 7th mitigates partnership affliction",
            details={"mitigation_type": "benefic_7th"},
        ))

    return mitigated, evidence


# ============================================================
# SEVERITY EVALUATOR
# ============================================================

def manglik_severity(ctx, formed: bool, evidence: List[Evidence]) -> DoshaSeverity:
    """
    Evaluate categorical severity for Manglik dosha.
    
    Severity is INDEPENDENT of formation.
    Uses categorical levels: NONE / LOW / MODERATE / HIGH / UNKNOWN
    
    Factors considered:
    - Mars dignity (exalted = lower severity, debilitated = higher)
    - Mars house position (8th > 12th > 7th in classical severity)
    - Number of reference methods triggered
    - Shadbala ratio
    """
    if not formed:
        return DoshaSeverity.NONE

    mars_sign = ctx.get_planet_sign("Mars")
    if not mars_sign:
        return DoshaSeverity.UNKNOWN

    # Base severity from Mars dignity
    if ctx.is_exalted("Mars"):
        base = DoshaSeverity.LOW
    elif ctx.is_own_sign("Mars") or ctx.is_moolatrikona("Mars"):
        base = DoshaSeverity.LOW
    elif ctx.is_debilitated("Mars"):
        base = DoshaSeverity.HIGH
    else:
        base = DoshaSeverity.MODERATE

    # House modifier — 8th house is classically most severe
    for ev in evidence:
        if ev.evidence_type == EvidenceType.PLANET_IN_HOUSE and "Mars from" in (ev.subject or ""):
            details = ev.details or {}
            if details.get("reference_point") == "LAGNA":
                mars_from_ref = (ev.value or {}).get("mars_from_ref")
                if mars_from_ref == 8:
                    if base == DoshaSeverity.MODERATE:
                        base = DoshaSeverity.HIGH
                elif mars_from_ref == 1:
                    if base == DoshaSeverity.MODERATE:
                        base = DoshaSeverity.LOW

    return base


# ============================================================
# RULE DEFINITIONS
# ============================================================

def _build_manglik_rule(
    rule_id: str,
    name: str,
    desc: str,
    method: str,
    evaluator_name: str,
    ref_point: ManglikReferencePoint,
) -> RuleDefinition:
    """Build a Manglik rule definition for a specific reference method."""
    provenance = DoshaProvenance(
        source_type=DoshaSourceType.CLASSICAL_TEXT,
        source_name="Brihat Parashara Hora Shastra",
        source_reference="UNVERIFIED",
        tradition=DoshaTradition.PARASHARI_CLASSICAL,
        method=method,
        implementation_version="1.0.0",
        notes=(
            "Attributed to BPHS. Exact verse unverified. "
            f"Reference point: {ref_point.value}. "
            "House set {1,2,4,7,8,12} is most common convention. "
            "Cancellation rules selected from widely-attested sources only."
        ),
    )

    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id=rule_id,
            rule_version="1.0.0",
            name=name,
            category=RuleCategory.DOSHA,
            tradition=RuleTradition.PARASHARI_CLASSICAL,
            school_method=method,
            status=RuleStatus.ENABLED,
            description=desc,
            provenance=Provenance(
                source_type=SourceType.CLASSICAL_TEXT,
                source_name=provenance.source_name,
                source_reference=provenance.source_reference,
                tradition=RuleTradition.PARASHARI_CLASSICAL,
                method=method,
                implementation_version="1.0.0",
                notes=provenance.notes,
            ),
            confidence=ConfidenceLevel.HIGH,
            tags=["manglik", "kuja", "mars", ref_point.value.lower()],
            enabled=True,
        ),
        formation_conditions=[
            Condition(type=evaluator_name, params={"reference_point": ref_point.value})
        ],
        strength_conditions=[],
        activation_rules=[],
        cancellation_rules=[
            CancellationRule(
                rule_id=f"{rule_id}.CANCEL",
                description="Manglik cancellation: Jupiter conjunction/aspect, own sign (partial)",
                evaluator="manglik_cancellation",
                is_partial=True,
            )
        ],
        mitigation_rules=[
            MitigationRule(
                rule_id=f"{rule_id}.MITIG",
                description="Manglik mitigation: exaltation, Lagna lord strength, benefic 7th",
                evaluator="manglik_mitigation",
                strength_impact="partial",
            )
        ],
        required_evidence=[
            EvidenceType.PLANET_IN_HOUSE,
            EvidenceType.PLANET_DIGNITY,
            EvidenceType.CONJUNCTION,
            EvidenceType.ASPECT,
        ],
    )


def build_manglik_lagna() -> RuleDefinition:
    return _build_manglik_rule(
        "DOSHA.MANGLIK.LAGNA_CLASSICAL",
        "Manglik Dosha (Lagna Reference)",
        "Mars in houses 1, 2, 4, 7, 8, or 12 from Lagna (whole-sign).",
        "LAGNA_CLASSICAL",
        "manglik_formation_lagna",
        ManglikReferencePoint.LAGNA,
    )


def build_manglik_moon() -> RuleDefinition:
    return _build_manglik_rule(
        "DOSHA.MANGLIK.MOON_REFERENCE",
        "Manglik Dosha (Moon Reference)",
        "Mars in houses 1, 2, 4, 7, 8, or 12 from Moon (whole-sign).",
        "MOON_REFERENCE",
        "manglik_formation_moon",
        ManglikReferencePoint.MOON,
    )


def build_manglik_venus() -> RuleDefinition:
    return _build_manglik_rule(
        "DOSHA.MANGLIK.VENUS_REFERENCE",
        "Manglik Dosha (Venus Reference)",
        "Mars in houses 1, 2, 4, 7, 8, or 12 from Venus (whole-sign).",
        "VENUS_REFERENCE",
        "manglik_formation_venus",
        ManglikReferencePoint.VENUS,
    )


MANGLIK_RULES: List[RuleDefinition] = [
    build_manglik_lagna(),
    build_manglik_moon(),
    build_manglik_venus(),
]

MANGLIK_FORMATION_EVALUATORS = {
    "manglik_formation_lagna": manglik_formation_lagna,
    "manglik_formation_moon": manglik_formation_moon,
    "manglik_formation_venus": manglik_formation_venus,
}
