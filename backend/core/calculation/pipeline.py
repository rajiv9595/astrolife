from typing import Dict, Any, Optional
from datetime import datetime
from .config import CalculationProfile, DEFAULT_PROFILE
from .models import (
    Location, TimeDetails, AyanamshaDetails, LongitudeDetails,
    SignPosition, NakshatraPosition, PlanetData, HouseData, 
    AscendantData, ChartFacts
)
from .time_utils import get_utc_and_julian_day
from .ephemeris import get_ayanamsha, calculate_planet_positions, calculate_ascendant
from .houses import get_sign_from_longitude, calculate_houses, get_house_for_sign
from .nakshatra import get_nakshatra_from_longitude

def generate_chart_facts(
    year: int, month: int, day: int, 
    hour: int, minute: int, second: int,
    lat: float, lon: float, tz_name: str,
    location_name: str = "Unknown",
    country_name: str = "Unknown",
    profile: CalculationProfile = DEFAULT_PROFILE,
    evaluation_datetime: Optional[datetime] = None
) -> ChartFacts:
    """
    Core Canonical Pipeline to generate ChartFacts.
    evaluation_datetime is used to track when this chart was calculated, separating static birth from dynamic evaluations.
    """
    # 1. Time Pipeline
    dt_utc, jd_ut = get_utc_and_julian_day(year, month, day, hour, minute, second, tz_name)
    time_details = TimeDetails(
        local_datetime=f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}",
        timezone=tz_name,
        utc_datetime=dt_utc.isoformat(),
        julian_day=jd_ut
    )
    
    # 2. Location
    loc_details = Location(
        name=location_name,
        country=country_name,
        latitude=lat,
        longitude=lon,
        timezone=tz_name
    )
    
    # 3. Ayanamsha
    ay_system, swiss_mode, ay_value = get_ayanamsha(jd_ut, profile)
    ay_details = AyanamshaDetails(
        system=ay_system,
        swiss_mode=swiss_mode,
        value=ay_value
    )
    
    # 4. Ascendant
    asc_raw = calculate_ascendant(jd_ut, lat, lon, ay_value)
    asc_sign_id, asc_sign_name, asc_sign_deg = get_sign_from_longitude(asc_raw["sidereal"])
    asc_nakshatra = get_nakshatra_from_longitude(asc_raw["sidereal"])
    
    asc_data = AscendantData(
        longitude=LongitudeDetails(tropical=asc_raw["tropical"], sidereal=asc_raw["sidereal"]),
        sign=SignPosition(id=asc_sign_id, name=asc_sign_name, degree=asc_sign_deg),
        nakshatra=asc_nakshatra
    )
    
    # 5. Houses
    houses_data = calculate_houses(asc_sign_id, profile)
    
    # 6. Planets
    raw_planets = calculate_planet_positions(jd_ut, ay_value, profile)
    planets_data: Dict[str, PlanetData] = {}
    
    for p_id, p_raw in raw_planets.items():
        p_sign_id, p_sign_name, p_sign_deg = get_sign_from_longitude(p_raw["sidereal"])
        p_nakshatra = get_nakshatra_from_longitude(p_raw["sidereal"])
        p_house = get_house_for_sign(p_sign_id, houses_data)
        
        planets_data[p_id] = PlanetData(
            id=p_id,
            name=p_id,
            longitude=LongitudeDetails(tropical=p_raw["tropical"], sidereal=p_raw["sidereal"]),
            latitude=p_raw["latitude"],
            distance=p_raw["distance"],
            speed=p_raw["speed"],
            retrograde=p_raw["retrograde"],
            sign=SignPosition(id=p_sign_id, name=p_sign_name, degree=p_sign_deg),
            house=p_house,
            nakshatra=p_nakshatra
        )
        
    metadata = {
        "evaluation_datetime": evaluation_datetime.isoformat() if evaluation_datetime else None
    }
        
    return ChartFacts(
        calculation_profile=profile,
        location=loc_details,
        time=time_details,
        ayanamsha=ay_details,
        ascendant=asc_data,
        planets=planets_data,
        houses=houses_data,
        metadata=metadata
    )
