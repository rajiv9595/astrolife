"""
Phase 5H — Jaimini Timing + Event-Candidate Engine.

Deterministic structured timing engine. Zero prediction, zero AI,
zero outcome interpretation. Produces event candidates: structured
time windows where deterministic astrological conditions are active.
"""
from .pipeline import evaluate_jaimini_timing
from .candidates import build_candidates
from .dasha_activation import activate_dasha_periods
from .transit_activation import activate_transits
from .convergence import classify_convergence
from .deduplication import deduplicate_candidates
from .conflicts import report_candidate_conflicts
from .profile_isolation import ProfileIsolationGuard
from .golden import capture_golden_snapshot, verify_golden_snapshot

__all__ = [
    "evaluate_jaimini_timing",
    "build_candidates",
    "activate_dasha_periods",
    "activate_transits",
    "classify_convergence",
    "deduplicate_candidates",
    "report_candidate_conflicts",
    "ProfileIsolationGuard",
    "capture_golden_snapshot",
    "verify_golden_snapshot",
]
