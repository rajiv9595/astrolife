"""
Kala Bala Calculation - Classical Parashari Implementation

Components:
1. Nathonnatha Bala (Day/Night strength)
2. Paksha Bala (Lunar phase strength)
3. Tribhaga Bala (Day/night thirds strength)
4. Varsha Bala (Year lord strength) - Abda Bala
5. Masa Bala (Month lord strength)
6. Dina Bala (Day lord strength) - Vara Bala
7. Hora Bala (Hour lord strength)
8. Ayana Bala (Solstice strength)
9. Yuddha Bala (Planetary war strength)

Classical source: Parashara Hora Shastra, Chapter 27 (Shadbala)
Note: Varsha/Masa/Dina/Hora are collectively called "Abda/Masa/Vara/Hora Bala"
and form a group of 4 components totaling 60 virupas (15 each max in some traditions,
or 60 each in others - we follow the 60 each convention as per standard Shadbala)
"""
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
import swisseph as swe

from .models import KalaBala, KalaBalaComponent
from .profile import StrengthCalculationProfile, NATURAL_FRIENDSHIP, SIGNS, get_sign_index, normalize_deg
from ..calculation.pipeline import ChartFacts
from ..calculation.config import DEFAULT_PROFILE
from ..calculation.pipeline import generate_chart_facts


# Planet order for Hora calculations (Chaldean order)
PLANET_ORDER_HORA = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

# Weekday lords (0=Monday ... 6=Sunday)
WEEKDAY_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]

# Ayana Bala reference: Sun's declination
# Maximum at solstices (23°27'), zero at equinoxes
OBLIQUITY = 23.4392911  # Mean obliquity of ecliptic (J2000)


def calculate_nathonnatha_bala(
    planet: str,
    is_day_birth: bool,
    profile: StrengthCalculationProfile
) -> KalaBalaComponent:
    """
    Nathonnatha Bala: Diurnal/Nocturnal strength.
    
    Classical (Parashara):
    - Diurnal planets (Sun, Jupiter, Venus): 60 virupas day, 0 night
    - Nocturnal planets (Moon, Mars, Saturn): 60 virupas night, 0 day
    - Mercury: 60 virupas always (both day and night)
    """
    diurnal = {"Sun", "Jupiter", "Venus"}
    nocturnal = {"Moon", "Mars", "Saturn"}
    
    if planet in diurnal:
        value = 60.0 if is_day_birth else 0.0
        desc = "Diurnal planet" + (" (day birth)" if is_day_birth else " (night birth)")
    elif planet in nocturnal:
        value = 0.0 if is_day_birth else 60.0
        desc = "Nocturnal planet" + (" (day birth)" if is_day_birth else " (night birth)")
    else:  # Mercury
        value = 60.0
        desc = "Mercury (always strong)"
    
    return KalaBalaComponent(
        name="Nathonnatha Bala",
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        description=desc,
        classification="CLASSICAL"
    )


def calculate_paksha_bala(
    planet: str,
    moon_sidereal: float,
    sun_sidereal: float,
    profile: StrengthCalculationProfile
) -> KalaBalaComponent:
    """
    Paksha Bala: Lunar phase strength.
    
    Classical (Parashara):
    - Benefics (Jupiter, Venus, Mercury, waxing Moon): strength increases from New Moon to Full Moon
    - Malefics (Sun, Mars, Saturn, waning Moon): strength decreases from New Moon to Full Moon
    - Formula: 60 * (phase_angle / 180) for benefics, 60 * (1 - phase_angle / 180) for malefics
    - Phase angle = (Moon - Sun) normalized to 0-360, then 0-180 for paksha
    """
    # Calculate Moon-Sun angle
    angle = normalize_deg(moon_sidereal - sun_sidereal)
    if angle > 180:
        angle = 360 - angle  # 0-180 for paksha
    
    # Waxing (0-180) vs Waning (180-360)
    raw_diff = normalize_deg(moon_sidereal - sun_sidereal)
    is_waxing = raw_diff < 180
    
    benefics = {"Jupiter", "Venus", "Mercury"}
    malefics = {"Sun", "Mars", "Saturn"}
    
    if planet == "Moon":
        # Moon's own paksha bala: 60 at full moon, 0 at new moon
        value = 60.0 * (angle / 180.0)
        desc = f"Moon {'waxing' if is_waxing else 'waning'}, phase angle {angle:.2f}°"
    elif planet in benefics:
        value = 60.0 * (angle / 180.0)
        desc = f"Benefic, Moon {'waxing' if is_waxing else 'waning'}, phase angle {angle:.2f}°"
    elif planet in malefics:
        value = 60.0 * (1.0 - angle / 180.0)
        desc = f"Malefic, Moon {'waxing' if is_waxing else 'waning'}, phase angle {angle:.2f}°"
    else:
        value = 30.0  # Neutral
        desc = "Neutral planet"
    
    return KalaBalaComponent(
        name="Paksha Bala",
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        description=desc,
        classification="CLASSICAL"
    )


def calculate_tribhaga_bala(
    planet: str,
    birth_hour: int,
    is_day_birth: bool,
    profile: StrengthCalculationProfile
) -> KalaBalaComponent:
    """
    Tribhaga Bala: Strength based on which third of day/night birth occurs.
    
    Classical (Parashara):
    - Day divided into 3 parts: 6AM-10AM, 10AM-2PM, 2PM-6PM
    - Night divided into 3 parts: 6PM-10PM, 10PM-2AM, 2AM-6AM
    - Mercury: 1st part day/night
    - Sun: 2nd part day
    - Saturn: 3rd part day
    - Moon: 1st part night
    - Venus: 2nd part night
    - Mars: 3rd part night
    - Jupiter: all parts (always 60)
    """
    # Determine which third (1, 2, or 3)
    if is_day_birth:
        # Day: 6AM to 6PM
        if 6 <= birth_hour < 10:
            third = 1
        elif 10 <= birth_hour < 14:
            third = 2
        elif 14 <= birth_hour < 18:
            third = 3
        else:
            # Before 6AM or after 6PM but marked as day - use 1
            third = 1
    else:
        # Night: 6PM to 6AM
        if 18 <= birth_hour < 22:
            third = 1
        elif 22 <= birth_hour < 24:
            third = 2
        elif 0 <= birth_hour < 2:
            third = 2
        elif 2 <= birth_hour < 6:
            third = 3
        else:
            third = 1
    
    # Planet -> favored third mapping
    planet_thirds = {
        "Mercury": [1],      # 1st part day and night
        "Sun": [2],          # 2nd part day
        "Saturn": [3],       # 3rd part day
        "Moon": [1],         # 1st part night
        "Venus": [2],        # 2nd part night
        "Mars": [3],         # 3rd part night
        "Jupiter": [1, 2, 3], # All parts
    }
    
    favored = planet_thirds.get(planet, [])
    if third in favored or planet == "Jupiter":
        value = 60.0
    else:
        value = 0.0
    
    period = "day" if is_day_birth else "night"
    return KalaBalaComponent(
        name="Tribhaga Bala",
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        description=f"Birth in {period} third {third}, planet {'favors' if third in favored else 'does not favor'} this third",
        classification="CLASSICAL"
    )


def calculate_abda_bala(
    planet: str,
    birth_dt: datetime,
    lat: float,
    lon: float,
    tz_name: str,
    profile: StrengthCalculationProfile
) -> KalaBalaComponent:
    """
    Varsha Bala (Abda Bala): Year lord strength.
    
    Classical (Parashara):
    - Year lord = planet ruling the weekday of Mesha Sankranti (Sun's entry into Aries)
    - If birth is before Mesha Sankranti, use previous year's Mesha Sankranti
    - The year lord gets 60 virupas, others get 0
    
    We calculate the exact Mesha Sankranti using Swiss Ephemeris.
    """
    # Calculate Mesha Sankranti for the birth year
    # Mesha Sankranti = Sun enters Aries (sidereal 0°)
    # We need to find when Sun's sidereal longitude = 0°
    
    # Get ayanamsha for the year
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    
    # Search for Sun at sidereal 0° (tropical = ayanamsha)
    # Start from Jan 1 of birth year
    year = birth_dt.year
    
    def sun_sidereal_at(jd_ut: float) -> float:
        swe.set_topo(lon, lat, 0)
        res, _ = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        return normalize_deg(res[0])
    
    # Find Mesha Sankranti for this year
    # Start search from Jan 1
    jan1_jd = swe.julday(year, 1, 1, 0, swe.GREG_CAL)
    
    # Sun moves ~1°/day, so search around March 21 ± 30 days
    march21_jd = swe.julday(year, 3, 21, 0, swe.GREG_CAL)
    
    # Binary search for Sun sidereal = 0°
    low_jd = march21_jd - 30
    high_jd = march21_jd + 30
    
    for _ in range(50):  # Enough iterations for arcsecond precision
        mid_jd = (low_jd + high_jd) / 2
        sun_sid = sun_sidereal_at(mid_jd)
        if sun_sid > 180:  # Crossed 0°
            sun_sid -= 360
        if sun_sid > 0:
            high_jd = mid_jd
        else:
            low_jd = mid_jd
    
    mesha_sankranti_jd = (low_jd + high_jd) / 2
    
    # If birth is before Mesha Sankranti, use previous year's
    birth_jd = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day,
                           birth_dt.hour + birth_dt.minute/60.0 + birth_dt.second/3600.0, swe.GREG_CAL)
    
    if birth_jd < mesha_sankranti_jd:
        # Use previous year's Mesha Sankranti
        year = birth_dt.year - 1
        # Recalculate for previous year
        march21_jd = swe.julday(year, 3, 21, 0, swe.GREG_CAL)
        low_jd = march21_jd - 30
        high_jd = march21_jd + 30
        for _ in range(50):
            mid_jd = (low_jd + high_jd) / 2
            sun_sid = sun_sidereal_at(mid_jd)
            if sun_sid > 180:
                sun_sid -= 360
            if sun_sid > 0:
                high_jd = mid_jd
            else:
                low_jd = mid_jd
        mesha_sankranti_jd = (low_jd + high_jd) / 2
    
    # Get weekday of Mesha Sankranti
    # Convert JD to datetime
    y, m, d, h = swe.revjul(mesha_sankranti_jd, swe.GREG_CAL)
    sankranti_dt = datetime(int(y), int(m), int(d), int(h), int((h % 1) * 60), int(((h % 1) * 60) % 1 * 60))
    
    weekday = sankranti_dt.weekday()  # 0=Monday
    year_lord = WEEKDAY_LORDS[weekday]
    
    value = 60.0 if planet == year_lord else 0.0
    
    return KalaBalaComponent(
        name="Varsha Bala",
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        description=f"Year lord: {year_lord} (Mesha Sankranti {sankranti_dt.strftime('%Y-%m-%d %H:%M')} was {['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][weekday]})",
        classification="CLASSICAL"
    )


def calculate_masa_bala(
    planet: str,
    birth_dt: datetime,
    lat: float,
    lon: float,
    tz_name: str,
    profile: StrengthCalculationProfile
) -> KalaBalaComponent:
    """
    Masa Bala: Month lord strength.
    
    Classical (Parashara):
    - Month lord = planet ruling the weekday of New Moon (Amavasya) of birth month
    - The month starts from New Moon to next New Moon
    - The weekday of the New Moon determines the month lord
    """
    # Calculate the New Moon (Amavasya) for the birth month
    # New Moon = Moon-Sun longitude difference = 0° (or 360°)
    
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    swe.set_topo(lon, lat, 0)
    
    def moon_sun_diff(jd_ut: float) -> float:
        moon_res, _ = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        sun_res, _ = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        moon_lon = normalize_deg(moon_res[0])
        sun_lon = normalize_deg(sun_res[0])
        diff = normalize_deg(moon_lon - sun_lon)
        return diff
    
    # Start from 1st of birth month
    start_jd = swe.julday(birth_dt.year, birth_dt.month, 1, 0, swe.GREG_CAL)
    
    # New Moon occurs roughly every 29.5 days
    # Search in a window around the expected New Moon
    # New Moon around day 1-2 of month (if month starts with New Moon) or day 15-16
    # We'll search the whole month
    
    # Find the New Moon that starts the birth month
    # The month is defined from New Moon to next New Moon
    # Find the New Moon just before or on birth date
    
    birth_jd = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day,
                           birth_dt.hour + birth_dt.minute/60.0 + birth_dt.second/3600.0, swe.GREG_CAL)
    
    # Search backwards from birth date for New Moon (diff ~ 0)
    low_jd = birth_jd - 30
    high_jd = birth_jd
    
    # Find the most recent New Moon before birth
    # Moon-Sun diff = 0 at New Moon
    for _ in range(50):
        mid_jd = (low_jd + high_jd) / 2
        diff = moon_sun_diff(mid_jd)
        # At New Moon, diff goes from near 360 to near 0
        if diff > 180:
            # Past New Moon, going towards Full Moon
            high_jd = mid_jd
        else:
            # Before New Moon or just after
            low_jd = mid_jd
    
    # Actually, let's find the exact conjunction
    # We want Moon-Sun = 0° (mod 360)
    # Search for the root
    low_jd = birth_jd - 15
    high_jd = birth_jd + 15
    
    # Use the fact that at New Moon, diff ≈ 0
    # The derivative is positive (Moon moves faster than Sun)
    for _ in range(50):
        mid_jd = (low_jd + high_jd) / 2
        diff = moon_sun_diff(mid_jd)
        if diff > 180:
            diff -= 360  # Now diff is in [-180, 180]
        if diff > 0:
            # Past conjunction
            high_jd = mid_jd
        else:
            low_jd = mid_jd
    
    new_moon_jd = (low_jd + high_jd) / 2
    
    # Get weekday of New Moon
    y, m, d, h = swe.revjul(new_moon_jd, swe.GREG_CAL)
    new_moon_dt = datetime(int(y), int(m), int(d), int(h), int((h % 1) * 60), int(((h % 1) * 60) % 1 * 60))
    
    weekday = new_moon_dt.weekday()
    month_lord = WEEKDAY_LORDS[weekday]
    
    value = 60.0 if planet == month_lord else 0.0
    
    return KalaBalaComponent(
        name="Masa Bala",
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        description=f"Month lord: {month_lord} (New Moon {new_moon_dt.strftime('%Y-%m-%d %H:%M')} was {['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][weekday]})",
        classification="CLASSICAL"
    )


def calculate_dina_bala(
    planet: str,
    birth_dt: datetime,
    lat: float,
    lon: float,
    tz_name: str,
    profile: StrengthCalculationProfile
) -> KalaBalaComponent:
    """
    Dina Bala (Vara Bala): Day lord strength.
    
    Classical (Parashara):
    - Day lord = planet ruling the weekday of birth
    - Day is from sunrise to next sunrise (not midnight)
    - We need to check if birth is before or after sunrise
    """
    # Calculate sunrise for birth date
    tz = pytz.timezone(tz_name)
    
    # Get birth date in local timezone
    birth_local = tz.localize(datetime(birth_dt.year, birth_dt.month, birth_dt.day, birth_dt.hour, birth_dt.minute, birth_dt.second))
    
    # Calculate sunrise
    swe.set_topo(lon, lat, 0)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    
    # Get JD for local midnight
    midnight_local = birth_local.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = midnight_local.astimezone(pytz.utc)
    ut_dec = midnight_utc.hour + midnight_utc.minute/60.0 + midnight_utc.second/3600.0
    jd_midnight = swe.julday(midnight_utc.year, midnight_utc.month, midnight_utc.day, ut_dec, swe.GREG_CAL)
    
    # Find sunrise
    try:
        res_rise = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_RISE, (lon, lat, 0), 0, 0, swe.FLG_SWIEPH)
        sunrise_jd = res_rise[1][0]
        
        # Convert sunrise JD to local datetime
        sunrise_dt_utc = datetime(*swe.revjul(sunrise_jd, swe.GREG_CAL)[:4])
        sunrise_dt_utc = pytz.utc.localize(sunrise_dt_utc)
        sunrise_local = sunrise_dt_utc.astimezone(tz)
        
        # Determine day: if birth is before sunrise, it belongs to previous day
        if birth_local < sunrise_local:
            # Previous day
            prev_day = birth_local - timedelta(days=1)
            weekday = prev_day.weekday()
        else:
            weekday = birth_local.weekday()
    except Exception:
        # Fallback to simple weekday
        weekday = birth_local.weekday()
    
    day_lord = WEEKDAY_LORDS[weekday]
    value = 60.0 if planet == day_lord else 0.0
    
    return KalaBalaComponent(
        name="Dina Bala",
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        description=f"Day lord: {day_lord} (birth {birth_local.strftime('%A')} after sunrise check)",
        classification="CLASSICAL"
    )


def calculate_hora_bala(
    planet: str,
    birth_dt: datetime,
    lat: float,
    lon: float,
    tz_name: str,
    profile: StrengthCalculationProfile
) -> KalaBalaComponent:
    """
    Hora Bala: Hour lord strength.
    
    Classical (Parashara):
    - Day has 12 horas from sunrise to sunset
    - Night has 12 horas from sunset to next sunrise
    - Each hora = (day/night duration) / 12
    - Day horas start at sunrise with the day lord (weekday lord)
    - Night horas start at sunset with the 5th planet from day lord
    - Planets cycle in Chaldean order: Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon
    """
    tz = pytz.timezone(tz_name)
    birth_local = tz.localize(datetime(birth_dt.year, birth_dt.month, birth_dt.day, birth_dt.hour, birth_dt.minute, birth_dt.second))
    
    # Calculate sunrise and sunset
    swe.set_topo(lon, lat, 0)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    
    # Get JD for local midnight
    midnight_local = birth_local.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = midnight_local.astimezone(pytz.utc)
    ut_dec = midnight_utc.hour + midnight_utc.minute/60.0 + midnight_utc.second/3600.0
    jd_midnight = swe.julday(midnight_utc.year, midnight_utc.month, midnight_utc.day, ut_dec, swe.GREG_CAL)
    
    try:
        # Sunrise
        res_rise = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_RISE, (lon, lat, 0), 0, 0, swe.FLG_SWIEPH)
        sunrise_jd = res_rise[1][0]
        sunrise_dt_utc = datetime(*swe.revjul(sunrise_jd, swe.GREG_CAL)[:4])
        sunrise_dt_utc = pytz.utc.localize(sunrise_dt_utc)
        sunrise_local = sunrise_dt_utc.astimezone(tz)
        
        # Sunset
        res_set = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_SET, (lon, lat, 0), 0, 0, swe.FLG_SWIEPH)
        sunset_jd = res_set[1][0]
        sunset_dt_utc = datetime(*swe.revjul(sunset_jd, swe.GREG_CAL)[:4])
        sunset_dt_utc = pytz.utc.localize(sunset_dt_utc)
        sunset_local = sunset_dt_utc.astimezone(tz)
        
        # Determine if day or night birth
        is_day = sunrise_local <= birth_local < sunset_local
        
        # Day lord (weekday lord at sunrise)
        weekday = sunrise_local.weekday()
        day_lord = WEEKDAY_LORDS[weekday]
        day_lord_idx = PLANET_ORDER_HORA.index(day_lord)
        
        if is_day:
            # Day hora: 12 horas from sunrise to sunset
            day_duration = (sunset_local - sunrise_local).total_seconds()
            hora_duration = day_duration / 12
            seconds_since_sunrise = (birth_local - sunrise_local).total_seconds()
            hora_index = int(seconds_since_sunrise // hora_duration)
            if hora_index >= 12:
                hora_index = 11
            hora_lord_idx = (day_lord_idx + hora_index) % 7
        else:
            # Night hora: 12 horas from sunset to next sunrise
            # Next sunrise
            next_midnight = midnight_local + timedelta(days=1)
            next_midnight_utc = next_midnight.astimezone(pytz.utc)
            ut_dec_next = next_midnight_utc.hour + next_midnight_utc.minute/60.0 + next_midnight_utc.second/3600.0
            jd_next = swe.julday(next_midnight_utc.year, next_midnight_utc.month, next_midnight_utc.day, ut_dec_next, swe.GREG_CAL)
            
            res_next_rise = swe.rise_trans(jd_next, swe.SUN, swe.CALC_RISE, (lon, lat, 0), 0, 0, swe.FLG_SWIEPH)
            next_sunrise_jd = res_next_rise[1][0]
            next_sunrise_dt_utc = datetime(*swe.revjul(next_sunrise_jd, swe.GREG_CAL)[:4])
            next_sunrise_dt_utc = pytz.utc.localize(next_sunrise_dt_utc)
            next_sunrise_local = next_sunrise_dt_utc.astimezone(tz)
            
            night_duration = (next_sunrise_local - sunset_local).total_seconds()
            hora_duration = night_duration / 12
            seconds_since_sunset = (birth_local - sunset_local).total_seconds()
            if seconds_since_sunset < 0:
                seconds_since_sunset = 0
            hora_index = int(seconds_since_sunset // hora_duration)
            if hora_index >= 12:
                hora_index = 11
            # Night starts with 5th planet from day lord
            night_start_idx = (day_lord_idx + 4) % 7
            hora_lord_idx = (night_start_idx + hora_index) % 7
        
        hora_lord = PLANET_ORDER_HORA[hora_lord_idx]
        value = 60.0 if planet == hora_lord else 0.0
        
        return KalaBalaComponent(
            name="Hora Bala",
            value=round(value, 4),
            maximum=60.0,
            unit="virupas",
            description=f"Hora lord: {hora_lord} ({'day' if is_day else 'night'} hora {hora_index+1}, sunrise {sunrise_local.strftime('%H:%M')}, sunset {sunset_local.strftime('%H:%M')})",
            classification="CLASSICAL"
        )
    except Exception as e:
        # Fallback
        weekday = birth_local.weekday()
        day_lord = WEEKDAY_LORDS[weekday]
        day_lord_idx = PLANET_ORDER_HORA.index(day_lord)
        is_day = 6 <= birth_dt.hour < 18
        if is_day:
            hour_offset = birth_dt.hour - 6
            hora_lord_idx = (day_lord_idx + hour_offset) % 7
        else:
            night_start_idx = (day_lord_idx + 4) % 7
            hour_offset = birth_dt.hour - 18 if birth_dt.hour >= 18 else birth_dt.hour + 6
            hora_lord_idx = (night_start_idx + hour_offset) % 7
        hora_lord = PLANET_ORDER_HORA[hora_lord_idx]
        value = 60.0 if planet == hora_lord else 0.0
        return KalaBalaComponent(
            name="Hora Bala",
            value=round(value, 4),
            maximum=60.0,
            unit="virupas",
            description=f"Hora lord (fallback): {hora_lord}",
            classification="APPROXIMATION"
        )


def calculate_ayana_bala(
    planet: str,
    sun_tropical: float,
    profile: StrengthCalculationProfile
) -> KalaBalaComponent:
    """
    Ayana Bala: Solstice strength based on Sun's declination.
    
    Classical (Parashara):
    - Based on Sun's distance from equinox (ayana)
    - Maximum at solstices (23°27'), zero at equinoxes
    - Sun, Mars, Jupiter, Venus: strength proportional to Sun's northern declination
    - Moon, Saturn: strength proportional to Sun's southern declination
    - Mercury: always 30
    
    Formula: 60 * |sin(Sun_tropical)| * sin(obliquity) / sin(90°) ≈ 60 * |sin(Sun_tropical)| * sin(ε)
    Where ε = obliquity of ecliptic (~23.44°)
    
    More precisely: declination = arcsin(sin(ε) * sin(Sun_tropical))
    Ayana Bala = 60 * |declination| / ε_max
    """
    # Calculate Sun's declination
    # declination = arcsin(sin(obliquity) * sin(Sun_tropical))
    sun_declination = math.degrees(math.asin(math.sin(math.radians(OBLIQUITY)) * math.sin(math.radians(sun_tropical))))
    
    northern_planets = {"Sun", "Mars", "Jupiter", "Venus"}
    southern_planets = {"Moon", "Saturn"}
    
    max_declination = OBLIQUITY  # ~23.44°
    
    if planet in northern_planets:
        # Strong when Sun is north (positive declination)
        value = 60.0 * max(0, sun_declination) / max_declination
    elif planet in southern_planets:
        # Strong when Sun is south (negative declination)
        value = 60.0 * max(0, -sun_declination) / max_declination
    else:  # Mercury
        value = 30.0
    
    return KalaBalaComponent(
        name="Ayana Bala",
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        description=f"Sun tropical {sun_tropical:.2f}°, declination {sun_declination:.4f}°",
        classification="CLASSICAL"
    )


def calculate_yuddha_bala(
    planet: str,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile
) -> KalaBalaComponent:
    """
    Yuddha Bala: Planetary war strength.
    
    When two planets are within 1° of each other (in same sign), they are in war.
    Winner gets 60 virupas, loser gets 0.
    Non-participating planets get 30.
    """
    # Check if planet is in war with any other planet
    planet_data = chart_facts.planets.get(planet)
    if not planet_data:
        return KalaBalaComponent(
            name="Yuddha Bala",
            value=30.0,
            maximum=60.0,
            unit="virupas",
            description="Planet not found",
            classification="CLASSICAL"
        )
    
    planet_lon = planet_data.longitude.sidereal
    planet_sign = planet_data.sign.id
    
    in_war = False
    is_winner = False
    opponent = None
    
    for other_name, other_data in chart_facts.planets.items():
        if other_name == planet:
            continue
        if other_data.sign.id != planet_sign:
            continue
        other_lon = other_data.longitude.sidereal
        distance = abs(planet_lon - other_lon)
        if distance < 1.0:  # Within 1 degree = war
            in_war = True
            opponent = other_name
            # Winner = higher longitude (more advanced in sign)
            is_winner = planet_lon > other_lon
            break
    
    if not in_war:
        value = 30.0
        desc = "Not in planetary war"
    elif is_winner:
        value = 60.0
        desc = f"In war with {opponent} - WINNER"
    else:
        value = 0.0
        desc = f"In war with {opponent} - LOSER"
    
    return KalaBalaComponent(
        name="Yuddha Bala",
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        description=desc,
        classification="CLASSICAL"
    )


def calculate_kala_bala(
    planet: str,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile,
    evaluation_datetime: Optional[datetime] = None
) -> KalaBala:
    """Calculate complete Kala Bala with all subcomponents"""
    
    # Use birth time from chart facts
    birth_dt = datetime.fromisoformat(chart_facts.time.local_datetime.replace('T', ' '))
    lat = chart_facts.location.latitude
    lon = chart_facts.location.longitude
    tz_name = chart_facts.location.timezone
    is_day_birth = 6 <= birth_dt.hour < 18  # Approximate for Nathonnatha
    
    # Get Sun and Moon positions
    sun_data = chart_facts.planets.get("Sun")
    moon_data = chart_facts.planets.get("Moon")
    
    components = []
    
    # 1. Nathonnatha Bala
    nathonnatha = calculate_nathonnatha_bala(planet, is_day_birth, profile)
    components.append(nathonnatha)
    
    # 2. Paksha Bala
    if sun_data and moon_data:
        paksha = calculate_paksha_bala(planet, moon_data.longitude.sidereal, sun_data.longitude.sidereal, profile)
    else:
        paksha = KalaBalaComponent(name="Paksha Bala", value=30.0, maximum=60.0, unit="virupas", description="Sun/Moon data missing", classification="APPROXIMATION")
    components.append(paksha)
    
    # 3. Tribhaga Bala
    tribhaga = calculate_tribhaga_bala(planet, birth_dt.hour, is_day_birth, profile)
    components.append(tribhaga)
    
    # 4. Varsha Bala (Abda Bala) - Year lord from Mesha Sankranti
    varsha = calculate_abda_bala(planet, birth_dt, lat, lon, tz_name, profile)
    components.append(varsha)
    
    # 5. Masa Bala - Month lord from New Moon
    masa = calculate_masa_bala(planet, birth_dt, lat, lon, tz_name, profile)
    components.append(masa)
    
    # 6. Dina Bala (Vara Bala) - Day lord from sunrise
    dina = calculate_dina_bala(planet, birth_dt, lat, lon, tz_name, profile)
    components.append(dina)
    
    # 7. Hora Bala - Hour lord from sunrise/sunset
    hora = calculate_hora_bala(planet, birth_dt, lat, lon, tz_name, profile)
    components.append(hora)
    
    # 8. Ayana Bala
    if sun_data:
        ayana = calculate_ayana_bala(planet, sun_data.longitude.tropical, profile)
    else:
        ayana = KalaBalaComponent(name="Ayana Bala", value=30.0, maximum=60.0, unit="virupas", description="Sun data missing", classification="APPROXIMATION")
    components.append(ayana)
    
    # 9. Yuddha Bala
    yuddha = calculate_yuddha_bala(planet, chart_facts, profile)
    components.append(yuddha)
    
    total = sum(c.value for c in components)
    maximum = sum(c.maximum for c in components)
    
    return KalaBala(
        nathonnatha_bala=nathonnatha,
        paksha_bala=paksha,
        tribhaga_bala=tribhaga,
        varsha_bala=varsha,
        masa_bala=masa,
        dina_bala=dina,
        hora_bala=hora,
        ayana_bala=ayana,
        yuddha_bala=yuddha,
        total=round(total, 4),
        maximum=round(maximum, 4),
        unit="virupas",
        components=components
    )