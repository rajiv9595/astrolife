"""
Future transit-window support — post-release bugfix (no new astrology).

Parses natural-language future date ranges from the user query (DATA only)
and evaluates them with the EXISTING canonical engines:

  generate_chart_facts (once) -> get_dynamic_state (exact transit events
  over the window via existing root-finding) -> build_production_entry ->
  evaluate_prediction (existing evaluator, windows preserved).

No transit positions invented, no timestamps manufactured: exact timestamps
enter only from canonical exact signals; otherwise EVENT_WINDOW/UNKNOWN
semantics are preserved verbatim.
"""

from __future__ import annotations

import calendar
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

MAX_WINDOW_DAYS = 366

_MONTH_RE = r"(january|february|march|april|may|june|july|august|september|october|november|december)"


def _tz(tz_name: str):
    try:
        import pytz
        return pytz.timezone(tz_name or "UTC")
    except Exception:
        return timezone.utc


def _month_end(year: int, month: int, tz) -> datetime:
    last = calendar.monthrange(year, month)[1]
    return tz.localize(datetime(year, month, last, 23, 59, 59))


def _month_start(year: int, month: int, tz) -> datetime:
    return tz.localize(datetime(year, month, 1, 0, 0, 0))


def _resolve_year(text: str, now: datetime) -> Optional[int]:
    match = re.search(r"\b(19|20)\d{2}\b", text)
    if match:
        return int(match.group(0))
    return None


def parse_requested_range(
    query: str,
    now: datetime,
    tz_name: str = "UTC",
) -> Optional[Dict[str, Any]]:
    """Parse a future date range from free text. Pure parsing — no astrology.

    Returns {start, end, future_start, future_end, label} with aware
    datetimes, or None when no range is present or the range is entirely
    in the past. `now` must be timezone-aware.
    """
    if not query or not isinstance(query, str):
        return None
    tz = _tz(tz_name)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    text = query.lower()
    year = _resolve_year(text, now)

    def _yr(default_future_bias: bool = True) -> int:
        if year is not None:
            return year
        return now.year

    span: Optional[Tuple[datetime, datetime, str]] = None

    # "september 15 to december 31 2026" / "september 15 - december 31, 2026"
    m = re.search(
        _MONTH_RE + r"\s+(\d{1,2})\s*(?:to|\-|through|till|until)\s*"
        + _MONTH_RE + r"\s+(\d{1,2})", text)
    if m and not span:
        m1, d1, m2, d2 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
        y = _yr()
        try:
            span = (tz.localize(datetime(y, MONTHS[m1], min(d1, 28), 0, 0, 0)),
                    tz.localize(datetime(y, MONTHS[m2],
                                         min(d2, calendar.monthrange(y, MONTHS[m2])[1]),
                                         23, 59, 59)),
                    f"{m1} {d1} to {m2} {d2} {y}")
        except ValueError:
            span = None

    # "september to december 2026" / "between september and december 2026"
    m = re.search(
        r"(?:between\s+)?" + _MONTH_RE + r"\s*(?:to|\-|and|through|till|until)\s*"
        + _MONTH_RE, text)
    if m and not span:
        m1, m2 = m.group(1), m.group(2)
        y = _yr()
        span = (_month_start(y, MONTHS[m1], tz), _month_end(y, MONTHS[m2], tz),
                f"{m1} to {m2} {y}")

    # "by december 2026" (open start -> now)
    m = re.search(r"\bby\s+" + _MONTH_RE + r"(?:\s+(19|20)\d{2})?", text)
    if m and not span and ("to" not in text[max(0, m.start() - 24):m.start()]
                           and "and" not in text[max(0, m.start() - 24):m.start()]):
        m1 = m.group(1)
        y = _yr()
        span = (now, _month_end(y, MONTHS[m1], tz), f"now to {m1} {y}")

    # "next three months" / "next 3 months/weeks"
    m = re.search(r"\bnext\s+(\w+)\s+(months?|weeks?)\b", text)
    if m and not span:
        words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                 "eleven": 11, "twelve": 12}
        raw = m.group(1)
        n = words.get(raw, int(raw) if raw.isdigit() else None)
        if n is not None and 1 <= n <= 12:
            unit = m.group(2)
            days = n * 7 if unit.startswith("week") else n * 30
            span = (now, now + timedelta(days=days), f"next {n} {unit}")

    # "october 2026" / single month (nearest occurrence: explicit year else
    # current-or-next occurrence so the range is never silently past)
    m = re.search(_MONTH_RE + r"(?:\s+(19|20)\d{2})?", text)
    if m and not span:
        m1 = m.group(1)
        y = _yr()
        start, end = _month_start(y, MONTHS[m1], tz), _month_end(y, MONTHS[m1], tz)
        if year is None and end < now:
            # roll to next year so a bare "october" stays future-useful
            start = _month_start(y + 1, MONTHS[m1], tz)
            end = _month_end(y + 1, MONTHS[m1], tz)
            span = (start, end, f"{m1} {y + 1}")
        else:
            span = (start, end, f"{m1} {y}")

    if span is None:
        return None
    start, end, label = span
    if end <= now:
        return None  # entirely historical: no future context to build
    future_start = max(start, now)
    future_end = end
    if (future_end - future_start).days > MAX_WINDOW_DAYS:
        future_end = future_start + timedelta(days=MAX_WINDOW_DAYS)
    return {
        "start": start,
        "end": end,
        "future_start": future_start,
        "future_end": future_end,
        "label": label,
        "clamped_past": start < now,
    }


def build_future_window_section(
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
    range_start: datetime,
    range_end: datetime,
    eval_tz: Optional[str] = None,
    eval_lat: Optional[float] = None,
    eval_lon: Optional[float] = None,
    label: str = "",
) -> Dict[str, Any]:
    """Evaluate a future interval with canonical engines (raises on failure).

    Natal facts are generated ONCE and reused. Exact transit events come
    from the existing root-finding over [future_start, future_end]; the
    existing prediction evaluator produces windowed candidates. Nothing is
    invented: no exact timestamp appears unless a canonical exact signal
    provides it.
    """
    from backend.core.calculation.dynamic import get_dynamic_state
    from backend.core.calculation.pipeline import generate_chart_facts
    from backend.core.prediction.models import PredictionRequest
    from backend.core.prediction.pipeline import evaluate_prediction
    from backend.routes.prediction import build_production_entry

    loc_tz = eval_tz or tz
    loc_lat = float(eval_lat) if eval_lat is not None else float(lat)
    loc_lon = float(eval_lon) if eval_lon is not None else float(lon)

    chart_facts = generate_chart_facts(
        year=int(year), month=int(month), day=int(day),
        hour=int(hour), minute=int(minute), second=int(second),
        lat=float(lat), lon=float(lon), tz_name=str(tz),
    )
    window_days = max(1, min(
        (range_end - range_start).days + 1, MAX_WINDOW_DAYS))
    state = get_dynamic_state(
        chart_facts, range_start,
        latitude=loc_lat, longitude=loc_lon, tz_name=loc_tz,
        include_events=True, event_window_days=window_days,
    )
    state_d = state.model_dump()
    entry = build_production_entry(state_d)
    start_iso = range_start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    end_iso = range_end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    request = PredictionRequest(
        request_id=f"FUTURE-WINDOW-{start_iso}-{end_iso}",
        chart_fingerprint="future-window-chart",
        event_types=[],
        event_ids=[],
        prediction_profile="PREDICTION_DEFAULT_V1",
        start=start_iso,
        end=end_iso,
        requested_timing_precision="DATE_RANGE",
        traditions=[],
        dasha_profiles=[],
        include_alternatives=True,
        include_conflicts=True,
        notes="",
    )
    result = evaluate_prediction(request, entry)
    result_d = result.model_dump(mode="json")
    current = (state_d.get("dasha") or {}).get("current", {})
    return {
        "REQUESTED_PERIOD": {
            "label": label,
            "evaluation_start": range_start.isoformat(),
            "evaluation_end": range_end.isoformat(),
            "window_days": window_days,
            "timezone": loc_tz,
        },
        "DASHA_AT_WINDOW_START": {
            "mahadasha": ((current.get("mahadasha") or {}).get("lord")
                          if isinstance(current.get("mahadasha"), dict)
                          else getattr(current.get("mahadasha"), "lord", None)),
            "hierarchy": current.get("hierarchy", []),
        },
        "TRANSIT_FACTS_AT_WINDOW_START": entry.get("transit_facts", {}),
        "EXACT_TRANSIT_EVENTS": entry.get("transit_events", []),
        "PREDICTION": {
            "status": result_d.get("status"),
            "evidence_state": result_d.get("evidence_state"),
            "profile": result_d.get("profile"),
            "candidates": result_d.get("candidates", []),
            "unknowns": result_d.get("unknowns", []),
            "conflicts": result_d.get("conflicts", []),
            "warnings": result_d.get("warnings", []),
        },
        "PROVENANCE": {
            "source": "canonical_transit_engine",
            "system": "Swiss Ephemeris",
            "ayanamsha": "Lahiri",
            "node_mode": "Mean Node",
            "engine": "evaluate_prediction",
            "exact_timestamps": "canonical root-finding only; no sampled dates promoted",
            "evaluation_start": range_start.isoformat(),
            "evaluation_end": range_end.isoformat(),
        },
        "_source": "canonical",
    }
