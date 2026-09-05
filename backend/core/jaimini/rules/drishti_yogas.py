"""
Phase 5E — Rashi-Drishti yogas.

Uses ONLY the accepted Phase 5D Rashi Drishti engine. No Parashari planetary
aspects, no Western aspects, no orbs. Evidence always cites source sign,
target sign, the drishti relationship, and occupying planets.
"""
from __future__ import annotations
from typing import Any

from .models import FormationEvidenceItem, YogaOutcome
from .predicates import (
    benefic_support_for_sign,
    karaka_planet,
    karaka_sign,
    karaka_identity_tied,
    planet_aspects_sign,
    planets_aspecting_sign,
    signs_in_mutual_drishti,
)
from ...rules.enums import CancellationStatus, MitigationStatus


def _tie_none(jaimini_facts: Any, codes: list, tolerance: float) -> tuple:
    tied, detail = karaka_identity_tied(jaimini_facts, codes, tolerance)
    if tied:
        return CancellationStatus.PARTIAL, [f"CANCELLATION (PARTIAL): {detail}"]
    return CancellationStatus.NONE, [f"No cancellation: {detail}"]


def evaluate_ak_amk_mutual_drishti(
    chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float
) -> YogaOutcome:
    """AK and AmK occupied signs in mutual Rashi Drishti (same sign excluded)."""
    ak, amk = karaka_planet(jaimini_facts, "AK"), karaka_planet(jaimini_facts, "AmK")
    ak_sign, amk_sign = karaka_sign(jaimini_facts, "AK"), karaka_sign(jaimini_facts, "AmK")
    formed = bool(ak and amk and ak_sign and amk_sign and signs_in_mutual_drishti(ak_sign, amk_sign))
    ev = [
        FormationEvidenceItem(
            condition="mutual_rashi_drishti(AK_sign, AmK_sign)",
            actual_value=f"{ak} in {ak_sign}; {amk} in {amk_sign}; mutual={formed}",
            expected_value="mutual Rashi Drishti (same-sign excluded)",
            source_fact="JaiminiFacts.rashi_drishti + JaiminiFacts.chara_karakas",
            passed=formed,
        )
    ]
    cstat, cev = _tie_none(jaimini_facts, ["AK", "AmK"], tolerance)
    supported, mdetail = benefic_support_for_sign(chart_facts, jaimini_facts, ak_sign) if ak_sign else (False, "No focal sign.")
    return YogaOutcome(
        formed=formed, formation_evidence=ev,
        cancellation_status=cstat, cancellation_evidence=cev,
        mitigation_status=MitigationStatus.PARTIAL if supported else MitigationStatus.NONE,
        mitigation_evidence=[mdetail],
        relevant_planets=sorted(p for p in [ak, amk] if p),
        relevant_signs=sorted(s for s in [ak_sign, amk_sign] if s),
        dependencies=["JaiminiFacts.chara_karakas", "JaiminiFacts.rashi_drishti"],
        notes="AK–AmK mutual Rashi Drishti combination; condition formed, no outcome claimed.",
    )


def _karaka_on_al(
    chart_facts: Any, jaimini_facts: Any, code: str, tolerance: float
) -> YogaOutcome:
    planet = karaka_planet(jaimini_facts, code)
    psign = karaka_sign(jaimini_facts, code)
    al = jaimini_facts.arudha_lagna.final_sign
    formed = bool(planet and planet_aspects_sign(jaimini_facts, planet, al))
    aspecters = planets_aspecting_sign(jaimini_facts, al)
    ev = [
        FormationEvidenceItem(
            condition=f"{code}_aspects_AL",
            actual_value=f"{code}={planet} in {psign}; AL={al}; aspects_AL={formed}; planets_aspecting_AL={aspecters}",
            expected_value=f"{code} casts Rashi Drishti on AL",
            source_fact="JaiminiFacts.rashi_drishti.planet_aspects",
            passed=formed,
        )
    ]
    cstat, cev = _tie_none(jaimini_facts, [code], tolerance)
    supported, mdetail = benefic_support_for_sign(chart_facts, jaimini_facts, al)
    return YogaOutcome(
        formed=formed, formation_evidence=ev,
        cancellation_status=cstat, cancellation_evidence=cev,
        mitigation_status=MitigationStatus.PARTIAL if supported else MitigationStatus.NONE,
        mitigation_evidence=[mdetail],
        relevant_planets=[planet] if planet else [],
        relevant_signs=sorted(s for s in [psign, al] if s),
        dependencies=["JaiminiFacts.chara_karakas", "JaiminiFacts.arudha_padas", "JaiminiFacts.rashi_drishti"],
        notes=f"{code}–AL Rashi Drishti combination; condition formed, no outcome claimed.",
    )


def evaluate_amk_on_al(chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float) -> YogaOutcome:
    """AmK casts Rashi Drishti on AL via its occupied sign."""
    return _karaka_on_al(chart_facts, jaimini_facts, "AmK", tolerance)


def evaluate_ak_on_al(chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float) -> YogaOutcome:
    """AK casts Rashi Drishti on AL via its occupied sign."""
    return _karaka_on_al(chart_facts, jaimini_facts, "AK", tolerance)
