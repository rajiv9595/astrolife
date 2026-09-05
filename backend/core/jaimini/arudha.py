"""
Arudha Engine — Astrolife V2 Phase 5D

Calculates deterministic Arudha Padas for any given house using classical Jaimini / Parashari projection
and standard 10th-house exception rules.

Classical Algorithm:
1. Identify source sign of the house (S_house) and its lord (L).
2. Determine lord's occupied sign (S_lord).
3. Measure distance D = (S_lord - S_house) mod 12.
4. Raw projection: S_raw = (S_lord + D) mod 12 = (S_house + 2*D) mod 12.
5. Apply Classical Exceptions:
   - If S_raw == S_house (1st house from source): Final pada is 10th from source house ((S_house + 9) mod 12).
   - If S_raw == (S_house + 6) mod 12 (7th house from source): Final pada is 10th from 7th house, i.e., 4th from source house ((S_house + 3) mod 12).
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any

from ..calculation.models import ChartFacts
from .profile import JaiminiCalculationProfile, ArudhaMethod, CoLordMethod
from .models import ArudhaPadaItem


SIGNS: List[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

CLASSICAL_SIGN_LORDS: Dict[str, str] = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter"
}

PADA_NAMES: Dict[int, Tuple[str, str]] = {
    1: ("A1", "Arudha Lagna (AL)"),
    2: ("A2", "Dhana Pada (Kosa Pada)"),
    3: ("A3", "Bhratru Pada (Vikrama Pada)"),
    4: ("A4", "Matru Pada (Sukh Pada)"),
    5: ("A5", "Putra Pada (Mantra Pada)"),
    6: ("A6", "Satru Pada (Roga Pada)"),
    7: ("A7", "Dara Pada (Kalatra Pada)"),
    8: ("A8", "Mrityu Pada (Randhra Pada)"),
    9: ("A9", "Dharma Pada (Bhagya Pada)"),
    10: ("A10", "Karma Pada (Rajya Pada)"),
    11: ("A11", "Labha Pada"),
    12: ("A12", "Upapada Lagna (UL / Gauna Pada)")
}


def calculate_single_arudha(
    house_num: int,
    ascendant_sign_idx: int,
    planet_sign_map: Dict[str, int],
    profile: Optional[JaiminiCalculationProfile] = None
) -> ArudhaPadaItem:
    """
    Core pure mathematical function to calculate the Arudha Pada for a single house (1-12).
    
    ascendant_sign_idx: 0-indexed (0=Aries ... 11=Pisces)
    planet_sign_map: Dict[planet_name, sign_idx (0..11)]
    """
    if profile is None:
        profile = JaiminiCalculationProfile()
        
    arudha_method = profile.arudha_method
    
    # 1. Source House Sign
    house_sign_idx = (ascendant_sign_idx + (house_num - 1)) % 12
    source_sign = SIGNS[house_sign_idx]
    source_sign_num = house_sign_idx + 1
    
    # 2. House Lord
    lord = CLASSICAL_SIGN_LORDS.get(source_sign)
    if not lord or lord not in planet_sign_map:
        raise ValueError(f"Cannot resolve lord {lord} for sign {source_sign}")
        
    lord_sign_idx = planet_sign_map[lord]
    lord_sign = SIGNS[lord_sign_idx]
    lord_sign_num = lord_sign_idx + 1
    
    # 3. Distance from House to Lord (0-indexed count: 0 means same sign, 1 means 2nd house...)
    # In classical counting: count_houses = distance_signs + 1
    distance_signs = (lord_sign_idx - house_sign_idx) % 12
    count_houses = distance_signs + 1
    
    # 4. Raw Projection: project same distance from lord
    raw_proj_idx = (lord_sign_idx + distance_signs) % 12
    raw_projected_sign = SIGNS[raw_proj_idx]
    raw_projected_sign_num = raw_proj_idx + 1
    
    # 5. Exception handling
    exception_applied: Optional[str] = None
    final_sign_idx = raw_proj_idx
    
    if arudha_method == ArudhaMethod.PARASHARI_JAIMINI_STANDARD:
        # Check if raw projection falls in 1st house from source (same sign)
        if raw_proj_idx == house_sign_idx:
            # Shift to 10th house from source: +9 signs
            final_sign_idx = (house_sign_idx + 9) % 12
            exception_applied = (
                f"1st House Exception: Raw projection fell in source house ({source_sign}). "
                f"Shifted 10 houses forward to {SIGNS[final_sign_idx]}."
            )
        # Check if raw projection falls in 7th house from source (+6 signs)
        elif raw_proj_idx == (house_sign_idx + 6) % 12:
            # Shift to 10th house from 7th house = 4th house from source (+3 signs)
            final_sign_idx = (house_sign_idx + 3) % 12
            exception_applied = (
                f"7th House Exception: Raw projection fell in 7th from source house ({SIGNS[(house_sign_idx + 6) % 12]}). "
                f"Shifted 10 houses forward from 7th (4th from house) to {SIGNS[final_sign_idx]}."
            )
            
    final_sign = SIGNS[final_sign_idx]
    final_sign_num = final_sign_idx + 1
    
    code, trad_name = PADA_NAMES.get(house_num, (f"A{house_num}", f"Pada {house_num}"))
    
    evidence = [
        f"House {house_num} ({source_sign}, Sign {source_sign_num}) ruled by {lord}.",
        f"Lord {lord} is placed in {lord_sign} (Sign {lord_sign_num}).",
        f"Distance from House {house_num} to lord is {count_houses} houses ({distance_signs} signs).",
        f"Raw projected Pada is {count_houses} houses from lord ({lord_sign}) -> {raw_projected_sign} (Sign {raw_projected_sign_num})."
    ]
    
    if exception_applied:
        evidence.append(f"EXCEPTION APPLIED: {exception_applied}")
    else:
        evidence.append("No exception required. Raw projection is final.")
        
    evidence.append(f"Final {code} ({trad_name}) = {final_sign} (Sign {final_sign_num}).")
    
    return ArudhaPadaItem(
        house_number=house_num,
        pada_code=code,
        traditional_name=trad_name,
        source_sign=source_sign,
        source_sign_num=source_sign_num,
        house_lord=lord,
        lord_sign=lord_sign,
        lord_sign_num=lord_sign_num,
        distance_signs=distance_signs,
        raw_projected_sign=raw_projected_sign,
        raw_projected_sign_num=raw_projected_sign_num,
        exception_applied=exception_applied,
        final_sign=final_sign,
        final_sign_num=final_sign_num,
        evidence=evidence
    )
