"""
Phase 5E — Arudha / AL / UL yogas.

Consumes canonical ArudhaPadaItem facts only; Arudha arithmetic is never
recomputed here. Pada evidence (source/lord/distance/raw/exception/final) is
already exposed by the 5D engine and referenced via dependencies.
"""
from __future__ import annotations
from typing import Any

from .models import FormationEvidenceItem, YogaOutcome
from .predicates import (
    benefic_support_for_sign,
    d1_sign_of,
    house_of_sign_from,
    is_kendra_or_trikona_from,
    planets_in_d1_sign,
    sign_lord,
    signs_in_mutual_drishti,
    NATURAL_BENEFICS,
)
from ...rules.enums import CancellationStatus, MitigationStatus


def _no_structural_cancellation(reason: str) -> tuple:
    return CancellationStatus.NONE, [f"No cancellation: {reason}"]


def evaluate_al_benefic_occupancy(
    chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float
) -> YogaOutcome:
    """A natural benefic occupies AL in D1."""
    al = jaimini_facts.arudha_lagna.final_sign
    occupants = planets_in_d1_sign(chart_facts, al)
    benefics = [p for p in occupants if p in NATURAL_BENEFICS]
    formed = len(benefics) > 0
    ev = [
        FormationEvidenceItem(
            condition="benefic occupies AL (D1)",
            actual_value=f"AL={al}; occupants={occupants}; benefics={benefics}",
            expected_value=">=1 of Jupiter/Venus/Mercury/Moon in AL",
            source_fact="JaiminiFacts.arudha_padas[1] + ChartFacts.planets",
            passed=formed,
        )
    ]
    cstat, cev = _no_structural_cancellation("occupancy is factual; malefic co-presence is not modelled as cancellation.")
    supported, mdetail = benefic_support_for_sign(chart_facts, jaimini_facts, al)
    return YogaOutcome(
        formed=formed, formation_evidence=ev,
        cancellation_status=cstat, cancellation_evidence=cev,
        mitigation_status=MitigationStatus.PARTIAL if supported else MitigationStatus.NONE,
        mitigation_evidence=[mdetail],
        relevant_planets=benefics, relevant_signs=[al],
        dependencies=["JaiminiFacts.arudha_padas", "ChartFacts.planets"],
        notes="AL benefic-occupancy combination; condition formed, no outcome claimed.",
    )


def evaluate_al_lord_kendra_trine(
    chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float
) -> YogaOutcome:
    """AL lord occupies a kendra or trikona counted whole-sign from AL."""
    al_item = jaimini_facts.arudha_lagna
    al, lord = al_item.final_sign, al_item.house_lord
    lord_sign = d1_sign_of(chart_facts, lord)
    house = house_of_sign_from(lord_sign, al) if lord_sign else None
    formed = house is not None and is_kendra_or_trikona_from(lord_sign, al)
    ev = [
        FormationEvidenceItem(
            condition="house_of(AL-lord from AL) in {1,4,5,7,9,10}",
            actual_value=f"AL={al}; lord={lord} in {lord_sign}; house={house}",
            expected_value="kendra or trikona from AL",
            source_fact="JaiminiFacts.arudha_padas[1] + ChartFacts.planets",
            passed=formed,
        )
    ]
    cstat, cev = _no_structural_cancellation("lord placement is factual; no defensible structural cancellation.")
    supported, mdetail = benefic_support_for_sign(chart_facts, jaimini_facts, al)
    return YogaOutcome(
        formed=formed, formation_evidence=ev,
        cancellation_status=cstat, cancellation_evidence=cev,
        mitigation_status=MitigationStatus.PARTIAL if supported else MitigationStatus.NONE,
        mitigation_evidence=[mdetail],
        relevant_planets=[lord] if lord else [],
        relevant_signs=sorted(s for s in [al, lord_sign] if s),
        relevant_houses=[house] if house else [],
        dependencies=["JaiminiFacts.arudha_padas", "ChartFacts.planets"],
        notes="AL-lord kendra/trikona combination; condition formed, no outcome claimed.",
    )


def evaluate_dhana_a2_a11(
    chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float
) -> YogaOutcome:
    """A2–A11 wealth-related combination: same sign, mutual Rashi Drishti, or
    shared lord. Mode recorded in evidence."""
    a2 = jaimini_facts.arudha_padas[2].final_sign
    a11 = jaimini_facts.arudha_padas[11].final_sign
    mode = "none"
    if a2 == a11:
        mode = "same_sign"
    elif signs_in_mutual_drishti(a2, a11):
        mode = "mutual_drishti"
    elif sign_lord(a2) == sign_lord(a11):
        mode = "shared_lord"
    formed = mode != "none"
    ev = [
        FormationEvidenceItem(
            condition="A2==A11 OR mutual-drishti(A2,A11) OR lord(A2)==lord(A11)",
            actual_value=f"A2={a2} (lord {sign_lord(a2)}); A11={a11} (lord {sign_lord(a11)}); mode={mode}",
            expected_value="same_sign | mutual_drishti | shared_lord",
            source_fact="JaiminiFacts.arudha_padas",
            passed=formed,
        )
    ]
    cstat, cev = _no_structural_cancellation("pada relationship is factual; no defensible structural cancellation.")
    m_a2, d_a2 = benefic_support_for_sign(chart_facts, jaimini_facts, a2)
    m_a11, d_a11 = benefic_support_for_sign(chart_facts, jaimini_facts, a11)
    supported = m_a2 or m_a11
    return YogaOutcome(
        formed=formed, formation_evidence=ev,
        cancellation_status=cstat, cancellation_evidence=cev,
        mitigation_status=MitigationStatus.PARTIAL if supported else MitigationStatus.NONE,
        mitigation_evidence=[d_a2, d_a11],
        relevant_planets=[],
        relevant_signs=sorted({a2, a11}),
        dependencies=["JaiminiFacts.arudha_padas"],
        notes="A2–A11 wealth-related combination; condition formed, no wealth outcome claimed.",
    )


def evaluate_a7_ul_alignment(
    chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float
) -> YogaOutcome:
    """A7 (Dara Pada) and UL fall in the same sign. Family-related combination."""
    a7 = jaimini_facts.arudha_padas[7].final_sign
    ul = jaimini_facts.upapada.final_sign
    formed = a7 == ul
    ev = [
        FormationEvidenceItem(
            condition="A7 == UL",
            actual_value=f"A7={a7}; UL={ul}",
            expected_value="same sign",
            source_fact="JaiminiFacts.arudha_padas[7] + JaiminiFacts.upapada",
            passed=formed,
        )
    ]
    cstat, cev = _no_structural_cancellation("pada relationship is factual; no defensible structural cancellation.")
    supported, mdetail = benefic_support_for_sign(chart_facts, jaimini_facts, ul)
    return YogaOutcome(
        formed=formed, formation_evidence=ev,
        cancellation_status=cstat, cancellation_evidence=cev,
        mitigation_status=MitigationStatus.PARTIAL if supported else MitigationStatus.NONE,
        mitigation_evidence=[mdetail],
        relevant_planets=[], relevant_signs=sorted({a7, ul}),
        dependencies=["JaiminiFacts.arudha_padas", "JaiminiFacts.upapada"],
        notes="A7–UL family-related combination; condition formed, no marriage outcome claimed.",
    )
