"""
Phase 9 — promotion firewall: explicit PromotionRequest, 12 gates,
no EXPERIMENTAL->ACTIVE shortcut. Failed attempts remain visible.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .models import fingerprint_of
from .validation import evaluate_promotion_gates

_REQUESTS: Dict[str, Dict[str, Any]] = {}
_AUDIT: List[Dict[str, Any]] = []
_PROMOTED: Dict[str, Dict[str, Any]] = {}  # target-catalogue entries (research-side record only)


def create_promotion_request(request_id: str, rule_id: str, rule_version: str,
                             package_id: str, requested_by: str,
                             target_catalogue: str, **extra: Any) -> Dict[str, Any]:
    req = {
        "request_id": request_id,
        "rule_id": rule_id,
        "rule_version": rule_version,
        "package_id": package_id,
        "package_version": extra.get("package_version", ""),
        "requested_by": requested_by,
        "target_catalogue": target_catalogue,
        "target_tradition": extra.get("target_tradition", ""),
        "target_profile": extra.get("target_profile", ""),
        "target_version": extra.get("target_version", rule_version),
        "required_validation": extra.get("required_validation", True),
        "required_review": extra.get("required_review", True),
        "source_state": extra.get("source_state", "UNVERIFIED"),
        "evidence_state": extra.get("evidence_state", "UNVERIFIED"),
        "regression_state": extra.get("regression_state", "UNKNOWN"),
        "approval_state": extra.get("approval_state", "PENDING"),
        "status": "PENDING",
    }
    if not target_catalogue:
        raise ValueError("promotion target catalogue required (no implicit destination)")
    _REQUESTS[request_id] = req
    return req


def evaluate_gates(package: Dict[str, Any], rule: Dict[str, Any],
                   review: Dict[str, Any] | None,
                   fixture_report: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return evaluate_promotion_gates(package, rule, review, fixture_report)


def record_promotion_attempt(request_id: str, gate_report: Dict[str, Any],
                             review: Dict[str, Any] | None,
                             package: Dict[str, Any], rule: Dict[str, Any],
                             resulting_state: str, notes: List[str] | None = None) -> Dict[str, Any]:
    entry = {
        "request_id": request_id,
        "requested_state": (_REQUESTS.get(request_id, {}) or {}).get("status", "PENDING"),
        "gate_results": gate_report.get("gates", {}),
        "reviewer_decision": (review or {}).get("decision", ""),
        "package_fingerprint": package.get("fingerprint", ""),
        "rule_fingerprint": fingerprint_of(rule),
        "evidence_fingerprint": fingerprint_of(package.get("evidence", [])),
        "resulting_state": resulting_state,
        "notes": list(notes or []),
    }
    _AUDIT.append(entry)
    if request_id in _REQUESTS:
        _REQUESTS[request_id] = {**_REQUESTS[request_id], "status": resulting_state}
    return entry


def promote_research_rule(request_id: str, package: Dict[str, Any], rule: Dict[str, Any],
                          review: Dict[str, Any] | None,
                          fixture_report: Dict[str, Any] | None = None) -> Dict[str, Any]:
    req = _REQUESTS.get(request_id)
    if req is None:
        raise ValueError(f"unknown promotion request {request_id}")
    gates = evaluate_promotion_gates(package, rule, review, fixture_report)
    if not gates["all_pass"]:
        entry = record_promotion_attempt(request_id, gates, review, package, rule, "REJECTED",
                                         ["promotion gates failed"])
        return {"promoted": False, "gates": gates, "audit": entry}
    if (review or {}).get("decision") != "APPROVE":
        entry = record_promotion_attempt(request_id, gates, review, package, rule, "REVIEW_PENDING",
                                         ["review approval required"])
        return {"promoted": False, "gates": gates, "audit": entry}
    # explicit promotion into the designated target only; never classical by default
    key = f"{req['target_catalogue']}/{rule['rule_id']}@{rule['rule_version']}"
    _PROMOTED[key] = {"rule": rule, "target": req["target_catalogue"],
                      "classification": "USER_SUPPLIED",
                      "request_id": request_id}
    entry = record_promotion_attempt(request_id, gates, review, package, rule, "PROMOTED",
                                     [f"promoted to {req['target_catalogue']}"])
    return {"promoted": True, "gates": gates, "audit": entry, "target": req["target_catalogue"]}


def get_promotion_audit(request_id: str | None = None) -> List[Dict[str, Any]]:
    if request_id:
        return [a for a in _AUDIT if a.get("request_id") == request_id]
    return list(_AUDIT)


def clear_all() -> None:
    _REQUESTS.clear()
    _AUDIT.clear()
    _PROMOTED.clear()
