from typing import Dict, Tuple
from .models import SignPosition, HouseData
from .config import CalculationProfile, HouseSystem
import math

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_sign_from_longitude(longitude: float) -> Tuple[int, str, float]:
    """
    Returns (sign_id, sign_name, degree_within_sign)
    sign_id is 1-indexed (1=Aries, 12=Pisces).
    """
    lon = longitude % 360.0
    sign_idx = int(math.floor(lon / 30.0))
    degree_within = lon % 30.0
    return (sign_idx + 1, SIGNS[sign_idx], degree_within)

def calculate_houses(ascendant_sign_id: int, profile: CalculationProfile) -> Dict[int, HouseData]:
    """
    Returns mapping from house number (1-12) to HouseData based on the calculation profile.
    """
    houses = {}
    if profile.house_system == HouseSystem.WHOLE_SIGN:
        for i in range(12):
            house_num = i + 1
            # Calculate sign id offset correctly. 
            # If Ascendant is sign 2 (Taurus), house 1 is sign 2.
            # House 2 is sign 3, etc.
            # formula: ((ascendant_sign_id - 1 + i) % 12) + 1
            sign_id = ((ascendant_sign_id - 1 + i) % 12) + 1
            
            houses[house_num] = HouseData(
                id=house_num,
                sign=SignPosition(
                    id=sign_id,
                    name=SIGNS[sign_id - 1],
                    degree=0.0 # Whole sign houses don't have a specific cusp degree other than 0
                )
            )
    else:
        raise ValueError(f"Unsupported house system: {profile.house_system}")
        
    return houses

def get_house_for_sign(sign_id: int, houses: Dict[int, HouseData]) -> int:
    """
    Given a sign ID (1-12) and the generated houses, returns the house number (1-12).
    """
    for h_num, h_data in houses.items():
        if h_data.sign.id == sign_id:
            return h_num
    return 1 # Fallback, shouldn't happen
