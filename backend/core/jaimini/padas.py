"""
12 Arudha Padas Engine — Astrolife V2 Phase 5D

Calculates all 12 Arudha Padas (A1 through A12) including Arudha Lagna (AL / A1)
and Upapada Lagna (UL / A12) with full structured evidence.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any

from ..calculation.models import ChartFacts
from .profile import JaiminiCalculationProfile
from .models import ArudhaPadaItem
from .arudha import calculate_single_arudha, SIGNS


def calculate_all_arudha_padas(
    chart_facts: ChartFacts,
    profile: Optional[JaiminiCalculationProfile] = None
) -> Dict[int, ArudhaPadaItem]:
    """
    Calculates all 12 Arudha Padas from canonical ChartFacts.
    Returns a dictionary mapping house number (1-12) to ArudhaPadaItem.
    """
    if profile is None:
        profile = JaiminiCalculationProfile()
        
    asc_sign_name = chart_facts.ascendant.sign.name
    asc_sign_idx = SIGNS.index(asc_sign_name)
    
    # Build planet sign map (0-indexed 0..11)
    planet_sign_map: Dict[str, int] = {}
    for p_name, p_data in chart_facts.planets.items():
        s_name = p_data.sign.name
        if s_name in SIGNS:
            planet_sign_map[p_name] = SIGNS.index(s_name)
            
    padas: Dict[int, ArudhaPadaItem] = {}
    
    for h in range(1, 13):
        pada_item = calculate_single_arudha(
            house_num=h,
            ascendant_sign_idx=asc_sign_idx,
            planet_sign_map=planet_sign_map,
            profile=profile
        )
        padas[h] = pada_item
        
    return padas
