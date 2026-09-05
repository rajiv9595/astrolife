from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, List, Optional
from ..calculation.config import CalculationProfile as BaseCalculationProfile


class ShadbalaMethod(str, Enum):
    PARASHARI_CLASSICAL = "PARASHARI_CLASSICAL"
    # Other methods can be added: BPHS, SARAVALI, etc.


class KalaBalaMethod(str, Enum):
    PARASHARI_COMPLETE = "PARASHARI_COMPLETE"
    PARASHARI_SIMPLIFIED = "PARASHARI_SIMPLIFIED"  # Day/night only


class ChestaBalaMethod(str, Enum):
    PARASHARI_SPEED_BASED = "PARASHARI_SPEED_BASED"
    PARASHARI_RETROGRADE_ONLY = "PARASHARI_RETROGRADE_ONLY"


class DrigBalaMethod(str, Enum):
    PARASHARI_ASPECT_BASED = "PARASHARI_ASPECT_BASED"
    PLACEHOLDER = "PLACEHOLDER"


class SaptavargajaMethod(str, Enum):
    PARASHARI_7_VARGAS = "PARASHARI_7_VARGAS"  # D1, D2, D3, D7, D9, D12, D30
    BPHS_7_VARGAS = "BPHS_7_VARGAS"  # May differ


class StrengthCalculationProfile(BaseModel):
    """Extended profile for strength calculations"""
    
    # Base astronomical profile (from Phase 1)
    base_profile: BaseCalculationProfile = Field(default_factory=BaseCalculationProfile)
    
    # Shadbala method selection
    shadbala_method: ShadbalaMethod = ShadbalaMethod.PARASHARI_CLASSICAL
    
    # Sthana Bala sub-methods
    saptavargaja_method: SaptavargajaMethod = SaptavargajaMethod.PARASHARI_7_VARGAS
    
    # Kala Bala method
    kala_bala_method: KalaBalaMethod = KalaBalaMethod.PARASHARI_COMPLETE
    
    # Chesta Bala method
    chesta_bala_method: ChestaBalaMethod = ChestaBalaMethod.PARASHARI_SPEED_BASED
    
    # Drig Bala method
    drig_bala_method: DrigBalaMethod = DrigBalaMethod.PARASHARI_ASPECT_BASED
    
    # Minimum Shadbala requirements (in Rupas)
    minimum_shadbala_rupas: Dict[str, float] = Field(default_factory=lambda: {
        "Sun": 6.5,
        "Moon": 6.0,
        "Mars": 5.0,
        "Mercury": 7.0,
        "Jupiter": 6.5,
        "Venus": 5.5,
        "Saturn": 5.0,
    })
    
    # Vimsopaka configuration
    vimsopaka_vargas: List[int] = Field(default_factory=lambda: [1, 2, 3, 7, 9, 12, 30])
    vimsopaka_weights: Dict[int, float] = Field(default_factory=lambda: {
        1: 6, 2: 2, 3: 2, 7: 4, 9: 5, 12: 2, 30: 4
    })
    
    # Avastha configuration
    avastha_systems: List[str] = Field(default_factory=lambda: ["BALA_AVASTHA"])
    
    # Functional strength rules
    functional_rules: Dict = Field(default_factory=dict)
    
    # Enable/disable components
    calculate_bhava_bala: bool = True
    calculate_vimsopaka: bool = True
    calculate_avastha: bool = True
    calculate_dignity: bool = True
    calculate_functional: bool = True
    calculate_composite: bool = True


# Default profile for Astrolife V2
DEFAULT_STRENGTH_PROFILE = StrengthCalculationProfile()


# Traditional reference data
EXALTATION_DATA = {
    "Sun": {"sign": "Aries", "degree": 10, "debilitation_sign": "Libra", "debilitation_degree": 10},
    "Moon": {"sign": "Taurus", "degree": 3, "debilitation_sign": "Scorpio", "debilitation_degree": 3},
    "Mars": {"sign": "Capricorn", "degree": 28, "debilitation_sign": "Cancer", "debilitation_degree": 28},
    "Mercury": {"sign": "Virgo", "degree": 15, "debilitation_sign": "Pisces", "debilitation_degree": 15},
    "Jupiter": {"sign": "Cancer", "degree": 5, "debilitation_sign": "Capricorn", "debilitation_degree": 5},
    "Venus": {"sign": "Pisces", "degree": 27, "debilitation_sign": "Virgo", "debilitation_degree": 27},
    "Saturn": {"sign": "Libra", "degree": 20, "debilitation_sign": "Aries", "debilitation_degree": 20},
}

MOOLATRIKONA_DATA = {
    "Sun": {"sign": "Leo", "start": 0, "end": 20},
    "Moon": {"sign": "Taurus", "start": 3, "end": 30},
    "Mars": {"sign": "Aries", "start": 0, "end": 12},
    "Mercury": {"sign": "Virgo", "start": 15, "end": 20},
    "Jupiter": {"sign": "Sagittarius", "start": 0, "end": 10},
    "Venus": {"sign": "Libra", "start": 0, "end": 15},
    "Saturn": {"sign": "Aquarius", "start": 0, "end": 20},
}

# Natural friendship (Naisargika Maitri) - standard Parashari
NATURAL_FRIENDSHIP = {
    "Sun": {"friends": ["Moon", "Mars", "Jupiter"], "neutrals": ["Mercury"], "enemies": ["Venus", "Saturn"]},
    "Moon": {"friends": ["Sun", "Mercury"], "neutrals": ["Mars", "Jupiter", "Venus", "Saturn"], "enemies": []},
    "Mars": {"friends": ["Sun", "Moon", "Jupiter"], "neutrals": ["Venus", "Saturn"], "enemies": ["Mercury"]},
    "Mercury": {"friends": ["Sun", "Venus"], "neutrals": ["Mars", "Jupiter", "Saturn"], "enemies": ["Moon"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "neutrals": ["Saturn"], "enemies": ["Mercury", "Venus"]},
    "Venus": {"friends": ["Mercury", "Saturn"], "neutrals": ["Mars", "Jupiter"], "enemies": ["Sun", "Moon"]},
    "Saturn": {"friends": ["Mercury", "Venus"], "neutrals": ["Jupiter"], "enemies": ["Sun", "Moon", "Mars"]},
}

# Temporary friendship (Tatkalika Maitri) - based on house positions
def get_temporal_friends(planet_houses: Dict[str, int]) -> Dict[str, Dict[str, List[str]]]:
    """
    Calculate temporal friends/enemies based on house positions from each planet.
    Friend: 2, 12, 5, 9, 8, 4 from the planet
    Enemy: 1, 3, 6, 7, 10, 11 from the planet
    """
    friends = {2, 12, 5, 9, 8, 4}
    enemies = {1, 3, 6, 7, 10, 11}
    
    result = {}
    for p1, h1 in planet_houses.items():
        result[p1] = {"friends": [], "enemies": [], "neutrals": []}
        for p2, h2 in planet_houses.items():
            if p1 == p2:
                continue
            dist = (h2 - h1) % 12
            if dist == 0:
                dist = 12
            if dist in friends:
                result[p1]["friends"].append(p2)
            elif dist in enemies:
                result[p1]["enemies"].append(p2)
            else:
                result[p1]["neutrals"].append(p2)
    return result


# Compound friendship (Panchadha Maitri)
def get_compound_relationship(natural: Dict, temporal: Dict, planet: str) -> str:
    """Combine natural and temporal friendship"""
    nat_friends = set(natural.get(planet, {}).get("friends", []))
    nat_enemies = set(natural.get(planet, {}).get("enemies", []))
    temp_friends = set(temporal.get(planet, {}).get("friends", []))
    temp_enemies = set(temporal.get(planet, {}).get("enemies", []))
    
    # Great Friend: Natural friend + Temporal friend
    if planet in nat_friends and planet in temp_friends:
        return "GREAT_FRIEND"
    # Friend: Natural friend + Temporal neutral, or Natural neutral + Temporal friend
    if (planet in nat_friends and planet not in temp_enemies) or (planet not in nat_enemies and planet in temp_friends):
        return "FRIEND"
    # Neutral: Both neutral
    if planet not in nat_friends and planet not in nat_enemies and planet not in temp_friends and planet not in temp_enemies:
        return "NEUTRAL"
    # Enemy: Natural enemy + Temporal neutral, or Natural neutral + Temporal enemy
    if (planet in nat_enemies and planet not in temp_friends) or (planet not in nat_friends and planet in temp_enemies):
        return "ENEMY"
    # Great Enemy: Natural enemy + Temporal enemy
    if planet in nat_enemies and planet in temp_enemies:
        return "GREAT_ENEMY"
    return "NEUTRAL"


# Dig Bala ideal houses
DIG_BALA_HOUSES = {
    "Sun": 10,
    "Mars": 10,
    "Saturn": 7,
    "Moon": 4,
    "Venus": 4,
    "Jupiter": 1,
    "Mercury": 1,
}

# Naisargika Bala traditional values (in Virupas)
NAISARGIKA_BALA = {
    "Sun": 60.0,
    "Moon": 51.428571,
    "Venus": 42.857143,
    "Jupiter": 34.285714,
    "Mercury": 25.714286,
    "Mars": 17.142857,
    "Saturn": 8.571429,
}

# Sign order for calculations
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_sign_index(sign: str) -> int:
    """0-indexed sign index"""
    try:
        return SIGNS.index(sign)
    except ValueError:
        return 0


def normalize_deg(deg: float) -> float:
    """Normalize to 0-360"""
    return deg % 360.0