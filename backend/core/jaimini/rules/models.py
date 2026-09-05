"""
Phase 5E — Jaimini yoga result models.

Timestamp-free by design: no datetime fields anywhere, so serialized
evaluations are bit-for-bit deterministic. Reuses accepted Phase 5A enums;
does NOT reuse RuleResult (which stamps wall-clock evaluation time).
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.rules.enums import (
    RuleCategory,
    RuleTradition,
    FormationStatus,
    StrengthStatus,
    CancellationStatus,
    MitigationStatus,
    ConfidenceLevel,
    SourceType,
)


class FormationEvidenceItem(BaseModel):
    """Single structured formation check: condition / actual / expected / source."""

    condition: str = Field(description="Condition tested, e.g. 'AK_sign == AmK_sign'")
    actual_value: Any = Field(description="Observed value from canonical facts")
    expected_value: Any = Field(description="Value required for formation")
    source_fact: str = Field(description="Canonical fact layer, e.g. 'JaiminiFacts.chara_karakas'")
    passed: bool = Field(description="Whether this condition held")


class JaiminiRuleResult(BaseModel):
    """Evaluation result for one Jaimini yoga/rule. Formation, cancellation,
    mitigation, and quality are independent layers (formed != strong)."""

    rule_id: str
    name: str
    formed: bool = Field(description="Top-level formation boolean")
    formation_status: FormationStatus = FormationStatus.NOT_FORMED
    quality: StrengthStatus = Field(
        default=StrengthStatus.UNKNOWN,
        description="UNASSESSED (UNKNOWN) unless a defensible quality rule exists"
    )
    cancellation_status: CancellationStatus = CancellationStatus.NONE
    mitigation_status: MitigationStatus = MitigationStatus.NONE
    category: RuleCategory = RuleCategory.JAIMINI
    tradition: RuleTradition = RuleTradition.JAIMINI
    origin_label: str = Field(
        default="TRADITION_DEPENDENT",
        description="CLASSICAL_JAIMINI | TRADITION_DEPENDENT | MODERN_SYNTHESIS"
    )
    method: str = Field(description="Evaluation method key, e.g. 'ak_amk_conjunction'")
    confidence: ConfidenceLevel = ConfidenceLevel.TRADITION_DEPENDENT
    source_type: SourceType = SourceType.UNVERIFIED
    source_reference: str = "UNVERIFIED"
    formation_evidence: List[FormationEvidenceItem] = Field(default_factory=list)
    cancellation_evidence: List[str] = Field(default_factory=list)
    mitigation_evidence: List[str] = Field(default_factory=list)
    strength_factors: List[str] = Field(default_factory=list)
    relevant_planets: List[str] = Field(default_factory=list)
    relevant_signs: List[str] = Field(default_factory=list)
    relevant_houses: List[int] = Field(default_factory=list)
    dependencies: List[str] = Field(
        default_factory=list,
        description="Canonical fact layers consumed, e.g. 'JaiminiFacts.arudha_padas'"
    )
    notes: str = ""
    rule_version: str = "1.0.0"


class YogaOutcome(BaseModel):
    """Internal evaluator output: formation plus independent
    cancellation/mitigation layers. Quality is always UNASSESSED (UNKNOWN)."""

    formed: bool = False
    formation_evidence: List[FormationEvidenceItem] = Field(default_factory=list)
    cancellation_status: CancellationStatus = CancellationStatus.NONE
    cancellation_evidence: List[str] = Field(default_factory=list)
    mitigation_status: MitigationStatus = MitigationStatus.NONE
    mitigation_evidence: List[str] = Field(default_factory=list)
    relevant_planets: List[str] = Field(default_factory=list)
    relevant_signs: List[str] = Field(default_factory=list)
    relevant_houses: List[int] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    notes: str = ""


class JaiminiYogaEvaluation(BaseModel):
    """Deterministic container for a full yoga evaluation run."""

    results: List[JaiminiRuleResult] = Field(description="Ordered by rule_id")
    profile_method: str = ""
    facts_karaka_method: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)
    total_rules: int = 0
    formed_count: int = 0

    def get_by_id(self, rule_id: str) -> Optional[JaiminiRuleResult]:
        for r in self.results:
            if r.rule_id == rule_id:
                return r
        return None
