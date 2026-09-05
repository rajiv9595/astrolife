"""
Phase 5H — Dasha Activation Engine.

Intersects Jaimini Dasha periods with the evaluation range to determine
which dasha windows are active for each candidate.

Profile isolation: never mixes periods from different Jaimini Dasha profiles.
All datetime handling uses explicit inputs, never datetime.now().
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from ..dasha.models import JaiminiDashaPeriod, JaiminiDashaResult

from .models import DashaActivationRecord, TemporalWindow


def _parse_iso(iso_str: str) -> datetime:
    """Parse UTC ISO string to tz-aware datetime."""
    if not iso_str:
        return datetime(1900, 1, 1, tzinfo=timezone.utc)
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _period_window(period: JaiminiDashaPeriod) -> TemporalWindow:
    """Convert a dasha period to a TemporalWindow."""
    start = _parse_iso(period.start_utc_iso)
    end = _parse_iso(period.end_utc_iso)
    return TemporalWindow(start=start, end=end)


def _flatten_periods(
    result: JaiminiDashaResult,
    levels: Optional[List[str]] = None,
) -> List[JaiminiDashaPeriod]:
    """Flatten dasha periods to requested levels.

    Default: MAHA_DASHA only. If levels includes ANTARDASHA, also yields
    nested antardasha periods.
    """
    if levels is None:
        levels = ["MAHA_DASHA"]

    flattened: List[JaiminiDashaPeriod] = []
    for period in result.periods:
        if period.level in levels:
            flattened.append(period)
        if "ANTARDASHA" in levels:
            for ad in period.antardashas:
                if ad.level in levels:
                    flattened.append(ad)
    return flattened


def activate_dasha_periods(
    dasha_result: JaiminiDashaResult,
    evaluation_window: TemporalWindow,
    levels: Optional[List[str]] = None,
) -> List[DashaActivationRecord]:
    """Find all dasha periods intersecting the evaluation window.

    Returns sorted by start time. Profile isolation: the caller must
    ensure dasha_result belongs to a single profile — this function
    does not validate profile boundaries (see profile_isolation.py).
    """
    if levels is None:
        levels = ["MAHA_DASHA"]

    flattened = _flatten_periods(dasha_result, levels)
    activations: List[DashaActivationRecord] = []

    for period in flattened:
        pw = _period_window(period)
        intersection = pw.intersection(evaluation_window)
        if intersection is not None:
            activations.append(DashaActivationRecord(
                period_id=period.period_id,
                level=period.level,
                sign=period.sign,
                start=intersection.start,
                end=intersection.end,
                profile_id=dasha_result.profile_method,
            ))

    activations.sort(key=lambda a: (a.start, a.period_id))
    return activations


def get_dasha_windows(
    dasha_result: JaiminiDashaResult,
    evaluation_window: TemporalWindow,
    levels: Optional[List[str]] = None,
) -> List[TemporalWindow]:
    """Return the intersection windows for all active dasha periods."""
    activations = activate_dasha_periods(dasha_result, evaluation_window, levels)
    return [
        TemporalWindow(start=a.start, end=a.end)
        for a in activations
    ]
