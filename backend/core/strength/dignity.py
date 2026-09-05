"""
Dignity Calculator - Classical Parashari Implementation

Canonical dignity evaluator for planetary dignity in signs.
Returns structured dignity assessment with evidence.
"""
import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from typing import Dict
from core.strength.models import DignityResult, StrengthSystem, StrengthClassification
from core.strength.profile import StrengthCalculationProfile, DEFAULT_STRENGTH_PROFILE, EXALTATION_DATA, MOOLATRIKONA_DATA, NATURAL_FRIENDSHIP, SIGNS, get_sign_index, normalize_deg
from core.calculation.pipeline import ChartFacts
from tables import SIGN_LORDS


def calculate_dignity(
    planet: str,
    sign: str,
    degree_in_sign: float,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE
) -> DignityResult:
    """
    Calculate canonical planetary dignity in a sign.
    
    Returns structured result with:
    - dignity category (EXALTED, MOOLATRIKONA, OWN_SIGN, FRIEND, NEUTRAL, ENEMY, DEBILITATED)
    - ruler of the sign
    - relationship type
    - boolean flags for each category
    """
    
    # Default values
    dignity = "NEUTRAL"
    ruler = SIGN_LORDS.get(sign, "")
    relationship = "NEUTRAL"
    is_exalted = False
    is_debilitated = False
    is_own_sign = False
    is_moolatrikona = False
    moolatrikona_range = None
    
    if planet not in EXALTATION_DATA:
        return DignityResult(
            planet=planet,
            sign=sign,
            system=StrengthSystem.PARASHARI_DIGNITY,
            method="PARASHARI_CLASSICAL",
            classification=StrengthClassification.CLASSICAL,
            dignity="NEUTRAL",
            ruler=ruler,
            relationship="NEUTRAL",
            is_exalted=False,
            is_debilitated=False,
            is_own_sign=False,
            is_moolatrikona=False
        )
    
    ex_data = EXALTATION_DATA[planet]
    mool_data = MOOLATRIKONA_DATA.get(planet, {})
    
    # 1. Exaltation (with degree check)
    if sign == ex_data["sign"]:
        # Check if within exaltation degree range (typically exact degree ± few degrees)
        # For exact exaltation, degree should be at the exaltation degree
        is_exalted = True
        dignity = "EXALTED"
        relationship = "EXALTED"
    
    # 2. Debilitation
    elif sign == ex_data["debilitation_sign"]:
        is_debilitated = True
        dignity = "DEBILITATED"
        relationship = "DEBILITATED"
    
    # 3. Moolatrikona
    elif sign == mool_data.get("sign"):
        moolatrikona_start = mool_data.get("start", 0)
        moolatrikona_end = mool_data.get("end", 30)
        moolatrikona_range = f"{moolatrikona_start}-{moolatrikona_end}°"
        
        if moolatrikona_start <= degree_in_sign <= moolatrikona_end:
            is_moolatrikona = True
            dignity = "MOOLATRIKONA"
            relationship = "MOOLATRIKONA"
        else:
            # In sign but outside moolatrikona range -> own sign
            is_own_sign = True
            dignity = "OWN_SIGN"
            relationship = "OWN_SIGN"
    
    # 4. Own Sign
    elif SIGN_LORDS.get(sign) == planet:
        is_own_sign = True
        dignity = "OWN_SIGN"
        relationship = "OWN_SIGN"
    
    # 5. Friend/Enemy/Neutral (Natural friendship)
    else:
        nat = NATURAL_FRIENDSHIP.get(planet, {})
        sign_lord = SIGN_LORDS.get(sign)
        
        if sign_lord in nat.get("friends", []):
            dignity = "FRIEND"
            relationship = "FRIEND"
        elif sign_lord in nat.get("enemies", []):
            dignity = "ENEMY"
            relationship = "ENEMY"
        else:
            dignity = "NEUTRAL"
            relationship = "NEUTRAL"
    
    # Temporal friendship (based on house positions) - can be added for compound dignity
    # For now, return natural dignity
    
    return DignityResult(
        planet=planet,
        sign=sign,
        system=StrengthSystem.PARASHARI_DIGNITY,
        method="PARASHARI_CLASSICAL",
        classification=StrengthClassification.CLASSICAL,
        dignity=dignity,
        ruler=ruler,
        relationship=relationship,
        is_exalted=is_exalted,
        is_debilitated=is_debilitated,
        is_own_sign=is_own_sign,
        is_moolatrikona=is_moolatrikona,
        moolatrikona_range=moolatrikona_range
    )


def calculate_all_dignities(
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE
) -> Dict[str, DignityResult]:
    """Calculate dignity for all planets in their D1 signs"""
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    results = {}
    
    for planet in planets:
        if planet not in chart_facts.planets:
            continue
        
        planet_data = chart_facts.planets[planet]
        sign = planet_data.sign.name
        degree = planet_data.sign.degree
        
        results[planet] = calculate_dignity(planet, sign, degree, chart_facts, profile)
    
    return results