"""
Production prediction route — integration hotfix (additive only).

Exposes the existing Phase 8 deterministic engine
(core/prediction/evaluate_prediction + PredictionInput/entry contract)
over HTTP using the SAME canonical transit facts as /dynamic/state.

Chain (no new astrology):
  birth params + evaluation_datetime (explicit; now() only at boundary)
  -> generate_chart_facts(...) (natal)
  -> get_dynamic_state(..., evaluation_datetime, ...) (canonical transits)
  -> entry {transit_facts (sign map, windowless), transit_events (exact ts only),
            dasha periods, outcomes: [] (honest UNKNOWN when no rules supplied)}
  -> evaluate_prediction(request, entry)
  -> candidates / windows / supporting_transits / evidence / provenance.

Windowless transit sign strings NEVER become exact timing events: only
canonical transit events with exact timestamps enter transit_events.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/prediction", tags=["Prediction (deterministic)"])


class PredictionEvaluateRequest(BaseModel):
    # Natal birth data (for ChartFacts)
    year: int
    month: int
    day: int
    hour: int = 0
    minute: int = 0
    second: int = 0
    tz: str = Field(description="IANA timezone of birth place")
    lat: float
    lon: float
    # Evaluation moment — explicit; omitted => now at API boundary (bulk reads clock here only).
    evaluation_datetime: Optional[str] = Field(default=None)
    evaluation_iso: Optional[str] = Field(default=None)
    evaluation_tz: Optional[str] = Field(default=None)
    eval_lat: Optional[float] = None
    eval_lon: Optional[float] = None
    eval_tz: Optional[str] = None
    include_transit_events: bool = True
    event_window_days: int = 30
    # Prediction request window + selectors (existing PredictionRequest contract)
    start: str = Field(description="ISO window start, e.g. 2026-01-01T00:00:00Z")
    end: str = Field(description="ISO window end")
    event_types: List[str] = Field(default_factory=list)
    event_ids: List[str] = Field(default_factory=list)
    prediction_profile: str = "PREDICTION_DEFAULT_V1"
    requested_timing_precision: str = "DATE_RANGE"
    traditions: List[str] = Field(default_factory=list)
    dasha_profiles: List[str] = Field(default_factory=list)
    include_alternatives: bool = True
    include_conflicts: bool = True
    notes: str = ""
    request_id: Optional[str] = None


def _eval_iso(req: PredictionEvaluateRequest) -> Optional[str]:
    return req.evaluation_datetime if req.evaluation_datetime else req.evaluation_iso


def _parse_eval(value: Optional[str], fallback_tz: str) -> datetime:
    if value:
        try:
            import pytz

            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = pytz.timezone(fallback_tz or "UTC").localize(dt)
            return dt
        except Exception as exc:
            raise ValueError(f"Invalid evaluation datetime {value!r}: {exc}")
    return datetime.now(timezone.utc)


def _event_fingerprint(ev_type: str, planet: str, natal: str, stamp: str) -> str:
    return hashlib.sha256(
        f"{ev_type}|{planet}|{natal}|{stamp}".encode("utf-8")
    ).hexdigest()[:16]


def build_production_entry(
    dynamic_state_dump: Dict[str, Any],
    chart_fingerprint: str = "live-chart",
) -> Dict[str, Any]:
    """
    Convert canonical DynamicAstrologyState (dumped) into the existing
    PredictionInput/entry contract. Pure mapping — no astrology recomputed.
    Exact transit event timestamps preserved verbatim.
    """
    transits = dynamic_state_dump.get("transits") or {}
    snapshot = transits.get("snapshot") or {}
    planets = snapshot.get("planets") or {}
    transit_facts: Dict[str, str] = {
        name: str(p.get("sign")) for name, p in sorted(planets.items()) if p.get("sign")
    }
    raw_events = dynamic_state_dump.get("events") or []
    transit_events: List[Dict[str, Any]] = []
    for ev in raw_events:
        if not isinstance(ev, dict) or "error" in ev:
            continue
        stamp = str(ev.get("utc_iso", ""))
        if not stamp:
            continue  # only exact-timestamp events may enter
        ev_type = str(ev.get("type", ""))
        planet = str(ev.get("transit_planet", ""))
        natal = str(ev.get("natal_planet", "") or "")
        transit_events.append(
            {
                "planet": planet,
                "kind": ev_type,
                "natal_target": natal,
                "timestamp_iso": stamp,  # verbatim root timestamp
                "fingerprint": _event_fingerprint(ev_type, planet, natal, stamp),
            }
        )
    periods: List[Dict[str, Any]] = []
    dasha = dynamic_state_dump.get("dasha") or {}
    timeline = dasha.get("timeline") or {}
    for md in timeline.get("mahadashas", []) or []:
        period = md.get("period", {}) or {}
        if period.get("lord"):
            periods.append(
                {
                    "system": "VIMSHOTTARI",
                    "profile": "VIMSHOTTARI_DEFAULT",
                    "level": "MD",
                    "key": str(period.get("lord", "")),
                    "start_iso": str(period.get("start_utc_iso", "")),
                    "end_iso": str(period.get("end_utc_iso", "")),
                    "fingerprint": "canonical-vimshottari",
                }
            )
        for ad in md.get("antar_dashas", []) or []:
            sub = ad.get("period", {}) or {}
            if sub.get("lord"):
                periods.append(
                    {
                        "system": "VIMSHOTTARI",
                        "profile": "VIMSHOTTARI_DEFAULT",
                        "level": "AD",
                        "key": f"{period.get('lord', '')}/{sub.get('lord', '')}",
                        "start_iso": str(sub.get("start_utc_iso", "")),
                        "end_iso": str(sub.get("end_utc_iso", "")),
                        "fingerprint": "canonical-vimshottari",
                    }
                )
    has_transit = transits is not None and bool(planets)
    # Honest availability flags derived from actually-supplied content:
    # VIMSHOTTARI periods come from the canonical timeline above; CHARA
    # periods are never supplied on this route, so has_jaimini stays False
    # and the engine emits its explicit missing-layer UNKNOWN signal.
    has_dasha = bool(periods)
    has_jaimini = any(p.get("system") == "CHARA" for p in periods)
    try:
        from backend.core.prediction.models import PredictionInput
    except ImportError:  # pragma: no cover
        from core.prediction.models import PredictionInput  # type: ignore
    entry_input = PredictionInput(
        chart_fingerprint=chart_fingerprint,
        calculation_profile="DEFAULT",
        rule_outcomes=[],
        dasha_periods=[],
        transit_facts=transit_facts,
        transit_events=[],  # typed validation only; raw dicts used in entry below
        has_dasha=has_dasha,
        has_transit=has_transit,
        has_jaimini=has_jaimini,
        has_strength=True,  # informational; engine consumes no strength input
        conflicts=[],
        evidence_ids=[],
        sources={},
    )
    return {
        "outcomes": [],
        "periods": periods,
        "transit_facts": transit_facts,
        "transit_events": transit_events,
        "has_dasha": has_dasha,
        "has_transit": has_transit,
        "has_jaimini": has_jaimini,
        "has_strength": True,
        "conflicts": [],
        "input_fingerprint": entry_input.fingerprint(),
    }


@router.post("/evaluate")
def evaluate(req: PredictionEvaluateRequest) -> Dict[str, Any]:
    """Production evaluation over live canonical transit state."""
    try:
        from backend.core.calculation.pipeline import generate_chart_facts
        from backend.core.calculation.dynamic import get_dynamic_state
        from backend.core.prediction.models import PredictionRequest
        from backend.core.prediction.pipeline import evaluate_prediction
    except ImportError:  # pragma: no cover - alternate import root
        from core.calculation.pipeline import generate_chart_facts  # type: ignore
        from core.calculation.dynamic import get_dynamic_state  # type: ignore
        from core.prediction.models import PredictionRequest  # type: ignore
        from core.prediction.pipeline import evaluate_prediction  # type: ignore

    try:
        eval_dt = _parse_eval(_eval_iso(req), req.evaluation_tz or req.tz)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    chart_facts = generate_chart_facts(
        year=req.year, month=req.month, day=req.day,
        hour=req.hour, minute=req.minute, second=req.second,
        lat=req.lat, lon=req.lon, tz_name=req.tz,
    )
    state = get_dynamic_state(
        chart_facts,
        eval_dt,
        latitude=req.eval_lat if req.eval_lat is not None else req.lat,
        longitude=req.eval_lon if req.eval_lon is not None else req.lon,
        tz_name=req.eval_tz or req.tz,
        include_events=bool(req.include_transit_events),
        event_window_days=int(req.event_window_days),
    )
    state_d = state.model_dump()
    entry = build_production_entry(state_d)
    request = PredictionRequest(
        request_id=req.request_id or f"LIVE-{eval_dt.isoformat()}",
        chart_fingerprint="live-chart",
        event_types=list(req.event_types),
        event_ids=list(req.event_ids),
        prediction_profile=req.prediction_profile,
        start=req.start,
        end=req.end,
        requested_timing_precision=req.requested_timing_precision,
        traditions=list(req.traditions),
        dasha_profiles=list(req.dasha_profiles),
        include_alternatives=bool(req.include_alternatives),
        include_conflicts=bool(req.include_conflicts),
        notes=req.notes,
    )
    result = evaluate_prediction(request, entry)
    result_d = result.model_dump(mode="json")
    candidates = result_d.get("candidates", []) or []
    return {
        "request_id": request.request_id,
        "status": result_d.get("status"),
        "evidence_state": result_d.get("evidence_state"),
        "profile": result_d.get("profile"),
        "input_fingerprint": result_d.get("input_fingerprint"),
        "output_fingerprint": result_d.get("output_fingerprint"),
        "unknowns": result_d.get("unknowns", []),
        "conflicts": result_d.get("conflicts", []),
        "warnings": result_d.get("warnings", []),
        "candidates": candidates,
        "timing_windows": [
            {"hypothesis_id": c.get("hypothesis_id"), "windows": c.get("windows", [])}
            for c in candidates
        ],
        "supporting_transits": sorted(
            {t for c in candidates for t in (c.get("supporting_transits") or [])}
        ),
        "evaluation_datetime": state_d.get("evaluation_datetime"),
        "evaluation_utc_iso": state_d.get("evaluation_utc_iso"),
        "transit_available": bool((state_d.get("transits") or {}).get("snapshot")),
        "transit_facts": entry["transit_facts"],
        "transit_events": entry["transit_events"],
        "provenance": {
            "source": "canonical_transit_engine",
            "system": "Swiss Ephemeris",
            "ayanamsha": "Lahiri",
            "node_mode": "Mean Node",
            "evaluation_datetime": state_d.get("evaluation_datetime"),
            "evaluation_utc_iso": state_d.get("evaluation_utc_iso"),
            "engine": "evaluate_prediction",
        },
    }
