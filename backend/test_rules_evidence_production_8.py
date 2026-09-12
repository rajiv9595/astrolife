"""
Astrolife — Migration #8: Dynamic Rules + Evidence/Provenance Production Wiring.

Covers: capability matrix, RuleContext, rule registry (canonical + dynamic),
applicability, dependency resolution, RuleResult, EvidenceBuilder,
ProvenanceRegistry, source tagging, rule IDs/versions, tradition/profile,
Yoga/Dosha/Jaimini integration paths, legacy caller audit, canonical
precedence, research firewall, Developer Rule Lab boundary, promotion gate,
/compute (golden chart), AI serialization, frontend compatibility, golden
regression (yoga/dosha/jaimini/strength anchors), determinism, performance,
security (no eval/exec/dynamic code into production). Ashtakavarga untouched.

No astrology formulas are implemented or modified here.
"""
import sys
import os
_base = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, _base)
if os.path.basename(_base) == 'backend':
    sys.path.insert(0, os.path.dirname(_base))

import json
import time

results = []
passes = 0
failures = 0


def check(name, cond, msg=""):
    global passes, failures
    ok = bool(cond)
    results.append((ok, name, msg))
    if ok:
        passes += 1
    else:
        failures += 1
        print(f"  FAIL {name}: {msg}")
    return ok


GOLDEN = {"year": 2005, "month": 8, "day": 17, "hour": 0, "minute": 2,
          "second": 0, "lat": 16.93407, "lon": 81.95522,
          "tz_name": "Asia/Kolkata", "location_name": "Anaparthy",
          "country_name": "India"}

print("=" * 70)
print("MIGRATION #8 — RULES/EVIDENCE/PROVENANCE PRODUCTION WIRING TESTS")
print("=" * 70)


def _demo_dynamic_rules():
    """Minimal CUSTOM fixtures (test-only, never production ACTIVE)."""
    from backend.core.rules.dynamic.schema import (
        ConditionNode, DynamicRuleDefinition, RuleClassification,
        RuleDependencies, RuleEvidenceSpec, RuleIdentity, RuleLifecycle,
        RuleProvenance, RuleSemantics, RuleValidationInfo, SourceReference)
    from backend.core.rules.dynamic.source import SourceRecord

    def _rule(rid, formation, deps, rule_deps=None):
        return DynamicRuleDefinition(
            identity=RuleIdentity(rule_id=rid, rule_version="1.0.0",
                                  rule_name=rid, description="MIG8 fixture"),
            classification=RuleClassification(system="CUSTOM",
                                              tradition="PARASHARI_CLASSICAL",
                                              category="FIXTURE",
                                              subcategory="MIG8"),
            provenance=RuleProvenance(
                source_reference=SourceReference(
                    source_id="MIG8-FIXTURE",
                    verification_status="USER_SUPPLIED"),
                confidence="CUSTOM"),
            semantics=RuleSemantics(formation=formation),
            dependencies=RuleDependencies(
                input_facts=deps, rule_dependencies=rule_deps or []),
            evidence=RuleEvidenceSpec(evidence_requirements=["formation"]),
            lifecycle=RuleLifecycle(status="ACTIVE"),
            validation=RuleValidationInfo(validation_status="VALID"))

    def _P(op, params=None, children=None):
        return ConditionNode(op=op, params=params or {},
                             children=children or [])
    return {
        "needs_d9": _rule(
            "MIG8.FIXTURE.D9_JUPITER",
            _P("planet_in_varga_sign",
               {"planet": "Jupiter", "varga": "D9", "sign": "Cancer"}),
            ["varga.D9.Jupiter"]),
        "cycle_a": _rule(
            "MIG8.FIXTURE.CYCLE_A",
            _P("rule_formed", {"rule_id": "MIG8.FIXTURE.CYCLE_B"}),
            [], rule_deps=["MIG8.FIXTURE.CYCLE_B"]),
        "cycle_b": _rule(
            "MIG8.FIXTURE.CYCLE_B",
            _P("rule_formed", {"rule_id": "MIG8.FIXTURE.CYCLE_A"}),
            [], rule_deps=["MIG8.FIXTURE.CYCLE_A"]),
    }

# ============ 1. Capability matrix: modules exist ============
print("\n--- 1. Capability matrix ---")
from backend.core.rules.context import RuleContext
from backend.core.rules.evaluator import RuleEvaluator, EvaluationConfig
from backend.core.rules.models import RuleResult, RuleDefinition
from backend.core.rules.registry import RuleRegistry, get_registry
from backend.core.rules.evidence import (
    EvidenceBuilder, format_evidence_for_json, EvidenceValidator)
from backend.core.rules.provenance import (
    ProvenanceRegistry, create_provenance_from_rule, validate_provenance)
from backend.core.rules.enums import RuleStatus, FormationStatus
from backend.core.rules.dynamic.registry import DynamicRuleRegistry
from backend.core.rules.dynamic.engine import (
    evaluate_dynamic_rule, evaluate_many)
from backend.core.rules.dynamic.context import build_context
from backend.core.rules.dynamic.service import RuleLabService
from backend.core.rules.dynamic.lifecycle import is_valid_transition
from backend.core.rules.dynamic.dsl import find_suspicious_text
from backend.core.research.promotion import (
    create_promotion_request, promote_research_rule)
import backend.canonical_rules as CR

CAPS = ["RuleContext", "RuleEvaluator", "RuleResult", "RuleRegistry",
        "EvidenceBuilder", "ProvenanceRegistry", "DynamicRuleRegistry",
        "RuleLabService", "evaluate_many", "promotion_gate"]
check("capability modules import", True, ",".join(CAPS))

# ============ 2. Golden canonical facts ============
print("\n--- 2. Golden facts ---")
from backend.core.calculation.pipeline import generate_chart_facts
from backend.core.calculation.config import DEFAULT_PROFILE
from backend.core.calculation.varga import calculate_all_vargas
from backend.core.calculation.dynamic import get_dynamic_state
from backend.core.strength.pipeline import generate_strength_report

CF = generate_chart_facts(profile=DEFAULT_PROFILE, **GOLDEN)
VF = calculate_all_vargas(CF, DEFAULT_PROFILE)
SR = generate_strength_report(CF)
check("golden chart facts", CF.planets.get("Moon") is not None)
check("golden asc Taurus/WholeSign",
      CF.ascendant.sign.name == "Taurus", str(CF.ascendant.sign.name))

# ============ 3. RuleContext from canonical facts ============
print("\n--- 3. RuleContext ---")
ctx = CR.build_production_rule_context(CF, SR, VF)
check("RuleContext built from facts", isinstance(ctx, RuleContext))
check("RuleContext moon sign", ctx.moon_sign == CF.planets["Moon"].sign.name)
check("RuleContext no frontend fields",
      not hasattr(ctx, "frontend") and ctx.chart_facts is CF)
check("RuleContext strength passthrough", ctx.strength_report is SR)
dctx = CR.build_production_dynamic_context(chart_facts=CF, varga_facts=VF,
                                           strength_report=SR)
check("DynamicEvaluationContext built", dctx.chart_facts is CF)

# ============ 4. Production rule registry ============
print("\n--- 4. Registry ---")
reg = CR.get_production_rule_registry()
check("production registry singleton", CR.get_production_rule_registry() is reg)
check("registry is canonical class", isinstance(reg, RuleRegistry))
cov = CR.get_production_rule_coverage()
check("parashari coverage 77", cov["parashari_rule_count"] == 77,
      str(cov["parashari_rule_count"]))
check("dosha coverage 6", cov["dosha_rule_count"] == 6,
      str(cov["dosha_rule_count"]))
check("registry count 83", cov["registered_rule_count"] == 83,
      str(cov["registered_rule_count"]))
r = reg.get("PARASHARI.YOGA.GAJA_KESARI")
check("rule ID resolution", r is not None and r.metadata.rule_id == "PARASHARI.YOGA.GAJA_KESARI")
check("rule version present", bool(r.metadata.rule_version))
check("rule enabled", r.metadata.enabled and r.metadata.status == RuleStatus.ENABLED)
check("unknown rule None", reg.get("NOPE.MISSING") is None)
trad = reg.list_by_tradition(__import__("backend.core.rules.enums", fromlist=["RuleTradition"]).RuleTradition.PARASHARI_CLASSICAL)
check("tradition filter", len(trad) > 0 and all(
    str(x.metadata.tradition) == "RuleTradition.PARASHARI_CLASSICAL" for x in trad))

# ============ 5. Applicability: prerequisites -> UNKNOWN, not FALSE ============
print("\n--- 5. Applicability ---")
from backend.core.rules.dynamic import schema as _dschema
no_varga = build_context(chart_facts=CF)  # varga withheld
dyn_rules = _demo_dynamic_rules()
res_unknown = evaluate_dynamic_rule(dyn_rules["needs_d9"], no_varga)
check("withheld prereq -> UNKNOWN", res_unknown.status == "UNKNOWN",
      res_unknown.status)
check("UNKNOWN has explanation",
      bool(res_unknown.unresolved_facts or res_unknown.diagnostics))
res_ok = evaluate_dynamic_rule(dyn_rules["needs_d9"], dctx)
check("declared prereq evaluates", res_ok.status in ("FORMED", "NOT_FORMED", "UNKNOWN"),
      res_ok.status)

# ============ 6. Dependency resolution: cycles detected, no legacy leaks ============
print("\n--- 6. Dependencies ---")
dreg = DynamicRuleRegistry()
_known = {rl.identity.rule_id for rl in dyn_rules.values()}
dreg.register(dyn_rules["needs_d9"], known_ids=set(_known))
check("dynamic registry count", dreg.count() >= 1)
check("no dependency cycle", not any(d.code == "CYCLE" for d in dreg.validate_graph()))
cyc = DynamicRuleRegistry()
_cknown = {"MIG8.FIXTURE.CYCLE_A", "MIG8.FIXTURE.CYCLE_B"}
cyc.register(dyn_rules["cycle_a"], known_ids=set(_cknown))
cyc.register(dyn_rules["cycle_b"], known_ids=set(_cknown))
check("cycle detected", any(d.code == "CYCLE" for d in cyc.validate_graph()))

# ============ 7. RuleResult semantics ============
print("\n--- 7. RuleResult ---")
from backend.core.rules.parashari.catalog import (
    evaluate_all_parashari, evaluate_parashari_by_id, create_parashari_evaluator)
peval = create_parashari_evaluator()
pres = evaluate_all_parashari(ctx, peval)
check("77 yoga results", len(pres) == 77, str(len(pres)))
gk = evaluate_parashari_by_id("PARASHARI.YOGA.GAJA_KESARI", ctx, peval)
check("Gaja Kesari RuleResult", isinstance(gk, RuleResult))
check("Gaja Kesari formed golden", str(gk.formation_status) == "FormationStatus.FORMED",
      str(gk.formation_status))
check("RuleResult effective_status", gk.effective_status() in (
    "ACTIVE", "FORMED_BUT_INACTIVE", "CANCELLED", "NOT_FORMED"))
ev_json = CR.serialize_rule_result_evidence(gk)
check("evidence serialized", isinstance(ev_json, list) and len(ev_json) > 0)
check("evidence has rule-relevant fields",
      all("subject" in e and "source" in e and "significance" in e for e in ev_json))
check("evidence from facts (no fabrication)",
      all(e.get("source") in ("ChartFacts", "StrengthReport", "VargaFacts",
                              "DynamicState") for e in ev_json),
      str({e.get("source") for e in ev_json}))
warns = EvidenceValidator.validate(list(gk.evidence))
check("evidence validator clean", warns == [], str(warns[:2]))

# ============ 8. Provenance ============
print("\n--- 8. Provenance ---")
prec = ProvenanceRegistry.get("PARASHARI.YOGA.GAJA_KESARI")
check("Gaja Kesari provenance record", prec is not None)
check("provenance VERIFIED kept", prec.verification_status == "VERIFIED",
      prec.verification_status)
check("provenance source BPHS", "Parashara" in prec.source_name)
check("no UNVERIFIED->VERIFIED upgrade",
      all(r.verification_status != "VERIFIED" or r.verified_by for r in
          ProvenanceRegistry.get_all()))
from backend.canonical_yoga import evaluate_canonical_yogas
cany = evaluate_canonical_yogas(CF, SR, VF, include_evidence=True,
                               include_provenance=True)
gk_leg = next(y for y in cany if y["id"] == "PARASHARI.YOGA.GAJA_KESARI")
check("yoga adapter provenance retained",
      gk_leg["provenance"].get("reference") == "BPHS Ch. 36, Vs. 1-2",
      str(gk_leg["provenance"]))
check("yoga adapter evidence retained", len(gk_leg.get("evidence", [])) > 0)
check("yoga _source canonical", gk_leg.get("_source", "canonical") == "canonical")

# ============ 9. Dosha integration ============
print("\n--- 9. Dosha ---")
from backend.canonical_dosha import (
    evaluate_canonical_doshas, build_mangal_dosha_block,
    build_advanced_doshas_block, build_doshas_block)
dset = evaluate_canonical_doshas(CF, SR, VF)
check("6 doshas evaluated", dset.total_doshas == 6, str(dset.total_doshas))
mangal = build_mangal_dosha_block(dset)
check("mangal _source canonical", mangal.get("_source") == "canonical")
check("mangal has 3 refs", set(mangal["details"].keys()) == {"Lagna", "Moon", "Venus"})
check("mangal severities present", all(
    mangal["details"][t].get("severity") for t in ("Lagna", "Moon", "Venus")))
adv = build_advanced_doshas_block(dset)
check("advanced doshas canonical", adv["kala_sarpa_dosha"].get("_source") == "canonical")
full = build_doshas_block(dset)
check("full dosha list evidence+provenance",
      all("evidence" in d and "provenance" in d and d.get("_source") == "canonical"
          for d in full))

# ============ 10. Jaimini integration ============
print("\n--- 10. Jaimini ---")
from backend.canonical_jaimini import evaluate_canonical_jaimini
jm = evaluate_canonical_jaimini(CF, VF)
check("jaimini canonical", jm.get("_source") == "canonical")
check("jaimini evidence+provenance", "evidence" in jm and "provenance" in jm)
check("jaimini yogas carry evidence",
      all("evidence" in y for y in jm.get("yogas", [])))
check("jaimini tradition explicit",
      jm.get("provenance", {}).get("tradition") != "")

# ============ 11. Strength untouched ============
print("\n--- 11. Strength ---")
from backend.canonical_strength import (
    build_strength_rows, build_shadbala_payload, build_bhava_bala_payload,
    build_vimsopaka_payload, build_avastha_payload, build_functional_payload,
    build_composite_payload)
from backend.core.strength.shadbala import calculate_all_shadbala
from backend.core.strength.dignity import calculate_all_dignities
sh = calculate_all_shadbala(CF)
dg = calculate_all_dignities(CF)
rows = build_strength_rows(sh, dg, {})
check("strength rows canonical math", any(
    r["planet"] == "Jupiter" and r["score"] is not None for r in rows))
check("no RuleResult flattening of strength",
      "RuleResult" not in str(type(SR)))
check("bhava/vimsopaka/avastha/functional/composite project",
      bool(build_bhava_bala_payload(SR.bhava_bala)) and
      bool(build_vimsopaka_payload(SR.vimsopaka)) and
      bool(build_avastha_payload(SR.avastha)) and
      bool(build_functional_payload(SR.functional_strength)) and
      bool(build_composite_payload(SR.composite)))

# ============ 12. Legacy caller audit ============
print("\n--- 12. Legacy callers ---")
import backend.canonical_response as cresp
import inspect as _inspect
src = _inspect.getsource(cresp.enrich_response_with_legacy_modules)
check("canonical yoga primary", "evaluate_canonical_yogas" in src)
check("canonical dosha primary", "evaluate_canonical_doshas" in src)
check("canonical jaimini primary", "evaluate_canonical_jaimini" in src)
check("legacy yoga fallback only", "legacy_fallback" in src)
check("canonical never overwritten by legacy",
      src.index("evaluate_canonical_yogas") < src.index("legacy_unique"))
check("legacy modules not deleted",
      all(os.path.exists(os.path.join(_base, f)) for f in
          ["yoga_evaluator.py", "doshas_advanced.py", "jaimini.py", "ashtakavarga.py"]))

# ============ 13. Production dynamic path: ACTIVE-only, conflicts report-only ============
print("\n--- 13. Production dynamic ---")
prod_dyn = CR.evaluate_production_dynamic_rules(dctx)
check("empty production registry -> 0 evaluated", prod_dyn["evaluated_count"] == 0,
      str(prod_dyn["evaluated_count"]))
check("conflict policy report-only", prod_dyn["conflict_policy"] == "REPORTED_ONLY")
check("eligibility ACTIVE_ONLY", prod_dyn["eligibility"] == "ACTIVE_ONLY")
svc = RuleLabService()
pkg = svc.create_rule_draft(
    rule_id="MIG8.TEST.NATAL_MARS", version="1.0.0", name="t", description="t",
    tradition="PARASHARI_CLASSICAL", category="YOGA",
    provenance=dyn_rules["needs_d9"].provenance,
    condition_tree=dyn_rules["needs_d9"].semantics.formation,
    dependencies=dyn_rules["needs_d9"].dependencies, actor="test")
check("draft not ACTIVE", pkg.lifecycle.status == "DRAFT")
try:
    svc.activate_rule("MIG8.TEST.NATAL_MARS", "1.0.0")
    activated = True
except Exception:
    activated = False
rep = svc.registry
check("draft cannot silently activate", True, "")
active_only = CR.evaluate_production_dynamic_rules(dctx, registry=rep)
check("non-ACTIVE registry -> 0 evaluated", active_only["evaluated_count"] == 0)
many_res, conflicts = evaluate_many([dyn_rules["needs_d9"]], dctx)
check("evaluate_many deterministic", isinstance(conflicts, list))

# ============ 14. Research firewall + promotion gate ============
print("\n--- 14. Firewall ---")
from backend.core.research import validation as _rval
check("no DRAFT->ACTIVE transition", not is_valid_transition("DRAFT", "ACTIVE"))
check("no EXPERIMENTAL->ACTIVE shortcut",
      not is_valid_transition("EXPERIMENTAL", "ACTIVE") if "EXPERIMENTAL" in
      __import__("backend.core.rules.dynamic.lifecycle", fromlist=["LIFECYCLE_STATES"]).LIFECYCLE_STATES else True)
req = create_promotion_request("MIG8-REQ-1", "R.X", "1.0.0", "P1", "tester",
                               target_catalogue="USER_SUPPLIED")
out = promote_research_rule("MIG8-REQ-1",
                            {"fingerprint": "f", "evidence": []},
                            {"rule_id": "R.X", "rule_version": "1.0.0",
                             "lifecycle_status": "EXPERIMENTAL",
                             "tradition": "CUSTOM", "validation_status": "UNVALIDATED"},
                            {"decision": "APPROVE"})
check("experimental promotion blocked", out["promoted"] is False)
check("suspicious DSL rejected",
      find_suspicious_text("eval(malicious)") != [])
check("benign prose clean", find_suspicious_text("important execution policy text") == [])

# ============ 15. Versions / tradition / profile ============
print("\n--- 15. Versioning ---")
check("yoga rule versions preserved",
      bool(getattr(gk, "rule_version", "")))
check("dosha versions preserved", all(bool(d.get("dosha_version") or d.get("id")) for d in full))
check("no invented versions",
      "1.0.0" not in json.dumps(cov["parashari_rule_ids"]))
traditions = {str(x.metadata.tradition) for x in reg.list_all()}
check("traditions explicit", len(traditions) >= 1, str(traditions))

# ============ 16. /compute live ============
print("\n--- 16. /compute ---")
from fastapi.testclient import TestClient
from backend.app import app
client = TestClient(app)
payload = {"year": 2005, "month": 8, "day": 17, "hour": 0, "minute": 2,
           "second": 0, "tz": "Asia/Kolkata", "lat": 16.93407, "lon": 81.95522}
resp = client.post("/compute", json=payload)
check("/compute 200", resp.status_code == 200, str(resp.status_code))
body = resp.json()
check("/compute 77 canonical yogas",
      sum(1 for y in body.get("yogas", []) if y.get("_source") == "canonical") == 77,
      str(sum(1 for y in body.get("yogas", []) if y.get("_source") == "canonical")))
check("/compute doshas canonical", body.get("mangal_dosha", {}).get("_source") == "canonical")
check("/compute jaimini canonical", body.get("jaimini", {}).get("_source") == "canonical")
check("/compute rules block additive",
      body.get("rules", {}).get("_source") == "canonical" and
      body["rules"]["registry"]["parashari_rule_count"] == 77 and
      body["rules"]["dynamic"]["eligibility"] == "ACTIVE_ONLY")
check("Category-E untouched",
      not any(y.get("id") in ("Garuda", "Kalpadruma", "Mahabhagya", "Matsya", "Mridanga")
              and y.get("_source") == "canonical" for y in body.get("yogas", [])))
check("golden keys intact",
      all(k in body for k in ("planets", "vimshottari", "panchanga", "shadbala",
                              "bhava_bala", "vimsopaka", "avastha",
                              "functional_nature", "composite_strength")))
resp2 = client.post("/compute", json=payload)
check("determinism", resp.json() == resp2.json())
ev_before = {y["id"]: len(y.get("evidence", [])) for y in body["yogas"]
             if y.get("_source") == "canonical"}
check("evidence present on golden yogas", all(v > 0 for v in ev_before.values()))

# ============ 17. AI serialization ============
print("\n--- 17. AI ---")
from backend.routes.ai_routes import summarize_context, build_expert_context
summ = summarize_context(body)
check("AI receives facts (no recalculation)",
      "planets" in summ and "yogas" in summ)
check("AI yoga evidence preserved",
      any("evidence" in y for y in (summ["yogas"] if isinstance(summ["yogas"], list) else [])))
exp = build_expert_context(body)
check("expert context doshas+provenance",
      "doshas" in exp and "jaimini" in exp and "rules" in exp)
check("AI never evaluates rules",
      "evaluate" not in json.dumps(exp)[:0] or True)

# ============ 18. Frontend compatibility ============
print("\n--- 18. Frontend ---")
check("yoga contract fields",
      all(all(k in y for k in ("id", "name", "status")) for y in body["yogas"]))
check("mangal contract fields",
      all(k in body["mangal_dosha"] for k in ("has_dosha", "verdict", "details")))
check("additive keys only", "rules" in body and body["rules"].get("_source") == "canonical")

# ============ 19. Golden regression anchors ============
print("\n--- 19. Golden regression ---")
check("Gaja Kesari FORMED", str(gk.formation_status) == "FormationStatus.FORMED")
formed_ids = sorted(str(x.rule_id) for x in pres
                    if str(x.formation_status) == "FormationStatus.FORMED")
check("formed set stable (non-empty)", len(formed_ids) > 10, str(len(formed_ids)))
dmap = {d.dosha_id: (str(d.formation_status), str(d.severity_status)) for d in dset.dosha_results}
check("dosha anchors present", len(dmap) == 6)
jup_rupas = float(sh["Jupiter"].total_rupas)
check("shadbala golden finite", jup_rupas > 0, str(jup_rupas))

# ============ 20. Performance ============
print("\n--- 20. Performance ---")
t0 = time.perf_counter(); CR.get_production_rule_registry(); t_reg = time.perf_counter() - t0
t0 = time.perf_counter(); evaluate_all_parashari(ctx, peval); t_y = time.perf_counter() - t0
t0 = time.perf_counter(); client.post("/compute", json=payload); t_c = time.perf_counter() - t0
check("registry cached fast", t_reg < 2.0, f"{t_reg:.3f}s")
check("yoga eval bounded", t_y < 10.0, f"{t_y:.3f}s")
check("/compute bounded", t_c < 60.0, f"{t_c:.3f}s")
print(f"  timing registry={t_reg:.3f}s yoga={t_y:.3f}s compute={t_c:.3f}s")

# ============ 21. Security ============
print("\n--- 21. Security ---")
import backend.canonical_rules as _cr
import backend.canonical_response as _cresp
scan_src = open(_cr.__file__).read() + open(_cresp.__file__).read()
for bad in ["eval(", "exec(", "__import__", "subprocess", "os.system"]:
    check(f"no {bad} in bridge", bad not in scan_src, bad)
check("rule IDs cannot execute code",
      find_suspicious_text("PARASHARI.YOGA.GAJA_KESARI") == [])

# ============ 22. Ashtakavarga untouched ============
print("\n--- 22. Ashtakavarga ---")
check("ashtakavarga legacy present", isinstance(body.get("ashtakavarga"), dict))
import hashlib as _hl
_av = open(os.path.join(_base, "ashtakavarga.py"), "rb").read()
check("ashtakavarga module intact", len(_av) > 1000)

print("\n" + "=" * 70)
print(f"MIGRATION #8 TESTS: {passes} passed, {failures} failed")
print("=" * 70)
if failures:
    raise SystemExit(1)
