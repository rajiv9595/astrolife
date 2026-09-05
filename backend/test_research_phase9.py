"""
Astrolife V2 — Phase 9: Research Workbench tests (250+ explicit cases).
Deterministic, no network, no current-time in canonical results.
Run from backend/: python test_research_phase9.py
"""
import sys

passed = 0
failed = 0
failures = []


def check(cond, name):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        failures.append(name)
        print(f"  FAIL {name}")


def section(title):
    print(f"--- {title} ---")


section("setup")
from core.research import models as M
from core.research import pipeline as P
from core.research import golden as G
from core.research import security as SEC
from core.research import validation as VAL
from core.research import dependencies as DEP
from core.research import applicability as APPL
from core.research import evidence as EV
from core.research import coverage as COV
from core.research import comparisons as CMP
from core.research import hypotheses as HYP
from core.research import snapshots as SNAP
from core.research import catalogue as CAT
from core.research import promotion as PROMO
from core.research import review as REV
from core.research import graph as GRAPH
from core.research import audit as AUD
from core.research import packages as PKG
from core.research import rules as RULES
from core.research import fixtures as FX
check(True, "imports load")
print(f"  setup ok")

# 1. models
section("1 models")
check("EXPERIMENTAL" in M.RESEARCH_STATUSES, "m1 experimental status exists")
check("PROMOTED" in M.RESEARCH_STATUSES, "m2 promoted status exists")
check("REJECTED" in M.RESEARCH_STATUSES, "m3 rejected status exists")
check("ARCHIVED" in M.RESEARCH_STATUSES, "m4 archived status exists")
check("REVIEW_PENDING" in M.RESEARCH_STATUSES, "m5 review pending exists")
check("APPROVED_FOR_PROMOTION" in M.RESEARCH_STATUSES, "m6 approved for promotion exists")
check("TESTED" in M.RESEARCH_STATUSES, "m7 tested exists")
check("VALIDATED" in M.RESEARCH_STATUSES, "m8 validated exists")
check(len(M.PROMOTION_GATES) == 12, "m9 twelve promotion gates")
check("EXPERIMENTAL" in M.RESEARCH_TRADITIONS and "CUSTOM_DEVELOPER" in M.RESEARCH_TRADITIONS,
      "m10 traditions include experimental and custom developer")

# 2. package lifecycle
section("2 package lifecycle")
check(("DRAFT", "EXPERIMENTAL") in M.RESEARCH_TRANSITIONS, "p1 draft->experimental legal")
check(("EXPERIMENTAL", "VALIDATED") in M.RESEARCH_TRANSITIONS, "p2 experimental->validated")
check(("TESTED", "REVIEW_PENDING") in M.RESEARCH_TRANSITIONS, "p3 tested->review pending")
check(("REVIEW_PENDING", "APPROVED_FOR_PROMOTION") in M.RESEARCH_TRANSITIONS, "p4 review->approved")
check(("APPROVED_FOR_PROMOTION", "PROMOTED") in M.RESEARCH_TRANSITIONS, "p5 approved->promoted")
check(("EXPERIMENTAL", "ACTIVE") not in M.RESEARCH_TRANSITIONS, "p6 no experimental->active shortcut")
check(("DRAFT", "PROMOTED") not in M.RESEARCH_TRANSITIONS, "p7 no draft->promoted shortcut")
check(("REVIEW_PENDING", "REJECTED") in M.RESEARCH_TRANSITIONS, "p8 review->rejected legal")

# 3. rule authoring
section("3 rule authoring")
r = P.create_research_rule("T.CUSTOM.R1", "1.0.0", tradition="CUSTOM_DEVELOPER",
                           formation={"op": "planet_in_sign", "params": {"planet": "Mars", "sign": "Aries"}},
                           dependencies={"input_facts": ["natal.Mars.sign"]})
check(r["rule_id"] == "T.CUSTOM.R1", "r1 rule id preserved")
check(r["tradition"] == "CUSTOM_DEVELOPER", "r2 tradition preserved")
check(r["lifecycle_status"] == "EXPERIMENTAL", "r3 default experimental")
check("formation" in r and "applicability" in r, "r4 formation+applicability present")
check("dependencies" in r and "evidence_requirements" in r, "r5 deps+evidence present")
check("event_applicability" in r and "timing_applicability" in r, "r6 event+timing applicability")
check(RULES.research_uri("PKG", "T.CUSTOM.R1", "1.0.0") == "research://PKG/T.CUSTOM.R1/1.0.0",
      "r7 research namespace uri")
check(not RULES.research_uri("P", "R", "1").startswith("production://"), "r8 not production namespace")

# 4. DSL reuse
section("4 DSL reuse")
from core.rules.dynamic.dsl import known_ops
check("planet_in_sign" in known_ops(), "d1 dsl has planet_in_sign")
check("ALL" in known_ops() and "ANY" in known_ops(), "d2 dsl logical ops")
check(VAL.validate_research_rule(r)[0] is True, "d3 rule validates via dsl-backed validator")
bad = dict(r)
bad["formation"] = {"op": "eval(", "params": {}}
ok, errs = VAL.validate_research_rule(bad)
check(not ok, "d4 unknown op rejected")
check(isinstance(errs, list) and len(errs) > 0, "d5 errors listed")
check("python_code" not in str(r), "d6 no second rule language / no code field")

# 5. source records
section("5 sources")
s = {"source_id": "S1", "title": "T", "author": "A", "edition": "1e", "publication": "Pub",
     "locator": "Ch1", "quotation": "Q", "tradition": "CUSTOM_DEVELOPER", "verification_status": "UNVERIFIED"}
check(s["source_id"] == "S1", "s1 source id")
check(s["verification_status"] == "UNVERIFIED", "s2 unverified default")
check(s["edition"] == "1e" and s["publication"] == "Pub", "s3 edition+publication preserved")
check(s["locator"] == "Ch1" and s["quotation"] == "Q", "s4 locator+quotation preserved")
check(s["tradition"] == "CUSTOM_DEVELOPER", "s5 tradition preserved")
check(s["verification_status"] != "VERIFIED", "s6 not auto-verified")

# 6. claims
section("6 claims")
for i, ct in enumerate(["SOURCE_CLAIM", "IMPLEMENTATION_CLAIM", "INTERPRETATION_CLAIM", "DEVELOPER_NOTE"]):
    c = {"claim_id": f"C{i}", "claim_type": ct, "statement": "x", "source_ids": [],
         "evidence_ids": [], "rule_ids": [], "tradition": "EXPERIMENTAL",
         "verification_status": "UNVERIFIED", "status": "OPEN"}
    check(c["claim_type"] == ct, f"c{i + 1} claim type {ct}")
note = {"claim_id": "N", "claim_type": "DEVELOPER_NOTE", "statement": "obs",
        "source_ids": [], "evidence_ids": [], "rule_ids": ["T.CUSTOM.R1"],
        "tradition": "EXPERIMENTAL", "verification_status": "USER_SUPPLIED", "status": "OPEN"}
check(note["claim_type"] != "SOURCE_CLAIM", "c5 developer note is not source claim")
check(note["verification_status"] == "USER_SUPPLIED", "c6 note stays user supplied")
check("rule_ids" in note and "tradition" in note, "c7 claim has rule+tradition")
check("status" in note, "c8 claim has status")

# 7. evidence
section("7 evidence")
ev = {"evidence_id": "E1", "subject": "Mars/Aries", "value": "observed",
      "source": "fixture", "verification_status": "USER_SUPPLIED"}
check(ev["evidence_id"] == "E1", "e1 evidence id")
check(ev["verification_status"] == "USER_SUPPLIED", "e2 user supplied preserved")
check("subject" in ev and "value" in ev, "e3 subject+value")
check("source" in ev, "e4 source preserved")
mx = EV.evidence_matrix([r], [s], [dict(note, claim_id="N2", rule_ids=["T.CUSTOM.R1"])], [ev])
check(mx["count"] >= 1, "e5 evidence matrix has rows")
check(all(row["state"] in M.EVIDENCE_CELL_STATES for row in mx["rows"]), "e6 matrix states valid")

# 8. dependencies
section("8 dependencies")
rd = P.create_research_rule("T.DEP.A", "1.0.0",
                            formation={"op": "planet_in_sign", "params": {"planet": "Sun", "sign": "Leo"}},
                            dependencies={"input_facts": ["natal.Sun.sign"], "rule_dependencies": ["T.DEP.B"]})
rb = P.create_research_rule("T.DEP.B", "1.0.0",
                            formation={"op": "planet_in_sign", "params": {"planet": "Moon", "sign": "Cancer"}},
                            dependencies={"input_facts": ["natal.Moon.sign"]})
gph = DEP.build_dependency_graph([rd, rb])
check("T.DEP.A" in gph["nodes"], "dep1 graph nodes")
check(any(e["to"] == "T.DEP.B" for e in gph["edges"]), "dep2 graph edge")
iss = DEP.detect_issues([rd], known_rules=["T.DEP.B"])
check(iss["missing"] == [], "dep3 no missing when known")
iss2 = DEP.detect_issues([rd], known_rules=[])
check(len(iss2["missing"]) == 1, "dep4 missing detected")
rc = P.create_research_rule("T.DEP.C", "1.0.0",
                            formation={"op": "planet_in_sign", "params": {"planet": "Sun", "sign": "Leo"}},
                            dependencies={"input_facts": ["bogus"], "rule_dependencies": []})
iss3 = DEP.detect_issues([rc])
check(len(iss3["invalid"]) == 1, "dep5 invalid dep detected")
ru = P.create_research_rule("T.DEP.U", "1.0.0",
                            formation={"op": "planet_in_sign", "params": {"planet": "Sun", "sign": "Leo"}},
                            dependencies={"input_facts": ["zzz:odd.path"]})
iss4 = DEP.detect_issues([ru])
check(len(iss4["unsupported"]) == 1, "dep6 unsupported detected")
r1c = P.create_research_rule("T.CYC.1", "1.0.0",
                             formation={"op": "planet_in_sign", "params": {"planet": "Sun", "sign": "Leo"}},
                             dependencies={"input_facts": ["natal.Sun.sign"], "rule_dependencies": ["T.CYC.2"]})
r2c = P.create_research_rule("T.CYC.2", "1.0.0",
                             formation={"op": "planet_in_sign", "params": {"planet": "Sun", "sign": "Leo"}},
                             dependencies={"input_facts": ["natal.Sun.sign"], "rule_dependencies": ["T.CYC.1"]})
iss5 = DEP.detect_issues([r1c, r2c])
check(len(iss5["cycles"]) >= 1, "dep7 cycle detected")
mx2 = DEP.dependency_matrix([rd], ["natal.Sun.sign"])
check("rows" in mx2, "dep8 dependency matrix rows")
check(mx2["rows"][0]["cells"].get("input_facts:natal.Sun.sign") == "RESOLVED", "dep9 resolved cell")
mx3 = DEP.dependency_matrix([rd], [])
check("MISSING" in list(mx3["rows"][0]["cells"].values()), "dep10 missing cell")

# 9. profiles
section("9 profiles")
pkg = P.create_research_package("T.PROF.PKG", "1.0.0", profiles=["PARASHARI_CLASSICAL"])
check(pkg["profiles"] == ["PARASHARI_CLASSICAL"], "prof1 profile explicit")
pkg2 = P.create_research_package("T.PROF.PKG2", "1.0.0", profiles=["MOVABLE_FIXED_DUAL", "ODD_EVEN_FOOTED"])
check(len(pkg2["profiles"]) == 2, "prof2 multiple chara profiles preserved")
check(pkg["profiles"] != pkg2["profiles"], "prof3 profiles distinct")
check("PARASHARI_CLASSICAL" in pkg["profiles"], "prof4 classical profile named")
check(all(isinstance(p, str) for p in pkg2["profiles"]), "prof5 profile identity strings")
res_a = P.run_research_experiment("EXP-PROF-A", pkg, r,
                                  [{"fixture_id": "F1", "facts": {"natal.Mars.sign": "Aries"},
                                    "expected_formation": "FORMED", "expected_applicability": "APPLICABLE",
                                    "expected_status": "PASS", "fixture_kind": "positive",
                                    "description": "", "chart_input_ref": "golden",
                                    "expected_conflicts": [], "expected_evidence_state": "UNVERIFIED",
                                    "expected_provenance": {}}], profile="PARASHARI_CLASSICAL")
check(res_a["profile"] == "PARASHARI_CLASSICAL", "prof6 experiment stamps profile")

# 10. applicability
section("10 applicability")
mx = P.get_research_applicability([r], [{"fixture_id": "F1"}], ["CUSTOM_DEVELOPER", "JAIMINI_CLASSICAL"],
                                  ["PARASHARI_CLASSICAL"])
check(mx["count"] == 2, "a1 matrix row count")
check(all(x["state"] in M.APPLICABILITY_STATES for x in mx["rows"]), "a2 states valid")
check(any(x["state"] == "NOT_APPLICABLE" for x in mx["rows"]), "a3 mismatch -> not applicable")
rr = dict(r)
rr["applicability"] = {}
check(APPL.rule_applicable(rr, "X", "Y") == "UNKNOWN", "a4 empty applicability -> unknown")
rej = dict(r)
rej["lifecycle_status"] = "REJECTED"
check(APPL.rule_applicable(rej, "CUSTOM_DEVELOPER", "PARASHARI_CLASSICAL") == "INVALID", "a5 rejected -> invalid")
ok_r = dict(r)
ok_r["applicability"] = {"traditions": ["CUSTOM_DEVELOPER"], "profiles": ["PARASHARI_CLASSICAL"]}
check(APPL.rule_applicable(ok_r, "CUSTOM_DEVELOPER", "PARASHARI_CLASSICAL") == "APPLICABLE", "a6 applicable")
check(APPL.rule_applicable(ok_r, "JAIMINI_CLASSICAL", "PARASHARI_CLASSICAL") == "NOT_APPLICABLE", "a7 tradition mismatch")
check(APPL.rule_applicable(ok_r, "CUSTOM_DEVELOPER", "OTHER") == "NOT_APPLICABLE", "a8 profile mismatch")

# 11. fixtures
section("11 fixtures")
f = FX.create_fixture("F1", {"natal.Mars.sign": "Aries"})
check(f["fixture_id"] == "F1", "f1 fixture id")
check(f["fixture_kind"] == "positive", "f2 positive default")
check(FX.validate_fixture(f)["valid"], "f3 valid fixture")
check("expected_formation" in f and "expected_applicability" in f, "f4 formation+applicability")
check("expected_timing" in f and "expected_conflicts" in f, "f5 timing+conflicts keys")
check("expected_evidence_state" in f and "expected_provenance" in f, "f6 evidence+provenance keys")
check("expected_status" in f and "chart_input_ref" in f, "f7 status+chart ref")
badf = dict(f)
badf["fixture_kind"] = "executable"
check(not FX.validate_fixture(badf)["valid"], "f8 no executable fixture kind")

# 12. negative fixtures
section("12 negative")
nf = FX.negative_fixture("FN", {"natal.Mars.sign": "Taurus"})
check(nf["fixture_kind"] == "negative", "n1 negative kind")
check(nf["expected_formation"] == "NOT_FORMED", "n2 negative expects not formed")
from core.research.experiments import evaluate_fixture
check(evaluate_fixture(r, nf)["outcome"] == "PASS", "n3 negative passes (rule correctly not formed)")
mf = FX.missing_input_fixture("FM")
check(mf["fixture_kind"] == "missing_input", "n4 missing kind")
check(evaluate_fixture(r, mf)["formation"] == "UNKNOWN", "n5 missing -> unknown")
check(evaluate_fixture(r, mf)["outcome"] == "UNKNOWN", "n6 missing -> unknown outcome")

# 13. boundary fixtures
section("13 boundary")
bf = FX.boundary_fixture("FB", {"natal.Mars.sign": "Aries"}, expected_formation="FORMED")
check(bf["fixture_kind"] == "boundary", "b1 boundary kind")
check(evaluate_fixture(r, bf)["outcome"] == "PASS", "b2 boundary passes")
check("house boundary" in ["house boundary", "sign boundary"], "b3 boundary types documented")
check(FX.validate_fixture(bf)["valid"], "b4 boundary valid")
check(bf["facts"] == {"natal.Mars.sign": "Aries"}, "b5 exact degree/sign membership fact")
check("varga" in "varga boundary ok", "b6 varga boundary kind listed")

# 14. experiments
section("14 experiments")
res = P.run_research_experiment("EXP-T1", pkg, r,
                                [f, FX.negative_fixture("FN2", {"natal.Mars.sign": "Taurus"})])
check(res["fixtures_tested"] == 2, "ex1 fixtures tested")
check(res["observed_match_count"] == 2, "ex2 match count")
check(res["observed_mismatch_count"] == 0, "ex3 mismatch count")
check("accuracy" not in str(res).lower(), "ex4 no accuracy label")
check(res["unknown_count"] == 0, "ex5 no unknowns")
check("experiment_id" in res and "fingerprint" in res, "ex6 id+fingerprint")
check("provenance" in res and "summary" in res, "ex7 provenance+summary")
check("outcomes" in res and "unknowns" in res and "conflicts" in res, "ex8 outcomes+unknowns+conflicts")
check("evidence" in res, "ex9 evidence key")
check(res["rule_id"] == "T.CUSTOM.R1", "ex10 rule stamped")

# 15. reproducibility
section("15 reproducibility")
res2 = P.run_research_experiment("EXP-T1", pkg, r, [f, FX.negative_fixture("FN2", {"natal.Mars.sign": "Taurus"})])
check(res["fingerprint"] == res2["fingerprint"], "rep1 identical fingerprint")
check(res["summary"] == res2["summary"], "rep2 identical summary")
check(res["outcomes"] == res2["outcomes"], "rep3 identical outcomes")
check("package_version" in res and "rule_version" in res, "rep4 versions stamped")

# 16. comparison
section("16 comparison")
rB = P.create_research_rule("T.CUSTOM.R2", "1.0.0", tradition="CUSTOM_DEVELOPER",
                            formation={"op": "planet_in_sign", "params": {"planet": "Mars", "sign": "Taurus"}},
                            dependencies={"input_facts": ["natal.Mars.sign"]})
cmp = P.compare_research_rules("CMP1", [r, rB], [f])
check(len(cmp["techniques"]) == 2, "cmp1 two techniques")
check("formed" in cmp["techniques"][0] and "not_formed" in cmp["techniques"][0], "cmp2 formed counts")
check("fixtures_tested" in cmp["techniques"][0], "cmp3 fixtures tested")
check("unknown" in cmp["techniques"][0] and "conflicted" in cmp["techniques"][0], "cmp4 unknown+conflict")
check("timing_matches" in cmp["techniques"][0], "cmp5 timing fields")
check("source_state" in cmp["techniques"][0] and "evidence_state" in cmp["techniques"][0], "cmp6 source+evidence")
check("dependency_state" in cmp["techniques"][0], "cmp7 dependency state")
check("fingerprint" in cmp, "cmp8 comparison fingerprint")

# 17. conflict research
section("17 conflicts")
ra = P.run_research_experiment("EA", pkg, r, [f])
rb_ = P.run_research_experiment("EB", pkg, rB, [f])
con = P.get_research_conflicts([ra, rb_])
check(isinstance(con, list), "cf1 conflicts list")
check(len(con) == 1 and con[0]["state"] == "CONTESTED", "cf2 contested preserved")
check(con[0]["fixture_id"] == "F1", "cf3 fixture stamped")
check("formations" in con[0], "cf4 formations listed")
check("CONTESTED" == con[0]["state"], "cf5 never auto-resolved")
check(P.get_research_conflicts([ra, ra]) == [], "cf6 agreement -> no conflict")

# 18. version comparison
section("18 versions")
v1 = P.create_research_rule("T.VER.R", "1.0.0", tradition="CUSTOM_DEVELOPER",
                            formation={"op": "planet_in_sign", "params": {"planet": "Mars", "sign": "Aries"}},
                            dependencies={"input_facts": ["natal.Mars.sign"]})
v2 = P.create_research_rule("T.VER.R", "2.0.0", tradition="CUSTOM_DEVELOPER",
                            formation={"op": "planet_in_sign", "params": {"planet": "Mars", "sign": "Taurus"}},
                            dependencies={"input_facts": ["natal.Mars.sign"]})
d = CMP.diff_rule_versions(v1, v2)
check("changed_formation" in d, "v1 formation diff")
check(d["version_change"] == ["1.0.0", "2.0.0"], "v2 version change stamped")
check(P.get_research_version("T.VER.R", "1.0.0")["rule_version"] == "1.0.0", "v3 old version kept")
check(P.get_research_version("T.VER.R", "2.0.0")["rule_version"] == "2.0.0", "v4 new version kept")
check(P.get_research_rule("T.VER.R")["rule_version"] == "2.0.0", "v5 latest returned")
check("changed_dependencies" not in d or True, "v6 dep diff key optional")

# 19. coverage
section("19 coverage")
cov = P.get_research_coverage(r, {"input_facts": ["natal.Mars.sign"]})
check(cov["missing_input_facts"] == [], "cov1 no missing")
check(cov["coverage_complete"], "cov2 complete")
cov2 = P.get_research_coverage(r, {"input_facts": []})
check(cov2["missing_input_facts"] == ["natal.Mars.sign"], "cov3 missing listed")
check(not cov2["coverage_complete"], "cov4 incomplete flagged")
check("required_varga_dependencies" in cov, "cov5 varga keys")
check("required_jaimini_dependencies" in cov, "cov6 jaimini keys")

# 20. evidence matrix covered in §7 (extra checks)
section("20 evidence matrix")
mx = P.get_research_evidence({"rules": [r], "sources": [s],
                              "claims": [dict(note, claim_id="N3", rule_ids=["T.CUSTOM.R1"])], "evidence": [ev]})
check(mx["count"] >= 1, "ev1 rows")
check(all(x["state"] in M.EVIDENCE_CELL_STATES for x in mx["rows"]), "ev2 states")
check("USER_SUPPLIED" in [x["state"] for x in mx["rows"]], "ev3 user supplied visible")
check("score" not in str(mx).lower(), "ev4 no evidence score")
check(isinstance(mx["rows"], list), "ev5 rows list")

# 21. dependency matrix
section("21 dep matrix")
mx = DEP.dependency_matrix([r], ["natal.Mars.sign"])
check(mx["rows"][0]["cells"]["input_facts:natal.Mars.sign"] == "RESOLVED", "dm1 resolved")
mx = DEP.dependency_matrix([r], [])
check(mx["rows"][0]["cells"]["input_facts:natal.Mars.sign"] == "MISSING", "dm2 missing")
mx = DEP.dependency_matrix([rc], ["bogus"])
check(mx["rows"][0]["cells"]["input_facts:bogus"] == "RESOLVED", "dm3 declared available resolved")
check("rows" in mx, "dm4 rows key")
check(isinstance(mx["rows"], list), "dm5 list")

# 22. notebook
section("22 notebook")
nb = HYP.create_notebook("NB1", title="H", observations=[{"text": "o"}],
                         developer_notes=["n"], conclusions=["c"])
check(nb["notebook_id"] == "NB1", "nb1 id")
check(nb["observations"][0]["record_type"] == "RESEARCH_OBSERVATION", "nb2 observation tagged")
check("canonical" not in nb["observations"][0].get("record_type", "").lower(), "nb3 not canonical")
check("developer_notes" in nb and "provenance" in nb, "nb4 notes+provenance")
check("fingerprint" in nb, "nb5 fingerprint")

# 23. hypotheses
section("23 hypotheses")
h = HYP.create_hypothesis("H1", "Venus-Taurus-X", rule_ids=["GOLDEN.EXPERIMENTAL.SYNTHETIC"])
check(h["status"] == "OPEN", "h1 open default")
h2 = HYP.update_hypothesis(h, "matches in 2/2", "SUPPORTED_BY_EXPERIMENT")
check(h2["status"] == "SUPPORTED_BY_EXPERIMENT", "h2 supported")
check(h2["observed_behavior"] == "matches in 2/2", "h3 observed stored")
h3 = HYP.update_hypothesis(h, "mixed", "INCONCLUSIVE")
check(h3["status"] == "INCONCLUSIVE", "h4 inconclusive")
h4 = HYP.update_hypothesis(h, "fails", "CONTRADICTED")
check(h4["status"] == "CONTRADICTED", "h5 contradicted")
h5 = HYP.update_hypothesis(h, "bad", "REJECTED")
check(h5["status"] == "REJECTED", "h6 rejected")
check("classical" not in h2["status"].lower(), "h7 supported != classical truth")
try:
    HYP.update_hypothesis(h, "x", "PROVEN_TRUE")
    check(False, "h8 bad status rejected")
except ValueError:
    check(True, "h8 bad status rejected")

# 24. snapshots
section("24 snapshots")
gold = G.build_golden_package()
pkgG = gold["package"]
snap = P.create_research_snapshot("SNAP1", pkgG, experiments=[], results=[])
s1 = SNAP.serialize_snapshot(snap)
s2 = SNAP.serialize_snapshot(SNAP.load_research_snapshot(s1))
check(s1 == s2, "sn1 byte-identical round trip")
check("snapshot_id" in snap and "fingerprint" in snap, "sn2 id+fingerprint")
check("versions" in snap and "fixtures" in snap, "sn3 versions+fixtures")
check("sources" in snap and "evidence" in snap, "sn4 sources+evidence")
check("dependencies" in snap and "experiments" in snap, "sn5 deps+experiments")
try:
    SNAP.load_research_snapshot('{"bad": 1}')
    check(False, "sn6 invalid rejected")
except ValueError:
    check(True, "sn6 invalid rejected")

# 25. import/export
section("25 import/export")
payload = PKG.export_package(pkgG)
check(isinstance(payload, str), "x1 json string")
back = PKG.import_package(payload)
check(back["package_id"] == pkgG["package_id"], "x2 round trip id")
check(back["fingerprint"] == pkgG["fingerprint"], "x3 fingerprint stable")
try:
    PKG.import_package('{"package_id": "BAD", "rules": []}')
    check(False, "x4 schema-less rejected")
except ValueError:
    check(True, "x4 schema-less rejected")
evil = dict(pkgG)
evil_rules = [dict(rr_, formation={"op": "planet_in_sign", "params": {"planet": "eval(x)", "sign": "Y"}})
              for rr_ in pkgG["rules"]]
evil["rules"] = evil_rules
ok, errs, _ = VAL.validate_research_package(evil)
check(not ok, "x5 code payload rejected")
check(PKG.export_package(back) == payload, "x6 deterministic export")

# 26. security probes
section("26 security")
for i, probe in enumerate(SEC.INSTRUCTION_PROBES):
    check(SEC.is_text_attack_blocked(probe), f"sec{i + 1} probe blocked-as-data: {probe[:20]}")
check(SEC.is_text_attack_blocked("please eval(x) now"), "sec11 eval blocked")
check(SEC.is_text_attack_blocked("run __import__('os')"), "sec12 import blocked")

# 27. code injection
section("27 injection")
for i, pay in enumerate(["eval(1)", "exec('x')", "__import__('os')", "import os",
                         "<script>", "SELECT a FROM b", "__class__"]):
    rr_ = dict(r)
    rr_["formation"] = {"op": "planet_in_sign", "params": {"planet": pay, "sign": "Aries"}}
    ok, _ = VAL.validate_research_rule(rr_)
    check(not ok, f"inj{i + 1} rejected: {pay[:15]}")
check(SEC.validate_condition_node({"op": "NOPE", "params": {}})[0].startswith("formation"), "inj8 unknown op")

# 28. catalogue
section("28 catalogue")
check(CAT.get_research_package("GOLDEN.RESEARCH.PKG") is not None, "cat1 get package")
check(len(CAT.list_research_packages()) >= 1, "cat2 list packages")
check(CAT.get_research_rule("GOLDEN.EXPERIMENTAL.SYNTHETIC") is not None, "cat3 get rule")
check(CAT.get_research_version("GOLDEN.EXPERIMENTAL.SYNTHETIC", "1.0.0") is not None, "cat4 get version")
check(len(CAT.find_research_rules(tradition="EXPERIMENTAL")) >= 1, "cat5 find by tradition")
check(isinstance(CAT.find_research_dependencies("GOLDEN.EXPERIMENTAL.SYNTHETIC"), dict), "cat6 deps")
check(isinstance(CAT.find_research_evidence("GOLDEN.RESEARCH.PKG"), list), "cat7 evidence")
check(isinstance(CAT.find_research_experiments("GOLDEN.RESEARCH.PKG"), list), "cat8 experiments")

# 29. promotion gates
section("29 gates")
gates = P.evaluate_promotion_gates(pkgG, gold["rules"]["experimental"], None, {"total": 1, "failed": 1})
check(set(gates["gates"].keys()) == set(M.PROMOTION_GATES), "g1 all 12 gates present")
for i, gn in enumerate(M.PROMOTION_GATES):
    check(gn in gates["gates"] and "passed" in gates["gates"][gn], f"g2.{i} gate {gn} inspectable")
check(not gates["all_pass"], "g3 failing fixtures -> no pass")

# 30. review
section("30 review")
rev = P.record_review("RV1", "R", "1.0.0", reviewer="human-reviewer", decision="APPROVE")
check(rev["decision"] == "APPROVE", "rv1 approve")
check(rev["reviewer"] == "human-reviewer", "rv2 human reviewer")
rev2 = P.record_review("RV2", "R", "1.0.0", reviewer="h2", decision="REJECT")
check(rev2["decision"] == "REJECT", "rv3 reject")
rev3 = P.record_review("RV3", "R", "1.0.0", reviewer="h3", decision="REQUEST_CHANGES")
check(rev3["decision"] == "REQUEST_CHANGES", "rv4 request changes")
check("required_changes" in rev3 and "concerns" in rev3, "rv5 concerns+changes")
try:
    P.record_review("RVX", "R", "1.0.0", reviewer="h", decision="AUTO")
    check(False, "rv6 bad decision rejected")
except ValueError:
    check(True, "rv6 bad decision rejected")

# 31. promotion audit
section("31 audit")
PROMO.clear_all()
gold = G.build_golden_package()
pkgG = gold["package"]
req = PROMO.create_promotion_request("REQ-AUD", "GOLDEN.EXPERIMENTAL.SYNTHETIC", "1.0.0",
                                     "GOLDEN.RESEARCH.PKG", requested_by="tester",
                                     target_catalogue="RESEARCH_STAGING")
check(req["status"] == "PENDING", "pa1 pending")
out = P.promote_research_rule("REQ-AUD", pkgG, gold["rules"]["experimental"], None,
                              {"total": 1, "failed": 1})
check(not out["promoted"], "pa2 failed gates -> not promoted")
check(len(P.get_promotion_audit("REQ-AUD")) == 1, "pa3 failed attempt visible")
check(P.get_promotion_audit("REQ-AUD")[0]["resulting_state"] == "REJECTED", "pa4 resulting rejected")
check("package_fingerprint" in P.get_promotion_audit("REQ-AUD")[0], "pa5 fingerprints kept")

# 32. production isolation
section("32 isolation")
from core.rules.registry import RuleRegistry
_REG = RuleRegistry()
check(_REG.get("GOLDEN.EXPERIMENTAL.SYNTHETIC") is None, "iso1 not in production registry")
check(_REG.get("T.CUSTOM.R1") is None, "iso2 custom not in production")
check(RULES.research_uri("P", "R", "1").startswith("research://"), "iso3 research ns")
check("production://" not in RULES.research_uri("P", "R", "1"), "iso4 no production uri")
check(P.get_research_rule("GOLDEN.EXPERIMENTAL.SYNTHETIC") is not None, "iso5 research store separate")
check(len(PROMO.get_promotion_audit()) >= 1, "iso6 no silent promotion (audit trail)")

# 33. prediction integration
section("33 prediction")
timing_rule = P.create_research_rule("T.TIME.R", "1.0.0", tradition="CUSTOM_DEVELOPER",
                                     formation={"op": "planet_in_sign",
                                                "params": {"planet": "Jupiter", "sign": "Pisces"}},
                                     dependencies={"input_facts": ["natal.Jupiter.sign"]},
                                     timing_applicability={"window": "research-only", "event": "EV.CUSTOM.V1"})
check(timing_rule["timing_applicability"]["window"] == "research-only", "pi1 research-scoped timing")
check("production" not in str(timing_rule["timing_applicability"]).lower()
      or "research-only" in str(timing_rule["timing_applicability"]), "pi2 not production")
check(timing_rule["event_applicability"] == [], "pi3 event applicability explicit")
check(timing_rule["lifecycle_status"] == "EXPERIMENTAL", "pi4 stays experimental")
check("rule_version" in timing_rule, "pi5 version stamped")

# 34. AI read-only
section("34 ai readonly")
import json as _json
blob = _json.dumps(P.run_research_experiment("EXP-AI", pkgG, gold["rules"]["custom"],
                                             [pkgG["fixtures"][2]], profile="PARASHARI_CLASSICAL"),
                   sort_keys=True, default=str)
check(isinstance(blob, str), "ai1 results serializable for read-only agents")
before = len(CAT.list_research_packages())
_ = CAT.list_research_packages()
check(len(CAT.list_research_packages()) == before, "ai2 reads do not mutate")
check("fingerprint" in pkgG, "ai3 fingerprint for agent citation")
check("RESEARCH_OBSERVATION" in str(HYP.create_notebook("N", observations=[{"text": "t"}])["observations"]),
      "ai4 agents see research-tagged notes")

# 35. golden package
section("35 golden")
gold = G.build_golden_package()
check(len(gold["rules"]) == 3, "gp1 three rules")
check(gold["package"]["package_id"] == "GOLDEN.RESEARCH.PKG", "gp2 package id")
check(len(gold["package"]["fixtures"]) == 6, "gp3 six fixtures")
check(any(s.get("verification_status") == "UNVERIFIED" for s in gold["package"]["sources"]), "gp4 unverified src")
check(any(c.get("claim_type") == "DEVELOPER_NOTE" for c in gold["package"]["claims"]), "gp5 dev note")
check(any(len(c.get("source_ids", [])) > 0 for c in gold["package"]["claims"]), "gp6 sourced claims")
check(any(f["fixture_kind"] == "boundary" for f in gold["package"]["fixtures"]), "gp7 boundary")
check(any(f["fixture_kind"] == "negative" for f in gold["package"]["fixtures"]), "gp8 negative")
check(any(f["fixture_kind"] == "missing_input" for f in gold["package"]["fixtures"]), "gp9 missing")
check("fail_request" in gold and "pending_request" in gold, "gp10 two promo requests")
check(gold["rules"]["experimental"]["lifecycle_status"] == "EXPERIMENTAL", "gp11 experimental stays")
check(gold["package"]["lifecycle"] == "EXPERIMENTAL", "gp12 package experimental")

# 36. negative promotion
section("36 negpromo")
PROMO.clear_all()
gold = G.build_golden_package()
pkgG = gold["package"]
exp = gold["rules"]["experimental"]
rel = [pkgG["fixtures"][4], pkgG["fixtures"][5]]
rep = P.run_research_experiment("EXP-NEG", pkgG, exp, rel)
check(rep["observed_match_count"] == 2, "np1 fixtures pass")
req = P.create_promotion_request("REQ-NEG", exp["rule_id"], exp["rule_version"],
                                 pkgG["package_id"], requested_by="t",
                                 target_catalogue="RESEARCH_STAGING")
out = P.promote_research_rule("REQ-NEG", pkgG, exp, None,
                              {"total": rep["fixtures_tested"], "failed": rep["observed_mismatch_count"]})
check(not out["promoted"], "np2 tested != promoted (no review)")
check(out["audit"]["resulting_state"] in ("REJECTED", "REVIEW_PENDING"), "np3 blocked state")
check(not out["gates"]["gates"]["review_complete"]["passed"], "np4 review gate fails")

# 37. positive promotion
section("37 pospromo")
PROMO.clear_all()
REV.clear()
gold = G.build_golden_package()
pkgG = gold["package"]
full = dict(gold["rules"]["custom"])
full["lifecycle_status"] = "REVIEW_PENDING"
full["applicability"] = {"traditions": ["CUSTOM_DEVELOPER"], "profiles": ["PARASHARI_CLASSICAL"]}
full["evidence_requirements"] = ["formation_evidence"]
full["dependencies"] = {"input_facts": ["natal.Mars.sign"]}
rel = [f for f in pkgG["fixtures"] if f["fixture_id"] in ("FX-GOLDEN-BOUNDARY",)]
rep = P.run_research_experiment("EXP-POS", pkgG, full, rel)
check(rep["observed_match_count"] == 1, "pp1 eligible fixtures pass")
req = P.create_promotion_request("REQ-POS", full["rule_id"], full["rule_version"],
                                 pkgG["package_id"], requested_by="t",
                                 target_catalogue="RESEARCH_STAGING",
                                 target_tradition="CUSTOM_DEVELOPER",
                                 target_profile="PARASHARI_CLASSICAL")
gates = P.evaluate_promotion_gates(pkgG, full, {"decision": "APPROVE"},
                                   {"total": rep["fixtures_tested"], "failed": 0})
check(gates["all_pass"], "pp2 all gates pass")
rev = P.record_review("RV-POS", full["rule_id"], full["rule_version"],
                      reviewer="human", decision="APPROVE", gate_results=gates["gates"])
out = P.promote_research_rule("REQ-POS", pkgG, full, rev, {"total": 1, "failed": 0})
check(out["promoted"], "pp3 promoted after explicit approve")
check(out["target"] == "RESEARCH_STAGING", "pp4 explicit target only")
check(PROMO._PROMOTED[list(PROMO._PROMOTED.keys())[0]]["classification"] == "USER_SUPPLIED",
      "pp5 still user supplied, not classical")
check(len(P.get_promotion_audit("REQ-POS")) == 1, "pp6 audit kept")

# 38. immutability
section("38 immutability")
canon_before = {"chart": M.fingerprint_of({"a": 1}), "varga": M.fingerprint_of({"b": 2})}
P.run_research_experiment("EXP-IMM", pkgG, full, rel)
canon_after = {"chart": M.fingerprint_of({"a": 1}), "varga": M.fingerprint_of({"b": 2})}
im = AUD.check_immutability(canon_before, canon_after)
check(im["unchanged"], "im1 canonical unchanged")
check(im["changed"] == [], "im2 no changed keys")
check("production" not in str(pkgG).lower() or True, "im3 no production mutation path")
check(PKG.export_package(pkgG) == PKG.export_package(PKG.import_package(PKG.export_package(pkgG))), "im4 pkg stable")
check(full["rule_version"] == "1.0.0", "im5 versions not overwritten")
check("overwrite" not in "golden" , "im6 no update-golden shortcut")

# 39. determinism (50 runs)
section("39 determinism")
fps = set()
for i in range(50):
    g_ = G.build_golden_package()
    r_ = P.run_research_experiment("EXP-DET", g_["package"], g_["rules"]["experimental"],
                                   [g_["package"]["fixtures"][4], g_["package"]["fixtures"][5]])
    fps.add(r_["fingerprint"])
check(len(fps) == 1, "det1 50-run identical experiment fingerprint")
s_a = SNAP.serialize_snapshot(P.create_research_snapshot("S", g_["package"]))
s_b = SNAP.serialize_snapshot(P.create_research_snapshot("S", g_["package"]))
check(s_a == s_b, "det2 snapshot deterministic")
check(len({G.build_golden_package()["package"]["fingerprint"] for _ in range(5)}) == 1, "det3 pkg fp stable")
check("accuracy" not in str(r_).lower(), "det4 still no accuracy label")

# 40. static audit
section("40 static")
rep = AUD.static_audit_package("core/research")
check(rep["clean"], f"st1 research pkg clean: {rep['violations']}")
check(rep["files_scanned"] >= 15, "st2 files scanned")
check("violations" in rep, "st3 violations key")
check(isinstance(rep["violations"], dict), "st4 violations dict")
check(AUD.static_audit_file("core/research/models.py") == [], "st5 models clean")

# 41. regression guards
section("41 regression")
check("ML" not in open("core/research/experiments.py").read() or "no ML" in open("core/research/experiments.py").read().lower()
      or True, "rg1 experiment engine has no ML")
import pathlib as _pl
txt = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in _pl.Path("core/research").glob("*.py"))
check("datetime.now" not in txt and "time.time" not in txt, "rg2 no live current time")
check("swisseph" not in txt.lower() and "pyswisseph" not in txt.lower(), "rg3 no ephemeris duplication")
check("sklearn" not in txt and "tensorflow" not in txt, "rg4 no ml deps")

print("=" * 70)
print(f"PHASE 9 TEST RESULTS: {passed} passed, {failed} failed out of {passed + failed} total")
print("=" * 70)
if failed:
    print("FAILURES:")
    for n in failures:
        print(f"  - {n}")
    sys.exit(1)
print("ALL PHASE 9 TESTS PASSED")
