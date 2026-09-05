"""
Phase 6C — Immutable audit log.

Every lifecycle mutation generates an immutable audit event. Audit records
identify: event type, rule, version, actor/source, reason, deterministic
payload. History mutation is not allowed.

Event types:
  RULE_CREATED
  RULE_VALIDATED
  RULE_TESTED
  RULE_REVIEWED
  RULE_ACTIVATED
  RULE_DISABLED
  RULE_DEPRECATED
  RULE_ARCHIVED
  RULE_VERSION_CREATED
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


AUDIT_EVENT_TYPES = frozenset({
    "RULE_CREATED",
    "RULE_VALIDATED",
    "RULE_TESTED",
    "RULE_REVIEWED",
    "RULE_ACTIVATED",
    "RULE_DISABLED",
    "RULE_DEPRECATED",
    "RULE_ARCHIVED",
    "RULE_VERSION_CREATED",
})


class AuditRecord(BaseModel):
    """An immutable audit record capturing a single lifecycle event."""
    audit_id: str
    event_type: str
    rule_id: str
    version: str
    timestamp: str  # ISO string or deterministic label
    actor: str      # user, developer, service, or system
    reason: str
    payload: Dict[str, Any]

    model_config = {"frozen": True}

    def to_json(self) -> str:
        """Serialize as compact canonical JSON for immutable storage."""
        return json.dumps({
            "audit_id": self.audit_id,
            "event_type": self.event_type,
            "rule_id": self.rule_id,
            "version": self.version,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "reason": self.reason,
            "payload": self.payload,
        }, sort_keys=True, separators=(",", ":"))


class AuditLog:
    """Append-only immutable audit log for rule lifecycle mutations."""

    def __init__(self) -> None:
        self._records: List[AuditRecord] = []

    def record(
        self,
        event_type: str,
        rule_id: str,
        version: str,
        actor: str,
        reason: str,
        payload: Dict[str, Any],
        timestamp: Optional[str] = None,
        audit_id: Optional[str] = None,
    ) -> AuditRecord:
        """Append an immutable audit record and return it."""
        seq = len(self._records) + 1
        ts_str = timestamp or f"audit_step_{seq:06d}"

        if audit_id is None:
            raw = f"{seq}:{event_type}:{rule_id}:{version}:{actor}:{reason}:{ts_str}"
            audit_id = f"aud_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"

        rec = AuditRecord(
            audit_id=audit_id,
            event_type=event_type,
            rule_id=rule_id,
            version=version,
            timestamp=ts_str,
            actor=actor,
            reason=reason,
            payload=payload,
        )
        self._records.append(rec)
        return rec

    def get_records(self) -> List[AuditRecord]:
        """Return all audit records in chronological append order."""
        return list(self._records)

    def get_records_by_type(self, event_type: str) -> List[AuditRecord]:
        """Get audit records filtered by event type."""
        return [r for r in self._records if r.event_type == event_type]

    def get_records_for_rule(self, rule_id: str) -> List[AuditRecord]:
        """Get all audit records for a specific rule."""
        return [r for r in self._records if r.rule_id == rule_id]

    def export(self) -> List[Dict[str, Any]]:
        """Export all records as serializable dictionaries."""
        return [r.model_dump() for r in self._records]

    @classmethod
    def import_records(cls, records: List[Dict[str, Any]]) -> "AuditLog":
        """Import audit records into a new AuditLog instance."""
        log = cls()
        for r in records:
            record = AuditRecord(
                audit_id=r["audit_id"],
                event_type=r["event_type"],
                rule_id=r["rule_id"],
                version=r["version"],
                timestamp=r["timestamp"],
                actor=r["actor"],
                reason=r["reason"],
                payload=r.get("payload", {}),
            )
            log._records.append(record)
        return log