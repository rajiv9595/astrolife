"""
Phase 5G — Jaimini Dasha models. Timestamp-free definitions; datetimes are
tz-aware data (birth anchor + computed boundaries), never wall-clock reads.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DashaDurationEvidence(BaseModel):
    reference_sign: str
    lord: str
    lord_sign: str
    distance_houses: int
    direction: str
    exception: str
    duration_years: float


class JaiminiDashaPeriod(BaseModel):
    """Immutable period fact at one hierarchy level. Identity is deterministic."""

    period_id: str
    dasha_system: str = "JAIMINI_CHARA"
    profile_method: str = "CHARA_DASHA_LAGNA_START_V1"
    level: str = "MAHA_DASHA"
    sign: str = ""
    sequence_index: int = 0
    direction: str = "FORWARD"
    previous_sign: Optional[str] = None
    next_sign: Optional[str] = None
    start_utc_iso: str = ""
    end_utc_iso: str = ""
    duration_years: float = 0.0
    duration_days: float = 0.0
    parent_id: Optional[str] = None
    index_in_parent: Optional[int] = None
    duration_evidence: Optional[DashaDurationEvidence] = None
    antardashas: List["JaiminiDashaPeriod"] = Field(default_factory=list)


JaiminiDashaPeriod.model_rebuild()


class JaiminiDashaResult(BaseModel):
    dasha_system: str = "JAIMINI_CHARA"
    profile_method: str = "CHARA_DASHA_LAGNA_START_V1"
    status: str = "COMPUTED"
    starting_sign: str = ""
    direction: str = "FORWARD"
    birth_utc_iso: str = ""
    total_years: float = 0.0
    periods: List[JaiminiDashaPeriod] = Field(default_factory=list)
    starting_sign_evidence: Dict[str, Any] = Field(default_factory=dict)
    validation: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
