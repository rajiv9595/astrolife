"""
Karakamsha & Swamsa Engine — Astrolife V2 Phase 5D

Calculates deterministic Karakamsha and Swamsa facts by consuming canonical ChartFacts
and pre-computed VargaFacts (D9 Navamsha).
Does NOT recompute astronomy or divisional charts.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any

from core.calculation.models import ChartFacts
from core.calculation.varga import VargaPosition
from .models import KarakamshaDetails, CharaKarakasReport
from .karakas import calculate_chara_karakas
from .profile import JaiminiCalculationProfile


def calculate_karakamsha(
    chart_facts: ChartFacts,
    varga_facts: Dict[str, Any],
    chara_karakas: Optional[CharaKarakasReport] = None,
    profile: Optional[JaiminiCalculationProfile] = None
) -> KarakamshaDetails:
    """
    Computes Karakamsha and Swamsa facts from canonical facts.
    
    1. Identifies Atmakaraka (AK).
    2. Reads AK's Navamsha (D9) position from varga_facts.
    3. Reads D9 Ascendant (Swamsa Navamsha Lagna) from varga_facts.
    4. Emits structured derivation evidence.
    """
    if chara_karakas is None:
        chara_karakas = calculate_chara_karakas(chart_facts, profile)
        
    ak_item = chara_karakas.karakas.get("AK")
    if ak_item is None:
        raise ValueError("Cannot calculate Karakamsha: Atmakaraka (AK) not found in Chara Karakas report.")
        
    ak_planet = ak_item.planet
    ak_d1_sign = ak_item.sign
    ak_d1_degree = ak_item.degree_in_sign
    
    # Extract D9 Navamsha position from varga_facts
    # varga_facts schema: {"planets": {planet: {"D9": VargaPosition}}, "ascendant": {"D9": VargaPosition}}
    planets_vargas = varga_facts.get("planets", {})
    ak_vargas = planets_vargas.get(ak_planet, {})
    ak_d9 = ak_vargas.get("D9")
    
    if ak_d9 is None:
        raise ValueError(f"Cannot resolve D9 Navamsha position for Atmakaraka '{ak_planet}' from varga_facts.")
        
    if isinstance(ak_d9, dict):
        karakamsha_sign = ak_d9.get("sign", "")
        karakamsha_sign_num = ak_d9.get("sign_num", 0)
        karakamsha_d9_deg = ak_d9.get("degree", 0.0)
    elif isinstance(ak_d9, VargaPosition):
        karakamsha_sign = ak_d9.sign
        karakamsha_sign_num = ak_d9.sign_num
        karakamsha_d9_deg = ak_d9.degree
    else:
        karakamsha_sign = getattr(ak_d9, "sign", "")
        karakamsha_sign_num = getattr(ak_d9, "sign_num", 0)
        karakamsha_d9_deg = getattr(ak_d9, "degree", 0.0)

    # Extract D9 Ascendant (Navamsha Lagna)
    asc_vargas = varga_facts.get("ascendant", {})
    asc_d9 = asc_vargas.get("D9")
    
    if asc_d9 is not None:
        if isinstance(asc_d9, dict):
            swamsa_lagna_sign = asc_d9.get("sign", "")
            swamsa_lagna_sign_num = asc_d9.get("sign_num", 0)
        elif isinstance(asc_d9, VargaPosition):
            swamsa_lagna_sign = asc_d9.sign
            swamsa_lagna_sign_num = asc_d9.sign_num
        else:
            swamsa_lagna_sign = getattr(asc_d9, "sign", "")
            swamsa_lagna_sign_num = getattr(asc_d9, "sign_num", 0)
    else:
        swamsa_lagna_sign = "Unknown"
        swamsa_lagna_sign_num = 0

    evidence = [
        f"Atmakaraka (AK) identified as {ak_planet} (placed in D1 {ak_d1_sign} at {ak_d1_degree:.6f}°).",
        f"Navamsha (D9) position of Atmakaraka ({ak_planet}) retrieved from validated Varga facts: {karakamsha_sign} (Sign {karakamsha_sign_num}) at {karakamsha_d9_deg:.6f}°.",
        f"Therefore, Karakamsha sign = {karakamsha_sign}.",
        f"Navamsha Lagna (D9 Ascendant / Swamsa) retrieved from validated Varga facts: {swamsa_lagna_sign} (Sign {swamsa_lagna_sign_num}).",
        "Note: Karakamsha refers strictly to the D9 sign of Atmakaraka; Swamsa Lagna refers to the D9 Ascendant."
    ]
    
    return KarakamshaDetails(
        atmakaraka_planet=ak_planet,
        atmakaraka_d1_sign=ak_d1_sign,
        atmakaraka_d1_degree=ak_d1_degree,
        karakamsha_sign=karakamsha_sign,
        karakamsha_sign_num=karakamsha_sign_num,
        karakamsha_navamsha_degree=karakamsha_d9_deg,
        swamsa_navamsha_lagna_sign=swamsa_lagna_sign,
        swamsa_navamsha_lagna_sign_num=swamsa_lagna_sign_num,
        evidence=evidence
    )
