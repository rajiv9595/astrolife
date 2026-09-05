"""
Phase 5B — cancellation / mitigation evaluators (separate from formation).

Each evaluator is evidence-backed and never overwrites formation evidence.
Signatures match RuleEvaluator custom-evaluator convention:
    (context, result, rule) -> (applies: bool, evidence: List[Evidence])
Cancellation evaluator names: 'parashari_cancellation_generic'.
Mitigation evaluator names: 'parashari_mitigation_generic'.
Rule metadata declares is_partial / strength_impact so the evaluator maps
to PARTIAL vs FULL / PARTIAL vs SIGNIFICANT.
"""
from __future__ import annotations
from typing import Dict, List, Tuple

from ..models import Evidence
from ..enums import EvidenceType
from .structural import (
    house_of, sign_of, NATURAL_BENEFICS, is_dusthana_house,
)


def _relevant_planets(ctx, result) -> List[str]:
    planets = list(getattr(result, "relevant_planets", []) or [])
    if planets:
        return planets
    # fallback: parse evidence subjects
    found = []
    for e in getattr(result, "evidence", []) or []:
        subj = getattr(e, "subject", "") or ""
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            if p in subj and p not in found:
                found.append(p)
    return found


def _is_debilitated_no_bhanga(ctx, planet: str) -> bool:
    if not ctx.is_debilitated(planet):
        return False
    try:
        from .neecha_bhanga import neecha_bhanga_conditions
        conds = neecha_bhanga_conditions(ctx, planet)
        return not any(c["met"] for c in conds)
    except Exception:
        return True


def generic_cancellation_evaluator(context, result, rule) -> Tuple[bool, List[Evidence]]:
    """Applies when: relevant planet debilitated without bhanga, or in
    Dusthana, or hemmed by malefics (same house as Saturn/Mars/Rahu/Ketu
    without benefic in same house). Returns applies=True if any hit."""
    planets = _relevant_planets(context, result)
    evidence: List[Evidence] = []
    hit = False
    for planet in planets:
        h = house_of(context, planet)
        if context.is_debilitated(planet):
            no_bhanga = _is_debilitated_no_bhanga(context, planet)
            evidence.append(Evidence(
                evidence_type=EvidenceType.PLANET_DIGNITY,
                subject=f"{planet} debilitation vs bhanga",
                value="debilitated_without_bhanga" if no_bhanga else "debilitated_with_bhanga",
                expected="no uncancelled debilitation",
                actual=context.get_dignity_category(planet),
                source="StrengthReport",
                significance=f"{planet} debilitated {'without' if no_bhanga else 'with'} Neecha Bhanga",
            ))
            if no_bhanga:
                hit = True
        if h is not None and is_dusthana_house(h):
            evidence.append(Evidence(
                evidence_type=EvidenceType.DUSTHANA,
                subject=f"{planet} in Dusthana",
                value=h, expected="non-Dusthana for full effect",
                actual=f"house {h}", source="ChartFacts",
                significance=f"{planet} in Dusthana house {h} weakens yoga",
            ))
            hit = True
        # malefic same-house pressure without benefic companion
        housemates = context.get_planets_in_house(h) if h else []
        malefics = [p for p in housemates if p in ("Saturn", "Mars", "Rahu", "Ketu") and p != planet]
        benefics = [p for p in housemates if p in NATURAL_BENEFICS and p != planet]
        if malefics and not benefics:
            evidence.append(Evidence(
                evidence_type=EvidenceType.ASPECT,
                subject=f"{planet} malefic association",
                value={"malefics": malefics, "benefics": benefics},
                expected="no unrelieved malefic pressure",
                actual=f"with {malefics}", source="ChartFacts",
                significance=f"{planet} with malefics {malefics}, no benefic relief",
            ))
            hit = True
    if not evidence:
        evidence.append(Evidence(
            evidence_type=EvidenceType.CUSTOM, subject="cancellation scan",
            value="no cancellation trigger", expected="clean",
            actual="clean", source="RuleContext",
            significance="no debilitation/dusthana/malefic trigger found",
        ))
    return hit, evidence


def generic_mitigation_evaluator(context, result, rule) -> Tuple[bool, List[Evidence]]:
    """Applies when: benefic conjunction/aspect on relevant planets, or
    relevant planet in exaltation/own sign, or in Kendra/Trikona."""
    planets = _relevant_planets(context, result)
    evidence: List[Evidence] = []
    hit = False
    for planet in planets:
        h = house_of(context, planet)
        housemates = context.get_planets_in_house(h) if h else []
        benefic_mates = [p for p in housemates if p in NATURAL_BENEFICS and p != planet]
        aspecting_benefics = [b for b in NATURAL_BENEFICS if b != planet
                              and context.get_planet_aspecting_planet(b, planet)]
        if benefic_mates or aspecting_benefics:
            evidence.append(Evidence(
                evidence_type=EvidenceType.ASPECT,
                subject=f"{planet} benefic support",
                value={"conjunct": benefic_mates, "aspecting": aspecting_benefics},
                expected="benefic support", actual="present", source="ChartFacts",
                significance=f"{planet} supported by {benefic_mates + aspecting_benefics}",
            ))
            hit = True
        if context.is_exalted(planet) or context.is_own_sign(planet) or context.is_moolatrikona(planet):
            evidence.append(Evidence(
                evidence_type=EvidenceType.PLANET_DIGNITY,
                subject=f"{planet} dignity mitigation",
                value=context.get_dignity_category(planet),
                expected="strong dignity", actual=context.get_dignity_category(planet),
                source="StrengthReport",
                significance=f"{planet} dignity {context.get_dignity_category(planet)} supports yoga",
            ))
            hit = True
        if h is not None and h in (1, 4, 7, 10, 5, 9):
            evidence.append(Evidence(
                evidence_type=EvidenceType.KENDRA_TRIKONA,
                subject=f"{planet} house mitigation",
                value=h, expected="Kendra/Trikona", actual=f"house {h}",
                source="ChartFacts",
                significance=f"{planet} in house {h} supports yoga",
            ))
            hit = True
    if not hit:
        evidence.append(Evidence(
            evidence_type=EvidenceType.CUSTOM, subject="mitigation scan",
            value="no mitigation", expected="support factors",
            actual="none", source="RuleContext",
            significance="no benefic/dignity/house mitigation found",
        ))
    return hit, evidence


def evaluate_cancellation(context, result, rule):
    return generic_cancellation_evaluator(context, result, rule)


def evaluate_mitigation(context, result, rule):
    return generic_mitigation_evaluator(context, result, rule)


CANCELLATION_EVALUATORS: Dict[str, object] = {
    "parashari_cancellation_generic": generic_cancellation_evaluator,
    "default_cancellation": generic_cancellation_evaluator,
}

MITIGATION_EVALUATORS: Dict[str, object] = {
    "parashari_mitigation_generic": generic_mitigation_evaluator,
    "default_mitigation": generic_mitigation_evaluator,
}
