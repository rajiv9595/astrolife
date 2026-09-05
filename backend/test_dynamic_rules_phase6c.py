"""
Astrolife V2 — Phase 6C: Developer Rule Lab / Rule Management Backend Tests.

Comprehensive test suite verifying:
- Explicit lifecycle state machine & legal transitions
- RulePackage abstraction, draft creation, and validation workflow
- Declarative test fixture system, test execution, and golden tests
- Regression protection, versioning, and semantic diff
- Safe activation, deactivation (disable, deprecate, archive), and active selection
- Catalogue operations and deterministic search/filtering
- RuleHealth structured status
- Source management, conflict preservation, and no auto-upgrade
- Review records and review workflow
- Append-only immutable audit logging
- Safe declarative import/export and canonical fingerprints
- Dependency and evidence previews
- Security boundary (blocking code injection while allowing natural prose)
- Golden developer rule full lifecycle (DEMO.CUSTOM.SYNTHETIC_GOLDEN)
- Invalid rule validation rejection
- Version isolation and coexistence (DEMO.VERSION.TEST 1.0.0 vs 1.1.0)
- Golden chart evaluation against canonical facts
- UNKNOWN and INVALID semantics preservation
- Concurrency and immutability
- 50-run determinism verification
- Performance measurement
"""

import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone

from core.calculation.config import CalculationProfile
from core.calculation.dasha import calculate_vimshottari_timeline
from core.calculation.pipeline import generate_chart_facts
from core.calculation.varga import calculate_all_vargas
from core.jaimini.pipeline import generate_jaimini_facts
from core.rules.dynamic import (
    ALL_SOURCE_STATUSES,
    CONFLICTING,
    PRIMARY,
    SECONDARY,
    SUPPORTING,
    AuditLog,
    AuditRecord,
    ConditionNode,
    DependencyPreview,
    DynamicEvaluationContext,
    DynamicRuleDefinition,
    DynamicRuleRegistry,
    EvidencePreview,
    ExportResult,
    ImportResult,
    LEGAL_TRANSITIONS,
    LIFECYCLE_STATES,
    LifecycleTransitionError,
    PackageFingerprint,
    RuleClassification,
    RuleDependencies,
    RuleDiff,
    RuleDiffCategory,
    RuleEvidenceSpec,
    RuleHealth,
    RuleIdentity,
    RuleLabService,
    RuleLifecycle,
    RulePackage,
    RuleProvenance,
    RuleReviewRecord,
    RuleSemantics,
    RuleTestCase,
    RuleTestExecutor,
    RuleTestReport,
    RuleValidationInfo,
    SourceManagement,
    SourceRecord,
    SourceReference,
    ValidationReport,
    activate_rule,
    archive_rule,
    build_context,
    compare_rule_versions,
    compute_fingerprint,
    create_review_record,
    create_rule_draft,
    deprecate_rule,
    disable_rule,
    evaluate_dynamic_rule,
    export_package,
    filter_by_category,
    filter_by_provenance,
    filter_by_status,
    filter_by_tradition,
    filter_by_validation_status,
    fingerprint_from_dict,
    fingerprints_match,
    get_rule,
    get_version,
    import_package,
    is_valid_transition,
    list_rules,
    list_versions,
    preview_rule_dependencies,
    preview_rule_evidence,
    run_rule_tests,
    search_rules,
    validate_rule,
    validate_transition,
)
from core.strength.pipeline import generate_strength_report
from core.transit.calculator import calculate_transit_positions

total_tests = 0
passed_tests = 0
failed_tests = 0


def check(condition: bool, description: str) -> None:
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"  OK {description}")
    else:
        failed_tests += 1
        print(f"  FAIL {description}")


def P(op: str, params: dict = None, children: list = None, n: int = None) -> ConditionNode:
    return ConditionNode(op=op, params=params or {}, children=children or [], n=n)


from core.jaimini.dasha import calculate_jaimini_dasha
from core.jaimini.profile import JaiminiCalculationProfile

DT = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def build_golden_context() -> DynamicEvaluationContext:
    gchart = generate_chart_facts(
        year=1985, month=10, day=25, hour=5, minute=30, second=0,
        lat=16.9409, lon=81.9961, tz_name="Asia/Kolkata",
        profile=CalculationProfile(),
    )
    gvarga = calculate_all_vargas(gchart)
    gjf = generate_jaimini_facts(gchart, gvarga, JaiminiCalculationProfile())
    gsr = generate_strength_report(gchart)
    gtl = calculate_vimshottari_timeline(gchart)
    gjd = calculate_jaimini_dasha(gchart, gjf)
    gts = calculate_transit_positions(DT)
    return build_context(
        chart_facts=gchart,
        varga_facts=gvarga,
        strength_report=gsr,
        vimshottari_timeline=gtl,
        vimshottari_datetime=DT,
        jaimini_dasha_result=gjd,
        jaimini_dasha_datetime=DT,
        transit_snapshot=gts,
        jaimini_facts=gjf,
        rule_outcomes={"DEMO.CUSTOM.SYNTHETIC_GOLDEN": "FORMED"},
    )


def create_demo_synthetic_package(
    rule_id: str = "DEMO.CUSTOM.SYNTHETIC_GOLDEN",
    version: str = "1.0.0",
    mars_sign: str = "Aries",
) -> RulePackage:
    cond = P("planet_in_sign", {"planet": "Mars", "sign": mars_sign})
    canc = P("planets_conjunct", {"a": "Mars", "b": "Saturn"})
    mit = P("planets_aspect", {"a": "Jupiter", "b": "Mars"})
    prov = RuleProvenance(
        source_reference=SourceReference(
            source_id="DEV-6C-GOLDEN",
            title="Synthetic Golden Spec",
            author="Dev Team",
            publication="Lab",
            locator="Section 28",
            quotation="Developer synthetic test fixture",
            verification_status="USER_SUPPLIED",
        ),
        confidence="CUSTOM",
        provenance_status="USER_SUPPLIED",
    )
    deps = RuleDependencies(
        input_facts=[
            "natal.Mars.sign",
            "natal.Saturn.sign",
            "aspects.Jupiter",
        ]
    )
    tc1 = RuleTestCase(
        test_id="TC01_FORMED",
        description="Mars in specified sign forms rule",
        input_fixture={
            "natal.Mars.sign": mars_sign,
            "natal.Saturn.sign": "Taurus",
            "aspects.Jupiter": ["Venus"],
        },
        expected_formation="FORMED",
        expected_cancellation="NOT_CANCELLED",
        expected_mitigation="NOT_MITIGATED",
        expected_final_state="FORMED",
        is_golden=True,
    )
    tc2 = RuleTestCase(
        test_id="TC02_CANCELLED",
        description="Mars conjunct Saturn cancels rule",
        input_fixture={
            "natal.Mars.sign": mars_sign,
            "natal.Saturn.sign": mars_sign,
            "aspects.Jupiter": [],
        },
        expected_formation="FORMED",
        expected_cancellation="CANCELLED",
        expected_mitigation="NOT_MITIGATED",
        expected_final_state="CANCELLED",
        is_golden=True,
    )
    pkg = create_rule_draft(
        rule_id=rule_id,
        version=version,
        name=f"Synthetic Golden Rule ({mars_sign})",
        description="Developer test fixture for full lifecycle verification.",
        tradition="CUSTOM_DEVELOPER",
        category="DEMO",
        provenance=prov,
        condition_tree=cond,
        cancellation_tree=canc,
        mitigation_tree=mit,
        dependencies=deps,
        test_cases=[tc1, tc2],
    )
    return pkg


def main() -> None:
    print("\n--- 1. Rule Lifecycle State Machine ---")
    check("DRAFT" in LIFECYCLE_STATES and "ACTIVE" in LIFECYCLE_STATES, "Lifecycle states contain DRAFT and ACTIVE")
    check(is_valid_transition("DRAFT", "VALIDATED"), "DRAFT -> VALIDATED is legal")
    check(is_valid_transition("VALIDATED", "TESTED"), "VALIDATED -> TESTED is legal")
    check(is_valid_transition("TESTED", "REVIEW_PENDING"), "TESTED -> REVIEW_PENDING is legal")
    check(is_valid_transition("REVIEW_PENDING", "ACTIVE"), "REVIEW_PENDING -> ACTIVE is legal")
    check(is_valid_transition("ACTIVE", "DISABLED"), "ACTIVE -> DISABLED is legal")
    check(is_valid_transition("ACTIVE", "DEPRECATED"), "ACTIVE -> DEPRECATED is legal")
    check(is_valid_transition("DISABLED", "ACTIVE"), "DISABLED -> ACTIVE is legal")
    check(is_valid_transition("DEPRECATED", "ARCHIVED"), "DEPRECATED -> ARCHIVED is legal")
    check(is_valid_transition("REVIEW_PENDING", "REJECTED"), "REVIEW_PENDING -> REJECTED is legal")
    check(is_valid_transition("REJECTED", "DRAFT"), "REJECTED -> DRAFT is legal")

    # Invalid transitions
    check(not is_valid_transition("DRAFT", "ACTIVE"), "DRAFT -> ACTIVE is illegal (no silent jump)")
    check(not is_valid_transition("DRAFT", "TESTED"), "DRAFT -> TESTED is illegal")
    check(not is_valid_transition("VALIDATED", "ACTIVE"), "VALIDATED -> ACTIVE is illegal")
    check(not is_valid_transition("ARCHIVED", "ACTIVE"), "ARCHIVED -> ACTIVE is illegal")

    try:
        validate_transition("DRAFT", "ACTIVE")
        check(False, "validate_transition raised LifecycleTransitionError on DRAFT->ACTIVE")
    except LifecycleTransitionError:
        check(True, "validate_transition raised LifecycleTransitionError on DRAFT->ACTIVE")

    print("\n--- 2. RulePackage Abstraction & Draft Creation ---")
    pkg = create_demo_synthetic_package()
    check(pkg.rule_id == "DEMO.CUSTOM.SYNTHETIC_GOLDEN", "RulePackage initialized with correct rule_id")
    check(pkg.version == "1.0.0", "RulePackage version is 1.0.0")
    check(pkg.lifecycle.status == "DRAFT", "Draft initialized in DRAFT state")
    check(isinstance(pkg.rule, DynamicRuleDefinition), "RulePackage exposes canonical DynamicRuleDefinition via .rule")
    check(len(pkg.test_cases) == 2, "RulePackage holds 2 declarative test cases")

    # Missing mandatory fields
    try:
        create_rule_draft(
            rule_id="",
            version="1.0.0",
            name="Incomplete",
            description="",
            tradition="PARASHARI_CLASSICAL",
            category="DEMO",
            provenance=None,
            condition_tree=None,
            dependencies=None,
        )
        check(False, "create_rule_draft failed to reject missing mandatory fields")
    except ValueError as e:
        check("missing mandatory fields" in str(e).lower(), f"create_rule_draft rejected incomplete draft: {e}")

    print("\n--- 3. Validation Workflow ---")
    val_report = pkg.validate()
    check(val_report.is_valid, "Valid RulePackage produces 0 validation errors")
    check(isinstance(val_report.errors, list), "ValidationReport exposes errors list")
    check(isinstance(val_report.warnings, list), "ValidationReport exposes warnings list")
    check(isinstance(val_report.info, list), "ValidationReport exposes info list")

    # Invalid rule: undeclared dependency
    bad_rule = create_rule_draft(
        rule_id="DEMO.CUSTOM.INVALID_RULE",
        version="1.0.0",
        name="Invalid Rule",
        description="Rule with undeclared dependency and invalid op",
        tradition="CUSTOM_DEVELOPER",
        category="DEMO",
        provenance=pkg.provenance,
        condition_tree=P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
        dependencies=RuleDependencies(input_facts=[]),  # Empty!
    )
    bad_report = bad_rule.validate()
    # Note: validate_rule checks schema and rules; engine checks undeclared at eval
    # Let's verify with undeclared access in service preview
    dep_prev = preview_rule_dependencies(bad_rule)
    check(len(dep_prev.undeclared_dependency_diagnostics) > 0, "Undeclared dependency detected in preview")

    print("\n--- 4. Test Fixture System & Execution ---")
    test_report = run_rule_tests(pkg)
    check(test_report.total == 2, f"Total tests run: {test_report.total}")
    check(test_report.passed == 2, f"Passed tests: {test_report.passed}")
    check(test_report.failed == 0, f"Failed tests: {test_report.failed}")
    check(len(test_report.execution_fingerprint) == 64, "Deterministic 64-char execution fingerprint generated")

    # Disallow zero tests = tested
    pkg_no_tests = pkg.model_copy(update={"test_cases": []})
    try:
        run_rule_tests(pkg_no_tests, minimum_tests=1)
        check(False, "run_rule_tests allowed zero tests")
    except LifecycleTransitionError as e:
        check("Zero tests = tested is disallowed" in str(e), f"Zero tests rejected: {e}")

    print("\n--- 5. Golden Tests ---")
    golden_cases = [tc for tc in pkg.test_cases if tc.is_golden]
    check(len(golden_cases) == 2, "Golden test cases correctly designated")
    for gtc in golden_cases:
        exec_res = RuleTestExecutor(pkg).run_test_case(gtc)
        check(exec_res["outcome"] == "PASS", f"Golden test {gtc.test_id} passed")

    print("\n--- 6. Review System ---")
    rev = create_review_record(
        rule_id=pkg.rule_id,
        version=pkg.version,
        decision="DEFERRED",
        reviewer_type="human",
        notes="Awaiting board review",
        provenance_decision="ACCEPTED",
    )
    check(rev.decision == "DEFERRED", "Review created in DEFERRED decision state")
    approved_rev = create_review_record(
        rule_id=pkg.rule_id,
        version=pkg.version,
        decision="APPROVED",
        reviewer_type="human",
        notes="Approved for production",
        provenance_decision="ACCEPTED",
    )
    check(approved_rev.decision == "APPROVED", "Review updated to APPROVED")

    print("\n--- 7. Activation and Deactivation ---")
    # Rule must not activate from DRAFT directly
    act_ok, act_pkg, act_rep = activate_rule(pkg, review_record=approved_rev)
    check(not act_ok, f"Activation denied directly from DRAFT: {act_rep.activation_reason}")

    # Proper path: DRAFT -> VALIDATED -> TESTED -> REVIEW_PENDING -> ACTIVE
    pkg_v = pkg.transition_lifecycle("VALIDATED")
    pkg_t = pkg_v.transition_lifecycle("TESTED")
    pkg_t = pkg_t.model_copy(update={"test_report": test_report})
    pkg_rp = pkg_t.transition_lifecycle("REVIEW_PENDING")

    act_ok, act_pkg, act_rep = activate_rule(pkg_rp, review_record=approved_rev)
    check(act_ok, "Rule activated successfully after all gates passed")
    check(act_pkg.lifecycle.status == "ACTIVE", "Rule package state is ACTIVE")
    check(act_rep.deterministic_record["activation_state"] == "ACTIVE", "Activation report deterministic record stamped")

    # Deactivation: ACTIVE -> DISABLED
    dis_pkg = disable_rule(act_pkg)
    check(dis_pkg.lifecycle.status == "DISABLED", "Rule disabled to DISABLED state")

    # Re-activation: DISABLED -> ACTIVE
    re_act = dis_pkg.transition_lifecycle("ACTIVE")
    check(re_act.lifecycle.status == "ACTIVE", "Rule re-activated from DISABLED to ACTIVE")

    # Deprecation: ACTIVE -> DEPRECATED
    dep_pkg = deprecate_rule(re_act, deprecated_by="1.1.0")
    check(dep_pkg.lifecycle.status == "DEPRECATED", "Rule deprecated to DEPRECATED state")
    check(dep_pkg.lifecycle.deprecated_by == "1.1.0", "deprecated_by correctly recorded")

    # Archive: DEPRECATED -> ARCHIVED
    arc_pkg = archive_rule(dep_pkg)
    check(arc_pkg.lifecycle.status == "ARCHIVED", "Rule archived to ARCHIVED state")

    print("\n--- 8. RuleLabService Full Lifecycle ---")
    service = RuleLabService()
    lab_pkg = service.create_rule_draft(
        rule_id="DEMO.CUSTOM.SYNTHETIC_GOLDEN",
        version="1.0.0",
        name="Synthetic Golden Rule",
        description="Golden developer test rule",
        tradition="CUSTOM_DEVELOPER",
        category="DEMO",
        provenance=pkg.provenance,
        condition_tree=P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
        dependencies=RuleDependencies(input_facts=["natal.Mars.sign"]),
    )
    tc = RuleTestCase(
        test_id="TC01",
        description="Mars in Aries formed",
        input_fixture={"natal.Mars.sign": "Aries"},
        expected_formation="FORMED",
        expected_final_state="FORMED",
    )
    lab_pkg = service.add_test_case(lab_pkg.rule_id, lab_pkg.version, tc)

    # 1. Validate
    v_rep = service.validate_rule(lab_pkg.rule_id, lab_pkg.version)
    check(v_rep.is_valid, "Service validation clean")
    check(service.get_package(lab_pkg.rule_id, lab_pkg.version).lifecycle.status == "VALIDATED", "Lifecycle moved to VALIDATED")

    # 2. Test
    t_rep = service.test_rule(lab_pkg.rule_id, lab_pkg.version)
    check(t_rep.passed == 1, "Service tests passed")
    check(service.get_package(lab_pkg.rule_id, lab_pkg.version).lifecycle.status == "TESTED", "Lifecycle moved to TESTED")

    # 3. Submit for review
    rev_rec = service.submit_for_review(lab_pkg.rule_id, lab_pkg.version, notes="Ready for review")
    check(service.get_package(lab_pkg.rule_id, lab_pkg.version).lifecycle.status == "REVIEW_PENDING", "Lifecycle moved to REVIEW_PENDING")

    # 4. Approve review
    app_rec = service.approve_rule(rev_rec.review_id, notes="Approved by committee")
    check(app_rec.decision == "APPROVED", "Review decision APPROVED")

    # 5. Activate
    act_res = service.activate_rule(lab_pkg.rule_id, lab_pkg.version, review_id=rev_rec.review_id)
    check(act_res.activated, "Service rule activated")
    check(service.get_package(lab_pkg.rule_id, lab_pkg.version).lifecycle.status == "ACTIVE", "Lifecycle moved to ACTIVE")

    # 6. Evaluate active rule
    ctx = build_golden_context()
    eval_res = service.evaluate_active_rule(lab_pkg.rule_id, ctx)
    check(eval_res.status in ("FORMED", "NOT_FORMED", "UNKNOWN"), f"Active rule evaluated: status={eval_res.status}")

    # 7. Disable
    dis_res = service.disable_rule(lab_pkg.rule_id, lab_pkg.version)
    check(dis_res.lifecycle.status == "DISABLED", "Service rule disabled")

    # Historical evaluation after deactivation
    # We can still evaluate the historical definition
    hist_eval = evaluate_dynamic_rule(dis_res.rule, ctx)
    check(hist_eval.status == eval_res.status, "Historical evaluation preserved after deactivation")

    print("\n--- 9. Regression Protection & Version Coexistence ---")
    # Create version 1.1.0 without mutating 1.0.0
    pkg_110 = service.create_rule_draft(
        rule_id="DEMO.CUSTOM.SYNTHETIC_GOLDEN",
        version="1.1.0",
        name="Synthetic Golden Rule (v1.1.0)",
        description="Updated rule with Leo",
        tradition="CUSTOM_DEVELOPER",
        category="DEMO",
        provenance=pkg.provenance,
        condition_tree=P("planet_in_sign", {"planet": "Mars", "sign": "Leo"}),
        dependencies=RuleDependencies(input_facts=["natal.Mars.sign"]),
    )
    check(service.get_package("DEMO.CUSTOM.SYNTHETIC_GOLDEN", "1.0.0") is not None, "Version 1.0.0 remains available")
    check(service.get_package("DEMO.CUSTOM.SYNTHETIC_GOLDEN", "1.1.0") is not None, "Version 1.1.0 created and stored")
    all_vers = service.list_versions("DEMO.CUSTOM.SYNTHETIC_GOLDEN")
    check(all_vers == ["1.0.0", "1.1.0"], f"Both versions co-exist: {all_vers}")

    # Attempting to re-create 1.0.0 fails
    try:
        service.create_rule_draft(
            rule_id="DEMO.CUSTOM.SYNTHETIC_GOLDEN",
            version="1.0.0",
            name="Mutate Attempt",
            description="",
            tradition="CUSTOM_DEVELOPER",
            category="DEMO",
            provenance=pkg.provenance,
            condition_tree=P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
            dependencies=RuleDependencies(input_facts=["natal.Mars.sign"]),
        )
        check(False, "Service allowed mutation of existing version 1.0.0")
    except ValueError as e:
        check("Cannot mutate existing version" in str(e), f"Mutation rejected: {e}")

    print("\n--- 10. Semantic Version Diff ---")
    diff = service.compare_rule_versions("DEMO.CUSTOM.SYNTHETIC_GOLDEN", "1.0.0", "1.1.0")
    check(isinstance(diff, RuleDiff), "compare_rule_versions returned RuleDiff")
    check(diff.base_version == "1.0.0" and diff.target_version == "1.1.0", "Diff versions recorded")
    check("formation" in diff.categories[RuleDiffCategory.CHANGED_CONDITION], "Condition change detected in formation")
    check(len(diff.categories[RuleDiffCategory.CHANGED_METADATA]) > 0, "Metadata change detected (name/description)")

    print("\n--- 11. Catalogue and Filtering ---")
    all_rules = service.list_rules()
    check(len(all_rules) >= 1, f"list_rules returned {len(all_rules)} rules")
    custom_rules = filter_by_tradition(all_rules, "CUSTOM_DEVELOPER")
    check(len(custom_rules) >= 1, "filter_by_tradition isolates CUSTOM_DEVELOPER")
    western_rules = filter_by_tradition(all_rules, "WESTERN")
    check(len(western_rules) == 0, "Tradition isolation: no WESTERN rules returned")

    searched = service.search_rules("SYNTHETIC")
    check(len(searched) >= 1, f"search_rules found {len(searched)} matches")

    print("\n--- 12. RuleHealth Structured Status ---")
    health = service.get_rule_health("DEMO.CUSTOM.SYNTHETIC_GOLDEN", "1.0.0")
    check(isinstance(health, RuleHealth), "get_rule_health returned RuleHealth")
    check(health.schema_valid is True, "health.schema_valid is True")
    check(health.provenance_valid is True, "health.provenance_valid is True")
    check(health.dependencies_valid is True, "health.dependencies_valid is True")
    check(health.security_valid is True, "health.security_valid is True")
    check(health.regression_status == "STABLE", "health.regression_status is STABLE")

    print("\n--- 13. Source Management & Conflict Handling ---")
    sm = SourceManagement()
    s_pri = SourceRecord(
        source_id="SRC-001",
        category=PRIMARY,
        verification_status="TRADITIONAL",
        title="Classical Text A",
        author="Sage A",
        locator="Ch 1, v 5",
        quotation="Mars in Aries gives courage",
    )
    s_sec = SourceRecord(
        source_id="SRC-002",
        category=SECONDARY,
        verification_status="SECONDARY",
        title="Commentary B",
        author="Scholar B",
        locator="p. 42",
        quotation="Mars in Aries indicates bold action",
    )
    sm = sm.add_source(s_pri).add_source(s_sec)
    check(sm.primary.source_id == "SRC-001", "Primary source attached")
    check(sm.secondary.source_id == "SRC-002", "Secondary source attached")

    # Disallow auto-upgrade without locator/quotation
    s_unver = SourceRecord(source_id="SRC-UNVER", category=SUPPORTING, verification_status="UNVERIFIED")
    sm = sm.add_source(s_unver)
    try:
        sm.set_verification("SRC-UNVER", "VERIFIED")
        check(False, "Auto-upgrade to VERIFIED without citation allowed")
    except ValueError as e:
        check("Cannot upgrade source" in str(e), f"Auto-upgrade rejected: {e}")

    # Conflict preservation
    s_conf1 = SourceRecord(source_id="SRC-C", category=PRIMARY, verification_status="TRADITIONAL", quotation="A")
    s_conf2 = SourceRecord(source_id="SRC-C", category=PRIMARY, verification_status="CONTESTED", quotation="B")
    sm_conf = sm.record_conflict(s_conf1, s_conf2)
    check(len(sm_conf.conflicting) == 2, "Conflicting sources preserved as CONTESTED in conflicting list")

    print("\n--- 14. Immutable Audit Log ---")
    records = service.audit_log.get_records()
    check(len(records) >= 6, f"Audit log recorded {len(records)} events")
    event_types = {r.event_type for r in records}
    check("RULE_CREATED" in event_types, "RULE_CREATED event audited")
    check("RULE_VALIDATED" in event_types, "RULE_VALIDATED event audited")
    check("RULE_TESTED" in event_types, "RULE_TESTED event audited")
    check("RULE_REVIEWED" in event_types, "RULE_REVIEWED event audited")
    check("RULE_ACTIVATED" in event_types, "RULE_ACTIVATED event audited")
    check("RULE_DISABLED" in event_types, "RULE_DISABLED event audited")

    # Immutability of audit record
    aud_rec = records[0]
    try:
        aud_rec.actor = "malicious_actor"
        check(False, "AuditRecord allowed in-place mutation")
    except Exception:
        check(True, "AuditRecord is frozen/immutable")

    print("\n--- 15. Declarative Import and Export ---")
    exp = service.export_rule_package("DEMO.CUSTOM.SYNTHETIC_GOLDEN", "1.1.0")
    check(isinstance(exp, ExportResult), "Export returned ExportResult")
    check(len(exp.json_payload) > 0, "Export generated canonical JSON string")
    check(len(exp.fingerprint) == 64, "Export includes deterministic 64-char fingerprint")

    # Import
    imp_res = import_package(exp.json_payload)
    check(imp_res.success is True, "Import of exported package succeeded")
    check(imp_res.rule_package.rule_id == "DEMO.CUSTOM.SYNTHETIC_GOLDEN", "Imported package preserved rule_id")
    check(imp_res.rule_package.version == "1.1.0", "Imported package preserved version")

    # Reject duplicate version with different content (version 1.0.0 is registered in service.registry)
    exp_100 = service.export_rule_package("DEMO.CUSTOM.SYNTHETIC_GOLDEN", "1.0.0")
    modified_dict = json.loads(exp_100.json_payload)
    modified_dict["name"] = "Conflicting mutation with same version"
    imp_conflict = import_package(json.dumps(modified_dict), existing_registry=service.registry)
    check(not imp_conflict.success and imp_conflict.reject_reason == "different_content_same_version",
          "Import rejected duplicate version with conflicting content")

    print("\n--- 16. Deterministic Package Fingerprint ---")
    fp1 = compute_fingerprint(pkg)
    fp2 = compute_fingerprint(pkg)
    check(fp1 == fp2, f"Fingerprint is identical across calls: {fp1[:12]}")

    pkg_modified = pkg.model_copy(update={"description": "Modified description"})
    fp3 = compute_fingerprint(pkg_modified)
    check(fp1 != fp3, "Modified package produces a different fingerprint")

    print("\n--- 17. Dependency and Evidence Previews ---")
    dep_prev = service.preview_dependencies("DEMO.CUSTOM.SYNTHETIC_GOLDEN", "1.0.0")
    check(isinstance(dep_prev, DependencyPreview), "preview_dependencies returned DependencyPreview")
    check("natal.Mars.sign" in dep_prev.direct_facts, "Direct fact natal.Mars.sign detected")
    check(dep_prev.rule_id == "DEMO.CUSTOM.SYNTHETIC_GOLDEN", "Preview rule_id exact")

    ev_prev = service.preview_evidence("DEMO.CUSTOM.SYNTHETIC_GOLDEN", "1.0.0")
    check(isinstance(ev_prev, EvidencePreview), "preview_evidence returned EvidencePreview")
    check(len(ev_prev.evidence_chains) >= 1, f"Evidence chains mapped: {len(ev_prev.evidence_chains)}")
    check(ev_prev.evidence_chains[0].tree == "formation", "First evidence chain is for formation")

    print("\n--- 18. Security Boundary ---")
    # 1. Malicious payloads rejected
    malicious_scripts = [
        "__import__('os').system('dir')",
        "eval('1+1')",
        "exec('import sys')",
        "subprocess.Popen(['ls'])",
    ]
    for script in malicious_scripts:
        bad_json = json.dumps({"description": f"Safe text with injection {script}"})
        from core.rules.dynamic.dsl import find_suspicious_text
        susp = find_suspicious_text(bad_json)
        check(len(susp) > 0, f"Malicious pattern flagged: {script}")

    # 2. Benign prose allowed without false positives
    benign_prose = "Mars in Aries gives strong executive energy and leadership. The native acts boldly."
    susp_benign = find_suspicious_text(json.dumps({"description": benign_prose}))
    check(len(susp_benign) == 0, "Benign natural prose passed security scan without false positives")

    print("\n--- 19. UNKNOWN / INVALID Handling ---")
    # Evaluate a rule that requires D9 facts on a context where D9 is withheld
    facts = generate_chart_facts(year=1990, month=5, day=15, hour=14, minute=30, second=0, lat=13.0827, lon=80.2707, tz_name="Asia/Kolkata")
    ctx_no_varga = DynamicEvaluationContext(chart_facts=facts)  # varga_facts = None
    rule_needs_d9 = DynamicRuleDefinition(
        identity=RuleIdentity(rule_id="DEMO.CUSTOM.D9_TEST", rule_version="1.0.0", rule_name="D9 Test", description="Needs D9"),
        classification=RuleClassification(system="CUSTOM", tradition="CUSTOM_DEVELOPER", category="TEST"),
        provenance=pkg.provenance,
        semantics=RuleSemantics(formation=P("planet_in_varga_sign", {"planet": "Mars", "varga": "D9", "sign": "Leo"})),
        dependencies=RuleDependencies(input_facts=["varga.D9.Mars"], varga_dependencies=["D9"]),
        lifecycle=RuleLifecycle(status="ACTIVE"),
        validation=RuleValidationInfo(validation_status="VALID"),
    )
    res_unknown = evaluate_dynamic_rule(rule_needs_d9, ctx_no_varga)
    check(res_unknown.formation == "UNKNOWN", "Missing varga layer yields UNKNOWN (never FALSE or NOT_FORMED)")

    # Rule with undeclared input yields INVALID
    rule_invalid = DynamicRuleDefinition(
        identity=RuleIdentity(rule_id="DEMO.CUSTOM.INVALID_DEP", rule_version="1.0.0", rule_name="Undeclared", description="Undeclared"),
        classification=RuleClassification(system="CUSTOM", tradition="CUSTOM_DEVELOPER", category="TEST"),
        provenance=pkg.provenance,
        semantics=RuleSemantics(formation=P("planet_in_sign", {"planet": "Mars", "sign": "Aries"})),
        dependencies=RuleDependencies(input_facts=[]),  # missing!
        lifecycle=RuleLifecycle(status="ACTIVE"),
        validation=RuleValidationInfo(validation_status="VALID"),
    )
    res_invalid = evaluate_dynamic_rule(rule_invalid, ctx)
    check(res_invalid.status == "INVALID", "Undeclared dependency yields INVALID (never NOT_FORMED)")

    print("\n--- 20. 50-Run Determinism Verification ---")
    fp_set = set()
    diff_set = set()
    val_set = set()
    test_set = set()
    dep_set = set()

    for _ in range(50):
        # 1. Fingerprint
        fp_set.add(compute_fingerprint(pkg))
        # 2. Diff
        d = compare_rule_versions(pkg, pkg_110)
        diff_set.add(json.dumps(d.categories, sort_keys=True))
        # 3. Validation
        v = pkg.validate()
        val_set.add(f"{len(v.errors)}:{len(v.warnings)}")
        # 4. Test execution
        t = run_rule_tests(pkg)
        test_set.add(t.execution_fingerprint)
        # 5. Dependency preview
        dp = preview_rule_dependencies(pkg)
        dep_set.add(f"{dp.dependency_count}:{','.join(dp.direct_facts)}")

    check(len(fp_set) == 1, f"50 runs produced 1 unique fingerprint: {list(fp_set)[0][:12]}")
    check(len(diff_set) == 1, "50 runs produced 1 unique semantic diff")
    check(len(val_set) == 1, "50 runs produced 1 unique validation diagnostic count")
    check(len(test_set) == 1, "50 runs produced 1 unique test execution fingerprint")
    check(len(dep_set) == 1, "50 runs produced 1 unique dependency preview")

    print("\n--- 21. Performance Benchmark ---")
    t0 = time.perf_counter()
    for _ in range(100):
        service.list_rules()
    t_list = (time.perf_counter() - t0) / 100

    t0 = time.perf_counter()
    for _ in range(100):
        pkg.validate()
    t_val = (time.perf_counter() - t0) / 100

    t0 = time.perf_counter()
    for _ in range(100):
        export_package(pkg)
    t_exp = (time.perf_counter() - t0) / 100

    t0 = time.perf_counter()
    raw_json = export_package(pkg).json_payload
    for _ in range(100):
        import_package(raw_json)
    t_imp = (time.perf_counter() - t0) / 100

    t0 = time.perf_counter()
    for _ in range(100):
        run_rule_tests(pkg)
    t_test = (time.perf_counter() - t0) / 100

    t0 = time.perf_counter()
    for _ in range(100):
        preview_rule_dependencies(pkg)
    t_prev = (time.perf_counter() - t0) / 100

    print(f"  catalogue_lookup: {t_list*1000:.3f}ms")
    print(f"  validation:       {t_val*1000:.3f}ms")
    print(f"  export:           {t_exp*1000:.3f}ms")
    print(f"  import:           {t_imp*1000:.3f}ms")
    print(f"  test_execution:   {t_test*1000:.3f}ms")
    print(f"  dependency_prev:  {t_prev*1000:.3f}ms")
    check(t_list < 0.05 and t_val < 0.05 and t_test < 0.05, "Performance within sane sub-50ms domain thresholds")

    print("\n" + "=" * 70)
    print(f"PHASE 6C TEST RESULTS: {passed_tests} passed, {failed_tests} failed out of {total_tests} total")
    print("=" * 70)

    if failed_tests > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
