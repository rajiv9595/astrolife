"""
Transit Events — deterministic detection (no interpretation).

Detects for a given time window:
 - sign ingress (30° boundary crossing)
 - nakshatra ingress (13°20')
 - retrograde station (speed sign change)
 - direct station
 - exact natal conjunction / opposition (0° / 180°)
 - exact Western aspect perfection
 - parashari aspect becoming active/inactive (house change)

Uses bracketing + bisection for exact times (Step 19).
Do not interpret as good/bad.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import math
import swisseph as swe
from pydantic import BaseModel, Field

from ..calculation.config import CalculationProfile, DEFAULT_PROFILE, AyanamshaSystem, NodeSystem
from ..calculation.models import ChartFacts
from .calculator import calculate_transit_positions, TransitSnapshot, _evaluation_jd

# ---------------------------------------------------------------------------
# Event models
# ---------------------------------------------------------------------------
class TransitEvent(BaseModel):
    type: str = Field(description="sign_ingress | nakshatra_ingress | retrograde_station | direct_station | exact_conjunction | exact_opposition | western_aspect_exact | parashari_aspect_change")
    transit_planet: str
    natal_planet: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    jd: float
    utc_iso: str
    system: str = "TRANSIT_EVENT_FACT"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _jd_to_utc_iso(jd: float) -> str:
    y,m,d,h_dec = swe.revjul(jd, swe.GREG_CAL)
    h = int(math.floor(h_dec))
    min_dec = (h_dec - h)*60.0
    mi = int(math.floor(min_dec))
    sec_dec = (min_dec - mi)*60.0
    sec_int = int(math.floor(sec_dec))
    micro = int(round((sec_dec - sec_int)*1_000_000))
    if micro>=1_000_000: micro-=1_000_000; sec_int+=1
    if sec_int>=60: sec_int-=60; mi+=1
    if mi>=60: mi-=60; h+=1
    if h>=24: h=23; mi=59; sec_int=59; micro=999999
    try:
        dt = datetime(y,m,d,h,mi,sec_int,micro, tzinfo=timezone.utc)
    except ValueError:
        dt = datetime(1900,1,1, tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00","Z")

def _get_transit_lon(jd: float, planet: str, profile: CalculationProfile) -> float:
    if profile.ayanamsha == AyanamshaSystem.LAHIRI_STANDARD:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        ay = swe.get_ayanamsa_ut(jd)
    else:
        ay = 0
    swe_map = {"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN}
    if planet in swe_map:
        res,_ = swe.calc_ut(jd, swe_map[planet], swe.FLG_SWIEPH | swe.FLG_SPEED)
        return (float(res[0]) - ay) % 360.0
    elif planet == "Rahu":
        flag = swe.MEAN_NODE if profile.node == NodeSystem.MEAN else swe.TRUE_NODE
        res,_ = swe.calc_ut(jd, flag, swe.FLG_SWIEPH | swe.FLG_SPEED)
        return (float(res[0]) - ay) % 360.0
    elif planet == "Ketu":
        flag = swe.MEAN_NODE if profile.node == NodeSystem.MEAN else swe.TRUE_NODE
        res,_ = swe.calc_ut(jd, flag, swe.FLG_SWIEPH | swe.FLG_SPEED)
        return (float(res[0]) + 180.0 - ay) % 360.0
    else:
        raise ValueError(planet)

def _get_transit_speed(jd: float, planet: str, profile: CalculationProfile) -> float:
    swe_map = {"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN}
    if planet in swe_map:
        res,_ = swe.calc_ut(jd, swe_map[planet], swe.FLG_SWIEPH | swe.FLG_SPEED)
        return float(res[3])
    elif planet in ("Rahu","Ketu"):
        flag = swe.MEAN_NODE if profile.node == NodeSystem.MEAN else swe.TRUE_NODE
        res,_ = swe.calc_ut(jd, flag, swe.FLG_SWIEPH | swe.FLG_SPEED)
        return float(res[3])
    return 0.0

def _find_sign_ingress(planet: str, lo_jd: float, hi_jd: float, profile: CalculationProfile, tol: float = 0.5/86400.0) -> Optional[float]:
    # Sign boundaries at k*30°
    lo_lon = _get_transit_lon(lo_jd, planet, profile)
    hi_lon = _get_transit_lon(hi_jd, planet, profile)
    lo_sign = int(lo_lon //30)
    hi_sign = int(hi_lon //30)
    if lo_sign == hi_sign:
        return None
    # Handle possible retrograde crossing (backwards). For ingress we detect any sign change regardless direction.
    # Find exact crossing at boundary = (lo_sign+1)*30 for direct, or lo_sign*30 for retrograde
    # We'll bisect for each candidate boundary between lo and hi
    # Since motion is monotonic in small step (unless station), we'll just bisect assuming monotonic through boundary.
    # For retrograde, lo_lon slightly higher than hi_lon crossing downwards.
    # We'll just find the boundary that lies between lons in shortest arc
    # Simplify: iterate boundaries and check if crossed
    candidates: List[float] = []
    for k in range(12):
        b = k*30.0
        # Check if b lies between lo_lon and hi_lon in circular sense (consider direction)
        # Direct: lo<hi and b between
        # Retro: lo>hi and b between when going backwards
        if lo_lon < hi_lon: # direct
            if lo_lon < b <= hi_lon or (lo_lon < b+360 <= hi_lon+360):
                candidates.append(b)
        else: # retrograde
            if hi_lon < b <= lo_lon:
                candidates.append(b)
    # Also wrap: try b+360 variants
    # Choose first candidate
    if not candidates:
        # may be crossing 0: lo 359 hi 5 direct -> boundary 0
        if lo_lon > 350 and hi_lon < 10:
            candidates.append(0.0)
        elif lo_lon < 10 and hi_lon > 350: # retro crossing 0 backwards
            candidates.append(0.0)
    if not candidates:
        return None
    target = candidates[0]
    # Bisection to find jd where lon == target
    lo = lo_jd; hi = hi_jd
    for _ in range(60):
        mid = (lo+hi)/2
        if abs(hi-lo) < tol:
            return mid
        mid_lon = _get_transit_lon(mid, planet, profile)
        lo_lon_cur = _get_transit_lon(lo, planet, profile)
        # Need unwrapped comparison
        # Direct case: lo->hi increasing
        if _get_transit_speed(lo, planet, profile) >=0: # direct approx
            if (lo_lon_cur <= target <= mid_lon) or (lo_lon_cur <= target+360 <= mid_lon+360) or (lo_lon_cur <= target and mid_lon < lo_lon_cur): # wrap
                hi = mid
            else:
                lo = mid
        else: # retro
            if mid_lon <= target <= lo_lon_cur or (target <= lo_lon_cur and target >= mid_lon):
                hi = mid
            else:
                lo = mid
        # fallback monotonic if speed near zero: compare unwrapped
    return (lo+hi)/2

def _find_nakshatra_ingress(planet: str, lo_jd: float, hi_jd: float, profile: CalculationProfile, tol: float = 0.5/86400.0) -> Optional[float]:
    lo_lon = _get_transit_lon(lo_jd, planet, profile)
    hi_lon = _get_transit_lon(hi_jd, planet, profile)
    nak_size = 360/27
    lo_idx = int(lo_lon // nak_size)
    hi_idx = int(hi_lon // nak_size)
    if lo_idx == hi_idx:
        return None
    # target boundary
    if hi_lon > lo_lon: # direct
        target = (lo_idx+1)*nak_size
    else:
        target = lo_idx * nak_size
    target = target % 360.0
    lo = lo_jd; hi = hi_jd
    def between(a,b,t):
        if a <= b:
            return a <= t <= b
        else:
            return t >= a or t <= b
    for _ in range(60):
        mid = (lo+hi)/2
        if abs(hi-lo) < tol:
            return mid
        mid_lon = _get_transit_lon(mid, planet, profile)
        lo_lon_cur = _get_transit_lon(lo, planet, profile)
        direct = hi_lon > lo_lon
        if direct:
            if between(lo_lon_cur, mid_lon, target):
                hi = mid
            else:
                lo= mid
        else:
            if between(mid_lon, lo_lon_cur, target):
                hi=mid
            else:
                lo=mid
    return (lo+hi)/2

# ---------------------------------------------------------------------------
# Main detection over range by daily sampling then refine
# ---------------------------------------------------------------------------
def detect_transit_events(
    natal: ChartFacts,
    start_datetime: datetime,
    end_datetime: datetime,
    profile: Optional[CalculationProfile] = None,
    sample_step_days: float = 1.0,
) -> List[TransitEvent]:
    if profile is None:
        profile = DEFAULT_PROFILE
    jd_start = _evaluation_jd(start_datetime)
    jd_end = _evaluation_jd(end_datetime)
    planets = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]

    events: List[TransitEvent] = []

    # sample JDs
    jds: List[float] = []
    jd = jd_start
    while jd <= jd_end + 1e-9:
        jds.append(jd)
        jd += sample_step_days
    if jds[-1] < jd_end - 1e-9:
        jds.append(jd_end)

    # Precompute positions and speeds at sample points
    # For each interval [jds[i], jds[i+1]] check for ingress / retrograde
    for i in range(len(jds)-1):
        lo = jds[i]; hi = jds[i+1]
        for pl in planets:
            # Sign ingress
            ingress_jd = _find_sign_ingress(pl, lo, hi, profile)
            if ingress_jd is not None and jd_start <= ingress_jd <= jd_end:
                lon = _get_transit_lon(ingress_jd, pl, profile)
                sign_num = int(lon //30) +1
                from ..calculation.houses import SIGNS as H_SIGNS
                # previous sign for context
                prev_lon = _get_transit_lon(ingress_jd - 0.01, pl, profile)
                prev_sign = H_SIGNS[int(prev_lon//30)]
                new_sign = H_SIGNS[int(lon//30)]
                events.append(TransitEvent(
                    type="sign_ingress", transit_planet=pl,
                    details={"from_sign": prev_sign, "to_sign": new_sign, "longitude": lon},
                    jd=ingress_jd, utc_iso=_jd_to_utc_iso(ingress_jd)
                ))
            # Nakshatra ingress
            nak_jd = _find_nakshatra_ingress(pl, lo, hi, profile)
            if nak_jd is not None and jd_start <= nak_jd <= jd_end:
                lon2 = _get_transit_lon(nak_jd, pl, profile)
                from ..calculation.nakshatra import NAKSHATRA_NAMES
                nak_size=360/27
                # rough
                prev_lon2 = _get_transit_lon(nak_jd-0.01, pl, profile)
                prev_idx = int(prev_lon2 // nak_size)
                new_idx = int(lon2 // nak_size)
                events.append(TransitEvent(
                    type="nakshatra_ingress", transit_planet=pl,
                    details={"from_nakshatra": NAKSHATRA_NAMES[prev_idx], "to_nakshatra": NAKSHATRA_NAMES[new_idx %27], "longitude": lon2},
                    jd=nak_jd, utc_iso=_jd_to_utc_iso(nak_jd)
                ))
            # Retrograde / direct station (speed sign change)
            s_lo = _get_transit_speed(lo, pl, profile)
            s_hi = _get_transit_speed(hi, pl, profile)
            if s_lo * s_hi < 0:  # sign change
                # Find exact zero crossing via bisection on speed
                lo2 = lo; hi2 = hi
                for _ in range(50):
                    mid = (lo2+hi2)/2
                    if abs(hi2-lo2) < 0.5/86400.0:
                        break
                    s_mid = _get_transit_speed(mid, pl, profile)
                    if s_lo * s_mid <= 0:
                        hi2 = mid
                        s_hi = s_mid
                    else:
                        lo2 = mid
                        s_lo = s_mid
                station_jd = (lo2+hi2)/2
                is_retro = s_hi < 0  # after crossing, if negative then retro start
                # Wait: if s_lo >0 and s_hi <0 then transition to retrograde => retrograde_station
                # if s_lo <0 and s_hi >0 => direct_station
                s_lo_orig = _get_transit_speed(lo, pl, profile)
                s_hi_orig = _get_transit_speed(hi, pl, profile)
                if s_lo_orig >0 and s_hi_orig <0:
                    ev_type = "retrograde_station"
                elif s_lo_orig <0 and s_hi_orig >0:
                    ev_type = "direct_station"
                else:
                    ev_type = "station"
                events.append(TransitEvent(
                    type=ev_type, transit_planet=pl,
                    details={"speed_before": s_lo_orig, "speed_after": s_hi_orig},
                    jd=station_jd, utc_iso=_jd_to_utc_iso(station_jd)
                ))

    # Exact natal conjunction/opposition — need finer search per planet pair
    # For each transit planet vs each natal planet, find exact 0° and 180° in range
    # This is more expensive; we do per day interval bisection on angular separation
    for pl in planets:
        for natal_name, natal_planet in natal.planets.items():
            natal_lon = float(natal_planet.longitude.sidereal)  # default sidereal
            # Define function angular separation signed for finding zero of (transit - natal)
            # For conjunction: transit_lon - natal_lon ==0 mod360 => transit_lon == natal_lon
            # For opposition: transit_lon == natal_lon+180
            targets = [(natal_lon, "exact_conjunction"), ((natal_lon+180)%360, "exact_opposition")]
            for target_lon, ev_type in targets:
                # Sample to bracket
                prev_jd = None
                prev_diff = None
                # Use step 1 day samples already but need finer for fast moon
                # We'll scan with step 1 day for slow planets, 0.25 for Moon
                step = 0.25 if pl=="Moon" else 1.0
                jd_scan = jd_start
                # Build dense samples
                scan_jds: List[float] = []
                tmp = jd_start
                while tmp <= jd_end+1e-9:
                    scan_jds.append(tmp)
                    tmp+=step
                if scan_jds[-1] < jd_end:
                    scan_jds.append(jd_end)
                for k in range(len(scan_jds)-1):
                    lo2 = scan_jds[k]; hi2 = scan_jds[k+1]
                    lo_lon = _get_transit_lon(lo2, pl, profile)
                    hi_lon = _get_transit_lon(hi2, pl, profile)
                    # Check if target between lo_lon and hi_lon (consider direction)
                    # Determine direction via speed sign avg
                    speed_avg = (_get_transit_speed(lo2, pl, profile) + _get_transit_speed(hi2, pl, profile))/2
                    # Unwrap target for comparison: if transit moving direct (speed>0), lon increases
                    # So target crossed if lo_lon < target <= hi_lon (with wrap)
                    def between_direct(a,b,t):
                        # a->b direct increase, possibly wrapping 360
                        if a <= b:
                            return a <= t <= b
                        else:
                            return t >= a or t <= b
                    def between_retro(a,b,t):
                        if b <= a:
                            return b <= t <= a
                        else:
                            return t >= b or t <= a # actually retro decreasing: a > b, wrapping opposite
                    # For direct: between a and b forward
                    # For retro: between b and a forward but direction reversed — we'll just use direct check both ways?
                    # Simpler: compute angular distance to target crossing detection via shortest diff sign change?
                    # Alternative: compute signed difference diff = (t_lon - target +540)%360-180 -> -180..180, zero at target
                    # Then look for sign change across interval
                    def signed_diff(lon):
                        return ((lon - target_lon + 540)%360)-180
                    d_lo = signed_diff(lo_lon)
                    d_hi = signed_diff(hi_lon)
                    # If sign changes or close to zero
                    if d_lo == 0:
                        events.append(TransitEvent(type=ev_type, transit_planet=pl, natal_planet=natal_name,
                                                    details={"target_longitude": target_lon, "transit_longitude": lo_lon, "separation": 0.0},
                                                    jd=lo2, utc_iso=_jd_to_utc_iso(lo2)))
                        continue
                    if d_lo * d_hi < 0:
                        # bracket found, bisect
                        lo_b = lo2; hi_b = hi2
                        for _ in range(50):
                            mid = (lo_b+hi_b)/2
                            if abs(hi_b-lo_b) < 0.5/86400.0:
                                break
                            mid_lon = _get_transit_lon(mid, pl, profile)
                            d_mid = signed_diff(mid_lon)
                            if d_lo * d_mid <= 0:
                                hi_b = mid; d_hi = d_mid
                            else:
                                lo_b = mid; d_lo = d_mid
                        mid_jd = (lo_b+hi_b)/2
                        mid_lon2 = _get_transit_lon(mid_jd, pl, profile)
                        sep = abs(((mid_lon2 - natal_lon +540)%360)-180) # distance to ... actually for conj we want diff to target, for opp target+180 else above already
                        events.append(TransitEvent(type=ev_type, transit_planet=pl, natal_planet=natal_name,
                                                    details={"target_longitude": target_lon, "transit_longitude": mid_lon2, "separation": sep},
                                                    jd=mid_jd, utc_iso=_jd_to_utc_iso(mid_jd)))
    # Sort by JD
    events.sort(key=lambda e: e.jd)
    return events
