"""
Pitru Dosha Engine — Astrolife V2 Phase 5C

TRADITION-DEPENDENT / UNVERIFIED — conservative implementation.

Pitru Dosha (Ancestral Affliction) has no clearly defined classical
Parashari formation rule in BPHS. The concept of ancestral affliction
is traditional, but the specific astrological formation rules are
largely modern synthesis.

Implemented conditions (most commonly cited):
  1. Sun conjunct Rahu (same sign)
  2. Sun conjunct Ketu (same sign)
  3. Moon conjunct Rahu (same sign)
  4. Moon conjunct Ketu (same sign)
  5. Rahu in 9th house from Lagna
  6. Ketu in 9th house from Lagna

Classification: TRADITION_DEPENDENT
Confidence: LOW (formation rules are secondary/modern)
No deterministic predictions should be generated from this dosha.
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


def pitru_formation(ctx, params=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate Pitru Dosha formation.
    
    Conditions (ANY one triggers formation):
    1. Sun conjunct Rahu (same whole-sign house)
    2. Sun conjunct Ketu (same whole-sign house)
    3. Moon conjunct Rahu (same whole-sign house)
    4. Moon conjunct Ketu (same whole-sign house)
    5. Rahu in 9th house from Lagna
    6. Ketu in 9th house from Lagna
    """
    evidence: List[Evidence] = []
    reasons = []

    # Get positions
    sun_house = ctx.get_planet_house("Sun")
    moon_house = ctx.get_planet_house("Moon")
    rahu_house = ctx.get_planet_house("Rahu")
    ketu_house = ctx.get_planet_house("Ketu")
    lagna_house = 1

    if any(h is None for h in [sun_house, moon_house, rahu_house, ketu_house]):
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject="Required planets",
            value=None,
            expected="Sun, Moon, Rahu, Ketu present",
            actual="Missing one or more required planets",
            source="ChartFacts",
            significance="Cannot evaluate Pitru Dosha",
        ))
        return False, evidence

    # C1: Sun conjunct Rahu
    if sun_house == rahu_house:
        reasons.append("Sun conjunct Rahu")
        evidence.append(Evidence(
            evidence_type=EvidenceType.CONJUNCTION,
            subject="Sun-Rahu conjunction",
            value={"sun_house": sun_house, "rahu_house": rahu_house},
            expected="No conjunction",
            actual="Sun and Rahu in same house",
            source="ChartFacts",
            significance="Sun (karaka for father) afflicted by Rahu",
            details={"condition": "sun_conjunct_rahu"},
        ))

    # C2: Sun conjunct Ketu
    if sun_house == ketu_house:
        reasons.append("Sun conjunct Ketu")
        evidence.append(Evidence(
            evidence_type=EvidenceType.CONJUNCTION,
            subject="Sun-Ketu conjunction",
            value={"sun_house": sun_house, "ketu_house": ketu_house},
            expected="No conjunction",
            actual="Sun and Ketu in same house",
            source="ChartFacts",
            significance="Sun (karaka for father) afflicted by Ketu",
            details={"condition": "sun_conjunct_ketu"},
        ))

    # C3: Moon conjunct Rahu
    if moon_house == rahu_house:
        reasons.append("Moon conjunct Rahu")
        evidence.append(Evidence(
            evidence_type=EvidenceType.CONJUNCTION,
            subject="Moon-Rahu conjunction",
            value={"moon_house": moon_house, "rahu_house": rahu_house},
            expected="No conjunction",
            actual="Moon and Rahu in same house",
            source="ChartFacts",
            significance="Moon (karaka for mother) afflicted by Rahu",
            details={"condition": "moon_conjunct_rahu"},
        ))

    # C4: Moon conjunct Ketu
    if moon_house == ketu_house:
        reasons.append("Moon conjunct Ketu")
        evidence.append(Evidence(
            evidence_type=EvidenceType.CONJUNCTION,
            subject="Moon-Ketu conjunction",
            value={"moon_house": moon_house, "ketu_house": ketu_house},
            expected="No conjunction",
            actual="Moon and Ketu in same house",
            source="ChartFacts",
            significance="Moon (karaka for mother) afflicted by Ketu",
            details={"condition": "moon_conjunct_ketu"},
        ))

    # C5: Rahu in 9th house
    if rahu_house == 9:
        reasons.append("Rahu in 9th house")
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject="Rahu in 9th house",
            value={"rahu_house": rahu_house},
            expected="Rahu not in 9th",
            actual="Rahu in 9th house (House of Ancestors/Dharma)",
            source="ChartFacts",
            significance="Rahu in 9th — ancestral affliction indicator",
            details={"condition": "rahu_9th"},
        ))

    # C6: Ketu in 9th house
    if ketu_house == 9:
        reasons.append("Ketu in 9th house")
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject="Ketu in 9th house",
            value={"ketu_house": ketu_house},
            expected="Ketu not in 9th",
            actual="Ketu in 9th house (House of Ancestors/Dharma)",
            source="ChartFacts",
            significance="Ketu in 9th — ancestral affliction indicator",
            details={"condition": "ketu_9th"},
        ))

    if not reasons:
        evidence.append(Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Pitru Dosha scan",
            value="none",
            expected="Any of 6 conditions",
            actual="No conditions met",
            source="ChartFacts",
            significance="Pitru Dosha not formed",
        ))

    return bool(reasons), evidence


# ============================================================
# CANCELLATION
# ============================================================

def pitru_cancellation(ctx, result, cancel_rule=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate cancellation for Pitru Dosha.
    
    Very few universally agreed cancellation rules.
    Jupiter in Ascendant or aspecting the afflicted planet is
    the most commonly cited mitigating factor.
    
    NOTE: No full cancellation is claimed — this is partial at best.
    """
    evidence: List[Evidence] = []

    jup_house = ctx.get_planet_house("Jupiter")
    if jup_house is not None and jup_house == 1:
        evidence.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject="Jupiter in Ascendant",
            value={"jupiter_house": 1},
            expected="No Jupiter in 1st",
            actual="Jupiter in 1st house",
            source="ChartFacts",
            significance="Jupiter in Ascendant — partial mitigation (not full cancellation)",
            details={"cancellation_type": "jupiter_ascendant_partial"},
        ))

    return False, evidence  # No full cancellation for Pitru Dosha


# ============================================================
# MITIGATION
# ============================================================

def pitru_mitigation(ctx, result, mit_rule=None) -> Tuple[bool, List[Evidence]]:
    """
    Evaluate mitigation for Pitru Dosha.
    
    Mitigation: Jupiter aspect on afflicted planet or strong Jupiter.
    """
    evidence: List[Evidence] = []
    mitigated = False

    jup_house = ctx.get_planet_house("Jupiter")
    if jup_house is not None:
        # Jupiter in 1st = protective
        if jup_house == 1:
            mitigated = True
            evidence.append(Evidence(
                evidence_type=EvidenceType.PLANET_IN_HOUSE,
                subject="Jupiter in Ascendant protection",
                value={"jupiter_house": 1},
                expected="Jupiter not in 1st",
                actual="Jupiter in 1st — protective",
                source="ChartFacts",
                significance="Jupiter in Ascendant mitigates",
                details={"mitigation_type": "jupiter_ascendant"},
            ))

    return mitigated, evidence


# ============================================================
# SEVERITY
# ============================================================

def pitru_severity(ctx, formed: bool, evidence: List[Evidence]) -> DoshaSeverity:
    """
    Categorical severity for Pitru Dosha.
    
    No validated classical severity scale exists.
    We count the number of conditions met as a rough indicator.
    """
    if not formed:
        return DoshaSeverity.NONE

    condition_count = sum(
        1 for e in evidence
        if e.evidence_type in (EvidenceType.CONJUNCTION, EvidenceType.PLANET_IN_HOUSE)
        and (e.details or {}).get("condition")
    )

    if condition_count >= 3:
        return DoshaSeverity.HIGH
    elif condition_count >= 2:
        return DoshaSeverity.MODERATE
    else:
        return DoshaSeverity.LOW


# ============================================================
# RULE DEFINITION
# ============================================================

def build_pitru_dosha() -> RuleDefinition:
    provenance_notes = (
        "TRADITION_DEPENDENT / UNVERIFIED. NOT a clearly defined classical "
        "Parashari dosha in BPHS. The concept of ancestral affliction (Pitri) "
        "is traditional, but the specific astrological formation rules are "
        "largely modern synthesis. Implemented conditions are the most commonly "
        "cited: Sun/Moon conjunct Rahu/Ketu, Rahu/Ketu in 9th house. "
        "No deterministic predictions should be generated. "
        "Cancellation rules are very few and not universally agreed."
    )

    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id="DOSHA.PITRU.MODERN_COMMON",
            rule_version="1.0.0",
            name="Pitru Dosha (Modern Common Definition)",
            category=RuleCategory.DOSHA,
            tradition=RuleTradition.TRADITION_DEPENDENT,
            school_method="MODERN_COMMON",
            status=RuleStatus.ENABLED,
            description=(
                "Ancestral affliction: Sun/Moon conjunct Rahu/Ketu, "
                "or Rahu/Ketu in 9th house from Lagna."
            ),
            provenance=Provenance(
                source_type=SourceType.UNVERIFIED,
                source_name="Modern synthesis (multiple secondary sources)",
                source_reference="UNVERIFIED",
                tradition=RuleTradition.TRADITION_DEPENDENT,
                method="MODERN_COMMON",
                implementation_version="1.0.0",
                notes=provenance_notes,
            ),
            confidence=ConfidenceLevel.TRADITION_DEPENDENT,
            tags=["pitru", "ancestral", "rahu", "ketu", "sun", "moon", "tradition_dependent"],
            enabled=True,
        ),
        formation_conditions=[
            Condition(type="pitru_formation", params={})
        ],
        strength_conditions=[],
        activation_rules=[],
        cancellation_rules=[
            CancellationRule(
                rule_id="DOSHA.PITRU.MODERN_COMMON.CANCEL",
                description="Jupiter in Ascendant (partial only — no full cancellation)",
                evaluator="pitru_cancellation",
                is_partial=True,
            )
        ],
        mitigation_rules=[
            MitigationRule(
                rule_id="DOSHA.PITRU.MODERN_COMMON.MITIG",
                description="Jupiter in Ascendant protection",
                evaluator="pitru_mitigation",
                strength_impact="partial",
            )
        ],
        required_evidence=[
            EvidenceType.CONJUNCTION,
            EvidenceType.PLANET_IN_HOUSE,
        ],
    )


PITRU_RULES: List[RuleDefinition] = [build_pitru_dosha()]

PITRU_FORMATION_EVALUATORS = {
    "pitru_formation": pitru_formation,
}
