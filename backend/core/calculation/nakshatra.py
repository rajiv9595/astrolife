import math
from .models import NakshatraPosition

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purvashada", "Uttarashada", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
]

def get_nakshatra_from_longitude(longitude: float) -> NakshatraPosition:
    """
    Calculates the canonical Nakshatra, Pada, and Lord from a sidereal longitude.
    """
    lon = longitude % 360.0
    nak_size = 360.0 / 27.0
    nak_index_float = lon / nak_size
    
    # Nakshatra index (0-26)
    nak_index = int(math.floor(nak_index_float))
    
    # Fraction into the nakshatra (0.0 to 1.0)
    fraction_into = nak_index_float - nak_index
    
    # Pada (1-4)
    pada = int(math.floor(fraction_into * 4)) + 1
    
    start_lon = nak_index * nak_size
    end_lon = start_lon + nak_size
    degree_within = lon - start_lon
    
    return NakshatraPosition(
        id=nak_index + 1, # 1-indexed for external use
        name=NAKSHATRA_NAMES[nak_index],
        lord=NAKSHATRA_LORDS[nak_index],
        pada=pada,
        fraction=fraction_into,
        start_longitude=start_lon,
        end_longitude=end_lon,
        degree_within=degree_within
    )
