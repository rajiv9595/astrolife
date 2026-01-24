from typing import Dict, Any, List

# Import tables to reuse mappings
from backend.tables import SIGN_LORDS, FRIENDLY_SIGNS

# Constants for Strength Scoring
SCORE_EXALTED = 100
SCORE_MOOLATRIKONA = 80  # Simplify: Moolatrikona ranges are complex, we might treat Own Sign high
SCORE_OWN_SIGN = 75
SCORE_FRIEND_SIGN = 60
SCORE_NEUTRAL_SIGN = 50
SCORE_ENEMY_SIGN = 30
SCORE_DEBILITATED = 0

# House Strengths (Slightly arbitrary but relative)
SCORE_KENDRA = 20  # Bonus for Kendra
SCORE_TRIKONA = 15 # Bonus for Trikona
SCORE_DUSTHANA = -15 # Penalty for Dusthana

# Functional Nature
TRINES = [1, 5, 9]
KENDRAS = [1, 4, 7, 10]
DUSTHANAS = [6, 8, 12]
UPACHAYAS = [3, 6, 10, 11]

# Digbala Houses (Directional Strength)
DIGBALA_HOUSES = {
    "Sun": [10], "Mars": [10],
    "Moon": [4], "Venus": [4],
    "Jupiter": [1], "Mercury": [1],
    "Saturn": [7]
}

def get_sign_nature(planet: str, sign: str) -> str:
    """Determine if sign is Own, Friend, Enemy, Exalted, Debilitated."""
    # Check Exalt/Debil first (Using calculations.py mappings logic, but hardcoded here for speed or import)
    # Actually better to import checks if possible, but let's define simplified here to avoid circular imports
    
    EXALTED = {
        "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
        "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra", "Rahu": "Taurus", "Ketu": "Scorpio"
    }
    DEBILITATED = {
        "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
        "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries", "Rahu": "Scorpio", "Ketu": "Taurus"
    }
    
    if EXALTED.get(planet) == sign: return "Exalted"
    if DEBILITATED.get(planet) == sign: return "Debilitated"
    if SIGN_LORDS.get(sign) == planet: return "Own Sign"
    
    lord = SIGN_LORDS.get(sign)
    friends = FRIENDLY_SIGNS.get(planet, [])
    
    # Simple enemy logic (if not friend and not own, assume neutral or enemy)
    # This is a simplification. For now, let's treat non-friends as Enemy/Neutral.
    if lord in friends: return "Friend Sign"
    
    return "Enemy Sign" # Simplified

def get_house_type(house_num: int) -> List[str]:
    types = []
    if house_num in KENDRAS: types.append("Kendra")
    if house_num in TRINES: types.append("Trikona")
    if house_num in DUSTHANAS: types.append("Dusthana")
    if house_num in UPACHAYAS: types.append("Upachaya")
    return types

def evaluate_planet_strength(planet_name: str, p_data: Dict, asc_sign: str, d9_planets: List[Dict]) -> Dict[str, Any]:
    """
    Evaluates the strength of a single planet based on D1 and D9.
    """
    score = 0
    reasons = []
    
    # 1. Sign Placement Prediction
    sign = p_data.get("sign") or p_data.get("sign_name")
    nature = get_sign_nature(planet_name, sign)
    
    if nature == "Exalted": 
        score += SCORE_EXALTED
        reasons.append("Exalted in D1 (+Power)")
    elif nature == "Debilitated": 
        score += SCORE_DEBILITATED
        reasons.append("Debilitated in D1 (-Power)")
    elif nature == "Own Sign": 
        score += SCORE_OWN_SIGN
        reasons.append("Own Sign (+Stability)")
    elif nature == "Friend Sign": 
        score += SCORE_FRIEND_SIGN
    else: 
        score += SCORE_ENEMY_SIGN
        reasons.append("Enemy Sign (-Comfort)")

    # 2. House Placement
    house_num = p_data.get("house_num") or p_data.get("house")
    if house_num:
        if house_num in KENDRAS: 
            score += SCORE_KENDRA
            reasons.append("In Kendra (Action Power)")
        if house_num in TRINES: 
            score += SCORE_TRIKONA
            if house_num != 1: reasons.append("In Trikona (Luck)")
        if house_num in DUSTHANAS: 
            score += SCORE_DUSTHANA
            reasons.append("In Dusthana (Obstacles)")
            
        # Digbala
        if house_num in DIGBALA_HOUSES.get(planet_name, []):
            score += 30
            reasons.append(f"Digbala in House {house_num} (Directional Strength)")

    # 3. Retrogression
    is_retro = p_data.get("retrograde") or p_data.get("is_retro")
    if is_retro:
        score += 20
        reasons.append("Retrograde (Chesta Bala - High Effort)")

    # 4. D9 (Navamsa) Confirmation
    # Find this planet in D9 data
    if d9_planets:
        d9_p = next((p for p in d9_planets if p["name"] == planet_name), None)
        if d9_p:
            d9_sign = d9_p.get("sign")
            d9_nature = get_sign_nature(planet_name, d9_sign)
            
            # Vargottama Check
            if d9_sign == sign:
                score += 40
                reasons.append("Vargottama (Strong in D1 & D9)")
            
            # Improvement Check
            if nature == "Debilitated" and (d9_nature == "Exalted" or d9_nature == "Own Sign"):
                score += 50 # massive redemption
                reasons.append("Neecha Bhanga (Improved in D9)")
            elif nature == "Exalted" and d9_nature == "Debilitated":
                score -= 40
                reasons.append("Weak in Navamsa (Outcome impacted)")
            elif d9_nature == "Exalted":
                score += 20
                reasons.append("Exalted in Navamsa")
            elif d9_nature == "Debilitated":
                score -= 20
                reasons.append("Debilitated in Navamsa")

    # 5. Final Categorization
    percentage = min(max(score, 0), 100) # Clamp 0-100 (roughly)
    # Actually score can go above 100, let's normalize roughly relative to max possible ~150
    normalized_score = min(score, 120) / 1.2
    
    strength_label = "Moderate"
    if normalized_score >= 80: strength_label = "Very Strong"
    elif normalized_score >= 65: strength_label = "Strong"
    elif normalized_score <= 35: strength_label = "Weak"
    elif normalized_score <= 20: strength_label = "Very Weak"

    return {
        "planet": planet_name,
        "score": round(normalized_score, 1),
        "label": strength_label,
        "nature": nature,
        "reasons": reasons
    }

def calculate_chart_strengths(chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Main function to calculate strengths for all planets in the chart.
    """
    results = []
    
    planets = chart_data.get("planets", {})
    if isinstance(planets, list): # Normalize input to list
        planet_list = planets
    elif isinstance(planets, dict):
        planet_list = []
        for k, v in planets.items():
            v['name'] = k
            planet_list.append(v)
    else:
        return []

    d9_data = chart_data.get("d9", {})
    d9_planets = d9_data.get("planets", [])
    
    asc_sign = chart_data.get("ascendant", {}).get("sign")

    for p in planet_list:
        if p["name"] in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
            strength = evaluate_planet_strength(p["name"], p, asc_sign, d9_planets)
            results.append(strength)
            
    return results
