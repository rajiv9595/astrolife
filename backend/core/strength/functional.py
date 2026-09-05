"""
Functional Strength Calculator - Classical Parashari Implementation

Functional Strength based on:
- Ascendant lordship
- House lordship (Kendra, Trikona, Dusthana, Maraka)
- Yogakaraka rules
- Functional benefic/malefic nature
"""
import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from typing import Dict, List
from core.strength.models import FunctionalStrengthResult, StrengthSystem, StrengthClassification
from core.strength.profile import StrengthCalculationProfile, DEFAULT_STRENGTH_PROFILE, SIGNS
from core.calculation.pipeline import ChartFacts
from tables import SIGN_LORDS


# Functional classifications per Ascendant
# This is a simplified mapping - full implementation would compute dynamically
FUNCTIONAL_NATURE = {
    # Key: (ascendant_sign, planet) -> nature
    # Will compute dynamically based on lordships
}


KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
UPACHAYA_HOUSES = {3, 6, 10, 11}
MARAKA_HOUSES = {2, 7}  # 2nd and 7th are maraka houses


def get_house_lordships(asc_sign: str) -> Dict[str, List[int]]:
    """
    Determine which houses each planet rules for a given Ascendant.
    Returns dict: planet -> list of house numbers ruled
    """
    # Get sign order starting from Ascendant
    asc_idx = SIGNS.index(asc_sign)
    house_signs = {}
    for i in range(12):
        house_num = i + 1
        sign_idx = (asc_idx + i) % 12
        house_signs[house_num] = SIGNS[sign_idx]
    
    # Map planets to houses they rule
    planet_houses = {}
    for house_num, sign in house_signs.items():
        lord = SIGN_LORDS.get(sign)
        if lord:
            if lord not in planet_houses:
                planet_houses[lord] = []
            planet_houses[lord].append(house_num)
    
    return planet_houses


def is_yogakaraka(planet: str, houses_ruled: List[int]) -> bool:
    """
    Check if planet is Yogakaraka (rules both a Kendra and a Trikona).
    Only one planet per Ascendant can be Yogakaraka.
    """
    rules_kendra = any(h in KENDRA_HOUSES for h in houses_ruled)
    rules_trikona = any(h in TRIKONA_HOUSES for h in houses_ruled)
    return rules_kendra and rules_trikona


def get_functional_nature(planet: str, houses_ruled: List[int], asc_sign: str) -> str:
    """
    Determine functional nature:
    - YOGAKARAKA: Rules Kendra + Trikona
    - BENEFIC: Rules Trikona (5,9) only
    - MALEFIC: Rules Dusthana (6,8,12) only
    - NEUTRAL: Rules Kendra only, or mixed
    """
    if is_yogakaraka(planet, houses_ruled):
        return "YOGAKARAKA"
    
    rules_trikona = any(h in TRIKONA_HOUSES for h in houses_ruled)
    rules_dusthana = any(h in DUSTHANA_HOUSES for h in houses_ruled)
    rules_kendra = any(h in KENDRA_HOUSES for h in houses_ruled)
    rules_maraka = any(h in MARAKA_HOUSES for h in houses_ruled)
    
    if rules_trikona and not rules_dusthana and not rules_maraka:
        return "FUNCTIONAL_BENEFIC"
    if rules_dusthana and not rules_trikona:
        return "FUNCTIONAL_MALEFIC"
    if rules_maraka and not rules_trikona:
        return "MARAKA"
    if rules_kendra and not rules_trikona and not rules_dusthana:
        return "NEUTRAL_KENDRA"
    
    return "NEUTRAL"


def calculate_functional_strength(
    planet: str,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE
) -> FunctionalStrengthResult:
    """Calculate functional strength for a planet based on Ascendant"""
    
    asc_sign = chart_facts.ascendant.sign.name
    planet_houses = get_house_lordships(asc_sign)
    houses_ruled = planet_houses.get(planet, [])
    
    yogakaraka = is_yogakaraka(planet, houses_ruled)
    functional_nature = get_functional_nature(planet, houses_ruled, asc_sign)
    
    # Determine specific flags
    kendra_trikona = any(h in KENDRA_HOUSES for h in houses_ruled) and any(h in TRIKONA_HOUSES for h in houses_ruled)
    dusthana_lord = any(h in DUSTHANA_HOUSES for h in houses_ruled)
    maraka = any(h in MARAKA_HOUSES for h in houses_ruled)
    
    # Score based on functional nature
    nature_scores = {
        "YOGAKARAKA": 100,
        "FUNCTIONAL_BENEFIC": 75,
        "NEUTRAL_KENDRA": 50,
        "NEUTRAL": 40,
        "MARAKA": 20,
        "FUNCTIONAL_MALEFIC": 10,
    }
    
    score = nature_scores.get(functional_nature, 40)
    
    # Details
    details = []
    details.append(f"Rules houses: {houses_ruled}")
    details.append(f"Functional nature: {functional_nature}")
    if yogakaraka:
        details.append("YOGAKARAKA - Rules both Kendra and Trikona")
    if dusthana_lord:
        details.append("Rules Dusthana (6,8,12)")
    if maraka:
        details.append("Rules Maraka (2,7)")
    
    return FunctionalStrengthResult(
        planet=planet,
        system=StrengthSystem.PARASHARI_FUNCTIONAL,
        method="PARASHARI_CLASSICAL",
        classification=StrengthClassification.TRADITION_DEPENDENT,
        lordship={"houses_ruled": houses_ruled, "ascendant": asc_sign},
        yogakaraka=yogakaraka,
        functional_nature=functional_nature,
        kendra_trikona=kendra_trikona,
        dusthana_lord=dusthana_lord,
        maraka=maraka,
        score=round(score, 2),
        details=details
    )


def calculate_all_functional_strength(
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE
) -> Dict[str, FunctionalStrengthResult]:
    """Calculate functional strength for all planets"""
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    results = {}
    
    for planet in planets:
        if planet in chart_facts.planets:
            results[planet] = calculate_functional_strength(planet, chart_facts, profile)
    
    return results