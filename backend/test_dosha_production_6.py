"""
Astrolife — Migration #6: Canonical Dosha Production Wiring tests.

Covers: capability inventory, canonical source, all 6 canonical doshas,
Mangal Dosha (golden + negatives + partial-cancellation semantics), statuses,
cancellation/mitigation layer usage, evidence, provenance, adapter contract,
canonical precedence, legacy fallback tagging, auth/anonymous, /compute, AI
context, JSON serialization, determinism, performance, Category-E audit
(no implementation). No canonical formula is modified.
"""
import sys
import os
_base = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, _base)
if os.path.basename(_base) == 'backend':
    sys.path.insert(0, os.path.dirname(_base))

from core.rules.doshas.catalog import (
    build_dosha_catalog, evaluate_all_doshas, evaluate_dosha_by_id,
    create_dosha_evaluator, DOSHA_RULE_IDS,
)
from core.rules.context import RuleContext
from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DEFAULT_PROFILE
from core.calculation.varga import calculate_all_vargas
from core.strength.pipeline import generate_strength_report

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
print("MIGRATION #6 — CANONICAL DOSHA PRODUCTION WIRING TESTS")
print("=" * 70)


def golden_ctx():
    cf = generate_chart_facts(profile=DEFAULT_PROFILE, **GOLDEN)
    return cf, RuleContext(
        chart_facts=cf,
        strength_report=generate_strength_report(cf),
        varga_facts=calculate_all_vargas(cf, DEFAULT_PROFILE))


CF, CTX = golden_ctx()
EVAL = create_dosha_evaluator()

# ============ 1. Capability inventory ============
print("\n--- 1. Inventory ---")
EXPECTED_IDS = ["DOSHA.MANGLIK.LAGNA_CLASSICAL", "DOSHA.MANGLIK.MOON_REFERENCE",
                "DOSHA.MANGLIK.VENUS_REFERENCE", "DOSHA.KEMADRUMA.CLASSICAL",
                "DOSHA.KALA_SARPA.SIGN_BASED", "DOSHA.PITRU.MODERN_COMMON"]
check("6 canonical dosha rules", DOSHA_RULE_IDS == EXPECTED_IDS,
      str(DOSHA_RULE_IDS))
check("catalog builds 6", len(build_dosha_catalog()) == 6)
check("manglik 3 references", sum("MANGLIK" in i for i in DOSHA_RULE_IDS) == 3)
check("no Category E yoga IDs in dosha catalogue",
      not any("GARUDA" in i or "MRIDANGA" in i for i in DOSHA_RULE_IDS))

# ============ 2. Golden statuses ============
print("\n--- 2. Golden ---")
GOLD = {"DOSHA.MANGLIK.LAGNA_CLASSICAL": ("FORMED", "LOW", "NONE", "PARTIAL"),
        "DOSHA.MANGLIK.MOON_REFERENCE": ("NOT_FORMED", "NONE", "NONE", "NONE"),
        "DOSHA.MANGLIK.VENUS_REFERENCE": ("FORMED", "LOW", "NONE", "PARTIAL"),
        "DOSHA.KEMADRUMA.CLASSICAL": ("NOT_FORMED", "NONE", "NONE", "NONE"),
        "DOSHA.KALA_SARPA.SIGN_BASED": ("NOT_FORMED", "NONE", "NONE", "NONE"),
        "DOSHA.PITRU.MODERN_COMMON": ("NOT_FORMED", "NONE", "NONE", "NONE")}
dset = evaluate_all_doshas(CTX, EVAL)
check("dosha set total 6", dset.total_doshas == 6)
by_id = {r.dosha_id: r for r in dset.dosha_results}
for rid, (form, sev, canc, mitig) in GOLD.items():
    r = by_id[rid]
    check(f"golden {rid.split('.')[-1]} {form}/{sev}/{canc}/{mitig}",
          str(r.formation_status).split(".")[-1] == form and
          str(r.severity_status).split(".")[-1] == sev and
          str(r.cancellation_status).split(".")[-1] == canc and
          str(r.mitigation_status).split(".")[-1] == mitig,
          f"{r.formation_status}/{r.severity_status}/{r.cancellation_status}/{r.mitigation_status}")
    check(f"golden {rid.split('.')[-1]} evidence>=1", len(r.evidence) >= 1)
    check(f"golden {rid.split('.')[-1]} activation NOT_EVALUATED",
          str(r.activation_status).endswith("NOT_EVALUATED"))

# ============ 3. Mangal negatives / variants ============
print("\n--- 3. Mangal variants ---")
from backend.core.rules.parashari.fixtures import make_synthetic_context


def synth_dosha(rid, asc, placements):
    tctx = make_synthetic_context(asc, placements)
    tcf = tctx.chart_facts
    tctx2 = RuleContext(
        chart_facts=tcf, strength_report=generate_strength_report(tcf),
        varga_facts=calculate_all_vargas(tcf, DEFAULT_PROFILE))
    return evaluate_dosha_by_id(rid, tctx2, EVAL)


r = synth_dosha("DOSHA.MANGLIK.LAGNA_CLASSICAL", "Taurus",
               {"Mars": "Taurus"})
check("mangal lagna FORMED Mars in 1st (dosha house)",
      str(r.formation_status).split(".")[-1] == "FORMED")
r = synth_dosha("DOSHA.MANGLIK.LAGNA_CLASSICAL", "Taurus",
               {"Mars": "Gemini"})
check("mangal lagna FORMED Mars in 2nd (dosha house)",
      str(r.formation_status).split(".")[-1] == "FORMED")
r = synth_dosha("DOSHA.MANGLIK.LAGNA_CLASSICAL", "Aries",
               {"Mars": "Leo"})
check("mangal lagna NOT_FORMED Mars 5th (non-dosha)",
      str(r.formation_status).split(".")[-1] == "NOT_FORMED")
r = synth_dosha("DOSHA.MANGLIK.MOON_REFERENCE", "Aries",
               {"Moon": "Aries", "Mars": "Scorpio"})
check("mangal moon FORMED Mars 8th from Moon",
      str(r.formation_status).split(".")[-1] == "FORMED")
# partial cancellation path: Mars+Jupiter conjunction is PARTIAL by design
r = synth_dosha("DOSHA.MANGLIK.LAGNA_CLASSICAL", "Taurus",
               {"Mars": "Leo", "Jupiter": "Leo"})
check("mangal conjunction cancellation PARTIAL by design (never FULL)",
      str(r.cancellation_status).split(".")[-1] == "PARTIAL")
check("manglik never FULL-cancelled (disputed rules partial only)",
      str(r.cancellation_status).split(".")[-1] != "FULL")

# ============ 4. Kala Sarpa positive + Pitru positive ============
print("\n--- 4. Kala Sarpa / Pitru ---")
r = synth_dosha("DOSHA.KALA_SARPA.SIGN_BASED", "Aries",
               {"Sun": "Taurus", "Moon": "Gemini", "Mars": "Cancer",
                "Mercury": "Leo", "Jupiter": "Virgo", "Venus": "Taurus",
                "Saturn": "Gemini", "Rahu": "Aries", "Ketu": "Libra"})
check("kala sarpa FORMED when contained",
      str(r.formation_status).split(".")[-1] == "FORMED")
STD_BASE = {"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries",
            "Mercury": "Gemini", "Jupiter": "Sagittarius",
            "Venus": "Libra", "Saturn": "Capricorn"}
_pitru_pl = dict(STD_BASE)
_pitru_pl.update({"Mars": "Scorpio", "Rahu": "Capricorn", "Ketu": "Cancer"})
r = synth_dosha("DOSHA.PITRU.MODERN_COMMON", "Cancer", _pitru_pl)
check("pitru FORMED case", str(r.formation_status).split(".")[-1] == "FORMED")

# ============ 5. Adapter ============
print("\n--- 5. Adapter ---")
from backend.canonical_dosha import (
    evaluate_canonical_doshas, build_mangal_dosha_block,
    build_advanced_doshas_block, build_doshas_block,
    MANGLIK_REF_IDS,
)
VF = calculate_all_vargas(CF, DEFAULT_PROFILE)
SR = generate_strength_report(CF)
dset2 = evaluate_canonical_doshas(CF, SR, VF)
check("adapter evaluates 6", dset2.total_doshas == 6)
mangal = build_mangal_dosha_block(dset2)
check("mangal has_dosha True (golden)", mangal["has_dosha"] is True)
check("mangal verdict LOW (golden severity verbatim)", mangal["verdict"] == "LOW")
check("mangal Lagna present house 12",
      mangal["details"]["Lagna"]["is_present"] is True and
      mangal["details"]["Lagna"]["house"] == 12)
check("mangal Moon absent house 5",
      mangal["details"]["Moon"]["is_present"] is False and
      mangal["details"]["Moon"]["house"] == 5)
check("mangal Venus present house 8",
      mangal["details"]["Venus"]["is_present"] is True and
      mangal["details"]["Venus"]["house"] == 8)
check("mangal no false Cancelled (partial-only design)",
      mangal["verdict"] != "Cancelled")
check("mangal _source canonical", mangal["_source"] == "canonical")
check("mangal card keys",
      set(("has_dosha", "verdict", "details", "cancellations_found")).issubset(mangal.keys()))
adv = build_advanced_doshas_block(dset2)
check("advanced kala shape",
      set(("has_dosha", "verdict", "details")).issubset(adv["kala_sarpa_dosha"].keys()))
check("advanced pitru reasons key",
      "reasons" in adv["pitru_dosha"])
check("advanced golden both inactive",
      adv["kala_sarpa_dosha"]["has_dosha"] is False and
      adv["pitru_dosha"]["has_dosha"] is False)
check("advanced verdicts legacy vocabulary",
      adv["kala_sarpa_dosha"]["verdict"] == "No Dosha" and
      adv["pitru_dosha"]["verdict"] == "No Dosha")
check("advanced _source canonical",
      adv["kala_sarpa_dosha"]["_source"] == "canonical" and
      adv["pitru_dosha"]["_source"] == "canonical")
dl = build_doshas_block(dset2)
check("doshas list 6 with statuses",
      len(dl) == 6 and all("formation" in d and "severity" in d and
                           "cancellation" in d and "mitigation" in d and
                           "evidence" in d and "provenance" in d for d in dl))
check("doshas _source canonical", all(d["_source"] == "canonical" for d in dl))
check("doshas provenance present",
      all(bool(d["provenance"].get("source_name")) for d in dl))
import json as _json
try:
    _json.dumps({"mangal": mangal, "adv": adv, "doshas": dl})
    check("dosha blocks JSON-serializable", True)
except TypeError as ex:
    check("dosha blocks JSON-serializable", False, str(ex))
# verdict-branch unit coverage with stubs (no engine invention)
from types import SimpleNamespace


def _stub_set(states):
    """states: list of (tab, formed, cancelled, severity)."""
    results = []
    for tab, formed, cancelled, sev in states:
        results.append(SimpleNamespace(
            dosha_id=MANGLIK_REF_IDS[tab],
            is_formed=lambda f=formed: f,
            is_cancelled=lambda c=cancelled: c,
            severity_status=sev, mitigation_status="NONE", evidence=[]))
    return SimpleNamespace(dosha_results=results)


stub_none = _stub_set([("Lagna", False, False, "NONE"),
                       ("Moon", False, False, "NONE"),
                       ("Venus", False, False, "NONE")])
check("verdict No Dosha when none formed",
      build_mangal_dosha_block(stub_none)["verdict"] == "No Dosha" and
      build_mangal_dosha_block(stub_none)["has_dosha"] is False)
stub_cancel = _stub_set([("Lagna", True, True, "LOW"),
                         ("Moon", False, False, "NONE"),
                         ("Venus", False, False, "NONE")])
check("verdict Cancelled when all formed FULL-cancelled",
      build_mangal_dosha_block(stub_cancel)["verdict"] == "Cancelled" and
      build_mangal_dosha_block(stub_cancel)["has_dosha"] is False)
stub_mix = _stub_set([("Lagna", True, False, "HIGH"),
                      ("Moon", True, False, "LOW"),
                      ("Venus", False, False, "NONE")])
check("verdict max severity among active",
      build_mangal_dosha_block(stub_mix)["verdict"] == "HIGH")

# ============ 6. Crosscheck canonical vs legacy ============
print("\n--- 6. Crosscheck ---")
from backend.doshas_advanced import compute_advanced_doshas
planets = {n: {"sign_manual": p.sign.name} for n, p in CF.planets.items()}
leg = compute_advanced_doshas(planets, CF.ascendant.sign.name)
check("golden kala MATCH (both inactive)",
      adv["kala_sarpa_dosha"]["has_dosha"] == leg["kala_sarpa_dosha"]["has_dosha"])
check("golden pitru MATCH (both inactive)",
      adv["pitru_dosha"]["has_dosha"] == leg["pitru_dosha"]["has_dosha"])
sweep = [(("Aries", {}), ("Taurus", {}),
          ("Cancer", {"Mars": "Scorpio", "Rahu": "Capricorn", "Ketu": "Cancer"}),
          ("Aries", {"Sun": "Taurus", "Moon": "Gemini", "Mars": "Cancer",
                     "Mercury": "Leo", "Jupiter": "Virgo", "Venus": "Taurus",
                     "Saturn": "Gemini", "Rahu": "Aries", "Ketu": "Libra"}))]
STD = {"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries", "Mercury": "Gemini",
       "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Capricorn"}
match = tot = 0
for asc, pl in sweep[0]:
    base = dict(STD)
    base.update(pl)
    tctx = make_synthetic_context(asc, base)
    tcf = tctx.chart_facts
    tds = evaluate_canonical_doshas(
        tcf, generate_strength_report(tcf),
        calculate_all_vargas(tcf, DEFAULT_PROFILE))
    tad = build_advanced_doshas_block(tds)
    tleg = compute_advanced_doshas(
        {n: {"sign_manual": p.sign.name} for n, p in tcf.planets.items()},
        tcf.ascendant.sign.name)
    for key in ("kala_sarpa_dosha", "pitru_dosha"):
        tot += 1
        if tad[key]["has_dosha"] == tleg[key]["has_dosha"]:
            match += 1
        else:
            print(f"  DIFF {asc} {pl} {key}: canon={tad[key]['has_dosha']} legacy={tleg[key]['has_dosha']}")
check("sweep canonical-vs-legacy MATCH", match == tot, f"{match}/{tot}")

# ============ 7. Production wiring ============
print("\n--- 7. Production ---")
from backend.canonical_response import (
    build_canonical_compute_response, enrich_response_with_legacy_modules)
REQ = {"year": 2005, "month": 8, "day": 17, "hour": 0, "minute": 2,
       "second": 0, "lat": 16.93407, "lon": 81.95522, "tz": "Asia/Kolkata"}
resp = enrich_response_with_legacy_modules(
    build_canonical_compute_response(CF, VF, REQ, current_user=object()),
    CF, REQ, current_user=object())
check("production mangal_dosha present (not dropped)",
      isinstance(resp.get("mangal_dosha"), dict) and
      resp["mangal_dosha"].get("has_dosha") is True)
check("production mangal verdict LOW",
      resp["mangal_dosha"].get("verdict") == "LOW")
check("production mangal _source canonical",
      resp["mangal_dosha"].get("_source") == "canonical")
check("production advanced_doshas canonical",
      resp["advanced_doshas"]["kala_sarpa_dosha"].get("_source") == "canonical")
check("production doshas list 6",
      isinstance(resp.get("doshas"), list) and len(resp["doshas"]) == 6)
check("production yogas intact (82)", len(resp.get("yogas", [])) == 82)
check("production jaimini canonical",
      resp.get("jaimini", {}).get("_source") == "canonical")
check("production strengths intact",
      abs(float(resp["shadbala"]["Sun"]["total_rupas"]) - 6.18) < 0.02)
resp_anon = enrich_response_with_legacy_modules(
    build_canonical_compute_response(CF, VF, REQ, current_user=None),
    CF, REQ, current_user=None)
check("anonymous mangal_dosha present (no auth change)",
      isinstance(resp_anon.get("mangal_dosha"), dict) and
      resp_anon["mangal_dosha"].get("_source") == "canonical")
check("anonymous advanced_doshas canonical",
      resp_anon["advanced_doshas"]["kala_sarpa_dosha"].get("_source") == "canonical")
# legacy cannot override: break legacy, production intact
import backend.doshas_advanced as _legmod
_orig = _legmod.compute_advanced_doshas


def _boom(*a, **k):
    raise RuntimeError("legacy must not be called")


_legmod.compute_advanced_doshas = _boom
try:
    resp2 = enrich_response_with_legacy_modules(
        build_canonical_compute_response(CF, VF, REQ, current_user=object()),
        CF, REQ, current_user=object())
    check("legacy outage does not break production",
          resp2["mangal_dosha"].get("_source") == "canonical" and
          resp2["advanced_doshas"]["kala_sarpa_dosha"].get("_source") == "canonical")
finally:
    _legmod.compute_advanced_doshas = _orig
# rollback: canonical failure -> tagged legacy fallback
import backend.canonical_dosha as _cd
_orig_ev = _cd.evaluate_canonical_doshas


def _fail(*a, **k):
    raise RuntimeError("simulated canonical failure")


_cd.evaluate_canonical_doshas = _fail
try:
    resp3 = enrich_response_with_legacy_modules(
        build_canonical_compute_response(CF, VF, REQ, current_user=object()),
        CF, REQ, current_user=object())
    check("rollback advanced tagged legacy_fallback",
          resp3["advanced_doshas"].get("_source") == "legacy_fallback")
    check("rollback mangal empty, doshas empty",
          resp3["mangal_dosha"] == {} and resp3["doshas"] == [])
finally:
    _cd.evaluate_canonical_doshas = _orig_ev
resp4 = enrich_response_with_legacy_modules(
    build_canonical_compute_response(CF, VF, REQ, current_user=object()),
    CF, REQ, current_user=object())
check("runtime determinism (dosha blocks)",
      _json.dumps(resp["mangal_dosha"], sort_keys=True, default=str) ==
      _json.dumps(resp4["mangal_dosha"], sort_keys=True, default=str) and
      _json.dumps(resp["advanced_doshas"], sort_keys=True, default=str) ==
      _json.dumps(resp4["advanced_doshas"], sort_keys=True, default=str) and
      _json.dumps(resp["doshas"], sort_keys=True, default=str) ==
      _json.dumps(resp4["doshas"], sort_keys=True, default=str))
try:
    _json.dumps({"m": resp["mangal_dosha"], "a": resp["advanced_doshas"],
                 "d": resp["doshas"]})
    check("runtime dosha JSON-serializable", True)
except TypeError as ex:
    check("runtime dosha JSON-serializable", False, str(ex))

# ============ 8. AI + frontend contract ============
print("\n--- 8. AI/frontend ---")
ai_src = open(os.path.join(_base, "routes", "ai_routes.py"), encoding="utf-8").read()
check("AI passthrough has mangal_dosha", '"mangal_dosha"' in ai_src)
check("AI passthrough has doshas", '"doshas"' in ai_src)
check("AI no-recalculation instruction",
      "Do not perform new calculations; interpret the provided ones" in ai_src)
horo = open(os.path.join(_base, "..", "frontend", "src", "pages",
                         "HoroscopePage.jsx"), encoding="utf-8").read()
check("frontend MangalDoshaCard wired to chartData.mangal_dosha",
      "chartData.mangal_dosha" in horo)
check("frontend AdvancedDoshasCard wired", "chartData.advanced_doshas" in horo)
check("frontend card keys compatible",
      set(("has_dosha", "verdict", "details")).issubset(mangal.keys()) and
      set(("has_dosha", "verdict", "details")).issubset(
          adv["kala_sarpa_dosha"].keys()))

# ============ 9. Adapter hygiene ============
print("\n--- 9. Hygiene ---")
mod_src = open(os.path.join(_base, "canonical_dosha.py"), encoding="utf-8").read()
check("adapter does not import legacy doshas",
      "doshas_advanced" not in mod_src and "from backend.jaimini" not in mod_src)
check("adapter has zero engine imports",
      all(tok not in mod_src for tok in (
          "calculate_all_shadbala(", "generate_jaimini_facts(",
          "generate_chart_facts(", "calculate_all_vargas(",
          "swisseph", "import swe")))
check("adapter imports only dosha catalogue/context",
      "core.rules.doshas.catalog" in mod_src)

# ============ 10. Category-E audit (no implementation) ============
print("\n--- 10. Category E ---")
import backend.canonical_yoga as _cy
covered = _cy.get_covered_legacy_ids()
for e in ("garuda_yoga", "kalpadruma_yoga", "mahabhagya_yoga",
          "matsya_yoga", "mridanga_yoga"):
    check(f"Category E {e} NOT canonically covered", e not in covered)
check("no E rule IDs in parashari catalogue",
      not any(r.metadata.rule_id.split(".")[-1] in
              ("GARUDA", "KALPADRUMA", "MAHABHAGYA", "MATSYA", "MRIDANGA")
              for r in __import__("core.rules.parashari.catalog",
                                  fromlist=["x"]).build_parashari_catalog()))
check("research firewall intact (no EXPERIMENTAL import in adapter)",
      "EXPERIMENTAL" not in mod_src and "research" not in mod_src.lower())

# ============ 11. Performance ============
print("\n--- 11. Performance ---")
import time as _t
_t0 = _t.perf_counter()
for _ in range(3):
    evaluate_canonical_doshas(CF, SR, VF)
_t1 = _t.perf_counter()
check("dosha eval mean < 5s", (_t1 - _t0) / 3 < 5.0, f"{(_t1 - _t0) / 3:.2f}s")

print("\n" + "=" * 70)
print(f"DOSHA PRODUCTION TESTS: {passes} passed, {failures} failed, {passes + failures} total")
print("=" * 70)
sys.exit(1 if failures else 0)
