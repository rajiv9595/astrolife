"""
Calculations Module
Handles all chart and dasha calculations including:
- Planetary positions and calculations
- Houses and ascendant
- Nakshatra, Karana, and Vimshottari dasha
- D9 (Navamsa) chart calculations
- D10 (Dashamsha) chart calculations
"""

from typing import Dict, Any, List, Optional, Tuple
import swisseph as swe
import math
from datetime import datetime
import pytz

try:
    from core.calculation.pipeline import generate_chart_facts  # when backend is on sys.path (cwd=backend)
except ImportError:
    from backend.core.calculation.pipeline import generate_chart_facts  # when project root is cwd
# Phase 2 Varga Engine — pure derivation layer (must not be removed)
_VARGA_ENGINE_AVAILABLE = False
try:
    from core.calculation.varga import (
        calculate_varga_position as _calc_varga_pos,
        calculate_all_vargas as _calc_all_vargas,
        VargaMethod as _VargaMethod,
        VALID_VARGAS as _VALID_VARGAS,
    )
    _VARGA_ENGINE_AVAILABLE = True
except ImportError:
    try:
        from backend.core.calculation.varga import (
            calculate_varga_position as _calc_varga_pos,
            calculate_all_vargas as _calc_all_vargas,
            VargaMethod as _VargaMethod,
            VALID_VARGAS as _VALID_VARGAS,
        )
        _VARGA_ENGINE_AVAILABLE = True
    except Exception as _e2:
        _calc_varga_pos = None  # type: ignore
        _calc_all_vargas = None  # type: ignore
        _VargaMethod = None  # type: ignore
        _VALID_VARGAS = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
        _VARGA_ENGINE_AVAILABLE = False
        print(f"[Varga] Engine import failed (both paths), falling back to legacy: {_e2}")

# Import constants from main (will be moved here if needed)
# For now, we'll import them to avoid duplication

# ---------------------------
# CONSTANTS
# ---------------------------
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purvashada", "Uttarashada", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
                   "Jupiter", "Saturn", "Mercury"] * 3

VIMSHOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars",
                     "Rahu", "Jupiter", "Saturn", "Mercury"]

VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10,
    "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}

KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara",
    "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
]

NITHYA_YOGA_NAMES = [
    "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
]

PLANET_KEYS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
}

COMBUST_LIMITS = {
    "Mercury": 13.0,  # 13 degrees
    "Venus": 9.0,     # 9 degrees
    "Mars": 17.0,     # 17 degrees
    "Jupiter": 11.0,  # 11 degrees
    "Saturn": 15.0   # 15 degrees
}

# Exaltation signs mapping
EXALTATION_SIGNS = {
    "Sun": "Aries",        # Exalted in Aries, Debilitated in Libra
    "Moon": "Taurus",      # Exalted in Taurus, Debilitated in Scorpio
    "Mercury": "Virgo",    # Exalted in Virgo, Debilitated in Pisces
    "Venus": "Pisces",     # Exalted in Pisces, Debilitated in Virgo
    "Mars": "Capricorn",   # Exalted in Capricorn, Debilitated in Cancer
    "Jupiter": "Cancer",   # Exalted in Cancer, Debilitated in Capricorn
    "Saturn": "Libra",     # Exalted in Libra, Debilitated in Aries
    "Rahu": "Taurus",      # Generally exalted in Taurus/Gemini (varies by school)
    "Ketu": "Scorpio"      # Generally exalted in Scorpio/Sagittarius (varies by school)
}

# Debilitation signs mapping
# A planet is debilitated when it's in the sign opposite to its exaltation sign
DEBILITATION_SIGNS = {
    "Sun": "Libra",      # Exalted in Aries, Debilitated in Libra
    "Moon": "Scorpio",   # Exalted in Taurus, Debilitated in Scorpio
    "Mercury": "Pisces", # Exalted in Virgo, Debilitated in Pisces
    "Venus": "Virgo",    # Exalted in Pisces, Debilitated in Virgo
    "Mars": "Cancer",    # Exalted in Capricorn, Debilitated in Cancer
    "Jupiter": "Capricorn", # Exalted in Cancer, Debilitated in Capricorn
    "Saturn": "Aries",   # Exalted in Libra, Debilitated in Aries
    "Rahu": "Scorpio",   # Generally debilitated in Scorpio (varies by school)
    "Ketu": "Taurus"     # Generally debilitated in Taurus (varies by school)
}

# Sign lords mapping
SIGN_LORDS_MAP = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}


# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def normalize_deg(d):
    """Normalize degrees to 0-360 range."""
    return float(d) % 360.0


def jd_to_datetime_naive(jd):
    """Convert Julian Day to naive UTC datetime object."""
    year, month, day, hour_decimal = swe.revjul(jd, swe.GREG_CAL)
    hour = int(hour_decimal)
    min_decimal = (hour_decimal - hour) * 60.0
    minute = int(min_decimal)
    sec_decimal = (min_decimal - minute) * 60.0
    second = int(sec_decimal)
    
    if second >= 60: second = 59
    if minute >= 60: minute = 59
    if hour >= 24: hour = 23
    
    try:
        return datetime(year, month, day, hour, minute, second)
    except (ValueError, TypeError):
        return datetime(1900, 1, 1, 0, 0, 0)


def deg_to_sign_and_degree(lon_deg):
    """Convert longitude to sign and degree within sign."""
    lon = normalize_deg(lon_deg)
    sign_index = int(lon // 30)
    degree_in_sign = lon - sign_index * 30
    return SIGNS[sign_index], degree_in_sign


def is_debilitated(planet_name: str, sign: str) -> bool:
    """Check if a planet is debilitated in the given sign."""
    debil_sign = DEBILITATION_SIGNS.get(planet_name)
    return debil_sign == sign if debil_sign else False


def is_exalted(planet_name: str, sign: str) -> bool:
    """Check if a planet is exalted in the given sign."""
    exalt_sign = EXALTATION_SIGNS.get(planet_name)
    return exalt_sign == sign if exalt_sign else False


def to_utc_julian_day(year, month, day, hour, minute, second, tz_name):
    """Convert local datetime to UTC and return Julian Day."""
    tz = pytz.timezone(tz_name)
    dt_local = datetime(year, month, day, hour, minute, second)
    dt_local = tz.localize(dt_local)
    dt_utc = dt_local.astimezone(pytz.utc)
    ut_decimal = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut_decimal, swe.GREG_CAL)
    return jd, dt_utc


def ang_dist(lon1, lon2):
    """Calculate angular distance between two longitudes."""
    diff = abs(normalize_deg(lon1 - lon2))
    return min(diff, 360.0 - diff)


# ---------------------------
# NAKSHATRA & KARANA
# ---------------------------
def compute_nakshatra_pada(lon_sidereal):
    """Calculate nakshatra and pada from sidereal longitude."""
    lon = normalize_deg(lon_sidereal)
    nak_size = 360.0 / 27.0
    nak_index_float = lon / nak_size
    nak_index = int(math.floor(nak_index_float))
    fraction_into = nak_index_float - nak_index
    pada = int(fraction_into * 4) + 1
    lord = NAKSHATRA_LORDS[nak_index]
    name = NAKSHATRA_NAMES[nak_index]
    return {"nakshatra_index": nak_index, "nakshatra": name,
            "pada": pada, "fraction": fraction_into, "lord": lord}


def compute_karana(moon_lon, sun_lon):
    """
    Calculate Karana using classical 60 half-Tithi sequence (Phase 3 corrected).
    Fixes prohibited int(diff/6)%11. Delegates to canonical panchanga engine
    KARANA_SEQUENCE_60: Kimstughna(0), Bava..Vishti x8 (1-56), Shakuni(57), Chatushpada(58), Naga(59).
    Returns both 60-index and 11-unique index for backward compat.
    """
    try:
        from core.calculation.panchanga import KARANA_SEQUENCE_60, KARANA_NAMES_11, karana_at_index
        diff = normalize_deg(moon_lon - sun_lon)
        idx60 = int(diff // 6.0 + 1e-9) % 60
        name = KARANA_SEQUENCE_60[idx60]
        unique_idx = KARANA_NAMES_11.index(name) if name in KARANA_NAMES_11 else idx60 % 11
        return {
            "karana": name,
            "karana_index": unique_idx,
            "karana_index_60": idx60,
            "karana_sequence_60": KARANA_SEQUENCE_60[idx60],
            "moon_sun_diff": round(diff, 4)
        }
    except Exception:
        # Fallback legacy (should not happen)
        moon = normalize_deg(moon_lon)
        sun = normalize_deg(sun_lon)
        diff = moon - sun
        if diff < 0:
            diff += 360.0
        karana_index = int(diff / 6.0) % 11
        karana_name = KARANA_NAMES[karana_index]
        return {
            "karana": karana_name,
            "karana_index": karana_index,
            "moon_sun_diff": round(diff, 4)
        }


def compute_tithi(moon_lon: float, sun_lon: float) -> Dict[str, Any]:
    """
    Calculate Tithi (lunar day).
    Difference between Moon and Sun longitudes divided by 12 degrees.
    """
    diff = normalize_deg(moon_lon - sun_lon)
    tithi_val = diff / 12.0
    tithi_index = int(tithi_val)  # 0-29
    
    # Check if Shukla (Waxing) or Krishna (Waning)
    # 0-14: Shukla (waxing), 15-29: Krishna (waning)
    if tithi_index < 15:
        paksha = "Shukla Paksha"
        # 14 is Purnima
        day_index = tithi_index + 1
    else:
        paksha = "Krishna Paksha"
        # 29 is Amavasya
        day_index = tithi_index - 14 + 1
        
    name = TITHI_NAMES[tithi_index]
    
    # Calculate percentage remaining/passed
    fraction = tithi_val - tithi_index
    
    return {
        "index": tithi_index + 1,
        "name": name,
        "paksha": paksha,
        "fraction": fraction,
        "degrees_left": (1.0 - fraction) * 12.0
    }


def compute_nithya_yoga(moon_lon: float, sun_lon: float) -> Dict[str, Any]:
    """
    Calculate Nithya Yoga (Daily Yoga).
    Sum of Moon and Sun longitudes divided by 13°20' (13.3333 degrees).
    """
    total = normalize_deg(moon_lon + sun_lon)
    yoga_length = 360.0 / 27.0  # 13.3333...
    yoga_val = total / yoga_length
    yoga_index = int(yoga_val)  # 0-26
    
    name = NITHYA_YOGA_NAMES[yoga_index]
    fraction = yoga_val - yoga_index
    
    return {
        "index": yoga_index + 1,
        "name": name,
        "fraction": fraction
    }


def compute_sunrise_sunset(jd_ut: float, lat: float, lon: float, tz_name: str) -> Dict[str, Any]:
    """Calculate Sunrise and Sunset times."""
    # We want sunrise/sunset for the day of the chart
    # Back up to start of the day in local time?
    # Or just search backwards for previous sunrise and forward for next sunset?
    
    # Search for sunrise (CALC_RISE=1, CALC_SET=2)
    # We search starting from 24h before to find the sunrise that started this day
    # Actually, simplistic approach: search back 24h and forward 24h, find the one on the same calendar civil day.
    
    # Let's try to find sunrise closest to the input time but on the same day.
    # Actually most accurate:
    # 1. Get local date
    # 2. Get JD for 12:00 PM local time of that date
    # 3. Search for sunrise before and after noon?
    
    # Trying swisseph approach
    swe.set_topo(lon, lat, 0)
    
    # Find sunrise
    flags = swe.FLG_SWIEPH
    # Look for sunrise relative to current jd_ut.
    # If it's night, sunrise might be next morning or previous morning.
    # We want the sunrise relevant to the Panchang (Start of the day).
    # In Hindu system, Day starts at Sunrise.
    # But usually UI shows "Sunrise: 06:xx AM" which implies the morning of that calendar date.
    
    # convert jd_ut to local datetime to get the date
    dt = jd_to_datetime_naive(jd_ut) # this returns UTC datetime from JD
    # No, jd_to_datetime_naive returns the naive datetime corresponding to the JD. JD is UT based.
    # So dt is UTC.
    # We need local date.
    ut_dt = pytz.utc.localize(dt)
    tz = pytz.timezone(tz_name)
    local_dt = ut_dt.astimezone(tz)
    
    # Construct JD for Local Midnight (Start of the day)
    # We want to find the sunrise that happens on this specific calendar day.
    # Searching from midnight ensures we find the morning sunrise (around 6-7 AM).
    # If we search from Noon, we might find the NEXT sunrise (Tomorrow).
    midnight_local = local_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = midnight_local.astimezone(pytz.utc)
    
    # Get JD for midnight utc
    ut_dec = midnight_utc.hour + midnight_utc.minute/60.0 + midnight_utc.second/3600.0
    jd_start = swe.julday(midnight_utc.year, midnight_utc.month, midnight_utc.day, ut_dec, swe.GREG_CAL)
    
    # Search for sunrise backwards from noon (usually morning)
    # rise_trans signature in pyswisseph:
    # rise_trans(tjdut, body, rsmi, geopos, atpress, attemp, flags)
    # Returns: (int_status, (tjd_event, ...))
    try:
        # Search for sunrise from midnight
        res_rise = swe.rise_trans(jd_start, swe.SUN, swe.CALC_RISE, (lon, lat, 0), 0, 0, flags)
        jd_rise = res_rise[1][0]
        
        # Search for sunset from midnight? 
        # Usually sunset is afternoon. Searching from midnight will find today's sunset (e.g. 18:00)
        res_set = swe.rise_trans(jd_start, swe.SUN, swe.CALC_SET, (lon, lat, 0), 0, 0, flags)
        jd_set = res_set[1][0]
        
        # Convert JDs to local formatted strings
        rise_dt = jd_to_datetime_naive(jd_rise).replace(tzinfo=pytz.utc).astimezone(tz)
        set_dt = jd_to_datetime_naive(jd_set).replace(tzinfo=pytz.utc).astimezone(tz)
        
        return {
            "sunrise": rise_dt.strftime("%I:%M %p"),
            "sunset": set_dt.strftime("%I:%M %p"),
            "sunrise_jd": jd_rise,
            "sunset_jd": jd_set
        }
    except Exception as e:
        print(f"Error computing sunrise/sunset: {e}")
        return {"sunrise": "N/A", "sunset": "N/A"}

_active_tz = None

# ---------------------------
# VIMSHOTTARI DASHA
# ---------------------------
def jd_to_datetime(jd):
    """Convert Julian Day to datetime object."""
    # Use swisseph's built-in conversion which handles the 12-hour offset correctly.
    # revjul returns (year, month, day, hour_decimal)
    year, month, day, hour_decimal = swe.revjul(jd, swe.GREG_CAL)
    
    hour = int(hour_decimal)
    min_decimal = (hour_decimal - hour) * 60.0
    minute = int(min_decimal)
    sec_decimal = (min_decimal - minute) * 60.0
    second = int(sec_decimal)
    
    if second >= 60: second = 59
    if minute >= 60: minute = 59
    if hour >= 24: hour = 23
    
    try:
        dt = datetime(year, month, day, hour, minute, second)
    except (ValueError, TypeError):
        # Fallback
        return datetime(1900, 1, 1, 0, 0, 0)
        
    global _active_tz
    if _active_tz:
        try:
            # Check calling function via stack frame to avoid side-effects in astronomical functions like sunrise/sunset
            import inspect
            frame = inspect.currentframe()
            caller_name = frame.f_back.f_code.co_name
            if caller_name != "compute_sunrise_sunset" and caller_name != "compute_sunrise_sunset_internal":
                dt_utc = dt.replace(tzinfo=pytz.utc)
                return dt_utc.astimezone(pytz.timezone(_active_tz))
        except Exception:
            pass
            
    return dt


def jd_to_local_iso(jd, tz_name="UTC"):
    """Convert Julian Day to timezone-aware ISO string representation in local timezone."""
    year, month, day, hour_decimal = swe.revjul(jd, swe.GREG_CAL)
    hour = int(hour_decimal)
    min_decimal = (hour_decimal - hour) * 60.0
    minute = int(min_decimal)
    sec_decimal = (min_decimal - minute) * 60.0
    second = int(sec_decimal)
    
    # Handle edge boundary cases
    if second >= 60:
        second = 59
    if minute >= 60:
        minute = 59
    if hour >= 24:
        hour = 23
        
    try:
        dt_utc = datetime(year, month, day, hour, minute, second, tzinfo=pytz.utc)
    except (ValueError, TypeError):
        dt_utc = datetime(1900, 1, 1, 0, 0, 0, tzinfo=pytz.utc)
        
    try:
        global _active_tz
        # Use active birth timezone if tz_name is default "UTC"
        active_tz = tz_name if tz_name != "UTC" else (_active_tz or "UTC")
        tz = pytz.timezone(active_tz)
        dt_local = dt_utc.astimezone(tz)
        return dt_local.isoformat()
    except Exception:
        return dt_utc.isoformat()


def calculate_antar_dasha(mahadasha_lord, mahadasha_years, start_jd, days_in_year, tz_name="UTC"):
    """
    Calculate Antar Dasha (sub-periods) for a given Mahadasha.
    
    Formula: Antar Dasha duration = (Antar Lord years × Mahadasha years) / 120
    
    Args:
        mahadasha_lord: The lord of the Mahadasha
        mahadasha_years: Duration of the Mahadasha in years
        start_jd: Start Julian Day for this Mahadasha
        days_in_year: Days per year (365.2425)
        tz_name: Birth timezone
    
    Returns:
        List of Antar Dasha periods
    """
    seq = VIMSHOTTARI_ORDER
    start_idx = seq.index(mahadasha_lord)
    antar_dashas = []
    cursor = start_jd
    
    for i in range(len(seq)):
        idx = (start_idx + i) % len(seq)
        antar_lord = seq[idx]
        antar_years = (VIMSHOTTARI_YEARS[antar_lord] * mahadasha_years) / 120.0
        end_jd = cursor + antar_years * days_in_year
        
        antar_dashas.append({
            "lord": antar_lord,
            "start_jd": cursor,
            "end_jd": end_jd,
            "start_date": jd_to_local_iso(cursor, tz_name),
            "end_date": jd_to_local_iso(end_jd, tz_name),
            "years": round(antar_years, 6),
            "is_current": False,  # Will be determined based on current date
            "pratyantar_dashas": []
        })
        cursor = end_jd
    
    return antar_dashas


def calculate_sookshma_dasha(pratyantar_lord, pratyantar_years, start_jd, days_in_year, tz_name="UTC"):
    """
    Calculate Sookshma Dasha (sub-sub-sub-periods).
    Formula: Sookshma Dasha duration = (Sookshma Lord years × Pratyantar Dasha years) / 120
    """
    seq = VIMSHOTTARI_ORDER
    start_idx = seq.index(pratyantar_lord)
    sookshma_dashas = []
    cursor = start_jd
    
    for i in range(len(seq)):
        idx = (start_idx + i) % len(seq)
        sookshma_lord = seq[idx]
        sookshma_years = (VIMSHOTTARI_YEARS[sookshma_lord] * pratyantar_years) / 120.0
        end_jd = cursor + sookshma_years * days_in_year
        
        sookshma_dashas.append({
            "lord": sookshma_lord,
            "start_jd": cursor,
            "end_jd": end_jd,
            "start_date": jd_to_local_iso(cursor, tz_name),
            "end_date": jd_to_local_iso(end_jd, tz_name),
            "years": round(sookshma_years, 8),
            "is_current": False,
            "prana_dashas": []
        })
        cursor = end_jd
    
    return sookshma_dashas


def calculate_prana_dasha(sookshma_lord, sookshma_years, start_jd, days_in_year, tz_name="UTC"):
    """
    Calculate Prana Dasha (sub-sub-sub-sub-periods).
    Formula: Prana Dasha duration = (Prana Lord years × Sookshma Dasha years) / 120
    """
    seq = VIMSHOTTARI_ORDER
    start_idx = seq.index(sookshma_lord)
    prana_dashas = []
    cursor = start_jd
    
    for i in range(len(seq)):
        idx = (start_idx + i) % len(seq)
        prana_lord = seq[idx]
        prana_years = (VIMSHOTTARI_YEARS[prana_lord] * sookshma_years) / 120.0
        end_jd = cursor + prana_years * days_in_year
        
        prana_dashas.append({
            "lord": prana_lord,
            "start_jd": cursor,
            "end_jd": end_jd,
            "start_date": jd_to_local_iso(cursor, tz_name),
            "end_date": jd_to_local_iso(end_jd, tz_name),
            "years": round(prana_years, 10),
            "is_current": False
        })
        cursor = end_jd
    
    return prana_dashas


def calculate_pratyantar_dasha(antar_lord, antar_years, start_jd, days_in_year, tz_name="UTC"):
    """
    Calculate Pratyantar Dasha (sub-sub-periods) for a given Antar Dasha.
    Also recursively computes Sookshma Dashas for each Pratyantar period.
    
    Formula: Pratyantar Dasha duration = (Pratyantar Lord years × Antar Dasha years) / 120
    
    Args:
        antar_lord: The lord of the Antar Dasha
        antar_years: Duration of the Antar Dasha in years
        start_jd: Start Julian Day for this Antar Dasha
        days_in_year: Days per year (365.2425)
        tz_name: Birth timezone
    
    Returns:
        List of Pratyantar Dasha periods
    """
    seq = VIMSHOTTARI_ORDER
    start_idx = seq.index(antar_lord)
    pratyantar_dashas = []
    cursor = start_jd
    
    for i in range(len(seq)):
        idx = (start_idx + i) % len(seq)
        pratyantar_lord = seq[idx]
        pratyantar_years = (VIMSHOTTARI_YEARS[pratyantar_lord] * antar_years) / 120.0
        end_jd = cursor + pratyantar_years * days_in_year
        
        # Recursively calculate Sookshma Dashas for this Pratyantar period
        sookshma_dashas = calculate_sookshma_dasha(pratyantar_lord, pratyantar_years, cursor, days_in_year, tz_name)
        
        pratyantar_dashas.append({
            "lord": pratyantar_lord,
            "start_jd": cursor,
            "end_jd": end_jd,
            "start_date": jd_to_local_iso(cursor, tz_name),
            "end_date": jd_to_local_iso(end_jd, tz_name),
            "years": round(pratyantar_years, 6),
            "is_current": False,  # Will be determined based on current date
            "sookshma_dashas": sookshma_dashas
        })
        cursor = end_jd
    
    return pratyantar_dashas


def compute_vimshottari_timeline(jd_birth, moon_sidereal_lon, years_ahead=100):
    """
    PURE Vimshottari timeline — Phase 3: delegates to canonical Dasha engine.

    Legacy shim preserved for backward compatibility (return shape unchanged
    except is_current flags are always False — caller must use
    core.calculation.dasha.get_current_dasha(timeline, evaluation_datetime)
    with explicit evaluation_datetime to mark current. No datetime.now() inside.

    This function is now PURE and respects DashaCalculationProfile default
    (365.2425 days/year). Use core/calculation/dasha.calculate_vimshottari_timeline
    for ChartFacts-based entry with profile support.
    """
    if moon_sidereal_lon is None:
        return None
    try:
        from core.calculation.dasha import legacy_compute_vimshottari_timeline_shim
        return legacy_compute_vimshottari_timeline_shim(jd_birth, moon_sidereal_lon, years_ahead=years_ahead, tz_name="UTC")
    except ImportError:
        try:
            from backend.core.calculation.dasha import legacy_compute_vimshottari_timeline_shim
            return legacy_compute_vimshottari_timeline_shim(jd_birth, moon_sidereal_lon, years_ahead=years_ahead, tz_name="UTC")
        except Exception as e:
            # If shim unavailable, fallback minimal empty (should not happen)
            return {"nakshatra_of_moon": compute_nakshatra_pada(moon_sidereal_lon), "timeline": [], "total_years_calculated": 0, "dasha_cycle_years": 120, "error": str(e)}


# ---------------------------
# VARGA (D9) CALCULATIONS
# ---------------------------
def deg_in_sign(longitude: float) -> float:
    """Get degree within sign (0-30)."""
    return normalize_deg(longitude) % 30.0


def navamsa_sign_num(d1_sign: int, deg_in_that_sign: float) -> int:
    """Compute D9 sign number using proper movable/fixed/dual classification."""
    # pada = 0..8
    pada = int((deg_in_that_sign * 9.0) // 30.0)
    
    # Determine starting sign based on D1 sign classification
    if d1_sign in (1, 4, 7, 10):  # Movable (Aries, Cancer, Libra, Capricorn)
        start = d1_sign
    elif d1_sign in (2, 5, 8, 11):  # Fixed (Taurus, Leo, Scorpio, Aquarius)
        start = ((d1_sign + 8 - 1) % 12) + 1  # 9th from
    else:  # Dual (Gemini, Virgo, Sagittarius, Pisces)
        start = ((d1_sign + 4 - 1) % 12) + 1  # 5th from
    
    return ((start - 1 + pada) % 12) + 1


def whole_sign_houses_from(lagna_sign: int) -> List[Dict[str, Any]]:
    """Create whole-sign houses starting from lagna sign."""
    houses = []
    for i in range(12):
        sign_num = ((lagna_sign - 1 + i) % 12) + 1
        houses.append({
            "house": i + 1,
            "cusp_degree": None,  # varga uses whole-sign houses
            "sign": SIGNS[sign_num - 1],
            "sign_num": sign_num
        })
    return houses


def build_chart_d9(asc_sidereal_deg: float, d1_planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build D9 chart using proper navamsa calculation."""
    # 1) D9 ascendant sign
    asc_sign_d1 = int(asc_sidereal_deg // 30) + 1
    if asc_sign_d1 > 12:
        asc_sign_d1 = 12
    elif asc_sign_d1 < 1:
        asc_sign_d1 = 1
    
    asc_deg_in_sign = deg_in_sign(asc_sidereal_deg)
    d9_lagna_sign = navamsa_sign_num(asc_sign_d1, asc_deg_in_sign)
    
    d9_ascendant = {
        "degree": round(asc_sidereal_deg, 4),  # Keep same degree as D1
        "sign": SIGNS[d9_lagna_sign - 1],
        "sign_num": d9_lagna_sign
    }
    
    # 2) Planets: keep original longitudes; map to D9 sign
    d9_planets = []
    for p in d1_planets:
        lon_sid_used = p.get("lon_sidereal_flag") or p.get("lon_sidereal_manual")
        if lon_sid_used is None:
            continue  # Skip planets without longitude data
        
        lon = float(lon_sid_used)
        # Convert longitude to sign number (1-12)
        d1_sign = int(lon // 30) + 1
        if d1_sign > 12:
            d1_sign = 12
        elif d1_sign < 1:
            d1_sign = 1
        
        dins = deg_in_sign(lon)
        d9_sign_num = navamsa_sign_num(d1_sign, dins)
        
        d9_sign = SIGNS[d9_sign_num - 1]
        debilitated_d9 = is_debilitated(p["name"], d9_sign)
        exalted_d9 = is_exalted(p["name"], d9_sign)
        
        d9_planets.append({
            "name": p["name"],
            "longitude": lon,  # Unchanged from D1
            "sign": d9_sign,  # D9 sign
            "sign_num": d9_sign_num,
            "retro": bool(p.get("retrograde", False)),
            "combust": bool(p.get("combust", False)),
            "debilitated": debilitated_d9,
            "exalted": exalted_d9
        })
    
    # 3) Whole-sign houses
    houses = whole_sign_houses_from(d9_lagna_sign)
    houses_signs = [
        {"house": h["house"], "sign": h["sign"], "sign_num": h["sign_num"]}
        for h in houses
    ]
    
    return {
        "ascendant": d9_ascendant,
        "houses": houses,
        "houses_signs": houses_signs,
        "planets": d9_planets
    }


# VARGA (D10) CALCULATIONS
# ---------------------------
def dashamsha_sign_num(d1_sign: int, deg_in_that_sign: float) -> int:
    """
    Compute D10 sign number using proper odd/even classification.
    Each sign is divided into 10 parts (3 degrees each).
    
    For Odd Signs (1,3,5,7,9,11): Start from same sign (sequential)
    For Even Signs (2,4,6,8,10,12): Start from 9th sign (9th from the sign)
    """
    dashamsha = int(deg_in_that_sign / 3.0)  # 0-9
    if dashamsha >= 10:
        dashamsha = 9
    
    # Determine if sign is odd (1-indexed: 1,3,5,7,9,11)
    is_odd = d1_sign % 2 == 1
    
    if is_odd:
        # Odd signs: start from same sign, continue sequentially
        d10_sign_num = ((d1_sign - 1) + dashamsha) % 12
    else:
        # Even signs: start from 9th sign from the sign
        # 9th sign calculation: (sign_num + 8) % 12 (since we're 1-indexed)
        ninth_sign = ((d1_sign - 1) + 8) % 12
        d10_sign_num = (ninth_sign + dashamsha) % 12
    
    return d10_sign_num + 1  # Convert to 1-indexed (1-12)


def build_chart_d10(asc_sidereal_deg: float, d1_planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build D10 chart using proper dashamsha calculation."""
    # 1) D10 ascendant sign
    asc_sign_d1 = int(asc_sidereal_deg // 30) + 1
    if asc_sign_d1 > 12:
        asc_sign_d1 = 12
    elif asc_sign_d1 < 1:
        asc_sign_d1 = 1
    
    asc_deg_in_sign = deg_in_sign(asc_sidereal_deg)
    d10_lagna_sign = dashamsha_sign_num(asc_sign_d1, asc_deg_in_sign)
    
    d10_ascendant = {
        "degree": round(asc_sidereal_deg, 4),  # Keep same degree as D1
        "sign": SIGNS[d10_lagna_sign - 1],
        "sign_num": d10_lagna_sign
    }
    
    # 2) Planets: keep original longitudes; map to D10 sign
    d10_planets = []
    for p in d1_planets:
        lon_sid_used = p.get("lon_sidereal_flag") or p.get("lon_sidereal_manual")
        if lon_sid_used is None:
            continue  # Skip planets without longitude data
        
        lon = float(lon_sid_used)
        d1_sign = int(lon // 30) + 1
        if d1_sign > 12:
            d1_sign = 12
        elif d1_sign < 1:
            d1_sign = 1
        
        dins = deg_in_sign(lon)
        d10_sign_num = dashamsha_sign_num(d1_sign, dins)
        
        d10_sign = SIGNS[d10_sign_num - 1]
        debilitated_d10 = is_debilitated(p["name"], d10_sign)
        exalted_d10 = is_exalted(p["name"], d10_sign)
        
        d10_planets.append({
            "name": p["name"],
            "longitude": lon,  # Unchanged from D1
            "sign": d10_sign,  # D10 sign
            "sign_num": d10_sign_num,
            "retro": bool(p.get("retrograde", False)),
            "combust": bool(p.get("combust", False)),
            "debilitated": debilitated_d10,
            "exalted": exalted_d10
        })
    
    # 3) Whole-sign houses
    houses = whole_sign_houses_from(d10_lagna_sign)
    houses_signs = [
        {"house": h["house"], "sign": h["sign"], "sign_num": h["sign_num"]}
        for h in houses
    ]
    
    return {
        "ascendant": d10_ascendant,
        "houses": houses,
        "houses_signs": houses_signs,
        "planets": d10_planets
    }



# ---------------------------
# GENERAL VARGA GENERATION (D1 to D60)
# ---------------------------
def get_varga_sign(varga_num: int, d1_sign: int, deg_in_sign: float) -> int:
    """
    Calculate the sign number (1-12) for a given varga and planet position.
    d1_sign: 1-12
    deg_in_sign: 0-30
    """
    if varga_num == 1:
        return d1_sign
        
    elif varga_num == 2:  # Hora
        is_odd = d1_sign % 2 == 1
        if deg_in_sign < 15.0:
            return 5 if is_odd else 4  # Sun (Leo) or Moon (Cancer)
        else:
            return 4 if is_odd else 5  # Moon (Cancer) or Sun (Leo)
            
    elif varga_num == 3:  # Drekkana
        part = int(deg_in_sign // 10.0)  # 0, 1, 2
        if part == 0:
            return d1_sign
        elif part == 1:
            return ((d1_sign + 4 - 1) % 12) + 1  # 5th from
        else:
            return ((d1_sign + 8 - 1) % 12) + 1  # 9th from
            
    elif varga_num == 4:  # Chaturthamsa
        part = int(deg_in_sign // 7.5)  # 0, 1, 2, 3
        return ((d1_sign + (part * 3) - 1) % 12) + 1  # 1st, 4th, 7th, 10th from
        
    elif varga_num == 7:  # Saptamsa
        part = int(deg_in_sign / (30.0 / 7.0))  # 0..6
        start = d1_sign if d1_sign % 2 == 1 else ((d1_sign + 6 - 1) % 12) + 1
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 9:  # Navamsa
        return navamsa_sign_num(d1_sign, deg_in_sign)
        
    elif varga_num == 10:  # Dasamsa
        return dashamsha_sign_num(d1_sign, deg_in_sign)
        
    elif varga_num == 12:  # Dwadasamsa
        part = int(deg_in_sign // 2.5)  # 0..11
        return ((d1_sign - 1 + part) % 12) + 1
        
    elif varga_num == 16:  # Shodasamsa
        part = int(deg_in_sign / 1.875)  # 0..15
        is_movable = d1_sign in (1, 4, 7, 10)
        is_fixed = d1_sign in (2, 5, 8, 11)
        start = 1 if is_movable else (5 if is_fixed else 9)
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 20:  # Vimsamsa
        part = int(deg_in_sign / 1.5)  # 0..19
        is_movable = d1_sign in (1, 4, 7, 10)
        is_fixed = d1_sign in (2, 5, 8, 11)
        start = 1 if is_movable else (9 if is_fixed else 5)
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 24:  # Chaturvimsamsa (Siddhamsa)
        part = int(deg_in_sign / 1.25)  # 0..23
        start = 5 if d1_sign % 2 == 1 else 4  # Odd: Leo (5), Even: Cancer (4)
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 27:  # Saptavimsamsa (Nakshatramsa)
        part = int(deg_in_sign / (30.0 / 27.0))  # 0..26
        element = (d1_sign - 1) % 4  # 0=Fire, 1=Earth, 2=Air, 3=Water
        start = [1, 4, 7, 10][element]
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 30:  # Trimsamsa
        is_odd = d1_sign % 2 == 1
        d = deg_in_sign
        if is_odd:
            if d < 5.0: return 1  # Mars (Aries)
            elif d < 10.0: return 11  # Saturn (Aquarius)
            elif d < 18.0: return 9  # Jupiter (Sagittarius)
            elif d < 25.0: return 3  # Mercury (Gemini)
            else: return 2  # Venus (Taurus)
        else:
            if d < 5.0: return 2  # Venus (Taurus)
            elif d < 12.0: return 6  # Mercury (Virgo)
            elif d < 20.0: return 12  # Jupiter (Pisces)
            elif d < 25.0: return 10  # Saturn (Capricorn)
            else: return 8  # Mars (Scorpio)
            
    elif varga_num == 40:  # Khavedamsa
        part = int(deg_in_sign / 0.75)  # 0..39
        start = 1 if d1_sign % 2 == 1 else 7
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 45:  # Akshavedamsa
        part = int(deg_in_sign / (30.0 / 45.0))  # 0..44
        is_movable = d1_sign in (1, 4, 7, 10)
        is_fixed = d1_sign in (2, 5, 8, 11)
        start = 1 if is_movable else (5 if is_fixed else 9)
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 60:  # Shastiamsa
        part = int(deg_in_sign / 0.5)  # 0..59
        return ((d1_sign - 1 + part) % 12) + 1
        
    return d1_sign


def build_chart_varga(varga_num: int, asc_sidereal_deg: float, d1_planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build any divisional chart structure.

    Phase 2: delegates to pure Varga engine when available so that sign
    and varga degree are mathematically correct for the declared method
    (PARASHARI_CLASSICAL) and floating boundaries are handled consistently.
    Falls back to legacy get_varga_sign path if engine unavailable.
    """
    # --- Try Phase 2 pure engine path ---
    if _VARGA_ENGINE_AVAILABLE and _calc_varga_pos is not None:
        try:
            # Ascendant via pure engine
            asc_pos = _calc_varga_pos(asc_sidereal_deg, varga_num, "PARASHARI_CLASSICAL")
            lagna_sign = asc_pos.sign_num
            # Build enriched ascendant: keep legacy 'degree' for compat, add correct varga_degree
            ascendant = {
                "degree": round(asc_sidereal_deg, 4),  # legacy compat: D1 degree
                "varga_degree": round(float(asc_pos.degree), 6),
                "varga_longitude": round(float(asc_pos.longitude), 6),
                "sign": SIGNS[lagna_sign - 1],
                "sign_num": lagna_sign,
                "method": asc_pos.method,
                "segment_index": asc_pos.segment_index,
                "source_longitude": round(float(asc_pos.source_longitude), 6),
                "source_sign": asc_pos.source_sign,
                "source_degree": round(float(asc_pos.source_degree), 6),
            }
            planets = []
            varga_data: Dict[str, Any] = {}
            for p in d1_planets:
                lon_sid_used = p.get("lon_sidereal_flag") or p.get("lon_sidereal_manual")
                if lon_sid_used is None:
                    continue
                lon = float(lon_sid_used)
                pos = _calc_varga_pos(lon, varga_num, "PARASHARI_CLASSICAL")
                sign_name = pos.sign
                sign_num = pos.sign_num
                planets.append({
                    "name": p["name"],
                    "longitude": lon,  # D1 lon for backward compat
                    "varga_longitude": round(float(pos.longitude), 6),
                    "varga_degree": round(float(pos.degree), 6),
                    "sign": sign_name,
                    "sign_num": sign_num,
                    "retro": bool(p.get("retrograde", False)),
                    "combust": bool(p.get("combust", False)),
                    "debilitated": is_debilitated(p["name"], sign_name),
                    "exalted": is_exalted(p["name"], sign_name),
                    "method": pos.method,
                    "segment_index": pos.segment_index,
                    "source_longitude": round(float(pos.source_longitude), 6),
                    "source_degree": round(float(pos.source_degree), 6),
                })
                # Per-planet dict entry: preserve legacy keys, add enriched keys
                varga_data[p["name"]] = {
                    f"d{varga_num}_sign": sign_name,  # legacy
                    f"d{varga_num}_sign_num": sign_num,
                    f"d{varga_num}_longitude": lon,  # legacy = D1 lon
                    # New structured keys (additive, not breaking)
                    f"d{varga_num}_varga_degree": round(float(pos.degree), 6),
                    f"d{varga_num}_varga_longitude": round(float(pos.longitude), 6),
                    f"d{varga_num}_segment_index": pos.segment_index,
                    f"d{varga_num}_method": pos.method,
                    f"d{varga_num}_source_longitude": round(float(pos.source_longitude), 6),
                    f"d{varga_num}_source_degree": round(float(pos.source_degree), 6),
                    f"d{varga_num}_source_sign": pos.source_sign,
                    "retrograde": bool(p.get("retrograde", False)),
                    "combust": bool(p.get("combust", False)),
                    "debilitated": is_debilitated(p["name"], sign_name),
                    "exalted": is_exalted(p["name"], sign_name),
                }
            houses = whole_sign_houses_from(lagna_sign)
            houses_signs = [
                {"house": h["house"], "sign": h["sign"], "sign_num": h["sign_num"]}
                for h in houses
            ]
            # Also expose structured positions for new consumers
            varga_data["_ascendant"] = ascendant
            varga_data["_houses"] = houses
            varga_data["_houses_signs"] = houses_signs
            varga_data["planets"] = planets
            # Extra structured dump for Phase 2 consumers (does not break legacy)
            varga_data["_varga_positions"] = {
                p["name"]: _calc_varga_pos(
                    float(next(x for x in d1_planets if x["name"] == p["name"])["lon_sidereal_flag"] or next(x for x in d1_planets if x["name"] == p["name"])["lon_sidereal_manual"]),
                    varga_num, "PARASHARI_CLASSICAL"
                ).model_dump() for p in planets
            }
            # Asc detailed also
            varga_data["_ascendant_position"] = asc_pos.model_dump()
            return varga_data
        except Exception as e:
            print(f"[Varga] build_chart_varga pure-engine path failed for D{varga_num}: {e}, falling back to legacy")
            # fall through to legacy

    # --- Legacy fallback path (kept for compatibility / engine unavailable) ---
    asc_sign_d1 = int(asc_sidereal_deg // 30) + 1
    if asc_sign_d1 > 12: asc_sign_d1 = 12
    elif asc_sign_d1 < 1: asc_sign_d1 = 1
    
    asc_deg_in_sign = deg_in_sign(asc_sidereal_deg)
    lagna_sign = get_varga_sign(varga_num, asc_sign_d1, asc_deg_in_sign)
    
    ascendant = {
        "degree": round(asc_sidereal_deg, 4),
        "sign": SIGNS[lagna_sign - 1],
        "sign_num": lagna_sign
    }
    
    planets = []
    for p in d1_planets:
        lon_sid_used = p.get("lon_sidereal_flag") or p.get("lon_sidereal_manual")
        if lon_sid_used is None:
            continue
            
        lon = float(lon_sid_used)
        d1_sign = int(lon // 30) + 1
        if d1_sign > 12: d1_sign = 12
        elif d1_sign < 1: d1_sign = 1
        
        dins = deg_in_sign(lon)
        sign_num = get_varga_sign(varga_num, d1_sign, dins)
        sign_name = SIGNS[sign_num - 1]
        
        planets.append({
            "name": p["name"],
            "longitude": lon,
            "sign": sign_name,
            "sign_num": sign_num,
            "retro": bool(p.get("retrograde", False)),
            "combust": bool(p.get("combust", False)),
            "debilitated": is_debilitated(p["name"], sign_name),
            "exalted": is_exalted(p["name"], sign_name)
        })
        
    houses = whole_sign_houses_from(lagna_sign)
    houses_signs = [
        {"house": h["house"], "sign": h["sign"], "sign_num": h["sign_num"]}
        for h in houses
    ]
    
    varga_data = {}
    for p in planets:
        varga_data[p["name"]] = {
            f"d{varga_num}_sign": p["sign"],
            f"d{varga_num}_sign_num": p["sign_num"],
            f"d{varga_num}_longitude": p["longitude"],
            "retrograde": p["retro"],
            "combust": p["combust"],
            "debilitated": p["debilitated"],
            "exalted": p["exalted"]
        }
    
    varga_data["_ascendant"] = ascendant
    varga_data["_houses"] = houses
    varga_data["_houses_signs"] = houses_signs
    varga_data["planets"] = planets  # Expose list form too
    
    return varga_data


# ---------------------------
# SUNRISE, SUNSET, MAANDI & GULIKA CALCULATIONS
# ---------------------------
def compute_sunrise_sunset_internal(jd_start: float, lat: float, lon: float) -> Dict[str, float]:
    """Calculate Sunrise and Sunset JDs for the day beginning at jd_start."""
    swe.set_topo(lon, lat, 0)
    flags = swe.FLG_SWIEPH
    try:
        res_rise = swe.rise_trans(jd_start, swe.SUN, swe.CALC_RISE, (lon, lat, 0), 0, 0, flags)
        jd_rise = res_rise[1][0]
        res_set = swe.rise_trans(jd_start, swe.SUN, swe.CALC_SET, (lon, lat, 0), 0, 0, flags)
        jd_set = res_set[1][0]
        return {"sunrise_jd": jd_rise, "sunset_jd": jd_set}
    except Exception as e:
        print(f"Error in compute_sunrise_sunset_internal: {e}")
        return {"sunrise_jd": jd_start + 0.25, "sunset_jd": jd_start + 0.75}


def calculate_maandi_and_gulika_positions(jd_birth: float, lat: float, lon: float, tz_name: str, ay: float) -> Dict[str, Dict[str, Any]]:
    """
    Calculate the positions of Maandi and Gulika.
    Based on standard division of dinamana/ratrimana into 8 equal parts.
    """
    dt_utc = jd_to_datetime_naive(jd_birth)
    
    # Get local birth date timezone aware
    tz = pytz.timezone(tz_name)
    ut_dt = pytz.utc.localize(dt_utc)
    local_dt = ut_dt.astimezone(tz)
    
    # Local Midnight start
    midnight_local = local_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = midnight_local.astimezone(pytz.utc)
    ut_dec = midnight_utc.hour + midnight_utc.minute/60.0 + midnight_utc.second/3600.0
    jd_start = swe.julday(midnight_utc.year, midnight_utc.month, midnight_utc.day, ut_dec, swe.GREG_CAL)
    
    today_sun = compute_sunrise_sunset_internal(jd_start, lat, lon)
    sunrise_jd = today_sun["sunrise_jd"]
    sunset_jd = today_sun["sunset_jd"]
    
    is_day = sunrise_jd <= jd_birth < sunset_jd
    cal_weekday = local_dt.weekday()  # 0=Monday, 6=Sunday
    
    # If birth is before sunrise, the weekday is the previous day
    if jd_birth < sunrise_jd:
        vedic_weekday = (cal_weekday - 1) % 7
    else:
        vedic_weekday = cal_weekday
        
    if is_day:
        duration = sunset_jd - sunrise_jd
        start_jd = sunrise_jd
        day_parts = {
            0: 6,  # Monday -> 6th part
            1: 5,  # Tuesday -> 5th part
            2: 4,  # Wednesday -> 4th part
            3: 3,  # Thursday -> 3rd part
            4: 2,  # Friday -> 2nd part
            5: 1,  # Saturday -> 1st part
            6: 7   # Sunday -> 7th part
        }
        part_idx = day_parts[vedic_weekday]
    else:
        # Night birth
        if jd_birth >= sunset_jd:
            start_jd = sunset_jd
            tomorrow_start_jd = jd_start + 1.0
            tomorrow_sun = compute_sunrise_sunset_internal(tomorrow_start_jd, lat, lon)
            end_jd = tomorrow_sun["sunrise_jd"]
        else:
            end_jd = sunrise_jd
            yesterday_start_jd = jd_start - 1.0
            yesterday_sun = compute_sunrise_sunset_internal(yesterday_start_jd, lat, lon)
            start_jd = yesterday_sun["sunset_jd"]
            
        duration = end_jd - start_jd
        night_parts = {
            0: 2,  # Monday -> 2nd part
            1: 1,  # Tuesday -> 1st part
            2: 7,  # Wednesday -> 7th part
            3: 6,  # Thursday -> 6th part
            4: 5,  # Friday -> 5th part
            5: 4,  # Saturday -> 4th part
            6: 3   # Sunday -> 3rd part
        }
        part_idx = night_parts[vedic_weekday]
        
    # Gulika is at the beginning of the Saturn portion
    # Maandi is at the middle of the Saturn portion
    gulika_jd = start_jd + (part_idx - 1) * (duration / 8.0)
    maandi_jd = start_jd + (part_idx - 0.5) * (duration / 8.0)
    
    def get_ascendant_at_jd(target_jd):
        cusps, ascmc = swe.houses(target_jd, lat, lon, b'P')
        asc_trop = float(ascmc[0])
        ay_target = swe.get_ayanamsa_ut(target_jd)
        asc_sid = normalize_deg(asc_trop - ay_target)
        sign, deg = deg_to_sign_and_degree(asc_sid)
        return asc_sid, sign, deg
        
    gulika_sid, gulika_sign, gulika_deg = get_ascendant_at_jd(gulika_jd)
    maandi_sid, maandi_sign, maandi_deg = get_ascendant_at_jd(maandi_jd)
    
    return {
        "Gulika": {
            "lon_tropical": gulika_sid + ay,
            "speed_lon": 0.0,
            "retrograde": False,
            "combust": False,
            "lon_sidereal_manual": gulika_sid,
            "lon_sidereal_flag": gulika_sid,
            "chosen_sidereal": gulika_sid,
            "sign_manual": gulika_sign,
            "degree_in_sign_manual": gulika_deg,
            "sign_flag": gulika_sign,
            "degree_in_sign_flag": gulika_deg,
            "debilitated": False,
            "exalted": False
        },
        "Maandi": {
            "lon_tropical": maandi_sid + ay,
            "speed_lon": 0.0,
            "retrograde": False,
            "combust": False,
            "lon_sidereal_manual": maandi_sid,
            "lon_sidereal_flag": maandi_sid,
            "chosen_sidereal": maandi_sid,
            "sign_manual": maandi_sign,
            "degree_in_sign_manual": maandi_deg,
            "sign_flag": maandi_sign,
            "degree_in_sign_flag": maandi_deg,
            "debilitated": False,
            "exalted": False
        }
    }


# ---------------------------
# GRAHA ASPECTS (DRISHTI) CALCULATIONS
# ---------------------------
def calculate_aspects_data(planets: Dict[str, Any], asc_sign: str) -> Dict[str, Any]:
    """
    Calculate Graha aspects (Drishti) for each planet and house.
    """
    planet_houses = {}
    house_planets = {i: [] for i in range(1, 13)}
    
    try:
        asc_idx = SIGNS.index(asc_sign)
    except ValueError:
        return {"planet_aspects": {}, "house_aspects": {}, "planet_aspected_by": {}}
        
    for p_name, p_data in planets.items():
        if p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Maandi", "Gulika"]:
            sign = p_data.get("sign_manual") or p_data.get("sign") or p_data.get("sign_flag")
            if sign:
                try:
                    sign_idx = SIGNS.index(sign)
                    house = ((sign_idx - asc_idx) % 12) + 1
                    planet_houses[p_name] = house
                    house_planets[house].append(p_name)
                except ValueError:
                    pass

    planet_aspects = {}
    house_aspects = {i: [] for i in range(1, 13)}
    planet_aspected_by = {p: [] for p in planet_houses}

    for p_name, house in planet_houses.items():
        # Standard aspect is 7th house
        aspected_houses = [((house + 7 - 1) % 12) + 1]
        
        # Special aspects
        if p_name == "Mars":
            aspected_houses.extend([((house + 4 - 1) % 12) + 1, ((house + 8 - 1) % 12) + 1])
        elif p_name in ["Jupiter", "Rahu", "Ketu"]:
            aspected_houses.extend([((house + 5 - 1) % 12) + 1, ((house + 9 - 1) % 12) + 1])
        elif p_name == "Saturn":
            aspected_houses.extend([((house + 3 - 1) % 12) + 1, ((house + 10 - 1) % 12) + 1])
            
        aspected_houses = sorted(list(set(aspected_houses)))
        
        aspected_planets = []
        for h in aspected_houses:
            aspected_planets.extend(house_planets[h])
            if p_name not in house_aspects[h]:
                house_aspects[h].append(p_name)
                
        planet_aspects[p_name] = {
            "house": house,
            "aspected_houses": aspected_houses,
            "aspected_planets": aspected_planets
        }
        
        for ap in aspected_planets:
            if ap != p_name:
                planet_aspected_by[ap].append(p_name)
                
    return {
        "planet_aspects": planet_aspects,
        "house_aspects": house_aspects,
        "planet_aspected_by": planet_aspected_by
    }


# ---------------------------
# PLANET CALCULATIONS
# ---------------------------

def calculate_planets(jd_ut: float, ay: float, planets: List[str], topo_lon: float = 0.0, 
                      topo_lat: float = 0.0, topo_alt: float = 0.0) -> Dict[str, Any]:
    """Calculate positions for all requested planets."""
    swe.set_topo(topo_lon, topo_lat, float(topo_alt))
    
    FLG_SPEED = getattr(swe, "SEFLG_SPEED", 256)
    FLG_SIDEREAL = getattr(swe, "SEFLG_SIDEREAL", 65536)
    flags_tropical = FLG_SPEED
    flags_sidereal = FLG_SPEED | FLG_SIDEREAL
    
    res_planets: Dict[str, Any] = {}
    
    # Get Sun longitude for combust calculation (calculate early)
    sun_pos, _ = swe.calc_ut(jd_ut, swe.SUN, flags_tropical)
    sun_lon_tropical = float(sun_pos[0])
    sun_lon_sidereal = normalize_deg(sun_lon_tropical - ay)
    
    for p in planets:
        if p == "Rahu":
            try:
                out = swe.calc_ut(jd_ut, PLANET_KEYS["Rahu"], flags_tropical)
                rahu_trop_lon = float(out[0][0])
                rahu_speed = float(out[0][3]) if len(out[0]) > 3 else None
                lon_sid_manual = normalize_deg(rahu_trop_lon - ay)

                try:
                    out_sid = swe.calc_ut(jd_ut, PLANET_KEYS["Rahu"], flags_sidereal)
                    rahu_sid_flag = float(out_sid[0][0])
                except Exception:
                    rahu_sid_flag = None

                sign_m, deg_m = deg_to_sign_and_degree(lon_sid_manual)
                sign_f, deg_f = (deg_to_sign_and_degree(rahu_sid_flag)
                                 if rahu_sid_flag is not None else (None, None))

                debilitated_rahu = is_debilitated("Rahu", sign_m) if sign_m else False
                exalted_rahu = is_exalted("Rahu", sign_m) if sign_m else False

                res_planets["Rahu"] = {
                    "lon_tropical": rahu_trop_lon,
                    "lon_sidereal_manual": lon_sid_manual,
                    "sign_manual": sign_m,
                    "degree_in_sign_manual": deg_m,
                    "lon_sidereal_flag": rahu_sid_flag,
                    "sign_flag": sign_f,
                    "degree_in_sign_flag": deg_f,
                    "speed_lon": rahu_speed,
                    "retrograde": True,  # Always retrograde
                    "debilitated": debilitated_rahu,
                    "exalted": exalted_rahu,
                    "combust": False  # Rahu/Ketu don't have combust
                }
            except Exception as e:
                res_planets["Rahu"] = {"error": str(e)}
            continue

        if p == "Ketu":
            try:
                rahu = res_planets.get("Rahu")
                if not rahu:
                    rah = swe.calc_ut(jd_ut, PLANET_KEYS["Rahu"], flags_tropical)
                    rahu_trop_lon = float(rah[0][0])
                else:
                    rahu_trop_lon = rahu["lon_tropical"]

                ketu_trop_lon = normalize_deg(rahu_trop_lon + 180.0)
                ketu_sid_manual = normalize_deg(ketu_trop_lon - ay)

                try:
                    rah_sid = swe.calc_ut(jd_ut, PLANET_KEYS["Rahu"], flags_sidereal)
                    rah_sid_lon = float(rah_sid[0][0])
                    ketu_sid_flag = normalize_deg(rah_sid_lon + 180.0)
                except Exception:
                    ketu_sid_flag = None

                sign_m, deg_m = deg_to_sign_and_degree(ketu_sid_manual)
                sign_f, deg_f = (deg_to_sign_and_degree(ketu_sid_flag)
                                 if ketu_sid_flag is not None else (None, None))

                debilitated_ketu = is_debilitated("Ketu", sign_m) if sign_m else False
                exalted_ketu = is_exalted("Ketu", sign_m) if sign_m else False

                res_planets["Ketu"] = {
                    "lon_tropical": ketu_trop_lon,
                    "lon_sidereal_manual": ketu_sid_manual,
                    "sign_manual": sign_m,
                    "degree_in_sign_manual": deg_m,
                    "lon_sidereal_flag": ketu_sid_flag,
                    "sign_flag": sign_f,
                    "degree_in_sign_flag": deg_f,
                    "retrograde": True,  # Always retrograde
                    "combust": False,  # Rahu/Ketu don't have combust
                    "debilitated": debilitated_ketu,
                    "exalted": exalted_ketu
                }
            except Exception as e:
                res_planets["Ketu"] = {"error": str(e)}
            continue

        # Normal planets
        pid = PLANET_KEYS[p]
        out_t = swe.calc_ut(jd_ut, pid, flags_tropical)
        lon_trop = float(out_t[0][0])
        speed = float(out_t[0][3]) if len(out_t[0]) > 3 else None
        retro = (speed is not None and speed < 0.0)

        try:
            out_sid = swe.calc_ut(jd_ut, pid, flags_sidereal)
            lon_sid_flag = float(out_sid[0][0])
        except Exception:
            lon_sid_flag = None

        lon_sid_manual = normalize_deg(lon_trop - ay)
        chosen_sid = lon_sid_flag if lon_sid_flag is not None else lon_sid_manual

        sign_m, deg_m = deg_to_sign_and_degree(lon_sid_manual)
        sign_f, deg_f = (deg_to_sign_and_degree(lon_sid_flag)
                         if lon_sid_flag else (None, None))

        # Calculate combust (planets too close to Sun) - use Sun already calculated
        combust = False
        if p != "Sun" and p != "Moon" and p in COMBUST_LIMITS:
            planet_sid_lon = lon_sid_manual
            dist = ang_dist(planet_sid_lon, sun_lon_sidereal)
            combust = dist <= COMBUST_LIMITS[p]

        # Check debilitation and exaltation for D1 sign
        debilitated_d1 = is_debilitated(p, sign_m) if sign_m else False
        exalted_d1 = is_exalted(p, sign_m) if sign_m else False
        
        res_planets[p] = {
            "lon_tropical": lon_trop,
            "speed_lon": speed,
            "retrograde": retro,
            "combust": combust,
            "lon_sidereal_manual": lon_sid_manual,
            "lon_sidereal_flag": lon_sid_flag,
            "chosen_sidereal": chosen_sid,
            "sign_manual": sign_m,
            "degree_in_sign_manual": deg_m,
            "sign_flag": sign_f,
            "degree_in_sign_flag": deg_f,
            "debilitated": debilitated_d1,  # D1 debilitation status
            "exalted": exalted_d1  # D1 exaltation status
        }

    return res_planets


def calculate_houses(jd_ut: float, lat: float, lon: float, ay: float) -> Dict[str, Any]:
    """Calculate houses and ascendant."""
    cusps, ascmc = swe.houses(jd_ut, lat, lon, b'P')
    asc_tropical = float(ascmc[0])
    asc_sidereal = normalize_deg(asc_tropical - ay)
    asc_sign, asc_deg = deg_to_sign_and_degree(asc_sidereal)

    first_house_start = math.floor(asc_sidereal / 30.0) * 30.0
    whole_sign_houses = {}
    for i in range(12):
        start_deg = normalize_deg(first_house_start + i * 30.0)
        end_deg = normalize_deg(start_deg + 30.0)
        sign_name = SIGNS[int(start_deg // 30) % 12]
        whole_sign_houses[f"house_{i+1}"] = {
            "start_deg_sidereal": start_deg,
            "end_deg_sidereal": end_deg,
            "sign": sign_name
        }

    return {
        "ascendant": {
            "tropical": asc_tropical,
            "sidereal": asc_sidereal,
            "sign": asc_sign,
            "deg_in_sign": asc_deg
        },
        "whole_sign_houses": whole_sign_houses,
        "asc_sidereal": asc_sidereal  # For use in D9 calculations
    }


# ---------------------------
# MAIN CHART CALCULATION FUNCTION
# ---------------------------
def compute_chart(year: int, month: int, day: int, hour: int, minute: int, second: int,
                  tz: str, lat: float, lon: float, planets: Optional[List[str]] = None,
                  topo_alt: float = 0.0) -> Dict[str, Any]:
    """
    Compute complete astrological chart including planets, houses, dasha, etc.
    """
    global _active_tz
    _active_tz = tz
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    
    # --- PHASE 1: CANONICAL TRUTH LAYER ---
    facts = generate_chart_facts(
        year=year, month=month, day=day,
        hour=hour, minute=minute, second=second,
        lat=lat, lon=lon, tz_name=tz
    )
    
    # 1. Map Time & Ayanamsha
    jd_ut = facts.time.julian_day
    dt_utc = datetime.fromisoformat(facts.time.utc_datetime)
    ay = facts.ayanamsha.value
    swe.set_topo(lon, lat, float(topo_alt))
    
    # Default planets list
    planets = planets or [
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Rahu", "Ketu"
    ]
    
    # 2. Call legacy planet calculator to retain derived attributes (combust, debilitated, etc.)
    res_planets = calculate_planets(jd_ut, ay, planets, lon, lat, topo_alt)
    
    # 3. Overwrite fundamental values with canonical facts
    for p_name, p_data in facts.planets.items():
        if p_name in res_planets:
            res_planets[p_name]["lon_tropical"] = p_data.longitude.tropical
            res_planets[p_name]["lon_sidereal_manual"] = p_data.longitude.sidereal
            res_planets[p_name]["lon_sidereal_flag"] = p_data.longitude.sidereal
            res_planets[p_name]["sign_manual"] = p_data.sign.name
            res_planets[p_name]["sign_flag"] = p_data.sign.name
            res_planets[p_name]["degree_in_sign_manual"] = p_data.sign.degree
            res_planets[p_name]["degree_in_sign_flag"] = p_data.sign.degree
            res_planets[p_name]["speed_lon"] = p_data.speed
            res_planets[p_name]["retrograde"] = p_data.retrograde
            
    # Calculate Maandi and Gulika positions
    try:
        mg_positions = calculate_maandi_and_gulika_positions(jd_ut, lat, lon, tz, ay)
        res_planets["Gulika"] = mg_positions["Gulika"]
        res_planets["Maandi"] = mg_positions["Maandi"]
    except Exception as e:
        print(f"Error calculating Maandi and Gulika: {e}")
        
    # 4. Map Canonical Ascendant & Houses
    # Calculate legacy houses_data for derived aspects, but overwrite root facts
    houses_data = calculate_houses(jd_ut, lat, lon, ay)
    houses_data["asc_sidereal"] = facts.ascendant.longitude.sidereal
    houses_data["ascendant"]["tropical"] = facts.ascendant.longitude.tropical
    houses_data["ascendant"]["sidereal"] = facts.ascendant.longitude.sidereal
    houses_data["ascendant"]["sign"] = facts.ascendant.sign.name
    houses_data["ascendant"]["degree"] = facts.ascendant.sign.degree
    
    for house_num, house_obj in facts.houses.items():
        # Legacy format uses "house_1", "house_2", etc. as dict keys
        legacy_key = f"house_{house_num}"
        if legacy_key in houses_data["whole_sign_houses"]:
            houses_data["whole_sign_houses"][legacy_key]["sign"] = house_obj.sign.name
                
    asc_sidereal = houses_data["asc_sidereal"]
    asc_sign = houses_data["ascendant"]["sign"]
    
    # Calculate Nakshatra, Dasha, Karana
    moon_sid = res_planets.get("Moon", {}).get("lon_sidereal_manual")
    sun_sid = res_planets.get("Sun", {}).get("lon_sidereal_manual")
    
    nakshatra = compute_nakshatra_pada(moon_sid) if moon_sid else None
    dasha = compute_vimshottari_timeline(jd_ut, moon_sid) if moon_sid else None
    
    karana_data = None
    tithi_data = None
    yoga_data = None
    
    if moon_sid is not None and sun_sid is not None:
        karana_data = compute_karana(moon_sid, sun_sid)
        tithi_data = compute_tithi(moon_sid, sun_sid)
        yoga_data = compute_nithya_yoga(moon_sid, sun_sid)
        
    # Calculate Sunrise/Sunset
    sun_data = compute_sunrise_sunset(jd_ut, lat, lon, tz)

    # Get Moon sign
    moon_sign = None
    if moon_sid is not None:
        moon_sign, moon_deg = deg_to_sign_and_degree(moon_sid)

    # Prepare list form of planets for varga calculations (legacy path)
    d1_planets_list = []
    for name, pdata in res_planets.items():
        lon_sid_used = pdata.get("lon_sidereal_flag") or pdata.get("lon_sidereal_manual")
        if lon_sid_used is not None:
            d1_planets_list.append({
                "name": name,
                "lon_sidereal_flag": pdata.get("lon_sidereal_flag"),
                "lon_sidereal_manual": pdata.get("lon_sidereal_manual"),
                "retrograde": pdata.get("retrograde", False),
                "combust": pdata.get("combust", False)
            })

    # Calculate all 16 divisional charts — Phase 2 pure derivation from ChartFacts
    vargas_list = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
    vargas = {}
    _varga_structured = None  # enriched structured dump from pure engine

    if _VARGA_ENGINE_AVAILABLE and _calc_all_vargas is not None:
        try:
            # Primary source: ChartFacts (canonical sidereal longitudes only)
            _varga_structured = _calc_all_vargas(facts)
            # Transform structured result into legacy vargas dict shape
            # _varga_structured = {"planets": {planet: {D1:Pos, D9:Pos,...}}, "ascendant": {D1:Pos,...}}
            for v_num in vargas_list:
                dkey_lower = f"d{v_num}"
                dkey_upper = f"D{v_num}"
                # Ascendant position for this varga (from facts)
                asc_pos = _varga_structured["ascendant"][dkey_upper]
                lagna_sign = asc_pos.sign_num
                # Legacy ascendant: preserve 'degree' for compat, add varga_degree
                ascendant_entry = {
                    "degree": round(asc_sidereal, 4),
                    "varga_degree": round(float(asc_pos.degree), 6),
                    "varga_longitude": round(float(asc_pos.longitude), 6),
                    "sign": asc_pos.sign,
                    "sign_num": lagna_sign,
                    "method": asc_pos.method,
                    "segment_index": asc_pos.segment_index,
                    "source_longitude": round(float(asc_pos.source_longitude), 6),
                    "source_sign": asc_pos.source_sign,
                    "source_degree": round(float(asc_pos.source_degree), 6),
                }
                # Houses from varga lagna
                houses = whole_sign_houses_from(lagna_sign)
                houses_signs = [
                    {"house": h["house"], "sign": h["sign"], "sign_num": h["sign_num"]}
                    for h in houses
                ]
                planets_list = []
                varga_data: Dict[str, Any] = {}
                for p_name, per_planet in _varga_structured["planets"].items():
                    pos = per_planet[dkey_upper]
                    # Find legacy retro/combust from res_planets where possible
                    legacy_p = res_planets.get(p_name, {})
                    planets_list.append({
                        "name": p_name,
                        "longitude": round(float(pos.source_longitude), 6),  # compat D1 lon
                        "varga_longitude": round(float(pos.longitude), 6),
                        "varga_degree": round(float(pos.degree), 6),
                        "sign": pos.sign,
                        "sign_num": pos.sign_num,
                        "retro": bool(legacy_p.get("retrograde", False)),
                        "combust": bool(legacy_p.get("combust", False)),
                        "debilitated": is_debilitated(p_name, pos.sign),
                        "exalted": is_exalted(p_name, pos.sign),
                        "method": pos.method,
                        "segment_index": pos.segment_index,
                        "source_longitude": round(float(pos.source_longitude), 6),
                        "source_degree": round(float(pos.source_degree), 6),
                    })
                    varga_data[p_name] = {
                        f"d{v_num}_sign": pos.sign,
                        f"d{v_num}_sign_num": pos.sign_num,
                        f"d{v_num}_longitude": round(float(pos.source_longitude), 6),  # legacy = D1 lon
                        f"d{v_num}_varga_degree": round(float(pos.degree), 6),
                        f"d{v_num}_varga_longitude": round(float(pos.longitude), 6),
                        f"d{v_num}_segment_index": pos.segment_index,
                        f"d{v_num}_method": pos.method,
                        f"d{v_num}_source_longitude": round(float(pos.source_longitude), 6),
                        f"d{v_num}_source_degree": round(float(pos.source_degree), 6),
                        f"d{v_num}_source_sign": pos.source_sign,
                        "retrograde": bool(legacy_p.get("retrograde", False)),
                        "combust": bool(legacy_p.get("combust", False)),
                        "debilitated": is_debilitated(p_name, pos.sign),
                        "exalted": is_exalted(p_name, pos.sign),
                    }
                varga_data["_ascendant"] = ascendant_entry
                varga_data["_houses"] = houses
                varga_data["_houses_signs"] = houses_signs
                varga_data["planets"] = planets_list
                # Enriched structured for new consumers
                varga_data["_ascendant_position"] = asc_pos.model_dump()
                varga_data["_varga_positions"] = {
                    p_name: per_planet[dkey_upper].model_dump()
                    for p_name, per_planet in _varga_structured["planets"].items()
                }
                vargas[dkey_lower] = varga_data
        except Exception as e:
            print(f"[Varga] _calc_all_vargas from ChartFacts failed: {e}, falling back to legacy loop")
            _varga_structured = None
            vargas = {}

    if not vargas:
        # Fallback: legacy build_chart_varga loop (still uses pure engine internally if available)
        for v_num in vargas_list:
            vargas[f"d{v_num}"] = build_chart_varga(v_num, asc_sidereal, d1_planets_list)
        
    # Maintain root-level d9 and d10 for backwards compatibility
    d9 = vargas["d9"]
    d10 = vargas["d10"]
    
    # Add nakshatra, sign lord, varga info for each planet
    for planet_name, planet_data in res_planets.items():
        if planet_data.get("lon_sidereal_manual") is not None:
            lon_sid = planet_data["lon_sidereal_manual"]
            nak_data = compute_nakshatra_pada(lon_sid)
            planet_data["nakshatra"] = nak_data
            planet_data["star_lord"] = nak_data["lord"]
            
            sign_d1 = planet_data.get("sign_manual")
            if sign_d1:
                planet_data["sign_lord"] = SIGN_LORDS_MAP.get(sign_d1, "")
                
        # Link sign and sign lord details for D9 and D10
        if planet_name in d9:
            d9_sign = d9[planet_name].get("d9_sign")
            if d9_sign:
                planet_data["d9_sign"] = d9_sign
                planet_data["d9_sign_lord"] = SIGN_LORDS_MAP.get(d9_sign, "")
        if planet_name in d10:
            d10_sign = d10[planet_name].get("d10_sign")
            if d10_sign:
                planet_data["d10_sign"] = d10_sign
                planet_data["d10_sign_lord"] = SIGN_LORDS_MAP.get(d10_sign, "")

    # Add nakshatra, sign lord, star lord for Ascendant
    asc_nakshatra = None
    asc_sign_lord = None
    if asc_sidereal is not None:
        asc_nakshatra = compute_nakshatra_pada(asc_sidereal)
        asc_sign_lord = SIGN_LORDS_MAP.get(asc_sign, "")
        
    ascendant_data = houses_data["ascendant"].copy()
    if asc_nakshatra:
        ascendant_data["nakshatra"] = asc_nakshatra
        ascendant_data["star_lord"] = asc_nakshatra["lord"]
    if asc_sign_lord:
        ascendant_data["sign_lord"] = asc_sign_lord
        
    if d9.get("_ascendant"):
        asc_d9_sign = d9["_ascendant"].get("sign")
        if asc_d9_sign:
            ascendant_data["d9_sign"] = asc_d9_sign
            ascendant_data["d9_sign_lord"] = SIGN_LORDS_MAP.get(asc_d9_sign, "")
            
    if d10.get("_ascendant"):
        asc_d10_sign = d10["_ascendant"].get("sign")
        if asc_d10_sign:
            ascendant_data["d10_sign"] = asc_d10_sign
            ascendant_data["d10_sign_lord"] = SIGN_LORDS_MAP.get(asc_d10_sign, "")
            
    aspects_data = calculate_aspects_data(res_planets, asc_sign)
    
    res = {
        "jd_ut": jd_ut,
        "utc_at_birth": dt_utc.isoformat(),
        "ayanamsha_deg": ay,
        "planets": res_planets,
        "ascendant": ascendant_data,
        "whole_sign_houses": houses_data["whole_sign_houses"],
        "d9": d9,
        "d10": d10,
        "vargas": vargas,
        "aspects": aspects_data,
        "vimshottari": dasha,
        "nakshatra_of_moon": nakshatra,
        "karana": karana_data,
        "tithi": tithi_data,
        "nithya_yoga": yoga_data,
        "sunrise": sun_data.get("sunrise"),
        "sunset": sun_data.get("sunset"),
        "moon_sign": moon_sign,
        "asc_sidereal": asc_sidereal,
        "asc_sign": asc_sign,
        "mangal_dosha": calculate_mangal_dosha(res_planets, houses_data["whole_sign_houses"], asc_sign)
    }
    
    _active_tz = None
    return res


def calculate_mangal_dosha(planets: Dict[str, Any], whole_sign_houses: Dict[str, Any], asc_sign: str) -> Dict[str, Any]:
    """
    Calculate Mangal Dosha (Kuja Dosha) from Lagna, Moon, and Venus reference points.
    Includes comprehensive exception and cancellation rulesets.
    """
    if "Mars" not in planets:
        return {
            "has_dosha": False,
            "verdict": "No Dosha",
            "details": {},
            "cancellations_found": []
        }

    mars_data = planets["Mars"]
    mars_sign = mars_data.get("sign_manual") or mars_data.get("sign")
    if not mars_sign:
        return {
            "has_dosha": False,
            "verdict": "No Dosha",
            "details": {},
            "cancellations_found": []
        }
    
    # 1. Determine reference points
    moon_data = planets.get("Moon", {})
    moon_sign = moon_data.get("sign_manual") or moon_data.get("sign")
    
    venus_data = planets.get("Venus", {})
    venus_sign = venus_data.get("sign_manual") or venus_data.get("sign")
    
    references = {
        "Lagna": asc_sign,
        "Moon": moon_sign,
        "Venus": venus_sign
    }
    
    dosha_houses_set = {1, 2, 4, 7, 8, 12}
    details = {}
    total_dosha_houses = 0
    all_cancellations = []
    
    for ref_name, ref_sign in references.items():
        if not ref_sign:
            details[ref_name] = {
                "is_present": False,
                "house": None,
                "is_cancelled": False,
                "cancellation_reasons": []
            }
            continue
            
        try:
            ref_idx = SIGNS.index(ref_sign)
            mars_idx = SIGNS.index(mars_sign)
            mars_house = ((mars_idx - ref_idx) % 12) + 1
        except Exception:
            mars_house = 1
            
        is_present = mars_house in dosha_houses_set
        is_cancelled = False
        reasons = []
        
        if is_present:
            total_dosha_houses += 1
            
            # 1. Own Sign placement
            if mars_sign in ["Aries", "Scorpio"]:
                is_cancelled = True
                reasons.append(f"Mars is in its own sign ({mars_sign})")
                
            # 2. Exaltation placement
            elif mars_sign == "Capricorn":
                is_cancelled = True
                reasons.append("Mars is in its exaltation sign (Capricorn)")
                
            # 3. Yoga Karaka / Friendly sign
            elif mars_sign in ["Leo", "Cancer"]:
                is_cancelled = True
                reasons.append(f"Mars is in an auspicious sign ({mars_sign})")
                
            # 4. House-Specific Sign Exceptions
            if mars_house == 2 and mars_sign in ["Gemini", "Virgo"]:
                is_cancelled = True
                reasons.append(f"Mars in 2nd house is in Mercury's sign ({mars_sign})")
            elif mars_house == 4 and mars_sign in ["Taurus", "Libra"]:
                is_cancelled = True
                reasons.append(f"Mars in 4th house is in Venus's sign ({mars_sign})")
            elif mars_house == 7 and mars_sign in ["Cancer", "Capricorn"]:
                is_cancelled = True
                reasons.append(f"Mars in 7th house is cancelled in ({mars_sign})")
            elif mars_house == 8 and mars_sign in ["Sagittarius", "Pisces"]:
                is_cancelled = True
                reasons.append(f"Mars in 8th house is in Jupiter's sign ({mars_sign})")
            elif mars_house == 12 and mars_sign in ["Taurus", "Libra"]:
                is_cancelled = True
                reasons.append(f"Mars in 12th house is in Venus's sign ({mars_sign})")
                
            # 5. Conjunction with Jupiter or Moon
            jupiter_data = planets.get("Jupiter", {})
            jupiter_sign = jupiter_data.get("sign_manual") or jupiter_data.get("sign")
            if jupiter_sign == mars_sign:
                is_cancelled = True
                reasons.append("Mars is conjunct with Jupiter (Guru)")
                
            if moon_sign == mars_sign:
                is_cancelled = True
                reasons.append("Mars is conjunct with Chandra (Moon)")
                
            # 6. Aspects from Jupiter
            if jupiter_sign:
                try:
                    jup_idx = SIGNS.index(jupiter_sign)
                    mars_from_jup = ((mars_idx - jup_idx) % 12) + 1
                    if mars_from_jup in [5, 7, 9]:
                        is_cancelled = True
                        reasons.append("Mars is aspected by benefic Jupiter")
                except Exception:
                    pass
            
            # Aspect from Moon (opposite house)
            if moon_sign:
                try:
                    moon_idx = SIGNS.index(moon_sign)
                    mars_from_moon = ((mars_idx - moon_idx) % 12) + 1
                    if mars_from_moon == 7:
                        is_cancelled = True
                        reasons.append("Mars is aspected by the Moon from the 7th house")
                except Exception:
                    pass
                    
        # Append unique reasons to global list
        for r in reasons:
            if r not in all_cancellations:
                all_cancellations.append(r)
                
        details[ref_name] = {
            "is_present": is_present,
            "house": mars_house,
            "is_cancelled": is_cancelled,
            "cancellation_reasons": reasons
        }

    active_dosha_count = sum(1 for v in details.values() if v["is_present"] and not v["is_cancelled"])
    
    if total_dosha_houses == 0:
        verdict = "No Dosha"
        has_dosha = False
    elif active_dosha_count == 0:
        verdict = "Cancelled"
        has_dosha = False
    else:
        has_dosha = True
        if active_dosha_count == 1:
            verdict = "Mild Dosha"
        elif active_dosha_count == 2:
            verdict = "Medium Dosha"
        else:
            verdict = "High Dosha"
            
    return {
        "has_dosha": has_dosha,
        "verdict": verdict,
        "details": details,
        "cancellations_found": all_cancellations
    }


# ---------------------------
# ASHTA KOOTA MATCHING (South Indian Rashi Koota + BPHS tables)
# ---------------------------

# Varna hierarchy (higher index is higher varna): Shudra < Vaishya < Kshatriya < Brahmin
VARNA_BY_SIGN = {
    "Aries": "Kshatriya", "Leo": "Kshatriya", "Sagittarius": "Kshatriya",
    "Taurus": "Vaishya", "Virgo": "Vaishya", "Capricorn": "Vaishya",
    "Gemini": "Shudra", "Libra": "Shudra", "Aquarius": "Shudra",
    "Cancer": "Brahmin", "Scorpio": "Brahmin", "Pisces": "Brahmin",
}
VARNA_ORDER = {"Shudra": 0, "Vaishya": 1, "Kshatriya": 2, "Brahmin": 3}

# Permanent friendship (Naisargika Maitri) per user-provided table
PERMANENT_FRIENDSHIP = {
    "Sun": {"friends": {"Moon", "Mars", "Jupiter"}, "neutrals": {"Mercury"}, "enemies": {"Venus", "Saturn"}},
    "Moon": {"friends": {"Sun", "Mercury"}, "neutrals": {"Mars", "Jupiter", "Venus", "Saturn"}, "enemies": set()},
    "Mars": {"friends": {"Sun", "Moon", "Jupiter"}, "neutrals": {"Venus", "Saturn"}, "enemies": {"Mercury"}},
    "Mercury": {"friends": {"Sun", "Venus"}, "neutrals": {"Mars", "Jupiter", "Saturn"}, "enemies": {"Moon"}},
    "Jupiter": {"friends": {"Sun", "Moon", "Mars"}, "neutrals": {"Saturn"}, "enemies": {"Mercury", "Venus"}},
    "Venus": {"friends": {"Mercury", "Saturn"}, "neutrals": {"Mars", "Jupiter"}, "enemies": {"Sun", "Moon"}},
    "Saturn": {"friends": {"Mercury", "Venus"}, "neutrals": {"Jupiter"}, "enemies": {"Sun", "Moon", "Mars"}},
}

# Gana mapping by nakshatra (BPHS): Deva, Manushya, Rakshasa
GANA_BY_NAKSHATRA = {
    "Ashwini": "Deva", "Bharani": "Manushya", "Krittika": "Rakshasa",
    "Rohini": "Manushya", "Mrigashirsha": "Deva", "Ardra": "Manushya",
    "Punarvasu": "Deva", "Pushya": "Deva", "Ashlesha": "Rakshasa",
    "Magha": "Rakshasa", "Purva Phalguni": "Manushya", "Uttara Phalguni": "Manushya",
    "Hasta": "Deva", "Chitra": "Rakshasa", "Swati": "Deva",
    "Vishakha": "Rakshasa", "Anuradha": "Deva", "Jyeshtha": "Rakshasa",
    "Mula": "Rakshasa", "Purvashada": "Manushya", "Uttarashada": "Manushya",
    "Shravana": "Deva", "Dhanishta": "Rakshasa", "Shatabhisha": "Rakshasa",
    "Purva Bhadrapada": "Manushya", "Uttara Bhadrapada": "Manushya", "Revati": "Deva",
}

# Nadi mapping by nakshatra (BPHS): Adi, Madhya, Antya
NADI_BY_NAKSHATRA = {
    "Ashwini": "Adi", "Bharani": "Adi", "Krittika": "Adi",
    "Rohini": "Madhya", "Mrigashirsha": "Madhya", "Ardra": "Madhya",
    "Punarvasu": "Antya", "Pushya": "Antya", "Ashlesha": "Antya",
    "Magha": "Adi", "Purva Phalguni": "Adi", "Uttara Phalguni": "Adi",
    "Hasta": "Madhya", "Chitra": "Madhya", "Swati": "Madhya",
    "Vishakha": "Antya", "Anuradha": "Antya", "Jyeshtha": "Antya",
    "Mula": "Adi", "Purvashada": "Adi", "Uttarashada": "Adi",
    "Shravana": "Madhya", "Dhanishta": "Madhya", "Shatabhisha": "Madhya",
    "Purva Bhadrapada": "Antya", "Uttara Bhadrapada": "Antya", "Revati": "Antya",
}

# Yoni mapping (BPHS standardized 28-pair animal mapping); score matrix will be derived
YONI_BY_NAKSHATRA = {
    "Ashwini": "Horse", "Bharani": "Elephant", "Krittika": "Sheep",
    "Rohini": "Serpent", "Mrigashirsha": "Serpent", "Ardra": "Dog",
    "Punarvasu": "Cat", "Pushya": "Sheep", "Ashlesha": "Cat",
    "Magha": "Rat", "Purva Phalguni": "Rat", "Uttara Phalguni": "Cow",
    "Hasta": "Buffalo", "Chitra": "Tiger", "Swati": "Buffalo",
    "Vishakha": "Tiger", "Anuradha": "Deer", "Jyeshtha": "Deer",
    "Mula": "Dog", "Purvashada": "Monkey", "Uttarashada": "Mongoose",
    "Shravana": "Monkey", "Dhanishta": "Lion", "Shatabhisha": "Horse",
    "Purva Bhadrapada": "Lion", "Uttara Bhadrapada": "Cow", "Revati": "Elephant",
}

# Yoni pair compatibility scores (BPHS commonly used):
# 4 = best (same animal or friendly pair), 3 = good, 2 = average, 1 = poor, 0 = incompatible
# The canonical symmetric map is large; implement via rules: same animal -> 4, enemy pairs -> 0, friendly -> 3, neutral -> 2.
# Enemy pairs as per standard lists
YONI_ENEMIES = {
    ("Cat", "Rat"), ("Rat", "Cat"), ("Cow", "Tiger"), ("Tiger", "Cow"),
    ("Snake", "Mongoose"), ("Mongoose", "Snake"), ("Elephant", "Lion"), ("Lion", "Elephant"),
    ("Dog", "Deer"), ("Deer", "Dog"), ("Monkey", "Goat"), ("Goat", "Monkey"),
}

# For animals used here, alias Serpent->Snake, Sheep->Goat for enemy lists
YONI_ALIAS = {"Serpent": "Snake", "Sheep": "Goat"}

def _yoniname(an: str) -> str:
    return YONI_ALIAS.get(an, an)

# Vashya groups by sign (commonly used classification)
VASHYA_GROUP_BY_SIGN = {
    # Chatushpada (quadruped)
    "Aries": "Chatushpada", "Taurus": "Chatushpada", "Leo": "Chatushpada", "Capricorn": "Chatushpada",
    # Manava (human)
    "Gemini": "Manava", "Virgo": "Manava",
    # Jalachara (water)
    "Cancer": "Jalachara", "Pisces": "Jalachara",
    # Vanachara (forest)
    "Sagittarius": "Vanachara",
    # Keeta (insect)
    "Scorpio": "Keeta",
    # Libra, Aquarius commonly taken as Manava (some texts vary)
    "Libra": "Manava", "Aquarius": "Manava",
}

# Control relations for Vashya (who is vashya to whom) used for 2/1/0 scoring
VASHYA_CONTROL = {
    "Manava": {"Chatushpada"},
    "Chatushpada": {"Jalachara"},
    "Jalachara": {"Manava"},
    "Vanachara": {"All"},  # Sagittarius tends to be vashya to many
    "Keeta": set(),
}

def koota_varna(sign_groom: str, sign_bride: str) -> Dict[str, Any]:
    vg = VARNA_BY_SIGN.get(sign_groom)
    vb = VARNA_BY_SIGN.get(sign_bride)
    score = 0
    if vg is not None and vb is not None:
        score = 1 if VARNA_ORDER[vg] >= VARNA_ORDER[vb] else 0
    return {"koota": "Varna", "max": 1, "score": score, "groom_varna": vg, "bride_varna": vb}

def koota_vashya(sign_groom: str, sign_bride: str) -> Dict[str, Any]:
    gg = VASHYA_GROUP_BY_SIGN.get(sign_groom)
    gb = VASHYA_GROUP_BY_SIGN.get(sign_bride)
    score = 0
    if gg and gb:
        if gg == gb:
            score = 2
        elif "All" in VASHYA_CONTROL.get(gg, set()) or gb in VASHYA_CONTROL.get(gg, set()):
            score = 2
        elif "All" in VASHYA_CONTROL.get(gb, set()) or gg in VASHYA_CONTROL.get(gb, set()):
            score = 1
        else:
            score = 0
    return {"koota": "Vashya", "max": 2, "score": score, "groom_group": gg, "bride_group": gb}

def _nak_distance(i_from: int, i_to: int) -> int:
    d = (i_to - i_from) % 27
    return d if d != 0 else 27

FAVORABLE_TARA_POS = {1, 3, 6, 7, 9, 10, 13, 15, 18, 19, 21, 22, 25, 27}

def koota_tara(nak_idx_groom: int, nak_idx_bride: int) -> Dict[str, Any]:
    # nak_idx are 0-based in our compute_nakshatra_pada
    d1 = _nak_distance(nak_idx_groom, nak_idx_bride)
    d2 = _nak_distance(nak_idx_bride, nak_idx_groom)
    s = (1.5 if d1 in FAVORABLE_TARA_POS else 0.0) + (1.5 if d2 in FAVORABLE_TARA_POS else 0.0)
    return {"koota": "Tara", "max": 3, "score": round(s, 2), "dist_g2b": d1, "dist_b2g": d2}

def koota_yoni(nak_name_groom: str, nak_name_bride: str) -> Dict[str, Any]:
    ag = _yoniname(YONI_BY_NAKSHATRA.get(nak_name_groom, ""))
    ab = _yoniname(YONI_BY_NAKSHATRA.get(nak_name_bride, ""))
    score = 0
    if ag and ab:
        if ag == ab:
            score = 4
        elif (ag, ab) in YONI_ENEMIES:
            score = 0
        else:
            # Assume friendly pairs get 3, others neutral 2
            score = 3 if {ag, ab} in [{"Horse", "Elephant"}, {"Lion", "Tiger"}, {"Dog", "Monkey"}, {"Cow", "Buffalo"}] else 2
    return {"koota": "Yoni", "max": 4, "score": score, "groom_yoni": ag, "bride_yoni": ab}

def _friend_category(lord_a: str, lord_b: str) -> str:
    if lord_a == lord_b:
        return "same"
    table = PERMANENT_FRIENDSHIP.get(lord_a)
    if not table:
        return "neutral"
    if lord_b in table["friends"]:
        return "friend"
    if lord_b in table["enemies"]:
        return "enemy"
    return "neutral"

def koota_graha_maitri(moon_sign_groom: str, moon_sign_bride: str) -> Dict[str, Any]:
    lg = SIGN_LORDS_MAP.get(moon_sign_groom)
    lb = SIGN_LORDS_MAP.get(moon_sign_bride)
    score = 0
    if lg and lb:
        ca = _friend_category(lg, lb)
        cb = _friend_category(lb, lg)
        if ca == "same":
            score = 5
        elif ca == "friend" and cb == "friend":
            score = 5
        elif (ca == "friend" and cb == "neutral") or (ca == "neutral" and cb == "friend"):
            score = 4
        elif ca == "neutral" and cb == "neutral":
            score = 3
        elif (ca == "friend" and cb == "enemy") or (ca == "enemy" and cb == "friend"):
            score = 1
        elif ca == "enemy" and cb == "enemy":
            score = 0
        else:
            score = 2  # fallback mixed neutral/enemy
    return {"koota": "Graha Maitri", "max": 5, "score": score, "groom_lord": lg, "bride_lord": lb}

def koota_gana(nak_name_groom: str, nak_name_bride: str) -> Dict[str, Any]:
    gg = GANA_BY_NAKSHATRA.get(nak_name_groom)
    gb = GANA_BY_NAKSHATRA.get(nak_name_bride)
    score = 0
    if gg and gb:
        if gg == gb:
            score = 6
        elif {gg, gb} == {"Deva", "Manushya"}:
            score = 5
        elif (gg == "Manushya" and gb == "Rakshasa") or (gg == "Rakshasa" and gb == "Manushya"):
            score = 1
        elif {gg, gb} == {"Deva", "Rakshasa"}:
            score = 0
        else:
            score = 3
    return {"koota": "Gana", "max": 6, "score": score, "groom_gana": gg, "bride_gana": gb}

def koota_rashi_south(moon_sign_groom: str, moon_sign_bride: str) -> Dict[str, Any]:
    # South Indian Rashi Koota via sign-lord friendship with same-lord exception
    lg = SIGN_LORDS_MAP.get(moon_sign_groom)
    lb = SIGN_LORDS_MAP.get(moon_sign_bride)
    score = 0
    if lg and lb:
        if lg == lb:
            score = 7
        else:
            ca = _friend_category(lg, lb)
            cb = _friend_category(lb, lg)
            if ca == "friend" and cb == "friend":
                score = 7
            elif (ca == "friend" and cb == "neutral") or (ca == "neutral" and cb == "friend"):
                score = 6
            elif ca == "neutral" and cb == "neutral":
                score = 4
            elif (ca == "friend" and cb == "enemy") or (ca == "enemy" and cb == "friend"):
                score = 2
            elif ca == "enemy" and cb == "enemy":
                score = 0
            else:
                score = 3
    return {"koota": "Rashi", "max": 7, "score": score, "groom_lord": lg, "bride_lord": lb}

def koota_nadi(nak_name_groom: str, nak_name_bride: str) -> Dict[str, Any]:
    ng = NADI_BY_NAKSHATRA.get(nak_name_groom)
    nb = NADI_BY_NAKSHATRA.get(nak_name_bride)
    score = 0
    if ng and nb:
        score = 0 if ng == nb else 8
    return {"koota": "Nadi", "max": 8, "score": score, "groom_nadi": ng, "bride_nadi": nb}

def compute_ashta_koota(boy_chart: Dict[str, Any], girl_chart: Dict[str, Any]) -> Dict[str, Any]:
    # Extract essentials
    boy_moon = boy_chart.get("moon_sign") or ""
    girl_moon = girl_chart.get("moon_sign") or ""
    boy_moon_nak = (boy_chart.get("planets", {}).get("Moon", {}).get("nakshatra", {}) or {}).get("nakshatra")
    girl_moon_nak = (girl_chart.get("planets", {}).get("Moon", {}).get("nakshatra", {}) or {}).get("nakshatra")
    boy_nak_idx = (boy_chart.get("planets", {}).get("Moon", {}).get("nakshatra", {}) or {}).get("nakshatra_index")
    girl_nak_idx = (girl_chart.get("planets", {}).get("Moon", {}).get("nakshatra", {}) or {}).get("nakshatra_index")

    # Scores
    varna = koota_varna(boy_moon, girl_moon)
    vashya = koota_vashya(boy_moon, girl_moon)
    tara = koota_tara(boy_nak_idx, girl_nak_idx) if (boy_nak_idx is not None and girl_nak_idx is not None) else {"koota": "Tara", "max": 3, "score": 0}
    yoni = koota_yoni(boy_moon_nak or "", girl_moon_nak or "")
    maitri = koota_graha_maitri(boy_moon, girl_moon)
    gana = koota_gana(boy_moon_nak or "", girl_moon_nak or "")
    rashi = koota_rashi_south(boy_moon, girl_moon)
    nadi = koota_nadi(boy_moon_nak or "", girl_moon_nak or "")

    breakdown = [varna, vashya, tara, yoni, maitri, gana, rashi, nadi]
    total = sum(item.get("score", 0) for item in breakdown)

    verdict = "Not Compatible"
    if total >= 30:
        verdict = "Excellent"
    elif total >= 24:
        verdict = "Very Good"
    elif total >= 18:
        verdict = "Acceptable"

    return {
        "total": round(float(total), 2),
        "max": 36,
        "verdict": verdict,
        "kootas": breakdown
    }

def compute_match_for_birth_data(
    boy_params: Dict[str, Any], girl_params: Dict[str, Any]
) -> Dict[str, Any]:
    # Compute charts using existing compute_chart
    boy_chart = compute_chart(**boy_params)
    girl_chart = compute_chart(**girl_params)
    ashta = compute_ashta_koota(boy_chart, girl_chart)
    return {
        "boy": boy_chart,
        "girl": girl_chart,
        "ashta_koota": ashta
    }

