"""
Dosha Result Models — Astrolife V2 Phase 5C

Structured result model for dosha evaluation.
Separates formation, severity, cancellation, mitigation, activation.
All statuses remain independent — formation does NOT imply severity.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..enums import (
    RuleCategory, RuleTradition, FormationStatus, EvidenceType,
    CancellationStatus, MitigationStatus, ActivationStatus, ConfidenceLevel,
    SourceType,
)
from .enums import (
    DoshaCategory, DoshaSeverity, DoshaFormationStatus,
    DoshaCancellationStatus, DoshaMitigationStatus, DoshaActivationStatus,
    DoshaTradition, DoshaConfidence, DoshaSourceType,
)


class DoshaProvenance(BaseModel):
    """Source tracking for dosha implementation"""
    source_type: DoshaSourceType = DoshaSourceType.UNVERIFIED
    source_name: str = ""
    source_reference: str = "UNVERIFIED"
    tradition: DoshaTradition = DoshaTradition.UNVERIFIED
    method: str = ""
    implementation_version: str = "1.0.0"
    notes: str = ""


class DoshaMetadata(BaseModel):
    """Identification and classification for a dosha rule"""
    dosha_id: str
    dosha_name: str
    dosha_version: str = "1.0.0"
    category: DoshaCategory = DoshaCategory.GENERAL
    tradition: DoshaTradition = DoshaTradition.UNVERIFIED
    school_method: str = ""
    description: str = ""
    provenance: DoshaProvenance = Field(default_factory=DoshaProvenance)
    confidence: DoshaConfidence = DoshaConfidence.UNVERIFIED
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True
    is_controversial: bool = False
    alternative_definitions: List[str] = Field(default_factory=list)


class DoshaEvidence(BaseModel):
    """Individual evidence item for dosha evaluation"""
    evidence_type: str = ""
    subject: str = ""
    value: Any = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    source: str = ""
    significance: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)


class DoshaResult(BaseModel):
    """
    Complete dosha evaluation result.
    
    All statuses are INDEPENDENT:
    - Formation: has the dosha formed?
    - Severity: how strong (categorical, not numerical)
    - Cancellation: has it been cancelled?
    - Mitigation: has it been weakened?
    - Activation: is it currently active?
    
    Formation = FORMED does NOT imply Severity = HIGH.
    Cancellation = FULL does NOT erase formation evidence.
    """
    dosha_id: str
    dosha_name: str
    dosha_version: str = "1.0.0"
    category: DoshaCategory = DoshaCategory.GENERAL
    tradition: DoshaTradition = DoshaTradition.UNVERIFIED
    method: str = ""

    formation_status: DoshaFormationStatus = DoshaFormationStatus.NOT_FORMED
    severity_status: DoshaSeverity = DoshaSeverity.UNKNOWN
    cancellation_status: DoshaCancellationStatus = DoshaCancellationStatus.NONE
    mitigation_status: DoshaMitigationStatus = DoshaMitigationStatus.NONE
    activation_status: DoshaActivationStatus = DoshaActivationStatus.NOT_EVALUATED

    confidence: DoshaConfidence = DoshaConfidence.UNVERIFIED
    evidence: List[DoshaEvidence] = Field(default_factory=list)
    relevant_planets: List[str] = Field(default_factory=list)
    relevant_houses: List[int] = Field(default_factory=list)
    relevant_vargas: List[int] = Field(default_factory=list)
    provenance: DoshaProvenance = Field(default_factory=DoshaProvenance)
    notes: str = ""
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    def is_formed(self) -> bool:
        return self.formation_status == DoshaFormationStatus.FORMED

    def is_cancelled(self) -> bool:
        return self.cancellation_status == DoshaCancellationStatus.FULL

    def is_mitigated(self) -> bool:
        return self.mitigation_status != DoshaMitigationStatus.NONE

    def effective_status(self) -> str:
        """Human-readable effective status combining all independent states"""
        if self.formation_status == DoshaFormationStatus.NOT_FORMED:
            return "NOT_FORMED"
        if self.is_cancelled():
            return "CANCELLED"
        if self.activation_status == DoshaActivationStatus.NOT_EVALUATED:
            return "FORMED_NOT_ACTIVATED"
        if self.is_mitigated():
            return "FORMED_MITIGATED"
        return "FORMED"

    def to_legacy(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility"""
        return {
            "has_dosha": self.is_formed() and not self.is_cancelled(),
            "verdict": self.effective_status(),
            "dosha_id": self.dosha_id,
            "formation": self.formation_status.value,
            "severity": self.severity_status.value,
            "cancellation": self.cancellation_status.value,
            "mitigation": self.mitigation_status.value,
            "activation": self.activation_status.value,
            "confidence": self.confidence.value,
            "method": self.method,
            "tradition": self.tradition.value,
            "evidence_count": len(self.evidence),
        }


class DoshaEvaluationSet(BaseModel):
    """Collection of all dosha results for a chart"""
    dosha_results: List[DoshaResult] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    total_doshas: int = 0
    formed_count: int = 0
    cancelled_count: int = 0
    mitigated_count: int = 0

    def get_by_id(self, dosha_id: str) -> Optional[DoshaResult]:
        for r in self.dosha_results:
            if r.dosha_id == dosha_id:
                return r
        return None

    def get_formed(self) -> List[DoshaResult]:
        return [r for r in self.dosha_results if r.is_formed()]

    def get_active(self) -> List[DoshaResult]:
        return [r for r in self.dosha_results
                if r.is_formed() and not r.is_cancelled()]

    def to_legacy(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility"""
        out = {}
        for r in self.dosha_results:
            out[r.dosha_id] = r.to_legacy()
        return out
