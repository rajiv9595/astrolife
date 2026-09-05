"""
DynamicAstrologyState — time-dependent layer (Phase 3 Step 27-28).

Combines:
 - Panchanga (evaluation_datetime, lat/lon/tz, profile)
 - Dasha current state (timeline + evaluation_datetime)
 - Transit positions + relations + aspects
 - Transit events (optional window)

Strictly separated from ChartFacts (static natal).
All functions pure with explicit evaluation_datetime — no datetime.now() inside core.

Cache structured so keys include datetime, location, profile, ephemeris version (Step 29).
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import swisseph as swe

from .models import ChartFacts
from .config import CalculationProfile, DEFAULT_PROFILE
from .panchanga import calculate_panchanga, PanchangaDetails
from .dasha import calculate_vimshottari_timeline, get_current_dasha, DashaTimeline

# Transit imports — avoid circular at import time; lazy inside function
# but we can import types
try:
    from ..transit.calculator import calculate_transit_positions, TransitSnapshot
    from ..transit.aspects import compute_western_aspects, compute_parashari_aspects, compute_transit_natal_relations
    from ..transit.events import detect_transit_events
    _TRANSIT_AVAILABLE = True
except Exception as e:
    _TRANSIT_AVAILABLE = False
    _transit_import_error = str(e)

class DynamicAstrologyState(BaseModel):
    evaluation_datetime: str = Field(description="ISO of evaluation_datetime as provided (aware)")
    evaluation_jd: float
    evaluation_utc_iso: str
    location: Dict[str, Any]
    panchanga: PanchangaDetails
    dasha: Dict[str, Any]  # contains timeline + current
    transits: Optional[Dict[str, Any]] = None
    events: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

def _evaluation_jd(dt: datetime) -> float:
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt.astimezone(timezone.utc)
    ut_dec = dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0 + dt_utc.microsecond/3600.0/1_000_000.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut_dec, swe.GREG_CAL)

def _jd_to_utc_iso(jd: float) -> str:
    import math
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

def get_dynamic_state(
    chart_facts: ChartFacts,
    evaluation_datetime: datetime,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    tz_name: Optional[str] = None,
    profile: Optional[CalculationProfile] = None,
    include_events: bool = False,
    event_window_days: int = 7,
) -> DynamicAstrologyState:
    """
    Pure service: evaluation_datetime is explicit (UI passes now, test passes fixed date).
    No datetime.now() inside.

    Args:
        chart_facts: static natal
        evaluation_datetime: explicit evaluation moment (any timezone, will be normalized to UTC)
        latitude/longitude/tz_name: for Panchanga location. Defaults to birth location if not provided.
        profile: CalculationProfile or None -> chart_facts.profile or DEFAULT
        include_events: if True, detect transit events in [evaluation, evaluation+event_window_days]
        event_window_days: window for events

    Returns:
        DynamicAstrologyState (pydantic)
    """
    if profile is None:
        try:
            profile = chart_facts.calculation_profile or DEFAULT_PROFILE
        except Exception:
            profile = DEFAULT_PROFILE

    # Resolve location defaults to birth
    if latitude is None:
        latitude = float(chart_facts.location.latitude)
    if longitude is None:
        longitude = float(chart_facts.location.longitude)
    if tz_name is None:
        tz_name = str(chart_facts.location.timezone)

    # Evaluation JD and iso
    eval_jd = _evaluation_jd(evaluation_datetime)
    eval_utc_iso = _jd_to_utc_iso(eval_jd)
    # Preserve original evaluation datetime iso form
    eval_iso = evaluation_datetime.isoformat()

    # 1. Panchanga
    panchanga = calculate_panchanga(evaluation_datetime, latitude, longitude, tz_name, profile)

    # 2. Dasha — timeline (120 years ahead from birth) + current selector
    # Generate timeline from birth covering evaluation (if evaluation is far future, ensure enough years)
    # Estimate years needed: (eval_jd - birth_jd)/days_per_year + buffer
    try:
        dasha_profile = profile.dasha_profile if hasattr(profile, "dasha_profile") else None
        from .config import DEFAULT_DASHA_PROFILE
        if dasha_profile is None:
            dasha_profile = DEFAULT_DASHA_PROFILE
        days_per_year = dasha_profile.days_per_year
    except Exception:
        days_per_year = 365.2425
    birth_jd = float(chart_facts.time.julian_day)
    years_needed = (eval_jd - birth_jd) / days_per_year + 10
    if years_needed < 120:
        years_needed = 120  # at least one cycle
    if years_needed > 200:
        years_needed = 200  # cap to avoid huge
    timeline: DashaTimeline = calculate_vimshottari_timeline(chart_facts, profile=dasha_profile, years_ahead=float(years_needed))
    current = get_current_dasha(timeline, evaluation_datetime)

    dasha_block: Dict[str, Any] = {
        "timeline": timeline.model_dump(),
        "current": {
            "evaluation_jd": current.get("evaluation_jd"),
            "evaluation_utc_iso": current.get("evaluation_utc_iso"),
            "mahadasha": current.get("mahadasha").model_dump() if current.get("mahadasha") else None,
            "antardasha": current.get("antardasha").model_dump() if current.get("antardasha") else None,
            "pratyantardasha": current.get("pratyantardasha").model_dump() if current.get("pratyantardasha") else None,
            "sookshma": current.get("sookshma").model_dump() if current.get("sookshma") else None,
            "prana": current.get("prana").model_dump() if current.get("prana") else None,
            "hierarchy": current.get("hierarchy", []),
            "note": current.get("note"),
        },
        "profile": dasha_profile.model_dump(),
        "boundary_convention": timeline.boundary_convention,
    }

    # 3. Transits
    transits_block = None
    events_block = None
    if _TRANSIT_AVAILABLE:
        snapshot: TransitSnapshot = calculate_transit_positions(evaluation_datetime, profile)
        western = compute_western_aspects(snapshot, chart_facts, profile)
        parashari = compute_parashari_aspects(snapshot, chart_facts, profile)
        relations = compute_transit_natal_relations(snapshot, chart_facts)
        transits_block = {
            "snapshot": snapshot.model_dump(),
            "western_aspects": [w.model_dump() for w in western],
            "parashari_aspects": [p.model_dump() for p in parashari],
            "relations": [r.model_dump() for r in relations],
            "cache_key": {
                "datetime": eval_utc_iso,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": tz_name,
                "profile": profile.model_dump() if hasattr(profile, "model_dump") else str(profile),
                "ephemeris_version": getattr(swe, "version", "2.10.03"),
                "jd": eval_jd,
            }
        }
        if include_events:
            try:
                end_dt = evaluation_datetime
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc) + timedelta(days=event_window_days)
                else:
                    end_dt = end_dt + timedelta(days=event_window_days)
                evs = detect_transit_events(chart_facts, evaluation_datetime, end_dt, profile)
                events_block = [e.model_dump() for e in evs]
            except Exception as e:
                events_block = [{"error": str(e)}]

    return DynamicAstrologyState(
        evaluation_datetime=eval_iso,
        evaluation_jd=eval_jd,
        evaluation_utc_iso=eval_utc_iso,
        location={"latitude": latitude, "longitude": longitude, "timezone": tz_name},
        panchanga=panchanga,
        dasha=dasha_block,
        transits=transits_block,
        events=events_block,
        metadata={
            "profile": profile.model_dump() if hasattr(profile, "model_dump") else {},
            "generated_via": "get_dynamic_state",
            "transit_available": _TRANSIT_AVAILABLE,
        }
    )

# Convenience: support explicit range transits without chart (for Transit Range tests)
def get_transit_range(
    start_datetime: datetime,
    end_datetime: datetime,
    latitude: float,
    longitude: float,
    tz_name: str,
    profile: Optional[CalculationProfile] = None,
) -> List[Dict[str, Any]]:
    """
    Calculate transits for arbitrary future range — no birth dependency.
    Example 5-month forecast: 2026-09-02 through 2027-02-02 arbitrary.
    No hard-coded duration.
    """
    if profile is None:
        profile = DEFAULT_PROFILE
    from ..transit.calculator import calculate_transits
    snaps = calculate_transits(start_datetime, end_datetime, profile, step_days=1.0)
    return [s.model_dump() for s in snaps]
