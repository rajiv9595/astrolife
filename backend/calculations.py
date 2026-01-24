"""
Calculations Module
Handles all chart and dasha calculations including:
- Planetary positions and calculations
- Houses and ascendant
- Nakshatra, Karana, and Vimshottari dasha
- D9 (Navamsa) chart calculations
- D10 (Dashamsha) chart calculations
"""

from typing import Dict, Any, List, Optional
import swisseph as swe
import math
from datetime import datetime
import pytz

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
    "Saturn": swe.SATURN, "Rahu": swe.TRUE_NODE
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
    """Calculate Karana based on Moon and Sun longitudes."""
    moon = normalize_deg(moon_lon)
    sun = normalize_deg(sun_lon)
    
    # Calculate difference (handle wrap-around)
    diff = moon - sun
    if diff < 0:
        diff += 360.0
    
    # Karana is 6 degrees each, 11 unique karanas repeating
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
    dt = jd_to_datetime(jd_ut) # this returns UTC datetime from JD?
    # No, jd_to_datetime returns the datetime corresponding to the JD. JD is UT based.
    # So dt is UTC.
    # We need local date.
    ut_dt = pytz.utc.localize(dt)
    tz = pytz.timezone(tz_name)
    local_dt = ut_dt.astimezone(tz)
    
    # Construct JD for Local Noon of that day
    noon_local = local_dt.replace(hour=12, minute=0, second=0, microsecond=0)
    noon_utc = noon_local.astimezone(pytz.utc)
    
    # Get JD for noon utc
    ut_dec = noon_utc.hour + noon_utc.minute/60.0 + noon_utc.second/3600.0
    jd_noon = swe.julday(noon_utc.year, noon_utc.month, noon_utc.day, ut_dec, swe.GREG_CAL)
    
    # Search for sunrise backwards from noon (usually morning)
    # rise_trans signature in pyswisseph:
    # rise_trans(tjdut, body, rsmi, geopos, atpress, attemp, flags)
    # Returns: (int_status, (tjd_event, ...))
    try:
        res_rise = swe.rise_trans(jd_noon, swe.SUN, swe.CALC_RISE, (lon, lat, 0), 0, 0, flags)
        jd_rise = res_rise[1][0]
        
        res_set = swe.rise_trans(jd_noon, swe.SUN, swe.CALC_SET, (lon, lat, 0), 0, 0, flags)
        jd_set = res_set[1][0]
        
        # Convert JDs to local formatted strings
        rise_dt = jd_to_datetime(jd_rise).replace(tzinfo=pytz.utc).astimezone(tz)
        set_dt = jd_to_datetime(jd_set).replace(tzinfo=pytz.utc).astimezone(tz)
        
        return {
            "sunrise": rise_dt.strftime("%I:%M %p"),
            "sunset": set_dt.strftime("%I:%M %p"),
            "sunrise_jd": jd_rise,
            "sunset_jd": jd_set
        }
    except Exception as e:
        print(f"Error computing sunrise/sunset: {e}")
        return {"sunrise": "N/A", "sunset": "N/A"}


# ---------------------------
# VIMSHOTTARI DASHA
# ---------------------------
def jd_to_datetime(jd):
    """Convert Julian Day to datetime object."""
    jd_int = int(jd)
    jd_frac = jd - jd_int
    
    # Convert to Gregorian calendar
    # swe.revjul returns (year, month, day, hour) as integers
    result = swe.revjul(jd_int, swe.GREG_CAL)
    year = int(result[0])
    month = int(result[1])
    day = int(result[2])
    
    # Add fractional part (time of day) from JD
    total_seconds = jd_frac * 86400.0
    hour = int(total_seconds // 3600) % 24
    minute = int((total_seconds % 3600) // 60)
    second = int(total_seconds % 60)
    
    try:
        dt = datetime(year, month, day, hour, minute, second)
        return dt
    except (ValueError, TypeError):
        # Fallback to date only if time conversion fails
        try:
            return datetime(year, month, day, 0, 0, 0)
        except:
            return datetime(1900, 1, 1, 0, 0, 0)


def calculate_antar_dasha(mahadasha_lord, mahadasha_years, start_jd, days_in_year):
    """
    Calculate Antar Dasha (sub-periods) for a given Mahadasha.
    
    Formula: Antar Dasha duration = (Antar Lord years × Mahadasha years) / 120
    
    Args:
        mahadasha_lord: The lord of the Mahadasha
        mahadasha_years: Duration of the Mahadasha in years
        start_jd: Start Julian Day for this Mahadasha
        days_in_year: Days per year (365.2425)
    
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
        
        start_dt = jd_to_datetime(cursor)
        end_dt = jd_to_datetime(end_jd)
        
        antar_dashas.append({
            "lord": antar_lord,
            "start_jd": cursor,
            "end_jd": end_jd,
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "years": round(antar_years, 6),
            "is_current": False,  # Will be determined based on current date
            "pratyantar_dashas": []
        })
        cursor = end_jd
    
    return antar_dashas


def calculate_pratyantar_dasha(antar_lord, antar_years, start_jd, days_in_year):
    """
    Calculate Pratyantar Dasha (sub-sub-periods) for a given Antar Dasha.
    
    Formula: Pratyantar Dasha duration = (Pratyantar Lord years × Antar Dasha years) / 120
    
    Args:
        antar_lord: The lord of the Antar Dasha
        antar_years: Duration of the Antar Dasha in years
        start_jd: Start Julian Day for this Antar Dasha
        days_in_year: Days per year (365.2425)
    
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
        
        start_dt = jd_to_datetime(cursor)
        end_dt = jd_to_datetime(end_jd)
        
        pratyantar_dashas.append({
            "lord": pratyantar_lord,
            "start_jd": cursor,
            "end_jd": end_jd,
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "years": round(pratyantar_years, 6),
            "is_current": False  # Will be determined based on current date
        })
        cursor = end_jd
    
    return pratyantar_dashas


def compute_vimshottari_timeline(jd_birth, moon_sidereal_lon, years_ahead=100):
    """
    Calculate Vimshottari dasha timeline for up to specified years ahead.
    
    Vimshottari Dasha is a 120-year cycle divided among 9 planets:
    - Ketu: 7 years, Venus: 20 years, Sun: 6 years, Moon: 10 years
    - Mars: 7 years, Rahu: 18 years, Jupiter: 16 years
    - Saturn: 19 years, Mercury: 17 years
    
    Each Mahadasha is divided into 9 Antar Dashas (sub-periods).
    Each Antar Dasha is divided into 9 Pratyantar Dashas (sub-sub-periods).
    
    The dasha period starts from the birth nakshatra's lord and continues
    in the fixed sequence. The first period (from birth) is partial based
    on how much of the nakshatra the Moon has traversed.
    
    Args:
        jd_birth: Julian Day of birth
        moon_sidereal_lon: Moon's sidereal longitude at birth
        years_ahead: Number of years to calculate ahead (default: 100)
    
    Returns:
        Dictionary with nakshatra info and timeline of dasha periods including
        Antar Dashas and Pratyantar Dashas
    """
    if moon_sidereal_lon is None:
        return None

    # Calculate nakshatra and its lord
    nak = compute_nakshatra_pada(moon_sidereal_lon)
    fraction_into = nak["fraction"]  # 0 to 1, how much of nakshatra traversed
    lord = nak["lord"]
    full_years = VIMSHOTTARI_YEARS[lord]
    
    # Calculate remaining years in current dasha period from birth
    # If Moon has traversed 30% of nakshatra, 70% remains
    remaining_years = (1.0 - fraction_into) * full_years

    days_in_year = 365.2425
    timeline = []
    seq = VIMSHOTTARI_ORDER
    start_idx = seq.index(lord)
    
    # Start from birth date for the first (partial) dasha period
    cursor = jd_birth
    
    # First period: remaining time in current dasha from birth
    end_jd = cursor + remaining_years * days_in_year
    start_dt = jd_to_datetime(cursor)
    end_dt = jd_to_datetime(end_jd)
    
    # Calculate Antar Dashas for the first (partial) Mahadasha
    # The full Mahadasha started: fraction_into * full_years ago
    # So: mahadasha_start = jd_birth - (full_years - remaining_years) * days_in_year
    mahadasha_start_jd = cursor - (full_years - remaining_years) * days_in_year
    antar_dashas_full = calculate_antar_dasha(lord, full_years, mahadasha_start_jd, days_in_year)
    
    # Find which Antar Dashas are within the remaining period (from birth to end of Mahadasha)
    antar_dashas_partial = []
    for antar in antar_dashas_full:
        # Only include Antar Dashas that overlap with the remaining period (from birth)
        if antar["end_jd"] > cursor:  # Ends after birth
            antar_start = max(antar["start_jd"], cursor)  # Start from birth or Antar Dasha start, whichever is later
            antar_end = min(antar["end_jd"], end_jd)  # End at end of Mahadasha or Antar Dasha end, whichever is earlier
            
            if antar_start < antar_end:  # Only include if there's actual time
                antar_years = (antar_end - antar_start) / days_in_year
                start_dt_ad = jd_to_datetime(antar_start)
                end_dt_ad = jd_to_datetime(antar_end)
                
                # Calculate Pratyantar Dashas for this Antar Dasha
                # Use the full Antar Dasha boundaries for calculation
                pratyantar_dashas_full = calculate_pratyantar_dasha(
                    antar["lord"], 
                    antar["years"],  # Full Antar Dasha years
                    antar["start_jd"],  # Full Antar Dasha start
                    days_in_year
                )
                
                # Find Pratyantar Dashas within the partial Antar Dasha period
                pratyantar_dashas_partial = []
                for pratyantar in pratyantar_dashas_full:
                    # Only include Pratyantar Dashas that overlap with the partial Antar Dasha period
                    if pratyantar["end_jd"] > antar_start and pratyantar["start_jd"] < antar_end:
                        pratyantar_start = max(pratyantar["start_jd"], antar_start)
                        pratyantar_end = min(pratyantar["end_jd"], antar_end)
                        if pratyantar_start < pratyantar_end:
                            pratyantar_years_partial = (pratyantar_end - pratyantar_start) / days_in_year
                            pratyantar_start_dt = jd_to_datetime(pratyantar_start)
                            pratyantar_end_dt = jd_to_datetime(pratyantar_end)
                            pratyantar_dashas_partial.append({
                                "lord": pratyantar["lord"],
                                "start_jd": pratyantar_start,
                                "end_jd": pratyantar_end,
                                "start_date": pratyantar_start_dt.isoformat(),
                                "end_date": pratyantar_end_dt.isoformat(),
                                "years": round(pratyantar_years_partial, 6),
                                "is_current": False  # Will be determined based on current date
                            })
                
                antar_dashas_partial.append({
                    "lord": antar["lord"],
                    "start_jd": antar_start,
                    "end_jd": antar_end,
                    "start_date": start_dt_ad.isoformat(),
                    "end_date": end_dt_ad.isoformat(),
                    "years": round(antar_years, 6),
                    "is_current": False,  # Will be determined based on current date
                    "pratyantar_dashas": pratyantar_dashas_partial
                })
    
    # Calculate age at start and end of this Mahadasha
    start_age = (cursor - jd_birth) / days_in_year
    end_age = (end_jd - jd_birth) / days_in_year

    timeline.append({
        "lord": lord,
        "start_jd": cursor,
        "end_jd": end_jd,
        "start_date": start_dt.isoformat(),
        "end_date": end_dt.isoformat(),
        "years": round(remaining_years, 4),
        "is_partial": True,
        "is_current": False,  # Will be determined based on current date
        "start_age": round(start_age, 2),
        "end_age": round(end_age, 2),
        "antar_dashas": antar_dashas_partial
    })
    cursor = end_jd

    # Continue with subsequent full dasha periods
    i = 1
    while (cursor - jd_birth) < years_ahead * days_in_year:
        idx = (start_idx + i) % len(seq)
        pl = seq[idx]
        yrs = VIMSHOTTARI_YEARS[pl]
        end_jd = cursor + yrs * days_in_year
        
        start_dt = jd_to_datetime(cursor)
        end_dt = jd_to_datetime(end_jd)
        
        # Calculate Antar Dashas for this Mahadasha
        antar_dashas = calculate_antar_dasha(pl, yrs, cursor, days_in_year)
        
        # Calculate Pratyantar Dashas for each Antar Dasha
        for antar in antar_dashas:
            antar_years = antar["years"]
            pratyantar_dashas = calculate_pratyantar_dasha(
                antar["lord"],
                antar_years,
                antar["start_jd"],
                days_in_year
            )
            antar["pratyantar_dashas"] = pratyantar_dashas
        
        # Calculate age at start and end of this Mahadasha
        start_age = (cursor - jd_birth) / days_in_year
        end_age = (end_jd - jd_birth) / days_in_year
        
        timeline.append({
            "lord": pl,
            "start_jd": cursor,
            "end_jd": end_jd,
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "years": yrs,
            "is_partial": False,
            "is_current": False,  # Will be determined based on current date
            "start_age": round(start_age, 2),
            "end_age": round(end_age, 2),
            "antar_dashas": antar_dashas
        })
        cursor = end_jd
        i += 1

    # Determine current dasha based on today's date
    # Get current date/time in UTC
    now_utc = datetime.now(pytz.utc)
    ut_decimal = now_utc.hour + now_utc.minute / 60.0 + now_utc.second / 3600.0
    jd_now = swe.julday(now_utc.year, now_utc.month, now_utc.day, ut_decimal, swe.GREG_CAL)
    
    # Find which Mahadasha contains the current date
    current_mahadasha_found = False
    for mahadasha in timeline:
        if mahadasha["start_jd"] <= jd_now < mahadasha["end_jd"]:
            mahadasha["is_current"] = True
            current_mahadasha_found = True
            
            # Find current Antar Dasha within this Mahadasha
            if mahadasha.get("antar_dashas"):
                for antar in mahadasha["antar_dashas"]:
                    # For partial Mahadashas, we need to check if antar dates overlap with current date
                    if "start_jd" in antar and "end_jd" in antar:
                        if antar["start_jd"] <= jd_now < antar["end_jd"]:
                            antar["is_current"] = True
                            
                            # Find current Pratyantar Dasha within this Antar Dasha
                            if antar.get("pratyantar_dashas"):
                                for pratyantar in antar["pratyantar_dashas"]:
                                    if pratyantar["start_jd"] <= jd_now < pratyantar["end_jd"]:
                                        pratyantar["is_current"] = True
            break
    
    # If no current Mahadasha found, check if we're before the first period or after the last
    if not current_mahadasha_found and timeline:
        # Check if current date is before the first period (shouldn't happen for birth-based calculations)
        if jd_now < timeline[0]["start_jd"]:
            # Mark first period as current if we're before it (edge case)
            timeline[0]["is_current"] = True
        # If we're after all periods, mark the last one (this shouldn't happen with 100 years ahead)
        elif jd_now >= timeline[-1]["end_jd"]:
            timeline[-1]["is_current"] = True

    return {
        "nakshatra_of_moon": nak,
        "timeline": timeline,
        "total_years_calculated": round((cursor - jd_birth) / days_in_year, 2),
        "dasha_cycle_years": 120  # Total Vimshottari cycle is 120 years
    }


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
    
    Returns:
        Dictionary containing all chart data including planets, houses, d9, dasha, etc.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    
    # Convert to UTC and get Julian Day
    jd_ut, dt_utc = to_utc_julian_day(year, month, day, hour, minute, second, tz)
    
    # Get Ayanamsha
    swe.set_topo(lon, lat, float(topo_alt))
    ay = swe.get_ayanamsa_ut(jd_ut)
    
    # Default planets list
    planets = planets or [
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Rahu", "Ketu"
    ]
    
    # Calculate planets
    res_planets = calculate_planets(jd_ut, ay, planets, lon, lat, topo_alt)
    
    # Calculate houses and ascendant
    houses_data = calculate_houses(jd_ut, lat, lon, ay)
    asc_sidereal = houses_data["asc_sidereal"]
    asc_sign = houses_data["ascendant"]["sign"]
    
    # Calculate Nakshatra, Dasha, Karana
    moon_sid = res_planets.get("Moon", {}).get("lon_sidereal_manual")
    sun_sid = res_planets.get("Sun", {}).get("lon_sidereal_manual")
    
    nakshatra = compute_nakshatra_pada(moon_sid) if moon_sid else None
    dasha = compute_vimshottari_timeline(jd_ut, moon_sid) if moon_sid else None
    
    # Calculate Karana, Tithi, Nithya Yoga
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

    # D9 chart calculation
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
    
    # Build complete D9 chart structure
    d9_chart = build_chart_d9(asc_sidereal, d1_planets_list)
    
    # Transform to current API format for backward compatibility
    d9 = {}
    for p in d9_chart["planets"]:
        planet_name = p["name"]
        d9[planet_name] = {
            "d9_sign": p["sign"],
            "d9_sign_num": p["sign_num"],
            "d9_longitude": p["longitude"],
            "retrograde": p.get("retro", False),
            "combust": p.get("combust", False),
            "debilitated": p.get("debilitated", False),
            "exalted": p.get("exalted", False)
        }
    
    # Add D9 ascendant and houses (new fields for future frontend use)
    d9["_ascendant"] = d9_chart["ascendant"]
    d9["_houses"] = d9_chart["houses"]
    d9["_houses_signs"] = d9_chart["houses_signs"]
    
    # D10 chart calculation
    d10_chart = build_chart_d10(asc_sidereal, d1_planets_list)
    
    # Transform to current API format for backward compatibility
    d10 = {}
    for p in d10_chart["planets"]:
        planet_name = p["name"]
        d10[planet_name] = {
            "d10_sign": p["sign"],
            "d10_sign_num": p["sign_num"],
            "d10_longitude": p["longitude"],
            "retrograde": p.get("retro", False),
            "combust": p.get("combust", False),
            "debilitated": p.get("debilitated", False),
            "exalted": p.get("exalted", False)
        }
    
    # Add D10 ascendant and houses (new fields for future frontend use)
    d10["_ascendant"] = d10_chart["ascendant"]
    d10["_houses"] = d10_chart["houses"]
    d10["_houses_signs"] = d10_chart["houses_signs"]
    
    # Add nakshatra, sign lord, and d9 info for each planet
    for planet_name, planet_data in res_planets.items():
        if planet_data.get("lon_sidereal_manual"):
            lon_sid = planet_data["lon_sidereal_manual"]
            # Calculate nakshatra for this planet
            nak_data = compute_nakshatra_pada(lon_sid)
            planet_data["nakshatra"] = nak_data
            
            # Add sign lord for D1 sign
            sign_d1 = planet_data.get("sign_manual")
            if sign_d1:
                planet_data["sign_lord"] = SIGN_LORDS_MAP.get(sign_d1, "")
        
        # Add D9 sign and its lord
        if planet_name in d9:
            d9_sign = d9[planet_name].get("d9_sign")
            if d9_sign:
                planet_data["d9_sign"] = d9_sign
                planet_data["d9_sign_lord"] = SIGN_LORDS_MAP.get(d9_sign, "")
        
        # Add D10 sign and its lord
        if planet_name in d10:
            d10_sign = d10[planet_name].get("d10_sign")
            if d10_sign:
                planet_data["d10_sign"] = d10_sign
                planet_data["d10_sign_lord"] = SIGN_LORDS_MAP.get(d10_sign, "")
    
    # Add nakshatra and sign lord for ascendant
    asc_nakshatra = None
    asc_sign_lord = None
    if asc_sidereal:
        asc_nakshatra = compute_nakshatra_pada(asc_sidereal)
        asc_sign_lord = SIGN_LORDS_MAP.get(asc_sign, "")
    
    # Add ascendant info with nakshatra and sign lord
    ascendant_data = houses_data["ascendant"].copy()
    if asc_nakshatra:
        ascendant_data["nakshatra"] = asc_nakshatra
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
    
    return {
        "jd_ut": jd_ut,
        "utc_at_birth": dt_utc.isoformat(),
        "ayanamsha_deg": ay,
        "planets": res_planets,
        "ascendant": ascendant_data,
        "whole_sign_houses": houses_data["whole_sign_houses"],
        "d9": d9,
        "d10": d10,
        "vimshottari": dasha,
        "nakshatra_of_moon": nakshatra,
        "karana": karana_data,
        "tithi": tithi_data,
        "nithya_yoga": yoga_data,
        "sunrise": sun_data.get("sunrise"),
        "sunset": sun_data.get("sunset"),
        "moon_sign": moon_sign,
        "asc_sidereal": asc_sidereal,  # For use by calling code (e.g., lucky factors)
        "asc_sign": asc_sign  # For use by calling code
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

