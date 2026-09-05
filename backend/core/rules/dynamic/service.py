"""
Phase 6C — Developer Rule Lab Service.

Unified domain/backend service coordinating the complete rule lifecycle:
  create_rule_draft, validate_rule, test_rule, submit_for_review,
  approve_rule, reject_rule, activate_rule, disable_rule, deprecate_rule,
  archive_rule, get_rule, get_rule_version, list_rules, search_rules,
  compare_rule_versions, import_rule_package, export_rule_package,
  preview_dependencies, preview_evidence, evaluate_active_rule, get_rule_health.

Zero UI, zero AI. Deterministic and auditable throughout.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set, Tuple

from .activation import (
    activate_rule as do_activate_rule,
    archive_rule as do_archive_rule,
    deprecate_rule as do_deprecate_rule,
    disable_rule as do_disable_rule,
)
from .audit import AuditLog, AuditRecord
from .catalogue import (
    get_rule as cat_get_rule,
    get_version as cat_get_version,
    list_rules as cat_list_rules,
    list_versions as cat_list_versions,
    search_rules as cat_search_rules,
)
from .diff import compare_rule_versions as do_compare_versions
from .dsl import find_suspicious_text
from .engine import evaluate_dynamic_rule
from .import_export import ExportResult, ImportResult, export_package, import_package
from .lifecycle import LifecycleTransitionError, validate_transition
from .preview import (
    DependencyPreview,
    EvidencePreview,
    preview_rule_dependencies,
    preview_rule_evidence,
)
from .registry import DynamicRuleRegistry
from .results import DynamicRuleResult
from .review import (
    RuleReviewRecord,
    create_review_record,
)
from .rule_package import (
    ActivationReport,
    RuleDiff,
    RuleHealth,
    RulePackage,
    RuleTestCase,
    RuleTestReport,
    ValidationReport,
    create_rule_draft as do_create_draft,
)
from .schema import ConditionNode, DynamicRuleDefinition, RuleDependencies, RuleProvenance


class RuleLabService:
    """Domain service managing the Developer Rule Lab lifecycle."""

    def __init__(
        self,
        registry: Optional[DynamicRuleRegistry] = None,
        audit_log: Optional[AuditLog] = None,
    ) -> None:
        self.registry: DynamicRuleRegistry = registry if registry is not None else DynamicRuleRegistry()
        self.audit_log: AuditLog = audit_log if audit_log is not None else AuditLog()
        self._packages: Dict[str, Dict[str, RulePackage]] = {}
        self._reviews: Dict[str, RuleReviewRecord] = {}

    # ——— 1. Draft Creation ———
    def create_rule_draft(
        self,
        rule_id: str,
        version: str,
        name: str,
        description: str,
        tradition: str,
        category: str,
        provenance: RuleProvenance,
        condition_tree: ConditionNode,
        dependencies: RuleDependencies,
        cancellation_tree: Optional[ConditionNode] = None,
        mitigation_tree: Optional[ConditionNode] = None,
        derived_facts: Optional[List[str]] = None,
        actor: str = "developer",
    ) -> RulePackage:
        """Create a new rule draft in the DRAFT lifecycle state."""
        # Reject mutation of existing version
        if rule_id in self._packages and version in self._packages[rule_id]:
            raise ValueError(
                f"Rule {rule_id}@{version} already exists. Cannot mutate existing version. Create a new version."
            )

        pkg = do_create_draft(
            rule_id=rule_id,
            version=version,
            name=name,
            description=description,
            tradition=tradition,
            category=category,
            provenance=provenance,
            condition_tree=condition_tree,
            dependencies=dependencies,
            cancellation_tree=cancellation_tree,
            mitigation_tree=mitigation_tree,
            derived_facts=derived_facts,
        )

        self._packages.setdefault(rule_id, {})[version] = pkg
        is_first = len(self._packages[rule_id]) == 1
        event = "RULE_CREATED" if is_first else "RULE_VERSION_CREATED"

        self.audit_log.record(
            event_type=event,
            rule_id=rule_id,
            version=version,
            actor=actor,
            reason="Initial draft created",
            payload={"name": name, "tradition": tradition, "category": category},
        )
        return pkg

    def register_package(self, pkg: RulePackage, actor: str = "developer") -> None:
        """Store an existing package in the lab service."""
        rule_id = pkg.rule_id
        version = pkg.version
        if rule_id in self._packages and version in self._packages[rule_id]:
            raise ValueError(f"Package {rule_id}@{version} already exists; mutation forbidden.")
        self._packages.setdefault(rule_id, {})[version] = pkg

    def get_package(self, rule_id: str, version: Optional[str] = None) -> Optional[RulePackage]:
        """Retrieve a RulePackage by rule_id and optional version."""
        versions = self._packages.get(rule_id)
        if not versions:
            return None
        if version is not None:
            return versions.get(version)
        latest_ver = sorted(
            versions.keys(),
            key=lambda v: tuple(int(x) for x in v.split("-")[0].split(".")),
        )[-1]
        return versions[latest_ver]

    # ——— 2. Validation Workflow ———
    def validate_rule(
        self,
        rule_id: str,
        version: str,
        actor: str = "developer",
    ) -> ValidationReport:
        """Validate a rule package. If clean, transitions DRAFT -> VALIDATED."""
        pkg = self._get_required_package(rule_id, version)
        val_report = pkg.validate(known_rule_ids=set(self._packages.keys()))

        if val_report.is_valid:
            if pkg.lifecycle.status == "DRAFT":
                pkg = pkg.transition_lifecycle("VALIDATED")
            pkg = pkg.model_copy(update={"validation_report": val_report})
            self._packages[rule_id][version] = pkg

            self.audit_log.record(
                event_type="RULE_VALIDATED",
                rule_id=rule_id,
                version=version,
                actor=actor,
                reason="Validation passed with 0 errors",
                payload={"warnings": len(val_report.warnings)},
            )
        else:
            pkg = pkg.model_copy(update={"validation_report": val_report})
            self._packages[rule_id][version] = pkg

        return val_report

    # ——— 3. Test Fixture System & Execution ———
    def add_test_case(
        self,
        rule_id: str,
        version: str,
        test_case: RuleTestCase,
    ) -> RulePackage:
        """Add a declarative test case to a package."""
        pkg = self._get_required_package(rule_id, version)
        updated = pkg.with_test_case(test_case)
        self._packages[rule_id][version] = updated
        return updated

    def test_rule(
        self,
        rule_id: str,
        version: str,
        context: Optional[Any] = None,
        minimum_tests: int = 1,
        actor: str = "developer",
    ) -> RuleTestReport:
        """Execute test cases. If all pass and rule is VALIDATED, transitions to TESTED."""
        pkg = self._get_required_package(rule_id, version)
        from .test_fixture import run_rule_tests
        report = run_rule_tests(pkg, context=context, minimum_tests=minimum_tests)

        updated_pkg = pkg.model_copy(update={"test_report": report})

        if report.failed == 0 and pkg.lifecycle.status == "VALIDATED":
            updated_pkg = updated_pkg.transition_lifecycle("TESTED")

        self._packages[rule_id][version] = updated_pkg

        self.audit_log.record(
            event_type="RULE_TESTED",
            rule_id=rule_id,
            version=version,
            actor=actor,
            reason=f"Ran {report.total} tests: {report.passed} passed, {report.failed} failed",
            payload={"passed": report.passed, "failed": report.failed, "fp": report.execution_fingerprint},
        )
        return report

    # ——— 4. Review System ———
    def submit_for_review(
        self,
        rule_id: str,
        version: str,
        reviewer_type: str = "human",
        notes: str = "",
        provenance_decision: str = "",
        actor: str = "developer",
    ) -> RuleReviewRecord:
        """Submit a rule package for review. Requires TESTED state."""
        pkg = self._get_required_package(rule_id, version)
        if pkg.lifecycle.status != "TESTED":
            raise LifecycleTransitionError(
                f"Cannot submit rule {rule_id}@{version} for review: state is '{pkg.lifecycle.status}', expected 'TESTED'."
            )

        updated_pkg = pkg.transition_lifecycle("REVIEW_PENDING")
        self._packages[rule_id][version] = updated_pkg

        rec = create_review_record(
            rule_id=rule_id,
            version=version,
            decision="DEFERRED",
            reviewer_type=reviewer_type,
            notes=notes,
            provenance_decision=provenance_decision,
        )
        self._reviews[rec.review_id] = rec

        self.audit_log.record(
            event_type="RULE_REVIEWED",
            rule_id=rule_id,
            version=version,
            actor=actor,
            reason="Submitted for review",
            payload={"review_id": rec.review_id, "decision": "DEFERRED"},
        )
        return rec

    def approve_rule(
        self,
        review_id: str,
        notes: str = "",
        actor: str = "reviewer",
    ) -> RuleReviewRecord:
        """Approve a submitted review record."""
        rec = self._reviews.get(review_id)
        if rec is None:
            raise KeyError(f"Review record {review_id} not found.")

        approved = rec.model_copy(update={"decision": "APPROVED", "notes": notes or rec.notes})
        self._reviews[review_id] = approved

        self.audit_log.record(
            event_type="RULE_REVIEWED",
            rule_id=rec.rule_id,
            version=rec.version,
            actor=actor,
            reason="Review approved",
            payload={"review_id": review_id, "decision": "APPROVED"},
        )
        return approved

    def reject_rule(
        self,
        review_id: str,
        notes: str = "",
        actor: str = "reviewer",
    ) -> RuleReviewRecord:
        """Reject a submitted review record, transitioning rule to REJECTED."""
        rec = self._reviews.get(review_id)
        if rec is None:
            raise KeyError(f"Review record {review_id} not found.")

        rejected = rec.model_copy(update={"decision": "REJECTED", "notes": notes or rec.notes})
        self._reviews[review_id] = rejected

        pkg = self.get_package(rec.rule_id, rec.version)
        if pkg and pkg.lifecycle.status == "REVIEW_PENDING":
            updated_pkg = pkg.transition_lifecycle("REJECTED")
            self._packages[rec.rule_id][rec.version] = updated_pkg

        self.audit_log.record(
            event_type="RULE_REVIEWED",
            rule_id=rec.rule_id,
            version=rec.version,
            actor=actor,
            reason="Review rejected",
            payload={"review_id": review_id, "decision": "REJECTED"},
        )
        return rejected

    # ——— 5. Activation & Deactivation ———
    def activate_rule(
        self,
        rule_id: str,
        version: str,
        review_id: Optional[str] = None,
        actor: str = "release_manager",
    ) -> ActivationReport:
        """Activate a rule version into production registry after meeting all gates."""
        pkg = self._get_required_package(rule_id, version)

        # Find approval record
        review_record: Optional[RuleReviewRecord] = None
        if review_id:
            review_record = self._reviews.get(review_id)
        else:
            for r in self._reviews.values():
                if r.rule_id == rule_id and r.version == version and r.decision == "APPROVED":
                    review_record = r
                    break

        success, activated_pkg, report = do_activate_rule(
            pkg,
            registry=self.registry,
            review_record=review_record,
        )

        if success:
            self._packages[rule_id][version] = activated_pkg
            # Register in DynamicRuleRegistry
            self.registry.register(activated_pkg.rule)

            self.audit_log.record(
                event_type="RULE_ACTIVATED",
                rule_id=rule_id,
                version=version,
                actor=actor,
                reason=report.activation_reason,
                payload=report.deterministic_record,
            )

        return report

    def disable_rule(
        self,
        rule_id: str,
        version: str,
        reason: str = "Manual deactivation",
        actor: str = "operator",
    ) -> RulePackage:
        """Disable an active rule. Historical evaluations remain reproducible."""
        pkg = self._get_required_package(rule_id, version)
        disabled_pkg = do_disable_rule(pkg, reason=reason)
        self._packages[rule_id][version] = disabled_pkg

        self.audit_log.record(
            event_type="RULE_DISABLED",
            rule_id=rule_id,
            version=version,
            actor=actor,
            reason=reason,
            payload={"status": "DISABLED"},
        )
        return disabled_pkg

    def deprecate_rule(
        self,
        rule_id: str,
        version: str,
        deprecated_by: str = "",
        reason: str = "Superseded",
        actor: str = "developer",
    ) -> RulePackage:
        """Deprecate an active rule."""
        pkg = self._get_required_package(rule_id, version)
        dep_pkg = do_deprecate_rule(pkg, deprecated_by=deprecated_by, reason=reason)
        self._packages[rule_id][version] = dep_pkg

        self.registry.deprecate(rule_id, version, deprecated_by=deprecated_by)

        self.audit_log.record(
            event_type="RULE_DEPRECATED",
            rule_id=rule_id,
            version=version,
            actor=actor,
            reason=reason,
            payload={"deprecated_by": deprecated_by},
        )
        return dep_pkg

    def archive_rule(
        self,
        rule_id: str,
        version: str,
        reason: str = "Archived",
        actor: str = "developer",
    ) -> RulePackage:
        """Archive a deprecated rule."""
        pkg = self._get_required_package(rule_id, version)
        archived_pkg = do_archive_rule(pkg, reason=reason)
        self._packages[rule_id][version] = archived_pkg

        self.audit_log.record(
            event_type="RULE_ARCHIVED",
            rule_id=rule_id,
            version=version,
            actor=actor,
            reason=reason,
            payload={"status": "ARCHIVED"},
        )
        return archived_pkg

    # ——— 6. Catalogue & Queries ———
    def get_rule(self, rule_id: str) -> Optional[DynamicRuleDefinition]:
        """Get the latest registered rule definition."""
        return self.registry.get(rule_id)

    def get_rule_version(self, rule_id: str, version: str) -> Optional[DynamicRuleDefinition]:
        """Get a specific version of a registered rule definition."""
        return self.registry.get(rule_id, version)

    def list_rules(
        self,
        tradition: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        provenance: Optional[str] = None,
    ) -> List[DynamicRuleDefinition]:
        """List rules from registry in deterministic order."""
        return cat_list_rules(
            self.registry,
            tradition=tradition,
            category=category,
            status=status,
            provenance=provenance,
        )

    def list_versions(self, rule_id: str) -> List[str]:
        """List versions of a rule from registry or lab store."""
        if rule_id in self._packages:
            return sorted(
                self._packages[rule_id].keys(),
                key=lambda v: tuple(int(x) for x in v.split("-")[0].split(".")),
            )
        return self.registry.list_versions(rule_id)

    def search_rules(self, pattern: str) -> List[DynamicRuleDefinition]:
        """Search rules by pattern."""
        return cat_search_rules(pattern, self.registry)

    # ——— 7. Version Comparison & Diff ———
    def compare_rule_versions(
        self,
        rule_id: str,
        version_a: str,
        version_b: str,
    ) -> RuleDiff:
        """Compare two versions of a rule semantically."""
        pkg_a = self._get_required_package(rule_id, version_a)
        pkg_b = self._get_required_package(rule_id, version_b)
        return do_compare_versions(pkg_a, pkg_b)

    # ——— 8. Import & Export ———
    def export_rule_package(self, rule_id: str, version: str) -> ExportResult:
        """Export a RulePackage to canonical JSON."""
        pkg = self._get_required_package(rule_id, version)
        return export_package(pkg)

    def import_rule_package(
        self,
        json_str: str,
        allow_identical: bool = False,
        actor: str = "importer",
    ) -> ImportResult:
        """Import a RulePackage from canonical JSON string."""
        res = import_package(
            json_str,
            existing_registry=self.registry,
            allow_identical=allow_identical,
        )
        if res.success and res.rule_package:
            pkg = res.rule_package
            # Store in lab packages
            self._packages.setdefault(pkg.rule_id, {})[pkg.version] = pkg
            self.audit_log.record(
                event_type="RULE_CREATED" if len(self._packages[pkg.rule_id]) == 1 else "RULE_VERSION_CREATED",
                rule_id=pkg.rule_id,
                version=pkg.version,
                actor=actor,
                reason="Imported from JSON",
                payload={"fingerprint": pkg.fingerprint()},
            )
        return res

    # ——— 9. Previews ———
    def preview_dependencies(self, rule_id: str, version: str) -> DependencyPreview:
        """Preview direct and indirect dependencies of a rule."""
        pkg = self._get_required_package(rule_id, version)
        return preview_rule_dependencies(pkg)

    def preview_evidence(self, rule_id: str, version: str) -> EvidencePreview:
        """Preview evidence chains and derived fact relationships."""
        pkg = self._get_required_package(rule_id, version)
        return preview_rule_evidence(pkg)

    # ——— 10. Active Rule Selection & Evaluation ———
    def evaluate_active_rule(
        self,
        rule_id: str,
        context: Any,
        version: Optional[str] = None,
        tradition: Optional[str] = None,
    ) -> DynamicRuleResult:
        """Select and evaluate an ACTIVE rule version deterministically.

        Excludes deprecated rules unless explicitly requested. Respects tradition filters.
        """
        if version is not None:
            rule_def = self.registry.get(rule_id, version)
        else:
            rule_def = self.registry.get(rule_id)

        if rule_def is None:
            raise KeyError(f"Active rule {rule_id} (version={version}) not found in registry.")

        if rule_def.lifecycle.status != "ACTIVE":
            raise ValueError(
                f"Rule {rule_id}@{rule_def.identity.rule_version} is '{rule_def.lifecycle.status}', not ACTIVE."
            )

        if tradition and tradition != "ALL" and rule_def.classification.tradition != tradition:
            raise ValueError(
                f"Tradition mismatch: rule tradition '{rule_def.classification.tradition}' "
                f"is isolated from requested tradition '{tradition}'."
            )

        return evaluate_dynamic_rule(rule_def, context)

    # ——— 11. Rule Health ———
    def get_rule_health(self, rule_id: str, version: str) -> RuleHealth:
        """Compute structured health status for a rule version."""
        pkg = self._get_required_package(rule_id, version)
        val_report = pkg.validate()
        schema_valid = val_report.is_valid

        verif = pkg.provenance.source_reference.verification_status
        prov_valid = verif in ("VERIFIED", "USER_SUPPLIED", "TRADITIONAL", "SECONDARY", "CUSTOM")

        reg_diags = self.registry.validate_graph()
        deps_valid = not any(d.code == "CYCLE" for d in reg_diags)

        pkg_json = json.dumps(pkg.to_canonical_dict())
        security_valid = len(find_suspicious_text(pkg_json)) == 0

        tests_passed = (pkg.test_report is not None and pkg.test_report.failed == 0 and pkg.test_report.total > 0)
        lifecycle_status = pkg.lifecycle.status
        activation_status = "ACTIVE" if lifecycle_status == "ACTIVE" else "INACTIVE"

        regression_status = "STABLE"
        if len(self._packages.get(rule_id, {})) > 1:
            regression_status = "STABLE"

        return RuleHealth(
            schema_valid=schema_valid,
            provenance_valid=prov_valid,
            dependencies_valid=deps_valid,
            security_valid=security_valid,
            tests_passed=tests_passed,
            regression_status=regression_status,
            lifecycle_status=lifecycle_status,
            activation_status=activation_status,
        )

    # ——— Internal helper ———
    def _get_required_package(self, rule_id: str, version: str) -> RulePackage:
        pkg = self.get_package(rule_id, version)
        if pkg is None:
            # Check registry to see if an active rule definition exists there
            rule_def = self.registry.get(rule_id, version)
            if rule_def:
                pkg = RulePackage.from_rule_definition(rule_def)
                self._packages.setdefault(rule_id, {})[version] = pkg
                return pkg
            raise KeyError(f"Rule package not found: {rule_id}@{version}")
        return pkg
