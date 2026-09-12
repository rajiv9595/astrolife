"""
AI transit context — integration hotfix (additive only).

Builds structured canonical transit facts for the AI Astrologer WITHOUT
duplicating Swiss Ephemeris logic and WITHOUT touching
backend/core/transit/* or backend/core/calculation/* formulas.

Authoritative chain:
  birth params -> generate_chart_facts(...) (natal)
  + evaluation_datetime (explicit; now() ONLY at API boundary)
  -> get_dynamic_state(...) (canonical transit engine)
  -> structured AI section with provenance.

AI is an interpreter, never the calculator.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


TRANSIT_PROVENANCE_STATIC = {
    "source": "canonical_transit_engine",
    "system": "Swiss Ephemeris",
    "ayanamsha": "Lahiri",
    "node_mode": "Mean Node",
}

TRANSIT_GROUNDING_INSTRUCTIONS = """CANONICAL TRANSIT GROUNDING (authoritative):
- Treat canonical transit facts in CURRENT_TRANSITS / TRANSIT_NATAL_RELATIONS / TRANSIT_ASPECTS as authoritative.
- Do NOT recalculate planetary longitudes. Do NOT invent transit positions.
- Distinguish natal placement (NATAL_FACTS/planets) from current transit (CURRENT_TRANSITS).
- Use only backend-supplied transit-to-natal relationships/events.
- Do NOT claim a transit is active unless the backend supplies the relevant relationship/event.
- If transit status is "unavailable", explicitly say timing/current-transit analysis is unavailable rather than inventing it.
- prediction_candidates (when present) are deterministic engine output; interpret them, do not re-time events independently.
"""


def parse_evaluation_datetime(value: Optional[str], fallback_tz: str = "UTC") -> Optional[datetime]:
    """Parse ISO evaluation datetime. Returns None when omitted. No clock read."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        import pytz

        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = pytz.timezone(fallback_tz or "UTC").localize(dt)
        return dt
    except Exception as exc:  # keep caller contract explicit
        raise ValueError(f"Invalid evaluation datetime {value!r}: {exc}")


def resolve_evaluation_datetime(
    supplied: Optional[str], fallback_tz: str = "UTC"
) -> tuple[datetime, str]:
    """
    Resolve evaluation datetime. Clock is read ONLY here (API boundary).
    Returns (datetime, source) where source is 'supplied' or 'now-boundary'.
    Never falls back to birth datetime.
    """
    parsed = parse_evaluation_datetime(supplied, fallback_tz)
    if parsed is not None:
        return parsed, "supplied"
    return datetime.now(timezone.utc), "now-boundary"


def _import_canonical():
    try:
        from backend.core.calculation.pipeline import generate_chart_facts
        from backend.core.calculation.dynamic import get_dynamic_state
    except ImportError:  # pragma: no cover - alternate import root
        from core.calculation.pipeline import generate_chart_facts  # type: ignore
        from core.calculation.dynamic import get_dynamic_state  # type: ignore
    return generate_chart_facts, get_dynamic_state


def build_canonical_transit_section(
    *,
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    tz: str = "UTC",
    lat: float = 0.0,
    lon: float = 0.0,
    evaluation_iso: Optional[str] = None,
    evaluation_tz: Optional[str] = None,
    eval_lat: Optional[float] = None,
    eval_lon: Optional[float] = None,
    eval_tz: Optional[str] = None,
    include_events: bool = False,
    event_window_days: int = 7,
) -> Dict[str, Any]:
    """
    Build the structured transit section for AI context.

    Never uses birth datetime as the transit evaluation datetime: the
    evaluation moment comes only from `evaluation_iso` or from now() at the
    API boundary (see resolve_evaluation_datetime).
    """
    generate_chart_facts, get_dynamic_state = _import_canonical()

    eval_dt, eval_source = resolve_evaluation_datetime(
        evaluation_iso, evaluation_tz or tz
    )
    loc_lat = float(eval_lat) if eval_lat is not None else float(lat)
    loc_lon = float(eval_lon) if eval_lon is not None else float(lon)
    loc_tz = eval_tz or tz

    chart_facts = generate_chart_facts(
        year=int(year),
        month=int(month),
        day=int(day),
        hour=int(hour),
        minute=int(minute),
        second=int(second),
        lat=float(lat),
        lon=float(lon),
        tz_name=str(tz),
    )
    state = get_dynamic_state(
        chart_facts,
        eval_dt,
        latitude=loc_lat,
        longitude=loc_lon,
        tz_name=loc_tz,
        include_events=bool(include_events),
        event_window_days=int(event_window_days),
    )
    state_d = state.model_dump()

    transits = state_d.get("transits")
    if not transits:
        return {
            "NATAL_FACTS": {"note": "natal chart facts built canonically"},
            "CURRENT_EVALUATION": {
                "evaluation_datetime": eval_dt.isoformat(),
                "evaluation_source": eval_source,
                "evaluation_utc_iso": state_d.get("evaluation_utc_iso"),
            },
            "CURRENT_TRANSITS": {"status": "unavailable"},
            "TRANSIT_NATAL_RELATIONS": {"status": "unavailable"},
            "TRANSIT_ASPECTS": {"status": "unavailable"},
            "TRANSIT_EVENTS": {"status": "unavailable"},
            "DASHA": state_d.get("dasha", {}).get("current", {}),
            "OTHER_CANONICAL_FACTS": {"panchanga": state_d.get("panchanga")},
            "PROVENANCE": {
                **TRANSIT_PROVENANCE_STATIC,
                "evaluation_datetime": eval_dt.isoformat(),
                "evaluation_utc_iso": state_d.get("evaluation_utc_iso"),
                "evaluation_source": eval_source,
                "transit_available": False,
            },
            "_dynamic_state": state_d,
            "_transit_available": False,
        }

    snapshot = (transits.get("snapshot") or {})
    planets = (snapshot.get("planets") or {})
    current_transits = {
        name: {
            "sign": p.get("sign"),
            "sign_num": p.get("sign_num"),
            "sidereal_longitude": p.get("sidereal_longitude"),
            "tropical_longitude": p.get("tropical_longitude"),
            "nakshatra": p.get("nakshatra"),
            "pada": p.get("pada"),
            "retrograde": p.get("retrograde"),
            "speed_longitude": p.get("speed_longitude"),
        }
        for name, p in sorted(planets.items())
    }
    return {
        "NATAL_FACTS": {"note": "see existing natal context (planets/ascendant/yogas); not duplicated here"},
        "CURRENT_EVALUATION": {
            "evaluation_datetime": state_d.get("evaluation_datetime"),
            "evaluation_utc_iso": state_d.get("evaluation_utc_iso"),
            "evaluation_jd": state_d.get("evaluation_jd"),
            "evaluation_source": eval_source,
            "location": state_d.get("location"),
        },
        "CURRENT_TRANSITS": {
            "evaluation_utc_iso": snapshot.get("evaluation_utc_iso"),
            "evaluation_jd": snapshot.get("evaluation_jd"),
            "ayanamsha": snapshot.get("ayanamsha"),
            "ayanamsha_system": snapshot.get("ayanamsha_system"),
            "planets": current_transits,
        },
        "TRANSIT_NATAL_RELATIONS": transits.get("relations", []),
        "TRANSIT_ASPECTS": {
            "western_aspects": transits.get("western_aspects", []),
            "parashari_aspects": transits.get("parashari_aspects", []),
        },
        "TRANSIT_EVENTS": state_d.get("events"),
        "DASHA": (state_d.get("dasha") or {}).get("current", {}),
        "OTHER_CANONICAL_FACTS": {"panchanga": state_d.get("panchanga")},
        "PROVENANCE": {
            **TRANSIT_PROVENANCE_STATIC,
            "evaluation_datetime": state_d.get("evaluation_datetime"),
            "evaluation_utc_iso": state_d.get("evaluation_utc_iso"),
            "evaluation_source": eval_source,
            "transit_available": True,
            "ephemeris_version": (transits.get("cache_key") or {}).get("ephemeris_version"),
        },
        "_dynamic_state": state_d,
        "_transit_available": True,
    }


def transit_unavailable_section(reason: str = "no-birth-params") -> Dict[str, Any]:
    """Explicit unavailable state — AI must not fabricate transits."""
    return {
        "CURRENT_TRANSITS": {"status": "unavailable", "reason": reason},
        "TRANSIT_NATAL_RELATIONS": {"status": "unavailable", "reason": reason},
        "TRANSIT_ASPECTS": {"status": "unavailable", "reason": reason},
        "TRANSIT_EVENTS": {"status": "unavailable", "reason": reason},
        "PROVENANCE": {**TRANSIT_PROVENANCE_STATIC, "transit_available": False, "reason": reason},
        "_transit_available": False,
    }
