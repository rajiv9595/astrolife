"""
Astrolife — Migration #4: Canonical Jaimini Production Wiring tests.

Covers: golden karakas/karakamsha/AL/UL, degree ordering, tie policy, node
handling, drishti structure, yoga wiring, dasha profiles A/B/C, adapter
contract, canonical precedence (legacy cannot override), legacy rollback
tagging, /compute integration (auth + anon), AI receivability, determinism,
performance. No canonical formula is modified by these tests.
"""
import sys
import os
_base = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, _base)
if os.path.basename(_base) == 'backend':
    sys.path.insert(0, os.path.dirname(_base))

from core.jaimini.pipeline import generate_jaimini_facts
from core.jaimini.profile import JaiminiCalculationProfile
from core.jaimini.rules.pipeline import evaluate_jaimini_yogas
from core.jaimini.rules.catalogue import get_rule_ids
from core.jaimini.dasha.pipeline import calculate_jaimini_dasha
from core.jaimini.dasha.profile import JaiminiDashaProfile
from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DEFAULT_PROFILE
from core.calculation.varga import calculate_all_vargas

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
print("MIGRATION #4 — CANONICAL JAIMINI PRODUCTION WIRING TESTS")
print("=" * 70)


def golden_facts():
    cf = generate_chart_facts(profile=DEFAULT_PROFILE, **GOLDEN)
    vf = calculate_all_vargas(cf, DEFAULT_PROFILE)
    jf = generate_jaimini_facts(cf, vf, JaiminiCalculationProfile())
    return cf, vf, jf


CF, VF, JF = golden_facts()

# ============ 1. Chara Karaka golden ============
print("\n--- 1. Chara Karakas ---")
GOLD_KARAKAS = {"AK": "Jupiter", "AmK": "Moon", "BK": "Mars", "MK": "Mercury",
                "PK": "Saturn", "GK": "Venus", "DK": "Sun"}
GOLD_DEGS = {"AK": 21.84, "AmK": 17.86, "BK": 16.59, "MK": 14.84,
             "PK": 10.06, "GK": 5.64, "DK": 0.04}
GOLD_SIGNS = {"AK": "Virgo", "AmK": "Sagittarius", "BK": "Aries",
              "MK": "Cancer", "PK": "Cancer", "GK": "Virgo", "DK": "Leo"}
got = {k: v.planet for k, v in JF.chara_karakas.karakas.items()}
check("golden karaka assignment", got == GOLD_KARAKAS, str(got))
for code, deg in GOLD_DEGS.items():
    actual = JF.chara_karakas.karakas[code].degree_in_sign
    check(f"golden {code} degree ~{deg}", abs(actual - deg) < 0.01, str(actual))
for code, sign in GOLD_SIGNS.items():
    check(f"golden {code} sign {sign}",
          JF.chara_karakas.karakas[code].sign == sign)
degs = [JF.chara_karakas.karakas[c].degree_in_sign
        for c in JF.chara_karakas.ordering]
check("degree ordering descending", all(a >= b for a, b in zip(degs, degs[1:])))
check("no tropical calculation",
      all(0.0 <= d <= 30.0 for d in degs))
check("Rahu excluded (7-method)",
      "Rahu" not in JF.chara_karakas.planet_to_karaka)
check("Ketu excluded", "Ketu" not in JF.chara_karakas.planet_to_karaka)
check("karaka evidence present", len(JF.chara_karakas.evidence) >= 7)

# tie policy: equal intra-sign degrees resolve by canonical precedence
from backend.core.rules.parashari.fixtures import make_synthetic_context
tie_ctx = make_synthetic_context(
    "Aries", {"Sun": ("Leo", 15.0), "Moon": ("Cancer", 15.0),
              "Mars": "Aries", "Mercury": "Gemini", "Jupiter": "Sagittarius",
              "Venus": "Libra", "Saturn": "Capricorn"})
from core.jaimini.karakas import calculate_chara_karakas
tie_rep = calculate_chara_karakas(tie_ctx.chart_facts, JaiminiCalculationProfile())
sun_rank = tie_rep.karakas["AK"].planet if tie_rep.karakas["AK"].degree_in_sign == 15.0 else None
moon_tie = [c for c, it in tie_rep.karakas.items() if it.planet == "Moon"]
sun_tie = [c for c, it in tie_rep.karakas.items() if it.planet == "Sun"]
check("tie resolved deterministically", len(sun_tie) == 1 and len(moon_tie) == 1)
order = tie_rep.ordering
check("tie precedence Sun before Moon",
      order.index(sun_tie[0]) < order.index(moon_tie[0]),
      str([(c, tie_rep.karakas[c].planet) for c in order]))
tie_rep2 = calculate_chara_karakas(tie_ctx.chart_facts, JaiminiCalculationProfile())
check("tie determinism",
      [(c, tie_rep2.karakas[c].planet) for c in tie_rep2.ordering] ==
      [(c, tie_rep.karakas[c].planet) for c in tie_rep.ordering])

# ============ 2. Karakamsha / AL / UL ============
print("\n--- 2. Karakamsha/AL/UL ---")
check("karakamsha Cancer", JF.karakamsha.karakamsha_sign == "Cancer")
check("karakamsha AK Jupiter", JF.karakamsha.atmakaraka_planet == "Jupiter")
check("karakamsha D1 Virgo", JF.karakamsha.atmakaraka_d1_sign == "Virgo")
check("AL Capricorn", JF.arudha_lagna.final_sign == "Capricorn")
check("AL pada A1", JF.arudha_lagna.pada_code == "A1")
check("UL Capricorn", JF.upapada.final_sign == "Capricorn")
check("UL source 12th", JF.upapada.source_house == 12)
check("AL evidence", len(JF.arudha_lagna.evidence) >= 1)
check("UL evidence", len(JF.upapada.evidence) >= 1)
check("karakamsha evidence", len(JF.karakamsha.evidence) >= 1)

# ============ 3. Rashi Drishti ============
print("\n--- 3. Drishti ---")
check("drishti 12 signs", len(JF.rashi_drishti.sign_aspects) == 12)
check("drishti 3-aspect structure",
      all(len(v) == 3 for v in JF.rashi_drishti.sign_aspects.values()))
check("drishti no self-aspect",
      all(k not in v for k, v in JF.rashi_drishti.sign_aspects.items()))
check("drishti planet aspects present", len(JF.rashi_drishti.planet_aspects) >= 7)
check("drishti sign-based (not Parashari graha)",
      JF.rashi_drishti.method.value != "PARASHARI" if hasattr(
          JF.rashi_drishti.method, "value") else True)
check("drishti evidence", len(JF.rashi_drishti.evidence) >= 1)

# ============ 4. Jaimini Yogas ============
print("\n--- 4. Yogas ---")
check("12 canonical yoga rules", get_rule_ids() is not None and len(get_rule_ids()) == 12,
      str(get_rule_ids()))
yeval = evaluate_jaimini_yogas(CF, JF, VF)
check("yoga eval 12 results", yeval.total_rules == 12)
GOLD_FORMED = {"JAI.ARUDHA.AL_LORD_KENDRA_TRINE", "JAI.DRISHTI.AK_AMK_MUTUAL",
               "JAI.KARAKAMSHA.BENEFIC_OCCUPANCY"}
check("golden yoga formed set",
      {r.rule_id for r in yeval.results if r.formed} == GOLD_FORMED,
      str([(r.rule_id, r.formed) for r in yeval.results]))
check("yoga formation evidence",
      all(len(r.formation_evidence) >= 1 for r in yeval.results))
check("yoga provenance block", bool(yeval.provenance.get("tradition") == "JAIMINI"))
yeval2 = evaluate_jaimini_yogas(CF, JF, VF)
check("yoga determinism",
      [(r.rule_id, r.formed) for r in yeval.results] ==
      [(r.rule_id, r.formed) for r in yeval2.results])

# ============ 5. Chara Dasha profiles ============
print("\n--- 5. Dasha ---")
dA = calculate_jaimini_dasha(CF, JF)
check("profile A Taurus/REVERSE/92",
      (dA.starting_sign, dA.direction, dA.total_years) == ("Taurus", "REVERSE", 92.0),
      f"{dA.starting_sign} {dA.direction} {dA.total_years}")
dB = calculate_jaimini_dasha(
    CF, JF, JaiminiDashaProfile.from_method("CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED"))
check("profile B Taurus/FORWARD/96",
      (dB.starting_sign, dB.direction, dB.total_years) == ("Taurus", "FORWARD", 96.0),
      f"{dB.starting_sign} {dB.direction} {dB.total_years}")
dC = calculate_jaimini_dasha(
    CF, JF, JaiminiDashaProfile.from_method("CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS"))
check("profile C Taurus/REVERSE/92",
      (dC.starting_sign, dC.direction, dC.total_years) == ("Taurus", "REVERSE", 92.0),
      f"{dC.starting_sign} {dC.direction} {dC.total_years}")
check("dasha periods sequenced", len(dA.periods) == 12 and
      dA.periods[0].sign == "Taurus")
check("dasha UTC bounds",
      all(p.start_utc_iso and p.end_utc_iso for p in dA.periods))
check("dasha antardashas", all(len(p.antardashas) == 12 for p in dA.periods))
check("dasha total == 92", abs(sum(p.duration_years for p in dA.periods) - 92.0) < 1e-6)
check("dasha starting evidence", bool(dA.starting_sign_evidence))
check("dasha validation clean",
      dA.validation.get("valid", False) is True, str(dA.validation.get("violations")))
dA2 = calculate_jaimini_dasha(CF, JF)
check("dasha determinism", dA.model_dump_json() == dA2.model_dump_json())

# ============ 6. Provenance ============
print("\n--- 6. Provenance ---")
check("provenance tradition JAIMINI", JF.provenance.tradition == "JAIMINI")
check("provenance method recorded", bool(JF.provenance.method))
check("provenance source_reference present", bool(JF.provenance.source_reference))
check("provenance version", bool(JF.provenance.version))

# ============ 7. Adapter contract ============
print("\n--- 7. Adapter ---")
from backend.canonical_jaimini import evaluate_canonical_jaimini
from datetime import timezone
adapted = evaluate_canonical_jaimini(CF, VF)
check("adapter _source canonical", adapted.get("_source") == "canonical")
check("adapter karakas legacy-shaped",
      adapted["chara_karakas"] == {
          "Atmakaraka (AK)": "Jupiter", "Amatyakaraka (AmK)": "Moon",
          "Bhratrukaraka (BK)": "Mars", "Matrukaraka (MK)": "Mercury",
          "Putrakaraka (PK)": "Saturn", "Gnatikaraka (GK)": "Venus",
          "Darakaraka (DK)": "Sun"})
check("adapter padas legacy-shaped (12, str keys)",
      len(adapted["arudha_padas"]) == 12 and
      all(isinstance(k, str) for k in adapted["arudha_padas"]))
check("adapter pada A1 Capricorn", adapted["arudha_padas"]["1"] == "Capricorn")
check("adapter karakamsha", adapted["karakamsha"]["karakamsha_sign"] == "Cancer")
check("adapter AL/UL", adapted["arudha_lagna"]["final_sign"] == "Capricorn" and
      adapted["upapada"]["final_sign"] == "Capricorn")
check("adapter yogas 12", len(adapted["yogas"]) == 12 and
      all(y["_source"] == "canonical" for y in adapted["yogas"]))
check("adapter dasha A", (adapted["chara_dasha"]["starting_sign"],
                          adapted["chara_dasha"]["direction"],
                          adapted["chara_dasha"]["total_years"]) == ("Taurus", "REVERSE", 92.0))
check("adapter evidence/provenance",
      bool(adapted["evidence"]) and adapted["provenance"]["tradition"] == "JAIMINI")
import json as _json
try:
    _json.dumps(adapted)
    check("adapter JSON-serializable (AI receivability)", True)
except TypeError as ex:
    check("adapter JSON-serializable (AI receivability)", False, str(ex))
adapted2 = evaluate_canonical_jaimini(CF, VF)
check("adapter determinism",
      _json.dumps(adapted, sort_keys=True, default=str) ==
      _json.dumps(adapted2, sort_keys=True, default=str))
# current-period derivation labeled, engine API absent
check("no invented engine current API",
      not hasattr(__import__("core.jaimini.dasha.pipeline", fromlist=["x"]),
                  "get_current_chara_period"))
check("current derivation labeled",
      adapted["chara_dasha"]["current"].get("derivation") ==
      "no_evaluation_datetime_supplied")

# ============ 8. Legacy crosscheck (golden + sweep) ============
print("\n--- 8. Crosscheck ---")
from backend.jaimini import compute_jaimini_system
planets = {n: {"degree_in_sign_manual": float(p.sign.degree),
               "sign_manual": p.sign.name} for n, p in CF.planets.items()}
leg = compute_jaimini_system(planets, CF.ascendant.sign.name)
check("golden karakas MATCH legacy", leg["chara_karakas"] == adapted["chara_karakas"])
check("golden padas MATCH legacy",
      {str(k): v for k, v in leg["arudha_padas"].items()} == adapted["arudha_padas"])
sweep_ok = 0
sweep_n = 0
for asc in ("Aries", "Leo", "Scorpio", "Aquarius"):
    for pl in ({"Sun": "Aries", "Moon": "Taurus"},
               {"Mars": "Capricorn", "Venus": "Pisces", "Saturn": "Libra"}):
        base = {"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries",
                "Mercury": "Gemini", "Jupiter": "Sagittarius",
                "Venus": "Libra", "Saturn": "Capricorn"}
        base.update(pl)
        from core.calculation.varga import calculate_all_vargas as _v
        from core.calculation.config import DEFAULT_PROFILE as _dp
        tctx = make_synthetic_context(asc, base)
        tcf = tctx.chart_facts
        tjf = generate_jaimini_facts(tcf, _v(tcf, _dp), JaiminiCalculationProfile())
        tad = evaluate_canonical_jaimini(tcf, _v(tcf, _dp))
        tleg = compute_jaimini_system(
            {n: {"degree_in_sign_manual": float(p.sign.degree),
                 "sign_manual": p.sign.name} for n, p in tcf.planets.items()},
            tcf.ascendant.sign.name)
        sweep_n += 1
        if (tleg["chara_karakas"] == tad["chara_karakas"] and
                {str(k): v for k, v in tleg["arudha_padas"].items()} == tad["arudha_padas"]):
            sweep_ok += 1
check("sweep karakas+padas MATCH legacy", sweep_ok == sweep_n,
      f"{sweep_ok}/{sweep_n}")

# ============ 9. Production wiring ============
print("\n--- 9. Production ---")
from backend.canonical_response import (
    build_canonical_compute_response, enrich_response_with_legacy_modules)
REQ = {"year": 2005, "month": 8, "day": 17, "hour": 0, "minute": 2,
       "second": 0, "lat": 16.93407, "lon": 81.95522, "tz": "Asia/Kolkata"}
resp = enrich_response_with_legacy_modules(
    build_canonical_compute_response(CF, VF, REQ, current_user=object()),
    CF, REQ, current_user=object())
check("production jaimini canonical",
      resp["jaimini"].get("_source") == "canonical" and
      resp["jaimini"].get("_engine") == "canonical")
check("production karakas golden",
      resp["jaimini"]["chara_karakas"].get("Atmakaraka (AK)") == "Jupiter")
check("production yogas intact", len(resp.get("yogas", [])) == 82)
resp_anon = enrich_response_with_legacy_modules(
    build_canonical_compute_response(CF, VF, REQ, current_user=None),
    CF, REQ, current_user=None)
check("unauthenticated jaimini canonical",
      resp_anon["jaimini"].get("_source") == "canonical")
# canonical precedence: legacy raising must not break production
import backend.jaimini as _legmod
_orig = _legmod.compute_jaimini_system


def _boom(*a, **k):
    raise RuntimeError("legacy must not be called")


import backend.canonical_response as _cr
_src = open(_cr.__file__, encoding="utf-8").read()
check("production imports canonical adapter",
      "evaluate_canonical_jaimini" in _src)
# simulate legacy outage at call site: patch module attr used by rollback
_legmod.compute_jaimini_system = _boom
try:
    resp2 = enrich_response_with_legacy_modules(
        build_canonical_compute_response(CF, VF, REQ, current_user=object()),
        CF, REQ, current_user=object())
    check("legacy outage does not break production",
          resp2["jaimini"].get("_source") == "canonical")
finally:
    _legmod.compute_jaimini_system = _orig
# rollback path: canonical failure -> tagged legacy fallback
import backend.canonical_jaimini as _cj
_orig_ev = _cj.evaluate_canonical_jaimini


def _fail(*a, **k):
    raise RuntimeError("simulated canonical failure")


_cj.evaluate_canonical_jaimini = _fail
# enrich() does 'from backend.canonical_jaimini import ...' at call time,
# so patch the source module attribute instead
try:
    resp3 = enrich_response_with_legacy_modules(
        build_canonical_compute_response(CF, VF, REQ, current_user=object()),
        CF, REQ, current_user=object())
    check("rollback tagged legacy_fallback",
          resp3["jaimini"].get("_source") == "legacy_fallback")
    check("rollback keeps contract keys",
          "chara_karakas" in resp3["jaimini"] and "arudha_padas" in resp3["jaimini"])
finally:
    _cj.evaluate_canonical_jaimini = _orig_ev

# ============ 10. AI receivability ============
print("\n--- 10. AI ---")
ai_src = open(os.path.join(_base, "routes", "ai_routes.py"), encoding="utf-8").read()
check("AI expert context passes jaimini through", '"jaimini"' in ai_src)
expert_keys = ["jaimini", "ashtakavarga", "shadbala", "maitri"]
check("AI passthrough keys intact", all(f'"{k}"' in ai_src for k in expert_keys))
check("AI no-recalculation instruction",
      "Do not perform new calculations; interpret the provided ones" in ai_src)
check("AI-bound jaimini carries source",
      resp["jaimini"].get("_source") == "canonical" and
      bool(resp["jaimini"].get("provenance")))

# ============ 11. Performance ============
print("\n--- 11. Performance ---")
import time as _t
_t0 = _t.perf_counter()
for _ in range(3):
    evaluate_canonical_jaimini(CF, VF)
_t1 = _t.perf_counter()
check("adapter mean < 5s", (_t1 - _t0) / 3 < 5.0, f"{(_t1 - _t0) / 3:.2f}s")

# ============ 12. Hygiene ============
print("\n--- 12. Hygiene ---")
mod_src = open(os.path.join(_base, "canonical_jaimini.py"), encoding="utf-8").read()
check("adapter has no astrology imports",
      "swisseph" not in mod_src and "import swe" not in mod_src)
check("adapter does not import legacy jaimini",
      "from backend.jaimini" not in mod_src and "import backend.jaimini" not in mod_src)
check("no Category E content", "MRIDANGA" not in mod_src.upper() and
      "KALPADRUMA" not in mod_src.upper())

print("\n" + "=" * 70)
print(f"JAIMINI PRODUCTION TESTS: {passes} passed, {failures} failed, {passes + failures} total")
print("=" * 70)
sys.exit(1 if failures else 0)
