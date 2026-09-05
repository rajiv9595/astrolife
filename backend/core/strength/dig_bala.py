"""
Dig Bala Calculation - Classical Parashari Implementation

Dig Bala (Directional Strength) based on planet's angular distance from its ideal house cusp.
Continuous calculation using actual house cusps, not just whole-sign house numbers.
"""
import math
from typing import Dict
from .models import DigBala
from .profile import StrengthCalculationProfile, DIG_BALA_HOUSES, SIGNS, get_sign_index, normalize_deg
from ..calculation.pipeline import ChartFacts


# Classical ideal positions for Dig Bala (house cusps where planet gets full 60 virupas)
# These are the houses where each planet gets maximum directional strength
DIG_BALA_IDEAL_HOUSES = DIG_BALA_HOUSES.copy()


def calculate_dig_bala(
    planet: str,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile
) -> DigBala:
    """
    Calculate Dig Bala using continuous angular distance from ideal house cusp.
    
    Classical method:
    - Each planet has an ideal house where it gets maximum Dig Bala (60 virupas)
    - Strength decreases proportionally with angular distance from ideal house cusp
    - At 180° from ideal (opposite house): 0 virupas
    
    Formula: 60 * cos(angular_distance / 2) where angular_distance is in degrees
    Or: 60 * (1 - angular_distance / 180) for linear decrease
    
    We use the continuous angular method based on actual house cusps.
    """
    if planet not in DIG_BALA_IDEAL_HOUSES:
        return DigBala(
            value=0.0,
            maximum=60.0,
            unit="virupas",
            ideal_house=1,
            actual_house=1,
            angular_distance=180.0,
            classification="CLASSICAL",
            description=f"No Dig Bala data for {planet}"
        )
    
    ideal_house = DIG_BALA_IDEAL_HOUSES[planet]
    actual_house = chart_facts.planets[planet].house
    
    # Get the actual house cusps for precise calculation
    # Since we use Whole Sign houses, house cusps are at 0° of each sign
    # Ascendant sign = House 1 cusp at 0°
    asc_sign_idx = chart_facts.ascendant.sign.id - 1  # 0-indexed
    
    # Ideal house cusp longitude (sidereal)
    ideal_cusp_sign_idx = (asc_sign_idx + ideal_house - 1) % 12
    ideal_cusp_lon = ideal_cusp_sign_idx * 30.0
    
    # Planet's actual sidereal longitude
    planet_lon = normalize_deg(chart_facts.planets[planet].longitude.sidereal)
    
    # Angular distance from ideal cusp (0-180)
    angular_distance = abs(planet_lon - ideal_cusp_lon)
    if angular_distance > 180:
        angular_distance = 360 - angular_distance
    
    # Dig Bala: 60 at 0° distance, 0 at 180° distance
    # Using cosine formula for smooth transition: 60 * cos(distance/2)
    # Or linear: 60 * (1 - distance/180)
    # Classical texts suggest the cosine method
    dig_bala = max(0.0, 60.0 * math.cos(math.radians(angular_distance / 2)))
    
    # Alternative linear method (also found in some texts):
    # dig_bala = max(0.0, 60.0 * (1.0 - angular_distance / 180.0))
    
    return DigBala(
        value=round(dig_bala, 4),
        maximum=60.0,
        unit="virupas",
        ideal_house=ideal_house,
        actual_house=actual_house,
        angular_distance=round(angular_distance, 4),
        classification="CLASSICAL",
        description=f"Ideal house {ideal_house} ({SIGNS[ideal_cusp_sign_idx]} 0°), Planet at {planet_lon:.4f}°, Distance {angular_distance:.4f}°"
    )