"""
Phase 5H — Candidate Builder.

Constructs JaiminiEventCandidate instances from CandidateContext.
Handles temporal precision derivation, evidence assembly, and
candidate ID generation.

All construction is deterministic. No datetime.now() calls.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..candidates import (
    JaiminiEventCandidate,
    JaiminiEventCategory,
    TemporalPrecision,
)
from ..mappings import MappingEntry

from .models import (
    CandidateContext,
    DashaActivationRecord,
    TemporalWindow,
    TransitConditionRecord,
)


def _derive_precision(
    transit_conditions: List[TransitConditionRecord],
    dasha_activations: List[DashaActivationRecord],
) -> TemporalPrecision:
    """Derive temporal precision from available evidence.

    EXACT: a transit condition has an exact_time (e.g. ingress, station)
    DAY: dasha boundaries known to day, no exact transit event
    WINDOW: overlap of multiple dasha periods
    APPROXIMATE: only evaluation range available
    UNKNOWN: no data
    """
    has_exact = any(c.exact_time is not None for c in transit_conditions)
    if has_exact:
        return TemporalPrecision.EXACT

    if len(dasha_activations) == 1:
        return TemporalPrecision.DAY
    elif len(dasha_activations) > 1:
        return TemporalPrecision.WINDOW
    elif len(transit_conditions) > 0:
        return TemporalPrecision.DAY
    else:
        return TemporalPrecision.UNKNOWN


def _compute_peak(
    transit_conditions: List[TransitConditionRecord],
) -> Optional[datetime]:
    """Compute peak time: exact transit event time if available."""
    exact_times = [
        c.exact_time for c in transit_conditions
        if c.exact_time is not None
    ]
    if exact_times:
        exact_times.sort()
        return exact_times[len(exact_times) // 2]
    return None


def _compute_window(
    dasha_activations: List[DashaActivationRecord],
) -> Optional[TemporalWindow]:
    """Compute candidate window from dasha activations.

    Window = intersection of all active dasha periods. If no intersection,
    use the union (earliest start to latest end).
    """
    if not dasha_activations:
        return None

    windows = [
        TemporalWindow(start=a.start, end=a.end)
        for a in dasha_activations
    ]

    result = windows[0]
    for w in windows[1:]:
        inter = result.intersection(w)
        if inter is not None:
            result = inter
        else:
            result = TemporalWindow(
                start=min(result.start, w.start),
                end=max(result.end, w.end),
            )

    return result


def _build_candidate_id(
    profile_id: str,
    category: str,
    start: datetime,
    end: datetime,
) -> str:
    """Build deterministic candidate ID."""
    s = start.isoformat()
    e = end.isoformat()
    return f"{profile_id}:{category}:{s}:{e}"


def _assemble_evidence(
    context: CandidateContext,
    transit_conditions: List[TransitConditionRecord],
) -> List[str]:
    """Assemble evidence paths for the candidate."""
    evidence = list(context.evidence_paths)

    for cond in transit_conditions:
        evidence.append(f"transit:{cond.condition_id}")

    for da in context.dasha_activations:
        evidence.append(f"dasha:{da.period_id}")

    evidence.append(f"rule:{context.rule_id}")
    evidence.append(f"category:{context.event_category}")

    return sorted(set(evidence))


def build_candidate(
    context: CandidateContext,
    window: TemporalWindow,
    convergence: str = "",
) -> Optional[JaiminiEventCandidate]:
    """Build a single JaiminiEventCandidate from context.

    Returns None if the context does not have enough data to build
    a valid candidate (no dasha activations, rule not formed).
    """
    if not context.rule_formed:
        return None
    if not context.dasha_activations:
        return None

    precision = _derive_precision(context.transit_conditions, context.dasha_activations)
    peak = _compute_peak(context.transit_conditions)

    duration_days = window.duration_days()
    duration_years = duration_days / 365.25

    evidence = _assemble_evidence(context, context.transit_conditions)

    candidate_id = _build_candidate_id(
        context.profile_id, context.event_category, window.start, window.end
    )

    return JaiminiEventCandidate(
        candidate_id=candidate_id,
        event_category=JaiminiEventCategory(context.event_category),
        rule_ids=[context.rule_id],
        dasha_period_ids=[a.period_id for a in context.dasha_activations],
        transit_condition_ids=[c.condition_id for c in context.transit_conditions],
        start=window.start,
        end=window.end,
        peak=peak,
        duration_years=duration_years,
        duration_precision=precision,
        status="ACTIVE",
        profile=context.profile_id,
        evidence=evidence,
        dependencies=context.dependency_paths,
        conflicts=context.conflict_ids,
        provenance=context.mapping_provenance,
        confidence=context.mapping_confidence,
        convergence=convergence,
        tradition=context.mapping_tradition,
        method=context.mapping_method,
        source_reference=context.mapping_source_reference,
    )


def build_candidates(
    contexts: List[CandidateContext],
    windows: List[TemporalWindow],
    convergence: str = "",
) -> List[JaiminiEventCandidate]:
    """Build candidates from multiple contexts and windows.

    Each context is paired with its corresponding window. If there are
    more contexts than windows, remaining contexts use their own dasha window.
    """
    candidates: List[JaiminiEventCandidate] = []

    for i, ctx in enumerate(contexts):
        if i < len(windows):
            window = windows[i]
        else:
            window = _compute_window(ctx.dasha_activations)
            if window is None:
                continue

        candidate = build_candidate(ctx, window, convergence)
        if candidate is not None:
            candidates.append(candidate)

    return candidates
