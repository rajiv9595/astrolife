from datetime import datetime
import pytz
import swisseph as swe

def get_utc_and_julian_day(year: int, month: int, day: int, hour: int, minute: int, second: int, tz_name: str):
    """
    Given a local date/time and IANA timezone name, calculates UTC and Julian Day.
    Returns: (utc_datetime, julian_day)
    """
    tz = pytz.timezone(tz_name)
    dt_local = datetime(year, month, day, hour, minute, second)
    
    # Check if the datetime is naive, then localize
    dt_local = tz.localize(dt_local)
    
    # Convert to UTC
    dt_utc = dt_local.astimezone(pytz.utc)
    
    # Decimal hours for Swiss Ephemeris
    ut_decimal = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    
    # Calculate Julian Day using Gregorian calendar
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut_decimal, swe.GREG_CAL)
    
    return dt_utc, jd

def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parses an ISO 8601 string to a datetime object.
    Returns an aware datetime if offset provided, otherwise naive.
    """
    return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
