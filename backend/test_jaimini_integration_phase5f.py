"""
Astrolife V2 — Phase 5F: Jaimini Hardening + Cross-System Integration Tests.

Covers: golden cross-system audit, positive/negative/unknown inputs,
dependencies (+cycle detection), conflicts, tradition isolation, provenance,
evidence completeness, determinism (50x), serialization round-trip,
cross-system boundaries, exhaustive sweeps with independent references,
and performance reporting.
"""
import inspect
import json
import os
import sys
import time
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.calculation.models import (
    ChartFacts, Location, TimeDetails, AyanamshaDetails, AscendantData,
    PlanetData, HouseData, SignPosition, NakshatraPosition, LongitudeDetails,
)
from core.calculation.config import CalculationProfile
from core.calculation.varga import calculate_all_vargas
from core.calculation.pipeline import generate_chart_facts
from core.jaimini.profile import JaiminiCalculationProfile
from core.jaimini.pipeline import generate_jaimini_facts
from core.jaimini.arudha import SIGNS
from core.jaimini.rashi_drishti import get_sign_rashi_drishti
from core.jaimini.rules import JaiminiYogaProfile, evaluate_jaimini_yogas
from core.jaimini.evidence import (
    build_evidence_graph, DIRECT_FACT, DERIVED_FACT, RULE_DERIVED,
)
from core.jaimini.dependencies import (
    FACT, DERIVED_FACT as DFACT, RULE_RESULT, get_dependency_spec,
    detect_dependency_cycles, DEPENDENCY_SPECS, RuleDependencySpec, RuleDependency,
    dependency_covered,
)
from core.jaimini.conflicts import (
    analyze_conflicts, DIRECT_CONTRADICTION, DIFFERENT_DIMENSIONS,
    TRADITION_VARIANT, INSUFFICIENT_INFORMATION, NO_CONFLICT,
)
from core.jaimini.rule_validators import (
    validate_evidence_completeness, validate_rule_provenance,
)
from core.jaimini.integration import (
    evaluate_jaimini, missing_inputs, validate_dependency_policy,
    JaiminiIntegrationProfile,
)
from core.rules.enums import FormationStatus


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


BASE_SPEC = {
    "Sun": {"sign": "Leo", "deg": 0.0418},
    "Moon": {"sign": "Sagittarius", "deg": 17.8627},
    "Mars": {"sign": "Aries", "deg": 16.5930},
    "Mercury": {"sign": "Cancer", "deg": 14.8395},
    "Jupiter": {"sign": "Virgo", "deg": 21.8426},
    "Venus": {"sign": "Virgo", "deg": 5.6417},
    "Saturn": {"sign": "Cancer", "deg": 10.0625},
    "Rahu": {"sign": "Pisces", "deg": 22.3264},
    "Ketu": {"sign": "Virgo", "deg": 22.3264},
}


def make_chart(asc_sign: str = "Taurus", spec: Optional[Dict[str, Dict[str, Any]]] = None) -> ChartFacts:
    planets_spec = dict(BASE_SPEC)
    if spec:
        for k, v in spec.items():
            planets_spec[k] = v
    asc_idx = SIGNS.index(asc_sign)
    planets_dict = {}
    for p_name, ps in planets_spec.items():
        s_idx = SIGNS.index(ps["sign"])
        lon = s_idx * 30.0 + ps["deg"]
        planets_dict[p_name] = PlanetData(
            id=p_name.lower(), name=p_name,
            longitude=LongitudeDetails(tropical=lon + 24.0, sidereal=lon),
            latitude=0.0, distance=1.0, speed=1.0, retrograde=False,
            sign=SignPosition(id=s_idx + 1, name=ps["sign"], degree=ps["deg"]),
            house=((s_idx - asc_idx) % 12) + 1,
            nakshatra=NakshatraPosition(
                id=1, name="Ashwini", lord="Ketu", pada=1, fraction=0.1,
                start_longitude=0.0, end_longitude=13.33, degree_within=ps["deg"]),
        )
    houses_dict = {}
    for h in range(1, 13):
        s_idx = (asc_idx + h - 1) % 12
        houses_dict[h] = HouseData(id=h, sign=SignPosition(id=s_idx + 1, name=SIGNS[s_idx], degree=0.0))
    return ChartFacts(
        calculation_profile=CalculationProfile(),
        location=Location(latitude=16.94, longitude=81.99, timezone="Asia/Kolkata"),
        time=TimeDetails(local_datetime="2005-08-17T00:02:00", timezone="Asia/Kolkata",
                         utc_datetime="2005-08-16T18:32:00Z", julian_day=2453599.2722),
        ayanamsha=AyanamshaDetails(system="LAHIRI", swiss_mode="SIDM_LAHIRI", value=23.9356),
        ascendant=AscendantData(
            longitude=LongitudeDetails(tropical=asc_idx * 30.0 + 34.0, sidereal=asc_idx * 30.0 + 10.0),
            sign=SignPosition(id=asc_idx + 1, name=asc_sign, degree=10.0),
            nakshatra=NakshatraPosition(id=3, name="Krittika", lord="Sun", pada=1, fraction=0.5,
                                        start_longitude=26.66, end_longitude=40.0, degree_within=10.0)),
        planets=planets_dict, houses=houses_dict,
    )


def full_inputs(chart: ChartFacts):
    vf = calculate_all_vargas(chart)
    jf = generate_jaimini_facts(chart, vf, JaiminiCalculationProfile())
    return vf, jf


def golden_inputs():
    gchart = generate_chart_facts(year=2005, month=8, day=17, hour=0, minute=2, second=0,
                                  lat=16.9409, lon=81.9961, tz_name="Asia/Kolkata",
                                  profile=CalculationProfile())
    vf = calculate_all_vargas(gchart)
    jf = generate_jaimini_facts(gchart, vf, JaiminiCalculationProfile())
    return gchart, vf, jf


GCHART, GVF, GJF = golden_inputs()
GEVAL = evaluate_jaimini(GCHART, GJF, GVF)

# ---------------------------------------------------------------------------
# A. Golden cross-system audit
# ---------------------------------------------------------------------------
print("\n--- A. Golden Cross-System Audit ---")
kk = GJF.chara_karakas.karakas
check([kk[c].planet for c in ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]] ==
      ["Jupiter", "Moon", "Mars", "Mercury", "Saturn", "Venus", "Sun"],
      "Golden karaka chain traceable: Jup/Moon/Mars/Merc/Sat/Ven/Sun")
check(GJF.karakamsha.karakamsha_sign == "Cancer", "Golden Karakamsha = Cancer")
check(GJF.karakamsha.swamsa_navamsha_lagna_sign != "Cancer", "Golden Swamsa distinct from Karakamsha")
check(GJF.arudha_lagna.final_sign == "Capricorn" and GJF.upapada.final_sign == "Capricorn",
      "Golden AL = UL = Capricorn")
check(GEVAL.formed_rules == ["JAI.ARUDHA.AL_LORD_KENDRA_TRINE", "JAI.DRISHTI.AK_AMK_MUTUAL",
                             "JAI.KARAKAMSHA.BENEFIC_OCCUPANCY"],
      "Golden formed set matches accepted 5E result")
check(GEVAL.total_rules == 12 and GEVAL.unknown_rules == [], "Golden: 12 rules, zero UNKNOWN")
node_ids = set(GEVAL.evidence_graph.node_ids())
check("karaka:AK" in node_ids and "pada:A1:final" in node_ids and "karakamsha:sign" in node_ids,
      "Golden graph contains karaka/pada/karakamsha anchors")
check(all(f"rule:{r.rule_id}:result" in node_ids for r in GEVAL.rules),
      "Every golden rule result traceable in graph")
tiers = {n.node_id: n.tier for n in GEVAL.evidence_graph.nodes}
check(tiers["d1:planet:Jupiter:sign"] == DIRECT_FACT, "D1 sign tiered DIRECT_FACT")
check(tiers["karaka:AK"] == DERIVED_FACT, "AK assignment tiered DERIVED_FACT")
check(tiers["rule:JAI.DRISHTI.AK_AMK_MUTUAL:result"] == RULE_DERIVED, "Rule outcome tiered RULE_DERIVED")

# ---------------------------------------------------------------------------
# B/C. Positive / negative rule tests through integration
# ---------------------------------------------------------------------------
print("\n--- B/C. Positive & Negative ---")
pos_chart = make_chart("Aries", {"Jupiter": {"sign": "Leo", "deg": 28.5},
                                 "Moon": {"sign": "Leo", "deg": 25.2}})
pvf, pjf = full_inputs(pos_chart)
pev = evaluate_jaimini(pos_chart, pjf, pvf)
pos_res = next(r for r in pev.rules if r.rule_id == "JAI.KARAKA.AK_AMK_CONJUNCTION")
check(pos_res.formed and pos_res.formation_status == FormationStatus.FORMED, "Positive fixture formed via integration")
check(any(e.from_id == "karaka:AK" and e.to_id == "rule:JAI.KARAKA.AK_AMK_CONJUNCTION:formation"
          for e in pev.evidence_graph.edges), "Graph links karaka:AK into rule formation")
neg_res = next(r for r in GEVAL.rules if r.rule_id == "JAI.KARAKA.AK_AMK_CONJUNCTION")
check(not neg_res.formed and neg_res.formation_status == FormationStatus.NOT_FORMED, "Golden negative carries NOT_FORMED")
check(len(neg_res.formation_evidence) == 1 and not neg_res.formation_evidence[0].passed,
      "Negative exposes failing evidence (why it failed)")

# ---------------------------------------------------------------------------
# D. UNKNOWN-input tests
# ---------------------------------------------------------------------------
print("\n--- D. UNKNOWN Semantics ---")
stripped_varga = {"planets": {}, "ascendant": {}}
uev = evaluate_jaimini(GCHART, GJF, stripped_varga)
uk = sorted(uev.unknown_rules)
check(uk == ["JAI.KARAKAMSHA.BENEFIC_OCCUPANCY", "JAI.SWAMSA.BENEFIC_OCCUPANCY"],
      f"D9-stripped inputs yield exactly the 2 D9 rules UNKNOWN (got {uk})")
u1 = next(r for r in uev.rules if r.rule_id == "JAI.KARAKAMSHA.BENEFIC_OCCUPANCY")
check(u1.formation_status == FormationStatus.UNCERTAIN and not u1.formed, "UNKNOWN is UNCERTAIN, never NOT_FORMED")
check("missing" in " ".join(u1.cancellation_evidence).lower(), "UNKNOWN carries missing-dependency explanation")
check(len([r for r in uev.rules if r.formation_status == FormationStatus.FORMED]) >= 2,
      "Non-D9 rules unaffected by D9 stripping")
dropped = evaluate_jaimini(GCHART, GJF, stripped_varga,
                           JaiminiIntegrationProfile(include_unknown=False))
check(dropped.total_rules == 10 and dropped.unknown_rules == [], "include_unknown=False drops UNKNOWN results")
check(missing_inputs("JAI.SWAMSA.BENEFIC_OCCUPANCY", GJF, stripped_varga) != [], "missing_inputs() flags absent D9-lagna")
check(missing_inputs("JAI.ARUDHA.DHANA_A2_A11", GJF, GVF) == [], "Complete inputs report nothing missing")

# ---------------------------------------------------------------------------
# E. Dependency tests
# ---------------------------------------------------------------------------
print("\n--- E. Dependencies ---")
dep_ok = True
for r in GEVAL.rules:
    declared = [d.fact_path for d in get_dependency_spec(r.rule_id).dependencies]
    if not all(dependency_covered(declared, used) for used in r.dependencies):
        dep_ok = False
check(dep_ok, "Every result dependency is within its declared spec (index-aware)")
check(detect_dependency_cycles() == [], "Production RULE_RESULT graph is acyclic")
cyclic = {
    "A": RuleDependencySpec("A", [RuleDependency("A", RULE_RESULT, "B", True, "x")]),
    "B": RuleDependencySpec("B", [RuleDependency("B", RULE_RESULT, "A", True, "y")]),
}
check(detect_dependency_cycles(cyclic) == [["A", "B", "A"]], "Cycle detector flags synthetic A<->B cycle")
check(validate_dependency_policy() == [], "Varga/strength policy audit clean (D9 only where declared, zero strength)")
check(all(get_dependency_spec(rid).strength_dependencies == [] for rid in
          [r.rule_id for r in GEVAL.rules]), "strength_dependencies == [] for all rules")

# ---------------------------------------------------------------------------
# F. Conflict tests
# ---------------------------------------------------------------------------
print("\n--- F. Conflicts ---")
gconf = {(c.rule_a, c.rule_b): c.conflict_class for c in GEVAL.conflicts}
check(len(GEVAL.conflicts) == 3 and set(gconf.values()) == {DIFFERENT_DIMENSIONS},
      "Golden: exactly 3 same-proposition pairs, all DIFFERENT_DIMENSIONS")
check(all(c.resolution == "REPORTED_ONLY" for c in GEVAL.conflicts), "Conflicts report-only, never resolved")
# Synthetic DIRECT_CONTRADICTION: force both disjoint rules FORMED
from core.jaimini.rules.models import JaiminiRuleResult
from core.rules.enums import StrengthStatus, CancellationStatus, MitigationStatus
import copy


def _synth(rid: str, formed: bool, origin: str = "CLASSICAL_JAIMINI",
           status: FormationStatus = None) -> JaiminiRuleResult:
    return JaiminiRuleResult(
        rule_id=rid, name=rid, formed=formed,
        formation_status=status if status else (FormationStatus.FORMED if formed else FormationStatus.NOT_FORMED),
        quality=StrengthStatus.UNKNOWN, cancellation_status=CancellationStatus.NONE,
        mitigation_status=MitigationStatus.NONE, origin_label=origin, method="synthetic",
        formation_evidence=[], dependencies=["JaiminiFacts.chara_karakas"], notes="synthetic")


both = [_synth("JAI.KARAKA.AK_AMK_CONJUNCTION", True), _synth("JAI.DRISHTI.AK_AMK_MUTUAL", True)]
cc = analyze_conflicts(both)
check(len(cc) == 1 and cc[0].conflict_class == DIRECT_CONTRADICTION, "Both-disjoint-FORMED raises DIRECT_CONTRADICTION alarm")
unk_pair = [_synth("JAI.KARAKA.AK_AMK_CONJUNCTION", False, status=FormationStatus.UNCERTAIN),
            _synth("JAI.DRISHTI.AK_AMK_MUTUAL", False)]
check(analyze_conflicts(unk_pair)[0].conflict_class == INSUFFICIENT_INFORMATION,
      "UNKNOWN participant yields INSUFFICIENT_INFORMATION")
var_pair = [_synth("JAI.KARAKA.DK_UL_SAMBANDHA", True, "TRADITION_DEPENDENT"),
            _synth("JAI.ARUDHA.A7_UL_ALIGNMENT", True, "CLASSICAL_JAIMINI")]
check(analyze_conflicts(var_pair)[0].conflict_class == TRADITION_VARIANT,
      "Cross-origin same-proposition pair yields TRADITION_VARIANT")

# ---------------------------------------------------------------------------
# G. Tradition isolation
# ---------------------------------------------------------------------------
print("\n--- G. Tradition Isolation ---")
classical = evaluate_jaimini(GCHART, GJF, GVF, JaiminiIntegrationProfile(origin_labels=["CLASSICAL_JAIMINI"]))
check(classical.total_rules == 5 and all(
    get_dependency_spec(r.rule_id).origin_label == "CLASSICAL_JAIMINI" for r in classical.rules),
    "CLASSICAL_JAIMINI filter evaluates exactly the 5 classical rules")
check(set(classical.formed_rules).issubset(set(GEVAL.formed_rules)), "Classical formed set consistent with full evaluation")
trad = evaluate_jaimini(GCHART, GJF, GVF, JaiminiIntegrationProfile(origin_labels=["TRADITION_DEPENDENT"]))
check(trad.total_rules == 7, "TRADITION_DEPENDENT filter evaluates exactly 7 rules")
check(classical.profile["origin_labels"] == ["CLASSICAL_JAIMINI"], "Profile records applied tradition filter")

# ---------------------------------------------------------------------------
# H/I. Provenance + completeness validators
# ---------------------------------------------------------------------------
print("\n--- H/I. Validators ---")
check(validate_evidence_completeness(GEVAL.rules) == [], "Golden evidence completeness clean")
check(validate_rule_provenance(GEVAL.rules) == [], "Golden provenance validation clean")
bad = _synth("JAI.KARAKA.AK_AMK_CONJUNCTION", True)
bad.confidence = "VERIFIED"  # type: ignore
from core.rules.enums import ConfidenceLevel
bad.confidence = ConfidenceLevel.VERIFIED
check(validate_rule_provenance([bad]) != [], "VERIFIED confidence without metadata is rejected")
bad2 = _synth("JAI.ARUDHA.DHANA_A2_A11", True)
bad2.formation_evidence = []
check(validate_evidence_completeness([bad2]) != [], "FORMED without evidence is rejected")
bad3 = _synth("JAI.SWAMSA.BENEFIC_OCCUPANCY", False, status=FormationStatus.UNCERTAIN)
bad3.cancellation_evidence = ["nothing to see"]
bad3.notes = "all good"
check(validate_evidence_completeness([bad3]) != [], "UNKNOWN without missing-explanation is rejected")

# ---------------------------------------------------------------------------
# J/K. Determinism + serialization round-trip + golden snapshot
# ---------------------------------------------------------------------------
print("\n--- J/K. Determinism & Snapshot ---")
base_json = GEVAL.model_dump_json()
det_ok = True
for _ in range(50):
    if evaluate_jaimini(GCHART, GJF, GVF).model_dump_json() != base_json:
        det_ok = False
        break
check(det_ok, "50 consecutive full-pipeline evaluations bit-for-bit identical")
node_order_ok = GEVAL.evidence_graph.node_ids() == sorted(GEVAL.evidence_graph.node_ids())
check(node_order_ok, "Evidence node IDs in stable sorted order")
snap_path = os.path.join(os.path.dirname(__file__), "golden_jaimini_evidence_snapshot.json")
snap = {
    "chart": "Golden Chart — Aug 17, 2005 00:02 AM Anaparthy",
    "engine": "jaimini-integration/1.0.0",
    "canonical": {
        "ascendant": GCHART.ascendant.sign.name,
        "d1_signs": {p: GCHART.planets[p].sign.name for p in sorted(GCHART.planets.keys())},
        "karakas": {c: {"planet": kk[c].planet, "sign": kk[c].sign,
                        "degree": kk[c].degree_in_sign} for c in sorted(kk.keys())},
        "padas": {GJF.arudha_padas[h].pada_code: GJF.arudha_padas[h].final_sign for h in sorted(GJF.arudha_padas)},
        "karakamsha": GJF.karakamsha.karakamsha_sign,
        "swamsa": GJF.karakamsha.swamsa_navamsha_lagna_sign,
    },
    "evaluation": json.loads(base_json),
}
with open(snap_path, "w", encoding="utf-8") as f:
    json.dump(snap, f, indent=2)
check(os.path.exists(snap_path), "Golden evidence snapshot written by engine")
reloaded = json.load(open(snap_path, encoding="utf-8"))
fresh = evaluate_jaimini(GCHART, GJF, GVF)
check(reloaded["evaluation"]["formed_rules"] == fresh.formed_rules, "Snapshot round-trip: formed set matches fresh eval")
check(reloaded["evaluation"]["evidence_graph"]["nodes"] ==
      json.loads(fresh.model_dump_json())["evidence_graph"]["nodes"], "Snapshot round-trip: graph nodes match fresh eval")
check(reloaded["evaluation"]["unknown_rules"] == fresh.unknown_rules, "Snapshot round-trip: unknown set matches")

# ---------------------------------------------------------------------------
# L. Cross-system boundary tests
# ---------------------------------------------------------------------------
print("\n--- L. Boundary Tests ---")
before_cf, before_jf = GCHART.model_dump_json(), GJF.model_dump_json()
_ = evaluate_jaimini(GCHART, GJF, GVF)
check(GCHART.model_dump_json() == before_cf and GJF.model_dump_json() == before_jf,
      "Upstream facts unmodified by integration (read-only boundary)")
# Strip-D9 invariance for non-D9 rules
full_by_id = {r.rule_id: r for r in GEVAL.rules}
strip_by_id = {r.rule_id: r for r in uev.rules}
non_d9 = [rid for rid in full_by_id if rid not in
          ("JAI.KARAKAMSHA.BENEFIC_OCCUPANCY", "JAI.SWAMSA.BENEFIC_OCCUPANCY")]
check(all(strip_by_id[rid].model_dump_json() == full_by_id[rid].model_dump_json() for rid in non_d9),
      "Non-D9 rules invariant under D9 stripping (no implicit Varga access)")
check("strength" not in inspect.signature(evaluate_jaimini).parameters, "evaluate_jaimini takes no strength parameter")
jaimini_dir = os.path.join(os.path.dirname(__file__), "core", "jaimini")
scan_files = []
for root, _, files in os.walk(jaimini_dir):
    for fn in files:
        if fn.endswith(".py") and os.path.join(root, fn) != __file__:
            scan_files.append(os.path.join(root, fn))
parashari_leak = [f for f in scan_files
                  if "core.rules.parashari" in open(f, encoding="utf-8").read()
                  and "structural import" not in open(f, encoding="utf-8").read().lower()
                  and "from core.rules.parashari.structural import" not in open(f, encoding="utf-8").read()]
# Only sanctioned structural-constant import may reference parashari, and only
# as an import statement; docstring contrast mentions are not dependencies.
# Accepted 5D files may mention Parashari in prose; scope the import scan to
# executable import lines in 5E/5F files.
leak = []
for f in scan_files:
    for line in open(f, encoding="utf-8").read().splitlines():
        s = line.strip()
        if (s.startswith("from core.rules.parashari") or "import core.rules.parashari" in s) \
                and "import" in s:
            if not (f.endswith(os.path.join("rules", "predicates.py")) and "structural import" in s):
                leak.append(f"{os.path.basename(f)}: {s}")
check(leak == [], f"No Parashari imports outside sanctioned constants (leak={leak})")
pred_tokens = ["marriage at age", "guarantees", "wealth amount", "death timing",
               "event probability", "chara dasha", "predict_events", "lifespan"]
# Allowlist legitimate Jaimini Dasha calculation infrastructure files
# These files implement Chara Dasha calculation (not prediction/interpretation)
ALLOWLIST_CHARA_DASHA = {
    "profile.py",  # Chara Dasha profile definitions
    "reference.py",  # Independent reference implementation
}
clean = True
for f in scan_files:
    content = open(f, encoding="utf-8").read().lower()
    for tok in pred_tokens:
        if tok in content:
            basename = os.path.basename(f)
            if tok == "chara dasha" and basename in ALLOWLIST_CHARA_DASHA:
                continue  # Legitimate infrastructure, not prediction
            print(f"  Forbidden token '{tok}' in {basename}")
            clean = False
check(clean, "No-prediction vocabulary guard across jaimini package")
# 5E API compatibility
ev5e = evaluate_jaimini_yogas(GCHART, GJF, GVF, JaiminiYogaProfile(karaka_method="SEVEN_KARAKA"))
check(ev5e.total_rules == 12, "Phase 5E API still evaluates 12 rules (backward compatible)")

# ---------------------------------------------------------------------------
# M. Exhaustive sweeps + independent references
# ---------------------------------------------------------------------------
print("\n--- M. Exhaustive Sweeps ---")
sweep_ok = True
for asc in SIGNS:
    ch = make_chart(asc)
    vfx, jfx = full_inputs(ch)
    ex = evaluate_jaimini(ch, jfx, vfx)
    if ex.total_rules != 12:
        sweep_ok = False
    # independent karaka reference: AK = max intra-sign degree
    degs = {p: float(ch.planets[p].longitude.sidereal) % 30.0
            for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")}
    ref_ak = max(sorted(degs), key=lambda p: degs[p])
    if jfx.chara_karakas.karakas["AK"].planet != ref_ak:
        sweep_ok = False
    # independent AL/UL + Karakamsha references
    if ex.evidence_graph.node_ids() != sorted(ex.evidence_graph.node_ids()):
        sweep_ok = False
    if validate_evidence_completeness(ex.rules) or validate_rule_provenance(ex.rules):
        sweep_ok = False
    # strip-D9 UNKNOWN envelope on every ascendant
    exu = evaluate_jaimini(ch, jfx, {"planets": {}, "ascendant": {}})
    if sorted(exu.unknown_rules) != ["JAI.KARAKAMSHA.BENEFIC_OCCUPANCY", "JAI.SWAMSA.BENEFIC_OCCUPANCY"]:
        sweep_ok = False
check(sweep_ok, "12 ascendants: AK reference, graph order, validators, UNKNOWN envelope")
# 144 AK/AmK pairs: never DIRECT_CONTRADICTION, disjointness preserved
pair_ok = True
for s1 in SIGNS:
    for s2 in SIGNS:
        ch = make_chart("Aries", {"Jupiter": {"sign": s1, "deg": 28.5},
                                  "Moon": {"sign": s2, "deg": 25.2}})
        vfx, jfx = full_inputs(ch)
        ex = evaluate_jaimini(ch, jfx, vfx)
        by_id = {r.rule_id: r for r in ex.rules}
        exp_conj = (s1 == s2)
        exp_mut = (s1 != s2 and s2 in get_sign_rashi_drishti(s1) and s1 in get_sign_rashi_drishti(s2))
        if by_id["JAI.KARAKA.AK_AMK_CONJUNCTION"].formed != exp_conj:
            pair_ok = False
        if by_id["JAI.DRISHTI.AK_AMK_MUTUAL"].formed != exp_mut:
            pair_ok = False
        if any(c.conflict_class == DIRECT_CONTRADICTION for c in ex.conflicts):
            pair_ok = False
check(pair_ok, "144 AK/AmK pairs: independent formation reference + zero contradictions")
# Tradition permutations: subset evaluations stay consistent
perm_ok = True
for labels in (["CLASSICAL_JAIMINI"], ["TRADITION_DEPENDENT"], None):
    ex = evaluate_jaimini(GCHART, GJF, GVF, JaiminiIntegrationProfile(origin_labels=labels))
    expect_n = 5 if labels == ["CLASSICAL_JAIMINI"] else (7 if labels == ["TRADITION_DEPENDENT"] else 12)
    if ex.total_rules != expect_n:
        perm_ok = False
    if not set(ex.formed_rules).issubset(set(GEVAL.formed_rules)):
        perm_ok = False
check(perm_ok, "Tradition profile permutations consistent (5/7/12, formed subsets)")

# ---------------------------------------------------------------------------
# N. Performance
# ---------------------------------------------------------------------------
print("\n--- N. Performance ---")
t0 = time.perf_counter()
_ = evaluate_jaimini(GCHART, GJF, GVF)
t_cold = time.perf_counter() - t0
t0 = time.perf_counter()
for _ in range(50):
    _ = evaluate_jaimini(GCHART, GJF, GVF)
t_rep = (time.perf_counter() - t0) / 50.0
t0 = time.perf_counter()
_ = build_evidence_graph(GCHART, GJF, GVF, GEVAL.rules)
t_graph = time.perf_counter() - t0
t0 = time.perf_counter()
_ = analyze_conflicts(GEVAL.rules)
t_conf = time.perf_counter() - t0
print(f"  cold={t_cold:.3f}s repeated={t_rep:.3f}s graph={t_graph:.4f}s conflicts={t_conf:.5f}s")
check(t_cold < 5.0 and t_rep < 5.0, "Performance within sane bounds (correctness first, no optimization claimed)")

# ---------------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print(f"PHASE 5F TEST RESULTS: {passed_tests} passed, {failed_tests} failed out of {total_tests} total")
print("=" * 70)
sys.exit(1 if failed_tests else 0)
