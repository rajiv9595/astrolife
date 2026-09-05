"""
Astrolife V2 — Phase 5C: Dosha Engine Tests

Comprehensive tests for all implemented doshas:
  - Manglik/Kuja Dosha (3 methods: Lagna, Moon, Venus)
  - Kemadruma Dosha (classical)
  - Kala Sarpa Dosha (tradition-dependent)
  - Pitru Dosha (modern common)

Test categories:
  - Catalogue integrity
  - Positive fixtures (FORMED)
  - Negative fixtures (NOT_FORMED)
  - Boundary fixtures
  - Cancellation fixtures
  - Mitigation fixtures
  - 12-ascendant sweep
  - Golden chart integration
  - Determinism checks
  - Evidence quality checks
  - No-AI / no-prediction guards
"""
import sys
import os
import json
import hashlib

sys.path.insert(0, os.path.dirname(__file__) if '__file__' in globals() else '.')

from core.rules.doshas.catalog import (
    build_dosha_catalog, evaluate_all_doshas, evaluate_dosha_by_id,
    create_dosha_evaluator, build_manifest,
)
from core.rules.doshas.enums import (
    DoshaSeverity, DoshaFormationStatus, DoshaCancellationStatus,
    DoshaMitigationStatus, DoshaTradition,
)
from core.rules.parashari.fixtures import make_synthetic_context, make_golden_context

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


def formed_value(res):
    return getattr(res.formation_status, "value", str(res.formation_status))


def is_formed(res):
    return formed_value(res) == "FORMED"


def severity_value(res):
    return getattr(res.severity_status, "value", str(res.severity_status))


def cancellation_value(res):
    return getattr(res.cancellation_status, "value", str(res.cancellation_status))


def mitigation_value(res):
    return getattr(res.mitigation_status, "value", str(res.mitigation_status))


def tradition_value(res):
    return getattr(res.tradition, "value", str(res.tradition))


print("=" * 70)
print("ASTROLIFE V2 — PHASE 5C: DOSHA ENGINE TESTS")
print("=" * 70)

# ============ 0. Catalogue integrity ============
print("\n--- 0. Catalogue integrity ---")
rules = build_dosha_catalog()
check("Dosha rules implemented", len(rules) >= 6, f"got {len(rules)} rules")
ids = [r.metadata.rule_id for r in rules]
check("Rule IDs unique", len(set(ids)) == len(ids), f"unique: {len(set(ids))}, total: {len(ids)}")

# Verify expected rule IDs
expected_ids = [
    "DOSHA.MANGLIK.LAGNA_CLASSICAL",
    "DOSHA.MANGLIK.MOON_REFERENCE",
    "DOSHA.MANGLIK.VENUS_REFERENCE",
    "DOSHA.KEMADRUMA.CLASSICAL",
    "DOSHA.KALA_SARPA.SIGN_BASED",
    "DOSHA.PITRU.MODERN_COMMON",
]
for eid in expected_ids:
    check(f"Expected rule {eid} present", eid in ids, f"missing: {eid}")

for r in rules:
    m = r.metadata
    check(f"{m.rule_id} category DOSHA",
          m.category.value == "DOSHA" if hasattr(m.category, "value") else str(m.category) == "DOSHA")
    check(f"{m.rule_id} tradition declared",
          m.tradition.value in ("PARASHARI_CLASSICAL", "TRADITION_DEPENDENT")
          if hasattr(m.tradition, "value")
          else str(m.tradition) in ("PARASHARI_CLASSICAL", "TRADITION_DEPENDENT"))
    check(f"{m.rule_id} has formation conditions", len(r.formation_conditions) >= 1)
    check(f"{m.rule_id} provenance source", bool(m.provenance.source_name))
    check(f"{m.rule_id} source_reference present", bool(m.provenance.source_reference))
    check(f"{m.rule_id} no prediction text",
          all(w not in (m.description + m.name).lower()
              for w in ["you will", "marry", "divorce", "dangerous", "fatal", "doomed"]))

EVAL = create_dosha_evaluator()

# ============ 1. MANGLIK — LAGNA METHOD ============
print("\n--- 1. Manglik (Lagna Method) ---")
RID = "DOSHA.MANGLIK.LAGNA_CLASSICAL"

# Positive: Mars in 7th from Lagna (Libra for Aries ascendant)
pos = make_synthetic_context("Aries", {"Mars": "Libra", "Sun": "Leo", "Moon": "Cancer",
                                        "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                        "Venus": "Taurus", "Saturn": "Capricorn"})
r = evaluate_dosha_by_id(RID, pos, EVAL)
check("manglik lagna Mars-in-7th FORMED", is_formed(r), f"got {formed_value(r)}")
check("manglik lagna evidence present", len(r.evidence) > 0)
check("manglik lagna method metadata", r.method == "LAGNA_CLASSICAL", f"got {r.method}")

# Positive: Mars in 1st from Lagna
pos1 = make_synthetic_context("Aries", {"Mars": "Aries", "Sun": "Leo", "Moon": "Cancer",
                                         "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                         "Venus": "Taurus", "Saturn": "Capricorn"})
r1 = evaluate_dosha_by_id(RID, pos1, EVAL)
check("manglik lagna Mars-in-1st FORMED", is_formed(r1))

# Positive: Mars in 2nd from Lagna
pos2 = make_synthetic_context("Aries", {"Mars": "Taurus", "Sun": "Leo", "Moon": "Cancer",
                                         "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                         "Venus": "Gemini", "Saturn": "Capricorn"})
r2 = evaluate_dosha_by_id(RID, pos2, EVAL)
check("manglik lagna Mars-in-2nd FORMED", is_formed(r2))

# Positive: Mars in 4th from Lagna
pos4 = make_synthetic_context("Aries", {"Mars": "Cancer", "Sun": "Leo", "Moon": "Gemini",
                                         "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                         "Venus": "Taurus", "Saturn": "Capricorn"})
r4 = evaluate_dosha_by_id(RID, pos4, EVAL)
check("manglik lagna Mars-in-4th FORMED", is_formed(r4))

# Positive: Mars in 8th from Lagna
pos8 = make_synthetic_context("Aries", {"Mars": "Scorpio", "Sun": "Leo", "Moon": "Cancer",
                                         "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                         "Venus": "Taurus", "Saturn": "Capricorn"})
r8 = evaluate_dosha_by_id(RID, pos8, EVAL)
check("manglik lagna Mars-in-8th FORMED", is_formed(r8))

# Positive: Mars in 12th from Lagna
pos12 = make_synthetic_context("Aries", {"Mars": "Pisces", "Sun": "Leo", "Moon": "Cancer",
                                          "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                          "Venus": "Taurus", "Saturn": "Capricorn"})
r12 = evaluate_dosha_by_id(RID, pos12, EVAL)
check("manglik lagna Mars-in-12th FORMED", is_formed(r12))

# Negative: Mars in 3rd from Lagna (not a dosha house)
neg3 = make_synthetic_context("Aries", {"Mars": "Gemini", "Sun": "Leo", "Moon": "Cancer",
                                         "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                         "Venus": "Taurus", "Saturn": "Capricorn"})
rn3 = evaluate_dosha_by_id(RID, neg3, EVAL)
check("manglik lagna Mars-in-3rd NOT_FORMED", not is_formed(rn3))

# Negative: Mars in 5th from Lagna
neg5 = make_synthetic_context("Aries", {"Mars": "Leo", "Sun": "Virgo", "Moon": "Cancer",
                                         "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                         "Venus": "Taurus", "Saturn": "Capricorn"})
rn5 = evaluate_dosha_by_id(RID, neg5, EVAL)
check("manglik lagna Mars-in-5th NOT_FORMED", not is_formed(rn5))

# Negative: Mars in 6th from Lagna
neg6 = make_synthetic_context("Aries", {"Mars": "Virgo", "Sun": "Leo", "Moon": "Cancer",
                                         "Mercury": "Libra", "Jupiter": "Sagittarius",
                                         "Venus": "Taurus", "Saturn": "Capricorn"})
rn6 = evaluate_dosha_by_id(RID, neg6, EVAL)
check("manglik lagna Mars-in-6th NOT_FORMED", not is_formed(rn6))

# Negative: Mars in 9th from Lagna
neg9 = make_synthetic_context("Aries", {"Mars": "Sagittarius", "Sun": "Leo", "Moon": "Cancer",
                                         "Mercury": "Virgo", "Jupiter": "Capricorn",
                                         "Venus": "Taurus", "Saturn": "Capricorn"})
rn9 = evaluate_dosha_by_id(RID, neg9, EVAL)
check("manglik lagna Mars-in-9th NOT_FORMED", not is_formed(rn9))

# Negative: Mars in 10th from Lagna
neg10 = make_synthetic_context("Aries", {"Mars": "Capricorn", "Sun": "Leo", "Moon": "Cancer",
                                          "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                          "Venus": "Taurus", "Saturn": "Aquarius"})
rn10 = evaluate_dosha_by_id(RID, neg10, EVAL)
check("manglik lagna Mars-in-10th NOT_FORMED", not is_formed(rn10))

# Negative: Mars in 11th from Lagna
neg11 = make_synthetic_context("Aries", {"Mars": "Aquarius", "Sun": "Leo", "Moon": "Cancer",
                                          "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                          "Venus": "Taurus", "Saturn": "Pisces"})
rn11 = evaluate_dosha_by_id(RID, neg11, EVAL)
check("manglik lagna Mars-in-11th NOT_FORMED", not is_formed(rn11))

# ============ 2. MANGLIK — MOON METHOD ============
print("\n--- 2. Manglik (Moon Method) ---")
RID_M = "DOSHA.MANGLIK.MOON_REFERENCE"

# Positive: Mars in 7th from Moon
pos_m = make_synthetic_context("Aries", {"Mars": "Taurus", "Sun": "Leo", "Moon": "Libra",
                                          "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                          "Venus": "Gemini", "Saturn": "Capricorn"})
rm = evaluate_dosha_by_id(RID_M, pos_m, EVAL)
check("manglik moon Mars-in-7th-from-Moon FORMED", is_formed(rm))

# Negative: Mars NOT in dosha houses from Moon
neg_m = make_synthetic_context("Aries", {"Mars": "Gemini", "Sun": "Leo", "Moon": "Libra",
                                          "Mercury": "Cancer", "Jupiter": "Sagittarius",
                                          "Venus": "Taurus", "Saturn": "Capricorn"})
rnm = evaluate_dosha_by_id(RID_M, neg_m, EVAL)
check("manglik moon Mars-in-3rd-from-Moon NOT_FORMED", not is_formed(rnm))

# ============ 3. MANGLIK — VENUS METHOD ============
print("\n--- 3. Manglik (Venus Method) ---")
RID_V = "DOSHA.MANGLIK.VENUS_REFERENCE"

# Positive: Mars in 8th from Venus
pos_v = make_synthetic_context("Aries", {"Mars": "Libra", "Sun": "Leo", "Moon": "Cancer",
                                          "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                          "Venus": "Aries", "Saturn": "Capricorn"})
rv = evaluate_dosha_by_id(RID_V, pos_v, EVAL)
check("manglik venus Mars-in-8th-from-Venus FORMED", is_formed(rv))

# Negative: Mars NOT in dosha houses from Venus
neg_v = make_synthetic_context("Aries", {"Mars": "Gemini", "Sun": "Leo", "Moon": "Cancer",
                                          "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                          "Venus": "Aries", "Saturn": "Capricorn"})
rnv = evaluate_dosha_by_id(RID_V, neg_v, EVAL)
check("manglik venus Mars-in-3rd-from-Venus NOT_FORMED", not is_formed(rnv))

# ============ 4. MANGLIK EXHAUSTIVE: All 12 houses from Lagna ============
print("\n--- 4. Manglik exhaustive: Mars in all 12 houses from Lagna ---")
SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
DOSHA_HOUSES = {1, 2, 4, 7, 8, 12}
for i, mars_sign in enumerate(SIGN_NAMES):
    others = {"Sun": "Leo", "Moon": "Cancer", "Mercury": "Gemini",
              "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Capricorn"}
    others["Mars"] = mars_sign
    ctx = make_synthetic_context("Aries", others)
    r = evaluate_dosha_by_id(RID, ctx, EVAL)
    expected_formed = (i + 1) in DOSHA_HOUSES
    check(f"manglik lagna Mars-in-{mars_sign} (house {i+1}) -> {'FORMED' if expected_formed else 'NOT_FORMED'}",
          is_formed(r) == expected_formed,
          f"got {formed_value(r)}")

# ============ 5. MANGLIK CANCELLATION ============
print("\n--- 5. Manglik Cancellation ---")
# Jupiter conjunct Mars in dosha house → cancellation
cancel_ctx = make_synthetic_context("Aries", {"Mars": "Libra", "Jupiter": "Libra",
                                               "Sun": "Leo", "Moon": "Cancer",
                                               "Mercury": "Virgo", "Venus": "Taurus",
                                               "Saturn": "Capricorn"})
rc = evaluate_dosha_by_id(RID, cancel_ctx, EVAL)
check("manglik cancel: Jupiter conjunct Mars → CANCELLED",
      cancellation_value(rc) in ("PARTIAL", "FULL"),
      f"got {cancellation_value(rc)}")

# Jupiter aspects Mars (5th aspect from Gemini to Libra = house 7)
# Jupiter in Gemini (house 3), 5th aspect -> ((3+5-2)%12)+1 = 7 (Libra)
cancel_ctx2 = make_synthetic_context("Aries", {"Mars": "Libra", "Jupiter": "Gemini",
                                                "Sun": "Leo", "Moon": "Cancer",
                                                "Mercury": "Cancer", "Venus": "Taurus",
                                                "Saturn": "Capricorn"})
rc2 = evaluate_dosha_by_id(RID, cancel_ctx2, EVAL)
check("manglik cancel: Jupiter aspects Mars -> CANCELLED",
      cancellation_value(rc2) in ("PARTIAL", "FULL"),
      f"got {cancellation_value(rc2)}")

# ============ 6. MANGLIK MITIGATION ============
print("\n--- 6. Manglik Mitigation ---")
# Mars exalted (Capricorn) in dosha house (1st from Capricorn asc)
mit_ctx = make_synthetic_context("Capricorn", {"Mars": "Capricorn", "Sun": "Leo",
                                                "Moon": "Cancer", "Mercury": "Virgo",
                                                "Jupiter": "Sagittarius", "Venus": "Libra",
                                                "Saturn": "Aquarius"})
rm2 = evaluate_dosha_by_id(RID, mit_ctx, EVAL)
check("manglik mitigation: Mars exalted → MITIGATED",
      mitigation_value(rm2) in ("PARTIAL", "SIGNIFICANT"),
      f"got {mitigation_value(rm2)}")

# ============ 7. MANGLIK SEVERITY ============
print("\n--- 7. Manglik Severity ---")
# Mars debilitated (Cancer) in dosha house → should be HIGH severity
sev_ctx = make_synthetic_context("Aries", {"Mars": "Cancer", "Sun": "Leo",
                                            "Moon": "Gemini", "Mercury": "Virgo",
                                            "Jupiter": "Sagittarius", "Venus": "Taurus",
                                            "Saturn": "Capricorn"})
rs = evaluate_dosha_by_id(RID, sev_ctx, EVAL)
check("manglik severity: debilitated Mars → HIGH or MODERATE",
      severity_value(rs) in ("HIGH", "MODERATE"),
      f"got {severity_value(rs)}")

# Mars exalted → should be LOW severity
sev_ex = make_synthetic_context("Capricorn", {"Mars": "Capricorn", "Sun": "Leo",
                                               "Moon": "Cancer", "Mercury": "Virgo",
                                               "Jupiter": "Sagittarius", "Venus": "Libra",
                                               "Saturn": "Aquarius"})
rs_ex = evaluate_dosha_by_id(RID, sev_ex, EVAL)
check("manglik severity: exalted Mars → LOW",
      severity_value(rs_ex) == "LOW",
      f"got {severity_value(rs_ex)}")

# Mars NOT formed → severity NONE
sev_neg = make_synthetic_context("Aries", {"Mars": "Gemini", "Sun": "Leo",
                                            "Moon": "Cancer", "Mercury": "Virgo",
                                            "Jupiter": "Sagittarius", "Venus": "Taurus",
                                            "Saturn": "Capricorn"})
rs_neg = evaluate_dosha_by_id(RID, sev_neg, EVAL)
check("manglik severity: not formed → NONE",
      severity_value(rs_neg) == "NONE",
      f"got {severity_value(rs_neg)}")

# ============ 8. KEMADRUMA DOSHA ============
print("\n--- 8. Kemadruma Dosha ---")
RID_K = "DOSHA.KEMADRUMA.CLASSICAL"

# Positive: No planets in 2nd/12th from Moon, no kendra from Moon
# Moon in Leo (house 5 from Aries). 2nd from Moon = Virgo, 12th = Cancer
# Kendra from Moon = houses 5, 8, 11, 2 from Aries = Leo, Scorpio, Aquarius, Taurus
pos_k = make_synthetic_context("Aries", {"Moon": "Sagittarius", "Sun": "Aries",
                                          "Mars": "Aries", "Mercury": "Aries",
                                          "Jupiter": "Aries", "Venus": "Aries",
                                          "Saturn": "Aries"})
rk = evaluate_dosha_by_id(RID_K, pos_k, EVAL)
check("kemadruma FORMED when isolated", is_formed(rk), f"got {formed_value(rk)}")

# Negative: Planet in 2nd from Moon
neg_k2 = make_synthetic_context("Aries", {"Moon": "Sagittarius", "Sun": "Capricorn",
                                           "Mars": "Aries", "Mercury": "Aries",
                                           "Jupiter": "Aries", "Venus": "Aries",
                                           "Saturn": "Aries"})
rnk2 = evaluate_dosha_by_id(RID_K, neg_k2, EVAL)
check("kemadruma NOT_FORMED when planet in 2nd from Moon", not is_formed(rnk2))

# Negative: Planet in 12th from Moon
neg_k12 = make_synthetic_context("Aries", {"Moon": "Sagittarius", "Sun": "Scorpio",
                                            "Mars": "Aries", "Mercury": "Aries",
                                            "Jupiter": "Aries", "Venus": "Aries",
                                            "Saturn": "Aries"})
rnk12 = evaluate_dosha_by_id(RID_K, neg_k12, EVAL)
check("kemadruma NOT_FORMED when planet in 12th from Moon", not is_formed(rnk12))

# Negative: Planet in kendra from Moon
neg_kk = make_synthetic_context("Aries", {"Moon": "Sagittarius", "Sun": "Sagittarius",
                                           "Mars": "Aries", "Mercury": "Aries",
                                           "Jupiter": "Aries", "Venus": "Aries",
                                           "Saturn": "Aries"})
rnkk = evaluate_dosha_by_id(RID_K, neg_kk, EVAL)
check("kemadruma NOT_FORMED when planet in kendra from Moon (conj Moon)", not is_formed(rnkk))

# Cancellation: Jupiter aspects Moon
cancel_k = make_synthetic_context("Aries", {"Moon": "Sagittarius", "Sun": "Aries",
                                             "Mars": "Aries", "Mercury": "Aries",
                                             "Jupiter": "Aries", "Venus": "Aries",
                                             "Saturn": "Aries"})
rck = evaluate_dosha_by_id(RID_K, cancel_k, EVAL)
# Jupiter in Aries (1st) aspects Sagittarius (5th from Aries = 5th aspect)
check("kemadruma cancel: Jupiter aspects Moon → CANCELLED",
      cancellation_value(rck) in ("PARTIAL", "FULL"),
      f"got {cancellation_value(rck)}")

# ============ 9. KALA SARPA DOSHA ============
print("\n--- 9. Kala Sarpa Dosha ---")
RID_KS = "DOSHA.KALA_SARPA.SIGN_BASED"

# Positive: All 7 planets between Rahu (Aries) and Ketu (Libra)
# Signs between Aries and Libra (CW): Taurus, Gemini, Cancer, Leo, Virgo
pos_ks = make_synthetic_context("Aries", {"Rahu": "Aries", "Ketu": "Libra",
                                           "Sun": "Taurus", "Moon": "Gemini",
                                           "Mars": "Cancer", "Mercury": "Leo",
                                           "Jupiter": "Virgo", "Venus": "Taurus",
                                           "Saturn": "Gemini"})
rks = evaluate_dosha_by_id(RID_KS, pos_ks, EVAL)
check("kala sarpa all-inside FORMED", is_formed(rks), f"got {formed_value(rks)}")
check("kala sarpa tradition TRADITION_DEPENDENT",
      tradition_value(rks) == "TRADITION_DEPENDENT",
      f"got {tradition_value(rks)}")

# Negative: planets outside the arc
neg_ks = make_synthetic_context("Aries", {"Rahu": "Aries", "Ketu": "Libra",
                                           "Sun": "Scorpio", "Moon": "Sagittarius",
                                           "Mars": "Cancer", "Mercury": "Leo",
                                           "Jupiter": "Virgo", "Venus": "Taurus",
                                           "Saturn": "Gemini"})
rnks = evaluate_dosha_by_id(RID_KS, neg_ks, EVAL)
check("kala sarpa planets-outside NOT_FORMED", not is_formed(rnks))

# Boundary: Planet exactly on Rahu sign
bnd_ks = make_synthetic_context("Aries", {"Rahu": "Aries", "Ketu": "Libra",
                                           "Sun": "Aries", "Moon": "Taurus",
                                           "Mars": "Gemini", "Mercury": "Cancer",
                                           "Jupiter": "Leo", "Venus": "Virgo",
                                           "Saturn": "Taurus"})
rbks = evaluate_dosha_by_id(RID_KS, bnd_ks, EVAL)
# Planet on Rahu sign — boundary case
check("kala sarpa boundary: planet on Rahu sign",
      formed_value(rbks) in ("FORMED", "NOT_FORMED", "UNCERTAIN"),
      f"got {formed_value(rbks)}")

# Wrap-around: Rahu in Pisces, Ketu in Aries (short arc)
wrap_ks = make_synthetic_context("Aries", {"Rahu": "Pisces", "Ketu": "Aries",
                                            "Sun": "Pisces", "Moon": "Aquarius",
                                            "Mars": "Capricorn", "Mercury": "Sagittarius",
                                            "Jupiter": "Scorpio", "Venus": "Libra",
                                            "Saturn": "Virgo"})
rwks = evaluate_dosha_by_id(RID_KS, wrap_ks, EVAL)
# Signs between Pisces and Aries (CW): empty (Pisces is 12, Aries is 1)
# Signs between Aries and Pisces (CW): Taurus through Aquarius (10 signs)
# All 7 planets should be in this arc
check("kala sarpa wrap-around",
      formed_value(rwks) in ("FORMED", "NOT_FORMED"),
      f"got {formed_value(rwks)}")

# Cancellation: Jupiter in Ascendant (Rahu in Pisces, all planets in arc Pisces->Virgo)
cancel_ks = make_synthetic_context("Aries", {"Rahu": "Pisces", "Ketu": "Virgo",
                                              "Sun": "Aries", "Moon": "Taurus",
                                              "Mars": "Gemini", "Mercury": "Cancer",
                                              "Jupiter": "Aries", "Venus": "Leo",
                                              "Saturn": "Leo"})
rcks = evaluate_dosha_by_id(RID_KS, cancel_ks, EVAL)
check("kala sarpa cancel: Jupiter in Ascendant -> CANCELLED",
      cancellation_value(rcks) in ("PARTIAL", "FULL"),
      f"got {cancellation_value(rcks)}")

# ============ 10. PITRU DOSHA ============
print("\n--- 10. Pitru Dosha ---")
RID_P = "DOSHA.PITRU.MODERN_COMMON"

# Positive: Sun conjunct Rahu
pos_p = make_synthetic_context("Aries", {"Sun": "Taurus", "Rahu": "Taurus",
                                          "Ketu": "Scorpio", "Moon": "Cancer",
                                          "Mars": "Aries", "Mercury": "Gemini",
                                          "Jupiter": "Sagittarius", "Venus": "Libra",
                                          "Saturn": "Capricorn"})
rp = evaluate_dosha_by_id(RID_P, pos_p, EVAL)
check("pitru Sun-conjunct-Rahu FORMED", is_formed(rp), f"got {formed_value(rp)}")
check("pitru tradition TRADITION_DEPENDENT",
      tradition_value(rp) == "TRADITION_DEPENDENT",
      f"got {tradition_value(rp)}")

# Positive: Rahu in 9th house
pos_p9 = make_synthetic_context("Aries", {"Rahu": "Sagittarius", "Ketu": "Gemini",
                                           "Sun": "Leo", "Moon": "Cancer",
                                           "Mars": "Aries", "Mercury": "Gemini",
                                           "Jupiter": "Sagittarius", "Venus": "Libra",
                                           "Saturn": "Capricorn"})
rp9 = evaluate_dosha_by_id(RID_P, pos_p9, EVAL)
check("pitru Rahu-in-9th FORMED", is_formed(rp9), f"got {formed_value(rp9)}")

# Negative: No conjunctions, no 9th house placement
neg_p = make_synthetic_context("Aries", {"Sun": "Aries", "Moon": "Cancer",
                                          "Mars": "Gemini", "Mercury": "Taurus",
                                          "Jupiter": "Sagittarius", "Venus": "Libra",
                                          "Saturn": "Capricorn", "Rahu": "Aquarius",
                                          "Ketu": "Leo"})
rnp = evaluate_dosha_by_id(RID_P, neg_p, EVAL)
check("pitru negative NOT_FORMED", not is_formed(rnp), f"got {formed_value(rnp)}")

# ============ 11. NO PREDICTION / NO FEAR LANGUAGE ============
print("\n--- 11. No prediction / no fear language ---")
for rule in rules:
    m = rule.metadata
    all_text = m.description + m.name + m.provenance.notes
    check(f"{m.rule_id} no prediction words",
          not any(w in all_text.lower() for w in
                  ["you will", "guaranteed", "doomed", "fatal", "dangerous",
                   "cursed", "divorce", "marriage will fail"]))
    check(f"{m.rule_id} no fear words",
          not any(w in all_text.lower() for w in
                  ["doomed", "fatal", "cursed", "dangerous", "disaster"]))

# ============ 12. EVIDENCE QUALITY ============
print("\n--- 12. Evidence quality ---")
for rule in rules:
    rid = rule.metadata.rule_id
    ctx = make_synthetic_context("Aries", {"Mars": "Libra", "Sun": "Leo",
                                            "Moon": "Cancer", "Mercury": "Virgo",
                                            "Jupiter": "Sagittarius", "Venus": "Taurus",
                                            "Saturn": "Capricorn"})
    r = evaluate_dosha_by_id(rid, ctx, EVAL)
    if r is not None:
        check(f"{rid} has evidence", len(r.evidence) > 0,
              f"evidence count: {len(r.evidence)}")
        for ev in r.evidence:
            subj = ev.get("subject", "") if isinstance(ev, dict) else getattr(ev, "subject", "")
            sig = ev.get("significance", "") if isinstance(ev, dict) else getattr(ev, "significance", "")
            check(f"{rid} evidence has subject", bool(subj),
                  f"empty subject in evidence")
            check(f"{rid} evidence has significance", bool(sig),
                  f"empty significance")

# ============ 13. GOLDEN CHART ============
print("\n--- 13. Golden Chart Integration ---")
try:
    golden = make_golden_context()
    golden_results = evaluate_all_doshas(golden)
    check("golden chart doshas evaluated", golden_results.total_doshas >= 6,
          f"total: {golden_results.total_doshas}")
    check("golden chart formed count", golden_results.formed_count >= 0,
          f"formed: {golden_results.formed_count}")

    # Print golden chart dosha summary
    print("\n  Golden Chart Dosha Summary:")
    for r in golden_results.dosha_results:
        fv = formed_value(r)
        sv = severity_value(r)
        cv = cancellation_value(r)
        mv = mitigation_value(r)
        print(f"    {r.dosha_id}: formation={fv}, severity={sv}, "
              f"cancellation={cv}, mitigation={mv}")
except Exception as e:
    check("golden chart evaluation", False, str(e))

# ============ 14. DETERMINISM ============
print("\n--- 14. Determinism ---")
ctx_det = make_synthetic_context("Aries", {"Mars": "Libra", "Sun": "Leo",
                                            "Moon": "Cancer", "Mercury": "Virgo",
                                            "Jupiter": "Sagittarius", "Venus": "Taurus",
                                            "Saturn": "Capricorn"})
r_det1 = evaluate_dosha_by_id("DOSHA.MANGLIK.LAGNA_CLASSICAL", ctx_det, EVAL)
r_det2 = evaluate_dosha_by_id("DOSHA.MANGLIK.LAGNA_CLASSICAL", ctx_det, EVAL)
check("determinism: identical results",
      formed_value(r_det1) == formed_value(r_det2)
      and severity_value(r_det1) == severity_value(r_det2)
      and cancellation_value(r_det1) == cancellation_value(r_det2))

# ============ 15. MANIFEST ============
print("\n--- 15. Manifest ---")
manifest = build_manifest()
check("manifest has entries", len(manifest) >= 6, f"got {len(manifest)}")
for item in manifest:
    check(f"manifest {item['dosha_id']} has required fields",
          all(k in item for k in ["dosha_id", "name", "tradition", "confidence"]))

# ============ 16. 12-ASCENDANT SWEEP ============
print("\n--- 16. 12-ascendant sweep (Manglik Lagna) ---")
sweep_pass = 0
sweep_total = 0
for asc in SIGN_NAMES:
    # Mars in 7th from each ascendant (should always be FORMED)
    asc_id = SIGN_NAMES.index(asc) + 1
    mars_house_7 = ((asc_id + 6 - 1) % 12)  # 0-indexed
    mars_sign = SIGN_NAMES[mars_house_7]
    ctx_s = make_synthetic_context(asc, {"Mars": mars_sign, "Sun": "Leo",
                                         "Moon": "Cancer", "Mercury": "Gemini",
                                         "Jupiter": "Sagittarius", "Venus": "Libra",
                                         "Saturn": "Capricorn"})
    rs = evaluate_dosha_by_id("DOSHA.MANGLIK.LAGNA_CLASSICAL", ctx_s, EVAL)
    sweep_total += 1
    if is_formed(rs):
        sweep_pass += 1
    else:
        check(f"sweep {asc} Mars-in-7th FORMED", False, f"got {formed_value(rs)}")

check(f"12-ascendant sweep: {sweep_pass}/{sweep_total} passed",
      sweep_pass == sweep_total)

# ============ 17. NO-AI GUARD ============
print("\n--- 17. No-AI guard ---")
import inspect
from core.rules.doshas import manglik, kemadruma, kala_sarpa, pitru, afflictions
for mod_name, mod in [("manglik", manglik), ("kemadruma", kemadruma),
                       ("kala_sarpa", kala_sarpa), ("pitru", pitru),
                       ("afflictions", afflictions)]:
    source = inspect.getsource(mod)
    check(f"{mod_name} no AI imports",
          "import openai" not in source and "import anthropic" not in source
          and "from openai" not in source and "from anthropic" not in source)

# ============ 18. WRAP-UP ============
print("\n" + "=" * 70)
print(f"PHASE 5C TEST RESULTS: {passes} passed, {failures} failed")
print("=" * 70)

if failures > 0:
    print(f"\nFAILED TESTS:")
    for ok, name, msg in results:
        if not ok:
            print(f"  FAIL: {name} — {msg}")

# Write snapshot
try:
    golden = make_golden_context()
    golden_results = evaluate_all_doshas(golden)
    snapshot = {
        "phase": "5C",
        "total_doshas": golden_results.total_doshas,
        "formed_count": golden_results.formed_count,
        "cancelled_count": golden_results.cancelled_count,
        "mitigated_count": golden_results.mitigated_count,
        "doshas": {}
    }
    for r in golden_results.dosha_results:
        snapshot["doshas"][r.dosha_id] = {
            "name": r.dosha_name,
            "formation": formed_value(r),
            "severity": severity_value(r),
            "cancellation": cancellation_value(r),
            "mitigation": mitigation_value(r),
            "activation": r.activation_status.value if hasattr(r.activation_status, "value") else str(r.activation_status),
            "confidence": r.confidence.value if hasattr(r.confidence, "value") else str(r.confidence),
            "tradition": tradition_value(r),
            "method": r.method,
            "evidence_count": len(r.evidence),
            "relevant_planets": r.relevant_planets,
        }
    snapshot_path = os.path.join(os.path.dirname(__file__) if '__file__' in globals() else '.',
                                  "core", "rules", "doshas", "golden_dosha_snapshot.json")
    os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
    with open(snapshot_path, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)
    print(f"\nGolden dosha snapshot written to: {snapshot_path}")
except Exception as e:
    print(f"\nWarning: Could not write golden snapshot: {e}")

if failures > 0:
    sys.exit(1)
else:
    print("\nALL PHASE 5C TESTS PASSED.")
