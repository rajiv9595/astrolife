"""
Phase 8 — core models (§§5, 7, 22, 34–36).

All models frozen, extra-forbid, JSON-serializable. No numeric prediction
scores exist: counts are plain ints, strength/confidence are categorical
labels drawn from canonical vocabularies. Time is ISO-8601 strings;
window algebra compares parsed values without computing astronomy.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Hypothesis statuses (§5). Distinct; UNSUPPORTED covers §57 explicitly.
FORMED = "FORMED"
NOT_FORMED = "NOT_FORMED"
UNKNOWN = "UNKNOWN"
CONFLICTED = "CONFLICTED"
UNSUPPORTED = "UNSUPPORTED"

HYPOTHESIS_STATUSES = (FORMED, NOT_FORMED, UNKNOWN, CONFLICTED, UNSUPPORTED)

# Signal types (§8).
FORMATION_SIGNAL = "FORMATION_SIGNAL"
DASHA_SIGNAL = "DASHA_SIGNAL"
ANTARDASHA_SIGNAL = "ANTARDASHA_SIGNAL"
PRATYANTAR_SIGNAL = "PRATYANTAR_SIGNAL"
TRANSIT_SIGNAL = "TRANSIT_SIGNAL"
JAIMINI_DASHA_SIGNAL = "JAIMINI_DASHA_SIGNAL"
YOGA_ACTIVATION_SIGNAL = "YOGA_ACTIVATION_SIGNAL"
DOSHA_ACTIVATION_SIGNAL = "DOSHA_ACTIVATION_SIGNAL"
CONVERGENCE_SIGNAL = "CONVERGENCE_SIGNAL"
EXCLUSION_SIGNAL = "EXCLUSION_SIGNAL"

SIGNAL_TYPES = (
    FORMATION_SIGNAL, DASHA_SIGNAL, ANTARDASHA_SIGNAL, PRATYANTAR_SIGNAL,
    TRANSIT_SIGNAL, JAIMINI_DASHA_SIGNAL, YOGA_ACTIVATION_SIGNAL,
    DOSHA_ACTIVATION_SIGNAL, CONVERGENCE_SIGNAL, EXCLUSION_SIGNAL,
)

# Source systems (§7).
SOURCE_SYSTEMS = ("PARASHARI", "JAIMINI", "DASHA", "TRANSIT", "STRENGTH",
                  "YOGA", "DOSHA", "CUSTOM")

# Convergence levels (§17). Categorical; never mapped to probability.
NONE = "NONE"
SINGLE_SYSTEM = "SINGLE_SYSTEM"
TWO_SYSTEM = "TWO_SYSTEM"
MULTI_SYSTEM = "MULTI_SYSTEM"
STRONG_MULTI_SYSTEM = "STRONG_MULTI_SYSTEM"

CONVERGENCE_LEVELS = (NONE, SINGLE_SYSTEM, TWO_SYSTEM, MULTI_SYSTEM,
                      STRONG_MULTI_SYSTEM)

# Precision categories (§22), finest first.
EXACT = "EXACT"
DAY = "DAY"
WEEK = "WEEK"
MONTH = "MONTH"
DATE_RANGE = "DATE_RANGE"
DASHA_RANGE = "DASHA_RANGE"
PRECISION_UNKNOWN = "UNKNOWN"

PRECISIONS = (EXACT, DAY, WEEK, MONTH, DATE_RANGE, DASHA_RANGE, PRECISION_UNKNOWN)

# Candidate ranks (§27). Categorical ordering with explicit reasons.
PRIMARY_CANDIDATE = "PRIMARY_CANDIDATE"
SECONDARY_CANDIDATE = "SECONDARY_CANDIDATE"
ALTERNATIVE_CANDIDATE = "ALTERNATIVE_CANDIDATE"
CONFLICTING_CANDIDATE = "CONFLICTING_CANDIDATE"
UNKNOWN_CANDIDATE = "UNKNOWN_CANDIDATE"

CANDIDATE_RANKS = (PRIMARY_CANDIDATE, SECONDARY_CANDIDATE,
                   ALTERNATIVE_CANDIDATE, CONFLICTING_CANDIDATE,
                   UNKNOWN_CANDIDATE)

# Evidence completeness (§§28, 38). NOT statistical probability.
EVIDENCE_COMPLETE = "EVIDENCE_COMPLETE"
EVIDENCE_PARTIAL = "EVIDENCE_PARTIAL"
EVIDENCE_INSUFFICIENT = "EVIDENCE_INSUFFICIENT"
EVIDENCE_CONFLICTED = "EVIDENCE_CONFLICTED"

EVIDENCE_STATES = (EVIDENCE_COMPLETE, EVIDENCE_PARTIAL,
                   EVIDENCE_INSUFFICIENT, EVIDENCE_CONFLICTED)

# Result statuses (§36).
SUCCESS = "SUCCESS"
PARTIAL = "PARTIAL"
RESULT_UNKNOWN = "UNKNOWN"
RESULT_CONFLICTED = "CONFLICTED"
INVALID = "INVALID"

RESULT_STATUSES = (SUCCESS, PARTIAL, RESULT_UNKNOWN, RESULT_CONFLICTED, INVALID)

SUPPORTED_RANGE_START = "1900-01-01T00:00:00Z"
SUPPORTED_RANGE_END = "2100-01-01T00:00:00Z"


class RuleOutcomeInput(BaseModel):
    """Supplied canonical rule outcome. Read, never recomputed."""

    rule_id: str
    rule_version: str = "1.0.0"
    tradition: str = ""
    system: str = ""
    formation: str = ""
    activation: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)
    verification: str = ""
    lifecycle: str = "ACTIVE"
    depends_on: List[str] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}


class DashaPeriodInput(BaseModel):
    """Supplied canonical dasha period row (Vimshottari MD/AD/PD or Chara)."""

    system: str = ""
    profile: str = ""
    level: str = ""
    key: str = ""
    start_iso: str = ""
    end_iso: str = ""
    fingerprint: str = ""

    model_config = {"frozen": True, "extra": "forbid"}


class TransitEventInput(BaseModel):
    """Supplied canonical exact transit event (root timestamp preserved)."""

    planet: str = ""
    kind: str = ""
    natal_target: str = ""
    timestamp_iso: str = ""
    fingerprint: str = ""

    model_config = {"frozen": True, "extra": "forbid"}


class SuppliedConflict(BaseModel):
    conflict_id: str
    rule_a: str = ""
    rule_b: str = ""
    system_a: str = ""
    system_b: str = ""
    detail: str = ""
    status: str = "REPORTED_ONLY"

    model_config = {"frozen": True, "extra": "forbid"}


class PredictionInput(BaseModel):
    """Everything the engine may read. Canonical objects never enter here."""

    chart_fingerprint: str = ""
    calculation_profile: str = ""
    rule_outcomes: List[RuleOutcomeInput] = Field(default_factory=list)
    dasha_periods: List[DashaPeriodInput] = Field(default_factory=list)
    transit_facts: Dict[str, str] = Field(default_factory=dict)
    transit_events: List[TransitEventInput] = Field(default_factory=list)
    has_dasha: bool = True
    has_transit: bool = True
    has_jaimini: bool = True
    has_strength: bool = True
    conflicts: List[SuppliedConflict] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    sources: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}

    def fingerprint(self) -> str:
        import hashlib
        import json
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True,
                             separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class EventSignal(BaseModel):
    signal_id: str
    source_system: str
    source_type: str
    source_id: str
    strength_label: str = ""
    active_from: str = ""
    active_to: str = ""
    exact_time: str = ""
    direction: str = ""
    status: str = ""
    ancestry: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    provenance: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}


class TimingWindow(BaseModel):
    start: str
    end: str
    precision: str = DASHA_RANGE
    source_signals: List[str] = Field(default_factory=list)
    exact_events: List[str] = Field(default_factory=list)
    uncertainty: str = ""
    profile: str = ""
    provenance: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}


class EventHypothesis(BaseModel):
    hypothesis_id: str
    event_type: str
    event_version: str = "1.0.0"
    status: str = UNKNOWN
    formation_status: str = UNKNOWN
    activation_status: str = UNKNOWN
    timing_status: str = UNKNOWN
    coverage: str = ""
    signals: List[EventSignal] = Field(default_factory=list)
    supporting_rules: List[str] = Field(default_factory=list)
    supporting_facts: List[str] = Field(default_factory=list)
    supporting_dashas: List[str] = Field(default_factory=list)
    supporting_transits: List[str] = Field(default_factory=list)
    supporting_jaimini: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list)
    convergence: str = NONE
    windows: List[TimingWindow] = Field(default_factory=list)
    rank: str = UNKNOWN_CANDIDATE
    rank_reason: str = ""
    evidence_state: str = EVIDENCE_INSUFFICIENT
    provenance: Dict[str, Any] = Field(default_factory=dict)
    input_fingerprint: str = ""
    output_fingerprint: str = ""

    model_config = {"frozen": True, "extra": "forbid"}

    def compute_output_fingerprint(self) -> str:
        import hashlib
        import json
        payload = json.dumps(self.model_dump(mode="json", exclude={"output_fingerprint"}),
                             sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class PredictionProfile(BaseModel):
    profile_id: str
    version: str = "1.0.0"
    traditions: List[str] = Field(default_factory=list)
    event_rules: List[str] = Field(default_factory=list)
    dasha_systems: List[str] = Field(default_factory=list)
    transit_systems: List[str] = Field(default_factory=list)
    convergence_policy: Dict[str, Any] = Field(default_factory=dict)
    conflict_policy: Dict[str, Any] = Field(default_factory=dict)
    uncertainty_policy: Dict[str, Any] = Field(default_factory=dict)
    window_policy: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}


class PredictionRequest(BaseModel):
    request_id: str
    chart_fingerprint: str = ""
    event_types: List[str] = Field(default_factory=list)
    event_ids: List[str] = Field(default_factory=list)
    prediction_profile: str = ""
    start: str = ""
    end: str = ""
    requested_timing_precision: str = DATE_RANGE
    traditions: List[str] = Field(default_factory=list)
    dasha_profiles: List[str] = Field(default_factory=list)
    include_alternatives: bool = True
    include_conflicts: bool = True
    notes: str = ""

    model_config = {"frozen": True, "extra": "forbid"}


class PredictionResult(BaseModel):
    request: PredictionRequest
    status: str = SUCCESS
    candidates: List[EventHypothesis] = Field(default_factory=list)
    rejected_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    evidence_state: str = EVIDENCE_INSUFFICIENT
    profile: str = ""
    input_fingerprint: str = ""
    output_fingerprint: str = ""
    warnings: List[str] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}

    def compute_output_fingerprint(self) -> str:
        import hashlib
        import json
        payload = json.dumps(self.model_dump(mode="json", exclude={"output_fingerprint"}),
                             sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
