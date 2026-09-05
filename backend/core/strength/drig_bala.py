"""
Drig Bala Calculation - Classical Parashari Implementation

Drig Bala (Aspectual Strength) - Strength from planetary aspects.
Based on benefic and malefic aspects received by each planet.
Uses Parashari aspect framework (not Western degree aspects).
"""
import math
from typing import Dict, List
from .models import DrigBala
from .profile import StrengthCalculationProfile, SIGNS, get_sign_index, normalize_deg
from ..calculation.pipeline import ChartFacts


# Parashari aspect strengths (full aspects = 60 virupas, partial = proportion)
# Full aspects (100%):
# - All planets: 7th house (180°) = 60 virupas
# Special aspects:
# - Mars: 4th (90°) and 8th (210°) = 45 virupas each
# - Jupiter: 5th (150°) and 9th (270°) = 45 virupas each
# - Saturn: 3rd (60°) and 10th (300°) = 45 virupas each
# - Rahu/Ketu: 5th and 9th (like Jupiter) = 45 virupas each

# Benefic planets: Jupiter, Venus, Mercury (well-associated), waxing Moon
# Malefic planets: Sun, Mars, Saturn, Rahu, Ketu, waning Moon

PLANET_NATURE = {
    "Sun": "MALEFIC",
    "Moon": "VARIABLE",  # Depends on paksha
    "Mars": "MALEFIC",
    "Mercury": "BENEFIC",
    "Jupiter": "BENEFIC",
    "Venus": "BENEFIC",
    "Saturn": "MALEFIC",
    "Rahu": "MALEFIC",
    "Ketu": "MALEFIC",
}

# Aspect definitions: (target_house_offset, strength_factor)
# Offset from planet's house (1=same house, 7=7th house, etc.)
ASPECT_DEFINITIONS = {
    "Sun": [(7, 1.0)],
    "Moon": [(7, 1.0)],
    "Mars": [(7, 1.0), (4, 0.75), (8, 0.75)],  # 4th and 8th = 3/4 strength
    "Mercury": [(7, 1.0)],
    "Jupiter": [(7, 1.0), (5, 0.75), (9, 0.75)],  # 5th and 9th = 3/4 strength
    "Venus": [(7, 1.0)],
    "Saturn": [(7, 1.0), (3, 0.75), (10, 0.75)],  # 3rd and 10th = 3/4 strength
    "Rahu": [(7, 1.0), (5, 0.75), (9, 0.75)],
    "Ketu": [(7, 1.0), (5, 0.75), (9, 0.75)],
}


def get_planet_nature(planet: str, moon_data, sun_data=None) -> str:
    """Determine if planet is benefic or malefic for aspect calculation"""
    nature = PLANET_NATURE.get(planet, "NEUTRAL")
    if planet == "Moon" and moon_data and sun_data:
        # Waxing Moon (Shukla Paksha) = benefic, Waning Moon (Krishna Paksha) = malefic
        # Paksha determined by Moon-Sun angle
        moon_lon = moon_data.longitude.sidereal
        sun_lon = sun_data.longitude.sidereal
        angle = normalize_deg(moon_lon - sun_lon)
        # 0-180 = waxing (Shukla), 180-360 = waning (Krishna)
        is_waxing = angle < 180
        nature = "BENEFIC" if is_waxing else "MALEFIC"
    return nature


def calculate_drig_bala(
    planet: str,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile
) -> DrigBala:
    """
    Calculate Drig Bala from Parashari aspects received.
    
    Each planet receives aspect strength from other planets.
    Benefic aspects add positive strength, malefic aspects subtract.
    Total scaled to 60 virupas maximum.
    """
    planet_data = chart_facts.planets.get(planet)
    if not planet_data:
        return DrigBala(
            value=0.0,
            maximum=60.0,
            unit="virupas",
            classification="CLASSICAL",
            description=f"Planet {planet} not found"
        )
    
    target_house = planet_data.house
    target_sign = planet_data.sign.id
    
    benefic_total = 0.0
    malefic_total = 0.0
    aspect_details = []
    
    # Get Sun and Moon data for nature determination
    sun_data = chart_facts.planets.get("Sun")
    moon_data = chart_facts.planets.get("Moon")
    
    # Check aspects from each other planet
    for aspecting_name, aspecting_data in chart_facts.planets.items():
        if aspecting_name == planet:
            continue
        
        aspecting_house = aspecting_data.house
        aspecting_sign = aspecting_data.sign.id
        
        # Determine house distance (1-12)
        house_dist = (target_house - aspecting_house) % 12
        if house_dist == 0:
            house_dist = 12
        
        # Check if this planet aspects the target house
        aspects = ASPECT_DEFINITIONS.get(aspecting_name, [])
        for offset, strength_factor in aspects:
            if offset == house_dist:
                # This planet aspects the target
                aspect_nature = get_planet_nature(aspecting_name, moon_data, sun_data)
                
                # Base aspect strength = 60 * strength_factor
                aspect_strength = 60.0 * strength_factor
                
                detail = {
                    "from_planet": aspecting_name,
                    "from_house": aspecting_house,
                    "aspect_house": offset,
                    "strength_factor": strength_factor,
                    "nature": aspect_nature,
                    "virupas": aspect_strength
                }
                aspect_details.append(detail)
                
                if aspect_nature == "BENEFIC":
                    benefic_total += aspect_strength
                elif aspect_nature == "MALEFIC":
                    malefic_total += aspect_strength
    
    # Net Drig Bala: Benefic - Malefic, normalized to 0-60
    # Classical: Drig Bala = benefic_aspects - malefic_aspects, scaled
    # If net positive, scale to 0-60. If negative, 0.
    net = benefic_total - malefic_total
    
    # Maximum possible benefic aspects: all 8 planets with full 7th aspect = 8*60 = 480
    # Maximum possible malefic: same
    # Normalize: net ranges from -480 to +480, map to 0-60
    if net > 0:
        value = min(60.0, net * 60.0 / 480.0)
    else:
        value = 0.0
    
    return DrigBala(
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        benefic_aspect_strength=round(benefic_total, 4),
        malefic_aspect_strength=round(malefic_total, 4),
        aspect_details=aspect_details,
        classification="CLASSICAL",
        description=f"Benefic aspects: {benefic_total:.1f}, Malefic aspects: {malefic_total:.1f}, Net: {net:.1f} -> {value:.4f} virupas"
    )