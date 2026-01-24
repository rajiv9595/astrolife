# yoga_evaluator.py - Evaluate yoga rulesets using D1 placements

import json
import os
from typing import Dict, List, Any, Optional, Tuple
import math

# Sign lords mapping
SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter"
}

# Kendra houses: 1, 4, 7, 10
KENDRA_HOUSES = [1, 4, 7, 10]

# Trikona houses: 1, 5, 9
TRIKONA_HOUSES = [1, 5, 9]

# Dusthana houses: 6, 8, 12
DUSTHANA_HOUSES = [6, 8, 12]

# Debilitation signs for each planet
DEBILITATION = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mercury": "Pisces",
    "Venus": "Virgo",
    "Mars": "Cancer",
    "Jupiter": "Capricorn",
    "Saturn": "Aries"
}

# Exaltation signs for each planet
EXALTATION = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mercury": "Virgo",
    "Venus": "Pisces",
    "Mars": "Capricorn",
    "Jupiter": "Cancer",
    "Saturn": "Libra"
}

# Signs array for indexing
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


def normalize_deg(d):
    """Normalize degrees to 0-360"""
    return float(d) % 360.0


def get_house_from_sign(sign: str, asc_sign: str) -> int:
    """Get house number (1-12) for a sign relative to ascendant"""
    asc_idx = SIGNS.index(asc_sign)
    sign_idx = SIGNS.index(sign)
    house = ((sign_idx - asc_idx) % 12) + 1
    return house


def get_sign_lord(sign: str) -> str:
    """Get the lord of a sign"""
    return SIGN_LORDS.get(sign, "Unknown")


def is_planet_debilitated(planet: str, sign: str) -> bool:
    """Check if planet is debilitated in a sign"""
    deb_sign = DEBILITATION.get(planet)
    return deb_sign == sign


def is_planet_exalted(planet: str, sign: str) -> bool:
    """Check if planet is exalted in a sign"""
    exalt_sign = EXALTATION.get(planet)
    return exalt_sign == sign


def get_planet_sign(planet_data: Dict, planet: str) -> Optional[str]:
    """Get the sign of a planet from planet data"""
    if planet not in planet_data:
        return None
    
    pdata = planet_data[planet]
    # Try sidereal sign (flag first, then manual)
    sign = pdata.get("sign_flag") or pdata.get("sign_manual")
    return sign


def get_planet_house(planet_data: Dict, planet: str, asc_sign: str) -> Optional[int]:
    """Get the house number (1-12) of a planet"""
    sign = get_planet_sign(planet_data, planet)
    if not sign:
        return None
    return get_house_from_sign(sign, asc_sign)


def get_house_lord(house_num: int, asc_sign: str, planet_data: Dict) -> Optional[str]:
    """Get the lord of a house (1-12)"""
    asc_idx = SIGNS.index(asc_sign)
    house_sign_idx = (asc_idx + house_num - 1) % 12
    house_sign = SIGNS[house_sign_idx]
    return get_sign_lord(house_sign)


def resolve_planet_or_lord(identifier: str, asc_sign: str, planet_data: Dict) -> Optional[str]:
    """Resolve 'planet' or 'lord(n)' to actual planet name"""
    if identifier.startswith("lord(") and identifier.endswith(")"):
        house_str = identifier[5:-1]
        try:
            house_num = int(house_str)
            return get_house_lord(house_num, asc_sign, planet_data)
        except:
            return None
    return identifier


def angular_distance_deg(lon1: float, lon2: float) -> float:
    """Calculate angular distance between two longitudes"""
    diff = abs(lon1 - lon2)
    return min(diff, 360.0 - diff)


def get_planet_longitude(planet_data: Dict, planet: str) -> Optional[float]:
    """Get sidereal longitude of a planet"""
    if planet not in planet_data:
        return None
    pdata = planet_data[planet]
    # Try sidereal (flag first, then manual)
    lon = pdata.get("lon_sidereal_flag") or pdata.get("lon_sidereal_manual")
    return lon


def evaluate_predicate(predicate: str, params: Dict, planet_data: Dict, 
                       whole_sign_houses: Dict, asc_sign: str) -> bool:
    """Evaluate a single predicate"""
    
    if predicate == "kendra_from":
        a = resolve_planet_or_lord(params.get("a"), asc_sign, planet_data)
        b = resolve_planet_or_lord(params.get("b"), asc_sign, planet_data)
        if not a or not b:
            return False
        
        house_a = get_planet_house(planet_data, a, asc_sign)
        house_b = get_planet_house(planet_data, b, asc_sign)
        if not house_a or not house_b:
            return False
        
        include_conj = params.get("include_conjunction", False)
        
        # Kendra from B: 1st, 4th, 7th, 10th from B's position
        # If B is in house X, A should be in X, X+3, X+6, or X+9 (mod 12)
        diff = (house_a - house_b) % 12
        is_kendra = diff in [0, 3, 6, 9]  # 1st (0), 4th (3), 7th (6), 10th (9)
        
        if not is_kendra:
            return False
        
        # If same house, check include_conjunction
        if diff == 0 and not include_conj:
            return False
        
        # Optional orb check
        orb_deg = params.get("orb_deg", 0)
        if orb_deg > 0:
            lon_a = get_planet_longitude(planet_data, a)
            lon_b = get_planet_longitude(planet_data, b)
            if lon_a and lon_b:
                angular_diff = angular_distance_deg(lon_a, lon_b)
                # Check if within orb for kendra angles (0, 90, 180, 270 degrees)
                expected_angles = [0, 90, 180, 270]
                for expected in expected_angles:
                    if abs(angular_diff - expected) <= orb_deg:
                        return True
                # Also check exact kendra house angles
                return angular_diff <= orb_deg or abs(angular_diff - 90) <= orb_deg or abs(angular_diff - 180) <= orb_deg or abs(angular_diff - 270) <= orb_deg
        
        return True
    
    elif predicate == "planet_in_signs":
        planet = params.get("planet")
        if not planet:
            return False
        signs_list = params.get("signs", [])
        sign = get_planet_sign(planet_data, planet)
        if not sign:
            return False
        sign_idx = SIGNS.index(sign)
        # Signs are 1-indexed in JSON (1=Aries, 12=Pisces)
        return (sign_idx + 1) in signs_list
    
    elif predicate == "planet_debilitated":
        planet = params.get("planet")
        if not planet:
            return False
        sign = get_planet_sign(planet_data, planet)
        if not sign:
            return False
        return is_planet_debilitated(planet, sign)
    
    elif predicate == "planet_exalted":
        planet = params.get("planet")
        if not planet:
            return False
        sign = get_planet_sign(planet_data, planet)
        if not sign:
            return False
        return is_planet_exalted(planet, sign)

    elif predicate == "planet_combust":
        planet = params.get("planet")
        if not planet:
            return False
        # Retrieve combust status from planet_data
        if planet in planet_data:
             return planet_data[planet].get("combust", False)
        return False
    
    elif predicate == "any_connection":
        a = resolve_planet_or_lord(params.get("a"), asc_sign, planet_data)
        b = resolve_planet_or_lord(params.get("b"), asc_sign, planet_data)
        if not a or not b:
            return False
        
        lon_a = get_planet_longitude(planet_data, a)
        lon_b = get_planet_longitude(planet_data, b)
        if not lon_a or not lon_b:
            return False
        
        orb_deg = params.get("orb_deg", 8)
        angular_diff = angular_distance_deg(lon_a, lon_b)
        
        # Check conjunction (same sign or within orb)
        if angular_diff <= orb_deg:
            return True
        
        # Check aspects (basic - 7th house aspect)
        house_a = get_planet_house(planet_data, a, asc_sign)
        house_b = get_planet_house(planet_data, b, asc_sign)
        if house_a and house_b:
            diff = abs(house_a - house_b) % 12
            if diff == 6:  # 7th house aspect
                return True
        
        return False
    
    elif predicate == "conjunction":
        a = resolve_planet_or_lord(params.get("a"), asc_sign, planet_data)
        b = resolve_planet_or_lord(params.get("b"), asc_sign, planet_data)
        if not a or not b:
            return False
        
        lon_a = get_planet_longitude(planet_data, a)
        lon_b = get_planet_longitude(planet_data, b)
        if not lon_a or not lon_b:
            return False
        
        orb_deg = params.get("orb_deg", 8)
        angular_diff = angular_distance_deg(lon_a, lon_b)
        return angular_diff <= orb_deg
    
    elif predicate == "planet_in_house_group_from_asc":
        planet = resolve_planet_or_lord(params.get("planet"), asc_sign, planet_data)
        if not planet:
            return False
        
        group = params.get("group")
        house = get_planet_house(planet_data, planet, asc_sign)
        if not house:
            return False
        
        if group == "kendra":
            return house in KENDRA_HOUSES
        elif group == "trikona":
            return house in TRIKONA_HOUSES
        elif group == "dusthana":
            return house in DUSTHANA_HOUSES
        return False
    
    elif predicate == "lord_exchange":
        a = resolve_planet_or_lord(params.get("a"), asc_sign, planet_data)
        b = resolve_planet_or_lord(params.get("b"), asc_sign, planet_data)
        if not a or not b:
            return False
        
        # Check if lord A is in sign B and lord B is in sign A
        sign_a = get_planet_sign(planet_data, a)
        sign_b = get_planet_sign(planet_data, b)
        if not sign_a or not sign_b:
            return False
        
        lord_a = get_sign_lord(sign_a)
        lord_b = get_sign_lord(sign_b)
        
        # Check if a is in sign ruled by b, and b is in sign ruled by a
        return (get_sign_lord(sign_a) == b and get_sign_lord(sign_b) == a)
    
    elif predicate == "any_yogakaraka":
        # Yogakaraka = planet that is both lord of a kendra and lord of a trikona
        # For each sign, check if its lord owns both kendra and trikona
        for house in range(1, 13):
            lord = get_house_lord(house, asc_sign, planet_data)
            if not lord:
                continue
            
            # Check if this lord owns both kendra and trikona
            kendra_owned = any(get_house_lord(h, asc_sign, planet_data) == lord for h in KENDRA_HOUSES)
            trikona_owned = any(get_house_lord(h, asc_sign, planet_data) == lord for h in TRIKONA_HOUSES)
            
            if kendra_owned and trikona_owned:
                return True
        return False
    
    elif predicate == "yogakaraka_in_group_from_asc":
        group = params.get("group")
        # Find yogakaraka and check if it's in the group
        for house in range(1, 13):
            lord = get_house_lord(house, asc_sign, planet_data)
            if not lord:
                continue
            
            kendra_owned = any(get_house_lord(h, asc_sign, planet_data) == lord for h in KENDRA_HOUSES)
            trikona_owned = any(get_house_lord(h, asc_sign, planet_data) == lord for h in TRIKONA_HOUSES)
            
            if kendra_owned and trikona_owned:
                house_yk = get_planet_house(planet_data, lord, asc_sign)
                if not house_yk:
                    continue
                
                if group == "kendra":
                    return house_yk in KENDRA_HOUSES
                elif group == "trikona":
                    return house_yk in TRIKONA_HOUSES
        return False
    
    elif predicate == "yogakaraka_strong_place":
        # Check if yogakaraka is in kendra or trikona
        for house in range(1, 13):
            lord = get_house_lord(house, asc_sign, planet_data)
            if not lord:
                continue
            
            kendra_owned = any(get_house_lord(h, asc_sign, planet_data) == lord for h in KENDRA_HOUSES)
            trikona_owned = any(get_house_lord(h, asc_sign, planet_data) == lord for h in TRIKONA_HOUSES)
            
            if kendra_owned and trikona_owned:
                house_yk = get_planet_house(planet_data, lord, asc_sign)
                if not house_yk:
                    continue
                
                return house_yk in KENDRA_HOUSES or house_yk in TRIKONA_HOUSES
        return False
    
    return False


def evaluate_condition(condition_str: str, signal_results: Dict[str, bool]) -> bool:
    """Evaluate a boolean condition string like 'signal1 and signal2 or not signal3'"""
    if not condition_str:
        return False
    
    # Replace signal IDs with their boolean values
    expr = condition_str
    for signal_id, value in signal_results.items():
        expr = expr.replace(signal_id, str(value))
    
    # Replace Python boolean operators
    expr = expr.replace("and", " and ")
    expr = expr.replace("or", " or ")
    expr = expr.replace("not", " not ")
    
    # Evaluate (simple eval - in production, use a proper parser for safety)
    try:
        return eval(expr)
    except:
        return False




def evaluate_named_pattern(pattern_name: str, planet_data: Dict, whole_sign_houses: Dict, asc_sign: str) -> bool:
    """Evaluate specific named patterns for complicated yogas"""
    
    # --- Constants ---
    benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
    malefics = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]

    # --- Aliases ---
    if pattern_name == "brahma_complex":
        pattern_name = "brahma_pattern"
    elif pattern_name == "complex_placement_indra":
        pattern_name = "indra_pattern"

    # --- Helpers ---
    def get_h(p): return get_planet_house(planet_data, p, asc_sign)
    def get_sgn(p): return get_planet_sign(planet_data, p)
    def check_house_has(h, p_list):
        in_h = [p for p in planet_data if get_h(p) == h]
        return any(x in p_list for x in in_h)
    
    # --- Patterns ---
    
    if pattern_name == "hari_pattern":
        # Benefics in 2nd, 12th, 8th from 2nd Lord
        lord_2 = get_house_lord(2, asc_sign, planet_data)
        if not lord_2: return False
        h_l2 = get_h(lord_2)
        if not h_l2: return False
        
        targets = [((h_l2 + 1) % 12) or 12, ((h_l2 + 7) % 12) or 12, ((h_l2 + 11) % 12) or 12]
        for h in targets:
             curr_ps = [p for p in planet_data if get_h(p) == h]
             if not any(p in benefics for p in curr_ps): return False
        return True

    elif pattern_name == "hara_pattern":
        # Benefics in 4, 8, 9 from 7th Lord of Ascendant
        l7 = get_house_lord(7, asc_sign, planet_data)
        if not l7: return False
        h_l7 = get_h(l7)
        if not h_l7: return False
        
        offsets = [3, 7, 8] # 4th, 8th, 9th (0-based: 3, 7, 8)
        # 4th from X = (X + 3)
        targets = [((h_l7 + off) % 12) or 12 for off in offsets]
        for h in targets:
             curr_ps = [p for p in planet_data if get_h(p) == h]
             if not any(p in benefics for p in curr_ps): return False
        return True

    elif pattern_name == "gandharva_pattern":
        # 10th Lord in Kama Trikona (3, 7, 11), Sun strong, Moon 9th
        lord_10 = get_house_lord(10, asc_sign, planet_data)
        if not get_h(lord_10) in [3, 7, 11]: return False
        
        sun_sign = get_sgn("Sun")
        if not sun_sign or (sun_sign != "Leo" and sun_sign != "Aries"): return False
        if get_h("Moon") != 9: return False
        return True

    elif pattern_name == "shiva_pattern":
        # 5L in 9, 9L in 10, 10L in 5
        l5, l9, l10 = get_house_lord(5, asc_sign, planet_data), get_house_lord(9, asc_sign, planet_data), get_house_lord(10, asc_sign, planet_data)
        return get_h(l5) == 9 and get_h(l9) == 10 and get_h(l10) == 5

    elif pattern_name == "vishnu_pattern":
        # 9L and 10L in 2nd
        l9, l10 = get_house_lord(9, asc_sign, planet_data), get_house_lord(10, asc_sign, planet_data)
        return get_h(l9) == 2 and get_h(l10) == 2

    elif pattern_name == "brahma_pattern":
        # Ju, Ve, Me in Kendras from Lagna Lord
        l1 = get_house_lord(1, asc_sign, planet_data)
        h_l1 = get_h(l1)
        if not h_l1: return False
        kendras = [h_l1, ((h_l1 + 3 - 1) % 12) + 1, ((h_l1 + 6 - 1) % 12) + 1, ((h_l1 + 9 - 1) % 12) + 1]
        
        for p in ["Jupiter", "Venus", "Mercury"]:
            if get_h(p) not in kendras: return False
        return True

    elif pattern_name == "indra_pattern":
         # Mars 3 from Moon, Sat 7 from Mars, Ven 7 from Sat
         h_m = get_h("Moon")
         if not h_m: return False
         h_ma = get_h("Mars")
         if h_ma != (((h_m + 2) % 12) or 12): return False # 3rd
         h_sa = get_h("Saturn")
         if h_sa != (((h_ma + 6) % 12) or 12): return False # 7th
         h_ve = get_h("Venus")
         if h_ve != (((h_sa + 6) % 12) or 12): return False # 7th
         return True
    
    elif pattern_name == "matsya_pattern":
        # Malefics in 1, 9; Benefics in 5
        return (check_house_has(1, malefics) and check_house_has(9, malefics) and check_house_has(5, benefics))

    elif pattern_name == "kurma_pattern":
        # Benefics 5,6,7; Malefics 1,3,11
        # Simplified to ANY benefic in 5,6,7 and ANY malefic in 1,3,11 for now
        # Strict rule: Benefics occupying 5,6,7 (and no malefics?)
        # We will follow: All of 5,6,7 have benefics AND All of 1,3,11 have malefics.
        # Actually standard definition requires planets to be PRESENT.
        good = all(check_house_has(h, benefics) for h in [5, 6, 7])
        bad = all(check_house_has(h, malefics) for h in [1, 3, 11])
        return good and bad

    elif pattern_name == "viparita_raja_yoga_check":
        # Lords of 6, 8, 12 in 6, 8, 12
        dusthanas = [6, 8, 12]
        for idx in dusthanas:
            lord = get_house_lord(idx, asc_sign, planet_data)
            if not lord: continue
            if get_h(lord) in dusthanas: return True
        return False

    elif pattern_name == "akhanda_samrajya_check":
        # 1. One of the lords of 11, 2, 9 is in Kendra from Moon
        # 2. Jupiter is Lord of 2, 5, or 11
        # Check rule 2 first
        l2 = get_house_lord(2, asc_sign, planet_data)
        l5 = get_house_lord(5, asc_sign, planet_data)
        l11 = get_house_lord(11, asc_sign, planet_data)
        
        is_ju_ruler = ("Jupiter" in [l2, l5, l11])
        if not is_ju_ruler: return False
        
        # Check rule 1
        lords_to_check = [l11, l2, get_house_lord(9, asc_sign, planet_data)]
        h_moon = get_h("Moon")
        if not h_moon: return False
        
        moon_kendras = [h_moon, ((h_moon+3-1)%12)+1, ((h_moon+6-1)%12)+1, ((h_moon+9-1)%12)+1]
        
        for lord in lords_to_check:
            if not lord: continue
            if get_h(lord) in moon_kendras:
                return True
        return False

    elif pattern_name == "benefics_in_kendras" or pattern_name == "benefics_kendra_quad":
        # Benefics occupy Kendras (1, 4, 7, 10).
        # Loose: Check if ANY kendra has benefic? No, usually implies Kendras are dominated by benefics or at least one is present and strong.
        # Chamara: "Benefics in Kendras" usually means Benefics occupy 1, 4, 7, 10 (or some of them) not ill-associated.
        # Let's check: Are there benefics in Kendras and NO malefics in Kendras? Or just Benefics presence.
        # Strict Chamara: TWO benefics in Lagna, 7th, 9th, 10th?
        # Let's implement: At least 2 Kendras occupied by Benefics.
        count = 0
        for k in KENDRA_HOUSES:
            if check_house_has(k, benefics): count += 1
        return count >= 2

    elif pattern_name == "benefics_in_upachaya":
        # Benefics in 3, 6, 10, 11
        # Vasumati: All benefics in Upachayas.
        bs = ["Jupiter", "Venus", "Mercury", "Moon"] # Moon is benefic if bright, check phase? Assume yes.
        for b in bs:
            if get_h(b) not in [3, 6, 10, 11]: return False
        return True

    elif pattern_name == "dhana_yoga_check":
        # Connection between lords of 1, 2, 5, 9, 11
        wealth_houses = [1, 2, 5, 9, 11]
        wealth_lords = set()
        for h in wealth_houses:
            l = get_house_lord(h, asc_sign, planet_data)
            if l: wealth_lords.add(l)
        
        # Check for conjunctions or mutual aspects between these lords
        # Simple conj check for now
        wl_list = list(wealth_lords)
        for i in range(len(wl_list)):
            for j in range(i+1, len(wl_list)):
                l1, l2 = wl_list[i], wl_list[j]
                if get_h(l1) == get_h(l2): return True # Conjunct
                # Mutual Aspect (7th)
                if abs(get_h(l1) - get_h(l2)) == 6: return True
        return False

    elif pattern_name == "dispositor_exalt":
        # Dispositor of Moon is Exalted? Or Dispositor of Lagna Lord?
        # Usually "Dispositor of X is Exalted". Param 'planet' needed in JSON.
        # Since this is a named pattern without params in JSON calls (usually), we assume Dispositor of Lagna Lord or Moon.
        # Kahala Yoga often involves Dispositor of Jupiter or Lord of 4th/9th.
        # Let's check Lagna Lord Dispositor
        l1 = get_house_lord(1, asc_sign, planet_data)
        if not l1: return False
        sign_l1 = get_sgn(l1)
        disp_l1 = SIGN_LORDS.get(sign_l1)
        if not disp_l1: return False
        sign_disp = get_sgn(disp_l1)
        return is_planet_exalted(disp_l1, sign_disp)

    elif pattern_name == "kalpadruma_chain":
        # Lagna Lord -> Dispositor -> Dispositor -> In Kendra/Trikona/Exalted
        l1 = get_house_lord(1, asc_sign, planet_data)
        if not l1: return False
        
        d1 = SIGN_LORDS.get(get_sgn(l1)) # Disp 1
        if not d1: return False
        d2 = SIGN_LORDS.get(get_sgn(d1)) # Disp 2
        if not d2: return False
        
        h_d2 = get_h(d2)
        s_d2 = get_sgn(d2)
        
        if h_d2 in KENDRA_HOUSES or h_d2 in TRIKONA_HOUSES or is_planet_exalted(d2, s_d2):
            return True
        return False

    elif pattern_name == "malefics_in_kendras":
        # Sarpa Yoga: Malefics in 3 or more Kendras
        count = 0
        for k in KENDRA_HOUSES:
            if check_house_has(k, malefics): count += 1
        return count >= 3

    elif pattern_name == "moon_navamsa_exalt":
        # Moon in Exalted Navamsa
        # Use simple exaltation check on d9_sign
        moon_data = planet_data.get("Moon", {})
        d9_sign = moon_data.get("d9_sign")
        if not d9_sign: return False
        return is_planet_exalted("Moon", d9_sign)

    elif pattern_name == "mridanga_complex":
        # Lagna Lord strong, etc.
        # Simplified: Lagna Lord Exalted or Own House
        l1 = get_house_lord(1, asc_sign, planet_data)
        if not l1: return False
        s_l1 = get_sgn(l1)
        return is_planet_exalted(l1, s_l1) or (SIGN_LORDS.get(s_l1) == l1)

    elif pattern_name == "neechabhanga_check":
        # Check if ANY debilitated planet has cancellation
        debilitated_planets = []
        for p in planet_data:
            if is_planet_debilitated(p, get_sgn(p)):
                debilitated_planets.append(p)
        
        if not debilitated_planets: return False # No neecha = No Yoga (Technically correct)
        
        for p in debilitated_planets:
            is_cancelled = False
            s_p = get_sgn(p)
            l_s = SIGN_LORDS.get(s_p) # Lord of debilitation sign
            
            exalt_sign = EXALTATION.get(p)
            l_exalt = SIGN_LORDS.get(exalt_sign) # Lord of exaltation sign
            
            # 1. Lord of Dep Sign in Kendra from Lagna/Moon
            for ref in ["Ascendant", "Moon"]:
                h_ref = 1 if ref == "Ascendant" else get_h("Moon")
                if not h_ref: continue
                
                h_ls = get_h(l_s)
                h_le = get_h(l_exalt)
                
                # Check Kendras from Ref
                kendras = [((h_ref + i) % 12) or 12 for i in [0, 3, 6, 9]]
                
                if h_ls in kendras or h_le in kendras:
                    is_cancelled = True
                    break
            
            # 2. Parivartana with Lord of Dep Sign
            # handled via generic logic? No, specific check.
            # If P is in Sign A (Dep), and Lord of A is in Sign of P (Not possible since P has no sign here), wait. P is a planet.
            # Parivartana: P is in L_S's sign (yes, definition of deb). L_S is in P's own sign?
            # Example: Sun in Libra (Deb). Lord Venus in Leo (Sun's sign).
            own_s = [] 
            for s, l in SIGN_LORDS.items(): 
                if l == p: own_s.append(s)
            
            if l_s and get_sgn(l_s) in own_s:
                 is_cancelled = True

            if is_cancelled: return True
            
        return False

    elif pattern_name.startswith("parivartana"):
        # Generic Parivartana check + filters
        pairs = []
        # Find all pairs exchanging signs
        planets = list(planet_data.keys())
        for i in range(len(planets)):
            for j in range(i+1, len(planets)):
                p1, p2 = planets[i], planets[j]
                s1, s2 = get_sgn(p1), get_sgn(p2)
                l1, l2 = SIGN_LORDS.get(s1), SIGN_LORDS.get(s2)
                if l1 == p2 and l2 == p1:
                    pairs.append((p1, p2))
        
        if not pairs: return False
        
        if pattern_name == "parivartana_3rd":
            # Khala Yoga: 3rd Lord with others
            l3 = get_house_lord(3, asc_sign, planet_data)
            for p1, p2 in pairs:
                if p1 == l3 or p2 == l3: return True
            return False
            
        elif pattern_name == "parivartana_dusthana":
            # Dainya Yoga: 6, 8, 12 Lords
            bad_lords = [get_house_lord(h, asc_sign, planet_data) for h in [6,8,12]]
            for p1, p2 in pairs:
                if p1 in bad_lords or p2 in bad_lords: return True
            return False
            
        elif pattern_name == "parivartana_kendra_trikona":
            # Maha Yoga: 1, 2, 4, 5, 7, 9, 10, 11 (Good houses)
            good_houses = [1, 2, 4, 5, 7, 9, 10, 11]
            good_lords = [get_house_lord(h, asc_sign, planet_data) for h in good_houses]
            # Must contain ONLY good lords
            for p1, p2 in pairs:
                if p1 in good_lords and p2 in good_lords: return True
            return False

        return False # Fallback

    elif pattern_name == "parvata_def":
        # 1. Benefics in Kendras
        # 2. 6th and 8th houses empty
        ben_in_kendra = False
        for k in KENDRA_HOUSES:
             if check_house_has(k, benefics): ben_in_kendra = True
        
        h6_empty = not [p for p in planet_data if get_h(p) == 6]
        h8_empty = not [p for p in planet_data if get_h(p) == 8]
        
        return ben_in_kendra and h6_empty and h8_empty

    elif pattern_name == "pushkala_def":
        # Lord of Moon Sign (L_M) with Lord of Lagna (L_1)
        # In Kendra or Friend's house? Simplified: Conjunct in Kendra
        moon_sign = get_sgn("Moon")
        l_moon = SIGN_LORDS.get(moon_sign)
        l_1 = get_house_lord(1, asc_sign, planet_data)
        
        if not l_moon or not l_1: return False
        
        h_lm = get_h(l_moon)
        h_l1 = get_h(l_1)
        
        if h_lm == h_l1 and h_lm in KENDRA_HOUSES: return True
        return False

    elif pattern_name == "raja_yoga_9_10":
        # 9th and 10th Lord Conjunct or Exchange
        l9 = get_house_lord(9, asc_sign, planet_data)
        l10 = get_house_lord(10, asc_sign, planet_data)
        if not l9 or not l10: return False
        
        # Conjunction
        if get_h(l9) == get_h(l10): return True
        
        # Exchange
        s9, s10 = get_sgn(l9), get_sgn(l10)
        return (SIGN_LORDS.get(s9) == l10 and SIGN_LORDS.get(s10) == l9)

    return False


def load_ruleset(filepath: str) -> Dict:
    """Load a ruleset JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate_yoga(ruleset: Dict, planet_data: Dict, whole_sign_houses: Dict, 
                  asc_sign: str) -> Dict[str, Any]:
    """Evaluate a yoga ruleset and return score and status"""
    
    # Evaluate all signals
    signal_results = {}
    signal_details = {}
    
    # If signals is missing, check for 'conditions' (new schema)
    if not ruleset.get("signals") and ruleset.get("conditions"):
        conditions = ruleset.get("conditions", [])
        all_passed = True
        details = {}
        
        for idx, cond in enumerate(conditions):
            is_handled = False
            
            # Check for named patterns
            if "condition" in cond:
                is_handled = True
                pattern_name = cond["condition"]
                result = evaluate_named_pattern(pattern_name, planet_data, whole_sign_houses, asc_sign)
                details[f"condition_{idx}"] = {"pattern": pattern_name, "result": result}
                if not result:
                    all_passed = False
                    
            # Check for structured conditions
            elif "house_from_moon" in cond:
                is_handled = True
                # Anapha, Sunapha, Durdhara style
                offset = cond.get("house_from_moon")
                should_have = cond.get("has_planets", True)
                excludes = cond.get("exclude_planets", [])
                
                moon_h = get_planet_house(planet_data, "Moon", asc_sign)
                if not moon_h: 
                    all_passed = False
                    continue
                    
                target_h = ((moon_h - 1 + offset - 1) % 12) + 1
                
                # Find planets in target house
                in_target = []
                for p_name in planet_data:
                    if p_name in excludes: continue
                    if get_planet_house(planet_data, p_name, asc_sign) == target_h:
                        in_target.append(p_name)
                
                if should_have and len(in_target) == 0:
                    all_passed = False
                elif not should_have and len(in_target) > 0:
                     all_passed = False

            elif "planet" in cond:
                is_handled = True
                p_name = cond.get("planet")
                
                # Check House Constraints
                if "house" in cond:
                    allowed_houses = cond.get("house") # list or single int
                    if not isinstance(allowed_houses, list): allowed_houses = [allowed_houses]
                    
                    actual_h = get_planet_house(planet_data, p_name, asc_sign)
                    if actual_h not in allowed_houses:
                        all_passed = False
                
                # Check Sign Constraints (Own/Exaltation)
                if "sign_type" in cond:
                    allowed_types = cond.get("sign_type") # list or str
                    if isinstance(allowed_types, str): allowed_types = [allowed_types]
                    
                    p_sign = get_planet_sign(planet_data, p_name)
                    is_valid_sign = False
                    
                    if "own" in allowed_types:
                        lord = SIGN_LORDS.get(p_sign)
                        if lord == p_name: is_valid_sign = True
                        
                    if "exaltation" in allowed_types:
                        if is_planet_exalted(p_name, p_sign): is_valid_sign = True
                    
                    if not is_valid_sign:
                        all_passed = False
                
                # Check Relationship (existing adapter)
                rel = cond.get("relationship")
                target = cond.get("target")
                
                if rel == "kendra_from_moon" or (rel == "kendra_from" and target == "Moon"):
                     is_kendra = evaluate_predicate("kendra_from", {"a": p_name, "b": "Moon"}, planet_data, whole_sign_houses, asc_sign)
                     if not is_kendra:
                         all_passed = False
                         
                elif rel == "6_8_12_from" and target:
                     # Check if planet is in 6/8/12 from target
                     h_target = get_planet_house(planet_data, target, asc_sign)
                     h_planet = get_planet_house(planet_data, p_name, asc_sign)
                     
                     if not h_target or not h_planet:
                         all_passed = False
                     else:
                         dist = ((h_planet - h_target) % 12) + 1
                         if dist not in [6, 8, 12]:
                             all_passed = False

                elif rel == "conjunction" and target:
                     # Check if planet is in same house as target
                     h_target = get_planet_house(planet_data, target, asc_sign)
                     h_planet = get_planet_house(planet_data, p_name, asc_sign)
                     
                     if not h_target or not h_planet or h_target != h_planet:
                         all_passed = False
                         
                # Nipuna uses 'conjunct_with'
                if "conjunct_with" in cond:
                     partner = cond.get("conjunct_with")
                     h_source = get_planet_house(planet_data, p_name, asc_sign)
                     
                     if isinstance(partner, list):
                         # If list, check if conjunct with ALL or ANY?
                         # Usually "conjunct with Mercury, Venus" implies both or any depending on context?
                         # For Kalanidhi "Jupiter conj Mercury/Venus", usually implies combined influence.
                         # Let's assume ANY for now unless specified
                         partners = partner
                         is_conjunct = False
                         for pt in partners:
                             h_pt = get_planet_house(planet_data, pt, asc_sign)
                             if h_source and h_pt and h_source == h_pt:
                                 is_conjunct = True
                                 break
                         if not is_conjunct:
                             all_passed = False
                     else:
                         # Single string
                         h_partner = get_planet_house(planet_data, partner, asc_sign)
                         if not h_source or not h_partner or h_source != h_partner:
                             all_passed = False

            elif "lord_of" in cond:
                is_handled = True
                house_num = cond.get("lord_of")
                lord_name = get_house_lord(house_num, asc_sign, planet_data)
                
                if not lord_name:
                    all_passed = False
                else:
                    # Check Sign Type Constraints
                    if "sign_type" in cond:
                         allowed_types = cond.get("sign_type")
                         if isinstance(allowed_types, str): allowed_types = [allowed_types]
                         
                         p_sign = get_planet_sign(planet_data, lord_name)
                         is_valid_sign = False
                         
                         if "exaltation" in allowed_types:
                             if is_planet_exalted(lord_name, p_sign): is_valid_sign = True
                         if "own" in allowed_types:
                             if SIGN_LORDS.get(p_sign) == lord_name: is_valid_sign = True
                             
                         if not is_valid_sign:
                             all_passed = False
                             
                    # Check Strength (Generic 'strong' check for now - Exaltation, Own, or Kendra)
                    if "strength" in cond and cond.get("strength") == "strong":
                        p_sign = get_planet_sign(planet_data, lord_name)
                        is_exalt = is_planet_exalted(lord_name, p_sign)
                        is_own = (SIGN_LORDS.get(p_sign) == lord_name)
                        h_lord = get_planet_house(planet_data, lord_name, asc_sign)
                        is_kendra = h_lord in [1, 4, 7, 10]
                        
                        if not (is_exalt or is_own or is_kendra):
                            all_passed = False

                    # Check House Placement
                    if "house" in cond:
                         allowed_houses = cond.get("house")
                         if not isinstance(allowed_houses, list): allowed_houses = [allowed_houses]
                         actual_h = get_planet_house(planet_data, lord_name, asc_sign)
                         if actual_h not in allowed_houses:
                             all_passed = False

            if not is_handled:
                # If we encounter a condition we don't understand, Fail it.
                all_passed = False
        
        score_percentage = 100.0 if all_passed else 0.0
        is_strong = all_passed
        is_active = all_passed
        status = "ACTIVE" if is_active else "INACTIVE"
        
        return {
            "id": ruleset.get("id"),
            "name": ruleset.get("name", ruleset.get("id")),
            "description": ruleset.get("description"),
            "score": round(score_percentage, 1),
            "status": status,
            "is_strong": is_strong,
            "is_active": is_active,
            "signal_results": {},
            "signal_details": details
        }

    # Original signal-based evaluation
    for signal in ruleset.get("signals", []):
        signal_id = signal.get("id")
        predicate = signal.get("predicate")
        params = signal.get("params", {})
        
        result = evaluate_predicate(predicate, params, planet_data, whole_sign_houses, asc_sign)
        signal_results[signal_id] = result
        
        # Store details for debugging
        signal_details[signal_id] = {
            "predicate": predicate,
            "params": params,
            "result": result
        }
    
    # Calculate weighted score (classic path)
    weights = ruleset.get("weights", {})
    total_weight = sum(weights.values())
    score = 0.0
    
    for signal_id, weight in weights.items():
        if signal_results.get(signal_id, False):
            score += weight
    
    # Normalize to percentage
    if total_weight > 0:
        score_percentage = (score / total_weight) * 100.0
    else:
        score_percentage = 0.0
    
    # Determine status
    strong_if = ruleset.get("strong_if", "")
    active_if = ruleset.get("active_if", "")
    
    # FIX: Default to False if no active_if is present, to avoid showing everything
    is_strong = evaluate_condition(strong_if, signal_results) if strong_if else False
    is_active = evaluate_condition(active_if, signal_results) if active_if else False
    
    status = "STRONG" if is_strong else ("ACTIVE" if is_active else "INACTIVE")
    
    return {
        "id": ruleset.get("id"),
        "name": ruleset.get("name", ruleset.get("id")),
        "description": ruleset.get("description"),
        "score": round(score_percentage, 1),
        "status": status,
        "is_strong": is_strong,
        "is_active": is_active,
        "signal_results": signal_results,
        "signal_details": signal_details
    }


def evaluate_all_yogas(ruleset_dir: str, planet_data: Dict, whole_sign_houses: Dict, 
                       asc_sign: str) -> List[Dict[str, Any]]:
    """Evaluate all yoga rulesets in a directory"""
    results = []
    
    if not os.path.exists(ruleset_dir):
        return results
    
    # Load all JSON files (skip YAML)
    for filename in os.listdir(ruleset_dir):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(ruleset_dir, filename)
        try:
            ruleset = load_ruleset(filepath)
            yoga_result = evaluate_yoga(ruleset, planet_data, whole_sign_houses, asc_sign)
            results.append(yoga_result)
        except Exception as e:
            print(f"Error evaluating {filename}: {e}")
            continue
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return results

