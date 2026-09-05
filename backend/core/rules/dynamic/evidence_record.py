"""
Phase 6D — Evidence Record Model.

Immutable evidence record linking a rule evaluation step to its source.
Distinct from JaiminiEvidenceGraph nodes — this is the canonical evidence
for dynamic rule evaluation, portable across traditions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


class EvidenceRecord(BaseModel):
    """A single piece of evidence supporting a rule evaluation.

    Unlike JaiminiEvidenceGraph nodes, EvidenceRecord is:
    - Tradition-agnostic
    - Directly source-linked via source_id
    - Carries pass/fail state for the specific condition
    - Immutable after creation
    - No timestamps in deterministic fingerprints
    """

    evidence_id: str
    rule_id: str
    rule_version: str
    condition_path: str                  # e.g. "semantics.formation.children[0].params.planet"
    condition_type: str                  # e.g. "planet_in_sign", "ALL", "ANY"
    claim_id: Optional[str] = None       # links to ClaimRecord if applicable
    source_id: Optional[str] = None      # links to SourceRecord
    fact_path: Optional[str] = None      # e.g. "natal.Mars.sign", "varga.D9.Mars"
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    passed: bool
    tier: Literal["DIRECT_FACT", "DERIVED_FACT", "RULE_DERIVED", "SOURCE_CLAIM"] = "DIRECT_FACT"
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    def to_fingerprint_dict(self) -> Dict[str, Any]:
        """Canonical dict for fingerprinting (excludes non-deterministic fields)."""
        return {
            "evidence_id": self.evidence_id,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "condition_path": self.condition_path,
            "condition_type": self.condition_type,
            "claim_id": self.claim_id,
            "source_id": self.source_id,
            "fact_path": self.fact_path,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "passed": self.passed,
            "tier": self.tier,
            "description": self.description,
            "metadata": {k: v for k, v in sorted(self.metadata.items())},
        }


class EvidenceBundle(BaseModel):
    """Complete immutable evidence bundle for a rule evaluation.

    Contains everything needed to answer "Why did this rule produce this result?"
    without recalculating. All IDs are stable and deterministic.

    Bundle structure:
      - rule identity + version
      - all evidence records (formation, cancellation, mitigation)
      - resolved/unresolved fact dependencies
      - source references
      - diagnostics
      - fingerprint
    """

    rule_id: str
    rule_version: str
    rule_name: str
    tradition: str
    category: str
    formation_status: str                  # FORMED | NOT_FORMED | UNKNOWN | INVALID
    cancellation_status: str               # CANCELLED | NOT_CANCELLED | PARTIAL | UNKNOWN
    mitigation_status: str                 # MITIGATED | NOT_MITIGATED | PARTIAL | UNKNOWN
    source_references: List[str] = Field(default_factory=list)  # source_ids
    evidence_records: List[EvidenceRecord] = Field(default_factory=list)
    resolved_facts: Dict[str, Any] = Field(default_factory=dict)
    unresolved_facts: List[str] = Field(default_factory=list)
    declared_dependencies: List[str] = Field(default_factory=list)
    used_dependencies: List[str] = Field(default_factory=list)
    diagnostics: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    fingerprint: str = ""

    model_config = {"frozen": True}

    def model_post_init(self, __context: Any) -> None:
        """Compute fingerprint after initialization if not set."""
        if not self.fingerprint:
            import hashlib
            import json
            canonical = {
                "rule_id": self.rule_id,
                "rule_version": self.rule_version,
                "rule_name": self.rule_name,
                "tradition": self.tradition,
                "category": self.category,
                "formation_status": self.formation_status,
                "cancellation_status": self.cancellation_status,
                "mitigation_status": self.mitigation_status,
                "source_references": sorted(self.source_references),
                "evidence_records": [e.to_fingerprint_dict() for e in sorted(self.evidence_records, key=lambda x: x.evidence_id)],
                "resolved_facts": {k: v for k, v in sorted(self.resolved_facts.items())},
                "unresolved_facts": sorted(self.unresolved_facts),
                "declared_dependencies": sorted(self.declared_dependencies),
                "used_dependencies": sorted(self.used_dependencies),
                "diagnostics": sorted(self.diagnostics),
                "conflicts": sorted(self.conflicts),
            }
            s = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
            object.__setattr__(self, "fingerprint", hashlib.sha256(s.encode("utf-8")).hexdigest())

    def evidence_by_tier(self, tier: str) -> List[EvidenceRecord]:
        return [e for e in self.evidence_records if e.tier == tier]

    def evidence_by_condition(self, condition_path: str) -> List[EvidenceRecord]:
        return [e for e in self.evidence_records if e.condition_path == condition_path]

    def source_evidence_map(self) -> Dict[str, List[EvidenceRecord]]:
        """Map source_id -> evidence records using that source."""
        result: Dict[str, List[EvidenceRecord]] = {}
        for ev in self.evidence_records:
            if ev.source_id:
                result.setdefault(ev.source_id, []).append(ev)
        return result

    def is_complete(self) -> bool:
        """Check if bundle has all required evidence for its formation status."""
        if self.formation_status == "FORMED":
            return len(self.evidence_records) > 0
        if self.formation_status in ("UNKNOWN", "INVALID"):
            return len(self.unresolved_facts) == 0 and len(self.diagnostics) == 0
        return True  # NOT_FORMED can have empty evidence

    def to_traceability_dict(self) -> Dict[str, Any]:
        """Export for traceability: RESULT → EVALUATION → RULE → DEPS → FACTS → EVIDENCE → SOURCE."""
        return {
            "rule": {
                "rule_id": self.rule_id,
                "rule_version": self.rule_version,
                "rule_name": self.rule_name,
                "tradition": self.tradition,
                "category": self.category,
            },
            "outcome": {
                "formation": self.formation_status,
                "cancellation": self.cancellation_status,
                "mitigation": self.mitigation_status,
            },
            "dependencies": {
                "declared": sorted(self.declared_dependencies),
                "used": sorted(self.used_dependencies),
                "unresolved": sorted(self.unresolved_facts),
            },
            "facts": {
                "resolved": {k: v for k, v in sorted(self.resolved_facts.items())},
            },
            "evidence": [
                {
                    "evidence_id": e.evidence_id,
                    "condition_path": e.condition_path,
                    "condition_type": e.condition_type,
                    "fact_path": e.fact_path,
                    "expected": e.expected_value,
                    "actual": e.actual_value,
                    "passed": e.passed,
                    "tier": e.tier,
                    "source_id": e.source_id,
                    "claim_id": e.claim_id,
                }
                for e in sorted(self.evidence_records, key=lambda e: e.evidence_id)
            ],
            "sources": sorted(self.source_references),
            "diagnostics": sorted(self.diagnostics),
            "conflicts": sorted(self.conflicts),
            "fingerprint": self.fingerprint,
        }