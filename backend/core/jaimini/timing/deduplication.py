"""
Phase 5H — Candidate Deduplicator.

Merges overlapping candidates with identical rule sets and categories.
Preserves all evidence from merged candidates.

Deterministic: merge order is sorted by candidate_id.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..candidates import JaiminiEventCandidate

from .models import TemporalWindow


def _candidate_key(c: JaiminiEventCandidate) -> Tuple[str, str, str]:
    """Deterministic merge key: (profile, category, frozen_rule_set)."""
    return (
        c.profile,
        c.event_category.value,
        "|".join(sorted(c.rule_ids)),
    )


def _windows_overlap(a: JaiminiEventCandidate, b: JaiminiEventCandidate) -> bool:
    """Check if two candidate windows overlap."""
    return a.start < b.end and b.start < a.end


def _merge_candidates(
    a: JaiminiEventCandidate,
    b: JaiminiEventCandidate,
) -> JaiminiEventCandidate:
    """Merge two overlapping candidates with the same key.

    The merged candidate has:
    - Union of rule_ids, dasha_period_ids, transit_condition_ids
    - Earliest start, latest end
    - Union of evidence, dependencies, conflicts
    - Convergence = max of the two (MULTI > DOUBLE > SINGLE)
    """
    start = min(a.start, b.start)
    end = max(a.end, b.end)
    peak = a.peak if a.peak is not None else b.peak

    rule_ids = sorted(set(a.rule_ids + b.rule_ids))
    dasha_ids = sorted(set(a.dasha_period_ids + b.dasha_period_ids))
    transit_ids = sorted(set(a.transit_condition_ids + b.transit_condition_ids))
    evidence = sorted(set(a.evidence + b.evidence))
    dependencies = sorted(set(a.dependencies + b.dependencies))
    conflicts = sorted(set(a.conflicts + b.conflicts))

    from core.jaimini.candidates import ConvergenceLevel
    conv_order = {
        ConvergenceLevel.SINGLE_CONDITION.value: 0,
        ConvergenceLevel.DOUBLE_CONDITION.value: 1,
        ConvergenceLevel.MULTI_CONDITION.value: 2,
    }
    max_conv = max(
        conv_order.get(a.convergence, 0),
        conv_order.get(b.convergence, 0),
    )
    convergence = [k for k, v in conv_order.items() if v == max_conv][0]

    duration_days = (end - start).total_seconds() / 86400.0
    duration_years = duration_days / 365.25

    candidate_id = f"{a.profile}:{a.event_category.value}:{start.isoformat()}:{end.isoformat()}"

    return JaiminiEventCandidate(
        candidate_id=candidate_id,
        event_category=a.event_category,
        rule_ids=rule_ids,
        dasha_period_ids=dasha_ids,
        transit_condition_ids=transit_ids,
        start=start,
        end=end,
        peak=peak,
        duration_years=duration_years,
        duration_precision=a.duration_precision,
        status=a.status,
        profile=a.profile,
        evidence=evidence,
        dependencies=dependencies,
        conflicts=conflicts,
        provenance=a.provenance,
        confidence=a.confidence,
        convergence=convergence,
        tradition=a.tradition,
        method=a.method,
        source_reference=a.source_reference,
    )


def deduplicate_candidates(
    candidates: List[JaiminiEventCandidate],
) -> List[JaiminiEventCandidate]:
    """Deduplicate and merge overlapping candidates.

    Candidates are grouped by (profile, category, rule_set). Within each
    group, overlapping candidates are merged. Non-overlapping candidates
    in the same group are kept separate.

    Returns sorted by (start, candidate_id) for determinism.
    """
    if not candidates:
        return []

    groups: Dict[Tuple[str, str, str], List[JaiminiEventCandidate]] = {}
    for c in candidates:
        key = _candidate_key(c)
        if key not in groups:
            groups[key] = []
        groups[key].append(c)

    result: List[JaiminiEventCandidate] = []

    for key in sorted(groups.keys()):
        group = sorted(groups[key], key=lambda c: (c.start, c.candidate_id))

        merged: List[JaiminiEventCandidate] = []
        for c in group:
            if merged and _windows_overlap(merged[-1], c):
                merged[-1] = _merge_candidates(merged[-1], c)
            else:
                merged.append(c)

        result.extend(merged)

    result.sort(key=lambda c: (c.start, c.candidate_id))
    return result
