"""
Phase 6B — production dynamic rule result. Timestamp-free; datetimes appear
only as canonical data inside resolved facts, never as creation metadata.
"""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class DynamicRuleResult(BaseModel):
    rule_id: str
    rule_version: str
    status: str = Field(description="FORMED | NOT_FORMED | UNKNOWN | INVALID")
    formation: str = ""
    cancellation: str = ""
    mitigation: str = ""
    final_state: str = Field(
        default="",
        description="FORMED | NOT_FORMED | UNKNOWN | INVALID | FORMED_CANCELLED | FORMED_MITIGATED")
    diagnostics: List[str] = Field(default_factory=list)
    evidence_paths: List[str] = Field(default_factory=list)
    dependency_paths: List[str] = Field(default_factory=list)
    resolved_facts: Dict[str, Any] = Field(default_factory=dict)
    unresolved_facts: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    evaluation_profile: str = "6B/1.0.0"
    model_config = {"frozen": True}
