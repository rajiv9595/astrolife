"""
Phase 9 — Research workbench models.

Declarative, JSON-serializable, deterministic. No executable code,
no wall-clock calls, no randomness in canonical results.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

RESEARCH_STATUSES = (
    "DRAFT",
    "EXPERIMENTAL",
    "VALIDATED",
    "TESTED",
    "REVIEW_PENDING",
    "APPROVED_FOR_PROMOTION",
    "PROMOTED",
    "REJECTED",
    "ARCHIVED",
)

# Legal research lifecycle transitions. No EXPERIMENTAL->ACTIVE shortcut;
# production ACTIVE lives in a different namespace (production catalogue).
RESEARCH_TRANSITIONS = frozenset({
    ("DRAFT", "EXPERIMENTAL"),
    ("EXPERIMENTAL", "VALIDATED"),
    ("VALIDATED", "TESTED"),
    ("TESTED", "REVIEW_PENDING"),
    ("REVIEW_PENDING", "APPROVED_FOR_PROMOTION"),
    ("REVIEW_PENDING", "REJECTED"),
    ("APPROVED_FOR_PROMOTION", "PROMOTED"),
    ("REJECTED", "DRAFT"),
    ("VALIDATED", "DRAFT"),
    ("TESTED", "DRAFT"),
    ("EXPERIMENTAL", "ARCHIVED"),
    ("REJECTED", "ARCHIVED"),
    ("PROMOTED", "ARCHIVED"),
})

RESEARCH_TRADITIONS = (
    "PARASHARI_CLASSICAL",
    "JAIMINI_CLASSICAL",
    "TRADITION_DEPENDENT",
    "MODERN_COMMON",
    "WESTERN",
    "CUSTOM_DEVELOPER",
    "EXPERIMENTAL",
)

CLAIM_TYPES = (
    "SOURCE_CLAIM",
    "IMPLEMENTATION_CLAIM",
    "INTERPRETATION_CLAIM",
    "DEVELOPER_NOTE",
)

VERIFICATION_STATES = (
    "VERIFIED",
    "UNVERIFIED",
    "CONTESTED",
    "USER_SUPPLIED",
    "TRADITIONAL",
)

PROMOTION_GATES = (
    "schema_valid",
    "security_valid",
    "dependency_valid",
    "applicability_valid",
    "evidence_valid",
    "fixture_valid",
    "regression_valid",
    "provenance_valid",
    "tradition_valid",
    "profile_valid",
    "review_complete",
    "lifecycle_valid",
)

APPLICABILITY_STATES = ("APPLICABLE", "NOT_APPLICABLE", "UNKNOWN", "INVALID")
EVIDENCE_CELL_STATES = ("VERIFIED", "UNVERIFIED", "CONTESTED", "USER_SUPPLIED", "MISSING")
DEPENDENCY_CELL_STATES = ("RESOLVED", "MISSING", "INVALID", "CONFLICTED", "UNAVAILABLE")
EXPERIMENT_OUTCOMES = ("PASS", "FAIL", "UNKNOWN", "CONFLICT")
HYPOTHESIS_STATUSES = ("OPEN", "SUPPORTED_BY_EXPERIMENT", "INCONCLUSIVE", "CONTRADICTED", "REJECTED")
REVIEW_DECISIONS = ("APPROVE", "REQUEST_CHANGES", "REJECT")


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def fingerprint_of(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


class ResearchRuleAuthoring(BaseModel):
    rule_id: str
    rule_version: str = "0.1.0"
    rule_name: str = ""
    description: str = ""
    tradition: str = "EXPERIMENTAL"
    category: str = "CUSTOM"
    formation: Dict[str, Any] = Field(default_factory=dict)
    cancellation: Optional[Dict[str, Any]] = None
    mitigation: Optional[Dict[str, Any]] = None
    activation: Optional[Dict[str, Any]] = None
    applicability: Dict[str, Any] = Field(default_factory=dict)
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    evidence_requirements: List[str] = Field(default_factory=list)
    event_applicability: List[str] = Field(default_factory=list)
    timing_applicability: Dict[str, Any] = Field(default_factory=dict)
    lifecycle_status: str = "EXPERIMENTAL"

    model_config = {"frozen": True}


class ResearchSource(BaseModel):
    source_id: str
    title: str = ""
    author: str = ""
    edition: str = ""
    publication: str = ""
    locator: str = ""
    quotation: str = ""
    tradition: str = "EXPERIMENTAL"
    verification_status: str = "UNVERIFIED"

    model_config = {"frozen": True}


class ResearchClaim(BaseModel):
    claim_id: str
    claim_type: str = "DEVELOPER_NOTE"
    statement: str = ""
    source_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    rule_ids: List[str] = Field(default_factory=list)
    tradition: str = "EXPERIMENTAL"
    verification_status: str = "UNVERIFIED"
    status: str = "OPEN"

    model_config = {"frozen": True}


class ResearchEvidence(BaseModel):
    evidence_id: str
    evidence_type: str = "RESEARCH_OBSERVATION"
    subject: str = ""
    value: Any = None
    source: str = ""
    verification_status: str = "UNVERIFIED"
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


class ResearchFixture(BaseModel):
    fixture_id: str
    description: str = ""
    chart_input_ref: str = "golden"
    facts: Dict[str, Any] = Field(default_factory=dict)
    expected_formation: str = "FORMED"
    expected_applicability: str = "APPLICABLE"
    expected_timing: Optional[Dict[str, Any]] = None
    expected_conflicts: List[str] = Field(default_factory=list)
    expected_evidence_state: str = "UNVERIFIED"
    expected_provenance: Dict[str, Any] = Field(default_factory=dict)
    expected_status: str = "PASS"
    fixture_kind: str = "positive"

    model_config = {"frozen": True}


class ResearchRulePackage(BaseModel):
    package_id: str
    package_version: str = "0.1.0"
    author: str = ""
    author_email: str = ""
    description: str = ""
    rules: List[ResearchRuleAuthoring] = Field(default_factory=list)
    sources: List[ResearchSource] = Field(default_factory=list)
    claims: List[ResearchClaim] = Field(default_factory=list)
    evidence: List[ResearchEvidence] = Field(default_factory=list)
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    fixtures: List[ResearchFixture] = Field(default_factory=list)
    profiles: List[str] = Field(default_factory=list)
    experiments: List[str] = Field(default_factory=list)
    review: Dict[str, Any] = Field(default_factory=dict)
    lifecycle: str = "EXPERIMENTAL"
    fingerprint: str = ""

    model_config = {"frozen": True}


class ResearchExperimentResult(BaseModel):
    experiment_id: str
    package_id: str
    package_version: str = ""
    rule_id: str
    rule_version: str = ""
    profile: str = ""
    fixtures_tested: int = 0
    observed_match_count: int = 0
    observed_mismatch_count: int = 0
    unknown_count: int = 0
    conflict_count: int = 0
    outcomes: List[Dict[str, Any]] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    summary: Dict[str, Any] = Field(default_factory=dict)
    fingerprint: str = ""

    model_config = {"frozen": True}


class TechniqueComparisonResult(BaseModel):
    comparison_id: str
    techniques: List[Dict[str, Any]] = Field(default_factory=list)
    fixture_set: List[str] = Field(default_factory=list)
    fingerprint: str = ""

    model_config = {"frozen": True}


class ResearchHypothesis(BaseModel):
    hypothesis_id: str
    statement: str = ""
    assumptions: List[str] = Field(default_factory=list)
    rule_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    fixture_ids: List[str] = Field(default_factory=list)
    expected_behavior: str = ""
    observed_behavior: str = ""
    status: str = "OPEN"

    model_config = {"frozen": True}


class ResearchNotebook(BaseModel):
    notebook_id: str
    title: str = ""
    hypothesis: str = ""
    objective: str = ""
    packages: List[str] = Field(default_factory=list)
    rules: List[str] = Field(default_factory=list)
    fixtures: List[str] = Field(default_factory=list)
    experiments: List[str] = Field(default_factory=list)
    comparisons: List[str] = Field(default_factory=list)
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    conclusions: List[str] = Field(default_factory=list)
    developer_notes: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    fingerprint: str = ""

    model_config = {"frozen": True}


class ReviewRecord(BaseModel):
    review_id: str
    rule_id: str
    rule_version: str = ""
    reviewer: str = ""
    review_status: str = "PENDING"
    gate_results: Dict[str, Any] = Field(default_factory=dict)
    concerns: List[str] = Field(default_factory=list)
    required_changes: List[str] = Field(default_factory=list)
    decision: str = "REQUEST_CHANGES"
    provenance: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


class PromotionRequest(BaseModel):
    request_id: str
    rule_id: str
    rule_version: str = ""
    package_id: str = ""
    package_version: str = ""
    requested_by: str = ""
    target_catalogue: str = ""
    target_tradition: str = ""
    target_profile: str = ""
    target_version: str = ""
    required_validation: bool = True
    required_review: bool = True
    source_state: str = "UNVERIFIED"
    evidence_state: str = "UNVERIFIED"
    regression_state: str = "UNKNOWN"
    approval_state: str = "PENDING"
    status: str = "PENDING"

    model_config = {"frozen": True}


class PromotionAuditEntry(BaseModel):
    request_id: str
    requested_state: str = ""
    gate_results: Dict[str, Any] = Field(default_factory=dict)
    reviewer_decision: str = ""
    package_fingerprint: str = ""
    rule_fingerprint: str = ""
    evidence_fingerprint: str = ""
    resulting_state: str = ""
    notes: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class ResearchSnapshot(BaseModel):
    snapshot_id: str
    package: Dict[str, Any] = Field(default_factory=dict)
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    versions: Dict[str, str] = Field(default_factory=dict)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    fixtures: List[Dict[str, Any]] = Field(default_factory=list)
    experiments: List[Dict[str, Any]] = Field(default_factory=list)
    results: List[Dict[str, Any]] = Field(default_factory=list)
    fingerprint: str = ""

    model_config = {"frozen": True}
