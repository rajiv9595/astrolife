"""
Phase 7 — shared agent data models.

Finding types, result statuses, categorical confidence labels.
No numeric astrology scores exist anywhere in this package by construction:
confidence is a closed categorical vocabulary validated with extra="forbid".
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Finding types (§8). Every finding declares exactly one.
FACT = "FACT"
DERIVED_FACT = "DERIVED_FACT"
RULE_RESULT = "RULE_RESULT"
INTERPRETATION = "INTERPRETATION"
UNKNOWN = "UNKNOWN"
CONFLICT = "CONFLICT"
WARNING = "WARNING"

FINDING_TYPES = (FACT, DERIVED_FACT, RULE_RESULT, INTERPRETATION, UNKNOWN, CONFLICT, WARNING)

# Agent result statuses (§7). Never collapsed.
SUCCESS = "SUCCESS"
PARTIAL = "PARTIAL"
UNKNOWN_STATUS = "UNKNOWN"
INVALID = "INVALID"
CONFLICTED = "CONFLICTED"

AGENT_STATUSES = (SUCCESS, PARTIAL, UNKNOWN_STATUS, INVALID, CONFLICTED)

# Categorical confidence only (§8). Floats are rejected by the validator.
CANONICAL = "CANONICAL"
SUPPLIED_RESULT = "SUPPLIED_RESULT"
SUPPORTED = "SUPPORTED"
TRADITION_DEPENDENT = "TRADITION_DEPENDENT"
UNSUPPORTED_INTERPRETATION = "UNSUPPORTED_INTERPRETATION"

CONFIDENCE_LABELS = (CANONICAL, SUPPLIED_RESULT, SUPPORTED, TRADITION_DEPENDENT,
                     UNSUPPORTED_INTERPRETATION)


class Finding(BaseModel):
    """One structured finding. Statement prose is presentation, never identity."""

    finding_id: str
    type: str
    statement: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    supporting_inputs: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    rule_ids: List[str] = Field(default_factory=list)
    confidence_label: str = SUPPORTED
    tradition: str = ""
    provenance: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}


class AgentProvenance(BaseModel):
    """Traceability chain: conclusion -> inputs -> canonical fact/rule result."""

    agent_id: str
    agent_version: str
    input_fingerprint: str
    evidence_ids: List[str] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)
    chain: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}


class RuleResultSummary(BaseModel):
    """Supplied (never computed) rule outcome. Agents restate these."""

    rule_id: str
    tradition: str = ""
    formation: str = ""
    cancellation: str = ""
    mitigation: str = ""
    activation: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}


class ConflictSummary(BaseModel):
    """Supplied canonical conflict. Agents propagate, never resolve."""

    conflict_id: str
    rule_a: str
    rule_b: str
    conflict_type: str = "REPORTED_ONLY"
    status: str = "REPORTED_ONLY"
    detail: str = ""

    model_config = {"frozen": True, "extra": "forbid"}


class TimingCandidateSummary(BaseModel):
    """Supplied timing candidate. Agents explain, never date."""

    candidate_id: str
    kind: str = ""
    window: str = ""
    basis_rule_ids: List[str] = Field(default_factory=list)
    detail: str = ""

    model_config = {"frozen": True, "extra": "forbid"}


class ExecutionRecord(BaseModel):
    """Deterministic observability record (§36). No timestamps in fingerprint."""

    agent_id: str
    agent_version: str
    context_fingerprint: str
    input_fingerprint: str
    output_fingerprint: str
    status: str
    validation_notes: List[str] = Field(default_factory=list)
    conflict_ids: List[str] = Field(default_factory=list)
    unknown_inputs: List[str] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}

    def fingerprint(self) -> str:
        import hashlib
        import json
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True,
                             separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
