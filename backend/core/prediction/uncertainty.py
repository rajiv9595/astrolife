"""
Phase 8 — uncertainty helpers (re-export; single implementation in conflicts).

Missing data is never negative evidence: MISSING != NOT_FORMED,
MISSING != INACTIVE, MISSING != NO_EVENT. All missing inputs surface in
hypothesis.unknowns and degrade evidence_state categorically.
"""
from __future__ import annotations

from .conflicts import collect_unknowns, evidence_state

__all__ = ["collect_unknowns", "evidence_state"]
