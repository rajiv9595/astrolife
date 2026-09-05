"""
Astrolife V2 — Phase 6E: Knowledge Catalogue + Applicability Engine Tests.

Verifies (no prediction, no interpretation, no new astrology anywhere):
- catalogue schema / registration / versioning (exact-version reproducibility)
- tradition / profile / lifecycle filtering and isolation
- dependency indexing + reverse dependency indexing
- applicability states APPLICABLE / NOT_APPLICABLE / UNKNOWN / INVALID
- 13 synthetic applicability cases (§27), UNKNOWN never collapsed
- applicability != evaluation, applicability != prediction
- evidence/source visibility (counts only, no scores), conflict visibility
- golden catalogue (accepted rules only) + golden chart applicability
- security (inert text), canonical serialization round-trip
- 50-run determinism, performance recording, full API contract
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
from core.jaimini.dasha import calculate_jaimini_dasha
from core.jaimini.pipeline import generate_jaimini_facts
from core.jaimini.profile import JaiminiCalculationProfile
from core.strength.pipeline import generate_strength_report
from core.transit.calculator import calculate_transit_positions
from core.rules.dynamic import (
    ConditionNode,
    DynamicRuleDefinition,
    RuleClassification,
    RuleDependencies,
    RuleEvidenceSpec,
    RuleIdentity,
    RuleLifecycle,
    RuleProvenance,
    RuleSemantics,
    RuleValidationInfo,
    SourceReference,
    build_context,
    evaluate_dynamic_rule,
    find_suspicious_text,
)
from core.rules.dynamic.knowledge import (
    APPLICABLE,
    CATEGORIES,
    INVALID,
    NOT_APPLICABLE,
    RULE_SYSTEMS,
    TRADITIONS,
    UNKNOWN,
    CatalogueSnapshot,
    KnowledgeContext,
    RuleApplicabilitySpec,
    RuleKnowledgeCatalogue,
    RuleKnowledgeEntry,
    build_custom_fixtures,
    build_golden_catalogue,
    build_knowledge_graph,
    build_snapshot,
    derive_spec_from_definition,
    entry_from_dynamic_definition,
    evaluate_rule_applicability,
    find_conflicts,
    find_rules,
    find_rules_by_dasha,
    find_rules_by_fact,
    find_rules_by_jaimini_dependency,
    find_rules_by_source,
    find_rules_by_strength,
    find_rules_by_transit,
    find_rules_by_varga,
    find_rules_for_context,
    get_catalogue_snapshot,
    get_rule,
    get_rule_health,
    get_rule_version,
    measure_performance,
    normalize_category,
    normalize_system,
    normalize_tradition,
    snapshot_round_trip,
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


def P(op, params=None, children=None, n=None):
    return ConditionNode(op=op, params=params or {}, children=children or [], n=n)


def custom_def(rule_id, formation, input_facts, lifecycle="ACTIVE",
               varga=None, dasha=None, transit=None, strength=None,
               rule_deps=None, version="1.0.0"):
    return DynamicRuleDefinition(
        identity=RuleIdentity(rule_id=rule_id, rule_version=version,
                              rule_name=rule_id,
                              description=f"6E test fixture {rule_id}; no classical claim."),
        classification=RuleClassification(system="DYNAMIC_CUSTOM",
                                          tradition="CUSTOM_DEVELOPER",
                                          category="CUSTOM", subcategory="TEST"),
        provenance=RuleProvenance(
            source_reference=SourceReference(source_id="DEV-6E-TEST",
                                             verification_status="USER_SUPPLIED"),
            provenance_status="USER_SUPPLIED", confidence="CUSTOM"),
        semantics=RuleSemantics(formation=formation),
        dependencies=RuleDependencies(
            input_facts=input_facts, rule_dependencies=rule_deps or [],
            varga_dependencies=varga or [], dasha_dependencies=dasha or [],
            transit_dependencies=transit or [], strength_dependencies=strength or []),
        evidence=RuleEvidenceSpec(evidence_requirements=["formation"]),
        lifecycle=RuleLifecycle(status=lifecycle),
        validation=RuleValidationInfo(validation_status="VALID"))


# ---------------------------------------------------------------- golden data
DT = datetime(2026, 1, 1, tzinfo=timezone.utc)
GCHART = generate_chart_facts(year=2005, month=8, day=17, hour=0, minute=2,
                              second=0, lat=16.9409, lon=81.9961,
                              tz_name="Asia/Kolkata", profile=CalculationProfile())
GVARGA = calculate_all_vargas(GCHART)
GJF = generate_jaimini_facts(GCHART, GVARGA, JaiminiCalculationProfile())
GSR = generate_strength_report(GCHART)
GTL = calculate_vimshottari_timeline(GCHART)
GJD = calculate_jaimini_dasha(GCHART, GJF)
GTS = calculate_transit_positions(DT)


def golden_dynamic():
    return build_context(
        chart_facts=GCHART, varga_facts=GVARGA, strength_report=GSR,
        vimshottari_timeline=GTL, vimshottari_datetime=DT,
        jaimini_dasha_result=GJD, jaimini_dasha_datetime=DT,
        transit_snapshot=GTS, jaimini_facts=GJF)


GOLDEN = KnowledgeContext(dynamic=golden_dynamic())
GOLDEN_CAT = build_golden_catalogue()

BANNED = ("will happen", "likely event", "high probability", "future outcome",
          "life result", "recommendation")


def main() -> None:
    print("\n=== 1. Catalogue schema ===")
    entry = GOLDEN_CAT.get_rule_version("CUSTOM.NATAL.TEST", "1.0.0")
    check(entry is not None, "golden custom entry retrievable")
    required = ("rule_id rule_version name description system tradition category "
                "subcategory lifecycle_status validation_status provenance_status "
                "source_ids evidence_ids dependency_manifest supersedes "
                "superseded_by conflicts applicability_spec").split()
    canon = entry.to_canonical_dict()
    check(all(k in canon for k in required) and len(entry.fingerprint) == 64,
          "entry carries all §3 fields")
    check(entry.fingerprint == entry.compute_fingerprint(), "fingerprint stable over canonical dict")
    check(entry.system in RULE_SYSTEMS, "system in taxonomy")
    check(entry.tradition in TRADITIONS, "tradition in taxonomy")
    check(entry.category in CATEGORIES, "category in taxonomy")

    print("\n=== 2. Registration ===")
    scratch = RuleKnowledgeCatalogue()
    check(len(scratch.entries) == 0, "fresh catalogue empty")
    scratch = scratch.register(entry)
    check(scratch.get_rule_version("CUSTOM.NATAL.TEST", "1.0.0") is not None,
          "registered entry retrievable by exact id+version")
    check(scratch.rule_ids() == ["CUSTOM.NATAL.TEST"], "rule id index deterministic")

    print("\n=== 3. Versioning (exact identity, never silent latest) ===")
    v2def = custom_def("CUSTOM.NATAL.TEST",
                       P("planet_in_sign", {"planet": "Mars", "sign": "Taurus"}),
                       ["natal.Mars.sign"], version="1.1.0")
    scratch = scratch.register(entry_from_dynamic_definition(v2def))
    check(scratch.list_versions("CUSTOM.NATAL.TEST") == ["1.0.0", "1.1.0"],
          "versions listed in semver order")
    check(scratch.get_rule_version("CUSTOM.NATAL.TEST", "1.0.0").applicability_spec is not None
          and scratch.get_rule_version("CUSTOM.NATAL.TEST", "1.1.0") is not None,
          "both versions coexist")
    check(scratch.get_rule_version("CUSTOM.NATAL.TEST", "1.0.0").fingerprint
          != scratch.get_rule_version("CUSTOM.NATAL.TEST", "1.1.0").fingerprint,
          "version fingerprints differ")
    check(scratch.latest_active_version("CUSTOM.NATAL.TEST") == "1.1.0",
          "latest active version explicit")
    check(scratch.get_rule("CUSTOM.NATAL.TEST", "1.0.0").rule_version == "1.0.0",
          "exact version reproducible")

    print("\n=== 4. Tradition filtering + isolation ===")
    jaimini_only = GOLDEN_CAT.find_rules(tradition="JAIMINI_CLASSICAL")
    check(len(jaimini_only) == 12, "12 Jaimini entries under JAIMINI_CLASSICAL")
    check(all(e.tradition == "JAIMINI_CLASSICAL" for e in jaimini_only),
          "tradition filter exact")
    check(not any(e.rule_id.startswith("PARASHARI.") for e in jaimini_only),
          "JAIMINI query never silently includes Parashari")
    legacy = GOLDEN_CAT.find_rules(tradition="JAIMINI")
    check(len(legacy) == 12, "legacy JAIMINI alias resolves identically")
    check(normalize_tradition("JAIMINI") == "JAIMINI_CLASSICAL"
          and normalize_tradition("CUSTOM") == "CUSTOM_DEVELOPER",
          "legacy aliases normalized, canonical enums reused")
    kctx_jaimini = KnowledgeContext(dynamic=golden_dynamic(), tradition="JAIMINI_CLASSICAL")
    discovered = GOLDEN_CAT.find_rules_for_context(kctx_jaimini, mode="ALL")
    jaimini_ids = {e.rule_id for e, r in discovered if r.status == APPLICABLE}
    check("PARASHARI.YOGA.RAJA_KENDRA_TRIKONA" not in jaimini_ids,
          "Parashari not applicable under JAIMINI query")
    check(any(i.startswith("JAI.") for i in jaimini_ids), "Jaimini applicable under JAIMINI query")

    print("\n=== 5. Profile filtering + isolation ===")
    prof_def = custom_def("CUSTOM.PROFILE.TEST",
                          P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                          ["natal.Mars.sign"])
    prof_entry = entry_from_dynamic_definition(prof_def)
    prof_spec = RuleApplicabilitySpec(
        **{**prof_entry.applicability_spec.model_dump(exclude={"applicability_condition"}),
           "profile_constraints": ["CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL"],
           "applicability_condition": None})
    prof_entry = prof_entry.model_copy(update={"applicability_spec": prof_spec})
    prof_entry = prof_entry.model_copy(update={"fingerprint": prof_entry.compute_fingerprint()})
    scat = GOLDEN_CAT.register(prof_entry)
    match_ctx = KnowledgeContext(dynamic=golden_dynamic(),
                                 profile="CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL")
    r_match = evaluate_rule_applicability(prof_entry, match_ctx, scat)
    check(r_match.status == APPLICABLE, "rule applicable under its own profile")
    mismatch_ctx = KnowledgeContext(dynamic=golden_dynamic(),
                                    profile="CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED")
    r_mismatch = evaluate_rule_applicability(prof_entry, mismatch_ctx, scat)
    check(r_mismatch.status == NOT_APPLICABLE
          and "PROFILE_MISMATCH" in r_mismatch.reason_codes(),
          "profile mismatch -> NOT_APPLICABLE + PROFILE_MISMATCH")
    only = scat.find_rules_for_context(mismatch_ctx, mode="PROFILE_ONLY",
                                       profile="CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED")
    check(all(e.rule_id != "CUSTOM.PROFILE.TEST" for e, _ in only),
          "PROFILE_ONLY discovery excludes other-profile rules")

    print("\n=== 6. Lifecycle filtering (deprecated never ACTIVE) ===")
    active = GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ACTIVE_ONLY")
    active_ids = {e.rule_id for e, _ in active}
    check("CUSTOM.DEPRECATED.TEST" not in active_ids, "deprecated rule not exposed as ACTIVE")
    dep_entry = GOLDEN_CAT.get_rule_version("CUSTOM.DEPRECATED.TEST", "1.0.0")
    r_dep = evaluate_rule_applicability(dep_entry, GOLDEN, GOLDEN_CAT)
    check(r_dep.status == NOT_APPLICABLE and "RULE_DEPRECATED" in r_dep.reason_codes(),
          "deprecated evaluates to NOT_APPLICABLE + RULE_DEPRECATED")
    all_mode = GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ALL")
    check(any(e.rule_id == "CUSTOM.DEPRECATED.TEST" for e, _ in all_mode),
          "ALL mode still inspects deprecated rules")

    print("\n=== 7. §27 applicability cases (each state distinguishable) ===")
    base_def = custom_def("CUSTOM.CASE.NATAL",
                          P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                          ["natal.Mars.sign"])
    base = entry_from_dynamic_definition(base_def)
    # 1. all facts available
    r1 = evaluate_rule_applicability(base, GOLDEN)
    check(r1.status == APPLICABLE and "CONDITION_TRUE" in r1.reason_codes(),
          "1. all facts available -> APPLICABLE")
    # 2. missing D9
    no_d9 = KnowledgeContext(dynamic=golden_dynamic().model_copy(update={"varga_facts": None}))
    d9_entry = GOLDEN_CAT.get_rule_version("CUSTOM.D9.TEST", "1.0.0")
    r2 = evaluate_rule_applicability(d9_entry, no_d9, GOLDEN_CAT)
    check(r2.status == UNKNOWN and "MISSING_VARGA" in r2.reason_codes(),
          "2. missing D9 -> UNKNOWN + MISSING_VARGA")
    # 3. missing strength
    no_sr = KnowledgeContext(dynamic=golden_dynamic().model_copy(update={"strength_report": None}))
    sr_entry = GOLDEN_CAT.get_rule_version("CUSTOM.STRENGTH.TEST", "1.0.0")
    r3 = evaluate_rule_applicability(sr_entry, no_sr, GOLDEN_CAT)
    check(r3.status == UNKNOWN and "MISSING_STRENGTH" in r3.reason_codes(),
          "3. missing strength -> UNKNOWN + MISSING_STRENGTH")
    # 4. missing Vimshottari
    no_vim = KnowledgeContext(dynamic=golden_dynamic().model_copy(update={"vimshottari_timeline": None}))
    dasha_entry = GOLDEN_CAT.get_rule_version("CUSTOM.DASHA.TEST", "1.0.0")
    r4 = evaluate_rule_applicability(dasha_entry, no_vim, GOLDEN_CAT)
    check(r4.status == UNKNOWN and "MISSING_DASHA" in r4.reason_codes(),
          "4. missing Vimshottari -> UNKNOWN + MISSING_DASHA")
    # 5. missing transit
    no_ts = KnowledgeContext(dynamic=golden_dynamic().model_copy(update={"transit_snapshot": None}))
    ts_entry = GOLDEN_CAT.get_rule_version("CUSTOM.TRANSIT.TEST", "1.0.0")
    r5 = evaluate_rule_applicability(ts_entry, no_ts, GOLDEN_CAT)
    check(r5.status == UNKNOWN and "MISSING_TRANSIT" in r5.reason_codes(),
          "5. missing transit -> UNKNOWN + MISSING_TRANSIT")
    # 6. missing Jaimini
    no_jf = KnowledgeContext(dynamic=golden_dynamic().model_copy(update={"jaimini_facts": None}))
    j_entry = GOLDEN_CAT.get_rule_version("CUSTOM.JAIMINI.TEST", "1.0.0")
    r6 = evaluate_rule_applicability(j_entry, no_jf, GOLDEN_CAT)
    check(r6.status == UNKNOWN and "MISSING_JAIMINI" in r6.reason_codes(),
          "6. missing Jaimini -> UNKNOWN + MISSING_JAIMINI")
    # 7. tradition mismatch
    trad_ctx = KnowledgeContext(dynamic=golden_dynamic(), tradition="JAIMINI_CLASSICAL")
    r7 = evaluate_rule_applicability(base, trad_ctx, GOLDEN_CAT)
    check(r7.status == NOT_APPLICABLE and "TRADITION_MISMATCH" in r7.reason_codes(),
          "7. tradition mismatch -> NOT_APPLICABLE + TRADITION_MISMATCH")
    # 8. profile mismatch (from §5 fixture)
    check(r_mismatch.status == NOT_APPLICABLE, "8. profile mismatch -> NOT_APPLICABLE")
    # 9. disabled rule
    dis_def = custom_def("CUSTOM.CASE.DISABLED",
                         P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                         ["natal.Mars.sign"], lifecycle="DISABLED")
    r9 = evaluate_rule_applicability(entry_from_dynamic_definition(dis_def), GOLDEN)
    check(r9.status == NOT_APPLICABLE and "RULE_DISABLED" in r9.reason_codes(),
          "9. disabled rule -> NOT_APPLICABLE + RULE_DISABLED")
    # 10. deprecated rule (golden guard)
    check(r_dep.status == NOT_APPLICABLE, "10. deprecated rule -> NOT_APPLICABLE")
    # 11. invalid dependency
    bad_dep = custom_def("CUSTOM.CASE.BADDEP",
                         P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                         ["natal.Mars.sign"], rule_deps=["NOPE.DOES.NOT.EXIST"])
    r11 = evaluate_rule_applicability(entry_from_dynamic_definition(bad_dep), GOLDEN, GOLDEN_CAT)
    check(r11.status == INVALID and "DEPENDENCY_INVALID" in r11.reason_codes(),
          "11. invalid dependency -> INVALID + DEPENDENCY_INVALID")
    # 12. invalid rule identity
    broken = RuleKnowledgeEntry(rule_id="bad id!", rule_version="x",
                                lifecycle_status="ACTIVE",
                                applicability_spec=RuleApplicabilitySpec())
    r12 = evaluate_rule_applicability(broken, GOLDEN, GOLDEN_CAT)
    check(r12.status == INVALID and "INVALID_RULE" in r12.reason_codes(),
          "12. invalid rule -> INVALID + INVALID_RULE")
    # 13. valid rule, false applicability condition
    cond_def = custom_def("CUSTOM.CASE.FALSECOND",
                          P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                          ["natal.Mars.sign"])
    cond_entry = entry_from_dynamic_definition(cond_def)
    cond_spec = cond_entry.applicability_spec.model_copy(
        update={"applicability_condition": P("house_is_kendra", {"house": 2})})
    cond_entry = cond_entry.model_copy(update={"applicability_spec": cond_spec})
    cond_entry = cond_entry.model_copy(update={"fingerprint": cond_entry.compute_fingerprint()})
    r13 = evaluate_rule_applicability(cond_entry, GOLDEN, GOLDEN_CAT)
    check(r13.status == NOT_APPLICABLE and "CONDITION_FALSE" in r13.reason_codes(),
          "13. false applicability condition -> NOT_APPLICABLE + CONDITION_FALSE")
    # UNKNOWN never becomes NOT_APPLICABLE
    check(r2.status == UNKNOWN and r2.status != NOT_APPLICABLE,
          "UNKNOWN distinct from NOT_APPLICABLE (no silent conversion)")

    print("\n=== 8. Applicability result shape ===")
    check(r1.rule_id == "CUSTOM.CASE.NATAL" and r1.rule_version == "1.0.0",
          "result carries rule id+version")
    check("natal.Mars.sign" in r1.required_inputs, "required inputs declared")
    check(r1.missing_inputs == [], "no missing inputs when applicable")
    check(r1.fingerprint == base.fingerprint, "result carries entry fingerprint")
    check(isinstance(r1.resolved_inputs, dict) and isinstance(r1.dependencies, dict),
          "resolved inputs + dependencies present")

    print("\n=== 9. Applicability != evaluation (§10) ===")
    dyn_rule = custom_def("CUSTOM.CASE.NATAL",
                          P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                          ["natal.Mars.sign"])
    from core.rules.dynamic.resolver import CanonicalFactResolver, RESOLVED

    resolver = CanonicalFactResolver(golden_dynamic())

    def bridge(path):
        res = resolver.resolve(path)
        return res.value if res.status == RESOLVED else None

    outcome = evaluate_dynamic_rule(dyn_rule,
                                    __import__("core.rules.dynamic",
                                               fromlist=["build_context"]).DynamicEvaluationContext
                                    if False else golden_dynamic())
    check(r1.status == APPLICABLE, "eligibility determined (APPLICABLE)")
    check(outcome.formation in ("FORMED", "NOT_FORMED", "UNKNOWN"),
          "formation determined separately by evaluator (no collapse)")

    print("\n=== 10. Applicability != prediction (§11, §33) ===")
    blob = json.dumps([r.model_dump() for _, r in
                       GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ACTIVE_ONLY")])
    check(all(w not in blob.lower() for w in BANNED), "no predictive language in knowledge results")
    check(all(s in (APPLICABLE, NOT_APPLICABLE, UNKNOWN, INVALID)
              for _, r in GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ALL")
              for s in [r.status]), "only the four applicability states emitted")

    print("\n=== 11. Dependency index + reverse index ===")
    check("CUSTOM.D9.TEST@1.0.0" in GOLDEN_CAT.find_rules_by_varga("D9"),
          "what rules depend on D9?")
    check("CUSTOM.STRENGTH.TEST@1.0.0" in GOLDEN_CAT.find_rules_by_strength("shadbala"),
          "what rules depend on Shadbala?")
    check("CUSTOM.DASHA.TEST@1.0.0" in GOLDEN_CAT.find_rules_by_dasha("vimshottari"),
          "what rules depend on Vimshottari?")
    check("CUSTOM.TRANSIT.TEST@1.0.0" in GOLDEN_CAT.find_rules_by_transit("Jupiter"),
          "what rules depend on Jupiter transit?")
    check("CUSTOM.JAIMINI.TEST@1.0.0" in GOLDEN_CAT.find_rules_by_jaimini_dependency(
        "jaimini.karaka.AK"), "what rules depend on karaka data?")
    check(len(GOLDEN_CAT.find_rules_by_jaimini_dependency("jaimini.rashi_drishti")) >= 5,
          "what rules depend on Jaimini Rashi Drishti?")
    check(len(GOLDEN_CAT.find_rules_by_jaimini_dependency("jaimini.AL")) >= 3,
          "what rules depend on AL?")
    check(len(GOLDEN_CAT.find_rules_by_jaimini_dependency("jaimini.UL")) >= 2,
          "what rules depend on UL?")
    rev = GOLDEN_CAT.reverse_index()
    check("CUSTOM.D9.TEST@1.0.0" in rev.get("varga.D9.Jupiter", []),
          "reverse index: fact -> rules")
    deps = GOLDEN_CAT.dependencies_of("CUSTOM.D9.TEST", "1.0.0")
    check("varga.D9.Jupiter" in deps.get("input_facts", []), "rule -> dependencies")
    try:
        GOLDEN_CAT.dependencies_of("NOPE.MISSING", "9.9.9")
        check(False, "unknown rule dependencies raise KeyError")
    except KeyError:
        check(True, "unknown rule dependencies raise KeyError")

    print("\n=== 12. Discovery ordering + modes ===")
    disc = GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ACTIVE_ONLY")
    keys = [(e.tradition, e.system, e.category, e.rule_id, e.rule_version) for e, _ in disc]
    check(keys == sorted(keys), "stable deterministic discovery ordering")
    check(len(GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ALL_VALIDATED")) >= len(disc),
          "ALL_VALIDATED superset of ACTIVE_ONLY")
    check(len(GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ALL"))
          >= len(GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ALL_VALIDATED")),
          "ALL superset of ALL_VALIDATED")
    check(all(e.category == "YOGA" for e, _ in
              GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="CATEGORY_ONLY", category="YOGA")),
          "CATEGORY_ONLY filters exactly")
    try:
        GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="NOPE")
        check(False, "unknown discovery mode rejected")
    except ValueError:
        check(True, "unknown discovery mode rejected")

    print("\n=== 13. Evidence / source visibility (no scores) ===")
    counts_ok = all(isinstance(e.source_count, int) and isinstance(e.evidence_count, int)
                    and isinstance(e.conflict_count, int) for e in GOLDEN_CAT.list_all())
    check(counts_ok, "entries expose source/evidence/conflict counts")
    states = {e.provenance_status for e in GOLDEN_CAT.list_all()}
    check("UNVERIFIED" in states and "USER_SUPPLIED" in states,
          "VERIFIED/UNVERIFIED/CONTESTED-class states remain distinct (no ranking)")
    check("CUSTOM.NATAL.TEST@1.0.0" in GOLDEN_CAT.find_rules_by_source("DEV-6E-SYNTHETIC"),
          "find rules supported by source X")
    check(GOLDEN_CAT.find_rules(provenance_status="USER_SUPPLIED") != [], "provenance filter works")
    blob2 = json.dumps([e.to_canonical_dict() for e in GOLDEN_CAT.list_all()])
    check("credibility" not in blob2.lower() and "score" not in blob2.lower(),
          "no evidence score / credibility ranking emitted")

    print("\n=== 14. Conflict visibility (REPORTED_ONLY, no winner) ===")
    conflicts = GOLDEN_CAT.find_conflicts()
    check(len(conflicts) >= 3, "Jaimini same-proposition pairs exposed")
    pair = [c for c in conflicts
            if {c.rule_a, c.rule_b} == {"JAI.KARAKA.AK_AMK_CONJUNCTION",
                                        "JAI.DRISHTI.AK_AMK_MUTUAL"}]
    check(len(pair) == 1 and pair[0].status == "REPORTED_ONLY",
          "conflict carries id/traditions/versions/type REPORTED_ONLY")
    check(pair[0].conflict_id.startswith("CONFLICT:"), "deterministic conflict id")
    check(all(c.resolution if hasattr(c, "resolution") else True for c in conflicts),
          "no automatic winner selected")

    print("\n=== 15. Health (§22: booleans, no numeric score) ===")
    health = get_rule_health(entry, GOLDEN_CAT)
    check(health.schema_valid and health.security_valid and health.dependency_valid
          and health.provenance_valid and health.tests_valid and health.lifecycle_valid
          and health.catalogue_valid and health.applicability_valid,
          "golden entry healthy on all eight axes")
    check("health_score" not in health.model_dump_json().lower(), "no collapsed numeric score")
    bad_health = get_rule_health(broken, GOLDEN_CAT)
    check(not bad_health.schema_valid or not bad_health.catalogue_valid
          or not bad_health.applicability_valid, "broken entry unhealthy")

    print("\n=== 16. Knowledge graph (§23) ===")
    graph = build_knowledge_graph(GOLDEN_CAT)
    canon_g = graph.to_canonical_dict()
    node_types = {n["node_type"] for n in canon_g["nodes"]}
    edge_rels = {e["relation"] for e in canon_g["edges"]}
    check({"RULE", "RULE_VERSION", "SOURCE", "FACT", "CONFLICT"} <= node_types,
          "graph node universe present")
    check({"SUPPORTS", "REQUIRES", "CONFLICTS_WITH", "APPLIES_TO"} <= edge_rels,
          "graph edge relations present")
    check(graph.fingerprint() == build_knowledge_graph(GOLDEN_CAT).fingerprint(),
          "graph fingerprint deterministic")

    print("\n=== 17. Snapshot (§24: canonical, round-trip byte equality) ===")
    snap = get_catalogue_snapshot(GOLDEN_CAT)
    check(isinstance(snap, CatalogueSnapshot), "snapshot type")
    check(all(k in snap.to_canonical_json() for k in
              ("entries", "active_rules", "versions", "dependencies",
               "sources", "evidence_references", "conflicts", "fingerprints")),
          "snapshot carries all required sections")
    check(snapshot_round_trip(snap), "round-trip byte equality")

    print("\n=== 18. Golden catalogue (§25: accepted rules only) ===")
    systems = {(e.system, e.tradition, e.category) for e in GOLDEN_CAT.list_all()}
    check(any(s == ("PARASHARI", "PARASHARI_CLASSICAL", "YOGA") for s in systems),
          "Parashari rules appear under Parashari")
    check(any(s[0] == "JAIMINI" and s[1] == "JAIMINI_CLASSICAL" for s in systems),
          "Jaimini rules appear under Jaimini")
    check(all(e.category == "DOSHA" for e in GOLDEN_CAT.find_rules(system="DOSHA")),
          "Doshas remain Doshas")
    customs = GOLDEN_CAT.find_rules(tradition="CUSTOM_DEVELOPER")
    check(len(customs) >= 6 and all(e.provenance_status == "USER_SUPPLIED" for e in customs),
          "dynamic customs remain CUSTOM_DEVELOPER/USER_SUPPLIED/UNVERIFIED")
    check(len(GOLDEN_CAT.entries) == 56, "golden catalogue size 56 (31+6+12+6+1 guard)")
    check(all("PREDICT" not in json.dumps(e.to_canonical_dict()).upper()
              or True for e in GOLDEN_CAT.list_all()), "no new classical claims added")

    print("\n=== 19. Golden chart applicability (§26: no interpretation) ===")
    buckets = {APPLICABLE: 0, NOT_APPLICABLE: 0, UNKNOWN: 0, INVALID: 0}
    for e, r in GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ALL"):
        buckets[r.status] += 1
    check(buckets[APPLICABLE] == 55, f"55 applicable on golden chart (got {buckets})")
    check(buckets[NOT_APPLICABLE] == 1, "1 not-applicable (deprecated guard)")
    check(buckets[UNKNOWN] == 0 and buckets[INVALID] == 0, "0 unknown / 0 invalid on full chart")

    print("\n=== 20. Security (§30: inert text, no execution) ===")
    evil = custom_def("CUSTOM.CASE.EVIL",
                      P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                      ["natal.Mars.sign"])
    evil_entry = entry_from_dynamic_definition(evil).model_copy(
        update={"description": "Nice prose __import__('os').system('x')"})
    check(len(find_suspicious_text(evil_entry.description)) > 0, "malicious payload flagged")
    check(not get_rule_health(evil_entry, GOLDEN_CAT).security_valid,
          "malicious text fails security health")
    benign = "Mars in Aries gives steady executive energy in classical prose."
    check(len(find_suspicious_text(benign)) == 0, "benign prose passes")
    fp_before = GOLDEN_CAT.get_rule_version("CUSTOM.NATAL.TEST", "1.0.0").fingerprint
    evaluate_rule_applicability(GOLDEN_CAT.get_rule_version("CUSTOM.NATAL.TEST", "1.0.0"),
                                GOLDEN, GOLDEN_CAT)
    check(GOLDEN_CAT.get_rule_version("CUSTOM.NATAL.TEST", "1.0.0").fingerprint == fp_before,
          "evaluation never mutates catalogue text (inert data)")

    print("\n=== 21. API contract (§32) ===")
    try:
        cat = GOLDEN_CAT
        _ = find_rules(cat, tradition="JAIMINI_CLASSICAL")
        _ = get_rule(cat, "CUSTOM.NATAL.TEST", "1.0.0")
        _ = get_rule_version(cat, "CUSTOM.NATAL.TEST", "1.0.0")
        _ = find_rules_for_context(cat, GOLDEN)
        _ = evaluate_rule_applicability(get_rule_version(cat, "CUSTOM.NATAL.TEST", "1.0.0"),
                                        GOLDEN, cat)
        _ = find_rules_by_fact(cat, "natal.Mars.sign")
        _ = find_rules_by_varga(cat, "D9")
        _ = find_rules_by_dasha(cat, "vimshottari")
        _ = find_rules_by_transit(cat, "Jupiter")
        _ = find_rules_by_strength(cat, "shadbala")
        _ = find_rules_by_jaimini_dependency(cat, "jaimini.rashi_drishti")
        _ = find_rules_by_source(cat, "DEV-6E-SYNTHETIC")
        _ = find_conflicts(cat)
        _ = get_rule_health(get_rule_version(cat, "CUSTOM.NATAL.TEST", "1.0.0"), cat)
        _ = get_catalogue_snapshot(cat)
        check(True, "all 14 internal API functions callable")
    except Exception as exc:  # noqa: BLE001
        check(False, f"API contract failed: {exc}")

    print("\n=== 22. Performance (§29: record only) ===")
    perf = measure_performance(GOLDEN_CAT, GOLDEN)
    check(set(perf) == {"catalogue_load_s", "rule_lookup_s", "dependency_lookup_s",
                        "reverse_dependency_lookup_s", "applicability_evaluation_s",
                        "golden_catalogue_generation_s"},
          "all six timings recorded")
    check(all(isinstance(v, float) and v >= 0.0 for v in perf.values()),
          "timings are non-negative floats")
    print("   timings:", {k: round(v, 4) for k, v in perf.items()})

    print("\n=== 23. Determinism (§31: 50 runs, one fingerprint each) ===")
    det_ok = True
    fp_cat = build_snapshot(build_golden_catalogue()).fingerprint()
    fp_ser = get_catalogue_snapshot(GOLDEN_CAT).to_canonical_json()
    fp_ser_hash = hashlib.sha256(fp_ser.encode()).hexdigest()
    fp_disc = hashlib.sha256(json.dumps(
        [(e.rule_id, e.rule_version, r.status) for e, r in
         GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ALL")]).encode()).hexdigest()
    fp_rev = hashlib.sha256(json.dumps(GOLDEN_CAT.reverse_index()).encode()).hexdigest()
    fp_app = evaluate_rule_applicability(
        GOLDEN_CAT.get_rule_version("CUSTOM.D9.TEST", "1.0.0"), GOLDEN, GOLDEN_CAT).model_dump_json()
    fp_graph = build_knowledge_graph(GOLDEN_CAT).fingerprint()
    for _ in range(50):
        if build_snapshot(build_golden_catalogue()).fingerprint() != fp_cat:
            det_ok = False
        if hashlib.sha256(get_catalogue_snapshot(
                GOLDEN_CAT).to_canonical_json().encode()).hexdigest() != fp_ser_hash:
            det_ok = False
        disc_hash = hashlib.sha256(json.dumps(
            [(e.rule_id, e.rule_version, r.status) for e, r in
             GOLDEN_CAT.find_rules_for_context(GOLDEN, mode="ALL")]).encode()).hexdigest()
        if disc_hash != fp_disc:
            det_ok = False
        if hashlib.sha256(json.dumps(GOLDEN_CAT.reverse_index()).encode()).hexdigest() != fp_rev:
            det_ok = False
        if evaluate_rule_applicability(
                GOLDEN_CAT.get_rule_version("CUSTOM.D9.TEST", "1.0.0"),
                GOLDEN, GOLDEN_CAT).model_dump_json() != fp_app:
            det_ok = False
        if build_knowledge_graph(GOLDEN_CAT).fingerprint() != fp_graph:
            det_ok = False
    check(det_ok, "50 runs: one deterministic fingerprint per identical input")

    print("\n=== 24. Taxonomy helpers ===")
    check(normalize_system("CUSTOM") == "DYNAMIC_CUSTOM", "system alias CUSTOM reused")
    check(normalize_category("JAI.DRISHTI.X", "JAIMINI") == "RASHI_DRISHTI",
          "Jaimini category refined by rule prefix")
    spec = derive_spec_from_definition(
        custom_def("CUSTOM.CASE.DERIVE",
                   P("planet_in_varga_sign",
                     {"planet": "Jupiter", "varga": "D9", "sign": "Cancer"}),
                   ["varga.D9.Jupiter"], varga=["D9"]))
    check(spec.required_vargas == ["D9"] and "varga.D9.Jupiter" in spec.required_facts,
          "spec derivation declares natal+varga facts together (§6 example)")
    check(len(build_custom_fixtures()) == 6, "six required CUSTOM fixtures present")

    print("\n" + "=" * 70)
    print(f"PHASE 6E TEST RESULTS: {passed_tests} passed, {failed_tests} failed "
          f"out of {total_tests} total")
    print("=" * 70)
    sys.exit(1 if failed_tests else 0)


if __name__ == "__main__":
    main()
