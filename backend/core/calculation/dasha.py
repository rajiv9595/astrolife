"""
Vimshottari Dasha Engine — Pure, Deterministic (Phase 3)

Architecture:
  ChartFacts (static natal) + evaluation_datetime -> DashaState
  No clock read inside. No globals. Full precision internally.

Year model: controlled by DashaCalculationProfile.days_per_year (default 365.2425).
Boundary: half-open [start, end) — start inclusive, end exclusive. Documented explicitly.
  Tests must verify exact start boundary is inside, exact end is outside (next period).

Levels: Mahadasha (MD) -> Antardasha (AD) -> Pratyantardasha (PD) -> Sookshma -> Prana
Each level divides parent proportionally: lordYears * parentYears / 120.

Source of truth: ChartFacts.planets["Moon"].longitude.sidereal + nakshatra fraction.
Does NOT recalculate Moon longitude.

Precision: keep JD as float64 internally, never round before recursion. Round only for display.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import math
import pytz
import swisseph as swe

from .config import DashaCalculationProfile, DEFAULT_DASHA_PROFILE
from .models import ChartFacts
from .time_utils import get_utc_and_julian_day

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VIMSHOTTARI_ORDER: List[str] = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSHOTTARI_YEARS: Dict[str, float] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10,
    "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}
TOTAL_CYCLE = 120.0
NAK_SIZE = 360.0 / 27.0  # 13.333...

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class DashaPeriod(BaseModel):
    """
    Generic period at any level.
    level: 1=MD, 2=AD, 3=PD, 4=Sookshma, 5=Prana
    """
    level: int = Field(description="1=MD 2=AD 3=PD 4=Sookshma 5=Prana")
    lord: str
    start_jd: float
    end_jd: float
    start_utc_iso: str
    end_utc_iso: str
    duration_years: float  # full precision double, not rounded
    duration_days: float
    parent_lord: Optional[str] = None
    index_in_parent: Optional[int] = None  # 0..8
    is_partial: bool = False  # only MD level can be partial at birth

class DashaTimeline(BaseModel):
    birth_jd: float
    birth_utc_iso: str
    moon_nakshatra_index: int  # 0..26
    moon_nakshatra_name: str
    moon_nakshatra_fraction: float
    starting_lord: str
    remaining_years_at_birth: float
    profile_used: DashaCalculationProfile
    mahadashas: List[Dict[str, Any]]  # each contains DashaPeriod + antar_dashas
    total_years_calculated: float
    boundary_convention: str = "[start_jd, end_jd) half-open — start inclusive, end exclusive"

# ---------------------------------------------------------------------------
# Helpers — pure
# ---------------------------------------------------------------------------
def _normalize_deg(d: float) -> float:
    return float(d) % 360.0

def _jd_to_utc_datetime(jd: float) -> datetime:
    """Convert JD to timezone-aware UTC datetime preserving fractional seconds."""
    y, m, d, h_dec = swe.revjul(jd, swe.GREG_CAL)
    h = int(math.floor(h_dec))
    min_dec = (h_dec - h) * 60.0
    mi = int(math.floor(min_dec))
    sec_dec = (min_dec - mi) * 60.0
    # preserve sub-second
    sec_int = int(math.floor(sec_dec))
    micro = int(round((sec_dec - sec_int) * 1_000_000))
    # carry
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
        h = 23
        mi = 59
        sec_int = 59
        micro = 999999
    try:
        return datetime(y, m, d, h, mi, sec_int, micro, tzinfo=timezone.utc)
    except ValueError:
        return datetime(1900, 1, 1, tzinfo=timezone.utc)

def _jd_to_utc_iso(jd: float) -> str:
    return _jd_to_utc_datetime(jd).isoformat().replace("+00:00", "Z")

def _evaluation_jd(evaluation_datetime: datetime) -> float:
    """
    Convert evaluation_datetime (aware or naive assumed UTC) to JD (UT).
    No clock read.
    """
    if evaluation_datetime.tzinfo is None:
        dt_utc = evaluation_datetime.replace(tzinfo=timezone.utc)
    else:
        dt_utc = evaluation_datetime.astimezone(timezone.utc)
    ut_dec = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0 + dt_utc.microsecond / 3600.0 / 1_000_000.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut_dec, swe.GREG_CAL)

def _moon_nakshatra_fraction(moon_sidereal_lon: float):
    lon = _normalize_deg(moon_sidereal_lon)
    nak_float = lon / NAK_SIZE
    nak_idx = int(math.floor(nak_float))
    fraction = nak_float - nak_idx
    return nak_idx, fraction

def _build_sublevels(parent_lord: str, parent_years: float, parent_start_jd: float, parent_level: int, profile: DashaCalculationProfile) -> List[Dict[str, Any]]:
    """
    Build 9 subperiods for a given parent period (pure).
    Returns list of dicts each with period + next-level children (if applicable).
    Does NOT apply birth slicing — caller does that for partial MD.
    Full precision: uses parent_years double directly.
    """
    days_per_year = profile.days_per_year
    seq = VIMSHOTTARI_ORDER
    start_idx = seq.index(parent_lord)
    cursor = parent_start_jd
    result: List[Dict[str, Any]] = []
    for i in range(len(seq)):
        lord = seq[(start_idx + i) % len(seq)]
        lord_full = VIMSHOTTARI_YEARS[lord]
        duration_years = (lord_full * parent_years) / TOTAL_CYCLE  # full precision
        duration_days = duration_years * days_per_year
        end_jd = cursor + duration_days
        level = parent_level + 1
        period = DashaPeriod(
            level=level,
            lord=lord,
            start_jd=cursor,
            end_jd=end_jd,
            start_utc_iso=_jd_to_utc_iso(cursor),
            end_utc_iso=_jd_to_utc_iso(end_jd),
            duration_years=duration_years,
            duration_days=duration_days,
            parent_lord=parent_lord,
            index_in_parent=i,
            is_partial=False
        )
        # Build next level if not yet at Prana (level 5)
        children: List[Dict[str, Any]] = []
        if level < 5:  # AD -> PD -> Sookshma -> Prana
            # recursively build one more level down
            children = _build_sublevels(lord, duration_years, cursor, level, profile)
        entry: Dict[str, Any] = {
            "period": period,
            "children": children
        }
        result.append(entry)
        cursor = end_jd
    return result

def _flatten_children(children: List[Dict[str, Any]]) -> List[DashaPeriod]:
    return [c["period"] for c in children]

# ---------------------------------------------------------------------------
# Public API 1: pure timeline generation consuming ChartFacts
# ---------------------------------------------------------------------------
def calculate_vimshottari_timeline(
    chart_facts: ChartFacts,
    profile: Optional[DashaCalculationProfile] = None,
    years_ahead: float = 120.0,
    # alternative explicit range:
    start_jd_override: Optional[float] = None,
    end_jd_override: Optional[float] = None,
) -> DashaTimeline:
    """
    Pure function: derive Vimshottari timeline from canonical ChartFacts.
    No clock read. No globals.

    Args:
        chart_facts: canonical ChartFacts (birth). Moon sidereal used to derive starting lord and balance.
        profile: DashaCalculationProfile or None -> DEFAULT_DASHA_PROFILE
        years_ahead: how many years ahead from birth to generate (default 120 = one full cycle)
        start_jd_override / end_jd_override: if provided, generate from/to those JDs instead of years_ahead
            (allows callers to request arbitrary calendar bounds per Step 3 example).

    Returns:
        DashaTimeline Pydantic model with nested structure.

    Boundary: [start_jd, end_jd) half-open.
    """
    if profile is None:
        # Use chart_facts profile if present
        try:
            p = getattr(chart_facts.calculation_profile, "dasha_profile", None)
            profile = p if p is not None else DEFAULT_DASHA_PROFILE
        except Exception:
            profile = DEFAULT_DASHA_PROFILE
    days_per_year = profile.days_per_year

    jd_birth = float(chart_facts.time.julian_day)
    # Prefer canonical moon sidereal from ChartFacts
    try:
        moon_lon = float(chart_facts.planets["Moon"].longitude.sidereal)
    except Exception as e:
        raise ValueError(f"ChartFacts missing Moon longitude: {e}")

    return _calculate_timeline_from_birth_params(
        jd_birth=jd_birth,
        moon_sidereal_lon=moon_lon,
        profile=profile,
        years_ahead=years_ahead,
        start_jd_override=start_jd_override,
        end_jd_override=end_jd_override,
    )

def _calculate_timeline_from_birth_params(
    jd_birth: float,
    moon_sidereal_lon: float,
    profile: DashaCalculationProfile,
    years_ahead: float = 120.0,
    start_jd_override: Optional[float] = None,
    end_jd_override: Optional[float] = None,
) -> DashaTimeline:
    days_per_year = profile.days_per_year
    nak_idx, fraction = _moon_nakshatra_fraction(moon_sidereal_lon)
    # Nakshatra names for display
    from .nakshatra import NAKSHATRA_NAMES
    nak_name = NAKSHATRA_NAMES[nak_idx]

    from .nakshatra import NAKSHATRA_LORDS
    lord = NAKSHATRA_LORDS[nak_idx]
    full_years = VIMSHOTTARI_YEARS[lord]
    remaining_years = (1.0 - fraction) * full_years
    seq = VIMSHOTTARI_ORDER
    start_idx = seq.index(lord)

    # Determine generation window
    if start_jd_override is not None or end_jd_override is not None:
        gen_start = start_jd_override if start_jd_override is not None else jd_birth
        if end_jd_override is not None:
            gen_end = end_jd_override
        else:
            gen_end = jd_birth + years_ahead * days_per_year
    else:
        gen_start = jd_birth
        gen_end = jd_birth + years_ahead * days_per_year

    mahadashas: List[Dict[str, Any]] = []
    cursor = jd_birth  # MD timeline always starts at birth

    # First MD is partial
    first_end = cursor + remaining_years * days_per_year
    # If generation window starts after first_end, we still need to walk correctly
    # Build MD list sequentially in chronological order
    i = 0
    # We need to handle the case where gen_start is before jd_birth (historical) — include earlier? For now start at birth; historical dasha before birth is previous MDs. Not required for Phase 3 but support if needed.
    # If start_jd_override < jd_birth, we need to generate backwards
    if gen_start < jd_birth - 1e-9:
        # backward generation: find how many MDs before birth cover gen_start
        # Walk backwards from birth
        back_cursor = jd_birth
        back_i = 0
        back_mds: List[Dict[str, Any]] = []
        # We know first MD's full start = jd_birth - (full_years - remaining_years)*days
        # So we can iterate backward
        temp_cursor = jd_birth
        temp_i = 0
        # Build a small list of MDs backward until gen_start
        # Approach: generate sequentially forward from some earlier point, easier to brute-force by iterating backwards through seq
        # Compute full MDs backwards:
        rev_mds: List[Tuple[str, float]] = []  # (lord, full_years)
        # Collect MDs backwards
        # First, the partial MD's start:
        full_start_of_first = jd_birth - (full_years - remaining_years) * days_per_year
        # For MD generation, we need to know MD lords preceding start lord in reverse order
        # Sequence is cyclic forward: ... Mercury -> Ketu -> Venus -> Sun -> Moon -> Mars -> Rahu -> Jupiter -> Saturn -> Mercury ...
        # So backwards from lord: index-1 mod 9
        # Prepend earlier MDs until their start < gen_start
        earlier_start = full_start_of_first
        earlier_idx = start_idx
        # Already have first MD from earlier_start with full span? But we expose timeline as starting at birth, so earlier_start is not exposed as partial; but if gen_start < jd_birth we want those earlier MDs.
        # Let's generate backward MDs in reverse and then reverse to chronological
        backward_defs: List[Tuple[str, float, float, float]] = []  # lord, full_years, start_jd, end_jd
        cur_start = full_start_of_first
        cur_lord_idx = start_idx
        cur_full = full_years
        # cur MD is the one containing birth, its window is [cur_start, cur_start + full*dpy) but we expose only [jd_birth, cur_start+full) as first MD partial
        # For full backward, we want MDs before cur
        # We'll walk backwards: previous lord = (cur_idx -1) %9
        prev_cursor_start = cur_start
        while prev_cursor_start > gen_start:
            prev_idx = (cur_lord_idx - 1) % 9
            prev_lord = seq[prev_idx]
            prev_years = VIMSHOTTARI_YEARS[prev_lord]
            prev_start = prev_cursor_start - prev_years * days_per_year
            backward_defs.append((prev_lord, prev_years, prev_start, prev_cursor_start))
            prev_cursor_start = prev_start
            cur_lord_idx = prev_idx
        # Reverse to chronological
        backward_defs.reverse()
        for lord_b, yrs_b, s_jd, e_jd in backward_defs:
            # Build children for these earlier MDs (full)
            children = _build_sublevels(lord_b, yrs_b, s_jd, parent_level=1, profile=profile)
            # Wrap with DashaPeriod at level 1
            md_period = DashaPeriod(
                level=1, lord=lord_b, start_jd=s_jd, end_jd=e_jd,
                start_utc_iso=_jd_to_utc_iso(s_jd), end_utc_iso=_jd_to_utc_iso(e_jd),
                duration_years=yrs_b, duration_days=yrs_b * days_per_year,
                parent_lord=None, index_in_parent=None, is_partial=False
            )
            mahadashas.append({
                "period": md_period,
                "antar_dashas": children,  # level 2 entries each with children level3 etc
            })
        # After backwards, reset cursor handling for first MD
        # First MD will be handled as partial below; cursor = jd_birth

    # Now forward generation from birth inclusive
    # First MD (partial)
    if first_end > gen_start and cursor < gen_end:
        # Determine intersection with [gen_start, gen_end)
        disp_start = max(cursor, gen_start)
        disp_end = min(first_end, gen_end)
        if disp_end > disp_start:
            # For display, period's JD should be sliced to intersection? But for MD semantics, the true MD is [cursor, first_end) — slicing should reflect remaining view
            # Spec says timeline from start_date to end_date — so we should slice if gen window clips
            # For birth-aligned window (gen_start==birth), disp == full partial
            # So we will store the MD as [cursor, first_end) if within generation, but if gen clipped, we adjust?
            # Simpler: store as [cursor, first_end) and let filtering happen at get_current_dasha? But caller requested range filtering
            # Instead we store sliced to intersect so callers see only requested range.
            # Use true MD boundaries for internal children slicing below accordingly.
            true_start = cursor
            true_end = first_end
            # Build antar children from true MD start (full MD start -> full_start_of_first)
            full_start_of_first = cursor - (full_years - remaining_years) * days_per_year
            # Generate full antar set from full_start
            full_antars = _build_sublevels(lord, full_years, full_start_of_first, parent_level=1, profile=profile)
            # Slice antars to [disp_start, disp_end)
            # Keep only those overlapping and slice periods to overlap window? The overlap antar should be clipped to parent remaining.
            sliced_antars: List[Dict[str, Any]] = []
            for ad_entry in full_antars:
                ad_period: DashaPeriod = ad_entry["period"]
                if ad_period.end_jd <= cursor or ad_period.start_jd >= true_end:
                    continue
                # intersection with [true_start(=cursor), true_end)
                ad_s = max(ad_period.start_jd, true_start)
                ad_e = min(ad_period.end_jd, true_end)
                if ad_s >= ad_e:
                    continue
                # Intersect further with generation window [gen_start, gen_end)
                ad_s2 = max(ad_s, gen_start)
                ad_e2 = min(ad_e, gen_end)
                if ad_s2 >= ad_e2:
                    continue
                # Clone period with sliced JDs if partial at edges? But internal duration should reflect sliced window or true?
                # For correctness we keep true period JDs for sublevels? Simpler to keep sliced as displayed.
                # However children (PD etc) must be sliced consistently to the sliced antar window.
                # So we slice AD to [ad_s, ad_e) intersecting true MD remaining, then filter its children (PDs) to that slice.
                is_ad_partial = (ad_s != ad_period.start_jd) or (ad_e != ad_period.end_jd)
                sliced_ad = DashaPeriod(
                    level=ad_period.level,
                    lord=ad_period.lord,
                    start_jd=ad_s2 if gen_start != cursor else ad_s,  # if gen window clips further, use gen clipped
                    end_jd=ad_e2 if gen_end != true_end else ad_e,
                    start_utc_iso=_jd_to_utc_iso(ad_s2 if gen_start != cursor else ad_s),
                    end_utc_iso=_jd_to_utc_iso(ad_e2 if gen_end != true_end else ad_e),
                    duration_years=(ad_e - ad_s) / days_per_year,  # sliced duration (remaining part)
                    duration_days=ad_e - ad_s,
                    parent_lord=lord,
                    index_in_parent=ad_period.index_in_parent,
                    is_partial=is_ad_partial
                )
                # Now need to slice PD children of this AD
                # Original PDs are stored in ad_entry["children"] (level 3)
                pd_children: List[Dict[str, Any]] = ad_entry["children"]
                sliced_pds: List[Dict[str, Any]] = []
                for pd_entry in pd_children:
                    pd_period: DashaPeriod = pd_entry["period"]
                    if pd_period.end_jd <= ad_s or pd_period.start_jd >= ad_e:
                        continue
                    pd_s = max(pd_period.start_jd, ad_s)
                    pd_e = min(pd_period.end_jd, ad_e)
                    # generation window clip
                    pd_s2 = max(pd_s, gen_start)
                    pd_e2 = min(pd_e, gen_end)
                    if pd_s2 >= pd_e2:
                        continue
                    is_pd_partial = (pd_s != pd_period.start_jd) or (pd_e != pd_period.end_jd)
                    sliced_pd = DashaPeriod(
                        level=pd_period.level, lord=pd_period.lord,
                        start_jd=pd_s2 if gen_start != cursor else pd_s,
                        end_jd=pd_e2 if gen_end != true_end else pd_e,
                        start_utc_iso=_jd_to_utc_iso(pd_s2 if gen_start != cursor else pd_s),
                        end_utc_iso=_jd_to_utc_iso(pd_e2 if gen_end != true_end else pd_e),
                        duration_years=(pd_e - pd_s) / days_per_year,
                        duration_days=pd_e - pd_s,
                        parent_lord=ad_period.lord,
                        index_in_parent=pd_period.index_in_parent,
                        is_partial=is_pd_partial
                    )
                    # Sookshma level (4) children of this PD
                    sook_children = pd_entry["children"]
                    sliced_sooks: List[Dict[str, Any]] = []
                    for sook_entry in sook_children:
                        sook_period: DashaPeriod = sook_entry["period"]
                        if sook_period.end_jd <= pd_s or sook_period.start_jd >= pd_e:
                            continue
                        sook_s = max(sook_period.start_jd, pd_s)
                        sook_e = min(sook_period.end_jd, pd_e)
                        sook_s2 = max(sook_s, gen_start)
                        sook_e2 = min(sook_e, gen_end)
                        if sook_s2 >= sook_e2:
                            continue
                        is_sook_partial = (sook_s != sook_period.start_jd) or (sook_e != sook_period.end_jd)
                        sliced_sook = DashaPeriod(
                            level=sook_period.level, lord=sook_period.lord,
                            start_jd=sook_s2 if gen_start != cursor else sook_s,
                            end_jd=sook_e2 if gen_end != true_end else sook_e,
                            start_utc_iso=_jd_to_utc_iso(sook_s2 if gen_start != cursor else sook_s),
                            end_utc_iso=_jd_to_utc_iso(sook_e2 if gen_end != true_end else sook_e),
                            duration_years=(sook_e - sook_s) / days_per_year,
                            duration_days=sook_e - sook_s,
                            parent_lord=pd_period.lord,
                            index_in_parent=sook_period.index_in_parent,
                            is_partial=is_sook_partial
                        )
                        # Prana children of sookshma (level 5)
                        prana_children = sook_entry["children"]
                        sliced_pranas: List[Dict[str, Any]] = []
                        for prana_entry in prana_children:
                            prana_period: DashaPeriod = prana_entry["period"]
                            if prana_period.end_jd <= sook_s or prana_period.start_jd >= sook_e:
                                continue
                            prana_s = max(prana_period.start_jd, sook_s)
                            prana_e = min(prana_period.end_jd, sook_e)
                            prana_s2 = max(prana_s, gen_start)
                            prana_e2 = min(prana_e, gen_end)
                            if prana_s2 >= prana_e2:
                                continue
                            is_prana_partial = (prana_s != prana_period.start_jd) or (prana_e != prana_period.end_jd)
                            sliced_prana = DashaPeriod(
                                level=prana_period.level, lord=prana_period.lord,
                                start_jd=prana_s2 if gen_start != cursor else prana_s,
                                end_jd=prana_e2 if gen_end != true_end else prana_e,
                                start_utc_iso=_jd_to_utc_iso(prana_s2 if gen_start != cursor else prana_s),
                                end_utc_iso=_jd_to_utc_iso(prana_e2 if gen_end != true_end else prana_e),
                                duration_years=(prana_e - prana_s) / days_per_year,
                                duration_days=prana_e - prana_s,
                                parent_lord=sook_period.lord,
                                index_in_parent=prana_period.index_in_parent,
                                is_partial=is_prana_partial
                            )
                            sliced_pranas.append({"period": sliced_prana, "children": []})
                        sliced_sooks.append({"period": sliced_sook, "children": sliced_pranas})
                    sliced_pds.append({"period": sliced_pd, "children": sliced_sooks})
                sliced_antars.append({"period": sliced_ad, "children": sliced_pds})
            # Build MD period display-sliced
            md_period = DashaPeriod(
                level=1, lord=lord, start_jd=disp_start, end_jd=disp_end,
                start_utc_iso=_jd_to_utc_iso(disp_start), end_utc_iso=_jd_to_utc_iso(disp_end),
                duration_years=(disp_end - disp_start) / days_per_year,
                duration_days=disp_end - disp_start,
                parent_lord=None, index_in_parent=None,
                is_partial=True
            )
            mahadashas.append({
                "period": md_period,
                "antar_dashas": sliced_antars,
            })
    cursor = first_end

    # Subsequent full MDs
    i = 1
    while cursor < gen_end - 1e-12:
        if cursor < gen_start:
            # skip until overlap
            # compute end of this MD
            p_lord = seq[(start_idx + i) % len(seq)]
            p_yrs = VIMSHOTTARI_YEARS[p_lord]
            p_end = cursor + p_yrs * days_per_year
            if p_end <= gen_start:
                cursor = p_end
                i += 1
                continue
            # if this MD overlaps gen_start, slicing needed
            # else proceed to slicing logic below
        p_lord = seq[(start_idx + i) % len(seq)]
        p_yrs = VIMSHOTTARI_YEARS[p_lord]
        p_end = cursor + p_yrs * days_per_year
        # slice to generation window
        disp_s = max(cursor, gen_start)
        disp_e = min(p_end, gen_end)
        if disp_s >= disp_e:
            cursor = p_end
            i += 1
            continue
        # Build full sublevels for this MD
        full_children = _build_sublevels(p_lord, p_yrs, cursor, parent_level=1, profile=profile)
        # full_children is list of AD entries with nested PDS/sooks/pranas already covering [cursor, p_end)
        # If generation window clips this MD, need to filter children to [disp_s, disp_e)
        if disp_s == cursor and disp_e == p_end:
            # no clipping of children needed
            sliced_antars_full = full_children  # each entry {"period":..., "children": [...]}
            # but full_children periods already have absolute JDs correctly covering entire MD
            # Convert to expected antars shape: keep as is but ensure is_partial False
            filtered_antars = sliced_antars_full
        else:
            # clipping
            filtered_antars: List[Dict[str, Any]] = []
            for ad_entry in full_children:
                ad_period: DashaPeriod = ad_entry["period"]
                if ad_period.end_jd <= disp_s or ad_period.start_jd >= disp_e:
                    continue
                ad_s = max(ad_period.start_jd, disp_s)
                ad_e = min(ad_period.end_jd, disp_e)
                if ad_s >= ad_e:
                    continue
                is_partial = (ad_s != ad_period.start_jd) or (ad_e != ad_period.end_jd)
                sliced_ad = DashaPeriod(
                    level=ad_period.level, lord=ad_period.lord,
                    start_jd=ad_s, end_jd=ad_e,
                    start_utc_iso=_jd_to_utc_iso(ad_s), end_utc_iso=_jd_to_utc_iso(ad_e),
                    duration_years=(ad_e - ad_s) / days_per_year,
                    duration_days=ad_e - ad_s,
                    parent_lord=p_lord, index_in_parent=ad_period.index_in_parent,
                    is_partial=is_partial
                )
                # PDs similarly filtered
                pd_children = ad_entry["children"]
                filtered_pds: List[Dict[str, Any]] = []
                for pd_entry in pd_children:
                    pd_period: DashaPeriod = pd_entry["period"]
                    if pd_period.end_jd <= ad_s or pd_period.start_jd >= ad_e:
                        continue
                    pd_s = max(pd_period.start_jd, ad_s)
                    pd_e = min(pd_period.end_jd, ad_e)
                    if pd_s >= pd_e:
                        continue
                    is_pd_partial = (pd_s != pd_period.start_jd) or (pd_e != pd_period.end_jd)
                    sliced_pd = DashaPeriod(
                        level=pd_period.level, lord=pd_period.lord,
                        start_jd=pd_s, end_jd=pd_e,
                        start_utc_iso=_jd_to_utc_iso(pd_s), end_utc_iso=_jd_to_utc_iso(pd_e),
                        duration_years=(pd_e - pd_s) / days_per_year,
                        duration_days=pd_e - pd_s,
                        parent_lord=ad_period.lord, index_in_parent=pd_period.index_in_parent,
                        is_partial=is_pd_partial
                    )
                    sook_children = pd_entry["children"]
                    filtered_sooks: List[Dict[str, Any]] = []
                    for sook_entry in sook_children:
                        sook_period: DashaPeriod = sook_entry["period"]
                        if sook_period.end_jd <= pd_s or sook_period.start_jd >= pd_e:
                            continue
                        sook_s = max(sook_period.start_jd, pd_s)
                        sook_e = min(sook_period.end_jd, pd_e)
                        if sook_s >= sook_e:
                            continue
                        is_sook_partial = (sook_s != sook_period.start_jd) or (sook_e != sook_period.end_jd)
                        sliced_sook = DashaPeriod(
                            level=sook_period.level, lord=sook_period.lord,
                            start_jd=sook_s, end_jd=sook_e,
                            start_utc_iso=_jd_to_utc_iso(sook_s), end_utc_iso=_jd_to_utc_iso(sook_e),
                            duration_years=(sook_e - sook_s) / days_per_year,
                            duration_days=sook_e - sook_s,
                            parent_lord=pd_period.lord, index_in_parent=sook_period.index_in_parent,
                            is_partial=is_sook_partial
                        )
                        prana_children = sook_entry["children"]
                        filtered_pranas: List[Dict[str, Any]] = []
                        for prana_entry in prana_children:
                            prana_period: DashaPeriod = prana_entry["period"]
                            if prana_period.end_jd <= sook_s or prana_period.start_jd >= sook_e:
                                continue
                            prana_s = max(prana_period.start_jd, sook_s)
                            prana_e = min(prana_period.end_jd, sook_e)
                            if prana_s >= prana_e:
                                continue
                            is_prana_partial = (prana_s != prana_period.start_jd) or (prana_e != prana_period.end_jd)
                            sliced_prana = DashaPeriod(
                                level=prana_period.level, lord=prana_period.lord,
                                start_jd=prana_s, end_jd=prana_e,
                                start_utc_iso=_jd_to_utc_iso(prana_s), end_utc_iso=_jd_to_utc_iso(prana_e),
                                duration_years=(prana_e - prana_s) / days_per_year,
                                duration_days=prana_e - prana_s,
                                parent_lord=sook_period.lord, index_in_parent=prana_period.index_in_parent,
                                is_partial=is_prana_partial
                            )
                            filtered_pranas.append({"period": sliced_prana, "children": []})
                        filtered_sooks.append({"period": sliced_sook, "children": filtered_pranas})
                    filtered_pds.append({"period": sliced_pd, "children": filtered_sooks})
                filtered_antars.append({"period": sliced_ad, "children": filtered_pds})
        md_period = DashaPeriod(
            level=1, lord=p_lord, start_jd=disp_s, end_jd=disp_e,
            start_utc_iso=_jd_to_utc_iso(disp_s), end_utc_iso=_jd_to_utc_iso(disp_e),
            duration_years=(disp_e - disp_s) / days_per_year,
            duration_days=disp_e - disp_s,
            parent_lord=None, index_in_parent=None,
            is_partial=(disp_s != cursor or disp_e != p_end)
        )
        mahadashas.append({
            "period": md_period,
            "antar_dashas": filtered_antars if (disp_s != cursor or disp_e != p_end) else full_children
        })
        cursor = p_end
        i += 1
        if i > 50:  # safety
            break

    # Total years is sum of displayed MD durations (exactly covers generation window)
    total_years = sum(m["period"].duration_years for m in mahadashas) if mahadashas else (gen_end - gen_start) / days_per_year

    return DashaTimeline(
        birth_jd=jd_birth,
        birth_utc_iso=_jd_to_utc_iso(jd_birth),
        moon_nakshatra_index=nak_idx,
        moon_nakshatra_name=nak_name,
        moon_nakshatra_fraction=fraction,
        starting_lord=lord,
        remaining_years_at_birth=remaining_years,
        profile_used=profile,
        mahadashas=mahadashas,
        total_years_calculated=round(float(total_years), 4),
        boundary_convention="[start_jd, end_jd) half-open — start inclusive, end exclusive"
    )

# ---------------------------------------------------------------------------
# Public API 2: pure selector — no clock
# ---------------------------------------------------------------------------
def get_current_dasha(
    dasha_timeline: DashaTimeline,
    evaluation_datetime: datetime,
) -> Dict[str, Any]:
    """
    Pure selector: given a precomputed DashaTimeline and an explicit evaluation_datetime,
    return current period at each level.
    Convention: half-open [start, end) — at exact boundary, the *next* period is current
    (because previous end is exclusive). This matches sweep of time continuously.

    Returns dict with keys:
      mahadasha, antardasha, pratyantardasha, sookshma, prana
    each is DashaPeriod or None.
    Also returns "hierarchy": list of lords from MD down.
    """
    jd_eval = _evaluation_jd(evaluation_datetime)
    result: Dict[str, Any] = {
        "evaluation_jd": jd_eval,
        "evaluation_utc_iso": _jd_to_utc_iso(jd_eval),
        "mahadasha": None,
        "antardasha": None,
        "pratyantardasha": None,
        "sookshma": None,
        "prana": None,
        "hierarchy": [],
    }

    # Find MD
    md_match = None
    md_entry = None
    for entry in dasha_timeline.mahadashas:
        p: DashaPeriod = entry["period"]
        if p.start_jd <= jd_eval < p.end_jd:
            md_match = p
            md_entry = entry
            break
        # edge: exactly at timeline start before first MD? no
        # if jd_eval < first start, no match -> before birth
        # if jd_eval >= last end -> after timeline, handle below
    if md_match is None:
        # Check before/after
        if dasha_timeline.mahadashas:
            first_p = dasha_timeline.mahadashas[0]["period"]
            last_p = dasha_timeline.mahadashas[-1]["period"]
            if jd_eval < first_p.start_jd:
                result["note"] = "evaluation before birth/start"
                return result
            if jd_eval >= last_p.end_jd:
                result["note"] = "evaluation beyond calculated timeline — extend years_ahead"
                # optionally return last
                # For determinism, return None for all levels beyond
                return result
        return result

    result["mahadasha"] = md_match
    result["hierarchy"].append(md_match.lord)

    antars = md_entry.get("antar_dashas", []) if md_entry else []
    ad_match = None
    ad_entry = None
    for ad in antars:
        p: DashaPeriod = ad["period"]
        if p.start_jd <= jd_eval < p.end_jd:
            ad_match = p
            ad_entry = ad
            break
    if ad_match:
        result["antardasha"] = ad_match
        result["hierarchy"].append(ad_match.lord)
    else:
        return result

    pds = ad_entry.get("children", []) if ad_entry else []
    pd_match = None
    pd_entry = None
    for pd in pds:
        p: DashaPeriod = pd["period"]
        if p.start_jd <= jd_eval < p.end_jd:
            pd_match = p
            pd_entry = pd
            break
    if pd_match:
        result["pratyantardasha"] = pd_match
        result["hierarchy"].append(pd_match.lord)
    else:
        return result

    sooks = pd_entry.get("children", []) if pd_entry else []
    sook_match = None
    sook_entry = None
    for sook in sooks:
        p: DashaPeriod = sook["period"]
        if p.start_jd <= jd_eval < p.end_jd:
            sook_match = p
            sook_entry = sook
            break
    if sook_match:
        result["sookshma"] = sook_match
        result["hierarchy"].append(sook_match.lord)
    else:
        return result

    pranas = sook_entry.get("children", []) if sook_entry else []
    prana_match = None
    for pr in pranas:
        p: DashaPeriod = pr["period"]
        if p.start_jd <= jd_eval < p.end_jd:
            prana_match = p
            break
    if prana_match:
        result["prana"] = prana_match
        result["hierarchy"].append(prana_match.lord)

    return result

# ---------------------------------------------------------------------------
# Backward-compatible shim for calculations.py
# ---------------------------------------------------------------------------
def legacy_compute_vimshottari_timeline_shim(jd_birth: float, moon_sidereal_lon: float, years_ahead: int = 100, tz_name: str = "UTC", profile: Optional[DashaCalculationProfile] = None) -> Dict[str, Any]:
    """
    Produces legacy-shaped dict for calculations.compute_vimshottari_timeline compatibility.
    Includes nakshatra_of_moon and timeline list with is_partial/antar_dashas etc.
    Does NOT set is_current — caller must use get_current_dasha separately.
    Kept for backward compat only.
    """
    from .nakshatra import NAKSHATRA_NAMES, NAKSHATRA_LORDS, get_nakshatra_from_longitude
    nak = get_nakshatra_from_longitude(moon_sidereal_lon)
    if profile is None:
        profile = DEFAULT_DASHA_PROFILE
    # Minimal ChartFacts stub for timeline generation
    # Instead directly use internal builder
    tl = _calculate_timeline_from_birth_params(jd_birth=jd_birth, moon_sidereal_lon=moon_sidereal_lon, profile=profile, years_ahead=float(years_ahead))
    # Convert to legacy dict shape expected by compute_chart and tests that read vimshottari timeline
    # Legacy expects: {"nakshatra_of_moon": nak_dict, "timeline": [ {lord,start_jd,end_jd,start_date,end_date,years,is_partial,is_current,start_age,end_age,antar_dashas:[{lord,start_jd,end_jd,start_date,end_date,years,is_current,pratyantar_dashas:...}]} ]}
    # We'll produce timeline with antar/pratyantar/sookshma nesting compatible with legacy shape but using UTC iso strings (legacy used local via _active_tz)
    # For compat we will map start_date/end_date as UTC iso (legacy used local iso via jd_to_local_iso)
    # Also compute start_age/end_age
    days_per_year = profile.days_per_year
    legacy_timeline = []
    for md_entry in tl.mahadashas:
        md_p: DashaPeriod = md_entry["period"]
        antar_list = []
        for ad_entry in md_entry.get("antar_dashas", []):
            ad_p: DashaPeriod = ad_entry["period"]
            praty_list = []
            for pd_entry in ad_entry.get("children", []):
                pd_p: DashaPeriod = pd_entry["period"]
                sook_list = []
                for sook_entry in pd_entry.get("children", []):
                    sook_p: DashaPeriod = sook_entry["period"]
                    prana_list = []
                    for prana_entry in sook_entry.get("children", []):
                        prana_p: DashaPeriod = prana_entry["period"]
                        prana_list.append({
                            "lord": prana_p.lord,
                            "start_jd": prana_p.start_jd,
                            "end_jd": prana_p.end_jd,
                            "start_date": prana_p.start_utc_iso,
                            "end_date": prana_p.end_utc_iso,
                            "years": round(prana_p.duration_years, 10),
                            "is_current": False,
                            "is_partial": prana_p.is_partial,
                        })
                    sook_list.append({
                        "lord": sook_p.lord,
                        "start_jd": sook_p.start_jd,
                        "end_jd": sook_p.end_jd,
                        "start_date": sook_p.start_utc_iso,
                        "end_date": sook_p.end_utc_iso,
                        "years": round(sook_p.duration_years, 8),
                        "is_current": False,
                        "is_partial": sook_p.is_partial,
                        "prana_dashas": prana_list,
                    })
                praty_list.append({
                    "lord": pd_p.lord,
                    "start_jd": pd_p.start_jd,
                    "end_jd": pd_p.end_jd,
                    "start_date": pd_p.start_utc_iso,
                    "end_date": pd_p.end_utc_iso,
                    "years": round(pd_p.duration_years, 6),
                    "is_current": False,
                    "is_partial": pd_p.is_partial,
                    "sookshma_dashas": sook_list,
                })
            antar_list.append({
                "lord": ad_p.lord,
                "start_jd": ad_p.start_jd,
                "end_jd": ad_p.end_jd,
                "start_date": ad_p.start_utc_iso,
                "end_date": ad_p.end_utc_iso,
                "years": round(ad_p.duration_years, 6),
                "is_current": False,
                "is_partial": ad_p.is_partial,
                "pratyantar_dashas": praty_list,
            })
        # ages
        start_age = (md_p.start_jd - jd_birth) / days_per_year
        end_age = (md_p.end_jd - jd_birth) / days_per_year
        legacy_timeline.append({
            "lord": md_p.lord,
            "start_jd": md_p.start_jd,
            "end_jd": md_p.end_jd,
            "start_date": md_p.start_utc_iso,
            "end_date": md_p.end_utc_iso,
            "years": round(md_p.duration_years, 4) if md_p.is_partial else int(round(md_p.duration_years)),
            "is_partial": md_p.is_partial,
            "is_current": False,
            "start_age": round(start_age, 2),
            "end_age": round(end_age, 2),
            "antar_dashas": antar_list,
        })
    return {
        "nakshatra_of_moon": {
            "nakshatra_index": nak.id - 1 if hasattr(nak, "id") else tl.moon_nakshatra_index,
            "nakshatra": nak.name if hasattr(nak, "name") else tl.moon_nakshatra_name,
            "pada": nak.pada if hasattr(nak, "pada") else None,
            "fraction": nak.fraction if hasattr(nak, "fraction") else tl.moon_nakshatra_fraction,
            "lord": nak.lord if hasattr(nak, "lord") else tl.starting_lord,
        },
        "timeline": legacy_timeline,
        "total_years_calculated": tl.total_years_calculated,
        "dasha_cycle_years": 120
    }
