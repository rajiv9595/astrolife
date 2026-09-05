"""
Upapada Engine — Astrolife V2 Phase 5D

Calculates deterministic Upapada Lagna (UL / Gauna Pada / A12) derived from the 12th house.
Produces structured mathematical facts and derivation steps. Zero predictions.
"""
from __future__ import annotations
from typing import Optional, Dict, Any

from core.calculation.models import ChartFacts
from .profile import JaiminiCalculationProfile
from .models import UpapadaDetails, ArudhaPadaItem
from .arudha import calculate_single_arudha, SIGNS


def calculate_upapada(
    chart_facts: ChartFacts,
    profile: Optional[JaiminiCalculationProfile] = None,
    precomputed_a12: Optional[ArudhaPadaItem] = None
) -> UpapadaDetails:
    """
    Calculates Upapada Lagna (UL / A12) from canonical ChartFacts.
    """
    if profile is None:
        profile = JaiminiCalculationProfile()
        
    if precomputed_a12 is not None:
        a12 = precomputed_a12
    else:
        asc_sign_name = chart_facts.ascendant.sign.name
        asc_sign_idx = SIGNS.index(asc_sign_name)
        
        planet_sign_map: Dict[str, int] = {}
        for p_name, p_data in chart_facts.planets.items():
            s_name = p_data.sign.name
            if s_name in SIGNS:
                planet_sign_map[p_name] = SIGNS.index(s_name)
                
        a12 = calculate_single_arudha(
            house_num=12,
            ascendant_sign_idx=asc_sign_idx,
            planet_sign_map=planet_sign_map,
            profile=profile
        )
        
    evidence = [
        "Upapada Lagna (UL) is the Arudha Pada of the 12th house.",
        *a12.evidence
    ]
    
    return UpapadaDetails(
        source_house=12,
        source_sign=a12.source_sign,
        source_sign_num=a12.source_sign_num,
        lord=a12.house_lord,
        lord_sign=a12.lord_sign,
        lord_sign_num=a12.lord_sign_num,
        distance_signs=a12.distance_signs,
        raw_projected_sign=a12.raw_projected_sign,
        raw_projected_sign_num=a12.raw_projected_sign_num,
        exception_applied=a12.exception_applied,
        final_sign=a12.final_sign,
        final_sign_num=a12.final_sign_num,
        evidence=evidence
    )
