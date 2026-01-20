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
    
    if pattern_name == "hari_pattern":
        # Benefics in 2nd, 12th, 8th from 2nd Lord
        lord_2 = get_house_lord(2, asc_sign, planet_data)
        if not lord_2: return False
        
        house_l2 = get_planet_house(planet_data, lord_2, asc_sign)
        if not house_l2: return False
        
        # Check 2nd from 2nd Lord (House X + 2 - 1)
        # Check 8th from 2nd Lord
        # Check 12th from 2nd Lord
        targets = [
            ((house_l2 + 1) % 12) or 12, # 2nd
            ((house_l2 + 7) % 12) or 12, # 8th
            ((house_l2 + 11) % 12) or 12 # 12th
        ]
        benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
        
        for h_num in targets:
             # Check if house has benefic
             planets_in_house = [p for p in planet_data if get_planet_house(planet_data, p, asc_sign) == h_num]
             if not any(p in benefics for p in planets_in_house):
                 return False
        return True

    elif pattern_name == "gandharva_pattern":
        # 10th Lord in Kama Trikona (3, 7, 11), Sun strong (exalted/own), Moon in 9th
        lord_10 = get_house_lord(10, asc_sign, planet_data)
        house_l10 = get_planet_house(planet_data, lord_10, asc_sign)
        if not house_l10 or house_l10 not in [3, 7, 11]: return False
        
        sun_sign = get_planet_sign(planet_data, "Sun")
        if not sun_sign or (sun_sign != "Leo" and sun_sign != "Aries"): return False # Own or Exalted
        
        moon_house = get_planet_house(planet_data, "Moon", asc_sign)
        if moon_house != 9: return False
        return True

    elif pattern_name == "shiva_pattern":
        # 5th Lord in 9th, 9th Lord in 10th, 10th Lord in 5th
        l5 = get_house_lord(5, asc_sign, planet_data)
        l9 = get_house_lord(9, asc_sign, planet_data)
        l10 = get_house_lord(10, asc_sign, planet_data)
        
        return (get_planet_house(planet_data, l5, asc_sign) == 9 and
                get_planet_house(planet_data, l9, asc_sign) == 10 and
                get_planet_house(planet_data, l10, asc_sign) == 5)

    elif pattern_name == "vishnu_pattern":
        # 9th and 10th Lords in 2nd house
        l9 = get_house_lord(9, asc_sign, planet_data)
        l10 = get_house_lord(10, asc_sign, planet_data)
        return (get_planet_house(planet_data, l9, asc_sign) == 2 and
                get_planet_house(planet_data, l10, asc_sign) == 2)

    elif pattern_name == "brahma_pattern":
        # Jupiter, Venus, Mercury in Kendras from Lagna Lords
        # Simplified: Check if Ju, Ve, Me are in Kendras from Ascendant (Classic variation)
        # Proper: Kendras from Lagna Lord
        l1 = get_house_lord(1, asc_sign, planet_data)
        h_l1 = get_planet_house(planet_data, l1, asc_sign)
        if not h_l1: return False
        
        # Houses that are Kendra from Lagna Lord
        kendras_from_l1 = [
            h_l1, 
            ((h_l1 + 3 - 1) % 12) + 1,
            ((h_l1 + 6 - 1) % 12) + 1,
            ((h_l1 + 9 - 1) % 12) + 1
        ]
        
        for p in ["Jupiter", "Venus", "Mercury"]:
            h_p = get_planet_house(planet_data, p, asc_sign)
            if h_p not in kendras_from_l1:
                return False
        return True

    elif pattern_name == "indra_pattern":
         # Mars in 3rd from Moon, Saturn in 7th from Mars, Venus in 7th from Saturn
         h_moon = get_planet_house(planet_data, "Moon", asc_sign)
         h_mars = get_planet_house(planet_data, "Mars", asc_sign)
         h_sat = get_planet_house(planet_data, "Saturn", asc_sign)
         h_ven = get_planet_house(planet_data, "Venus", asc_sign)
         
         if not (h_moon and h_mars and h_sat and h_ven): return False
         
         # 3rd from Moon
         target_mars = ((h_moon + 2) % 12) or 12
         if h_mars != target_mars: return False
         
         # 7th from Mars
         target_sat = ((h_mars + 6) % 12) or 12
         if h_sat != target_sat: return False
         
         # 7th from Saturn
         target_ven = ((h_sat + 6) % 12) or 12
         if h_ven != target_ven: return False
         
         return True
    
    elif pattern_name == "matsya_pattern":
        # Malefics in Lagna/9th, Mix in 5th, Malefics in 4th/8th
        # Strict classical check is complex, simplified:
        # Benefics in 5th, Malefics in 1 & 9
        benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
        malefics = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]
        
        def check_house(h, type_list, mode="any"):
             ps = [p for p in planet_data if get_planet_house(planet_data, p, asc_sign) == h]
             if not ps: return False
             if mode == "all": return all(p in type_list for p in ps)
             return any(p in type_list for p in ps)

        return (check_house(1, malefics) and check_house(9, malefics) and check_house(5, benefics))

    elif pattern_name == "kurma_pattern":
        # Benefics in 5, 6, 7; Malefics in 1, 3, 11
        benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
        malefics = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]
        
        def has_type(h_list, type_list):
            for h in h_list:
                ps = [p for p in planet_data if get_planet_house(planet_data, p, asc_sign) == h]
                if not ps: return False
                if not any(p in type_list for p in ps): return False
            return True
            
        return has_type([5, 6, 7], benefics) and has_type([1, 3, 11], malefics)

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

