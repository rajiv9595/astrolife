"""
Phase 9 — validation: schema/security/dependency/applicability/evidence/
fixture/regression/provenance/tradition/profile/review/lifecycle gates.
Each gate independently inspectable; no collapsed single score.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .models import PROMOTION_GATES, RESEARCH_STATUSES, RESEARCH_TRADITIONS
from .security import scan_package_text, validate_condition_node


def _ok() -> Dict[str, Any]:
    return {"passed": True, "reasons": []}


def _fail(*reasons: str) -> Dict[str, Any]:
    return {"passed": False, "reasons": list(reasons)}


def validate_research_rule(rule: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not rule.get("rule_id"):
        errors.append("rule_id required")
    if not rule.get("rule_version"):
        errors.append("rule_version required")
    trad = rule.get("tradition", "EXPERIMENTAL")
    if trad not in RESEARCH_TRADITIONS:
        errors.append(f"unknown tradition {trad!r}")
    status = rule.get("lifecycle_status", "EXPERIMENTAL")
    if status not in RESEARCH_STATUSES:
        errors.append(f"unknown lifecycle status {status!r}")
    formation = rule.get("formation")
    if not formation:
        errors.append("formation condition required")
    else:
        errors.extend(validate_condition_node(formation, "formation"))
    for key in ("cancellation", "mitigation", "activation"):
        node = rule.get(key)
        if node is not None:
            errors.extend(validate_condition_node(node, key))
    deps = rule.get("dependencies", {})
    if not isinstance(deps, dict):
        errors.append("dependencies must be an object")
    return (len(errors) == 0, errors)


def validate_research_package(pkg: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    for f in ("package_id", "package_version"):
        if not pkg.get(f):
            errors.append(f"{f} required")
    rules = pkg.get("rules", [])
    if not rules:
        errors.append("package must contain at least one rule")
    for i, r in enumerate(rules):
        ok, errs = validate_research_rule(r if isinstance(r, dict) else {})
        for e in errs:
            errors.append(f"rules[{i}]: {e}")
    # security scan is a warning-level flag here; promotion gate treats as fail
    for h in scan_package_text(pkg):
        if "instruction-probe" in h or "eval" in h or "exec" in h or "__import__" in h:
            errors.append(f"security: {h}")
        else:
            warnings.append(f"security-note: {h}")
    return (len(errors) == 0, errors, warnings)


def evaluate_promotion_gates(pkg: Dict[str, Any], rule: Dict[str, Any],
                             review: Dict[str, Any] | None,
                             fixture_report: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Evaluate the 12 promotion gates independently."""
    gates: Dict[str, Any] = {}
    ok, errs = validate_research_rule(rule)
    gates["schema_valid"] = _ok() if ok else _fail(*errs)
    sec = [h for h in scan_package_text({"rule": rule}) if ("instruction-probe" in h or "eval" in h)]
    gates["security_valid"] = _ok() if not sec else _fail(*sec)
    deps = rule.get("dependencies", {})
    dep_errs = [f"missing dependency declaration: {k}" for k in ("input_facts",) if k not in deps]
    gates["dependency_valid"] = _ok() if not dep_errs else _fail(*dep_errs)
    appl = rule.get("applicability", {})
    gates["applicability_valid"] = _ok() if appl else _fail("applicability matrix missing")
    ev_reqs = rule.get("evidence_requirements", [])
    gates["evidence_valid"] = _ok() if ev_reqs else _fail("evidence requirements missing")
    fr = fixture_report or {}
    gates["fixture_valid"] = _ok() if fr.get("failed", 0) == 0 and fr.get("total", 0) > 0 else _fail(
        f"fixtures total={fr.get('total',0)} failed={fr.get('failed',0)}")
    gates["regression_valid"] = _ok() if fr.get("failed", 0) == 0 and fr.get("total", 0) > 0 else _fail("regression not green")
    prov_ok = bool(rule.get("rule_id")) and bool(pkg.get("package_id"))
    gates["provenance_valid"] = _ok() if prov_ok else _fail("provenance incomplete")
    gates["tradition_valid"] = _ok() if rule.get("tradition") in RESEARCH_TRADITIONS else _fail("tradition invalid")
    gates["profile_valid"] = _ok() if pkg.get("profiles") else _fail("profile missing")
    if review and review.get("decision") == "APPROVE":
        gates["review_complete"] = _ok()
    else:
        gates["review_complete"] = _fail(f"review decision={review.get('decision') if review else None}")
    gates["lifecycle_valid"] = _ok() if rule.get("lifecycle_status") in ("REVIEW_PENDING", "APPROVED_FOR_PROMOTION") else _fail(
        f"lifecycle={rule.get('lifecycle_status')}")
    all_pass = all(g["passed"] for g in gates.values())
    return {"gates": gates, "all_pass": all_pass, "gate_names": list(PROMOTION_GATES)}
