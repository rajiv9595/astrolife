"""
Phase 5F — Jaimini validators (rule layer).

Kept separate from accepted `core/jaimini/validators.py` (fact layer — do not
touch). Covers evidence completeness and provenance honesty for rule results.
"""
from __future__ import annotations
from typing import Any, List

from core.rules.enums import (
    FormationStatus,
    ConfidenceLevel,
)

from .dependencies import get_dependency_spec


class JaiminiRuleValidationError(Exception):
    pass


def validate_evidence_completeness(results: List[Any]) -> List[str]:
    """Returns a list of violation strings (empty = complete). Rules:
    FORMED → formation evidence + dependencies + provenance;
    NOT_FORMED → failure (non-passing) evidence + dependencies + provenance;
    UNKNOWN (UNCERTAIN) → missing-dependency explanation + provenance;
    every rule → stable rule_id + declared dependency spec."""
    violations: List[str] = []
    for res in results:
        rid = getattr(res, "rule_id", "")
        if not rid:
            violations.append("Rule result missing stable rule_id.")
            continue
        try:
            get_dependency_spec(rid)
        except KeyError:
            violations.append(f"{rid}: no declared dependency spec.")
        prov_ok = getattr(res, "source_reference", "") != "" and \
            getattr(res, "tradition", None) is not None
        if not prov_ok:
            violations.append(f"{rid}: missing provenance.")
        if not getattr(res, "dependencies", []):
            violations.append(f"{rid}: missing dependencies.")
        status = getattr(res, "formation_status", None)
        ev = list(getattr(res, "formation_evidence", []) or [])
        if status == FormationStatus.FORMED:
            if not ev or not any(getattr(e, "passed", False) for e in ev):
                violations.append(f"{rid}: FORMED without passing formation evidence.")
        elif status == FormationStatus.NOT_FORMED:
            if not ev:
                violations.append(f"{rid}: NOT_FORMED without failure evidence.")
        elif status == FormationStatus.UNCERTAIN:
            blob = " ".join(getattr(res, "cancellation_evidence", []) or []) + " " + \
                getattr(res, "notes", "")
            if "missing" not in blob.lower() and "unavailable" not in blob.lower():
                violations.append(f"{rid}: UNKNOWN without missing-dependency explanation.")
    return sorted(violations)


def validate_rule_provenance(results: List[Any]) -> List[str]:
    """Rejects unsupported textual authority: VERIFIED/HIGH confidence or any
    source_reference other than UNVERIFIED is a violation unless the rule
    carries genuinely verified source metadata (none in the 5E catalogue)."""
    violations: List[str] = []
    for res in results:
        rid = getattr(res, "rule_id", "")
        conf = getattr(res, "confidence", None)
        conf_val = getattr(conf, "value", conf)
        if conf_val in (ConfidenceLevel.VERIFIED.value, ConfidenceLevel.HIGH.value,
                        ConfidenceLevel.MEDIUM.value):
            violations.append(f"{rid}: claims confidence {conf_val} without verified source metadata.")
        if getattr(res, "source_reference", "") != "UNVERIFIED":
            violations.append(f"{rid}: source_reference is not UNVERIFIED.")
    return sorted(violations)
