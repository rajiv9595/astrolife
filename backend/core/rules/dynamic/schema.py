"""
Phase 6A — Dynamic Rule Knowledge Specification: schema.

Versioned, serializable, data-only rule definitions. No executable code,
no timestamps, no random IDs. All fields explicitly typed.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = "6A/1.0.0"


class RuleIdentity(BaseModel):
    rule_id: str = Field(description="Stable ID, e.g. DEMO.CUSTOM.SYNTHETIC_GOLDEN")
    rule_version: str = Field(description="Immutable semver, e.g. 1.0.0")
    rule_name: str = ""
    description: str = ""
    model_config = {"frozen": True}


class RuleClassification(BaseModel):
    system: str = Field(description="E.g. JAIMINI, PARASHARI, CUSTOM")
    tradition: str = Field(
        description="PARASHARI_CLASSICAL | JAIMINI_CLASSICAL | TRADITION_DEPENDENT | MODERN_COMMON | WESTERN | CUSTOM_DEVELOPER"
    )
    category: str = ""
    subcategory: str = ""
    model_config = {"frozen": True}


class SourceReference(BaseModel):
    source_id: str = ""
    title: str = ""
    author: str = ""
    publication: str = ""
    locator: str = ""
    quotation: str = ""
    verification_status: str = Field(
        description="VERIFIED | UNVERIFIED | CONTESTED | SECONDARY | TRADITIONAL | USER_SUPPLIED | CUSTOM"
    )
    model_config = {"frozen": True}


class RuleProvenance(BaseModel):
    source_reference: SourceReference = Field(default_factory=SourceReference)
    source_type: str = ""
    source_author: str = ""
    source_title: str = ""
    source_locator: str = ""
    provenance_status: str = ""
    confidence: str = ""
    model_config = {"frozen": True}


class ConditionNode(BaseModel):
    op: str = Field(description="Primitive name or ALL | ANY | NOT | EXACTLY_N | AT_LEAST_N | AT_MOST_N")
    params: Dict[str, Any] = Field(default_factory=dict)
    children: List["ConditionNode"] = Field(default_factory=list)
    n: Optional[int] = Field(default=None, description="Threshold for EXACTLY_N / AT_LEAST_N / AT_MOST_N")
    model_config = {"frozen": True}


ConditionNode.model_rebuild()


class RuleSemantics(BaseModel):
    prerequisites: List[str] = Field(default_factory=list)
    formation: Optional[ConditionNode] = None
    cancellation: Optional[ConditionNode] = None
    mitigation: Optional[ConditionNode] = None
    derived_facts: List[str] = Field(default_factory=list)
    model_config = {"frozen": True}


class RuleDependencies(BaseModel):
    input_facts: List[str] = Field(default_factory=list)
    rule_dependencies: List[str] = Field(default_factory=list)
    varga_dependencies: List[str] = Field(default_factory=list)
    dasha_dependencies: List[str] = Field(default_factory=list)
    transit_dependencies: List[str] = Field(default_factory=list)
    strength_dependencies: List[str] = Field(default_factory=list)
    model_config = {"frozen": True}


class RuleEvidenceSpec(BaseModel):
    evidence_requirements: List[str] = Field(default_factory=list)
    evidence_paths: List[str] = Field(default_factory=list)
    model_config = {"frozen": True}


class RuleLifecycle(BaseModel):
    status: str = Field(description="ACTIVE | DEPRECATED | SUPERSEDED | DRAFT")
    effective_from: str = ""
    supersedes: str = ""
    deprecated_by: str = ""
    model_config = {"frozen": True}


class RuleValidationInfo(BaseModel):
    validation_status: str = Field(description="UNVALIDATED | VALID | INVALID | NEEDS_REVIEW")
    validation_notes: str = ""
    test_requirements: List[str] = Field(default_factory=list)
    model_config = {"frozen": True}


class DynamicRuleDefinition(BaseModel):
    identity: RuleIdentity
    classification: RuleClassification
    provenance: RuleProvenance
    semantics: RuleSemantics
    dependencies: RuleDependencies
    evidence: RuleEvidenceSpec = Field(default_factory=RuleEvidenceSpec)
    lifecycle: RuleLifecycle = Field(default_factory=RuleLifecycle)
    validation: RuleValidationInfo = Field(default_factory=RuleValidationInfo)
    schema_version: str = SCHEMA_VERSION
    model_config = {"frozen": True}
