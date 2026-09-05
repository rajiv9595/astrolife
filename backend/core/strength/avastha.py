"""
Avastha Calculation - Classical Parashari Implementation

Avastha (Planetary States) - Different states of planets based on position.
Main systems:
1. Bala Avastha (Infant, Youth, Adult, Old, Dead) - based on degrees in sign
2. Jagratadi Avastha (Waking, Dreaming, Deep Sleep) - based on sign type
3. Lajjitadi Avastha (Shame, etc.) - based on conjunctions
4. Deeptaadi Avastha (Bright, etc.) - based on dignity
"""
from typing import Dict
from .models import AvasthaResult, StrengthSystem, StrengthClassification
from .profile import StrengthCalculationProfile, DEFAULT_STRENGTH_PROFILE, SIGNS, get_sign_index
from ..calculation.pipeline import ChartFacts


# Bala Avastha: 5 states based on degree in sign (each 6°)
BALA_AVASTHA = [
    (0, 6, "BALA", "Infant", "Newborn, helpless, needs support"),
    (6, 12, "KUMARA", "Youth", "Growing, energetic, learning"),
    (12, 18, "YUVA", "Adult", "Prime, fully capable, authoritative"),
    (18, 24, "VRIDDHA", "Old", "Declining, experienced, wise but weak"),
    (24, 30, "MRITYA", "Dead", "End of cycle, transformation"),
]

# Jagratadi Avastha: 3 states based on sign type
JAGRATADI_AVASTHA = {
    "CHARA": "JAGRAT",      # Movable signs: Aries, Cancer, Libra, Capricorn -> Waking
    "STHIRA": "SVAPNA",     # Fixed signs: Taurus, Leo, Scorpio, Aquarius -> Dreaming
    "DWISVABHAVA": "SUSHUPTI"  # Dual signs: Gemini, Virgo, Sagittarius, Pisces -> Deep Sleep
}

SIGN_TYPES = {
    "Aries": "CHARA", "Cancer": "CHARA", "Libra": "CHARA", "Capricorn": "CHARA",
    "Taurus": "STHIRA", "Leo": "STHIRA", "Scorpio": "STHIRA", "Aquarius": "STHIRA",
    "Gemini": "DWISVABHAVA", "Virgo": "DWISVABHAVA", "Sagittarius": "DWISVABHAVA", "Pisces": "DWISVABHAVA",
}


def calculate_bala_avastha(
    planet: str,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile
) -> AvasthaResult:
    """Calculate Bala Avastha (Infant/Youth/Adult/Old/Dead)"""
    planet_data = chart_facts.planets.get(planet)
    if not planet_data:
        return AvasthaResult(
            planet=planet,
            system=StrengthSystem.AVASTHA,
            method="BALA_AVASTHA",
            classification=StrengthClassification.CLASSICAL,
            avastha_name="UNKNOWN",
            avastha_index=-1,
            degree_range="0-30",
            description="Planet not found"
        )
    
    deg_in_sign = planet_data.sign.degree
    
    for i, (start, end, name, label, desc) in enumerate(BALA_AVASTHA):
        if start <= deg_in_sign < end:
            return AvasthaResult(
                planet=planet,
                system=StrengthSystem.AVASTHA,
                method="BALA_AVASTHA",
                classification=StrengthClassification.CLASSICAL,
                avastha_name=name,
                avastha_index=i,
                degree_range=f"{start}-{end}°",
                description=f"{label}: {desc} (Planet at {deg_in_sign:.2f}° in sign)"
            )
    
    # Edge case: exactly 30° = 0° next sign (shouldn't happen with proper normalization)
    return AvasthaResult(
        planet=planet,
        system=StrengthSystem.AVASTHA,
        method="BALA_AVASTHA",
        classification=StrengthClassification.CLASSICAL,
        avastha_name="MRITYA",
        avastha_index=4,
        degree_range="24-30°",
        description=f"Dead state (Planet at {deg_in_sign:.2f}° in sign)"
    )


def calculate_jagratadi_avastha(
    planet: str,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile
) -> AvasthaResult:
    """Calculate Jagratadi Avastha (Waking/Dreaming/Deep Sleep)"""
    planet_data = chart_facts.planets.get(planet)
    if not planet_data:
        return AvasthaResult(
            planet=planet,
            system=StrengthSystem.AVASTHA,
            method="JAGRATADI_AVASTHA",
            classification=StrengthClassification.CLASSICAL,
            avastha_name="UNKNOWN",
            avastha_index=-1,
            degree_range="",
            description="Planet not found"
        )
    
    sign_name = planet_data.sign.name
    sign_type = SIGN_TYPES.get(sign_name, "CHARA")
    avastha = JAGRATADI_AVASTHA.get(sign_type, "JAGRAT")
    
    avastha_names = {"JAGRAT": 0, "SVAPNA": 1, "SUSHUPTI": 2}
    avastha_labels = {
        "JAGRAT": "Waking - Fully conscious and active",
        "SVAPNA": "Dreaming - Subconscious, imaginative",
        "SUSHUPTI": "Deep Sleep - Unconscious, dormant"
    }
    
    return AvasthaResult(
        planet=planet,
        system=StrengthSystem.AVASTHA,
        method="JAGRATADI_AVASTHA",
        classification=StrengthClassification.CLASSICAL,
        avastha_name=avastha,
        avastha_index=avastha_names.get(avastha, 0),
        degree_range=f"Sign: {sign_name} ({sign_type})",
        description=avastha_labels.get(avastha, "")
    )


def calculate_all_avastha(
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE
) -> Dict[str, Dict[str, AvasthaResult]]:
    """Calculate all Avastha systems for all planets"""
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    results = {}
    
    for planet in planets:
        if planet not in chart_facts.planets:
            continue
        
        planet_avasthas = {}
        
        if "BALA_AVASTHA" in profile.avastha_systems:
            planet_avasthas["BALA_AVASTHA"] = calculate_bala_avastha(planet, chart_facts, profile)
        
        if "JAGRATADI_AVASTHA" in profile.avastha_systems:
            planet_avasthas["JAGRATADI_AVASTHA"] = calculate_jagratadi_avastha(planet, chart_facts, profile)
        
        results[planet] = planet_avasthas
    
    return results