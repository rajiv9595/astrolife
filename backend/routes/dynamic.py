"""
Dynamic Astrology Routes — Phase 3 Step 28,30

Provides:
 POST /dynamic-state  — current Dasha + Panchanga + Transits for a birth + evaluation datetime
 POST /transit-range  — arbitrary future range (5-month forecast support)
 GET  /panchanga      — panchanga for arbitrary evaluation datetime + location
 GET  /transits       — transit snapshot for evaluation datetime

All dynamic calculations receive explicit evaluation_datetime — no clock inside core.
UI can pass evaluation_datetime = now; tests pass fixed date.
"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timezone
import pytz

from pydantic import BaseModel, Field

router = APIRouter(prefix="/dynamic", tags=["Dynamic Astrology"])

# We keep schema minimal to avoid breaking frontend; reuse ComputeRequest style
class DynamicStateRequest(BaseModel):
    # Birth data (for ChartFacts)
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    second: int = 0
    tz: str = Field(description="IANA timezone of birth place")
    lat: float
    lon: float
    # Evaluation time — explicit, mandatory for purity
    evaluation_datetime: Optional[str] = Field(default=None, description="ISO8601 for evaluation moment (any timezone). If omitted, server uses request time as UI boundary (reads clock only at API boundary, not inside core).")
    evaluation_tz: Optional[str] = Field(default=None, description="Timezone for evaluation if evaluation_datetime is naive local; defaults to birth tz")
    # Location for Panchanga (defaults to birth lat/lon/tz)
    eval_lat: Optional[float] = None
    eval_lon: Optional[float] = None
    eval_tz: Optional[str] = None
    include_events: bool = False
    event_window_days: int = 7

class PanchangaRequest(BaseModel):
    evaluation_datetime: str
    lat: float
    lon: float
    tz: str

class TransitRangeRequest(BaseModel):
    start_datetime: str
    end_datetime: str
    lat: float = 0.0
    lon: float = 0.0
    tz: str = "UTC"

def _parse_dt(s: str, fallback_tz: str = "UTC") -> datetime:
    # Accept ISO with Z or offset or naive
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = pytz.timezone(fallback_tz).localize(dt)
        return dt
    except Exception as e:
        raise ValueError(f"Invalid datetime '{s}': {e}")

@router.post("/state")
def dynamic_state(req: DynamicStateRequest):
    # Import here to avoid circular at startup
    from backend.core.calculation.pipeline import generate_chart_facts
    from backend.core.calculation.dynamic import get_dynamic_state

    # Determine evaluation datetime — at API boundary we MAY read clock, but core does not
    if req.evaluation_datetime:
        eval_tz = req.evaluation_tz or req.tz
        eval_dt = _parse_dt(req.evaluation_datetime, eval_tz)
    else:
        # UI request with no explicit time => "now" at API boundary (allowed per spec: "For UI requests: evaluation_datetime = current time")
        # Core still receives explicit param, so purity preserved
        eval_dt = datetime.now(timezone.utc)
        eval_tz = "UTC"

    chart_facts = generate_chart_facts(
        year=req.year, month=req.month, day=req.day,
        hour=req.hour, minute=req.minute, second=req.second,
        lat=req.lat, lon=req.lon, tz_name=req.tz
    )

    loc_lat = req.eval_lat if req.eval_lat is not None else req.lat
    loc_lon = req.eval_lon if req.eval_lon is not None else req.lon
    loc_tz = req.eval_tz if req.eval_tz is not None else req.tz

    state = get_dynamic_state(
        chart_facts=chart_facts,
        evaluation_datetime=eval_dt,
        latitude=loc_lat,
        longitude=loc_lon,
        tz_name=loc_tz,
        include_events=req.include_events,
        event_window_days=req.event_window_days
    )
    return state.model_dump()

@router.post("/panchanga")
def panchanga_endpoint(req: PanchangaRequest):
    from backend.core.calculation.panchanga import calculate_panchanga
    eval_dt = _parse_dt(req.evaluation_datetime, req.tz)
    panch = calculate_panchanga(eval_dt, req.lat, req.lon, req.tz)
    return panch.model_dump()

@router.post("/transit-snapshot")
def transit_snapshot(req: PanchangaRequest):
    from backend.core.transit.calculator import calculate_transit_positions
    eval_dt = _parse_dt(req.evaluation_datetime, req.tz)
    snap = calculate_transit_positions(eval_dt)
    return snap.model_dump()

@router.post("/transit-range")
def transit_range(req: TransitRangeRequest):
    from backend.core.calculation.dynamic import get_transit_range
    start_dt = _parse_dt(req.start_datetime, req.tz)
    end_dt = _parse_dt(req.end_datetime, req.tz)
    snaps = get_transit_range(start_dt, end_dt, req.lat, req.lon, req.tz)
    return {"count": len(snaps), "snapshots": snaps}

# Also expose legacy-shaped endpoint that mirrors /compute but adds dynamic fields (backward compat)
@router.post("/compute-dynamic")
def compute_dynamic(req: DynamicStateRequest):
    """
    Backward compat wrapper: returns legacy /compute shape plus dynamic fields.
    Existing frontend can migrate incrementally.
    """
    from backend.calculations import compute_chart
    from backend.core.calculation.pipeline import generate_chart_facts
    from backend.core.calculation.dynamic import get_dynamic_state
    if req.evaluation_datetime:
        eval_dt = _parse_dt(req.evaluation_datetime, req.evaluation_tz or req.tz)
    else:
        eval_dt = datetime.now(timezone.utc)

    legacy = compute_chart(
        year=req.year, month=req.month, day=req.day,
        hour=req.hour, minute=req.minute, second=req.second,
        tz=req.tz, lat=req.lat, lon=req.lon
    )
    chart_facts = generate_chart_facts(
        year=req.year, month=req.month, day=req.day,
        hour=req.hour, minute=req.minute, second=req.second,
        lat=req.lat, lon=req.lon, tz_name=req.tz
    )
    state = get_dynamic_state(chart_facts, eval_dt, latitude=req.eval_lat or req.lat, longitude=req.eval_lon or req.lon, tz_name=req.eval_tz or req.tz)
    # Merge
    legacy["dynamic_state"] = state.model_dump()
    legacy["evaluation_datetime"] = eval_dt.isoformat()
    return legacy
