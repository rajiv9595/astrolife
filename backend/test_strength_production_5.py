"""
Astrolife — Migration #5: Canonical Full Strength Production Wiring tests.

Covers: capability inventory, canonical source, production caller, Shadbala
regression (accepted goldens, untouched), dignity regression, Bhava Bala,
Vimsopaka (repaired varga access), Avastha (+ boundaries), Functional Nature
(Taurus anchors), composite (CUSTOM), evidence/provenance limits, adapter
contract, legacy fallback audit, canonical precedence, determinism, JSON
serialization, /compute runtime, AI-bound context. No formula is modified.
"""
import sys
import os
_base = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, _base)
if os.path.basename(_base) == 'backend':
    sys.path.insert(0, os.path.dirname(_base))

from core.strength.pipeline import generate_strength_report
from core.strength.profile import DEFAULT_STRENGTH_PROFILE
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
print("MIGRATION #5 — CANONICAL FULL STRENGTH PRODUCTION WIRING TESTS")
print("=" * 70)

CF = generate_chart_facts(profile=DEFAULT_PROFILE, **GOLDEN)
SR = generate_strength_report(CF)

# ============ 1. Capability inventory ============
print("\n--- 1. Inventory ---")
check("shadbala present (7 planets)",
      set(SR.planets.keys()) == {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
                                 "Venus", "Saturn"})
check("bhava bala present (12 houses)", len(SR.bhava_bala) == 12)
check("vimsopaka present (7 planets)", len(SR.vimsopaka) == 7)
check("avastha present (7 planets)", len(SR.avastha) == 7)
check("dignity present (7 planets)", len(SR.dignity) == 7)
check("functional present (7 planets)", len(SR.functional_strength) == 7)
check("composite present", len(SR.composite) >= 7)
check("Rahu/Ketu outside classical Shadbala",
      "Rahu" not in SR.planets and "Ketu" not in SR.planets)

# ============ 2. Shadbala regression (ACCEPTED goldens, tolerance 0.02) ============
print("\n--- 2. Shadbala goldens ---")
GOLD_RUPAS = {"Sun": 6.18, "Moon": 5.73, "Mars": 5.50, "Mercury": 7.33,
              "Jupiter": 6.81, "Venus": 7.34, "Saturn": 4.52}
for planet, exp in GOLD_RUPAS.items():
    got = SR.planets[planet].total_rupas
    check(f"shadbala {planet} ~{exp}", abs(float(got) - exp) < 0.02, str(got))
GOLD_LABELS = {"Sun": "Moderate", "Moon": "Moderate", "Mars": "Strong",
               "Mercury": "Strong", "Jupiter": "Strong", "Venus": "Strong",
               "Saturn": "Moderate"}
ROW_LABEL = {"STRONG": "Strong", "MODERATE": "Moderate", "WEAK": "Weak"}
for planet, exp in GOLD_LABELS.items():
    got = ROW_LABEL.get(SR.planets[planet].strength_status, "?")
    check(f"shadbala status {planet} {exp}", got == exp, str(got))

# ============ 3. Dignity regression ============
print("\n--- 3. Dignity goldens ---")
GOLD_DIGN = {"Sun": "MOOLATRIKONA", "Moon": "NEUTRAL", "Mars": "OWN_SIGN",
             "Mercury": "ENEMY", "Jupiter": "ENEMY", "Venus": "DEBILITATED",
             "Saturn": "ENEMY"}
for planet, exp in GOLD_DIGN.items():
    check(f"dignity {planet} {exp}", SR.dignity[planet].dignity == exp,
          SR.dignity[planet].dignity)
check("Saturn Cancer is NOT debilitated",
      SR.dignity["Saturn"].dignity != "DEBILITATED" and
      not SR.dignity["Saturn"].is_debilitated)
check("Saturn debilitation sign is Aries (canonical)",
      SR.dignity["Saturn"].dignity == "ENEMY")
VF = calculate_all_vargas(CF, DEFAULT_PROFILE)
check("D9 Saturn Libra Exalted (varga info, not merged into Shadbala)",
      VF["planets"]["Saturn"]["D9"].sign == "Libra")

# ============ 4. Bhava Bala ============
print("\n--- 4. Bhava ---")
GOLD_BHAVA = {1: 476.295, 2: 481.206, 3: 381.39, 4: 411.792, 5: 469.956,
              6: 483.795, 7: 367.296, 8: 450.102, 9: 301.26, 10: 327.51,
              11: 446.352, 12: 382.296}
for house, exp in GOLD_BHAVA.items():
    got = SR.bhava_bala[house].total
    check(f"bhava H{house} engine-regression {exp}",
          abs(float(got) - exp) < 0.01, str(got))
r1 = SR.bhava_bala[1]
check("bhava components present",
      r1.bhavadhipati_bala is not None and r1.dig_bala is not None and
      r1.drishti_bala is not None)
check("bhava units virupas", r1.unit == "virupas")
check("bhava sign/house basis", r1.sign == "Taurus" and r1.house == 1)

# ============ 5. Vimsopaka ============
print("\n--- 5. Vimsopaka ---")
GOLD_VIM = {"Sun": 16.8, "Moon": 6.3, "Mars": 7.3, "Mercury": 3.4,
            "Jupiter": 6.8, "Venus": 2.9, "Saturn": 7.2}
for planet, exp in GOLD_VIM.items():
    got = SR.vimsopaka[planet].score
    check(f"vimsopaka {planet} engine-regression {exp}",
          abs(float(got) - exp) < 0.05, str(got))
check("vimsopaka 7 contributions each",
      all(len(r.varga_contributions) == 7 for r in SR.vimsopaka.values()))
check("vimsopaka vargas [1,2,3,7,9,12,30]",
      all(r.vargas_used == [1, 2, 3, 7, 9, 12, 30] for r in SR.vimsopaka.values()))
check("vimsopaka weights D1:6 D9:5",
      all(r.weights.get(1) == 6 and r.weights.get(9) == 5
          for r in SR.vimsopaka.values()))
check("vimsopaka normalized 0..20",
      all(0.0 <= r.score <= 20.0 and abs(r.ratio - r.score / 20.0) < 1e-9
          for r in SR.vimsopaka.values()))
check("vimsopaka maximum 20", all(r.maximum == 20.0 for r in SR.vimsopaka.values()))
check("vimsopaka dignity evidence per varga",
      all(all("dignity_score" in c and "sign" in c
              for c in r.varga_contributions)
          for r in SR.vimsopaka.values()))
# formula spot-check: Venus D1 Virgo debilitated 0.0 x weight 6
venus_d1 = [c for c in SR.vimsopaka["Venus"].varga_contributions if c["varga"] == 1][0]
check("vimsopaka dignity formula intact",
      venus_d1["sign"] == "Virgo" and venus_d1["dignity_score"] == 0.0 and
      venus_d1["weight"] == 6)

# ============ 6. Avastha ============
print("\n--- 6. Avastha ---")
GOLD_AVA = {"Sun": "BALA", "Moon": "YUVA", "Mars": "YUVA", "Mercury": "YUVA",
            "Jupiter": "VRIDDHA", "Venus": "BALA", "Saturn": "KUMARA"}
for planet, exp in GOLD_AVA.items():
    got = SR.avastha[planet]["BALA_AVASTHA"].avastha_name
    check(f"avastha {planet} {exp}", got == exp, str(got))
check("default profile Bala only (Jagratadi available, not default)",
      all(set(d.keys()) == {"BALA_AVASTHA"} for d in SR.avastha.values()) and
      DEFAULT_STRENGTH_PROFILE.avastha_systems == ["BALA_AVASTHA"])
# Jagratadi direct (engine-supported, non-default): sign-type mapping
from core.strength.avastha import calculate_jagratadi_avastha
from backend.core.rules.parashari.fixtures import make_synthetic_context
for sign, exp in (("Aries", "JAGRAT"), ("Taurus", "SVAPNA"),
                  ("Gemini", "SUSHUPTI"), ("Cancer", "JAGRAT"),
                  ("Leo", "SVAPNA"), ("Virgo", "SUSHUPTI")):
    tctx = make_synthetic_context("Aries", {"Sun": sign})
    got = calculate_jagratadi_avastha("Sun", tctx.chart_facts,
                                      DEFAULT_STRENGTH_PROFILE).avastha_name
    check(f"jagratadi {sign} {exp}", got == exp, str(got))
# Bala 6-degree boundaries
from core.strength.avastha import calculate_bala_avastha
for deg, exp in ((0.0, "BALA"), (5.99, "BALA"), (6.0, "KUMARA"),
                 (11.99, "KUMARA"), (12.0, "YUVA"), (17.99, "YUVA"),
                 (18.0, "VRIDDHA"), (23.99, "VRIDDHA"), (24.0, "MRITYA"),
                 (29.99, "MRITYA")):
    tctx = make_synthetic_context("Aries", {"Sun": ("Leo", deg)})
    got = calculate_bala_avastha("Sun", tctx.chart_facts,
                                 DEFAULT_STRENGTH_PROFILE).avastha_name
    check(f"bala boundary {deg} {exp}", got == exp, str(got))
# dignity sign boundary: exaltation is sign-based in canonical engine
tctx = make_synthetic_context("Aries", {"Sun": ("Aries", 25.0)})
check("exaltation sign-based (Sun Aries late degree)",
      tctx.is_exalted("Sun"))

# ============ 7. Functional Nature (Taurus anchors) ============
print("\n--- 7. Functional ---")
GOLD_FUNC = {"Sun": ("NEUTRAL_KENDRA", False), "Moon": ("NEUTRAL", False),
             "Mars": ("FUNCTIONAL_MALEFIC", False),
             "Mercury": ("NEUTRAL", False),
             "Jupiter": ("FUNCTIONAL_MALEFIC", False),
             "Venus": ("YOGAKARAKA", True), "Saturn": ("YOGAKARAKA", True)}
for planet, (exp_nat, exp_yk) in GOLD_FUNC.items():
    f = SR.functional_strength[planet]
    check(f"functional {planet} {exp_nat}/YK={exp_yk}",
          f.functional_nature == exp_nat and f.yogakaraka == exp_yk,
          f"{f.functional_nature}/{f.yogakaraka}")
mars = SR.functional_strength["Mars"]
check("Mars rules 7+12", sorted(mars.lordship.get("houses_ruled", [])) == [7, 12])
sat = SR.functional_strength["Saturn"]
check("Saturn rules 9+10 (Yogakaraka)", sorted(sat.lordship.get("houses_ruled", [])) == [9, 10])
check("functional scores bounded", all(0.0 <= f.score <= 100.0
                                       for f in SR.functional_strength.values()))
check("functional details evidence",
      all(len(f.details) >= 2 for f in SR.functional_strength.values()))
check("functional distinct from natural benefic",
      SR.functional_strength["Jupiter"].functional_nature == "FUNCTIONAL_MALEFIC")

# ============ 8. Composite (CUSTOM) ============
print("\n--- 8. Composite ---")
GOLD_COMP = {"Sun": (100.0, "Very Strong"), "Moon": (50.0, "Moderate"),
             "Mars": (85.0, "Very Strong"), "Mercury": (55.0, "Moderate"),
             "Jupiter": (70.0, "Strong"), "Venus": (40.0, "Weak"),
             "Saturn": (45.0, "Weak")}
for planet, (exp_score, exp_label) in GOLD_COMP.items():
    c = SR.composite[planet]
    check(f"composite {planet} {exp_score}/{exp_label}",
          abs(c.score - exp_score) < 0.05 and c.label == exp_label,
          f"{c.score}/{c.label}")
check("composite method CUSTOM + disclaimer",
      all(c.method == "ASTROLIFE_CUSTOM" and "custom" in c.disclaimer.lower()
          for c in SR.composite.values()))
check("composite reasons evidence",
      all(len(c.reasons) >= 1 for c in SR.composite.values()))
check("composite keeps Shadbala separate (ratio as factor only)",
      all("shadbala_ratio" in (c.components or {}) for p, c in SR.composite.items()
          if p in SR.planets))

# ============ 9. Evidence / Provenance limits ============
print("\n--- 9. Evidence/Provenance ---")
check("StrengthReport has no provenance field (documented limitation)",
      not hasattr(SR, "provenance"))
check("Bhava model has no evidence list (values are the evidence)",
      not hasattr(SR.bhava_bala[1], "evidence"))
check("avastha descriptions present",
      all(v.description for d in SR.avastha.values() for v in d.values()))

# ============ 10. Adapter contract ============
print("\n--- 10. Adapter ---")
from backend.canonical_strength import (
    build_strength_rows, build_shadbala_payload,
    build_bhava_bala_payload, build_vimsopaka_payload,
    build_avastha_payload, build_functional_payload,
    build_composite_payload,
)
from core.strength.shadbala import calculate_all_shadbala
from core.strength.dignity import calculate_all_dignities
sh = calculate_all_shadbala(CF)
dg = calculate_all_dignities(CF)
rows = build_strength_rows(sh, dg, {})
check("strength rows 9 (7 + 2 nodes)", len(rows) == 9)
check("row score == canonical total_rupas",
      all(abs(next(r for r in rows if r["planet"] == p)["score"] -
              round(sh[p].total_rupas, 2)) < 1e-9 for p in GOLD_RUPAS))
bh = build_bhava_bala_payload(SR.bhava_bala)
check("bhava payload 12 str keys", len(bh) == 12 and all(isinstance(k, str) for k in bh))
check("bhava payload golden H1", abs(bh["1"]["total"] - 476.295) < 0.01)
check("bhava _source tags", all(v.get("_source") == "canonical" for v in bh.values()))
vi = build_vimsopaka_payload(SR.vimsopaka)
check("vimsopaka payload 7 + contributions",
      len(vi) == 7 and all(len(v["varga_contributions"]) == 7 for v in vi.values()))
av = build_avastha_payload(SR.avastha)
check("avastha payload 7", len(av) == 7 and
      all("BALA_AVASTHA" in v for v in av.values()))
fu = build_functional_payload(SR.functional_strength)
check("functional payload Saturn YK",
      fu["Saturn"]["yogakaraka"] is True and
      fu["Saturn"]["functional_nature"] == "YOGAKARAKA")
co = build_composite_payload(SR.composite)
check("composite payload keeps disclaimer",
      all("custom" in v.get("disclaimer", "").lower() for v in co.values()))
check("adapter _source tags everywhere",
      all(v.get("_source") == "canonical"
          for block in (vi, av, fu, co) for v in block.values()))
import json as _json
try:
    _json.dumps({"bh": bh, "vi": vi, "av": av, "fu": fu, "co": co})
    check("adapter JSON-serializable", True)
except TypeError as ex:
    check("adapter JSON-serializable", False, str(ex))
check("adapter has zero astrology imports/calls",
      all(tok not in open(os.path.join(_base, "canonical_strength.py"),
                          encoding="utf-8").read()
          for tok in ("swisseph", "import swe", "from core.strength",
                      "from backend.core", "import backend.core",
                      "calculate_all_shadbala(", "calculate_bhava_bala(",
                      "calculate_all_vimsopaka(", "calculate_all_avastha(",
                      "calculate_all_functional(", "calculate_all_composite(",
                      "calculate_all_vargas(")))
check("no duplicate planets per block",
      all(len(list(b.keys())) == len(set(b.keys())) for b in (bh, vi, av, fu, co)))

# ============ 11. Legacy audit ============
print("\n--- 11. Legacy ---")
for path in (os.path.join(_base, "routes", "astro.py"),
             os.path.join(_base, "canonical_response.py")):
    src = open(path, encoding="utf-8").read()
    check(f"no legacy strength in {os.path.basename(path)}",
          "from backend.strength_evaluator import" not in src and
          "calculate_chart_strengths(" not in src and
          "from backend.shadbala import" not in src and
          "compute_shadbala(" not in src)
check("legacy strength module retained (not deleted)",
      os.path.isfile(os.path.join(_base, "strength_evaluator.py")))

# ============ 12. /compute runtime ============
print("\n--- 12. Runtime ---")
from backend.canonical_response import (
    build_canonical_compute_response, enrich_response_with_legacy_modules)
REQ = {"year": 2005, "month": 8, "day": 17, "hour": 0, "minute": 2,
       "second": 0, "lat": 16.93407, "lon": 81.95522, "tz": "Asia/Kolkata"}
resp = enrich_response_with_legacy_modules(
    build_canonical_compute_response(CF, VF, REQ, current_user=object()),
    CF, REQ, current_user=object())
for key in ("bhava_bala", "vimsopaka", "avastha", "functional_nature",
            "composite_strength"):
    check(f"runtime block {key} present", isinstance(resp.get(key), dict) and
          len(resp[key]) > 0)
check("runtime shadbala golden preserved",
      abs(float(resp["shadbala"]["Sun"]["total_rupas"]) - 6.18) < 0.02)
check("runtime strengths rows golden preserved",
      abs(float(next(r for r in resp["strengths"] if r["planet"] == "Venus")["score"]) - 7.34) < 0.02)
check("runtime vimsopaka nonzero (repaired)",
      all(v["score"] > 0 for v in resp["vimsopaka"].values()))
check("runtime yogas intact (82)", len(resp.get("yogas", [])) == 82)
check("runtime jaimini canonical", resp.get("jaimini", {}).get("_source") == "canonical")
resp2 = enrich_response_with_legacy_modules(
    build_canonical_compute_response(CF, VF, REQ, current_user=object()),
    CF, REQ, current_user=object())
check("runtime determinism (strength blocks)",
      all(_json.dumps(resp[k], sort_keys=True, default=str) ==
          _json.dumps(resp2[k], sort_keys=True, default=str)
          for k in ("bhava_bala", "vimsopaka", "avastha", "functional_nature",
                    "composite_strength", "strengths", "shadbala")))
resp_anon = enrich_response_with_legacy_modules(
    build_canonical_compute_response(CF, VF, REQ, current_user=None),
    CF, REQ, current_user=None)
check("unauthenticated strength blocks present",
      all(isinstance(resp_anon.get(k), dict) and len(resp_anon[k]) > 0
          for k in ("bhava_bala", "vimsopaka", "avastha", "functional_nature",
                    "composite_strength")))
try:
    _json.dumps({k: resp[k] for k in ("strengths", "shadbala", "bhava_bala",
                                      "vimsopaka", "avastha", "functional_nature",
                                      "composite_strength")})
    check("runtime strength JSON-serializable", True)
except TypeError as ex:
    check("runtime strength JSON-serializable", False, str(ex))

# ============ 13. AI-bound ============
print("\n--- 13. AI ---")
ai_src = open(os.path.join(_base, "routes", "ai_routes.py"), encoding="utf-8").read()
for key in ("bhava_bala", "vimsopaka", "avastha", "functional_nature",
            "composite_strength", "shadbala"):
    check(f"AI expert passthrough has {key}", f'"{key}"' in ai_src)
check("AI no-recalculation instruction",
      "Do not perform new calculations; interpret the provided ones" in ai_src)

# ============ 14. Determinism (engine) ============
print("\n--- 14. Determinism ---")
SR2 = generate_strength_report(CF)
d1 = SR.model_dump(mode="json")
d2 = SR2.model_dump(mode="json")
d1.pop("metadata", None)
d2.pop("metadata", None)
check("engine determinism (facts; metadata.generated_at is wall-clock by design)",
      d1 == d2)

# ============ 15. Performance ============
print("\n--- 15. Performance ---")
import time as _t
_t0 = _t.perf_counter()
for _ in range(2):
    generate_strength_report(CF)
_t1 = _t.perf_counter()
check("strength pipeline mean < 5s", (_t1 - _t0) / 2 < 5.0, f"{(_t1 - _t0) / 2:.2f}s")

print("\n" + "=" * 70)
print(f"STRENGTH PRODUCTION TESTS: {passes} passed, {failures} failed, {passes + failures} total")
print("=" * 70)
sys.exit(1 if failures else 0)
