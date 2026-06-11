from typing import Dict, List

SIGNS_LIST = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Naisargika Maitri (Natural Relationship) 
# Dict[Planet, Dict[OtherPlanet, Relationship]]
NAISARGIKA_MAITRI = {
    "Sun": {"Friends": ["Moon", "Mars", "Jupiter"], "Enemies": ["Venus", "Saturn"], "Neutral": ["Mercury"]},
    "Moon": {"Friends": ["Sun", "Mercury"], "Enemies": [], "Neutral": ["Mars", "Jupiter", "Venus", "Saturn"]},
    "Mars": {"Friends": ["Sun", "Moon", "Jupiter"], "Enemies": ["Mercury"], "Neutral": ["Venus", "Saturn"]},
    "Mercury": {"Friends": ["Sun", "Venus"], "Enemies": ["Moon"], "Neutral": ["Mars", "Jupiter", "Saturn"]},
    "Jupiter": {"Friends": ["Sun", "Moon", "Mars"], "Enemies": ["Mercury", "Venus"], "Neutral": ["Saturn"]},
    "Venus": {"Friends": ["Mercury", "Saturn"], "Enemies": ["Sun", "Moon"], "Neutral": ["Mars", "Jupiter"]},
    "Saturn": {"Friends": ["Mercury", "Venus"], "Enemies": ["Sun", "Moon", "Mars"], "Neutral": ["Jupiter"]}
}

def get_sign_index(sign: str) -> int:
    try:
        return SIGNS_LIST.index(sign)
    except ValueError:
        return 0

def get_natural_relationship(p1: str, p2: str) -> str:
    if p1 == p2:
        return "Self"
    if p2 in NAISARGIKA_MAITRI[p1]["Friends"]:
        return "Friend"
    if p2 in NAISARGIKA_MAITRI[p1]["Enemies"]:
        return "Enemy"
    return "Neutral"

def get_compound_relationship(natural: str, temporal: str) -> str:
    """
    Combines Natural and Temporal relationships.
    Friend + Friend = Best Friend (Adhi Mitra)
    Friend + Enemy / Enemy + Friend = Neutral (Sama)
    Neutral + Friend = Friend (Mitra)
    Neutral + Enemy = Enemy (Shatru)
    Enemy + Enemy = Bitter Enemy (Adhi Shatru)
    """
    if natural == "Friend":
        return "Best Friend" if temporal == "Friend" else "Neutral"
    elif natural == "Enemy":
        return "Neutral" if temporal == "Friend" else "Bitter Enemy"
    else: # Neutral
        return "Friend" if temporal == "Friend" else "Enemy"

def compute_maitri_chakra(planets: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Computes the Panchadha Maitri Chakra (5-fold relationship).
    Returns a dictionary mapping each planet to its relationship with all other planets.
    """
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    chakra = {}

    for p1 in valid_planets:
        if p1 not in planets:
            continue
            
        chakra[p1] = {}
        p1_idx = get_sign_index(planets[p1].get("sign_manual"))

        for p2 in valid_planets:
            if p2 not in planets or p1 == p2:
                continue
                
            p2_idx = get_sign_index(planets[p2].get("sign_manual"))
            
            # Calculate Temporal Relationship
            # P2 is Friend if placed in 2, 3, 4, 10, 11, 12 from P1.
            # Else Enemy.
            house_diff = ((p2_idx - p1_idx + 12) % 12) + 1
            if house_diff in [2, 3, 4, 10, 11, 12]:
                temporal = "Friend"
            else:
                temporal = "Enemy"
                
            # Natural Relationship
            natural = get_natural_relationship(p1, p2)
            
            # Compound Relationship
            compound = get_compound_relationship(natural, temporal)
            
            chakra[p1][p2] = {
                "natural": natural,
                "temporal": temporal,
                "compound": compound
            }

    return chakra
