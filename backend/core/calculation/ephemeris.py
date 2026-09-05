import swisseph as swe
from typing import Dict, Any, Tuple
from .config import CalculationProfile, AyanamshaSystem, NodeSystem

# Set ephemeris path if needed, usually default is fine
# swe.set_ephe_path('path/to/ephe')

def get_ayanamsha(jd_ut: float, profile: CalculationProfile) -> Tuple[str, str, float]:
    """
    Returns (ayanamsha_system, swiss_mode, ayanamsha_value)
    """
    if profile.ayanamsha == AyanamshaSystem.LAHIRI_STANDARD:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        ay_val = swe.get_ayanamsa_ut(jd_ut)
        return ("LAHIRI_STANDARD", "SIDM_LAHIRI", ay_val)
    else:
        raise ValueError(f"Unsupported ayanamsha system: {profile.ayanamsha}")

def calculate_planet_positions(jd_ut: float, ay_deg: float, profile: CalculationProfile) -> Dict[str, Dict[str, Any]]:
    """
    Calculate planetary positions. Returns a dictionary of raw planet data.
    """
    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN
    }
    
    node_flag = swe.MEAN_NODE if profile.node == NodeSystem.MEAN else swe.TRUE_NODE
    
    results = {}
    
    # Standard planets
    for name, p_id in planets.items():
        # calculate tropical
        res_trop, _ = swe.calc_ut(jd_ut, p_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
        lon_trop = res_trop[0]
        lat = res_trop[1]
        dist = res_trop[2]
        speed = res_trop[3]
        
        lon_sid = (lon_trop - ay_deg) % 360.0
        
        results[name] = {
            "tropical": lon_trop,
            "sidereal": lon_sid,
            "latitude": lat,
            "distance": dist,
            "speed": speed,
            "retrograde": speed < 0
        }
        
    # Rahu
    res_node, _ = swe.calc_ut(jd_ut, node_flag, swe.FLG_SWIEPH | swe.FLG_SPEED)
    rahu_lon_trop = res_node[0]
    rahu_lat = res_node[1]
    rahu_dist = res_node[2]
    rahu_speed = res_node[3]
    rahu_lon_sid = (rahu_lon_trop - ay_deg) % 360.0
    
    results["Rahu"] = {
        "tropical": rahu_lon_trop,
        "sidereal": rahu_lon_sid,
        "latitude": rahu_lat,
        "distance": rahu_dist,
        "speed": rahu_speed,
        "retrograde": rahu_speed < 0
    }
    
    # Ketu (Exactly opposite Rahu)
    ketu_lon_trop = (rahu_lon_trop + 180.0) % 360.0
    ketu_lon_sid = (rahu_lon_sid + 180.0) % 360.0
    
    results["Ketu"] = {
        "tropical": ketu_lon_trop,
        "sidereal": ketu_lon_sid,
        "latitude": -rahu_lat, # Usually latitude is flipped for Ketu mathematically or just 0
        "distance": rahu_dist,
        "speed": rahu_speed,
        "retrograde": rahu_speed < 0
    }
    
    return results

def calculate_ascendant(jd_ut: float, lat: float, lon: float, ay_deg: float) -> Dict[str, Any]:
    """
    Calculate Ascendant and MC.
    """
    # swe.houses_ex(jd_ut, lat, lon, house_system)
    # 'W' is Whole Sign, but for Ascendant itself we just need Asc from any system, say Placidus 'P' or just 'W'
    res = swe.houses_ex(jd_ut, lat, lon, b'W')
    asc_trop = res[1][0] # Ascendant is first element of ascmc array
    mc_trop = res[1][1]
    
    asc_sid = (asc_trop - ay_deg) % 360.0
    
    return {
        "tropical": asc_trop,
        "sidereal": asc_sid
    }
