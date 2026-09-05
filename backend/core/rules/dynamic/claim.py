"""
Phase 6D — Claim Record Model.

Structured claim separation: source statement vs rule interpretation vs implementation.
Never merge these into one text field.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Literal

from pydantic import BaseModel, Field


class ClaimRecord(BaseModel):
    """A structured claim with explicit type and provenance.

    Types:
      SOURCE_CLAIM         — "Source text says X" (direct quotation + locator)
      INTERPRETATION_CLAIM — "Tradition interprets X as Y" (commentary/derivation)
      IMPLEMENTATION_CLAIM — "Astrolife implements X as condition Y" (code-level)
      DEVELOPER_NOTE       — Internal documentation, not a source claim

    Each claim is immutable and carries its own verification state.
    """

    claim_id: str
    claim_type: Literal["SOURCE_CLAIM", "INTERPRETATION_CLAIM", "IMPLEMENTATION_CLAIM", "DEVELOPER_NOTE"]
    rule_id: str
    rule_version: str
    text: str
    source_id: Optional[str] = None
    locator: Optional[str] = None
    quotation: Optional[str] = None
    verification_status: Literal["VERIFIED", "UNVERIFIED", "CONTESTED", "USER_SUPPLIED", "TRADITIONAL"] = "UNVERIFIED"
    tradition: Optional[str] = None
    notes: str = ""
    dependencies: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class ClaimRegistry(BaseModel):
    """Deterministic registry of claims for a rule version.

    Claims are stored in sorted order by claim_id for canonical serialization.
    """

    claims: List[ClaimRecord] = Field(default_factory=list)

    model_config = {"frozen": True}

    def add_claim(self, claim: ClaimRecord) -> "ClaimRegistry":
        if any(c.claim_id == claim.claim_id for c in self.claims):
            raise ValueError(f"Claim {claim.claim_id} already exists")
        new_claims = list(self.claims) + [claim]
        return self.model_copy(update={"claims": sorted(new_claims, key=lambda c: c.claim_id)})

    def get_claims_by_type(self, claim_type: str) -> List[ClaimRecord]:
        return [c for c in self.claims if c.claim_type == claim_type]

    def get_source_claims(self) -> List[ClaimRecord]:
        return self.get_claims_by_type("SOURCE_CLAIM")

    def get_implementation_claims(self) -> List[ClaimRecord]:
        return self.get_claims_by_type("IMPLEMENTATION_CLAIM")

    def get_interpretation_claims(self) -> List[ClaimRecord]:
        return self.get_claims_by_type("INTERPRETATION_CLAIM")

    def get_developer_notes(self) -> List[ClaimRecord]:
        return self.get_claims_by_type("DEVELOPER_NOTE")

    def list_all_claims(self) -> List[ClaimRecord]:
        return sorted(self.claims, key=lambda c: c.claim_id)