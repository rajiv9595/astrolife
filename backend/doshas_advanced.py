from typing import Dict, List

SIGNS_LIST = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_sign_index(sign: str) -> int:
    try:
        return SIGNS_LIST.index(sign)
    except ValueError:
        return 0

def check_kala_sarpa_dosha(planets: Dict[str, Dict]) -> Dict:
    """
    Checks if all 7 planets are hemmed between Rahu and Ketu.
    Returns dosha status and type.
    """
    rahu = planets.get("Rahu")
    ketu = planets.get("Ketu")
    
    if not rahu or not ketu:
        return {"has_dosha": False, "verdict": "No Dosha", "details": "Rahu or Ketu missing from chart data."}

    r_idx = get_sign_index(rahu.get("sign_manual"))
    k_idx = get_sign_index(ketu.get("sign_manual"))
    
    # Calculate the two halves
    half_1 = [] # Clockwise from Rahu to Ketu
    curr = r_idx
    while curr != k_idx:
        half_1.append(curr)
        curr = (curr + 1) % 12
        
    half_2 = [] # Clockwise from Ketu to Rahu
    curr = k_idx
    while curr != r_idx:
        half_2.append(curr)
        curr = (curr + 1) % 12

    primary_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    
    p_indices = []
    for p in primary_planets:
        if p in planets:
            p_indices.append(get_sign_index(planets[p].get("sign_manual")))

    all_in_half_1 = all(p_idx in half_1 for p_idx in p_indices)
    all_in_half_2 = all(p_idx in half_2 for p_idx in p_indices)

    if all_in_half_1 or all_in_half_2:
        return {
            "has_dosha": True, 
            "verdict": "Active Kala Sarpa", 
            "details": "All 7 primary planets are hemmed between the Rahu-Ketu axis, forming Kala Sarpa Yoga."
        }
    
    return {
        "has_dosha": False, 
        "verdict": "No Dosha", 
        "details": "Planets are distributed outside the Rahu-Ketu axis."
    }

def check_pitru_dosha(planets: Dict[str, Dict], asc_sign: str) -> Dict:
    """
    Checks for Pitru Dosha.
    Simplified classical rule: 
    Sun or Moon conjunct Rahu/Ketu, OR Rahu/Ketu placed in the 9th house.
    """
    rahu = planets.get("Rahu")
    ketu = planets.get("Ketu")
    sun = planets.get("Sun")
    moon = planets.get("Moon")
    
    if not all([rahu, ketu, sun, moon, asc_sign]):
        return {"has_dosha": False, "verdict": "No Dosha", "details": "Insufficient data."}

    asc_idx = get_sign_index(asc_sign)
    r_idx = get_sign_index(rahu.get("sign_manual"))
    k_idx = get_sign_index(ketu.get("sign_manual"))
    s_idx = get_sign_index(sun.get("sign_manual"))
    m_idx = get_sign_index(moon.get("sign_manual"))
    
    # Check 9th house
    ninth_house_idx = (asc_idx + 8) % 12
    
    reasons = []
    if r_idx == ninth_house_idx:
        reasons.append("Rahu is positioned in the 9th House (House of Ancestors/Dharma).")
    if k_idx == ninth_house_idx:
        reasons.append("Ketu is positioned in the 9th House (House of Ancestors/Dharma).")
        
    # Check conjunctions
    if s_idx == r_idx:
        reasons.append("Sun (Karaka for Father) is afflicted by conjunction with Rahu.")
    if s_idx == k_idx:
        reasons.append("Sun (Karaka for Father) is afflicted by conjunction with Ketu.")
    if m_idx == r_idx:
        reasons.append("Moon (Karaka for Mother) is afflicted by conjunction with Rahu.")
    if m_idx == k_idx:
        reasons.append("Moon (Karaka for Mother) is afflicted by conjunction with Ketu.")
        
    if reasons:
        return {
            "has_dosha": True,
            "verdict": "Active Pitru Dosha",
            "details": "Afflictions found in the ancestral and parental indicators.",
            "reasons": reasons
        }
        
    return {
        "has_dosha": False,
        "verdict": "No Dosha",
        "details": "No major afflictions found on the Sun, Moon, or 9th house by lunar nodes.",
        "reasons": []
    }

def compute_advanced_doshas(planets: Dict[str, Dict], asc_sign: str) -> Dict:
    return {
        "kala_sarpa_dosha": check_kala_sarpa_dosha(planets),
        "pitru_dosha": check_pitru_dosha(planets, asc_sign)
    }
