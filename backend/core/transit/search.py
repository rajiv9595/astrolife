"""
Transit Time Search — precise root finding for exact events.

Provides helper functions for:

 - exact conjunction (transit lon == natal lon)
 - exact opposition (transit lon == natal lon +180)
 - exact aspect (any western angle)
 - sign ingress (lon == k*30)
 - station (speed ==0)

All use bracketing + bisection to sub-second precision, storing full precision internally.
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
import swisseph as swe
import math
from ..calculation.config import CalculationProfile, DEFAULT_PROFILE
from .calculator import _evaluation_jd

def find_exact_conjunction(
    transit_planet: str,
    natal_longitude: float,
    lo_datetime: datetime,
    hi_datetime: datetime,
    profile: Optional[CalculationProfile] = None,
    tol_days: float = 0.5/86400.0,
) -> Optional[float]:
    """
    Find JD where transit_planet sidereal longitude == natal_longitude
    within [lo, hi]. Returns JD or None if not bracketed.
    """
    if profile is None:
        profile = DEFAULT_PROFILE
    from .events import _get_transit_lon
    lo_jd = _evaluation_jd(lo_datetime)
    hi_jd = _evaluation_jd(hi_datetime)
    target = natal_longitude % 360.0
    # Check bracket via signed diff sign change
    def signed(lon): return ((lon - target + 540)%360)-180
    lo_lon = _get_transit_lon(lo_jd, transit_planet, profile)
    hi_lon = _get_transit_lon(hi_jd, transit_planet, profile)
    d_lo = signed(lo_lon); d_hi = signed(hi_lon)
    if d_lo * d_hi > 0 and abs(d_lo) > 1e-9 and abs(d_hi)>1e-9:
        return None
    for _ in range(60):
        if abs(hi_jd-lo_jd) < tol_days:
            return (lo_jd+hi_jd)/2
        mid = (lo_jd+hi_jd)/2
        mid_lon = _get_transit_lon(mid, transit_planet, profile)
        d_mid = signed(mid_lon)
        if d_lo * d_mid <= 0:
            hi_jd = mid; d_hi = d_mid
        else:
            lo_jd = mid; d_lo = d_mid
    return (lo_jd+hi_jd)/2
