from typing import List, Dict

# Ashtakavarga Bindu (point) Tables
# The lists represent the house numbers (1-indexed) from the reference planet/Lagna
# where the planet contributes 1 point.
# Reference: Standard Parasara Ashtakavarga tables.

AV_TABLES = {
    "Sun": {
        "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon": [3, 6, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus": [6, 7, 12],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Ascendant": [3, 4, 6, 10, 11, 12]
    },
    "Moon": {
        "Sun": [3, 6, 7, 8, 10, 11],
        "Moon": [1, 3, 6, 7, 10, 11],
        "Mars": [2, 3, 5, 6, 9, 10, 11],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12],
        "Venus": [3, 4, 5, 7, 9, 10, 11],
        "Saturn": [3, 5, 6, 11],
        "Ascendant": [3, 6, 10, 11]
    },
    "Mars": {
        "Sun": [3, 5, 6, 10, 11],
        "Moon": [3, 6, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venus": [6, 8, 11, 12],
        "Saturn": [1, 4, 7, 8, 9, 10, 11],
        "Ascendant": [1, 3, 6, 10, 11]
    },
    "Mercury": {
        "Sun": [5, 6, 9, 11, 12],
        "Moon": [2, 4, 6, 8, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Ascendant": [1, 2, 4, 6, 8, 10, 11]
    },
    "Jupiter": {
        "Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon": [2, 5, 7, 9, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus": [2, 5, 6, 9, 10, 11],
        "Saturn": [3, 5, 6, 12],
        "Ascendant": [1, 2, 4, 5, 6, 9, 10, 11]
    },
    "Venus": {
        "Sun": [8, 11, 12],
        "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars": [3, 4, 6, 9, 11, 12],
        "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn": [3, 4, 5, 8, 9, 10, 11],
        "Ascendant": [1, 2, 3, 4, 5, 8, 9, 11]
    },
    "Saturn": {
        "Sun": [1, 2, 4, 7, 8, 10, 11],
        "Moon": [3, 6, 11],
        "Mars": [3, 5, 6, 10, 11],
        "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venus": [6, 11, 12],
        "Saturn": [3, 5, 6, 11],
        "Ascendant": [1, 3, 4, 6, 10, 11]
    }
}

SIGNS_LIST = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_sign_index(sign: str) -> int:
    try:
        return SIGNS_LIST.index(sign)
    except ValueError:
        return 0

def compute_bav(planets: List[Dict], asc_sign: str) -> Dict[str, List[int]]:
    """
    Computes the Bhinnashtakavarga (BAV) for the 7 primary planets.
    Returns a dictionary mapping each planet to a list of 12 integers representing the points in each sign (Aries to Pisces).
    """
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    
    # Get indices of planets and Ascendant
    positions = {}
    if isinstance(planets, dict):
        planet_items = planets.items()
    else:
        planet_items = [(p.get("name", ""), p) for p in planets]

    for name, p_data in planet_items:
        if name in valid_planets:
            positions[name] = get_sign_index(p_data.get("sign_manual"))
            
    positions["Ascendant"] = get_sign_index(asc_sign)
    
    bav = {}
    
    # For each planet we want to calculate BAV for
    for planet in valid_planets:
        bav[planet] = [0] * 12
        rules = AV_TABLES.get(planet, {})
        
        # From each reference point (the 7 planets + Ascendant)
        for ref_name, active_houses in rules.items():
            if ref_name not in positions:
                continue
            
            ref_idx = positions[ref_name]
            
            # Add a point to the corresponding sign
            for house_num in active_houses:
                # house_num is 1-indexed. Ex: If ref is Aries (0) and house is 1, target is Aries (0)
                target_sign_idx = (ref_idx + house_num - 1) % 12
                bav[planet][target_sign_idx] += 1
                
    return bav

def compute_sav(bav: Dict[str, List[int]]) -> List[int]:
    """
    Computes the Samudaya Ashtakavarga (SAV) by summing the 7 BAV arrays.
    Returns a list of 12 integers representing the total points in each sign (Aries to Pisces).
    """
    sav = [0] * 12
    for planet, points in bav.items():
        for i in range(12):
            sav[i] += points[i]
    return sav

def compute_ashtakavarga(planets: List[Dict], asc_sign: str) -> Dict:
    """
    Wrapper to compute all Ashtakavarga tables.
    """
    bav = compute_bav(planets, asc_sign)
    sav = compute_sav(bav)
    
    return {
        "bav": bav,
        "sav": sav
    }
