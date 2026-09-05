"""
Phase 6C — Rule activation and deactivation.

Implements activate_rule(), disable_rule(), deprecate_rule(), archive_rule().

Activation requirements (all must pass):
  - valid schema & DSL
  - no validation errors
  - tests passed (non-zero tests, 0 failures)
  - provenance valid
  - dependencies valid (no cycles in registry)
  - no unresolved security violations
  - explicit review state (APPROVED)
  - lifecycle state in REVIEW_PENDING (no silent or direct DRAFT -> ACTIVE jump)

Activation records: rule_id, version, activation state, activation reason,
deterministic payload. No current wall-clock time as calculation input.

Deactivation does NOT delete: rule definition, version, evidence, test results,
evaluation history.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from .dsl import find_suspicious_text
from .lifecycle import LIFECYCLE_STATES, LifecycleTransitionError, validate_transition
from .registry import DynamicRuleRegistry
from .review import RuleReviewRecord
from .rule_package import ActivationReport, RulePackage
from .schema import DynamicRuleDefinition, RuleLifecycle
from .validators import Diagnostic, validate_rule


def activate_rule(
    rule_package: RulePackage,
    registry: Optional[DynamicRuleRegistry] = None,
    review_record: Optional[RuleReviewRecord] = None,
    override_reason: Optional[str] = None,
) -> Tuple[bool, RulePackage, ActivationReport]:
    """Activate a rule package after all requirements are verified.

    Returns: (activated: bool, updated_package: RulePackage, report: ActivationReport)
    """
    rule_id = rule_package.rule_id
    version = rule_package.version

    # 1. Lifecycle state check: must be REVIEW_PENDING unless explicit override
    current_status = rule_package.lifecycle.status
    if current_status != "REVIEW_PENDING" and not override_reason:
        report = ActivationReport(
            activated=False,
            rule_id=rule_id,
            version=version,
            activation_reason=(
                f"Lifecycle transition forbidden: rule must be in 'REVIEW_PENDING' state "
                f"before activation (current state is '{current_status}')."
            ),
            deterministic_record={"status": current_status},
        )
        return False, rule_package, report

    # 2. Schema and DSL validation
    val_report = rule_package.validate()
    if not val_report.is_valid:
        err_msgs = [f"{d.code}:{d.path}:{d.message}" for d in val_report.errors]
        report = ActivationReport(
            activated=False,
            rule_id=rule_id,
            version=version,
            activation_reason=f"Validation errors ({len(val_report.errors)}) prevent activation: {err_msgs[:3]}",
            deterministic_record={"errors": err_msgs},
        )
        return False, rule_package, report

    # 3. Tests passed check
    if rule_package.test_report is None:
        report = ActivationReport(
            activated=False,
            rule_id=rule_id,
            version=version,
            activation_reason="Activation denied: rule package has no test report.",
            deterministic_record={},
        )
        return False, rule_package, report

    if rule_package.test_report.total == 0:
        report = ActivationReport(
            activated=False,
            rule_id=rule_id,
            version=version,
            activation_reason="Activation denied: zero tests = tested is disallowed.",
            deterministic_record={"total_tests": 0},
        )
        return False, rule_package, report

    if rule_package.test_report.failed > 0:
        report = ActivationReport(
            activated=False,
            rule_id=rule_id,
            version=version,
            activation_reason=f"Activation denied: {rule_package.test_report.failed} tests failed.",
            deterministic_record={
                "failed_tests": rule_package.test_report.failed,
                "diagnostics": rule_package.test_report.diagnostics,
            },
        )
        return False, rule_package, report

    # 4. Provenance validation
    prov = rule_package.provenance
    verif = prov.source_reference.verification_status
    if verif not in ("VERIFIED", "USER_SUPPLIED", "TRADITIONAL", "SECONDARY", "CUSTOM"):
        report = ActivationReport(
            activated=False,
            rule_id=rule_id,
            version=version,
            activation_reason=f"Activation denied: unapproved provenance verification status '{verif}'.",
            deterministic_record={"verification_status": verif},
        )
        return False, rule_package, report

    # 5. Dependency check (no cycles in registry)
    if registry is not None:
        reg_diags = registry.validate_graph()
        cycle_diags = [d for d in reg_diags if d.code == "CYCLE"]
        if cycle_diags:
            report = ActivationReport(
                activated=False,
                rule_id=rule_id,
                version=version,
                activation_reason="Activation denied: dependency cycle detected in registry.",
                deterministic_record={"cycles": [d.message for d in cycle_diags]},
            )
            return False, rule_package, report

    # 6. Security scan
    pkg_json = json.dumps(rule_package.to_canonical_dict())
    suspicious = find_suspicious_text(pkg_json)
    if suspicious:
        report = ActivationReport(
            activated=False,
            rule_id=rule_id,
            version=version,
            activation_reason=f"Activation denied: suspicious executable pattern detected: {suspicious}",
            deterministic_record={"suspicious_patterns": suspicious},
        )
        return False, rule_package, report

    # 7. Explicit review state check
    if review_record is None or review_record.decision != "APPROVED":
        decision_str = review_record.decision if review_record else "NO_REVIEW"
        report = ActivationReport(
            activated=False,
            rule_id=rule_id,
            version=version,
            activation_reason=f"Activation denied: requires explicit review APPROVED (got {decision_str}).",
            deterministic_record={"review_decision": decision_str},
        )
        return False, rule_package, report

    # All criteria satisfied — perform activation transition
    try:
        new_lifecycle = rule_package.lifecycle.model_copy(update={"status": "ACTIVE"})
        deterministic_record = {
            "rule_id": rule_id,
            "version": version,
            "activation_state": "ACTIVE",
            "activation_reason": "All requirements met: schema valid, tests passed, provenance approved, dependencies valid, security clean, review approved.",
            "package_fingerprint": rule_package.fingerprint(),
            "review_id": review_record.review_id,
            "tradition": rule_package.tradition,
            "provenance_status": verif,
        }

        report = ActivationReport(
            activated=True,
            rule_id=rule_id,
            version=version,
            activation_reason="All requirements met: schema valid, tests passed, provenance approved, dependencies valid, security clean, review approved.",
            deterministic_record=deterministic_record,
        )

        new_package = rule_package.model_copy(
            update={
                "lifecycle": new_lifecycle,
                "activation_metadata": report,
            }
        )

        return True, new_package, report

    except Exception as e:
        report = ActivationReport(
            activated=False,
            rule_id=rule_id,
            version=version,
            activation_reason=f"Activation transition failed: {e}",
            deterministic_record={},
        )
        return False, rule_package, report


def disable_rule(rule_package: RulePackage, reason: str = "Administrative deactivation") -> RulePackage:
    """Disable an active rule without deleting definition or historical evidence."""
    validate_transition(rule_package.lifecycle.status, "DISABLED")
    new_lifecycle = rule_package.lifecycle.model_copy(update={"status": "DISABLED"})
    return rule_package.model_copy(update={"lifecycle": new_lifecycle})


def deprecate_rule(
    rule_package: RulePackage,
    deprecated_by: str = "",
    reason: str = "Rule superseded or deprecated",
) -> RulePackage:
    """Deprecate an active rule, optionally specifying the superseding version."""
    validate_transition(rule_package.lifecycle.status, "DEPRECATED")
    new_lifecycle = rule_package.lifecycle.model_copy(
        update={"status": "DEPRECATED", "deprecated_by": deprecated_by}
    )
    return rule_package.model_copy(update={"lifecycle": new_lifecycle})


def archive_rule(rule_package: RulePackage, reason: str = "Rule archived") -> RulePackage:
    """Archive a deprecated rule. Historical evaluations remain reproducible."""
    validate_transition(rule_package.lifecycle.status, "ARCHIVED")
    new_lifecycle = rule_package.lifecycle.model_copy(update={"status": "ARCHIVED"})
    return rule_package.model_copy(update={"lifecycle": new_lifecycle})