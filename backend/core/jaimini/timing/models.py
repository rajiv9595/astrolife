"""
Phase 5H — Timing engine models.

Timestamp-free by design except for explicit datetime fields (start, end, peak)
which are tz-aware UTC datetimes passed as data — never wall-clock reads.

All models are immutable (frozen=True) after construction.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Temporal Window
# ============================================================================


class TemporalWindow(BaseModel):
    """Half-open interval [start, end) in UTC."""

    start: datetime = Field(description="Window start, UTC, tz-aware")
    end: datetime = Field(description="Window end, UTC, tz-aware, exclusive")

    model_config = {"frozen": True}

    def overlaps(self, other: "TemporalWindow") -> bool:
        return self.start < other.end and other.start < self.end

    def intersection(self, other: "TemporalWindow") -> Optional["TemporalWindow"]:
        lo = max(self.start, other.start)
        hi = min(self.end, other.end)
        if lo < hi:
            return TemporalWindow(start=lo, end=hi)
        return None

    def duration_days(self) -> float:
        delta = self.end - self.start
        return delta.total_seconds() / 86400.0


# ============================================================================
# Dasha Activation Record
# ============================================================================


class DashaActivationRecord(BaseModel):
    """Records which dasha period activated a candidate window."""

    period_id: str = Field(description="JaiminiDashaPeriod.period_id")
    level: str = Field(description="MAHA_DASHA or ANTARDASHA")
    sign: str = Field(description="Dasha sign")
    start: datetime = Field(description="Dasha period start (UTC)")
    end: datetime = Field(description="Dasha period end (UTC)")
    profile_id: str = Field(description="CharaDashaProfileID value")

    model_config = {"frozen": True}


# ============================================================================
# Transit Condition Record
# ============================================================================


class TransitConditionRecord(BaseModel):
    """Records a transit condition that is met during a candidate window."""

    condition_id: str = Field(
        description="Deterministic ID: {type}:{transit_planet}:{target}"
    )
    condition_type: str = Field(
        description="sign_ingress | conjunction | aspect | station | nakshatra_ingress"
    )
    transit_planet: str
    target: str = Field(description="Natal planet or sign target")
    exact_time: Optional[datetime] = Field(
        default=None,
        description="Exact event time if available (EXACT precision)"
    )
    window: TemporalWindow = Field(
        description="Window during which condition is met"
    )

    model_config = {"frozen": True}


# ============================================================================
# Candidate Context
# ============================================================================


class CandidateContext(BaseModel):
    """Immutable context for building a single candidate.

    Bundles the rule result, dasha activation, transit conditions,
    and all metadata needed to construct a JaiminiEventCandidate.
    """

    rule_id: str
    event_category: str
    rule_formed: bool
    formation_status: str
    dasha_activations: List[DashaActivationRecord] = Field(default_factory=list)
    transit_conditions: List[TransitConditionRecord] = Field(default_factory=list)
    mapping_tradition: str = "JAIMINI"
    mapping_method: str = ""
    mapping_confidence: str = "TRADITION_DEPENDENT"
    mapping_provenance: str = "UNVERIFIED"
    mapping_source_reference: str = "UNVERIFIED"
    evidence_paths: List[str] = Field(default_factory=list)
    dependency_paths: List[str] = Field(default_factory=list)
    conflict_ids: List[str] = Field(default_factory=list)
    profile_id: str = ""

    model_config = {"frozen": True}


# ============================================================================
# Candidate Evaluation (output of timing pipeline)
# ============================================================================


class CandidateEvaluation(BaseModel):
    """Complete timing evaluation output.

    Deterministic: sorted orderings, no hidden timestamps.
    Each candidate is immutable after construction.
    """

    profile_id: str = Field(default="")
    candidates: List[Any] = Field(
        default_factory=list,
        description="JaiminiEventCandidate instances"
    )
    conflicts: List[Any] = Field(
        default_factory=list,
        description="RuleConflict instances from candidate analysis"
    )
    evidence: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    validation: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    evaluation_range: Dict[str, str] = Field(default_factory=dict)
    total_candidates: int = Field(default=0)
    generated_at: str = Field(default="")

    model_config = {"frozen": True}
