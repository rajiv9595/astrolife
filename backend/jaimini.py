from typing import List, Dict

# Standard 7-karaka scheme
CHARA_KARAKA_NAMES = [
    "Atmakaraka (AK)",
    "Amatyakaraka (AmK)",
    "Bhratrukaraka (BK)",
    "Matrukaraka (MK)",
    "Putrakaraka (PK)",
    "Gnatikaraka (GK)",
    "Darakaraka (DK)"
]

def calculate_chara_karakas(planets: List[Dict]) -> Dict[str, str]:
    """
    Calculates the 7 Chara Karakas based on planetary degrees within a sign.
    Excludes Rahu, Ketu, and outer planets.
    """
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    
    # Extract valid planets and their degrees within a sign
    candidates = []
    # If planets is a dict:
    if isinstance(planets, dict):
        planet_items = planets.items()
    else:
        planet_items = [(p.get("name", ""), p) for p in planets]

    for name, p_data in planet_items:
        if name in valid_planets:
            # Degree within the sign is longitude % 30
            deg_in_sign = p_data.get("degree_in_sign_manual", 0.0)
            candidates.append({
                "name": name,
                "degree_in_sign": deg_in_sign
            })
            
    # Sort descending by degree in sign
    candidates.sort(key=lambda x: x["degree_in_sign"], reverse=True)
    
    karakas = {}
    for i, candidate in enumerate(candidates):
        if i < len(CHARA_KARAKA_NAMES):
            karakas[CHARA_KARAKA_NAMES[i]] = candidate["name"]
            
    return karakas

# Lords of the signs
SIGN_LORDS_MAP = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",      # Co-lord Ketu ignored for simple Arudha
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",   # Co-lord Rahu ignored for simple Arudha
    "Pisces": "Jupiter"
}

SIGNS_LIST = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def calculate_arudha_padas(planets: List[Dict], asc_sign: str) -> Dict[int, str]:
    """
    Calculates the Arudha Padas for all 12 houses.
    Returns a dictionary mapping house number (1-12) to the Sign name of its Arudha.
    """
    # Create a quick lookup for planet signs
    if isinstance(planets, dict):
        planet_signs = {name: p_data.get("sign_manual") for name, p_data in planets.items()}
    else:
        planet_signs = {p.get("name"): p.get("sign_manual") for p in planets}
    
    arudhas = {}
    
    try:
        asc_idx = SIGNS_LIST.index(asc_sign)
    except ValueError:
        return {}
        
    for house_num in range(1, 13):
        # 1. Sign of the house
        house_sign_idx = (asc_idx + house_num - 1) % 12
        house_sign = SIGNS_LIST[house_sign_idx]
        
        # 2. Lord of the house
        lord = SIGN_LORDS_MAP.get(house_sign)
        
        if not lord or lord not in planet_signs:
            continue
            
        lord_sign = planet_signs[lord]
        if lord_sign is None:
            continue
            
        lord_sign_idx = SIGNS_LIST.index(lord_sign)
        
        # 3. Distance from house to lord (inclusive)
        # e.g., if house is Aries (0) and lord is in Gemini (2), distance is 2 - 0 + 1 = 3
        # In modulus math:
        distance = (lord_sign_idx - house_sign_idx) % 12
        
        # 4. Count same distance from lord forward
        arudha_sign_idx = (lord_sign_idx + distance) % 12
        
        # 5. Apply exceptions (if Arudha falls in the same house or 7th from it)
        # Same house
        if arudha_sign_idx == house_sign_idx:
            arudha_sign_idx = (arudha_sign_idx + 9) % 12  # 10th house from it (0 + 10 - 1 = 9)
        # 7th house from it
        elif arudha_sign_idx == (house_sign_idx + 6) % 12:
            arudha_sign_idx = (arudha_sign_idx + 9) % 12  # 10th house from it
            
        arudha_sign = SIGNS_LIST[arudha_sign_idx]
        arudhas[house_num] = arudha_sign
        
    return arudhas

def compute_jaimini_system(planets: List[Dict], asc_sign: str) -> Dict:
    """
    Wrapper to compute all Jaimini-related components.
    """
    return {
        "chara_karakas": calculate_chara_karakas(planets),
        "arudha_padas": calculate_arudha_padas(planets, asc_sign)
    }
