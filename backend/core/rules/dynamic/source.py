"""
Phase 6C — Source management.

A rule may have: primary source, secondary source, supporting source,
conflicting source. Sources remain:
  VERIFIED | UNVERIFIED | CONTESTED | SECONDARY | TRADITIONAL | USER_SUPPLIED | CUSTOM
according to actual evidence.

Never automatically upgrade UNVERIFIED → VERIFIED.
If two sources conflict, preserve both as CONTESTED.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# Source categories
PRIMARY = "primary"
SECONDARY = "secondary"
SUPPORTING = "supporting"
CONFLICTING = "conflicting"

# Source verification statuses
VERIFIED = "VERIFIED"
UNVERIFIED = "UNVERIFIED"
CONTESTED = "CONTESTED"
SECONDARY_STATUS = "SECONDARY"
TRADITIONAL = "TRADITIONAL"
USER_SUPPLIED = "USER_SUPPLIED"
CUSTOM_STATUS = "CUSTOM"

ALL_SOURCE_STATUSES = frozenset({
    VERIFIED,
    UNVERIFIED,
    CONTESTED,
    SECONDARY_STATUS,
    TRADITIONAL,
    USER_SUPPLIED,
    CUSTOM_STATUS,
})


class SourceRecord(BaseModel):
    """A single source reference attached to a rule."""
    source_id: str
    category: str = PRIMARY
    verification_status: str = UNVERIFIED
    title: str = ""
    author: str = ""
    publication: str = ""
    locator: str = ""
    quotation: str = ""

    model_config = {"frozen": True}


class SourceManagement(BaseModel):
    """Manage multiple source attachments for a RulePackage."""
    primary: Optional[SourceRecord] = None
    secondary: Optional[SourceRecord] = None
    supporting: List[SourceRecord] = Field(default_factory=list)
    conflicting: List[SourceRecord] = Field(default_factory=list)

    model_config = {"frozen": True}

    def add_source(self, source: SourceRecord) -> "SourceManagement":
        """Add a source record according to its category."""
        cat = source.category
        if cat == PRIMARY:
            return self.model_copy(update={"primary": source})
        elif cat == SECONDARY:
            return self.model_copy(update={"secondary": source})
        elif cat == CONFLICTING:
            new_list = list(self.conflicting) + [source]
            return self.model_copy(update={"conflicting": new_list})
        else:
            new_list = list(self.supporting) + [source]
            return self.model_copy(update={"supporting": new_list})

    def set_verification(self, source_id: str, new_status: str) -> "SourceManagement":
        """Set verification status for a source.

        Enforces that UNVERIFIED cannot be upgraded to VERIFIED without
        substantive citation (locator and quotation).
        """
        if new_status not in ALL_SOURCE_STATUSES:
            raise ValueError(f"Invalid source status: {new_status}")

        def _update(s: Optional[SourceRecord]) -> Optional[SourceRecord]:
            if s is None or s.source_id != source_id:
                return s
            if new_status == VERIFIED and (not s.locator or not s.quotation):
                raise ValueError(
                    f"Cannot upgrade source '{source_id}' to VERIFIED: locator and quotation required."
                )
            return s.model_copy(update={"verification_status": new_status})

        new_pri = _update(self.primary)
        new_sec = _update(self.secondary)
        new_sup = [_update(s) for s in self.supporting]
        new_con = [_update(s) for s in self.conflicting]

        return self.model_copy(
            update={
                "primary": new_pri,
                "secondary": new_sec,
                "supporting": [s for s in new_sup if s is not None],
                "conflicting": [s for s in new_con if s is not None],
            }
        )

    def record_conflict(self, s1: SourceRecord, s2: SourceRecord) -> "SourceManagement":
        """When two sources conflict, preserve both as CONTESTED in the conflicting list."""
        contested1 = s1.model_copy(update={"verification_status": CONTESTED, "category": CONFLICTING})
        contested2 = s2.model_copy(update={"verification_status": CONTESTED, "category": CONFLICTING})

        new_conflicts = list(self.conflicting) + [contested1, contested2]
        return self.model_copy(update={"conflicting": new_conflicts})

    def list_all_sources(self) -> List[SourceRecord]:
        """Return all attached sources in deterministic order."""
        res: List[SourceRecord] = []
        if self.primary:
            res.append(self.primary)
        if self.secondary:
            res.append(self.secondary)
        res.extend(self.supporting)
        res.extend(self.conflicting)
        return sorted(res, key=lambda s: (s.category, s.source_id))