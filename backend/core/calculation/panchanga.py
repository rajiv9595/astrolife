"""
Panchanga Engine — Pure Deterministic (Phase 3)

Computes:
  Tithi, Vara, Nakshatra, Yoga, Karana, Sunrise, Sunset
plus Paksha, Sun/Moon longitudes.

All astronomy via Swiss Ephemeris. No AI. No datetime.now().
Evaluation is explicit: calculate_panchanga(evaluation_datetime, latitude, longitude, timezone, profile)

Time interpolation for boundaries (start/end) via bisection/root finding
rather than assuming fixed clock duration.

Karana implemented as 60 half-Tithi sequence with fixed/movable distinction
(not int(diff/6)%11).

Vara uses local civil date (prevents UTC rollover bug).

Sunrise/Sunset via swe.rise_trans with explicit date handling.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import math
import pytz
import swisseph as swe

from .config import CalculationProfile, DEFAULT_PROFILE
from .models import ChartFacts

# ---------------------------------------------------------------------------
# Constants — names
# ---------------------------------------------------------------------------
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

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purvashada", "Uttarashada", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
]

# ---------------------------------------------------------------------------
# Karana — 60 half-tithi classical sequence
# ---------------------------------------------------------------------------
# Per Drik Panchang / BPHS / JHora (dominant tradition):
# - Movable (Chara) Karanas: Bava, Balava, Kaulava, Taitila, Gara, Vanija, Vishti (Bhadra) = 7, repeated 8 times = 56 positions (indices 1..56)
# - Fixed (Sthira) Karanas: Shakuni, Chatushpada, Naga, Kimstughna = 4, at positions 57..0
# Arrangement used here (documented, most common in JHora):
#   index 0: Kimstughna (Shukla Pratipada first half 0°-6°)
#   indices 1-56: Bava..Vishti ×8
#   index 57: Shakuni (Krishna Chaturdashi second half)
#   index 58: Chatushpada
#   index 59: Naga
# Then wraps to 0 Kimstughna for next cycle.
# This yields 60 distinct karana positions per lunar month (30 tithis ×2).
# Alternative placements: some texts place Kimstughna at end (59) and Shakuni at 57 etc. — functional loop identical, just rotation.
# We document this choice explicitly; switching requires only reordering this list.
KARANA_SEQUENCE_60: List[str] = []
# Build
_movable = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
KARANA_SEQUENCE_60.append("Kimstughna")  # 0
for _ in range(8):
    KARANA_SEQUENCE_60.extend(_movable)  # 1..56
KARANA_SEQUENCE_60.append("Shakuni")      # 57
KARANA_SEQUENCE_60.append("Chatushpada")  # 58
KARANA_SEQUENCE_60.append("Naga")         # 59
assert len(KARANA_SEQUENCE_60) == 60, f"Karana sequence length {len(KARANA_SEQUENCE_60)}"

# The 11 unique karana names for reference
KARANA_NAMES_11 = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"]

def karana_at_index(idx_60: int) -> str:
    return KARANA_SEQUENCE_60[idx_60 % 60]

# ---------------------------------------------------------------------------
# Pydantic Models for Panchanga output
# ---------------------------------------------------------------------------
class TithiInfo(BaseModel):
    index: int = Field(description="1..30 (1=Shukla Pratipada, 15=Purnima, 30=Amavasya)")
    index0: int = Field(description="0..29")
    name: str
    paksha: str  # "Shukla Paksha" or "Krishna Paksha"
    fraction_elapsed: float = Field(description="0..1 within tithi")
    percent_elapsed: float
    degrees_elapsed: float
    degrees_left: float
    angular_distance: float = Field(description="Moon-Sun diff 0..360")
    start_jd: Optional[float] = None
    end_jd: Optional[float] = None
    start_utc_iso: Optional[str] = None
    end_utc_iso: Optional[str] = None
    system: str = "VEDIC_PANCHANGA"

class KaranaInfo(BaseModel):
    index_60: int = Field(description="0..59 half-tithi position")
    name: str
    unique_index: int = Field(description="0..10 among 11 unique names")
    is_fixed: bool
    is_movable: bool
    half_tithi_fraction: float = Field(description="0..1 within this 6° karana")
    angular_distance: float
    start_jd: Optional[float] = None
    end_jd: Optional[float] = None
    start_utc_iso: Optional[str] = None
    end_utc_iso: Optional[str] = None
    sequence_note: str = "60 half-tithi sequence: Kimstughna(0), Bava..Vishti x8 (1-56), Shakuni(57), Chatushpada(58), Naga(59)"
    system: str = "VEDIC_PANCHANGA"

class NakshatraInfo(BaseModel):
    index: int = Field(description="1..27")
    index0: int = Field(description="0..26")
    name: str
    pada: int = Field(description="1..4")
    lord: str
    fraction_elapsed: float
    percent_elapsed: float
    start_longitude: float
    end_longitude: float
    degree_within: float
    longitude: float = Field(description="Moon sidereal longitude used")
    start_jd: Optional[float] = None
    end_jd: Optional[float] = None
    start_utc_iso: Optional[str] = None
    end_utc_iso: Optional[str] = None
    system: str = "VEDIC_PANCHANGA"

class YogaInfo(BaseModel):
    index: int = Field(description="1..27")
    index0: int = Field(description="0..26")
    name: str
    fraction_elapsed: float
    percent_elapsed: float
    angular_sum: float = Field(description="(Sun+Moon) mod 360")
    start_jd: Optional[float] = None
    end_jd: Optional[float] = None
    start_utc_iso: Optional[str] = None
    end_utc_iso: Optional[str] = None
    system: str = "VEDIC_PANCHANGA"

class VaraInfo(BaseModel):
    weekday_index: int = Field(description="0=Monday ... 6=Sunday (ISO)")
    weekday_name: str
    local_date: str = Field(description="YYYY-MM-DD civil date in target timezone")
    is_vedic_sunrise_based: bool = False
    system: str = "VEDIC_PANCHANGA"

class SunriseSunsetInfo(BaseModel):
    sunrise_jd: Optional[float] = None
    sunset_jd: Optional[float] = None
    sunrise_utc_iso: Optional[str] = None
    sunset_utc_iso: Optional[str] = None
    sunrise_local: Optional[str] = None  # formatted local
    sunset_local: Optional[str] = None
    sunrise_local_iso: Optional[str] = None
    sunset_local_iso: Optional[str] = None
    latitude: float
    longitude: float
    timezone: str
    polar_case: bool = False
    note: Optional[str] = None

class PanchangaDetails(BaseModel):
    evaluation_jd: float
    evaluation_utc_iso: str
    evaluation_local_iso: str
    location: Dict[str, Any]
    tithi: TithiInfo
    karana: KaranaInfo
    nakshatra: NakshatraInfo
    yoga: YogaInfo
    vara: VaraInfo
    sunrise_sunset: SunriseSunsetInfo
    sun_sidereal: float
    moon_sidereal: float
    ayanamsha: float
    ayanamsha_system: str

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalize_deg(d: float) -> float:
    return float(d) % 360.0

def _jd_to_utc_datetime(jd: float) -> datetime:
    import math as _math
    y, m, d, h_dec = swe.revjul(jd, swe.GREG_CAL)
    h = int(_math.floor(h_dec))
    min_dec = (h_dec - h) * 60.0
    mi = int(_math.floor(min_dec))
    sec_dec = (min_dec - mi) * 60.0
    sec_int = int(_math.floor(sec_dec))
    micro = int(round((sec_dec - sec_int) * 1_000_000))
    if micro >= 1_000_000:
        micro -= 1_000_000
        sec_int += 1
    if sec_int >= 60:
        sec_int -= 60
        mi += 1
    if mi >= 60:
        mi -= 60
        h += 1
    if h >= 24:
        h = 23; mi = 59; sec_int = 59; micro = 999999
    try:
        return datetime(y, m, d, h, mi, sec_int, micro, tzinfo=timezone.utc)
    except ValueError:
        return datetime(1900,1,1,tzinfo=timezone.utc)

def _jd_to_utc_iso(jd: float) -> str:
    return _jd_to_utc_datetime(jd).isoformat().replace("+00:00", "Z")

def _evaluation_jd(evaluation_datetime: datetime) -> float:
    if evaluation_datetime.tzinfo is None:
        dt_utc = evaluation_datetime.replace(tzinfo=timezone.utc)
    else:
        dt_utc = evaluation_datetime.astimezone(timezone.utc)
    ut_dec = dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0 + dt_utc.microsecond/3600.0/1_000_000.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut_dec, swe.GREG_CAL)

def _get_sidereal_longitudes(jd_ut: float, profile: CalculationProfile) -> Tuple[float, float, float]:
    """
    Returns (sun_sidereal, moon_sidereal, ayanamsha) at jd_ut for given profile.
    Pure ephemeris call.
    """
    # Ensure ayanamsha mode matches profile
    if profile.ayanamsha.value == "LAHIRI_STANDARD":
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ay = swe.get_ayanamsa_ut(jd_ut)
    # Get tropical longitudes
    sun_trop, _ = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH)
    moon_trop, _ = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH)
    sun_trop_lon = float(sun_trop[0])
    moon_trop_lon = float(moon_trop[0])
    sun_sid = _normalize_deg(sun_trop_lon - ay)
    moon_sid = _normalize_deg(moon_trop_lon - ay)
    return sun_sid, moon_sid, ay

def _diff_tithi(jd: float, profile: CalculationProfile) -> float:
    sun_sid, moon_sid, _ = _get_sidereal_longitudes(jd, profile)
    return _normalize_deg(moon_sid - sun_sid)

def _sum_yoga(jd: float, profile: CalculationProfile) -> float:
    sun_sid, moon_sid, _ = _get_sidereal_longitudes(jd, profile)
    return _normalize_deg(sun_sid + moon_sid)

def _moon_lon(jd: float, profile: CalculationProfile) -> float:
    _, moon_sid, _ = _get_sidereal_longitudes(jd, profile)
    return moon_sid

# ---------------------------------------------------------------------------
# Root finding — bisection for angular boundaries
# ---------------------------------------------------------------------------
def _find_crossing(
    get_angle_fn,  # fn(jd) -> angle 0..360 where we seek angle == target (mod 360, monotonic increasing in window)
    target_angle: float,
    lo_jd: float,
    hi_jd: float,
    tol_days: float = 1.0/86400.0/2,  # ~0.5 sec
    max_iter: int = 60,
) -> float:
    """
    Find jd where get_angle_fn(jd) == target_angle (mod 360), assuming monotonic increase
    in [lo_jd, hi_jd] with at most one wrap crossing 360->0.
    Bisection on unwrapped angle.
    """
    target = _normalize_deg(target_angle)
    lo_val = _normalize_deg(get_angle_fn(lo_jd))
    hi_val = _normalize_deg(get_angle_fn(hi_jd))

    # Unwrap hi if wrapped
    # If lo > hi, it wrapped over 360
    # We want monotonic unwrapped: if target < lo_val, treat target as target+360 etc.
    # Simplify: work in unwrapped space by adding 360 where needed
    # Determine if interval wrapped
    wrapped = hi_val < lo_val
    if wrapped:
        hi_unwrapped = hi_val + 360.0
        # target unwrapped: if target < lo_val then target+360 else target
        target_unwrapped = target + (360.0 if target < lo_val else 0.0)
        lo_unwrapped = lo_val
    else:
        hi_unwrapped = hi_val
        lo_unwrapped = lo_val
        target_unwrapped = target
        # if target out of [lo,hi] then no crossing — return nearest? but we bracket ensures inside
    # Edge: ensure target between lo and hi (with possible 360 shift). If not, return closest
    if not (lo_unwrapped - 1e-9 <= target_unwrapped <= hi_unwrapped + 1e-9):
        # No crossing; return midpoint
        return (lo_jd + hi_jd) / 2.0

    for _ in range(max_iter):
        mid_jd = (lo_jd + hi_jd) / 2.0
        mid_val_raw = _normalize_deg(get_angle_fn(mid_jd))
        # unwrap mid
        if wrapped:
            mid_unwrapped = mid_val_raw + (360.0 if mid_val_raw < lo_val else 0.0)
        else:
            mid_unwrapped = mid_val_raw
        if abs(hi_jd - lo_jd) < tol_days:
            return mid_jd
        if mid_unwrapped < target_unwrapped:
            lo_jd = mid_jd
            lo_unwrapped = mid_unwrapped
        else:
            hi_jd = mid_jd
            hi_unwrapped = mid_unwrapped
    return (lo_jd + hi_jd) / 2.0

def _bracket_and_find_tithi_boundary(
    jd_center: float,
    target_diff: float,
    profile: CalculationProfile,
    search_days: float = 2.0,
    tol_days: float = 0.5/86400.0,
) -> Optional[float]:
    target = _normalize_deg(target_diff)
    lo = jd_center - search_days
    hi = jd_center + search_days
    # Sample to find bracket containing target
    # Since diff increases ~12°/day, target will be within ~±1 day. We step 0.5 days
    step = 0.5
    cur = lo
    # Collect samples
    samples: List[Tuple[float, float]] = []
    jd = lo
    while jd <= hi + 1e-9:
        val = _normalize_deg(_diff_tithi(jd, profile))
        samples.append((jd, val))
        jd += step
    # Find interval where target lies between consecutive samples (handling wrap)
    for i in range(len(samples)-1):
        a_jd, a_val = samples[i]
        b_jd, b_val = samples[i+1]
        # Check if target is crossed from a to b (monotonic increasing ~12deg per 0.5day => ~6deg, well below wrap 360)
        # Only one possible wrap in entire 4-day window (if crossing 360). The per-0.5d step of 6° won't cross wrap silently except when a_val ~358 and b_val ~4
        # Detect wrap: a_val > 300 and b_val < 60 => wrapped interval
        if a_val <= b_val:
            # no wrap
            if a_val <= target <= b_val or (a_val <= target+360 <= b_val):  # shouldn't happen
                return _find_crossing(lambda j: _diff_tithi(j, profile), target, a_jd, b_jd, tol_days=tol_days)
            # also handle near due to 360 wrap needing to consider target equivalence (target and target+360)
        else:
            # wrapped interval (crossed 360)
            # target could be >a_val (358->360) or <b_val (0->4)
            if target >= a_val or target <= b_val:
                return _find_crossing(lambda j: _diff_tithi(j, profile), target, a_jd, b_jd, tol_days=tol_days)
    return None

def _bracket_and_find_yoga_boundary(
    jd_center: float, target_sum: float, profile: CalculationProfile, search_days: float = 2.0, tol_days: float = 0.5/86400.0
) -> Optional[float]:
    target = _normalize_deg(target_sum)
    lo = jd_center - search_days
    hi = jd_center + search_days
    step = 0.5
    samples: List[Tuple[float,float]] = []
    jd = lo
    while jd <= hi + 1e-9:
        val = _normalize_deg(_sum_yoga(jd, profile))
        samples.append((jd, val))
        jd += step
    for i in range(len(samples)-1):
        a_jd, a_val = samples[i]
        b_jd, b_val = samples[i+1]
        if a_val <= b_val:
            if a_val <= target <= b_val:
                return _find_crossing(lambda j: _sum_yoga(j, profile), target, a_jd, b_jd, tol_days=tol_days)
        else:
            if target >= a_val or target <= b_val:
                return _find_crossing(lambda j: _sum_yoga(j, profile), target, a_jd, b_jd, tol_days=tol_days)
    return None

def _bracket_and_find_moon_boundary(
    jd_center: float, target_lon: float, profile: CalculationProfile, search_days: float = 2.0, tol_days: float = 0.5/86400.0
) -> Optional[float]:
    target = _normalize_deg(target_lon)
    lo = jd_center - search_days
    hi = jd_center + search_days
    step = 0.5
    # moon moves ~13 deg/day, in 0.5 day ~6.5 deg
    samples: List[Tuple[float,float]] = []
    jd = lo
    while jd <= hi + 1e-9:
        val = _normalize_deg(_moon_lon(jd, profile))
        samples.append((jd, val))
        jd += step
    for i in range(len(samples)-1):
        a_jd, a_val = samples[i]
        b_jd, b_val = samples[i+1]
        if a_val <= b_val:
            if a_val <= target <= b_val:
                return _find_crossing(lambda j: _moon_lon(j, profile), target, a_jd, b_jd, tol_days=tol_days)
        else:
            if target >= a_val or target <= b_val:
                return _find_crossing(lambda j: _moon_lon(j, profile), target, a_jd, b_jd, tol_days=tol_days)
    return None

# ---------------------------------------------------------------------------
# Individual Panchanga Calculators (pure, given longitudes)
# ---------------------------------------------------------------------------
def compute_tithi_info(
    moon_lon: float, sun_lon: float,
    jd_ut: Optional[float] = None,
    profile: Optional[CalculationProfile] = None,
) -> TithiInfo:
    diff = _normalize_deg(moon_lon - sun_lon)
    tithi_val = diff / 12.0
    idx0 = int(math.floor(tithi_val + 1e-9))  # epsilon snap at boundaries
    if idx0 >= 30:
        idx0 = 29
    if idx0 < 0:
        idx0 = 0
    name = TITHI_NAMES[idx0]
    if idx0 < 15:
        paksha = "Shukla Paksha"
    else:
        paksha = "Krishna Paksha"
    fraction = tithi_val - idx0
    if fraction < 0: fraction = 0
    if fraction >= 1: fraction = 0.999999
    percent = fraction * 100.0
    degrees_elapsed = fraction * 12.0
    degrees_left = (1.0 - fraction) * 12.0

    # Boundary times via interpolation if jd provided
    start_jd = end_jd = None
    start_iso = end_iso = None
    if jd_ut is not None and profile is not None:
        start_boundary = idx0 * 12.0
        end_boundary = (idx0 + 1) * 12.0
        # wrap end 360 -> 0
        end_boundary_norm = _normalize_deg(end_boundary)
        # Find start and end times
        s_jd = _bracket_and_find_tithi_boundary(jd_ut, start_boundary, profile)
        e_jd = _bracket_and_find_tithi_boundary(jd_ut, end_boundary_norm, profile)
        # s_jd should be before jd_ut, e_jd after; if our bracket swapped we adjust
        # Ensure ordering
        if s_jd is not None and e_jd is not None:
            if s_jd > jd_ut + 1e-9:
                # s_jd is next cycle, find previous
                # try shift by -12 deg?
                pass
            if e_jd < jd_ut - 1e-9:
                pass
        start_jd = s_jd
        end_jd = e_jd
        if start_jd is not None:
            start_iso = _jd_to_utc_iso(start_jd)
        if end_jd is not None:
            end_iso = _jd_to_utc_iso(end_jd)

    return TithiInfo(
        index=idx0+1, index0=idx0, name=name, paksha=paksha,
        fraction_elapsed=fraction, percent_elapsed=percent,
        degrees_elapsed=degrees_elapsed, degrees_left=degrees_left,
        angular_distance=diff,
        start_jd=start_jd, end_jd=end_jd, start_utc_iso=start_iso, end_utc_iso=end_iso
    )

def compute_karana_info(
    moon_lon: float, sun_lon: float,
    jd_ut: Optional[float] = None,
    profile: Optional[CalculationProfile] = None,
) -> KaranaInfo:
    diff = _normalize_deg(moon_lon - sun_lon)
    idx_60 = int(math.floor(diff / 6.0 + 1e-9)) % 60
    name = KARANA_SEQUENCE_60[idx_60]
    # unique index among 11
    unique_idx = KARANA_NAMES_11.index(name) if name in KARANA_NAMES_11 else -1
    is_fixed = name in ("Shakuni", "Chatushpada", "Naga", "Kimstughna")
    fraction = (diff - idx_60 * 6.0) / 6.0
    if fraction < 0: fraction = 0
    if fraction >= 1: fraction = 0.999999

    start_jd = end_jd = None
    start_iso = end_iso = None
    if jd_ut is not None and profile is not None:
        start_boundary = idx_60 * 6.0
        end_boundary = (idx_60 + 1) * 6.0
        start_boundary_norm = _normalize_deg(start_boundary)
        end_boundary_norm = _normalize_deg(end_boundary)
        s_jd = _bracket_and_find_tithi_boundary(jd_ut, start_boundary_norm, profile)  # same diff function
        # For end, if Karana spans 6 deg, same bracket but target is end_boundary
        # Use same helper (diff-based) — it's correct because Karana boundaries are same as half-Tithi boundaries
        e_jd = _bracket_and_find_tithi_boundary(jd_ut, end_boundary_norm, profile)
        start_jd = s_jd
        end_jd = e_jd
        if start_jd is not None:
            start_iso = _jd_to_utc_iso(start_jd)
        if end_jd is not None:
            end_iso = _jd_to_utc_iso(end_jd)

    return KaranaInfo(
        index_60=idx_60, name=name, unique_index=unique_idx,
        is_fixed=is_fixed, is_movable=not is_fixed,
        half_tithi_fraction=fraction, angular_distance=diff,
        start_jd=start_jd, end_jd=end_jd, start_utc_iso=start_iso, end_utc_iso=end_iso
    )

def compute_nakshatra_info(
    moon_lon: float,
    jd_ut: Optional[float] = None,
    profile: Optional[CalculationProfile] = None,
) -> NakshatraInfo:
    lon = _normalize_deg(moon_lon)
    nak_size = 360.0 / 27.0
    nak_float = lon / nak_size
    idx0 = int(math.floor(nak_float + 1e-9))
    if idx0 >= 27: idx0 = 26
    if idx0 < 0: idx0 = 0
    fraction = nak_float - idx0
    if fraction < 0: fraction = 0
    if fraction >= 1: fraction = 0.999999
    name = NAKSHATRA_NAMES[idx0]
    lord = NAKSHATRA_LORDS[idx0]
    pada = int(math.floor(fraction * 4 + 1e-9)) + 1
    if pada > 4: pada = 4
    if pada < 1: pada = 1
    start_lon = idx0 * nak_size
    end_lon = start_lon + nak_size
    degree_within = lon - start_lon

    start_jd = end_jd = None
    start_iso = end_iso = None
    if jd_ut is not None and profile is not None:
        start_lon_target = start_lon
        end_lon_target = _normalize_deg(end_lon % 360)
        s_jd = _bracket_and_find_moon_boundary(jd_ut, start_lon_target, profile)
        e_jd = _bracket_and_find_moon_boundary(jd_ut, end_lon_target, profile)
        start_jd = s_jd
        end_jd = e_jd
        if start_jd is not None:
            start_iso = _jd_to_utc_iso(start_jd)
        if end_jd is not None:
            end_iso = _jd_to_utc_iso(end_jd)

    return NakshatraInfo(
        index=idx0+1, index0=idx0, name=name, pada=pada, lord=lord,
        fraction_elapsed=fraction, percent_elapsed=fraction*100,
        start_longitude=start_lon, end_longitude=end_lon,
        degree_within=degree_within, longitude=lon,
        start_jd=start_jd, end_jd=end_jd, start_utc_iso=start_iso, end_utc_iso=end_iso
    )

def compute_yoga_info(
    moon_lon: float, sun_lon: float,
    jd_ut: Optional[float] = None,
    profile: Optional[CalculationProfile] = None,
) -> YogaInfo:
    total = _normalize_deg(moon_lon + sun_lon)
    yoga_size = 360.0 / 27.0
    yoga_val = total / yoga_size
    idx0 = int(math.floor(yoga_val + 1e-9))
    if idx0 >= 27: idx0 = 26
    if idx0 < 0: idx0 = 0
    name = NITHYA_YOGA_NAMES[idx0]
    fraction = yoga_val - idx0
    if fraction < 0: fraction = 0
    if fraction >= 1: fraction = 0.999999

    start_jd = end_jd = None
    start_iso = end_iso = None
    if jd_ut is not None and profile is not None:
        start_boundary = idx0 * yoga_size
        end_boundary = (idx0 + 1) * yoga_size
        end_boundary_norm = _normalize_deg(end_boundary)
        s_jd = _bracket_and_find_yoga_boundary(jd_ut, start_boundary, profile)
        e_jd = _bracket_and_find_yoga_boundary(jd_ut, end_boundary_norm, profile)
        start_jd = s_jd
        end_jd = e_jd
        if start_jd is not None:
            start_iso = _jd_to_utc_iso(start_jd)
        if end_jd is not None:
            end_iso = _jd_to_utc_iso(end_jd)

    return YogaInfo(
        index=idx0+1, index0=idx0, name=name,
        fraction_elapsed=fraction, percent_elapsed=fraction*100,
        angular_sum=total,
        start_jd=start_jd, end_jd=end_jd, start_utc_iso=start_iso, end_utc_iso=end_iso
    )

def compute_vara_info(evaluation_datetime: datetime, tz_name: str, sunrise_jd: Optional[float] = None) -> VaraInfo:
    """
    Calculate Vara (weekday) from correct local civil date.
    If sunrise_jd provided and evaluation time is before sunrise, Vedic sunrise-based vara is previous civil day.
    Preserves civil vara as primary, documents Vedic alternative.
    """
    tz = pytz.timezone(tz_name)
    if evaluation_datetime.tzinfo is None:
        # naive assumed already in tz_name local
        local_dt = tz.localize(evaluation_datetime)
    else:
        local_dt = evaluation_datetime.astimezone(tz)
    civil_date = local_dt.date()
    weekday_index = local_dt.weekday()  # 0=Mon
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Vedic sunrise adjustment
    is_vedic_sunrise = False
    if sunrise_jd is not None:
        # compare evaluation JD vs sunrise JD
        eval_jd = _evaluation_jd(evaluation_datetime)
        if eval_jd < sunrise_jd - 1e-9:
            # vedic day hasn't started yet
            is_vedic_sunrise = True
            # Not changing weekday_name here; just flagging
    return VaraInfo(
        weekday_index=weekday_index,
        weekday_name=weekday_names[weekday_index],
        local_date=civil_date.isoformat(),
        is_vedic_sunrise_based=is_vedic_sunrise
    )

def calculate_sunrise_sunset(
    evaluation_datetime: datetime,
    latitude: float,
    longitude: float,
    tz_name: str,
) -> SunriseSunsetInfo:
    """
    Pure sunrise/sunset for the local civil date containing evaluation_datetime.
    Uses swe.rise_trans with PLACED at local midnight UTC.
    Handles polar cases gracefully.
    Returns both UTC JD and local formatted strings.
    No clock read except via evaluation_datetime param.
    """
    tz = pytz.timezone(tz_name)
    if evaluation_datetime.tzinfo is None:
        local_dt = tz.localize(evaluation_datetime)
    else:
        local_dt = evaluation_datetime.astimezone(tz)
    # Local midnight of that civil date
    midnight_local = local_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = midnight_local.astimezone(pytz.utc)
    ut_dec = midnight_utc.hour + midnight_utc.minute/60.0 + midnight_utc.second/3600.0 + midnight_utc.microsecond/3600.0/1_000_000.0
    jd_start = swe.julday(midnight_utc.year, midnight_utc.month, midnight_utc.day, ut_dec, swe.GREG_CAL)

    swe.set_topo(longitude, latitude, 0)
    flags = swe.FLG_SWIEPH
    geopos = (longitude, latitude, 0)

    sunrise_jd = None
    sunset_jd = None
    polar = False
    note = None
    try:
        res_rise = swe.rise_trans(jd_start, swe.SUN, swe.CALC_RISE, geopos, 0, 0, flags)
        if res_rise[0] == 0:
            sunrise_jd = float(res_rise[1][0])
        else:
            polar = True
            note = f"rise_trans error code {res_rise[0]}"
    except Exception as e:
        polar = True
        note = f"rise exception: {e}"
    try:
        res_set = swe.rise_trans(jd_start, swe.SUN, swe.CALC_SET, geopos, 0, 0, flags)
        if res_set[0] == 0:
            sunset_jd = float(res_set[1][0])
        else:
            polar = True
            note = (note or "") + f"; set error {res_set[0]}"
    except Exception as e:
        polar = True
        note = (note or "") + f"; set exc {e}"

    sunrise_utc_iso = _jd_to_utc_iso(sunrise_jd) if sunrise_jd is not None else None
    sunset_utc_iso = _jd_to_utc_iso(sunset_jd) if sunset_jd is not None else None
    sunrise_local = None
    sunset_local = None
    sunrise_local_iso = None
    sunset_local_iso = None
    if sunrise_jd is not None:
        dt_utc = _jd_to_utc_datetime(sunrise_jd)
        dt_loc = dt_utc.astimezone(tz)
        sunrise_local = dt_loc.strftime("%I:%M %p")
        sunrise_local_iso = dt_loc.isoformat()
    if sunset_jd is not None:
        dt_utc = _jd_to_utc_datetime(sunset_jd)
        dt_loc = dt_utc.astimezone(tz)
        sunset_local = dt_loc.strftime("%I:%M %p")
        sunset_local_iso = dt_loc.isoformat()

    return SunriseSunsetInfo(
        sunrise_jd=sunrise_jd, sunset_jd=sunset_jd,
        sunrise_utc_iso=sunrise_utc_iso, sunset_utc_iso=sunset_utc_iso,
        sunrise_local=sunrise_local, sunset_local=sunset_local,
        sunrise_local_iso=sunrise_local_iso, sunset_local_iso=sunset_local_iso,
        latitude=latitude, longitude=longitude, timezone=tz_name,
        polar_case=polar, note=note
    )

# ---------------------------------------------------------------------------
# Main orchestrator — pure Panchanga for evaluation_datetime
# ---------------------------------------------------------------------------
def calculate_panchanga(
    evaluation_datetime: datetime,
    latitude: float,
    longitude: float,
    tz_name: str,
    profile: Optional[CalculationProfile] = None,
) -> PanchangaDetails:
    """
    Deterministic Panchanga for any evaluation_datetime (explicit, no clock).
    evaluation_datetime may be UTC-aware or naive (assumed tz_name local if naive? we treat naive as local civil time in tz_name).
    For tests: pass aware UTC or fixed local.
    """
    if profile is None:
        profile = DEFAULT_PROFILE

    eval_jd = _evaluation_jd(evaluation_datetime)
    sun_sid, moon_sid, ay = _get_sidereal_longitudes(eval_jd, profile)

    # Core elements with boundary interpolation
    tithi = compute_tithi_info(moon_sid, sun_sid, jd_ut=eval_jd, profile=profile)
    karana = compute_karana_info(moon_sid, sun_sid, jd_ut=eval_jd, profile=profile)
    nakshatra = compute_nakshatra_info(moon_sid, jd_ut=eval_jd, profile=profile)
    yoga = compute_yoga_info(moon_sid, sun_sid, jd_ut=eval_jd, profile=profile)
    sunrise_sunset = calculate_sunrise_sunset(evaluation_datetime, latitude, longitude, tz_name)
    vara = compute_vara_info(evaluation_datetime, tz_name, sunrise_jd=sunrise_sunset.sunrise_jd)

    # Also produce local/eval iso
    if evaluation_datetime.tzinfo is None:
        tz = pytz.timezone(tz_name)
        local_dt = tz.localize(evaluation_datetime)
        eval_local_iso = local_dt.isoformat()
        eval_utc_iso = local_dt.astimezone(pytz.utc).isoformat().replace("+00:00","Z")
    else:
        eval_utc_iso = _jd_to_utc_iso(eval_jd)
        tz = pytz.timezone(tz_name)
        # local
        utc_dt = _jd_to_utc_datetime(eval_jd)
        local_dt = utc_dt.astimezone(tz)
        eval_local_iso = local_dt.isoformat()

    return PanchangaDetails(
        evaluation_jd=eval_jd,
        evaluation_utc_iso=eval_utc_iso,
        evaluation_local_iso=eval_local_iso,
        location={"latitude": latitude, "longitude": longitude, "timezone": tz_name},
        tithi=tithi, karana=karana, nakshatra=nakshatra, yoga=yoga, vara=vara,
        sunrise_sunset=sunrise_sunset,
        sun_sidereal=sun_sid, moon_sidereal=moon_sid,
        ayanamsha=ay, ayanamsha_system=profile.ayanamsha.value
    )

# ---------------------------------------------------------------------------
# Backwards compat: instant calculators (no JD interpolation) for compute_chart path
# ---------------------------------------------------------------------------
def compute_tithi_legacy(moon_lon: float, sun_lon: float) -> Dict[str, Any]:
    """Legacy-shaped dict for calculations.py backward compat."""
    info = compute_tithi_info(moon_lon, sun_lon)
    return {"index": info.index, "name": info.name, "paksha": info.paksha, "fraction": info.fraction_elapsed, "degrees_left": info.degrees_left}

def compute_karana_legacy(moon_lon: float, sun_lon: float) -> Dict[str, Any]:
    info = compute_karana_info(moon_lon, sun_lon)
    return {"karana": info.name, "karana_index": info.unique_index, "karana_index_60": info.index_60, "moon_sun_diff": round(info.angular_distance,4)}
