from typing import List, Dict

SIGNS_LIST = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Max Dig Bala Houses for each planet
DIG_BALA_HOUSES = {
    "Sun": 10,
    "Mars": 10,
    "Saturn": 7,
    "Moon": 4,
    "Venus": 4,
    "Jupiter": 1,
    "Mercury": 1
}

# Fixed Natural Strength (in Virupas, out of 60)
NAISARGIKA_BALA = {
    "Sun": 60,
    "Moon": 51.43,
    "Venus": 42.85,
    "Jupiter": 34.28,
    "Mercury": 25.7,
    "Mars": 17.14,
    "Saturn": 8.57
}

# Exaltation signs and exact degrees
EXALTATION_DEGREES = {
    "Sun": ("Aries", 10),
    "Moon": ("Taurus", 3),
    "Mars": ("Capricorn", 28),
    "Mercury": ("Virgo", 15),
    "Jupiter": ("Cancer", 5),
    "Venus": ("Pisces", 27),
    "Saturn": ("Libra", 20)
}

def get_sign_index(sign: str) -> int:
    try:
        return SIGNS_LIST.index(sign)
    except ValueError:
        return 0

def compute_shadbala(planets: Dict[str, Dict], asc_sign: str, is_day_birth: bool = True) -> Dict[str, Dict]:
    """
    Computes a simplified Shadbala (6-fold strength) for the 7 primary planets.
    Returns strengths measured in Rupas (where 1 Rupa = 60 Virupas).
    """
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    shadbala_results = {}
    
    asc_idx = get_sign_index(asc_sign)

    for p_name in valid_planets:
        if p_name not in planets:
            continue
            
        p_data = planets[p_name]
        sign = p_data.get("sign_manual")
        deg_in_sign = p_data.get("degree_in_sign_manual", 0.0)
        p_idx = get_sign_index(sign)
        retrograde = p_data.get("retrograde", False)
        
        # 1. Sthana Bala (Ocha Bala component - Positional)
        # Max 60 Virupas at deep exaltation, 0 at deep debilitation.
        ex_sign, ex_deg = EXALTATION_DEGREES.get(p_name, ("Aries", 0))
        ex_sign_idx = get_sign_index(ex_sign)
        
        # Calculate absolute angular distance from deep exaltation point (0 to 180 degrees)
        planet_total_deg = (p_idx * 30) + deg_in_sign
        exalt_total_deg = (ex_sign_idx * 30) + ex_deg
        
        distance = abs(planet_total_deg - exalt_total_deg)
        if distance > 180:
            distance = 360 - distance
            
        # Ocha Bala: distance is mapped such that 0 distance = 60 virupas, 180 distance = 0 virupas
        sthana_bala = max(0, 60 - (distance / 3))

        # 2. Dig Bala (Directional)
        # Max 60 Virupas when exactly in its Dig house.
        dig_house = DIG_BALA_HOUSES.get(p_name, 1)
        # House calculation based on simple sign difference (Whole Sign)
        house_num = ((p_idx - asc_idx + 12) % 12) + 1
        
        # Distance in houses (max 6 away)
        house_dist = abs(house_num - dig_house)
        if house_dist > 6:
            house_dist = 12 - house_dist
            
        dig_bala = max(0, 60 - (house_dist * 10))

        # 3. Kaala Bala (Temporal)
        # Simplified: Nocturnal planets strong at night, Diurnal during day.
        # Diurnal: Sun, Jupiter, Venus. Nocturnal: Moon, Mars, Saturn. Mercury is strong in both.
        diurnal = ["Sun", "Jupiter", "Venus"]
        nocturnal = ["Moon", "Mars", "Saturn"]
        
        if p_name in diurnal:
            kaala_bala = 60 if is_day_birth else 30
        elif p_name in nocturnal:
            kaala_bala = 30 if is_day_birth else 60
        else: # Mercury
            kaala_bala = 60

        # 4. Chesta Bala (Motional)
        # Simplified: Retrograde planets get full 60, stationary get 30, direct get roughly based on speed.
        # We will assign 60 for retrograde, 30 for direct normal. Sun and Moon don't retrograde, they get standard 30.
        if p_name in ["Sun", "Moon"]:
            chesta_bala = 30
        else:
            chesta_bala = 60 if retrograde else 30

        # 5. Naisargika Bala (Natural)
        naisargika_bala = NAISARGIKA_BALA.get(p_name, 0)

        # 6. Drig Bala (Aspectual)
        # A baseline of 30 virupas assigned unless full aspecting engine is wired.
        drig_bala = 30

        # Total in Virupas
        total_virupas = sthana_bala + dig_bala + kaala_bala + chesta_bala + naisargika_bala + drig_bala
        
        # Convert to Rupas (1 Rupa = 60 Virupas)
        total_rupas = round(total_virupas / 60, 2)
        
        shadbala_results[p_name] = {
            "sthana_bala": round(sthana_bala, 1),
            "dig_bala": round(dig_bala, 1),
            "kaala_bala": round(kaala_bala, 1),
            "chesta_bala": round(chesta_bala, 1),
            "naisargika_bala": round(naisargika_bala, 1),
            "drig_bala": round(drig_bala, 1),
            "total_virupas": round(total_virupas, 1),
            "total_rupas": total_rupas,
            "strength_level": "High" if total_rupas >= 3.8 else ("Medium" if total_rupas >= 3.2 else "Low")
        }

    return shadbala_results
