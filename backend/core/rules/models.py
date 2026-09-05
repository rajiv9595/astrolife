"""
Rule Engine Models — Astrolife V2 Phase 5A
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

from .enums import (
    RuleCategory, RuleTradition, RuleStatus, FormationStatus, StrengthStatus,
    ActivationStatus, CancellationStatus, MitigationStatus, ConfidenceLevel,
    SourceType, EvidenceType, LogicalOperator
)


class Provenance(BaseModel):
    source_type: SourceType = SourceType.UNVERIFIED
    source_name: str = ""
    source_reference: str = "UNVERIFIED"
    tradition: RuleTradition = RuleTradition.CUSTOM
    method: str = ""
    implementation_version: str = "1.0.0"
    notes: str = ""


class RuleMetadata(BaseModel):
    rule_id: str
    rule_version: str = "1.0.0"
    name: str
    category: RuleCategory
    tradition: RuleTradition
    school_method: str = ""
    status: RuleStatus = RuleStatus.ENABLED
    description: str = ""
    provenance: Provenance = Field(default_factory=Provenance)
    confidence: ConfidenceLevel = ConfidenceLevel.CUSTOM
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True


class Evidence(BaseModel):
    evidence_type: EvidenceType
    subject: str
    value: Any
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    source: str = ""
    significance: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)


class ActivationRule(BaseModel):
    rule_id: str
    description: str = ""
    evaluator: str = ""  # Reference to evaluator function name


class CancellationRule(BaseModel):
    rule_id: str
    description: str = ""
    evaluator: str = ""
    is_partial: bool = False


class MitigationRule(BaseModel):
    rule_id: str
    description: str = ""
    evaluator: str = ""
    strength_impact: str = ""


class Condition(BaseModel):
    """Base condition model - extended by specific condition types"""
    type: str
    params: Dict[str, Any] = Field(default_factory=dict)
    operator: LogicalOperator = LogicalOperator.AND
    children: List[Condition] = Field(default_factory=list)
    negated: bool = False


class RuleDefinition(BaseModel):
    metadata: RuleMetadata
    formation_conditions: List[Condition] = Field(default_factory=list)
    strength_conditions: List[Condition] = Field(default_factory=list)
    activation_rules: List[ActivationRule] = Field(default_factory=list)
    cancellation_rules: List[CancellationRule] = Field(default_factory=list)
    mitigation_rules: List[MitigationRule] = Field(default_factory=list)
    required_evidence: List[EvidenceType] = Field(default_factory=list)
    custom_evaluator: str = ""  # Optional custom evaluator function name


class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    category: RuleCategory
    tradition: RuleTradition
    method: str
    formation_status: FormationStatus = FormationStatus.NOT_FORMED
    strength_status: StrengthStatus = StrengthStatus.UNKNOWN
    activation_status: ActivationStatus = ActivationStatus.NOT_EVALUATED
    cancellation_status: CancellationStatus = CancellationStatus.NONE
    mitigation_status: MitigationStatus = MitigationStatus.NONE
    confidence: ConfidenceLevel = ConfidenceLevel.CUSTOM
    evidence: List[Evidence] = Field(default_factory=list)
    relevant_planets: List[str] = Field(default_factory=list)
    relevant_houses: List[int] = Field(default_factory=list)
    relevant_vargas: List[int] = Field(default_factory=list)
    provenance: Provenance = Field(default_factory=Provenance)
    notes: str = ""
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    rule_version: str = "1.0.0"

    def is_active(self) -> bool:
        return self.activation_status in (ActivationStatus.ACTIVE, ActivationStatus.PARTIALLY_ACTIVE)

    def is_cancelled(self) -> bool:
        return self.cancellation_status == CancellationStatus.FULL

    def is_mitigated(self) -> bool:
        return self.mitigation_status != MitigationStatus.NONE

    def effective_status(self) -> str:
        if self.formation_status == FormationStatus.NOT_FORMED:
            return "NOT_FORMED"
        if self.is_cancelled():
            return "CANCELLED"
        if self.is_active():
            return "ACTIVE"
        return "FORMED_BUT_INACTIVE"


class RuleContextModel(BaseModel):
    """Immutable context for deterministic rule evaluation (Pydantic model for serialization)"""
    chart_facts: Any  # ChartFacts from core.calculation.models
    strength_report: Optional[Any] = None  # StrengthReport from core.strength.models
    varga_facts: Optional[Dict[str, Any]] = None  # All vargas from varga engine
    dynamic_state: Optional[Any] = None  # DynamicAstrologyState
    evaluation_datetime: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True


class EvaluationResult(BaseModel):
    rule_results: List[RuleResult] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    context_hash: str = ""
    total_rules: int = 0
    formed_count: int = 0
    active_count: int = 0
    cancelled_count: int = 0
    mitigated_count: int = 0

    def get_by_id(self, rule_id: str) -> Optional[RuleResult]:
        for r in self.rule_results:
            if r.rule_id == rule_id:
                return r
        return None

    def get_by_category(self, category: RuleCategory) -> List[RuleResult]:
        return [r for r in self.rule_results if r.category == category]

    def get_by_tradition(self, tradition: RuleTradition) -> List[RuleResult]:
        return [r for r in self.rule_results if r.tradition == tradition]

    def get_active(self) -> List[RuleResult]:
        return [r for r in self.rule_results if r.is_active()]

    def get_formed(self) -> List[RuleResult]:
        return [r for r in self.rule_results if r.formation_status == FormationStatus.FORMED]


class ConditionEvaluationResult(BaseModel):
    condition_id: str
    condition_type: str
    passed: bool
    evidence: List[Evidence] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    children: List[ConditionEvaluationResult] = Field(default_factory=list)


class RuleEvaluationTrace(BaseModel):
    rule_id: str
    formation_trace: List[ConditionEvaluationResult] = Field(default_factory=list)
    strength_trace: List[ConditionEvaluationResult] = Field(default_factory=list)
    activation_trace: List[ConditionEvaluationResult] = Field(default_factory=list)
    cancellation_trace: List[ConditionEvaluationResult] = Field(default_factory=list)
    mitigation_trace: List[ConditionEvaluationResult] = Field(default_factory=list)