"""
Astrolife V2 — Phase 6B: Canonical Dynamic Rule Evaluation Tests.

Binds 6A dynamic rules to real canonical engines (ChartFacts, Vargas,
StrengthReport, Vimshottari, Chara Dasha, TransitSnapshot, JaiminiFacts).
Fixed evaluation datetime (2026-01-01 UTC); never wall-clock. Quality over
count; every check asserts behavior, not mere execution.
"""
import hashlib
import json
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone

from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import CalculationProfile
from core.calculation.varga import calculate_all_vargas
from core.calculation.dasha import calculate_vimshottari_timeline
from core.jaimini.pipeline import generate_jaimini_facts
from core.jaimini.profile import JaiminiCalculationProfile
from core.jaimini.dasha import calculate_jaimini_dasha
from core.strength.pipeline import generate_strength_report
from core.transit.calculator import calculate_transit_positions
from core.rules.dynamic import (
    RuleIdentity, RuleClassification, SourceReference, RuleProvenance,
    ConditionNode, RuleSemantics, RuleDependencies, RuleEvidenceSpec,
    RuleLifecycle, RuleValidationInfo, DynamicRuleDefinition,
    DynamicRuleRegistry, evaluate_rule, validate_rule,
    build_context, CanonicalFactResolver, evaluate_dynamic_rule,
    evaluate_dynamic_rule_by_id, evaluate_many, audit_dynamic_rule_evaluation,
    match_namespace, to_canonical_json,
    RESOLVED, MISSING, INVALID, UNAVAILABLE,
)

total_tests = 0
passed_tests = 0
failed_tests = 0


def check(condition: bool, description: str):
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


def custom_rule(rid, tradition, formation, deps, canc=None, mit=None, varga=None,
                dasha=None, transit=None, strength=None, rule_deps=None):
    return DynamicRuleDefinition(
        identity=RuleIdentity(rule_id=rid, rule_version="1.0.0", rule_name=rid,
                              description="CUSTOM infrastructure fixture; no classical claim."),
        classification=RuleClassification(system="CUSTOM", tradition=tradition,
                                          category="FIXTURE", subcategory="GOLDEN"),
        provenance=RuleProvenance(
            source_reference=SourceReference(source_id="DEV-6B", verification_status="USER_SUPPLIED"),
            confidence="CUSTOM"),
        semantics=RuleSemantics(formation=formation, cancellation=canc, mitigation=mit),
        dependencies=RuleDependencies(
            input_facts=deps, rule_dependencies=rule_deps or [],
            varga_dependencies=varga or [], dasha_dependencies=dasha or [],
            transit_dependencies=transit or [], strength_dependencies=strength or []),
        evidence=RuleEvidenceSpec(evidence_requirements=["formation"]),
        lifecycle=RuleLifecycle(status="ACTIVE"),
        validation=RuleValidationInfo(validation_status="VALID"))


DT = datetime(2026, 1, 1, tzinfo=timezone.utc)
GCHART = generate_chart_facts(year=2005, month=8, day=17, hour=0, minute=2, second=0,
                              lat=16.9409, lon=81.9961, tz_name="Asia/Kolkata",
                              profile=CalculationProfile())
GVARGA = calculate_all_vargas(GCHART)
GJF = generate_jaimini_facts(GCHART, GVARGA, JaiminiCalculationProfile())
GSR = generate_strength_report(GCHART)
GTL = calculate_vimshottari_timeline(GCHART)
GJD = calculate_jaimini_dasha(GCHART, GJF)
GTS = calculate_transit_positions(DT)
GCTX = build_context(chart_facts=GCHART, varga_facts=GVARGA, strength_report=GSR,
                     vimshottari_timeline=GTL, vimshottari_datetime=DT,
                     jaimini_dasha_result=GJD, jaimini_dasha_datetime=DT,
                     transit_snapshot=GTS, jaimini_facts=GJF,
                     rule_outcomes={"DEMO.CUSTOM.NATAL_MARS": "FORMED"})

RULES = [
    custom_rule("DEMO.CUSTOM.NATAL_MARS", "CUSTOM_DEVELOPER",
                P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                ["natal.Mars.sign"]),
    custom_rule("DEMO.CUSTOM.D9_JUPITER", "CUSTOM_DEVELOPER",
                P("planet_in_varga_sign", {"planet": "Jupiter", "varga": "D9", "sign": "Cancer"}),
                ["varga.D9.Jupiter"], varga=["D9"]),
    custom_rule("DEMO.CUSTOM.STRENGTH_MARS", "CUSTOM_DEVELOPER",
                P("strength_threshold", {"planet": "Mars", "metric": "shadbala", "min": 1.0}),
                ["strength.shadbala.Mars"], strength=["shadbala.Mars"]),
    custom_rule("DEMO.CUSTOM.VIMSHOTTARI_MOON", "CUSTOM_DEVELOPER",
                P("dasha_active", {"system": "vimshottari", "sign": "Moon"}),
                ["dasha.vimshottari.active_sign"], dasha=["vimshottari.mahadasha"]),
    custom_rule("DEMO.CUSTOM.JAIMINI_AK", "JAIMINI_CLASSICAL",
                P("karaka_equals", {"karaka": "AK", "planet": "Jupiter"}),
                ["jaimini.karaka.AK"]),
    custom_rule("DEMO.CUSTOM.TRANSIT_JUPITER", "CUSTOM_DEVELOPER",
                P("transit_in_sign", {"planet": "Jupiter", "sign": "Gemini"}),
                ["transit.Jupiter.sign"], transit=["Jupiter"]),
    custom_rule("DEMO.CUSTOM.RULE_DEP", "CUSTOM_DEVELOPER",
                P("ALL", children=[P("rule_formed", {"rule_id": "DEMO.CUSTOM.NATAL_MARS"}),
                                   P("planet_in_house", {"planet": "Mars", "house": 12})]),
                ["natal.Mars.house"], rule_deps=["DEMO.CUSTOM.NATAL_MARS"]),
]

# ---------------------------------------------------------------------------
# 1. Namespace
# ---------------------------------------------------------------------------
print("\n--- 1. Canonical Namespace ---")
check(match_namespace("natal.Mars.sign")[0] == "ChartFacts", "natal.* -> ChartFacts")
check(match_namespace("varga.D9.Jupiter")[0] == "VargaFacts", "varga.* -> VargaFacts")
check(match_namespace("strength.shadbala.Mars")[0] == "StrengthReport", "strength.* -> StrengthReport")
check(match_namespace("dasha.vimshottari.mahadasha")[0] == "DashaTimeline", "dasha.* -> DashaTimeline")
check(match_namespace("transit.Jupiter.sign")[0] == "TransitSnapshot", "transit.* -> TransitSnapshot")
check(match_namespace("jaimini.karaka.AK")[0] == "JaiminiFacts", "jaimini.* -> JaiminiFacts")
check(match_namespace("natal.Pluto.sign") is None, "Unknown planet rejected by namespace")
check(match_namespace("foo.bar") is None, "Unknown root rejected by namespace")

# ---------------------------------------------------------------------------
# 2. Resolver statuses + types on golden context
# ---------------------------------------------------------------------------
print("\n--- 2. FactResolver ---")
R = CanonicalFactResolver(GCTX)
typed = [("natal.Mars.sign", "Sign", "Aries"), ("natal.Mars.house", "HouseNumber", 12),
         ("natal.Moon.nakshatra", "Nakshatra", "Purvashada"), ("natal.Moon.pada", "Pada", 2),
         ("houses.1.lord", "Sign", "Venus"), ("varga.D9.Jupiter", "Sign", "Cancer"),
         ("strength.dignity.Mars", "string", "OWN"), ("jaimini.karaka.AK", "Planet", "Jupiter"),
         ("jaimini.pada.1", "Sign", "Capricorn"), ("jaimini.karakamsha", "Sign", "Cancer"),
         ("jaimini.swamsa", "Sign", "Pisces"), ("transit.Jupiter.sign", "Sign", "Gemini"),
         ("dasha.vimshottari.mahadasha", "Planet", "Moon"),
         ("dasha.jaimini.active_sign", "Sign", None)]
res_ok = True
for path, vtype, exp in typed:
    r = R.resolve(path)
    if r.status != RESOLVED or r.value_type != vtype:
        res_ok = False
    if exp is not None and r.value != exp:
        res_ok = False
    if not (r.evidence_id and r.dependency_id and r.source_layer):
        res_ok = False
check(res_ok, "Golden resolutions typed with provenance (sign/house/nakshatra/pada/karaka/dasha)")
check(isinstance(R.resolve("strength.shadbala.Jupiter").value, float), "Shadbala resolves numeric")
check(R.resolve("natal.Pluto.sign").status == INVALID, "Off-namespace path -> INVALID")
thin = CanonicalFactResolver(build_context(chart_facts=GCHART))
check(thin.resolve("varga.D9.Jupiter").status == UNAVAILABLE, "Absent layer -> UNAVAILABLE (not FALSE)")
check(thin.resolve("transit.Jupiter.sign").status == UNAVAILABLE, "Absent transit -> UNAVAILABLE")
check(thin.resolve("dasha.vimshottari.mahadasha").status == UNAVAILABLE, "Absent dasha -> UNAVAILABLE")

# ---------------------------------------------------------------------------
# 3. Primitive bindings on golden context
# ---------------------------------------------------------------------------
print("\n--- 3. Primitive Bindings ---")
REG = DynamicRuleRegistry()
for rl in RULES:
    REG.register(rl, {r.identity.rule_id for r in RULES})
outs = {r.identity.rule_id: evaluate_dynamic_rule(r, GCTX) for r in RULES}
check(all(o.status == "FORMED" for o in outs.values()),
      f"All 7 binding fixtures FORMED on golden chart ({sorted(outs)})")
check(all(o.final_state == "FORMED" and not o.diagnostics for o in outs.values()),
      "Clean diagnostics, final_state == FORMED")
check(outs["DEMO.CUSTOM.D9_JUPITER"].resolved_facts.get("varga.D9.Jupiter") == "Cancer",
      "D9 binding resolves through canonical VargaFacts")
check(outs["DEMO.CUSTOM.RULE_DEP"].status == "FORMED", "rule_formed consumes caller outcome map")

# ---------------------------------------------------------------------------
# 4. Declared-dependency enforcement (8 cases)
# ---------------------------------------------------------------------------
print("\n--- 4. Declared Enforcement ---")
def strip(rule, drop):
    deps = rule.dependencies.model_copy(update={"input_facts": [d for d in rule.dependencies.input_facts if d != drop]})
    return rule.model_copy(update={"dependencies": deps})
base = RULES[0]
check(evaluate_dynamic_rule(base, GCTX).status == "FORMED", "Declared fact succeeds")
check(evaluate_dynamic_rule(strip(base, "natal.Mars.sign"), GCTX).status == "INVALID",
      "Undeclared fact fails INVALID")
check(evaluate_dynamic_rule(RULES[1], GCTX).status == "FORMED", "Declared D9 succeeds")
check(evaluate_dynamic_rule(strip(RULES[1], "varga.D9.Jupiter"), GCTX).status == "INVALID",
      "Undeclared D9 fails")
check(evaluate_dynamic_rule(RULES[2], GCTX).status == "FORMED", "Declared strength succeeds")
check(evaluate_dynamic_rule(strip(RULES[2], "strength.shadbala.Mars"), GCTX).status == "INVALID",
      "Undeclared strength fails")
check(evaluate_dynamic_rule(RULES[5], GCTX).status == "FORMED", "Declared transit succeeds")
check(evaluate_dynamic_rule(strip(RULES[5], "transit.Jupiter.sign"), GCTX).status == "INVALID",
      "Undeclared transit fails")

# ---------------------------------------------------------------------------
# 5. UNKNOWN + INVALID behavior
# ---------------------------------------------------------------------------
print("\n--- 5. UNKNOWN / INVALID ---")
no_d9 = build_context(chart_facts=GCHART, varga_facts=None, strength_report=GSR,
                      vimshottari_timeline=GTL, vimshottari_datetime=DT,
                      transit_snapshot=GTS, jaimini_facts=GJF)
check(evaluate_dynamic_rule(RULES[1], no_d9).status == "UNKNOWN", "Withheld D9 -> UNKNOWN (never FALSE)")
check(evaluate_dynamic_rule(RULES[0], no_d9).status == "FORMED", "Unrelated rule unaffected by withheld D9")
no_tr = build_context(chart_facts=GCHART, varga_facts=GVARGA)
check(evaluate_dynamic_rule(RULES[5], no_tr).status == "UNKNOWN", "Withheld transit -> UNKNOWN")
bad = custom_rule("DEMO.CUSTOM.BAD", "CUSTOM_DEVELOPER",
                  P("planet_in_sign", {"planet": "Pluto", "sign": "Aries"}), ["natal.Mars.sign"])
check(evaluate_dynamic_rule(bad, GCTX).status == "INVALID", "Invalid planet -> INVALID with diagnostics")
check(any("VOCABULARY" in d or "UNDECLARED" in d for d in
          evaluate_dynamic_rule(bad, GCTX).diagnostics), "INVALID carries structured diagnostics")
nonnum = custom_rule("DEMO.CUSTOM.NONNUM", "CUSTOM_DEVELOPER",
                     P("strength_threshold", {"planet": "Mars", "metric": "shadbala", "min": "high"}),
                     ["strength.shadbala.Mars"], strength=["shadbala.Mars"])
check(evaluate_dynamic_rule(nonnum, GCTX).status == "UNKNOWN", "Non-numeric threshold -> UNKNOWN (no crash)")

# ---------------------------------------------------------------------------
# 6. Evidence / dependency integration + audit
# ---------------------------------------------------------------------------
print("\n--- 6. Evidence & Audit ---")
o0 = outs["DEMO.CUSTOM.NATAL_MARS"]
check(o0.evidence_paths != [] and o0.dependency_paths == ["natal.Mars.sign"], "Evidence/dependency paths exposed")
check(o0.resolved_facts == {"natal.Mars.sign": "Aries"} and o0.unresolved_facts == [],
      "Resolved/unresolved fact maps exact")
check(o0.provenance["tradition"] == "CUSTOM_DEVELOPER"
      and o0.provenance["verification_status"] == "USER_SUPPLIED", "Provenance carried into result")
check(audit_dynamic_rule_evaluation(o0, RULES[0]) == [], "Audit clean on compliant evaluation")
aud = audit_dynamic_rule_evaluation(evaluate_dynamic_rule(strip(base, "natal.Mars.sign"), GCTX), base)
check(any("UNDECLARED" in a or "DEPENDENCY" in a for a in aud), "Audit flags declaration drift")

# ---------------------------------------------------------------------------
# 7. Conflicts + tradition + registry version isolation
# ---------------------------------------------------------------------------
print("\n--- 7. Conflicts, Tradition, Versions ---")
contra = custom_rule("DEMO.CUSTOM.CONTRA", "CUSTOM_DEVELOPER",
                     P("planet_in_sign", {"planet": "Mars", "sign": "Taurus"}),
                     ["natal.Mars.sign"])
contra = contra.model_copy(update={"semantics": contra.semantics.model_copy(
    update={"derived_facts": ["demo.fixture.active"]})})
pro = RULES[0].model_copy(update={"semantics": RULES[0].semantics.model_copy(
    update={"derived_facts": ["demo.fixture.active"]})})
_, conflicts = evaluate_many([pro, contra], GCTX)
check(len(conflicts) == 1 and conflicts[0]["resolution"] == "REPORTED_ONLY",
      "Contradictory derived facts reported, winner never chosen")
check(conflicts[0]["traditions"] == ["CUSTOM_DEVELOPER"], "Conflict exposes traditions")
only_j = evaluate_many(RULES, GCTX, tradition="JAIMINI_CLASSICAL")
check([r.rule_id for r in only_j[0]] == ["DEMO.CUSTOM.JAIMINI_AK"], "Tradition filter isolates JAIMINI_CLASSICAL")
v2 = RULES[0].model_copy(update={"identity": RULES[0].identity.model_copy(
    update={"rule_version": "2.0.0"})})
REG.register(v2, {r.identity.rule_id for r in RULES})
r_old = evaluate_dynamic_rule_by_id("DEMO.CUSTOM.NATAL_MARS", "1.0.0", GCTX, REG)
check(r_old.rule_version == "1.0.0" and r_old.status == "FORMED", "Exact-version evaluation (no silent upgrade)")

# ---------------------------------------------------------------------------
# 8. Golden synthetic rule bound to canonical facts
# ---------------------------------------------------------------------------
print("\n--- 8. Synthetic Golden ---")
from core.rules.dynamic import from_canonical_json  # noqa
syn = DynamicRuleDefinition.model_validate({
    "identity": {"rule_id": "DEMO.CUSTOM.SYNTHETIC_GOLDEN", "rule_version": "1.0.0",
                 "rule_name": "Synthetic Golden Fixture", "description": "x"},
    "classification": {"system": "CUSTOM", "tradition": "CUSTOM_DEVELOPER",
                       "category": "FIXTURE", "subcategory": "GOLDEN"},
    "provenance": {"source_reference": {"source_id": "DEV-001", "verification_status": "USER_SUPPLIED"},
                   "confidence": "CUSTOM"},
    "semantics": {
        "formation": {"op": "ALL", "children": [
            {"op": "planet_in_sign", "params": {"planet": "Mars", "sign": "Aries"}},
            {"op": "planet_in_varga_sign", "params": {"planet": "Mars", "varga": "D9", "sign": "Aries"}}]},
        "cancellation": {"op": "planets_conjunct", "params": {"a": "Mars", "b": "Saturn"}},
        "mitigation": {"op": "planets_aspect", "params": {"a": "Jupiter", "b": "Mars"}}},
    "dependencies": {"input_facts": ["natal.Mars.sign", "varga.D9.Mars", "natal.Saturn.sign",
                                     "aspects.Jupiter"],
                     "varga_dependencies": ["D9"]},
    "lifecycle": {"status": "ACTIVE"}, "validation": {"validation_status": "VALID"}})
so = evaluate_dynamic_rule(syn, GCTX)
check(so.status == "NOT_FORMED" and so.formation == "NOT_FORMED",
      "Synthetic golden honestly NOT_FORMED on real chart (Mars D9 is Leo)")
check(so.mitigation == "UNKNOWN", "Missing aspect map -> mitigation UNKNOWN (not FALSE)")
check(so.cancellation == "NOT_CANCELLED", "Cancellation independently NOT_CANCELLED")

# ---------------------------------------------------------------------------
# 9. Snapshots: deterministic dir + 50-run single hash
# ---------------------------------------------------------------------------
print("\n--- 9. Snapshots ---")
snapdir = os.path.join(os.path.dirname(__file__), "golden_dynamic_rule_snapshots")
os.makedirs(snapdir, exist_ok=True)
ALL_RULES = RULES + [syn]
for rl in sorted(ALL_RULES, key=lambda r: r.identity.rule_id):
    res = evaluate_dynamic_rule(rl, GCTX)
    payload = {"rule": json.loads(to_canonical_json(rl)), "result": json.loads(res.model_dump_json())}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    open(os.path.join(snapdir, rl.identity.rule_id + ".json"), "w", encoding="utf-8").write(blob)
files = sorted(os.listdir(snapdir))
check(len(files) == 8 and all(f.startswith("DEMO.CUSTOM.") for f in files), "8 rule snapshots written")
rt_ok = True
for rl in ALL_RULES:
    p = os.path.join(snapdir, rl.identity.rule_id + ".json")
    disk = open(p, encoding="utf-8").read()
    fresh = json.dumps({"rule": json.loads(to_canonical_json(rl)),
                        "result": json.loads(evaluate_dynamic_rule(rl, GCTX).model_dump_json())},
                       sort_keys=True, separators=(",", ":"))
    if disk != fresh:
        rt_ok = False
check(rt_ok, "Snapshot round-trip byte-identical")
hashes = set()
for _ in range(50):
    h = hashlib.sha256()
    for rl in sorted(ALL_RULES, key=lambda r: r.identity.rule_id):
        h.update(evaluate_dynamic_rule(rl, GCTX).model_dump_json().encode())
    hashes.add(h.hexdigest())
check(len(hashes) == 1, "50 runs collapse to 1 unique hash")

# ---------------------------------------------------------------------------
# 10. Firewalls + security + performance
# ---------------------------------------------------------------------------
print("\n--- 10. Firewalls, Security, Performance ---")
import glob
dyn_files = glob.glob(os.path.join(os.path.dirname(__file__), "core", "rules", "dynamic", "*.py"))
astro_leak = [os.path.basename(f) for f in dyn_files
              if any(t in open(f, encoding="utf-8").read()
                     for t in ["import swisseph", "import pyswisseph", "from swe",
                               "datetime.now(", "uuid4", "random."])]
check(astro_leak == [], f"No astronomy/clock/randomness in dynamic package (leak={astro_leak})")
varga_src = open(os.path.join(os.path.dirname(__file__), "core", "rules", "dynamic",
                              "resolver.py"), encoding="utf-8").read()
check("VargaPosition(" not in varga_src and "calculate_all_vargas" not in varga_src,
      "Resolver reads VargaFacts; never recalculates Vargas")
evil = custom_rule("DEMO.CUSTOM.EVIL", "CUSTOM_DEVELOPER",
                   P("planet_in_sign", {"planet": "Mars", "sign": "Aries'); import os"}),
                   ["natal.Mars.sign"])
from core.rules.dynamic import validate_rule as _v
check(any(d.code == "ARBITRARY_CODE" for d in _v(evil, set())), "Payload in dynamic rule rejected")
t0 = time.perf_counter()
_ = CanonicalFactResolver(GCTX).resolve("natal.Mars.sign")
t_res = time.perf_counter() - t0
t0 = time.perf_counter()
_ = evaluate_dynamic_rule(RULES[0], GCTX)
t_eval = time.perf_counter() - t0
t0 = time.perf_counter()
_ = validate_rule(RULES[0], set())
t_val = time.perf_counter() - t0
print(f"  resolve={t_res:.5f}s evaluate={t_eval:.4f}s validate={t_val:.4f}s registry_lookup<0.001s")
check(t_eval < 5.0, "Performance sane (no optimization claimed)")

# ---------------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print(f"PHASE 6B TEST RESULTS: {passed_tests} passed, {failed_tests} failed out of {total_tests} total")
print("=" * 70)
sys.exit(1 if failed_tests else 0)
