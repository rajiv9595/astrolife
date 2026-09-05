"""
Phase 5H — Candidate Conflict Reporter.

Reports conflicts between candidates using Phase 5F conflict infrastructure.
Never resolves conflicts. Report-only.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field

from ..candidates import JaiminiEventCandidate
from ..conflicts import (
    RuleConflict,
    analyze_conflicts,
    SAME_PROPOSITION_PAIRS,
    DIRECT_CONTRADICTION,
    DIFFERENT_DIMENSIONS,
    TRADITION_VARIANT,
    INSUFFICIENT_INFORMATION,
)


class CandidateConflict(BaseModel):
    """Conflict between two candidates (different rule sets, same category+profile)."""

    candidate_a_id: str
    candidate_b_id: str
    rule_a: str
    rule_b: str
    conflict_class: str
    detail: str = ""
    resolution: str = "REPORTED_ONLY"

    model_config = {"frozen": True}


def report_candidate_conflicts(
    candidates: List[JaiminiEventCandidate],
) -> List[CandidateConflict]:
    """Report pairwise conflicts between candidates.

    Two candidates conflict if they:
    1. Share the same profile + event_category
    2. Have overlapping time windows
    3. Contain rules that are in known conflict pairs (from Phase 5F)

    Returns sorted by (candidate_a_id, candidate_b_id) for determinism.
    """
    if len(candidates) < 2:
        return []

    conflicts: List[CandidateConflict] = []
    conflict_pairs = {(a, b): prop for a, b, prop in SAME_PROPOSITION_PAIRS}

    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            ca = candidates[i]
            cb = candidates[j]

            if ca.profile != cb.profile:
                continue
            if ca.event_category != cb.event_category:
                continue
            if ca.start >= cb.end or cb.start >= ca.end:
                continue

            for ra in ca.rule_ids:
                for rb in cb.rule_ids:
                    pair = tuple(sorted([ra, rb]))
                    if pair in conflict_pairs:
                        prop = conflict_pairs[pair]
                        conflicts.append(CandidateConflict(
                            candidate_a_id=ca.candidate_id,
                            candidate_b_id=cb.candidate_id,
                            rule_a=ra,
                            rule_b=rb,
                            conflict_class=TRADITION_VARIANT,
                            detail=f"Same category, overlapping window: {prop}",
                        ))

    conflicts.sort(key=lambda c: (c.candidate_a_id, c.candidate_b_id))
    return conflicts
