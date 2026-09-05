"""
Phase 8 — window algebra (§§22–23).

Half-open intervals [start, end), consistent with timing architecture.
ISO-8601 strings in, ISO-8601 strings out; empty end means unbounded.
Precision ordering: EXACT > DAY > WEEK > MONTH > DATE_RANGE > DASHA_RANGE >
UNKNOWN. Operations never invent precision beyond the weakest contributor.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    DASHA_RANGE,
    DATE_RANGE,
    DAY,
    EXACT,
    MONTH,
    PRECISION_UNKNOWN,
    PRECISIONS,
    WEEK,
    TimingWindow,
)

_PRECISION_RANK = {name: rank for rank, name in enumerate(PRECISIONS)}


def parse_iso(value: str) -> Optional[datetime]:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def weaker_precision(first: str, second: str) -> str:
    """The less precise of two precisions (bounds overclaim)."""
    return first if _PRECISION_RANK[first] >= _PRECISION_RANK[second] else second


def intersect(first: TimingWindow, second: TimingWindow) -> Optional[TimingWindow]:
    """Half-open intersection; None when empty. Precision degrades honestly,
    except an exact point inside a range stays EXACT (the timestamp stands)."""
    for point_win, range_win in ((first, second), (second, first)):
        if point_win.start and point_win.start == point_win.end:
            verdict = contains(range_win, point_win.start)
            if verdict is True:
                return TimingWindow(
                    start=point_win.start, end=point_win.end,
                    precision=EXACT,
                    source_signals=sorted(set(point_win.source_signals)
                                          | set(range_win.source_signals)),
                    exact_events=sorted(set(point_win.exact_events)
                                        | set(range_win.exact_events)),
                    uncertainty="; ".join(u for u in
                                          (point_win.uncertainty,
                                           range_win.uncertainty) if u),
                    profile=point_win.profile or range_win.profile,
                    provenance={"operation": "intersection-exact"})
            return None
    start_a, end_a = parse_iso(first.start), parse_iso(first.end)
    start_b, end_b = parse_iso(second.start), parse_iso(second.end)
    starts = [s for s in (start_a, start_b) if s is not None]
    ends = [e for e in (end_a, end_b) if e is not None]
    if not starts:
        return None
    start = max(starts)
    end = min(ends) if ends else None
    if end is not None and not start < end:
        # Touching boundaries do not overlap under half-open convention.
        return None
    return TimingWindow(
        start=start.isoformat().replace("+00:00", "Z"),
        end=end.isoformat().replace("+00:00", "Z") if end else "",
        precision=weaker_precision(first.precision, second.precision),
        source_signals=sorted(set(first.source_signals) | set(second.source_signals)),
        exact_events=sorted(set(first.exact_events) | set(second.exact_events)),
        uncertainty="; ".join(u for u in (first.uncertainty, second.uncertainty) if u),
        profile=first.profile or second.profile,
        provenance={"operation": "intersection"})


def union(first: TimingWindow, second: TimingWindow) -> TimingWindow:
    starts = [s for s in (parse_iso(first.start), parse_iso(second.start)) if s]
    ends = [e for e in (parse_iso(first.end), parse_iso(second.end)) if e]
    start = min(starts) if starts else None
    # Unbounded (empty end) dominates a union.
    if not first.end or not second.end:
        end = None
    else:
        end = max(ends) if ends else None
    return TimingWindow(
        start=start.isoformat().replace("+00:00", "Z") if start else "",
        end=end.isoformat().replace("+00:00", "Z") if end else "",
        precision=weaker_precision(first.precision, second.precision),
        source_signals=sorted(set(first.source_signals) | set(second.source_signals)),
        exact_events=sorted(set(first.exact_events) | set(second.exact_events)),
        uncertainty="; ".join(u for u in (first.uncertainty, second.uncertainty) if u),
        profile=first.profile or second.profile,
        provenance={"operation": "union"})


def contains(window: TimingWindow, point_iso: str) -> Optional[bool]:
    """Half-open containment of an exact point; None when undecidable."""
    point = parse_iso(point_iso)
    start, end = parse_iso(window.start), parse_iso(window.end)
    if point is None or start is None:
        return None
    if end is None:
        return start <= point
    return start <= point < end


def overlap(first: TimingWindow, second: TimingWindow) -> bool:
    return intersect(first, second) is not None


def distance(first: TimingWindow, second: TimingWindow) -> Optional[float]:
    """Gap in days between non-overlapping windows; 0.0 when overlapping."""
    if overlap(first, second):
        return 0.0
    end_a, start_b = parse_iso(first.end), parse_iso(second.start)
    end_b, start_a = parse_iso(second.end), parse_iso(first.start)
    gaps: List[float] = []
    if end_a is not None and start_b is not None and start_b >= end_a:
        gaps.append((start_b - end_a).total_seconds() / 86400.0)
    if end_b is not None and start_a is not None and start_a >= end_b:
        gaps.append((start_a - end_b).total_seconds() / 86400.0)
    if not gaps:
        return None
    return min(gaps)


def clip(window: TimingWindow, start_iso: str, end_iso: str) -> Optional[TimingWindow]:
    bounds = TimingWindow(start=start_iso, end=end_iso, precision=window.precision,
                          source_signals=list(window.source_signals),
                          exact_events=list(window.exact_events),
                          uncertainty=window.uncertainty, profile=window.profile,
                          provenance=dict(window.provenance))
    return intersect(window, bounds)
