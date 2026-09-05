"""
Phase 5E — Chara-Karaka yogas.

Consumes CharaKarakasReport output only. Never hardcodes karaka assignments;
7-karaka and 8-karaka facts flow through unchanged (pipeline guards mixing).
"""
from __future__ import annotations
from typing import Any

from .models import FormationEvidenceItem, YogaOutcome
from .predicates import (
    d1_sign_of,
    karaka_planet,
    karaka_sign,
    karaka_identity_tied,
    house_of_sign_from,
    is_kendra_from,
    sign_lord,
    signs_in_mutual_drishti,
)
from ...rules.enums import CancellationStatus, MitigationStatus
from .predicates import benefic_support_for_sign


def _tie_cancellation(jaimini_facts: Any, codes: list, tolerance: float) -> tuple:
    tied, detail = karaka_identity_tied(jaimini_facts, codes, tolerance)
    if tied:
        return CancellationStatus.PARTIAL, [f"CANCELLATION (PARTIAL): {detail}"]
    return CancellationStatus.NONE, [f"No cancellation: {detail}"]


def evaluate_ak_amk_conjunction(
    chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float
) -> YogaOutcome:
    """AK and AmK occupy the same D1 sign (conjunction by co-occupation)."""
    ak, amk = karaka_planet(jaimini_facts, "AK"), karaka_planet(jaimini_facts, "AmK")
    ak_sign, amk_sign = karaka_sign(jaimini_facts, "AK"), karaka_sign(jaimini_facts, "AmK")
    formed = ak is not None and amk is not None and ak_sign == amk_sign
    ev = [
        FormationEvidenceItem(
            condition="AK_sign == AmK_sign",
            actual_value=f"{ak} in {ak_sign}; {amk} in {amk_sign}",
            expected_value="same D1 sign",
            source_fact="JaiminiFacts.chara_karakas",
            passed=formed,
        )
    ]
    cstat, cev = _tie_cancellation(jaimini_facts, ["AK", "AmK"], tolerance)
    supported, mdetail = benefic_support_for_sign(chart_facts, jaimini_facts, ak_sign) if ak_sign else (False, "No focal sign.")
    return YogaOutcome(
        formed=formed, formation_evidence=ev,
        cancellation_status=cstat, cancellation_evidence=cev,
        mitigation_status=MitigationStatus.PARTIAL if supported else MitigationStatus.NONE,
        mitigation_evidence=[mdetail],
        relevant_planets=sorted(p for p in [ak, amk] if p),
        relevant_signs=sorted(s for s in [ak_sign, amk_sign] if s),
        dependencies=["JaiminiFacts.chara_karakas"],
        notes="Atmakaraka–Amatyakaraka conjunction combination; condition formed, no outcome claimed.",
    )


def evaluate_ak_kendra_from_al(
    chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float
) -> YogaOutcome:
    """AK occupies a kendra (1/4/7/10) counted whole-sign from AL."""
    ak, ak_sign = karaka_planet(jaimini_facts, "AK"), karaka_sign(jaimini_facts, "AK")
    al = jaimini_facts.arudha_lagna.final_sign
    house = house_of_sign_from(ak_sign, al) if ak_sign else None
    formed = house is not None and house in (1, 4, 7, 10)
    ev = [
        FormationEvidenceItem(
            condition="house_of(AK_sign from AL) in {1,4,7,10}",
            actual_value=f"{ak} in {ak_sign}; AL={al}; house={house}",
            expected_value="kendra from AL",
            source_fact="JaiminiFacts.arudha_padas[1] + JaiminiFacts.chara_karakas",
            passed=formed,
        )
    ]
    cstat, cev = _tie_cancellation(jaimini_facts, ["AK"], tolerance)
    supported, mdetail = benefic_support_for_sign(chart_facts, jaimini_facts, ak_sign) if ak_sign else (False, "No focal sign.")
    return YogaOutcome(
        formed=formed, formation_evidence=ev,
        cancellation_status=cstat, cancellation_evidence=cev,
        mitigation_status=MitigationStatus.PARTIAL if supported else MitigationStatus.NONE,
        mitigation_evidence=[mdetail],
        relevant_planets=[ak] if ak else [],
        relevant_signs=sorted(s for s in [ak_sign, al] if s),
        relevant_houses=[house] if house else [],
        dependencies=["JaiminiFacts.chara_karakas", "JaiminiFacts.arudha_padas"],
        notes="AK–AL kendra relationship; condition formed, no outcome claimed.",
    )


def evaluate_dk_ul_sambandha(
    chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float
) -> YogaOutcome:
    """DK–UL sambandha: DK occupies UL sign, or DK lords UL sign, or DK and
    the UL lord are in mutual Rashi Drishti. Mode recorded in evidence."""
    dk = karaka_planet(jaimini_facts, "DK")
    dk_sign = karaka_sign(jaimini_facts, "DK")
    ul = jaimini_facts.upapada.final_sign
    ul_lord = sign_lord(ul)
    ul_lord_sign = d1_sign_of(chart_facts, ul_lord)
    mode = "none"
    if dk and dk_sign == ul:
        mode = "occupation"
    elif dk and dk == ul_lord:
        mode = "lordship"
    elif dk and ul_lord_sign and signs_in_mutual_drishti(dk_sign, ul_lord_sign):
        mode = "mutual_drishti"
    formed = mode != "none"
    ev = [
        FormationEvidenceItem(
            condition="DK in UL OR DK lords UL OR mutual-drishti(DK, UL-lord)",
            actual_value=f"DK={dk} in {dk_sign}; UL={ul} (lord {ul_lord} in {ul_lord_sign}); mode={mode}",
            expected_value="occupation | lordship | mutual_drishti",
            source_fact="JaiminiFacts.chara_karakas + JaiminiFacts.upapada + Rashi Drishti",
            passed=formed,
        )
    ]
    cstat, cev = _tie_cancellation(jaimini_facts, ["DK"], tolerance)
    supported, mdetail = benefic_support_for_sign(chart_facts, jaimini_facts, ul)
    return YogaOutcome(
        formed=formed, formation_evidence=ev,
        cancellation_status=cstat, cancellation_evidence=cev,
        mitigation_status=MitigationStatus.PARTIAL if supported else MitigationStatus.NONE,
        mitigation_evidence=[mdetail],
        relevant_planets=sorted(p for p in [dk, ul_lord] if p),
        relevant_signs=sorted(s for s in [dk_sign, ul, ul_lord_sign] if s),
        dependencies=["JaiminiFacts.chara_karakas", "JaiminiFacts.upapada", "JaiminiFacts.rashi_drishti"],
        notes="Darakaraka–Upapada family-related combination; condition formed, no marriage outcome claimed.",
    )
