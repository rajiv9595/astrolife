"""
Phase 9 — review records: APPROVE / REQUEST_CHANGES / REJECT.
No automatic reviewer simulation (caller supplies reviewer identity).
"""
from __future__ import annotations

from typing import Any, Dict, List

_STORE: Dict[str, Dict[str, Any]] = {}


def record_review(review_id: str, rule_id: str, rule_version: str,
                  reviewer: str, decision: str,
                  gate_results: Dict[str, Any] | None = None,
                  concerns: List[str] | None = None,
                  required_changes: List[str] | None = None) -> Dict[str, Any]:
    if decision not in ("APPROVE", "REQUEST_CHANGES", "REJECT"):
        raise ValueError(f"bad review decision {decision!r}")
    rec = {
        "review_id": review_id,
        "rule_id": rule_id,
        "rule_version": rule_version,
        "reviewer": reviewer,
        "review_status": "COMPLETE",
        "gate_results": gate_results or {},
        "concerns": list(concerns or []),
        "required_changes": list(required_changes or []),
        "decision": decision,
        "provenance": {"reviewer": reviewer, "rule_id": rule_id},
    }
    _STORE[review_id] = rec
    return rec


def get_review(review_id: str) -> Dict[str, Any] | None:
    return _STORE.get(review_id)


def clear() -> None:
    _STORE.clear()
