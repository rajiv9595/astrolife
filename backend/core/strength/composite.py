"""
Composite Strength Calculator - Astrolife Custom Implementation

This is the CUSTOM Astrolife composite strength score.
It is explicitly labeled as CUSTOM and NOT presented as classical Shadbala.
Preserves backward compatibility with existing frontend.
"""
import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from typing import Dict, List, Optional
from .models import CompositeStrengthResult, StrengthSystem, StrengthClassification
from .profile import StrengthCalculationProfile, DEFAULT_STRENGTH_PROFILE
from ..calculation.pipeline import ChartFacts
from .shadbala import calculate_all_shadbala
from .dignity import calculate_dignity
from tables import SIGN_LORDS, FRIENDLY_SIGNS


# Original custom scoring constants (preserved for backward compatibility)
SCORE_EXALTED = 100
SCORE_MOOLATRIKONA = 80
SCORE_OWN_SIGN = 75
SCORE_FRIEND_SIGN = 60
SCORE_NEUTRAL_SIGN = 50
SCORE_ENEMY_SIGN = 30
SCORE_DEBILITATED = 0

SCORE_KENDRA = 20
SCORE_TRIKONA = 15
SCORE_DUSTHANA = -15

TRINES = [1, 5, 9]
KENDRAS = [1, 4, 7, 10]
DUSTHANAS = [6, 8, 12]
UPACHAYAS = [3, 6, 10, 11]

DIGBALA_HOUSES = {
    "Sun": [10], "Mars": [10],
    "Moon": [4], "Venus": [4],
    "Jupiter": [1], "Mercury": [1],
    "Saturn": [7]
}


def calculate_composite_strength(
    planet: str,
    chart_facts: ChartFacts,
    d9_chart_facts: Optional[ChartFacts] = None,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE
) -> CompositeStrengthResult:
    """
    Calculate the Astrolife Custom Composite Strength Score.
    
    This is NOT classical Shadbala. It is a custom heuristic combining:
    - D1 sign dignity
    - House placement
    - Retrogradation
    - D9 (Navamsa) confirmation
    - Classical Shadbala ratio (as one factor)
    
    Output: 0-100 normalized score with label
    """
    planet_data = chart_facts.planets.get(planet)
    if not planet_data:
        return CompositeStrengthResult(
            planet=planet,
            system=StrengthSystem.ASTROLIFE_COMPOSITE,
            method="ASTROLIFE_CUSTOM",
            classification=StrengthClassification.CUSTOM,
            score=0.0,
            label="Unknown",
            nature="Unknown",
            reasons=["Planet not found"],
            disclaimer="This is a custom Astrolife composite score, not a classical Shadbala calculation."
        )
    
    score = 0.0
    reasons = []
    
    # 1. D1 Sign Dignity (using canonical dignity)
    dignity_result = calculate_dignity(
        planet, 
        planet_data.sign.name, 
        planet_data.sign.degree,
        chart_facts,
        profile
    )
    
    nature = dignity_result.dignity
    if nature == "EXALTED":
        score += SCORE_EXALTED
        reasons.append("Exalted in D1 (+Power)")
    elif nature == "MOOLATRIKONA":
        score += SCORE_MOOLATRIKONA
        reasons.append("Moolatrikona in D1 (+Power)")
    elif nature == "OWN_SIGN":
        score += SCORE_OWN_SIGN
        reasons.append("Own Sign (+Stability)")
    elif nature == "FRIEND":
        score += SCORE_FRIEND_SIGN
        reasons.append("Friend Sign (+Comfort)")
    elif nature == "NEUTRAL":
        score += SCORE_NEUTRAL_SIGN
    elif nature == "ENEMY":
        score += SCORE_ENEMY_SIGN
        reasons.append("Enemy Sign (-Comfort)")
    elif nature == "DEBILITATED":
        score += SCORE_DEBILITATED
        reasons.append("Debilitated in D1 (-Power)")
    
    # 2. House Placement
    house_num = planet_data.house
    if house_num:
        if house_num in KENDRAS:
            score += SCORE_KENDRA
            reasons.append("In Kendra (Action Power)")
        if house_num in TRINES:
            score += SCORE_TRIKONA
            if house_num != 1:
                reasons.append("In Trikona (Luck)")
        if house_num in DUSTHANAS:
            score += SCORE_DUSTHANA
            reasons.append("In Dusthana (Obstacles)")
        
        # Digbala (binary check preserved for compatibility)
        if house_num in DIGBALA_HOUSES.get(planet, []):
            score += 30
            reasons.append(f"Digbala in House {house_num} (Directional Strength)")
    
    # 3. Retrogradation
    if planet_data.retrograde:
        score += 20
        reasons.append("Retrograde (Chesta Bala - High Effort)")
    
    # 4. Classical Shadbala Ratio as a factor (NEW: integrate classical calculation)
    shadbala_results = calculate_all_shadbala(chart_facts, profile)
    if planet in shadbala_results:
        shadbala_ratio = shadbala_results[planet].ratio
        if shadbala_ratio >= 1.0:
            score += 25
            reasons.append("Classical Shadbala: Strong")
        elif shadbala_ratio >= 0.8:
            score += 15
            reasons.append("Classical Shadbala: Moderate")
        else:
            score += 5
            reasons.append("Classical Shadbala: Weak")
    
    # 5. D9 (Navamsa) Confirmation
    if d9_chart_facts and planet in d9_chart_facts.planets:
        d9_data = d9_chart_facts.planets[planet]
        d9_sign = d9_data.sign.name
        d9_dignity = calculate_dignity(planet, d9_sign, d9_data.sign.degree, d9_chart_facts, profile).dignity
        
        # Vargottama Check
        if d9_sign == planet_data.sign.name:
            score += 40
            reasons.append("Vargottama (Strong in D1 & D9)")
        
        # Improvement/Debilitation checks
        if nature == "DEBILITATED" and d9_dignity in ["EXALTED", "OWN_SIGN", "MOOLATRIKONA"]:
            score += 30  # Reduced from 50 - not automatic Neecha Bhanga
            reasons.append(f"Improved in D9 ({d9_dignity}) - Mitigating factor")
        elif nature == "EXALTED" and d9_dignity == "DEBILITATED":
            score -= 30
            reasons.append("Weak in Navamsa (Outcome impacted)")
        elif d9_dignity == "EXALTED":
            score += 15
            reasons.append("Exalted in Navamsa")
        elif d9_dignity == "DEBILITATED":
            score -= 15
            reasons.append("Debilitated in Navamsa")
    
    # Normalize score (roughly 0-100, can exceed slightly)
    normalized_score = max(0, min(100, score))
    
    # Label
    if normalized_score >= 80:
        label = "Very Strong"
    elif normalized_score >= 65:
        label = "Strong"
    elif normalized_score >= 50:
        label = "Moderate"
    elif normalized_score >= 35:
        label = "Weak"
    else:
        label = "Very Weak"
    
    return CompositeStrengthResult(
        planet=planet,
        system=StrengthSystem.ASTROLIFE_COMPOSITE,
        method="ASTROLIFE_CUSTOM",
        classification=StrengthClassification.CUSTOM,
        score=round(normalized_score, 1),
        label=label,
        nature=nature,
        reasons=reasons,
        components={
            "dignity": nature,
            "house": house_num,
            "retrograde": planet_data.retrograde,
            "shadbala_ratio": shadbala_results.get(planet).ratio if planet in shadbala_results else None,
        },
        disclaimer="This is a custom Astrolife composite score, not a classical Shadbala calculation."
    )


def calculate_all_composite_strength(
    chart_facts: ChartFacts,
    d9_chart_facts: Optional[ChartFacts] = None,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE
) -> Dict[str, CompositeStrengthResult]:
    """Calculate composite strength for all planets"""
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    results = {}
    
    for planet in planets:
        if planet in chart_facts.planets:
            results[planet] = calculate_composite_strength(
                planet, chart_facts, d9_chart_facts, profile
            )
    
    return results