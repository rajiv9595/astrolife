"""
Varga Engine — Pure Derivation Layer (Phase 2)

All Varga calculations consume the canonical D1 sidereal longitude from ChartFacts.
They MUST NOT recalculate ayanamsha, JD, timezone, or call Swiss Ephemeris.

Architecture:
    ChartFacts (sidereal lon) -> Varga Engine -> D2..D60

Design goals:
- Pure functions: (sidereal_longitude, varga, method) -> VargaPosition
- Deterministic, no global state, no time dependency
- Single source for boundary handling with EPSILON
- Explicit method identifier per Varga
"""

from __future__ import annotations

import math
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum

from pydantic import BaseModel, Field

from .models import ChartFacts
from .config import VargaMethod as ConfigVargaMethod  # canonical

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SIGNS: List[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Epsilon for floating-point boundary handling.
# Small enough not to shift a genuine interior point across a boundary,
# large enough to absorb binary representation error at exact boundaries (e.g. 7.5).
EPSILON: float = 1e-9

# Valid Varga numbers (Shodusha Varga + D1)
VALID_VARGAS: List[int] = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

# ---------------------------------------------------------------------------
# Method / enums — re-export canonical from config for convenience
# ---------------------------------------------------------------------------
VargaMethod = ConfigVargaMethod


# ---------------------------------------------------------------------------
# Pydantic models for Varga output
# ---------------------------------------------------------------------------
class VargaPosition(BaseModel):
    """Single divisional position for one planet / ascendant."""
    varga: str = Field(description="e.g. 'D9'")
    varga_num: int = Field(description="e.g. 9")
    method: VargaMethod = Field(description="Calculation tradition")
    source_longitude: float = Field(description="Canonical D1 sidereal longitude 0-360")
    source_sign: str = Field(description="D1 sign name")
    source_sign_num: int = Field(description="D1 sign 1-12")
    source_degree: float = Field(description="Degree within D1 sign 0-30")
    segment_index: int = Field(description="0-indexed segment within D1 sign")
    segment_count: int = Field(description="Number of segments (division)")
    segment_size: float = Field(description="Size of one segment in degrees (30/division), NaN for D30 irregular")
    sign: str = Field(description="Varga sign name")
    sign_num: int = Field(description="Varga sign 1-12")
    degree: float = Field(description="Degree within Varga sign 0-30 (NOT D1 degree)")
    longitude: float = Field(description="Continuous longitude  (sign_num-1)*30 + degree in 0-360, convenience)")

class VargaChartPositions(BaseModel):
    """All vargas for a single object (planet or ascendant)."""
    d1_longitude: float
    vargas: Dict[str, VargaPosition] = Field(default_factory=dict)

# ---------------------------------------------------------------------------
# Internal helpers — pure, no I/O
# ---------------------------------------------------------------------------
def _normalize_lon(lon: float) -> float:
    return float(lon) % 360.0

def _get_d1_sign_and_degree(sidereal_longitude: float) -> Tuple[int, str, float]:
    """Return (sign_num 1-12, sign_name, degree_within_sign 0..30)."""
    lon = _normalize_lon(sidereal_longitude)
    sign_idx = int(math.floor(lon / 30.0))  # 0..11
    # Clamp exactly 360 -> 0
    if sign_idx >= 12:
        sign_idx = 11
    if sign_idx < 0:
        sign_idx = 0
    deg = lon - sign_idx * 30.0
    # Handle floating 29.9999999999 -> clamp
    if deg < 0:
        deg = 0.0
    if deg >= 30.0:
        # may be 30 due to rounding when lon ~ 359.999999999 + epsilon
        deg = 29.999999999
    return (sign_idx + 1, SIGNS[sign_idx], deg)

def _segment_index_uniform(deg_in_sign: float, division: int) -> int:
    """
    Common utility for uniform divisions.
    Half-open intervals [k*size, (k+1)*size), last interval [..,30).
    Adds EPSILON before floor to absorb e.g. 7.4999999999 -> 7.5 boundary.
    Clamps to [0, division-1].
    """
    if division <= 0:
        return 0
    size = 30.0 / division
    # deg_in_sign may be 29.9999999 due to FP; treat 30 as just below
    # Add tiny epsilon so exact boundary maps to next segment (e.g. 15.0 -> 1 for D2)
    idx = int(math.floor((deg_in_sign + EPSILON) / size))
    if idx < 0:
        idx = 0
    if idx >= division:
        idx = division - 1
    return idx

def _varga_degree_uniform(deg_in_sign: float, division: int, segment_index: int) -> float:
    """Map residual within segment to 0-30 inside Varga sign."""
    size = 30.0 / division
    residual = deg_in_sign - segment_index * size
    # Clamp residual for FP errors: if just below 0 due to EPSILON addition, clip
    if residual < 0:
        residual = 0.0
    if residual > size:
        # can happen due to clamping at last segment
        residual = size - 1e-12
    degree = residual * division  # because 30/size = division
    # Ensure <30
    if degree >= 30.0:
        degree = 29.999999999
    if degree < 0:
        degree = 0.0
    return degree

# Classification helpers
_MOVABLE = {1, 4, 7, 10}
_FIXED   = {2, 5, 8, 11}
_DUAL    = {3, 6, 9, 12}

def _is_odd(sign_num: int) -> bool:
    return sign_num % 2 == 1

# ---------------------------------------------------------------------------
# D30 helper — irregular Trimsamsa
# ---------------------------------------------------------------------------
# Returns (varga_sign_num 1-12, segment_index 0..4, slice_start, slice_end)
def _trimsamsa_lookup(d1_sign: int, deg: float) -> Tuple[int, int, float, float]:
    """
    Parashari Trimsamsa (BPHS) with 5 unequal slices.
    Odd signs:  0-5 Mars/Aries(1), 5-10 Saturn/Aqua(11), 10-18 Jupiter/Sag(9), 18-25 Mercury/Gem(3), 25-30 Venus/Taurus(2)
    Even signs: 0-5 Venus/Taurus(2), 5-12 Mercury/Virgo(6), 12-20 Jupiter/Pisces(12), 20-25 Saturn/Capricorn(10), 25-30 Mars/Scorpio(8)

    Boundaries are half-open: [start, end) except last includes 30.
    Exactly on boundary (e.g. 5.0) belongs to next slice — consistent with uniform rule.
    """
    is_odd = _is_odd(d1_sign)
    # Use EPSILON-adjusted comparison for boundaries
    # We add EPSILON to deg for boundary test so exactly 5.0 maps to next slice after floating error.
    # Effective test: deg + EPS < cut -> current slice; else next.
    # We implement via sequential if with < cut - EPSILON? Instead simpler: use deg+Eps < cut ? Better to use >= cut - eps?
    # Simplest: use raw deg but with small tolerance: if deg < cut - 1e-12 => else next.
    # But to mimic half-open where 5.0 => next, we use: if deg + EPS < cut => but then 5.0+eps >5 so goes next correct.
    # So condition: if deg + EPSILON < cut -> current
    # We implement by checking deg < cut - EPSILON? Equivalent but clearer:
    # Instead we just use: if deg < cut - EPS? do not; we use deg + EPS < cut is false for deg==cut
    # Let's just use direct comparisons with small adjustment: use (deg + EPSILON) < cut  => current slice, else next.
    # Example: deg=4.999999999 (just below 5) -> 4.999...+eps=5.000...000? may be 5.000001 >5 -> would incorrectly go next.
    # So we must NOT add epsilon before comparison for just-below values. Better to use deg < cut - 1e-12 vs >=.
    # Safer: use epsilon only to absorb 4.99999999999 representation when true value is 5.0.
    # Approach: round deg to near-cut if within 1e-9 of cut, snap to cut.
    # Then simple < cut logic gives correct half-open.
    def snapped(d: float) -> float:
        # Snap to known cuts if within EPSILON*10
        # Cuts differ for odd/even; check all relevant cuts with tolerance.
        cuts_odd = [5.0, 10.0, 18.0, 25.0, 30.0]
        cuts_even = [5.0, 12.0, 20.0, 25.0, 30.0]
        cuts = cuts_odd if is_odd else cuts_even
        for c in cuts:
            if abs(d - c) < 1e-9:
                return c
        return d
    d = snapped(deg)
    if is_odd:
        if d < 5.0:
            return (1, 0, 0.0, 5.0)
        elif d < 10.0:
            return (11, 1, 5.0, 10.0)
        elif d < 18.0:
            return (9, 2, 10.0, 18.0)
        elif d < 25.0:
            return (3, 3, 18.0, 25.0)
        else:
            return (2, 4, 25.0, 30.0)
    else:
        if d < 5.0:
            return (2, 0, 0.0, 5.0)
        elif d < 12.0:
            return (6, 1, 5.0, 12.0)
        elif d < 20.0:
            return (12, 2, 12.0, 20.0)
        elif d < 25.0:
            return (10, 3, 20.0, 25.0)
        else:
            return (8, 4, 25.0, 30.0)

def _trimsamsa_degree(deg: float, seg_idx: int, slice_start: float, slice_end: float) -> float:
    width = slice_end - slice_start
    residual = deg - slice_start
    if residual < 0:
        residual = 0.0
    if residual > width:
        residual = width - 1e-12
    # map width -> 30
    return (residual / width) * 30.0

# ---------------------------------------------------------------------------
# Core: get_varga_sign with method dispatch (pure)
# ---------------------------------------------------------------------------
def _get_varga_sign_and_segment(
    d1_sign: int, deg_in_sign: float, varga_num: int, method: VargaMethod
) -> Tuple[int, int, float]:
    """
    Returns (varga_sign_num 1-12, segment_index 0..N-1, segment_size)
    For D30, segment_size is NaN (irregular); caller must handle separately.
    """
    if method != VargaMethod.PARASHARI_CLASSICAL:
        raise ValueError(f"Unsupported varga method: {method}")

    if varga_num == 1:
        return (d1_sign, 0, 30.0)

    elif varga_num == 2:  # Hora
        is_odd = _is_odd(d1_sign)
        seg = _segment_index_uniform(deg_in_sign, 2)  # 0 first half, 1 second
        # Allocation: odd first->Leo(5) else Cancer(4); second half swapped
        if seg == 0:
            v_sign = 5 if is_odd else 4
        else:
            v_sign = 4 if is_odd else 5
        return (v_sign, seg, 15.0)

    elif varga_num == 3:  # Drekkana
        seg = _segment_index_uniform(deg_in_sign, 3)
        if seg == 0:
            v_sign = d1_sign
        elif seg == 1:
            v_sign = ((d1_sign + 4 - 1) % 12) + 1  # 5th
        else:
            v_sign = ((d1_sign + 8 - 1) % 12) + 1  # 9th
        return (v_sign, seg, 10.0)

    elif varga_num == 4:  # Chaturthamsa
        seg = _segment_index_uniform(deg_in_sign, 4)
        # Kendra: 1st,4th,7th,10th => offset 0,3,6,9
        v_sign = ((d1_sign - 1 + seg * 3) % 12) + 1
        return (v_sign, seg, 7.5)

    elif varga_num == 7:  # Saptamsa
        seg = _segment_index_uniform(deg_in_sign, 7)
        start = d1_sign if _is_odd(d1_sign) else ((d1_sign + 6 - 1) % 12) + 1  # same or 7th
        v_sign = ((start - 1 + seg) % 12) + 1
        return (v_sign, seg, 30.0 / 7.0)

    elif varga_num == 9:  # Navamsa
        seg = _segment_index_uniform(deg_in_sign, 9)  # pada 0..8
        if d1_sign in _MOVABLE:
            start = d1_sign
        elif d1_sign in _FIXED:
            start = ((d1_sign + 8 - 1) % 12) + 1  # 9th
        else:  # dual
            start = ((d1_sign + 4 - 1) % 12) + 1  # 5th
        v_sign = ((start - 1 + seg) % 12) + 1
        return (v_sign, seg, 30.0 / 9.0)

    elif varga_num == 10:  # Dasamsa
        seg = _segment_index_uniform(deg_in_sign, 10)
        is_odd = _is_odd(d1_sign)
        if is_odd:
            start = d1_sign
        else:
            start = ((d1_sign - 1 + 8) % 12) + 1  # 9th from even
        v_sign = ((start - 1 + seg) % 12) + 1
        return (v_sign, seg, 3.0)

    elif varga_num == 12:  # Dwadasamsa
        seg = _segment_index_uniform(deg_in_sign, 12)
        v_sign = ((d1_sign - 1 + seg) % 12) + 1
        return (v_sign, seg, 2.5)

    elif varga_num == 16:  # Shodasamsa
        seg = _segment_index_uniform(deg_in_sign, 16)
        if d1_sign in _MOVABLE:
            start = 1  # Aries
        elif d1_sign in _FIXED:
            start = 5  # Leo
        else:
            start = 9  # Sagittarius
        v_sign = ((start - 1 + seg) % 12) + 1
        return (v_sign, seg, 1.875)

    elif varga_num == 20:  # Vimsamsa
        seg = _segment_index_uniform(deg_in_sign, 20)
        if d1_sign in _MOVABLE:
            start = 1  # Aries
        elif d1_sign in _FIXED:
            start = 9  # Sagittarius
        else:
            start = 5  # Leo
        v_sign = ((start - 1 + seg) % 12) + 1
        return (v_sign, seg, 1.5)

    elif varga_num == 24:  # Chaturvimsamsa / Siddhamsa
        seg = _segment_index_uniform(deg_in_sign, 24)
        start = 5 if _is_odd(d1_sign) else 4  # Leo if odd, Cancer if even
        v_sign = ((start - 1 + seg) % 12) + 1
        return (v_sign, seg, 1.25)

    elif varga_num == 27:  # Saptavimsamsa / Bhamsha / Nakshatramsa
        seg = _segment_index_uniform(deg_in_sign, 27)
        element = (d1_sign - 1) % 4  # 0 Fire,1 Earth,2 Air,3 Water
        start = [1, 4, 7, 10][element]
        v_sign = ((start - 1 + seg) % 12) + 1
        return (v_sign, seg, 30.0 / 27.0)

    elif varga_num == 30:  # Trimsamsa — irregular
        v_sign, seg, s_start, s_end = _trimsamsa_lookup(d1_sign, deg_in_sign)
        # segment_size is variable; use NaN for uniform size
        return (v_sign, seg, float("nan"))

    elif varga_num == 40:  # Khavedamsa
        seg = _segment_index_uniform(deg_in_sign, 40)
        start = 1 if _is_odd(d1_sign) else 7  # Aries or Libra
        v_sign = ((start - 1 + seg) % 12) + 1
        return (v_sign, seg, 0.75)

    elif varga_num == 45:  # Akshavedamsa
        seg = _segment_index_uniform(deg_in_sign, 45)
        if d1_sign in _MOVABLE:
            start = 1
        elif d1_sign in _FIXED:
            start = 5
        else:
            start = 9
        v_sign = ((start - 1 + seg) % 12) + 1
        return (v_sign, seg, 30.0 / 45.0)

    elif varga_num == 60:  # Shashtiamsa
        seg = _segment_index_uniform(deg_in_sign, 60)
        v_sign = ((d1_sign - 1 + seg) % 12) + 1  # sequential from same
        return (v_sign, seg, 0.5)

    else:
        raise ValueError(f"Unsupported varga: {varga_num}")

# ---------------------------------------------------------------------------
# Public API 1: single position
# ---------------------------------------------------------------------------
def calculate_varga_position(
    sidereal_longitude: float,
    varga: int | str,
    method: VargaMethod | str = VargaMethod.PARASHARI_CLASSICAL,
) -> VargaPosition:
    """
    Pure function: derive Varga position from canonical D1 sidereal longitude.

    Args:
        sidereal_longitude: canonical sidereal longitude 0-360 from ChartFacts
        varga: integer 1..60 or string 'D9'/'d9'/9
        method: VargaMethod or string 'PARASHARI_CLASSICAL'

    Returns:
        VargaPosition with varga sign, degree INSIDE that sign, segment_index, etc.

    Raises:
        ValueError for unsupported varga/method.
    """
    # Normalize varga param
    if isinstance(varga, str):
        v_str = varga.strip().upper()
        if v_str.startswith("D"):
            v_str = v_str[1:]
        try:
            varga_num = int(v_str)
        except ValueError:
            raise ValueError(f"Invalid varga string: {varga}")
    else:
        varga_num = int(varga)

    if varga_num not in VALID_VARGAS:
        raise ValueError(f"Unsupported varga {varga_num}. Valid: {VALID_VARGAS}")

    # Normalize method
    if isinstance(method, str):
        try:
            method_enum = VargaMethod(method)
        except ValueError:
            raise ValueError(f"Unsupported varga method: {method}")
    else:
        method_enum = method

    lon_norm = _normalize_lon(sidereal_longitude)
    d1_sign_num, d1_sign_name, deg_in_sign = _get_d1_sign_and_degree(lon_norm)

    v_sign_num, seg_idx, seg_size = _get_varga_sign_and_segment(
        d1_sign_num, deg_in_sign, varga_num, method_enum
    )
    v_sign_name = SIGNS[v_sign_num - 1]

    # Compute varga degree inside derived sign
    if varga_num == 30:
        # Irregular — need slice boundaries for correct degree mapping
        _, _, s_start, s_end = _trimsamsa_lookup(d1_sign_num, deg_in_sign)
        v_degree = _trimsamsa_degree(deg_in_sign, seg_idx, s_start, s_end)
        # For display, segment_size is width of this slice
        seg_size_val = s_end - s_start
        seg_count = 5  # Trimsamsa has 5 slices regardless of irregular widths
    else:
        v_degree = _varga_degree_uniform(deg_in_sign, varga_num if varga_num != 1 else 1, seg_idx) if varga_num != 1 else deg_in_sign
        # For D1, degree is just degree_in_sign
        if varga_num == 1:
            v_degree = deg_in_sign
        seg_count = varga_num
        seg_size_val = seg_size

    # For D30, segment_count is 5 not 30 — override
    if varga_num == 30:
        seg_count_out = 5  # but keep varga_num as 30 for identity
        # segment_size is not uniform, store as NaN or actual slice width?
        # We store NaN to signal irregular; tests check via _trimsamsa_lookup
        seg_size_out = float("nan")
    else:
        seg_count_out = varga_num
        seg_size_out = seg_size_val

    # longitude convenience: (sign_num-1)*30 + degree
    # For D30, this is still defined as position inside sign
    v_longitude = (v_sign_num - 1) * 30.0 + v_degree

    return VargaPosition(
        varga=f"D{varga_num}",
        varga_num=varga_num,
        method=method_enum,
        source_longitude=lon_norm,
        source_sign=d1_sign_name,
        source_sign_num=d1_sign_num,
        source_degree=deg_in_sign,
        segment_index=seg_idx,
        segment_count=seg_count_out if varga_num != 30 else 5,
        segment_size=seg_size_out,
        sign=v_sign_name,
        sign_num=v_sign_num,
        degree=v_degree,
        longitude=_normalize_lon(v_longitude) if varga_num != 1 else lon_norm,
    )

# ---------------------------------------------------------------------------
# Public API 2: all vargas for a ChartFacts
# ---------------------------------------------------------------------------
def calculate_all_vargas(
    chart_facts: ChartFacts,
    profile: Optional[Any] = None,
) -> Dict[str, Dict[str, VargaPosition]]:
    """
    Derive all 16 vargas for every planet + ascendant from ChartFacts.

    Args:
        chart_facts: canonical ChartFacts from pipeline.generate_chart_facts()
        profile: CalculationProfile (optional) — reads varga_method if present.

    Returns:
        {
            "planets": { "Sun": { "D1": VargaPosition, "D2": ..., "D60": ... }, ... },
            "ascendant": { "D1": ..., "D60": ... }
        }
        Keys are 'D1'..'D60' per varga.

    No Swiss Ephemeris calls inside.
    """
    # Resolve method — single global or per-varga dict
    # profile may be ChartFacts.calculation_profile or explicit
    calc_profile = profile if profile is not None else chart_facts.calculation_profile
    # Support both CalculationProfile object and dict
    method_global = VargaMethod.PARASHARI_CLASSICAL
    per_varga_override: Dict[int, VargaMethod] = {}

    if calc_profile is not None:
        # Try attribute-style access
        vm = getattr(calc_profile, "varga_method", None)
        if vm is not None:
            if isinstance(vm, dict):
                # per-varga mapping like {"D9": "PARASHARI_CLASSICAL", 9: ...}
                for k, v in vm.items():
                    try:
                        # Normalize key to int
                        if isinstance(k, str):
                            ks = k.strip().upper().replace("D", "")
                            ki = int(ks)
                        else:
                            ki = int(k)
                        per_varga_override[ki] = VargaMethod(v) if isinstance(v, str) else v
                    except Exception:
                        continue
                method_global = VargaMethod.PARASHARI_CLASSICAL
            elif isinstance(vm, str):
                try:
                    method_global = VargaMethod(vm)
                except ValueError:
                    method_global = VargaMethod.PARASHARI_CLASSICAL
            elif isinstance(vm, VargaMethod):
                method_global = vm

        # Also handle legacy field `varga_methods` if present
        vm2 = getattr(calc_profile, "varga_methods", None)
        if isinstance(vm2, dict):
            for k, v in vm2.items():
                try:
                    if isinstance(k, str):
                        ks = k.strip().upper().replace("D", "")
                        ki = int(ks)
                    else:
                        ki = int(k)
                    per_varga_override[ki] = VargaMethod(v) if isinstance(v, str) else v
                except Exception:
                    continue

    def _method_for(vn: int) -> VargaMethod:
        return per_varga_override.get(vn, method_global)

    result: Dict[str, Dict[str, VargaPosition]] = {"planets": {}, "ascendant": {}}

    # Planets
    for p_name, p_data in chart_facts.planets.items():
        sid_lon = float(p_data.longitude.sidereal)
        per_planet: Dict[str, VargaPosition] = {}
        for vn in VALID_VARGAS:
            m = _method_for(vn)
            pos = calculate_varga_position(sid_lon, vn, m)
            per_planet[f"D{vn}"] = pos
        result["planets"][p_name] = per_planet

    # Ascendant
    asc_lon = float(chart_facts.ascendant.longitude.sidereal)
    per_asc: Dict[str, VargaPosition] = {}
    for vn in VALID_VARGAS:
        m = _method_for(vn)
        pos = calculate_varga_position(asc_lon, vn, m)
        per_asc[f"D{vn}"] = pos
    result["ascendant"] = per_asc

    return result

# ---------------------------------------------------------------------------
# Utility exposed for boundary handling (Step 21)
# ---------------------------------------------------------------------------
def varga_segment_index(degree_in_sign: float, division: int, epsilon: float = EPSILON) -> int:
    """Public boundary utility — tested independently."""
    # Use module epsilon if not overridden, but respect param
    old_eps = globals()["EPSILON"]
    try:
        globals()["EPSILON"] = epsilon
        return _segment_index_uniform(degree_in_sign, division)
    finally:
        globals()["EPSILON"] = old_eps

def varga_degree(degree_in_sign: float, division: int, segment_index: Optional[int] = None) -> float:
    """Public varga-degree utility for uniform divisions."""
    if segment_index is None:
        segment_index = _segment_index_uniform(degree_in_sign, division)
    return _varga_degree_uniform(degree_in_sign, division, segment_index)
