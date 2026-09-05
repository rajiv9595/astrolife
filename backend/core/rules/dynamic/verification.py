"""
Phase 6D — Source Verification Policy.

Explicit VERIFIED requirements. Rejects VERIFIED without sufficient evidence.
Reuses 6A/6C provenance states where possible.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Literal

from pydantic import BaseModel, Field

from .source import (
    SourceRecord,
    SourceManagement,
    VERIFIED,
    UNVERIFIED,
    CONTESTED,
    SECONDARY_STATUS,
    TRADITIONAL,
    USER_SUPPLIED,
    CUSTOM_STATUS,
    ALL_SOURCE_STATUSES,
)


class SourceVerificationPolicy(BaseModel):
    """Policy for source verification state transitions.

    VERIFIED requires:
      - source identity (source_id)
      - locator (chapter, verse, page, section)
      - quotation/evidence content

    Other states have no minimum requirements.
    """

    # Minimum requirements per status
    MIN_FIELDS_FOR_VERIFIED: List[str] = Field(
        default=["source_id", "locator", "quotation"],
        description="Fields that must be non-empty for VERIFIED status"
    )

    ALLOWED_TRANSITIONS: Dict[str, List[str]] = Field(
        default={
            UNVERIFIED: [VERIFIED, CONTESTED, SECONDARY_STATUS, TRADITIONAL, USER_SUPPLIED, CUSTOM_STATUS],
            VERIFIED: [CONTESTED],
            CONTESTED: [VERIFIED, UNVERIFIED],
            SECONDARY_STATUS: [VERIFIED, UNVERIFIED, CONTESTED],
            TRADITIONAL: [VERIFIED, UNVERIFIED, CONTESTED],
            USER_SUPPLIED: [VERIFIED, UNVERIFIED, CONTESTED],
            CUSTOM_STATUS: [VERIFIED, UNVERIFIED, CONTESTED],
        },
        description="Allowed verification state transitions"
    )

    model_config = {"frozen": True}

    def can_transition(self, from_status: str, to_status: str) -> bool:
        """Check if a verification state transition is allowed."""
        return to_status in self.ALLOWED_TRANSITIONS.get(from_status, [])

    def validate_verified(self, source: SourceRecord) -> List[str]:
        """Validate that a source meets VERIFIED requirements.

        Returns list of missing field names (empty = valid).
        """
        missing: List[str] = []
        if not source.source_id or not source.source_id.strip():
            missing.append("source_id")
        if not source.locator or not source.locator.strip():
            missing.append("locator")
        if not source.quotation or not source.quotation.strip():
            missing.append("quotation")
        return missing

    def enforce_verified(self, source: SourceRecord) -> None:
        """Raise ValueError if source is VERIFIED but doesn't meet requirements."""
        if source.verification_status == VERIFIED:
            missing = self.validate_verified(source)
            if missing:
                raise ValueError(
                    f"Source '{source.source_id}' cannot be VERIFIED: "
                    f"missing required fields: {', '.join(missing)}"
                )


# Default policy instance
DEFAULT_VERIFICATION_POLICY = SourceVerificationPolicy()


class SourceVerificationResult(BaseModel):
    """Result of verifying a source or source management object."""

    source_id: str
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    missing_verified_fields: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


def verify_source(source: SourceRecord, policy: SourceVerificationPolicy = DEFAULT_VERIFICATION_POLICY) -> SourceVerificationResult:
    """Verify a single source record against policy."""
    errors: List[str] = []
    warnings: List[str] = []
    missing_verified: List[str] = []

    if source.verification_status == VERIFIED:
        missing_verified = policy.validate_verified(source)
        if missing_verified:
            errors.append(
                f"Source '{source.source_id}' is VERIFIED but missing: {', '.join(missing_verified)}"
            )

    # Warn about empty important fields
    if not source.title or not source.title.strip():
        warnings.append(f"Source '{source.source_id}' has empty title")
    if not source.author or not source.author.strip():
        warnings.append(f"Source '{source.source_id}' has empty author")
    if not source.publication or not source.publication.strip():
        warnings.append(f"Source '{source.source_id}' has empty publication")

    return SourceVerificationResult(
        source_id=source.source_id,
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        missing_verified_fields=missing_verified,
    )


def verify_source_management(
    sm: SourceManagement,
    policy: SourceVerificationPolicy = DEFAULT_VERIFICATION_POLICY
) -> List[SourceVerificationResult]:
    """Verify all sources in a SourceManagement container."""
    results: List[SourceVerificationResult] = []
    for src in sm.list_all_sources():
        results.append(verify_source(src, policy))
    return results


def validate_verification_transition(
    from_status: str,
    to_status: str,
    source: Optional[SourceRecord] = None,
    policy: SourceVerificationPolicy = DEFAULT_VERIFICATION_POLICY
) -> List[str]:
    """Validate a verification state transition.

    Returns list of error messages (empty = valid).
    """
    errors: List[str] = []

    if from_status not in policy.ALLOWED_TRANSITIONS:
        errors.append(f"Unknown source status: {from_status}")
        return errors

    if to_status not in policy.ALLOWED_TRANSITIONS[from_status]:
        errors.append(f"Transition {from_status} -> {to_status} not allowed")
        return errors

    # If transitioning TO VERIFIED, source must meet requirements
    if to_status == VERIFIED and source is not None:
        missing = policy.validate_verified(source)
        if missing:
            errors.append(f"Cannot set VERIFIED: missing {', '.join(missing)}")

    return errors