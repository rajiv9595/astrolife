"""
Phase 6C — Review record system.

Create RuleReviewRecord with:
  review_id, rule_id, version, reviewer_type, decision, notes, diagnostics,
  provenance_decision.

Allowed decisions:
  APPROVED, REJECTED, REQUEST_CHANGES, DEFERRED.

A technically valid rule can still be REVIEW_PENDING (approval is never
automatic from test success alone).
"""

from __future__ import annotations

import hashlib
from typing import List, Optional

from pydantic import BaseModel, Field

from .rule_package import RulePackage


REVIEW_DECISIONS = frozenset({"APPROVED", "REJECTED", "REQUEST_CHANGES", "DEFERRED"})


class RuleReviewRecord(BaseModel):
    """An immutable review record for a rule version."""
    review_id: str
    rule_id: str
    version: str
    reviewer_type: str = "human"  # "human", "auto", "committee"
    decision: str = "DEFERRED"    # "APPROVED" | "REJECTED" | "REQUEST_CHANGES" | "DEFERRED"
    notes: str = ""
    diagnostics: List[str] = Field(default_factory=list)
    provenance_decision: str = ""  # e.g. "ACCEPTED", "REJECTED", "NEEDS_REVIEW"

    model_config = {"frozen": True}


def create_review_record(
    rule_id: str,
    version: str,
    decision: str = "DEFERRED",
    reviewer_type: str = "human",
    notes: str = "",
    diagnostics: Optional[List[str]] = None,
    provenance_decision: str = "",
    review_id: Optional[str] = None,
) -> RuleReviewRecord:
    """Create a deterministic RuleReviewRecord."""
    if decision not in REVIEW_DECISIONS:
        raise ValueError(
            f"Invalid review decision: {decision}. Must be one of {sorted(REVIEW_DECISIONS)}"
        )
    if review_id is None:
        raw_seed = f"{rule_id}:{version}:{reviewer_type}:{decision}:{notes}:{provenance_decision}"
        review_id = f"rev_{hashlib.sha256(raw_seed.encode('utf-8')).hexdigest()[:12]}"

    return RuleReviewRecord(
        review_id=review_id,
        rule_id=rule_id,
        version=version,
        reviewer_type=reviewer_type,
        decision=decision,
        notes=notes,
        diagnostics=diagnostics or [],
        provenance_decision=provenance_decision,
    )


class ReviewOutcome(BaseModel):
    """Outcome of a rule review process."""
    review_id: str
    rule_id: str
    version: str
    decision: str
    reviewer_type: str
    notes: str
    provenance_decision: str
    affected_rule_package: RulePackage

    model_config = {"frozen": True}


class ReviewWorkflow:
    """Manage the review workflow for a RulePackage."""

    @staticmethod
    def submit_for_review(
        rule_package: RulePackage,
        reviewer_type: str = "human",
        notes: str = "",
        provenance_decision: str = "",
    ) -> RuleReviewRecord:
        """Submit a rule package for review."""
        return create_review_record(
            rule_id=rule_package.rule_id,
            version=rule_package.version,
            decision="DEFERRED",
            reviewer_type=reviewer_type,
            notes=notes,
            provenance_decision=provenance_decision,
        )

    @staticmethod
    def approve(record: RuleReviewRecord, notes: str = "") -> RuleReviewRecord:
        """Approve a review record."""
        return create_review_record(
            rule_id=record.rule_id,
            version=record.version,
            decision="APPROVED",
            reviewer_type=record.reviewer_type,
            notes=notes or record.notes,
            diagnostics=record.diagnostics,
            provenance_decision=record.provenance_decision or "ACCEPTED",
        )

    @staticmethod
    def reject(record: RuleReviewRecord, notes: str = "") -> RuleReviewRecord:
        """Reject a review record."""
        return create_review_record(
            rule_id=record.rule_id,
            version=record.version,
            decision="REJECTED",
            reviewer_type=record.reviewer_type,
            notes=notes or record.notes,
            diagnostics=record.diagnostics,
            provenance_decision="REJECTED",
        )

    @staticmethod
    def request_changes(record: RuleReviewRecord, notes: str) -> RuleReviewRecord:
        """Request changes to a rule package."""
        return create_review_record(
            rule_id=record.rule_id,
            version=record.version,
            decision="REQUEST_CHANGES",
            reviewer_type=record.reviewer_type,
            notes=notes,
            diagnostics=record.diagnostics,
            provenance_decision="NEEDS_CHANGES",
        )

    @staticmethod
    def defer(record: RuleReviewRecord, notes: str = "") -> RuleReviewRecord:
        """Defer a review record."""
        return create_review_record(
            rule_id=record.rule_id,
            version=record.version,
            decision="DEFERRED",
            reviewer_type=record.reviewer_type,
            notes=notes or record.notes,
            diagnostics=record.diagnostics,
            provenance_decision=record.provenance_decision,
        )