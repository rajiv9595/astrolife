"""
Bhava Bala Calculation - Classical Parashari Implementation

Bhava Bala (House Strength) - Strength of each house/bhava.
Separate from planetary Shadbala.
"""
import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from typing import Dict
from core.strength.models import BhavaBalaResult, StrengthSystem, StrengthClassification
from core.strength.profile import StrengthCalculationProfile, DEFAULT_STRENGTH_PROFILE
from core.calculation.pipeline import ChartFacts
from tables import SIGN_LORDS


def calculate_bhava_bala(
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE
) -> Dict[int, BhavaBalaResult]:
    """
    Calculate Bhava Bala for all 12 houses.
    
    Classical components:
    1. Bhavadhipati Bala - Lord's strength (Shadbala of house lord)
    2. Dig Bala - Directional strength of house
    3. Drishti Bala - Aspects on the house
    4. Other factors per tradition
    """
    results = {}
    
    # Get planetary Shadbala for lords' strength
    from core.strength.shadbala import calculate_all_shadbala
    planet_shadbala = calculate_all_shadbala(chart_facts, profile)
    
    for house_num in range(1, 13):
        house_data = chart_facts.houses.get(house_num)
        if not house_data:
            continue
        
        sign_name = house_data.sign.name
        
        # Find lord of this house
        lord_planet = SIGN_LORDS.get(sign_name)
        
        # Bhavadhipati Bala: Lord's total Shadbala in Rupas * 10 (to get virupas equivalent)
        bhavadhipati_bala = 0.0
        if lord_planet and lord_planet in planet_shadbala:
            bhavadhipati_bala = planet_shadbala[lord_planet].total_rupas * 60  # Convert to virupas
        
        # Dig Bala for house (simplified)
        dig_bala = 30.0  # Base value
        
        # Drishti Bala: Aspects on this house
        drishti_bala = 0.0
        for planet_name, planet_data in chart_facts.planets.items():
            planet_house = planet_data.house
            # Check if planet aspects this house
            house_dist = (house_num - planet_house) % 12
            if house_dist == 0:
                house_dist = 12
            
            from core.strength.drig_bala import ASPECT_DEFINITIONS
            aspects = ASPECT_DEFINITIONS.get(planet_name, [])
            for offset, strength in aspects:
                if offset == house_dist:
                    drishti_bala += 60.0 * strength
        
        # Normalize drishti
        drishti_bala = min(60.0, drishti_bala * 60.0 / 480.0)
        
        total = bhavadhipati_bala + dig_bala + drishti_bala
        maximum = 60.0 + 60.0 + 60.0  # Approximate
        
        results[house_num] = BhavaBalaResult(
            house=house_num,
            sign=sign_name,
            system=StrengthSystem.BHava_BALA,
            method="PARASHARI_CLASSICAL",
            classification=StrengthClassification.CLASSICAL,
            bhavadhipati_bala=round(bhavadhipati_bala, 4),
            dig_bala=round(dig_bala, 4),
            drishti_bala=round(drishti_bala, 4),
            total=round(total, 4),
            maximum=round(maximum, 4),
            unit="virupas"
        )
    
    return results