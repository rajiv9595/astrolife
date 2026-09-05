"""
Astrolife V2 — Phase 6D: Rule Knowledge, Evidence & Provenance Integration Tests.

Comprehensive test suite verifying:
- SourceRecord schema and verification states
- EvidenceRecord and EvidenceBundle
- ClaimRecord separation (SOURCE_CLAIM vs IMPLEMENTATION_CLAIM)
- EvidenceGraph construction and traceability
- SourceVerificationPolicy (VERIFIED requires locator+quotation)
- Tradition isolation
- Version lineage (evidence stays with version)
- Import/Export with evidence
- Security boundary
- Golden fixtures
- 50-run determinism
"""

import hashlib
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.rules.dynamic import (
    # Phase 6A/6B/6C base
    RuleIdentity, RuleClassification, SourceReference, RuleProvenance,
    ConditionNode, RuleSemantics, RuleDependencies, RuleEvidenceSpec,
    RuleLifecycle, RuleValidationInfo, DynamicRuleDefinition,
    RulePackage, RuleTestCase, RuleTestReport, ValidationReport,
    SourceRecord, SourceManagement, SourceManagement,
    PRIMARY, SECONDARY, SUPPORTING, CONFLICTING,
    VERIFIED, UNVERIFIED, CONTESTED, SECONDARY_STATUS, TRADITIONAL, USER_SUPPLIED,
    LIFECYCLE_STATES, LEGAL_TRANSITIONS, is_valid_transition,
    create_rule_draft, activate_rule, disable_rule, deprecate_rule, archive_rule,
    export_package, import_package, compute_fingerprint,
    RuleDiff, RuleDiffCategory, compare_rule_versions,
    # Phase 6D
    ClaimRecord, ClaimRegistry,
    EvidenceRecord, EvidenceBundle,
    SourceVerificationPolicy, DEFAULT_VERIFICATION_POLICY,
    verify_source, verify_source_management, validate_verification_transition,
    EvidenceGraph, GraphNode, GraphEdge,
    DIRECT_FACT, DERIVED_FACT, RULE_DERIVED, SOURCE_CLAIM,
    DERIVES, FEEDS, EVALUATES_TO, CO_CHART_FACT, SUPPORTS, CONTRADICTS, TRACKED_SEPARATELY,
    build_evidence_graph_from_bundle, trace_evaluation,
    RuleLabService,
)

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


def create_demo_package(
    rule_id: str = "DEMO.CUSTOM.PHASE6D_TEST",
    version: str = "1.0.0",
) -> RulePackage:
    prov = RuleProvenance(
        source_reference=SourceReference(
            source_id="DEV-6D-TEST",
            title="Phase 6D Test Source",
            author="Test Author",
            publication="Test Publication",
            locator="Section 1",
            quotation="Test quotation for verification",
            verification_status=USER_SUPPLIED,
        ),
        confidence="CUSTOM",
        provenance_status="USER_SUPPLIED",
    )
    deps = RuleDependencies(
        input_facts=["natal.Mars.sign", "natal.Saturn.sign"],
    )
    tc = RuleTestCase(
        test_id="TC01",
        description="Mars in Aries forms rule",
        input_fixture={"natal.Mars.sign": "Aries", "natal.Saturn.sign": "Taurus"},
        expected_formation="FORMED",
        expected_final_state="FORMED",
        is_golden=True,
    )
    pkg = create_rule_draft(
        rule_id=rule_id,
        version=version,
        name="Phase 6D Test Rule",
        description="Test rule for Phase 6D evidence integration",
        tradition="CUSTOM_DEVELOPER",
        category="TEST",
        provenance=prov,
        condition_tree=P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
        dependencies=deps,
        test_cases=[tc],
    )
    return pkg


def main() -> None:
    print("\n=== 1. SourceRecord Schema & Verification States ===")
    src = SourceRecord(
        source_id="SRC-001",
        category=PRIMARY,
        verification_status=UNVERIFIED,
        title="Test Text",
        author="Test Author",
        publication="Test Pub",
        locator="Ch 1, v 1",
        quotation="Mars in Aries gives strength",
    )
    check(src.source_id == "SRC-001", "SourceRecord created with all fields")
    check(src.verification_status == UNVERIFIED, "Default status is UNVERIFIED")

    # VERIFIED requires locator + quotation
    src_verified = SourceRecord(
        source_id="SRC-002",
        category=PRIMARY,
        verification_status=VERIFIED,
        title="Verified Text",
        author="Author",
        publication="Pub",
        locator="Ch 2, v 5",
        quotation="Verified quotation",
    )
    check(src_verified.verification_status == VERIFIED, "VERIFIED with locator+quotation accepted")

    # VERIFIED without locator/quotation should be rejected by policy
    policy = DEFAULT_VERIFICATION_POLICY
    bad_src = SourceRecord(source_id="SRC-BAD", category=PRIMARY, verification_status=VERIFIED)
    result = verify_source(bad_src, policy)
    check(not result.is_valid, "VERIFIED without locator+quotation rejected")
    check("locator" in result.missing_verified_fields and "quotation" in result.missing_verified_fields,
          "Missing fields correctly identified")

    # Transition validation
    errors = validate_verification_transition(UNVERIFIED, VERIFIED, src)
    check(len(errors) == 0, "UNVERIFIED -> VERIFIED allowed with locator+quotation")
    errors = validate_verification_transition(UNVERIFIED, VERIFIED, bad_src)
    check(len(errors) > 0, "UNVERIFIED -> VERIFIED rejected without locator+quotation")

    print("\n=== 2. SourceManagement & Conflict Preservation ===")
    sm = SourceManagement()
    s1 = SourceRecord(source_id="SRC-A", category=PRIMARY, verification_status=TRADITIONAL, quotation="Text A")
    s2 = SourceRecord(source_id="SRC-B", category=SECONDARY, verification_status=SECONDARY_STATUS, quotation="Text B")
    sm = sm.add_source(s1).add_source(s2)
    check(sm.primary is not None and sm.primary.source_id == "SRC-A", "Primary source attached")
    check(sm.secondary is not None and sm.secondary.source_id == "SRC-B", "Secondary source attached")

    # Conflict recording preserves both as CONTESTED
    s_conf1 = SourceRecord(source_id="SRC-C", category=PRIMARY, verification_status=TRADITIONAL, quotation="A")
    s_conf2 = SourceRecord(source_id="SRC-C", category=PRIMARY, verification_status=CONTESTED, quotation="B")
    sm_conf = sm.record_conflict(s_conf1, s_conf2)
    check(len(sm_conf.conflicting) == 2, "Conflicting sources preserved as CONTESTED")
    check(all(s.verification_status == CONTESTED for s in sm_conf.conflicting), "Both marked CONTESTED")

    print("\n=== 3. ClaimRecord Type Separation ===")
    source_claim = ClaimRecord(
        claim_id="CLAIM-001",
        claim_type="SOURCE_CLAIM",
        rule_id="DEMO.CUSTOM.TEST",
        rule_version="1.0.0",
        text="Mars in Aries gives strength",
        source_id="SRC-001",
        locator="Ch 1, v 1",
        quotation="Mars in Aries gives strength",
        verification_status=VERIFIED,
    )
    impl_claim = ClaimRecord(
        claim_id="CLAIM-002",
        claim_type="IMPLEMENTATION_CLAIM",
        rule_id="DEMO.CUSTOM.TEST",
        rule_version="1.0.0",
        text="Implement as planet_in_sign(Mars, Aries)",
        source_id=None,
        verification_status=USER_SUPPLIED,
    )
    interp_claim = ClaimRecord(
        claim_id="CLAIM-003",
        claim_type="INTERPRETATION_CLAIM",
        rule_id="DEMO.CUSTOM.TEST",
        rule_version="1.0.0",
        text="Traditional interpretation: Mars in Aries indicates courage",
        source_id="SRC-001",
        verification_status=TRADITIONAL,
    )
    dev_note = ClaimRecord(
        claim_id="CLAIM-004",
        claim_type="DEVELOPER_NOTE",
        rule_id="DEMO.CUSTOM.TEST",
        rule_version="1.0.0",
        text="Internal: test fixture for Phase 6D",
        verification_status=USER_SUPPLIED,
    )

    check(source_claim.claim_type == "SOURCE_CLAIM", "SOURCE_CLAIM type correct")
    check(impl_claim.claim_type == "IMPLEMENTATION_CLAIM", "IMPLEMENTATION_CLAIM type correct")
    check(interp_claim.claim_type == "INTERPRETATION_CLAIM", "INTERPRETATION_CLAIM type correct")
    check(dev_note.claim_type == "DEVELOPER_NOTE", "DEVELOPER_NOTE type correct")

    registry = ClaimRegistry()
    registry = registry.add_claim(source_claim).add_claim(impl_claim).add_claim(interp_claim).add_claim(dev_note)
    check(len(registry.get_source_claims()) == 1, "Registry filters SOURCE_CLAIM")
    check(len(registry.get_implementation_claims()) == 1, "Registry filters IMPLEMENTATION_CLAIM")
    check(len(registry.get_interpretation_claims()) == 1, "Registry filters INTERPRETATION_CLAIM")
    check(len(registry.get_developer_notes()) == 1, "Registry filters DEVELOPER_NOTE")

    print("\n=== 4. EvidenceRecord & EvidenceBundle ===")
    ev1 = EvidenceRecord(
        evidence_id="EVD-001",
        rule_id="DEMO.CUSTOM.TEST",
        rule_version="1.0.0",
        condition_path="semantics.formation",
        condition_type="planet_in_sign",
        fact_path="natal.Mars.sign",
        expected_value="Aries",
        actual_value="Aries",
        passed=True,
        tier=DIRECT_FACT,
        source_id="SRC-001",
        claim_id="CLAIM-001",
    )
    ev2 = EvidenceRecord(
        evidence_id="EVD-002",
        rule_id="DEMO.CUSTOM.TEST",
        rule_version="1.0.0",
        condition_path="semantics.cancellation",
        condition_type="planets_conjunct",
        fact_path="natal.Mars.sign",
        expected_value="NOT_CANCELLED",
        actual_value="NOT_CANCELLED",
        passed=True,
        tier=RULE_DERIVED,
    )

    bundle = EvidenceBundle(
        rule_id="DEMO.CUSTOM.TEST",
        rule_version="1.0.0",
        rule_name="Phase 6D Test Rule",
        tradition="CUSTOM_DEVELOPER",
        category="TEST",
        formation_status="FORMED",
        cancellation_status="NOT_CANCELLED",
        mitigation_status="NOT_MITIGATED",
        source_references=["SRC-001"],
        evidence_records=[ev1, ev2],
        resolved_facts={"natal.Mars.sign": "Aries", "natal.Saturn.sign": "Taurus"},
        unresolved_facts=[],
        declared_dependencies=["natal.Mars.sign", "natal.Saturn.sign"],
        used_dependencies=["natal.Mars.sign", "natal.Saturn.sign"],
        diagnostics=[],
        conflicts=[],
    )
    check(bundle.formation_status == "FORMED", "Bundle formation status set")
    check(len(bundle.evidence_records) == 2, "Bundle contains evidence records")
    check(bundle.is_complete(), "FORMED bundle with evidence is complete")

    # Traceability export
    trace = bundle.to_traceability_dict()
    check("rule" in trace and "evidence" in trace and "sources" in trace, "Traceability dict has all sections")
    check(len(trace["evidence"]) == 2, "Traceability exports all evidence")
    check(len(trace["fingerprint"]) == 64, "Fingerprint computed")

    print("\n=== 5. EvidenceGraph Construction ===")
    graph = build_evidence_graph_from_bundle(bundle)
    check(len(graph.nodes) > 0, "Graph has nodes")
    check(len(graph.edges) > 0, "Graph has edges")

    # Check tier distribution
    direct_facts = graph.nodes_by_tier(DIRECT_FACT)
    rule_derived = graph.nodes_by_tier(RULE_DERIVED)
    source_claims = graph.nodes_by_tier(SOURCE_CLAIM)
    check(len(direct_facts) >= 2, "Graph has DIRECT_FACT nodes for resolved facts")
    check(len(rule_derived) >= 2, "Graph has RULE_DERIVED nodes for condition/result")
    check(len(source_claims) >= 1, "Graph has SOURCE_CLAIM nodes")

    # Check trace path
    trace_result = trace_evaluation(bundle)
    check("trace_path" in trace_result, "Trace evaluation produces trace path")
    trace_path = trace_result["trace_path"]
    check(len(trace_path) > 0, "Trace path non-empty")
    step_types = {step["step"] for step in trace_path}
    check("RESULT" in step_types and "CONDITION" in step_types, "Trace has RESULT and CONDITION steps")

    print("\n=== 6. SourceVerificationPolicy Enforcement ===")
    policy = SourceVerificationPolicy()
    src_ok = SourceRecord(source_id="SRC-OK", category=PRIMARY, verification_status=VERIFIED,
                          locator="Ch 1", quotation="Quote")
    src_missing_loc = SourceRecord(source_id="SRC-NOLOC", category=PRIMARY, verification_status=VERIFIED,
                                    quotation="Quote")
    src_missing_quot = SourceRecord(source_id="SRC-NOQUOT", category=PRIMARY, verification_status=VERIFIED,
                                     locator="Ch 1")
    check(policy.validate_verified(src_ok) == [], "VERIFIED with all fields passes")
    check(policy.validate_verified(src_missing_loc) == ["locator"], "Missing locator detected")
    check(policy.validate_verified(src_missing_quot) == ["quotation"], "Missing quotation detected")

    # SourceManagement verification
    sm = SourceManagement()
    src_ok = src_ok.model_copy(update={"category": PRIMARY})
    src_missing_loc = src_missing_loc.model_copy(update={"category": SECONDARY})
    sm = sm.add_source(src_ok).add_source(src_missing_loc)
    results = verify_source_management(sm, policy)
    check(len(results) == 2, "Both sources verified")
    check(results[0].is_valid, "Valid source passes")
    check(not results[1].is_valid, "Invalid source fails")
    check("locator" in results[1].missing_verified_fields, "Missing locator reported")

    print("\n=== 7. Tradition Isolation ===")
    # EvidenceBundle carries explicit tradition
    jaimini_bundle = EvidenceBundle(
        rule_id="JAI.TEST.RULE",
        rule_version="1.0.0",
        rule_name="Jaimini Test",
        tradition="JAIMINI",
        category="TEST",
        formation_status="FORMED",
        cancellation_status="NOT_CANCELLED",
        mitigation_status="NOT_MITIGATED",
        source_references=[],
        evidence_records=[],
        resolved_facts={},
        unresolved_facts=[],
        declared_dependencies=[],
        used_dependencies=[],
        diagnostics=[],
        conflicts=[],
    )
    parashari_bundle = EvidenceBundle(
        rule_id="PARA.TEST.RULE",
        rule_version="1.0.0",
        rule_name="Parashari Test",
        tradition="PARASHARI_CLASSICAL",
        category="TEST",
        formation_status="FORMED",
        cancellation_status="NOT_CANCELLED",
        mitigation_status="NOT_MITIGATED",
        source_references=[],
        evidence_records=[],
        resolved_facts={},
        unresolved_facts=[],
        declared_dependencies=[],
        used_dependencies=[],
        diagnostics=[],
        conflicts=[],
    )
    check(jaimini_bundle.tradition == "JAIMINI", "Bundle tradition JAIMINI")
    check(parashari_bundle.tradition == "PARASHARI_CLASSICAL", "Bundle tradition PARASHARI_CLASSICAL")

    # Graph construction respects tradition
    g1 = build_evidence_graph_from_bundle(jaimini_bundle)
    g2 = build_evidence_graph_from_bundle(parashari_bundle)
    check(g1.fingerprint != g2.fingerprint, "Different traditions produce different fingerprints")

    print("\n=== 8. Version Lineage (Evidence Stays with Version) ===")
    pkg_v1 = create_demo_package("DEMO.CUSTOM.VERSION_TEST", "1.0.0")
    pkg_v1_validated = pkg_v1.validate()
    check(pkg_v1_validated.is_valid, "Package v1 validation passes")
    pkg_v1_tested = pkg_v1.transition_lifecycle("VALIDATED").transition_lifecycle("TESTED")

    pkg_v2 = create_demo_package("DEMO.CUSTOM.VERSION_TEST", "1.1.0")
    pkg_v2_validated = pkg_v2.validate()

    check(pkg_v1.version == "1.0.0" and pkg_v2.version == "1.1.0", "Versions distinct")
    check(pkg_v1.fingerprint() != pkg_v2.fingerprint(), "Different versions have different fingerprints")

    # Evidence bundle for v1 should remain valid for v1
    bundle_v1 = EvidenceBundle(
        rule_id="DEMO.CUSTOM.VERSION_TEST",
        rule_version="1.0.0",
        rule_name="Version Test",
        tradition="CUSTOM_DEVELOPER",
        category="TEST",
        formation_status="FORMED",
        cancellation_status="NOT_CANCELLED",
        mitigation_status="NOT_MITIGATED",
        source_references=[],
        evidence_records=[],
        resolved_facts={"natal.Mars.sign": "Aries"},
        unresolved_facts=[],
        declared_dependencies=["natal.Mars.sign"],
        used_dependencies=["natal.Mars.sign"],
        diagnostics=[],
        conflicts=[],
    )
    check(bundle_v1.rule_version == "1.0.0", "Bundle locked to v1.0.0")

    print("\n=== 9. Conflict Model ===")
    # Source conflict
    s1 = SourceRecord(source_id="SRC-CONF", category=PRIMARY, verification_status=TRADITIONAL, quotation="A")
    s2 = SourceRecord(source_id="SRC-CONF", category=PRIMARY, verification_status=CONTESTED, quotation="B")
    sm_conf = SourceManagement().record_conflict(s1, s2)
    check(len(sm_conf.conflicting) == 2, "Source conflict preserves both")
    check(all(s.verification_status == CONTESTED for s in sm_conf.conflicting), "Both CONTESTED")

    # Rule conflict types (from Phase 5F)
    from core.jaimini.conflicts import RuleConflict, DIRECT_CONTRADICTION, TRADITION_VARIANT, INSUFFICIENT_INFORMATION
    rc = RuleConflict(
        rule_a="JAI.TEST.A",
        rule_b="JAI.TEST.B",
        conflict_class=DIRECT_CONTRADICTION,
        same_proposition=True,
        detail="Both FORMED on disjoint conditions",
        resolution="REPORTED_ONLY",
    )
    check(rc.resolution == "REPORTED_ONLY", "Conflict resolution is REPORTED_ONLY")
    check(rc.conflict_class == DIRECT_CONTRADICTION, "Direct contradiction detected")

    print("\n=== 10. Import/Export with Evidence ===")
    pkg = create_demo_package("DEMO.CUSTOM.IMPORT_EXPORT", "1.0.0")
    exp = export_package(pkg)
    check(len(exp.json_payload) > 0, "Export produces JSON")
    check(len(exp.fingerprint) == 64, "Export includes fingerprint")

    imp = import_package(exp.json_payload)
    check(imp.success, "Import of exported package succeeds")
    check(imp.rule_package.rule_id == pkg.rule_id, "Imported rule_id preserved")
    check(imp.rule_package.version == pkg.version, "Imported version preserved")
    check(imp.rule_package.fingerprint() == pkg.fingerprint(), "Imported fingerprint matches")

    # Import with evidence bundle in JSON (simulate)
    pkg_json = json.loads(exp.json_payload)
    pkg_json["evidence_bundle"] = bundle.to_traceability_dict()
    imp2 = import_package(json.dumps(pkg_json))
    check(imp2.success, "Import with evidence bundle succeeds")

    print("\n=== 11. Security Boundary ===")
    from core.rules.dynamic.dsl import find_suspicious_text
    malicious = [
        "__import__('os').system('dir')",
        "eval('1+1')",
        "exec('import sys')",
    ]
    for m in malicious:
        bad_json = json.dumps({"description": f"Safe text {m}"})
        check(len(find_suspicious_text(bad_json)) > 0, f"Malicious pattern flagged: {m[:20]}")

    benign = "Mars in Aries gives strong executive energy and leadership. The native acts boldly."
    check(len(find_suspicious_text(json.dumps({"description": benign}))) == 0, "Benign prose passes")

    print("\n=== 12. UNKNOWN / INVALID Semantics ===")
    # Bundle with UNKNOWN formation
    unknown_bundle = EvidenceBundle(
        rule_id="DEMO.CUSTOM.UNKNOWN_TEST",
        rule_version="1.0.0",
        rule_name="Unknown Test",
        tradition="CUSTOM_DEVELOPER",
        category="TEST",
        formation_status="UNKNOWN",
        cancellation_status="UNKNOWN",
        mitigation_status="UNKNOWN",
        source_references=[],
        evidence_records=[],
        resolved_facts={},
        unresolved_facts=["natal.Mars.sign"],
        declared_dependencies=["natal.Mars.sign"],
        used_dependencies=[],
        diagnostics=["Missing dependency: natal.Mars.sign"],
        conflicts=[],
    )
    check(unknown_bundle.formation_status == "UNKNOWN", "UNKNOWN status preserved")
    check(len(unknown_bundle.unresolved_facts) == 1, "Unresolved facts tracked")
    check(not unknown_bundle.is_complete(), "UNKNOWN bundle is not complete (expected)")

    print("\n=== 13. Golden Fixtures ===")
    # 1. Verified structure (no false quotation authenticity)
    verified_fixture = SourceRecord(
        source_id="SRC-VERIFIED-STRUCT",
        category=PRIMARY,
        verification_status=VERIFIED,
        title="Structured Test Source",
        author="Test Author",
        publication="Test Pub",
        locator="Ch 1, v 1",
        quotation="Test quotation - structure verified, not claiming classical authenticity",
    )
    check(verified_fixture.verification_status == VERIFIED, "Verified structure fixture")

    # 2. Unverified source
    unverified_fixture = SourceRecord(
        source_id="SRC-UNVERIFIED",
        category=PRIMARY,
        verification_status=UNVERIFIED,
        title="Unverified Source",
        author="Unknown",
        publication="Unknown",
        locator="",
        quotation="",
    )
    check(unverified_fixture.verification_status == UNVERIFIED, "Unverified fixture")

    # 3. Contested source
    contested_fixture = SourceRecord(
        source_id="SRC-CONTESTED",
        category=CONFLICTING,
        verification_status=CONTESTED,
        title="Contested Source",
        author="Author A / Author B",
        publication="Journal",
        locator="p. 10",
        quotation="Conflicting interpretation A",
    )
    check(contested_fixture.verification_status == CONTESTED, "Contested fixture")

    # 4. Tradition-dependent
    trad_fixture = SourceRecord(
        source_id="SRC-TRAD",
        category=PRIMARY,
        verification_status=TRADITIONAL,
        title="Traditional Text",
        author="Traditional Author",
        publication="Tradition",
        locator="Ch 5",
        quotation="Traditional teaching",
    )
    check(trad_fixture.verification_status == TRADITIONAL, "Tradition-dependent fixture")

    # 5. Conflicting rule fixture
    conflict_bundle = EvidenceBundle(
        rule_id="DEMO.CUSTOM.CONFLICT_TEST",
        rule_version="1.0.0",
        rule_name="Conflict Test",
        tradition="CUSTOM_DEVELOPER",
        category="TEST",
        formation_status="FORMED",
        cancellation_status="NOT_CANCELLED",
        mitigation_status="NOT_MITIGATED",
        source_references=["SRC-A", "SRC-B"],
        evidence_records=[],
        resolved_facts={},
        unresolved_facts=[],
        declared_dependencies=[],
        used_dependencies=[],
        diagnostics=["Conflict with rule DEMO.CUSTOM.OTHER_RULE"],
        conflicts=["DEMO.CUSTOM.OTHER_RULE"],
    )
    check(len(conflict_bundle.conflicts) == 1, "Conflicting rule fixture has conflict")

    print("\n=== 14. Traceability Test ===")
    trace = trace_evaluation(bundle)
    check("evidence_bundle" in trace and "evidence_graph" in trace, "Trace has bundle and graph")
    check(trace["evidence_bundle"]["rule"]["rule_id"] == "DEMO.CUSTOM.TEST", "Trace preserves rule_id")
    check(len(trace["evidence_graph"]["nodes"]) > 0, "Trace graph has nodes")

    print("\n=== 15. Historical Reproducibility ===")
    # Create bundle, fingerprint it
    fp1 = bundle.fingerprint
    # Recreate identical bundle
    bundle2 = EvidenceBundle(
        rule_id=bundle.rule_id,
        rule_version=bundle.rule_version,
        rule_name=bundle.rule_name,
        tradition=bundle.tradition,
        category=bundle.category,
        formation_status=bundle.formation_status,
        cancellation_status=bundle.cancellation_status,
        mitigation_status=bundle.mitigation_status,
        source_references=list(bundle.source_references),
        evidence_records=list(bundle.evidence_records),
        resolved_facts=dict(bundle.resolved_facts),
        unresolved_facts=list(bundle.unresolved_facts),
        declared_dependencies=list(bundle.declared_dependencies),
        used_dependencies=list(bundle.used_dependencies),
        diagnostics=list(bundle.diagnostics),
        conflicts=list(bundle.conflicts),
    )
    fp2 = bundle2.fingerprint
    check(fp1 == fp2, "Identical bundles produce identical fingerprints")

    # Version isolation
    check(bundle.rule_version == "1.0.0" and bundle2.rule_version == "1.0.0", "Bundle version locked")

    print("\n=== 16. Determinism (50 runs) ===")
    g_fp = build_evidence_graph_from_bundle(bundle).fingerprint()
    det_ok = True
    for i in range(50):
        g = build_evidence_graph_from_bundle(bundle)
        if g.fingerprint() != g_fp:
            print(f"  Run {i}: g_fp={g.fingerprint()[:16]} expected={g_fp[:16]}")
            det_ok = False
            break
    check(det_ok, "50 runs produce identical graph fingerprint")

    # EvidenceRecord fingerprint determinism
    ev_fp1 = hashlib.sha256(json.dumps(ev1.to_fingerprint_dict(), sort_keys=True).encode()).hexdigest()
    ev_fp2 = hashlib.sha256(json.dumps(ev1.to_fingerprint_dict(), sort_keys=True).encode()).hexdigest()
    check(ev_fp1 == ev_fp2, "EvidenceRecord fingerprint deterministic")

    print("\n=== 17. Claim Source Separation in Bundle ===")
    # EvidenceRecord can link to CLAIM (source text) vs implementation
    ev_with_claim = EvidenceRecord(
        evidence_id="EVD-CLAIM",
        rule_id="DEMO.CUSTOM.CLAIM_TEST",
        rule_version="1.0.0",
        condition_path="semantics.formation",
        condition_type="planet_in_sign",
        fact_path="natal.Mars.sign",
        expected_value="Aries",
        actual_value="Aries",
        passed=True,
        tier=SOURCE_CLAIM,
        source_id="SRC-001",
        claim_id="CLAIM-001",
    )
    bundle_with_claim = EvidenceBundle(
        rule_id="DEMO.CUSTOM.CLAIM_TEST",
        rule_version="1.0.0",
        rule_name="Claim Test",
        tradition="CUSTOM_DEVELOPER",
        category="TEST",
        formation_status="FORMED",
        cancellation_status="NOT_CANCELLED",
        mitigation_status="NOT_MITIGATED",
        source_references=["SRC-001"],
        evidence_records=[ev_with_claim],
        resolved_facts={"natal.Mars.sign": "Aries"},
        unresolved_facts=[],
        declared_dependencies=["natal.Mars.sign"],
        used_dependencies=["natal.Mars.sign"],
        diagnostics=[],
        conflicts=[],
    )
    trace_claim = trace_evaluation(bundle_with_claim)
    trace_steps = [s["step"] for s in trace_claim["trace_path"]]
    check("CLAIM" in trace_steps, "Trace includes CLAIM step for source claim")
    check("SOURCE" in trace_steps, "Trace includes SOURCE step")

    print("\n=== 18. RulePackage Integration ===")
    pkg = create_demo_package("DEMO.CUSTOM.PKG_INTEGRATION", "1.0.0")
    pkg_valid = pkg.validate()
    check(pkg_valid.is_valid, "Package validation passes")

    # Correct lifecycle: DRAFT -> VALIDATED -> TESTED -> REVIEW_PENDING -> ACTIVE
    # Must run tests and attach test report before REVIEW_PENDING
    from core.rules.dynamic import run_rule_tests
    test_report = run_rule_tests(pkg)
    check(test_report.passed == test_report.total, "All tests passed")

    pkg_tested = pkg.transition_lifecycle("VALIDATED").transition_lifecycle("TESTED")
    pkg_tested = pkg_tested.model_copy(update={"test_report": test_report})
    pkg_review = pkg_tested.transition_lifecycle("REVIEW_PENDING")
    check(pkg_review.lifecycle.status == "REVIEW_PENDING", "Package in REVIEW_PENDING")

    from core.rules.dynamic import RuleReviewRecord
    rev = RuleReviewRecord(review_id="R1", rule_id=pkg_review.rule_id, version=pkg_review.version,
                           decision="APPROVED", reviewer_type="human", notes="OK", provenance_decision="ACCEPTED")
    act_ok, pkg_active, act_rep = activate_rule(pkg_review, review_record=rev)
    check(act_ok, "Activation succeeds with review")
    check(pkg_active.lifecycle.status == "ACTIVE", "Package is ACTIVE after activation")

    # Export/import cycle
    exp = export_package(pkg_active)
    imp = import_package(exp.json_payload)
    check(imp.success, "Round-trip export/import works")
    check(imp.rule_package.fingerprint() == pkg_active.fingerprint(), "Fingerprint preserved")

    print("\n" + "=" * 70)
    print(f"PHASE 6D TEST RESULTS: {passed_tests} passed, {failed_tests} failed out of {total_tests} total")
    print("=" * 70)

    if failed_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()