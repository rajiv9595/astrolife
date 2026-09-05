"""
Sthana Bala Calculation - Classical Parashari Implementation

Components:
1. Uchcha Bala (Exaltation strength) - based on distance from deep exaltation
2. Saptavargaja Bala (7-division strength) - based on dignity in 7 Vargas
3. Ojhayugma Bala (Odd/Even strength) - based on odd/even sign/house placement
4. Kendradi Bala (Angle strength) - based on Kendra/Panaphara/Apoklima placement
5. Drekkana Bala (Drekkana strength) - based on Drekkana placement for specific planets
"""
import math
from typing import Dict, List, Optional
from .models import SthanaBala, SthanaBalaComponent
from .profile import (
    StrengthCalculationProfile, EXALTATION_DATA, MOOLATRIKONA_DATA,
    SIGNS, get_sign_index, normalize_deg, SaptavargajaMethod
)
from ..calculation.pipeline import ChartFacts
from ..calculation.varga import calculate_all_vargas


# Classical Saptavargaja Vargas (Parashari): D1, D2, D3, D7, D9, D12, D30
SAPTAVARGI_VARGAS = [1, 2, 3, 7, 9, 12, 30]

# Drekkana Bala planets (only these planets get Drekkana Bala)
DREKKANA_BALA_PLANETS = {"Sun", "Mars", "Jupiter"}  # Male planets in first drekkana, etc.


def calculate_uchcha_bala(
    planet: str,
    sidereal_longitude: float,
    profile: StrengthCalculationProfile
) -> SthanaBalaComponent:
    """
    Uchcha Bala: Strength based on distance from deep exaltation point.
    
    Formula: 60 * (1 - distance/180) where distance is angular distance from exaltation degree.
    At exact exaltation (distance=0): 60 virupas
    At exact debilitation (distance=180): 0 virupas
    """
    if planet not in EXALTATION_DATA:
        return SthanaBalaComponent(
            name="Uchcha Bala",
            value=0.0,
            maximum=60.0,
            unit="virupas",
            description=f"No exaltation data for {planet}",
            classification="CLASSICAL"
        )
    
    ex_data = EXALTATION_DATA[planet]
    ex_sign_idx = get_sign_index(ex_data["sign"])
    ex_degree = ex_data["degree"]
    ex_total_deg = ex_sign_idx * 30 + ex_degree
    
    # Planet's sidereal longitude
    planet_total_deg = normalize_deg(sidereal_longitude)
    
    # Angular distance from exaltation point (0-180)
    distance = abs(planet_total_deg - ex_total_deg)
    if distance > 180:
        distance = 360 - distance
    
    # Uchcha Bala: 60 at distance 0, 0 at distance 180
    uchcha_bala = max(0.0, 60.0 * (1.0 - distance / 180.0))
    
    return SthanaBalaComponent(
        name="Uchcha Bala",
        value=round(uchcha_bala, 4),
        maximum=60.0,
        unit="virupas",
        description=f"Distance from exaltation ({ex_data['sign']} {ex_degree}°): {distance:.4f}°",
        classification="CLASSICAL"
    )


def calculate_saptavargaja_bala(
    planet: str,
    chart_facts: ChartFacts,
    varga_results: Dict,
    profile: StrengthCalculationProfile
) -> SthanaBalaComponent:
    """
    Saptavargaja Bala: Strength based on dignity in 7 Vargas.
    
    Classical method: Each varga gives up to 60/7 ≈ 8.57 virupas based on sign dignity.
    Dignity scores: Exalted=60, Moolatrikona=45, Own=30, Friend=22.5, Neutral=15, Enemy=7.5, Debilitated=0
    Then averaged across 7 vargas.
    """
    if profile.saptavargaja_method != SaptavargajaMethod.PARASHARI_7_VARGAS:
        return SthanaBalaComponent(
            name="Saptavargaja Bala",
            value=0.0,
            maximum=60.0,
            unit="virupas",
            description=f"Method {profile.saptavargaja_method} not implemented",
            classification="APPROXIMATION"
        )
    
    # Dignity score mapping (virupas per varga, max 60 per varga)
    DIGNITY_SCORES = {
        "EXALTED": 60.0,
        "MOOLATRIKONA": 45.0,
        "OWN_SIGN": 30.0,
        "FRIEND": 22.5,
        "NEUTRAL": 15.0,
        "ENEMY": 7.5,
        "DEBILITATED": 0.0,
    }
    
    # Get planet's positions in each of the 7 vargas
    total_score = 0.0
    varga_details = []
    
    for varga_num in SAPTAVARGI_VARGAS:
        varga_key = f"d{varga_num}"
        if varga_key not in varga_results:
            continue
        
        varga_data = varga_results[varga_key]
        # Find planet in varga
        planet_varga = None
        for p in varga_data.get("planets", []):
            if p.get("name") == planet:
                planet_varga = p
                break
        
        if not planet_varga:
            continue
        
        varga_sign = planet_varga.get("sign")
        if not varga_sign:
            continue
        
        # Determine dignity in this varga
        dignity = get_dignity_in_sign(planet, varga_sign)
        score = DIGNITY_SCORES.get(dignity, 0.0)
        
        total_score += score
        varga_details.append({
            "varga": varga_num,
            "sign": varga_sign,
            "dignity": dignity,
            "score": score
        })
    
    # Average across 7 vargas (each contributes up to 60/7)
    # Actually classical method: sum of scores / 7
    avg_score = total_score / len(SAPTAVARGI_VARGAS) if varga_details else 0.0
    
    return SthanaBalaComponent(
        name="Saptavargaja Bala",
        value=round(avg_score, 4),
        maximum=60.0,
        unit="virupas",
        description=f"Average dignity across {len(varga_details)} vargas: {varga_details}",
        classification="CLASSICAL"
    )


def get_dignity_in_sign(planet: str, sign: str) -> str:
    """Determine dignity of planet in a sign"""
    if planet not in EXALTATION_DATA:
        return "NEUTRAL"
    
    ex_data = EXALTATION_DATA[planet]
    mool_data = MOOLATRIKONA_DATA.get(planet, {})
    
    # Exaltation check (with degree)
    if sign == ex_data["sign"]:
        return "EXALTED"
    
    # Debilitation check
    if sign == ex_data["debilitation_sign"]:
        return "DEBILITATED"
    
    # Moolatrikona check
    if sign == mool_data.get("sign"):
        return "MOOLATRIKONA"
    
    # Own sign
    from backend.tables import SIGN_LORDS
    if SIGN_LORDS.get(sign) == planet:
        return "OWN_SIGN"
    
    # Friend/Enemy/Neutral from natural friendship
    from core.strength.profile import NATURAL_FRIENDSHIP
    nat = NATURAL_FRIENDSHIP.get(planet, {})
    sign_lord = SIGN_LORDS.get(sign)
    
    if sign_lord in nat.get("friends", []):
        return "FRIEND"
    if sign_lord in nat.get("enemies", []):
        return "ENEMY"
    
    return "NEUTRAL"


def calculate_ojhayugma_bala(
    planet: str,
    sidereal_longitude: float,
    house: int,
    profile: StrengthCalculationProfile
) -> SthanaBalaComponent:
    """
    Ojhayugma Bala: Odd/Even sign and house strength.
    
    Classical rules (Parashara):
    - Moon and Venus: 15 virupas each in even sign, 15 in even house (max 30)
    - Other planets: 15 virupas each in odd sign, 15 in odd house (max 30)
    """
    sign_idx = int(sidereal_longitude // 30)  # 0-indexed
    is_odd_sign = (sign_idx % 2 == 0)  # Aries=0 is odd
    is_odd_house = (house % 2 == 1)
    
    value = 0.0
    details = []
    
    # Moon and Venus: strength in even signs/houses
    if planet in ["Moon", "Venus"]:
        if not is_odd_sign:  # even sign
            value += 15.0
            details.append("Even sign (+15)")
        if not is_odd_house:  # even house
            value += 15.0
            details.append("Even house (+15)")
    else:
        # Other planets: strength in odd signs/houses
        if is_odd_sign:
            value += 15.0
            details.append("Odd sign (+15)")
        if is_odd_house:
            value += 15.0
            details.append("Odd house (+15)")
    
    return SthanaBalaComponent(
        name="Ojhayugma Bala",
        value=round(value, 4),
        maximum=30.0,
        unit="virupas",
        description=f"Sign {'odd' if is_odd_sign else 'even'}, House {'odd' if is_odd_house else 'even'}: {'; '.join(details)}",
        classification="CLASSICAL"
    )


def calculate_kendradi_bala(
    planet: str,
    house: int,
    profile: StrengthCalculationProfile
) -> SthanaBalaComponent:
    """
    Kendradi Bala: Angular house strength.
    
    Classical (Parashara):
    - Kendra (1,4,7,10): 60 virupas
    - Panaphara (2,5,8,11): 30 virupas
    - Apoklima (3,6,9,12): 15 virupas
    """
    kendra_houses = {1, 4, 7, 10}
    panaphara_houses = {2, 5, 8, 11}
    apoklima_houses = {3, 6, 9, 12}
    
    if house in kendra_houses:
        value = 60.0
        house_type = "Kendra"
    elif house in panaphara_houses:
        value = 30.0
        house_type = "Panaphara"
    elif house in apoklima_houses:
        value = 15.0
        house_type = "Apoklima"
    else:
        value = 0.0
        house_type = "Unknown"
    
    return SthanaBalaComponent(
        name="Kendradi Bala",
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        description=f"House {house} = {house_type} ({value} virupas)",
        classification="CLASSICAL"
    )


def calculate_drekkana_bala(
    planet: str,
    sidereal_longitude: float,
    profile: StrengthCalculationProfile
) -> SthanaBalaComponent:
    """
    Drekkana Bala: Strength based on Drekkana (D3) placement.
    
    Classical (Parashara):
    - Male planets (Sun, Mars, Jupiter): 15 virupas in 1st drekkana of odd signs, 15 in 3rd drekkana of even signs
    - Female planets (Moon, Venus): 15 virupas in 2nd drekkana of odd signs, 15 in 2nd drekkana of even signs
    - Mercury: 15 virupas in 1st drekkana of odd signs, 15 in 3rd drekkana of even signs
    - Saturn: 15 virupas in 3rd drekkana of odd signs, 15 in 1st drekkana of even signs
    
    Each drekkana = 10 degrees
    Drekkana 1: 0-10°, Drekkana 2: 10-20°, Drekkana 3: 20-30°
    """
    if planet not in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        return SthanaBalaComponent(
            name="Drekkana Bala",
            value=0.0,
            maximum=15.0,
            unit="virupas",
            description=f"Drekkana Bala not defined for {planet}",
            classification="CLASSICAL"
        )
    
    deg_in_sign = sidereal_longitude % 30
    drekkana = int(deg_in_sign // 10) + 1  # 1, 2, or 3
    sign_idx = int(sidereal_longitude // 30)
    is_odd_sign = (sign_idx % 2 == 0)
    
    value = 0.0
    details = []
    
    # Male planets
    if planet in ["Sun", "Mars", "Jupiter"]:
        if is_odd_sign and drekkana == 1:
            value = 15.0
            details.append("Male planet in 1st drekkana of odd sign")
        elif not is_odd_sign and drekkana == 3:
            value = 15.0
            details.append("Male planet in 3rd drekkana of even sign")
    
    # Female planets
    elif planet in ["Moon", "Venus"]:
        if drekkana == 2:
            value = 15.0
            details.append("Female planet in 2nd drekkana")
    
    # Mercury (neutral/male)
    elif planet == "Mercury":
        if is_odd_sign and drekkana == 1:
            value = 15.0
            details.append("Mercury in 1st drekkana of odd sign")
        elif not is_odd_sign and drekkana == 3:
            value = 15.0
            details.append("Mercury in 3rd drekkana of even sign")
    
    # Saturn
    elif planet == "Saturn":
        if is_odd_sign and drekkana == 3:
            value = 15.0
            details.append("Saturn in 3rd drekkana of odd sign")
        elif not is_odd_sign and drekkana == 1:
            value = 15.0
            details.append("Saturn in 1st drekkana of even sign")
    
    return SthanaBalaComponent(
        name="Drekkana Bala",
        value=round(value, 4),
        maximum=15.0,
        unit="virupas",
        description=f"Drekkana {drekkana} in {'odd' if is_odd_sign else 'even'} sign: {'; '.join(details) if details else 'No strength'}",
        classification="CLASSICAL"
    )


def calculate_sthana_bala(
    planet: str,
    chart_facts: ChartFacts,
    varga_results: Dict,
    profile: StrengthCalculationProfile
) -> SthanaBala:
    """Calculate complete Sthana Bala with all subcomponents"""
    
    planet_data = chart_facts.planets.get(planet)
    if not planet_data:
        return SthanaBala(total=0, maximum=0, components=[])
    
    sidereal_lon = planet_data.longitude.sidereal
    house = planet_data.house
    
    components = []
    
    # 1. Uchcha Bala
    uchcha = calculate_uchcha_bala(planet, sidereal_lon, profile)
    components.append(uchcha)
    
    # 2. Saptavargaja Bala
    saptavargaja = calculate_saptavargaja_bala(planet, chart_facts, varga_results, profile)
    components.append(saptavargaja)
    
    # 3. Ojhayugma Bala
    ojhayugma = calculate_ojhayugma_bala(planet, sidereal_lon, house, profile)
    components.append(ojhayugma)
    
    # 4. Kendradi Bala
    kendradi = calculate_kendradi_bala(planet, house, profile)
    components.append(kendradi)
    
    # 5. Drekkana Bala
    drekkana = calculate_drekkana_bala(planet, sidereal_lon, profile)
    components.append(drekkana)
    
    total = sum(c.value for c in components)
    maximum = sum(c.maximum for c in components)
    
    return SthanaBala(
        uchcha_bala=uchcha,
        saptavargaja_bala=saptavargaja,
        ojhayugma_bala=ojhayugma,
        kendradi_bala=kendradi,
        drekkana_bala=drekkana,
        total=round(total, 4),
        maximum=round(maximum, 4),
        unit="virupas",
        components=components
    )