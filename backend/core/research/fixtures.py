"""
Phase 9 — fixtures: declarative only, positive/negative/boundary/
missing-input kinds. No executable fixture code.
"""
from __future__ import annotations

from typing import Any, Dict, List

FIXTURE_KINDS = ("positive", "negative", "boundary", "missing_input")


def create_fixture(fixture_id: str, facts: Dict[str, Any] | None = None,
                   expected_formation: str = "FORMED",
                   fixture_kind: str = "positive", **extra: Any) -> Dict[str, Any]:
    return {
        "fixture_id": fixture_id,
        "description": extra.get("description", ""),
        "chart_input_ref": extra.get("chart_input_ref", "golden"),
        "facts": dict(facts or {}),
        "expected_formation": expected_formation,
        "expected_applicability": extra.get("expected_applicability", "APPLICABLE"),
        "expected_timing": extra.get("expected_timing"),
        "expected_conflicts": list(extra.get("expected_conflicts", [])),
        "expected_evidence_state": extra.get("expected_evidence_state", "UNVERIFIED"),
        "expected_provenance": dict(extra.get("expected_provenance", {})),
        "expected_status": extra.get("expected_status", "PASS"),
        "fixture_kind": fixture_kind,
    }


def validate_fixture(fx: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    if not fx.get("fixture_id"):
        errors.append("fixture_id required")
    if fx.get("fixture_kind") not in FIXTURE_KINDS:
        errors.append(f"unknown fixture_kind {fx.get('fixture_kind')!r}")
    if not isinstance(fx.get("facts", {}), dict):
        errors.append("facts must be an object")
    if fx.get("expected_formation") not in ("FORMED", "NOT_FORMED", "UNKNOWN"):
        errors.append("bad expected_formation")
    if fx.get("expected_applicability") not in ("APPLICABLE", "NOT_APPLICABLE", "UNKNOWN", "INVALID"):
        errors.append("bad expected_applicability")
    return {"valid": len(errors) == 0, "errors": errors}


def boundary_fixture(fixture_id: str, facts: Dict[str, Any], **extra: Any) -> Dict[str, Any]:
    return create_fixture(fixture_id, facts, fixture_kind="boundary", **extra)


def negative_fixture(fixture_id: str, facts: Dict[str, Any], **extra: Any) -> Dict[str, Any]:
    extra.setdefault("expected_formation", "NOT_FORMED")
    return create_fixture(fixture_id, facts, fixture_kind="negative", **extra)


def missing_input_fixture(fixture_id: str, **extra: Any) -> Dict[str, Any]:
    extra.setdefault("expected_formation", "UNKNOWN")
    extra.setdefault("expected_status", "UNKNOWN")
    return create_fixture(fixture_id, {}, fixture_kind="missing_input", **extra)
