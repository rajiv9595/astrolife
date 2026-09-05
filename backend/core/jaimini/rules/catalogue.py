"""
Phase 5E — Jaimini yoga catalogue.

Stable rule IDs, honest provenance (all source_reference UNVERIFIED,
confidence TRADITION_DEPENDENT). Origin labels record consensus level only:
CLASSICAL_JAIMINI = broad classical consensus; TRADITION_DEPENDENT = narrower
or variant-sensitive attribution. No MODERN_SYNTHESIS rules are implemented.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from ...rules.enums import ConfidenceLevel, SourceType

from . import arudha_yogas, drishti_yogas, karaka_yogas, karakamsha_yogas


@dataclass(frozen=True)
class JaiminiRuleSpec:
    rule_id: str
    name: str
    origin_label: str
    method: str
    description: str
    evaluator: Callable[..., Any]
    rule_version: str = "1.0.0"


CATALOGUE: List[JaiminiRuleSpec] = [
    JaiminiRuleSpec(
        "JAI.KARAKA.AK_AMK_CONJUNCTION", "AK–AmK Conjunction Combination",
        "CLASSICAL_JAIMINI", "ak_amk_conjunction",
        "Atmakaraka and Amatyakaraka occupy the same D1 sign.",
        karaka_yogas.evaluate_ak_amk_conjunction,
    ),
    JaiminiRuleSpec(
        "JAI.KARAKA.AK_KENDRA_FROM_AL", "AK in Kendra from AL",
        "TRADITION_DEPENDENT", "ak_kendra_from_al",
        "Atmakaraka occupies a kendra (1/4/7/10) counted whole-sign from Arudha Lagna.",
        karaka_yogas.evaluate_ak_kendra_from_al,
    ),
    JaiminiRuleSpec(
        "JAI.KARAKA.DK_UL_SAMBANDHA", "DK–UL Sambandha",
        "TRADITION_DEPENDENT", "dk_ul_sambandha",
        "Darakaraka occupies UL, lords UL, or is in mutual Rashi Drishti with the UL lord.",
        karaka_yogas.evaluate_dk_ul_sambandha,
    ),
    JaiminiRuleSpec(
        "JAI.DRISHTI.AK_AMK_MUTUAL", "AK–AmK Mutual Rashi Drishti",
        "CLASSICAL_JAIMINI", "ak_amk_mutual_drishti",
        "AK and AmK occupied signs aspect each other (same-sign excluded).",
        drishti_yogas.evaluate_ak_amk_mutual_drishti,
    ),
    JaiminiRuleSpec(
        "JAI.DRISHTI.AMK_ON_AL", "AmK Rashi Drishti on AL",
        "TRADITION_DEPENDENT", "amk_on_al",
        "Amatyakaraka casts Rashi Drishti on Arudha Lagna via its occupied sign.",
        drishti_yogas.evaluate_amk_on_al,
    ),
    JaiminiRuleSpec(
        "JAI.DRISHTI.AK_ON_AL", "AK Rashi Drishti on AL",
        "TRADITION_DEPENDENT", "ak_on_al",
        "Atmakaraka casts Rashi Drishti on Arudha Lagna via its occupied sign.",
        drishti_yogas.evaluate_ak_on_al,
    ),
    JaiminiRuleSpec(
        "JAI.ARUDHA.AL_BENEFIC_OCCUPANCY", "Benefic in AL",
        "CLASSICAL_JAIMINI", "al_benefic_occupancy",
        "A natural benefic occupies Arudha Lagna in D1.",
        arudha_yogas.evaluate_al_benefic_occupancy,
    ),
    JaiminiRuleSpec(
        "JAI.ARUDHA.AL_LORD_KENDRA_TRINE", "AL Lord in Kendra/Trikona from AL",
        "CLASSICAL_JAIMINI", "al_lord_kendra_trine",
        "The AL lord occupies a kendra or trikona counted whole-sign from AL.",
        arudha_yogas.evaluate_al_lord_kendra_trine,
    ),
    JaiminiRuleSpec(
        "JAI.ARUDHA.DHANA_A2_A11", "A2–A11 Dhana Combination",
        "CLASSICAL_JAIMINI", "dhana_a2_a11",
        "A2 and A11 share a sign, share mutual Rashi Drishti, or share a lord.",
        arudha_yogas.evaluate_dhana_a2_a11,
    ),
    JaiminiRuleSpec(
        "JAI.ARUDHA.A7_UL_ALIGNMENT", "A7–UL Alignment",
        "TRADITION_DEPENDENT", "a7_ul_alignment",
        "Dara Pada (A7) and Upapada (UL) fall in the same sign.",
        arudha_yogas.evaluate_a7_ul_alignment,
    ),
    JaiminiRuleSpec(
        "JAI.KARAKAMSHA.BENEFIC_OCCUPANCY", "Benefic in Karakamsha (D9)",
        "TRADITION_DEPENDENT", "karakamsha_benefic_occupancy",
        "A natural benefic occupies the Karakamsha (AK's D9 sign) in D9.",
        karakamsha_yogas.evaluate_karakamsha_benefic,
    ),
    JaiminiRuleSpec(
        "JAI.SWAMSA.BENEFIC_OCCUPANCY", "Benefic in Swamsa (D9)",
        "TRADITION_DEPENDENT", "swamsa_benefic_occupancy",
        "A natural benefic occupies the Swamsa (D9 Lagna sign) in D9.",
        karakamsha_yogas.evaluate_swamsa_benefic,
    ),
]


def get_catalogue() -> List[JaiminiRuleSpec]:
    return list(CATALOGUE)


def get_rule_ids() -> List[str]:
    return [r.rule_id for r in CATALOGUE]


def describe_catalogue() -> List[Dict[str, Any]]:
    """JSON-serializable catalogue summary for docs/snapshot tooling."""
    return [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "origin_label": r.origin_label,
            "method": r.method,
            "description": r.description,
            "tradition": "JAIMINI",
            "confidence": ConfidenceLevel.TRADITION_DEPENDENT.value,
            "source_type": SourceType.UNVERIFIED.value,
            "source_reference": "UNVERIFIED",
            "rule_version": r.rule_version,
        }
        for r in CATALOGUE
    ]
