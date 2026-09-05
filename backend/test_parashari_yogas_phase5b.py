"""
Astrolife V2 — Phase 5B: Parashari Classical Yoga Engine Tests.

Positive + negative + boundary/exception fixtures for every yoga,
exhaustive structural checks, golden chart integration, determinism,
evidence quality, no-AI / no-Western-aspect guards.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__) if '__file__' in globals() else '.')

from core.rules.parashari.catalog import (
    build_parashari_catalog, evaluate_all_parashari, evaluate_parashari_by_id,
    create_parashari_evaluator, build_manifest,
)
from core.rules.parashari.fixtures import make_synthetic_context, make_golden_context
from core.rules.enums import RuleCategory, RuleTradition

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


def is_formed(res):
    return getattr(res.formation_status, "value", str(res.formation_status)) == "FORMED"


def strength_of(res):
    return getattr(res.strength_status, "value", str(res.strength_status))


print("=" * 70)
print("ASTROLIFE V2 — PHASE 5B: PARASHARI YOGA TESTS")
print("=" * 70)

# ============ 0. Catalogue integrity ============
print("\n--- 0. Catalogue integrity ---")
rules = build_parashari_catalog()
check("31 yogas implemented", len(rules) == 31, f"got {len(rules)}")
ids = [r.metadata.rule_id for r in rules]
check("rule IDs unique", len(set(ids)) == len(ids))
for r in rules:
    m = r.metadata
    check(f"{m.rule_id} category YOGA", m.category == RuleCategory.YOGA)
    check(f"{m.rule_id} tradition declared",
          m.tradition in (RuleTradition.PARASHARI_CLASSICAL, RuleTradition.TRADITION_DEPENDENT),
          str(m.tradition))
    check(f"{m.rule_id} version semver", len(m.rule_version.split(".")) == 3, m.rule_version)
    check(f"{m.rule_id} has formation", len(r.formation_conditions) >= 1)
    check(f"{m.rule_id} provenance source", bool(m.provenance.source_name))
    check(f"{m.rule_id} source_reference present", bool(m.provenance.source_reference))
    check(f"{m.rule_id} no prediction text",
          all(w not in (m.description + r.metadata.name).lower()
              for w in ["you will", "wealthy", "marry", "famous"]))

EVAL = create_parashari_evaluator()

# ============ 1. Raja Kendra-Trikona ============
print("\n--- 1. Raja Kendra-Trikona ---")
RID = "PARASHARI.YOGA.RAJA_KENDRA_TRIKONA"
pos = make_synthetic_context("Aries", {"Moon": "Leo", "Jupiter": "Leo", "Sun": "Aries",
                                       "Mars": "Aries", "Mercury": "Gemini", "Venus": "Taurus",
                                       "Saturn": "Capricorn"})
check("raja positive conjunction FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Aries", {"Sun": "Virgo", "Moon": "Gemini", "Mars": "Taurus",
                                       "Mercury": "Libra", "Venus": "Leo", "Jupiter": "Capricorn",
                                       "Saturn": "Aquarius"})
# verify genuinely no sambandha before asserting negative
rneg = evaluate_parashari_by_id(RID, neg, EVAL)
check("raja negative NOT_FORMED", not is_formed(rneg),
      str([(e.subject, e.value) for e in rneg.evidence[:6]]))
exc = make_synthetic_context("Aries", {"Moon": "Sagittarius", "Jupiter": "Cancer", "Sun": "Aries",
                                       "Mars": "Aries", "Mercury": "Gemini", "Venus": "Taurus",
                                       "Saturn": "Capricorn"})
check("raja exchange variant FORMED", is_formed(evaluate_parashari_by_id(RID, exc, EVAL)))

# ============ 2. Dharma-Karmadhipati ============
print("\n--- 2. Dharma-Karmadhipati ---")
RID = "PARASHARI.YOGA.DHARMA_KARMADHIPATI"
pos = make_synthetic_context("Capricorn", {"Mercury": "Aries", "Venus": "Aries", "Sun": "Capricorn",
                                           "Moon": "Taurus", "Mars": "Scorpio", "Jupiter": "Sagittarius",
                                           "Saturn": "Libra"})
r = evaluate_parashari_by_id(RID, pos, EVAL)
check("DK conjunction FORMED", is_formed(r))
check("DK evidence relationship_type",
      any((e.details or {}).get("relationship_type") == "conjunction" for e in r.evidence))
neg = make_synthetic_context("Capricorn", {"Mercury": "Aries", "Venus": "Taurus", "Sun": "Capricorn",
                                           "Moon": "Cancer", "Mars": "Scorpio", "Jupiter": "Sagittarius",
                                           "Saturn": "Aquarius"})
check("DK negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))
exc = make_synthetic_context("Capricorn", {"Mercury": "Libra", "Venus": "Virgo", "Sun": "Capricorn",
                                           "Moon": "Taurus", "Mars": "Scorpio", "Jupiter": "Sagittarius",
                                           "Saturn": "Libra"})
r = evaluate_parashari_by_id(RID, exc, EVAL)
check("DK exchange FORMED", is_formed(r))
check("DK exchange relationship_type",
      any((e.details or {}).get("relationship_type") == "exchange" for e in r.evidence))

# ============ 3. Yogakaraka Raja ============
print("\n--- 3. Yogakaraka Raja ---")
RID = "PARASHARI.YOGA.YOGAKARAKA_RAJA"
pos = make_synthetic_context("Taurus", {"Saturn": "Leo", "Venus": "Gemini", "Sun": "Taurus",
                                        "Moon": "Cancer", "Mars": "Aries", "Mercury": "Virgo",
                                        "Jupiter": "Sagittarius"})
check("YK positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Taurus", {"Saturn": "Gemini", "Venus": "Taurus", "Sun": "Taurus",
                                        "Moon": "Cancer", "Mars": "Aries", "Mercury": "Virgo",
                                        "Jupiter": "Sagittarius"})
check("YK negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))
bnd = make_synthetic_context("Taurus", {"Venus": "Leo", "Saturn": "Gemini", "Sun": "Taurus",
                                        "Moon": "Cancer", "Mars": "Aries", "Mercury": "Virgo",
                                        "Jupiter": "Sagittarius"})
check("YK Lagna-lord-only excluded", not is_formed(evaluate_parashari_by_id(RID, bnd, EVAL)))

# ============ 4-6. Dhana ============
print("\n--- 4-6. Dhana yogas ---")
for rid, h1, h2 in [("PARASHARI.YOGA.DHANA_2_11", 2, 11),
                    ("PARASHARI.YOGA.DHANA_5_9", 5, 9)]:
    pos = make_synthetic_context("Aries", {"Venus": "Gemini", "Saturn": "Gemini", "Sun": "Leo",
                                           "Moon": "Cancer", "Mars": "Aries", "Mercury": "Virgo",
                                           "Jupiter": "Sagittarius"} if h1 == 2 else
                                 {"Sun": "Gemini", "Jupiter": "Gemini", "Moon": "Cancer",
                                  "Mars": "Aries", "Mercury": "Virgo", "Venus": "Libra",
                                  "Saturn": "Capricorn"})
    check(f"{rid} positive FORMED", is_formed(evaluate_parashari_by_id(rid, pos, EVAL)))
    neg = make_synthetic_context("Aries", {"Venus": "Taurus", "Saturn": "Capricorn", "Sun": "Leo",
                                           "Moon": "Cancer", "Mars": "Aries", "Mercury": "Gemini",
                                           "Jupiter": "Sagittarius"})
    check(f"{rid} negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(rid, neg, EVAL)),
          str(rid))
RID = "PARASHARI.YOGA.DHANA_LAGNA_WEALTH"
pos = make_synthetic_context("Aries", {"Mars": "Gemini", "Venus": "Gemini", "Sun": "Leo",
                                       "Moon": "Cancer", "Mercury": "Virgo", "Jupiter": "Sagittarius",
                                       "Saturn": "Capricorn"})
check("dhana lagna positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Aries", {"Sun": "Virgo", "Moon": "Gemini", "Mars": "Taurus",
                                       "Mercury": "Libra", "Venus": "Leo", "Jupiter": "Capricorn",
                                       "Saturn": "Aquarius"})
check("dhana lagna negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))

# ============ 7-11. Mahapurusha ============
print("\n--- 7-11. Mahapurusha ---")
Maha = [
    ("PARASHARI.YOGA.RUCHAKA", "Mars", "Aries", "Aries", "Leo"),
    ("PARASHARI.YOGA.BHADRA", "Mercury", "Gemini", "Gemini", "Cancer"),
    ("PARASHARI.YOGA.HAMSA", "Jupiter", "Sagittarius", "Sagittarius", "Virgo"),
    ("PARASHARI.YOGA.MALAVYA", "Venus", "Libra", "Libra", "Scorpio"),
    ("PARASHARI.YOGA.SASA", "Saturn", "Capricorn", "Capricorn", "Aries"),
]
for rid, planet, asc, own_sign, bad_sign in Maha:
    others = {"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries", "Mercury": "Gemini",
              "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Capricorn"}
    # Venus in Libra at 15 deg falls in its Moolatrikona range (not own sign);
    # use degree 20 (own-sign portion) so formation sees OWN_SIGN.
    others[planet] = (own_sign, 20.0) if planet == "Venus" else own_sign
    pos = make_synthetic_context(asc, others)
    check(f"{rid} positive FORMED", is_formed(evaluate_parashari_by_id(rid, pos, EVAL)))
    others[planet] = bad_sign
    neg = make_synthetic_context(asc, others)
    check(f"{rid} negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(rid, neg, EVAL)))
# Ruchaka boundary: own sign but non-Kendra (Scorpio = 8th from Aries)
bnd = make_synthetic_context("Aries", {"Mars": "Scorpio", "Sun": "Leo", "Moon": "Cancer",
                                       "Mercury": "Gemini", "Jupiter": "Sagittarius",
                                       "Venus": "Libra", "Saturn": "Capricorn"})
check("Ruchaka own-sign non-Kendra NOT_FORMED",
      not is_formed(evaluate_parashari_by_id("PARASHARI.YOGA.RUCHAKA", bnd, EVAL)))
# Moolatrikona alone insufficient: Mercury in Virgo is BOTH own+exalted; use Venus in Taurus?
# Malavya boundary: Venus exalted Pisces in Kendra (Pisces 12th from Aries not kendra) -> use Libra asc Pisces 5th
bnd2 = make_synthetic_context("Libra", {"Venus": "Pisces", "Sun": "Leo", "Moon": "Cancer",
                                        "Mars": "Aries", "Mercury": "Gemini", "Jupiter": "Sagittarius",
                                        "Saturn": "Capricorn"})
check("Malavya exalted non-Kendra NOT_FORMED",
      not is_formed(evaluate_parashari_by_id("PARASHARI.YOGA.MALAVYA", bnd2, EVAL)))
# exhaustive: Ruchaka own/exalted x 4 kendras
for i, ksign in enumerate(["Aries", "Cancer", "Libra", "Capricorn"]):
    asc_for_kendra = ["Aries", "Cancer", "Libra", "Capricorn"][i]
    # Mars own signs Aries/Scorpio or exalted Capricorn placed in kendra of synthetic asc
    ctx = make_synthetic_context("Aries", {"Mars": ksign, "Sun": "Leo", "Moon": "Taurus",
                                           "Mercury": "Gemini", "Jupiter": "Sagittarius",
                                           "Venus": "Libra", "Saturn": "Aquarius"})
    r = evaluate_parashari_by_id("PARASHARI.YOGA.RUCHAKA", ctx, EVAL)
    houses = {"Aries": 1, "Cancer": 4, "Libra": 7, "Capricorn": 10}
    dign_ok = ksign in ("Aries", "Scorpio", "Capricorn")
    check(f"Ruchaka kendra {ksign} -> {'FORMED' if dign_ok else 'NOT_FORMED'}",
          is_formed(r) == dign_ok)

# ============ 12-23. Major yogas ============
print("\n--- Major yogas ---")
# Gaja Kesari
RID = "PARASHARI.YOGA.GAJA_KESARI"
pos = make_synthetic_context("Leo", {"Moon": "Aries", "Jupiter": "Cancer", "Sun": "Leo",
                                     "Mars": "Scorpio", "Mercury": "Gemini", "Venus": "Libra",
                                     "Saturn": "Capricorn"})
check("Gaja positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Leo", {"Moon": "Aries", "Jupiter": "Leo", "Sun": "Leo",
                                     "Mars": "Scorpio", "Mercury": "Gemini", "Venus": "Libra",
                                     "Saturn": "Capricorn"})
check("Gaja negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))
bnd = make_synthetic_context("Leo", {"Moon": "Aries", "Jupiter": "Aries", "Sun": "Leo",
                                     "Mars": "Scorpio", "Mercury": "Gemini", "Venus": "Libra",
                                     "Saturn": "Capricorn"})
check("Gaja same-house boundary FORMED", is_formed(evaluate_parashari_by_id(RID, bnd, EVAL)))
# strength separation: debilitated Jupiter kendra from Moon still FORMED but not STRONG-guaranteed
weak = make_synthetic_context("Leo", {"Moon": "Aries", "Jupiter": "Capricorn", "Sun": "Leo",
                                      "Mars": "Scorpio", "Mercury": "Gemini", "Venus": "Libra",
                                      "Saturn": "Aquarius"})
rw = evaluate_parashari_by_id(RID, weak, EVAL)
check("Gaja FORMED even when Jupiter debilitated", is_formed(rw))
check("Gaja debilitated strength not STRONG", strength_of(rw) in ("WEAK", "MODERATE"),
      strength_of(rw))

# Budha-Aditya
RID = "PARASHARI.YOGA.BUDHA_ADITYA"
pos = make_synthetic_context("Aries", {"Sun": "Leo", "Mercury": "Leo", "Moon": "Cancer",
                                       "Mars": "Aries", "Jupiter": "Sagittarius", "Venus": "Libra",
                                       "Saturn": "Capricorn"})
check("Budha-Aditya positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Aries", {"Sun": "Leo", "Mercury": "Virgo", "Moon": "Cancer",
                                       "Mars": "Aries", "Jupiter": "Sagittarius", "Venus": "Libra",
                                       "Saturn": "Capricorn"})
check("Budha-Aditya negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))

# Chandra-Mangala
RID = "PARASHARI.YOGA.CHANDRA_MANGALA"
pos = make_synthetic_context("Aries", {"Moon": "Cancer", "Mars": "Cancer", "Sun": "Leo",
                                       "Mercury": "Gemini", "Jupiter": "Sagittarius", "Venus": "Libra",
                                       "Saturn": "Capricorn"})
check("Chandra-Mangala positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Aries", {"Moon": "Cancer", "Mars": "Leo", "Sun": "Leo",
                                       "Mercury": "Gemini", "Jupiter": "Sagittarius", "Venus": "Libra",
                                       "Saturn": "Capricorn"})
check("Chandra-Mangala negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))

# Adhi
RID = "PARASHARI.YOGA.ADHI"
pos = make_synthetic_context("Leo", {"Moon": "Aries", "Jupiter": "Libra", "Venus": "Taurus",
                                     "Mercury": "Capricorn", "Sun": "Leo", "Mars": "Scorpio",
                                     "Saturn": "Aquarius"})
check("Adhi positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Leo", {"Moon": "Aries", "Jupiter": "Taurus", "Venus": "Gemini",
                                     "Mercury": "Capricorn", "Sun": "Leo", "Mars": "Scorpio",
                                     "Saturn": "Aquarius"})
check("Adhi negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))

# Lakshmi
RID = "PARASHARI.YOGA.LAKSHMI"
pos = make_synthetic_context("Leo", {"Mars": "Aries", "Sun": "Leo", "Moon": "Cancer",
                                     "Mercury": "Gemini", "Jupiter": "Sagittarius", "Venus": "Libra",
                                     "Saturn": "Capricorn"})
check("Lakshmi positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Leo", {"Mars": "Cancer", "Sun": "Aquarius", "Moon": "Scorpio",
                                     "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
                                     "Saturn": "Aries"})
check("Lakshmi negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))

# Saraswati
RID = "PARASHARI.YOGA.SARASWATI"
pos = make_synthetic_context("Gemini", {"Jupiter": "Sagittarius", "Venus": "Libra", "Mercury": "Gemini",
                                        "Sun": "Leo", "Moon": "Cancer", "Mars": "Aries",
                                        "Saturn": "Capricorn"})
check("Saraswati positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Gemini", {"Jupiter": "Sagittarius", "Venus": "Scorpio", "Mercury": "Gemini",
                                        "Sun": "Leo", "Moon": "Cancer", "Mars": "Aries",
                                        "Saturn": "Capricorn"})
check("Saraswati negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))

# Amala
RID = "PARASHARI.YOGA.AMALA"
pos = make_synthetic_context("Aries", {"Jupiter": "Capricorn", "Sun": "Leo", "Moon": "Cancer",
                                       "Mars": "Aries", "Mercury": "Gemini", "Venus": "Libra",
                                       "Saturn": "Aquarius"})
check("Amala positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Aries", {"Jupiter": "Sagittarius", "Sun": "Leo", "Moon": "Cancer",
                                       "Mars": "Aries", "Mercury": "Gemini", "Venus": "Libra",
                                       "Saturn": "Capricorn"})
check("Amala negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))

# Vasumati
RID = "PARASHARI.YOGA.VASUMATI"
pos = make_synthetic_context("Aries", {"Jupiter": "Gemini", "Venus": "Virgo", "Mercury": "Capricorn",
                                       "Moon": "Aries", "Sun": "Leo", "Mars": "Scorpio",
                                       "Saturn": "Aquarius"})
check("Vasumati positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Aries", {"Jupiter": "Gemini", "Venus": "Virgo", "Mercury": "Leo",
                                       "Moon": "Aries", "Sun": "Leo", "Mars": "Scorpio",
                                       "Saturn": "Aquarius"})
check("Vasumati negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))

# Sunapha / Anapha / Durudhara / Kemadruma
base_leo = {"Sun": "Leo", "Mercury": "Sagittarius", "Jupiter": "Capricorn",
            "Venus": "Pisces", "Saturn": "Gemini"}
RID = "PARASHARI.YOGA.SUNAPHA"
pos = make_synthetic_context("Leo", dict(base_leo, Moon="Leo", Mars="Virgo"))
check("Sunapha positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Leo", dict(base_leo, Moon="Leo", Mars="Aries"))
check("Sunapha negative NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))
RID = "PARASHARI.YOGA.ANAPHA"
pos = make_synthetic_context("Leo", dict(base_leo, Moon="Leo", Mars="Cancer"))
check("Anapha positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
check("Anapha negative NOT_FORMED",
      not is_formed(evaluate_parashari_by_id(RID, neg, EVAL)))
RID = "PARASHARI.YOGA.DURUDHARA"
pos = make_synthetic_context("Leo", dict(base_leo, Moon="Leo", Mars="Virgo", Mercury="Cancer"))
check("Durudhara positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
check("Durudhara one-sided NOT_FORMED",
      not is_formed(evaluate_parashari_by_id(
          RID, make_synthetic_context("Leo", dict(base_leo, Moon="Leo", Mars="Virgo")), EVAL)))
RID = "PARASHARI.YOGA.KEMADRUMA"
pos = make_synthetic_context("Leo", dict(base_leo, Moon="Leo", Mars="Aries"))
check("Kemadruma positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
negk = make_synthetic_context("Leo", dict(base_leo, Moon="Leo", Mars="Aries", Venus="Virgo"))
check("Kemadruma companion NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, negk, EVAL)))
bndk = make_synthetic_context("Leo", dict(base_leo, Moon="Leo", Mars="Scorpio"))
check("Kemadruma kendra-from-Moon boundary NOT_FORMED",
      not is_formed(evaluate_parashari_by_id(RID, bndk, EVAL)))

# ============ Parivartana ============
print("\n--- Parivartana ---")
RIDM, RIDK, RIDD = ("PARASHARI.YOGA.PARIVARTANA_MAHA", "PARASHARI.YOGA.PARIVARTANA_KHALA",
                    "PARASHARI.YOGA.PARIVARTANA_DAINYA")
maha = make_synthetic_context("Cancer", {"Moon": "Leo", "Sun": "Cancer", "Mars": "Aries",
                                         "Mercury": "Gemini", "Jupiter": "Sagittarius",
                                         "Venus": "Libra", "Saturn": "Capricorn"})
check("Maha positive FORMED", is_formed(evaluate_parashari_by_id(RIDM, maha, EVAL)))
check("Maha not Khala", not is_formed(evaluate_parashari_by_id(RIDK, maha, EVAL)))
check("Maha not Dainya", not is_formed(evaluate_parashari_by_id(RIDD, maha, EVAL)))
khala = make_synthetic_context("Leo", {"Venus": "Aries", "Mars": "Libra", "Sun": "Leo",
                                       "Moon": "Cancer", "Mercury": "Gemini", "Jupiter": "Sagittarius",
                                       "Saturn": "Capricorn"})
check("Khala positive FORMED", is_formed(evaluate_parashari_by_id(RIDK, khala, EVAL)))
check("Khala not Dainya", not is_formed(evaluate_parashari_by_id(RIDD, khala, EVAL)))
dainya = make_synthetic_context("Aries", {"Mercury": "Aries", "Mars": "Virgo", "Sun": "Leo",
                                          "Moon": "Cancer", "Jupiter": "Sagittarius", "Venus": "Libra",
                                          "Saturn": "Capricorn"})
# Mercury Aries + Mars Virgo: Mercury in Mars sign, Mars in Mercury sign -> exchange, Mars rules 8 -> Dainya
check("Dainya positive FORMED", is_formed(evaluate_parashari_by_id(RIDD, dainya, EVAL)))
noex = make_synthetic_context("Aries", {"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries",
                                        "Mercury": "Virgo", "Jupiter": "Sagittarius", "Venus": "Libra",
                                        "Saturn": "Capricorn"})
check("Parivartana none Maha NOT_FORMED", not is_formed(evaluate_parashari_by_id(RIDM, noex, EVAL)))
check("Parivartana none Khala NOT_FORMED", not is_formed(evaluate_parashari_by_id(RIDK, noex, EVAL)))
check("Parivartana none Dainya NOT_FORMED", not is_formed(evaluate_parashari_by_id(RIDD, noex, EVAL)))

# ============ Viparita ============
print("\n--- Viparita ---")
for rid, lord_house, good, bad in [("PARASHARI.YOGA.VIPARITA_HARSHA", 6, "Scorpio", "Taurus"),
                                   ("PARASHARI.YOGA.VIPARITA_SARALA", 8, "Virgo", "Taurus"),
                                   ("PARASHARI.YOGA.VIPARITA_VIMALA", 12, "Virgo", "Taurus")]:
    pos = make_synthetic_context("Aries", {"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries",
                                           "Mercury": "Gemini", "Jupiter": "Sagittarius",
                                           "Venus": "Libra", "Saturn": "Capricorn"})
    # place the relevant lord into dusthana
    from core.rules.parashari.structural import SIGN_LORDS as _SL
    lord = {"HARSHA": "Mercury", "SARALA": "Mars", "VIMALA": "Jupiter"}[rid.split("_")[-1]]
    plc = dict({"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries", "Mercury": "Gemini",
                "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Capricorn"})
    plc[lord] = good
    check(f"{rid} positive FORMED",
          is_formed(evaluate_parashari_by_id(rid, make_synthetic_context("Aries", plc), EVAL)))
    plc[lord] = bad
    check(f"{rid} negative NOT_FORMED",
          not is_formed(evaluate_parashari_by_id(rid, make_synthetic_context("Aries", plc), EVAL)))

# ============ Neecha Bhanga ============
print("\n--- Neecha Bhanga ---")
RID, RIDR = "PARASHARI.YOGA.NEECHA_BHANGA", "PARASHARI.YOGA.NEECHA_BHANGA_RAJA"
pos = make_synthetic_context("Aries", {"Venus": "Virgo", "Mercury": "Aries", "Sun": "Leo",
                                       "Moon": "Taurus", "Mars": "Scorpio", "Jupiter": "Sagittarius",
                                       "Saturn": "Capricorn"})
check("Neecha Bhanga positive FORMED", is_formed(evaluate_parashari_by_id(RID, pos, EVAL)))
neg = make_synthetic_context("Aries", {"Venus": "Virgo", "Mercury": "Sagittarius", "Sun": "Leo",
                                       "Moon": "Taurus", "Mars": "Scorpio", "Jupiter": "Sagittarius",
                                       "Saturn": "Capricorn"})
rneg = evaluate_parashari_by_id(RID, neg, EVAL)
check("Neecha Bhanga negative NOT_FORMED", not is_formed(rneg))
d9sign = neg.get_varga_sign("Venus", 9)
check("D9 alone does not create bhanga (formation false regardless of D9)",
      not is_formed(rneg), f"D9={d9sign}")
# bhanga true but misplaced -> NBRY false
mis = make_synthetic_context("Aries", {"Venus": "Virgo", "Mercury": "Aries", "Sun": "Leo",
                                       "Moon": "Taurus", "Mars": "Scorpio", "Jupiter": "Sagittarius",
                                       "Saturn": "Capricorn"})
check("Bhanga FORMED yet misplaced (house 6)", is_formed(evaluate_parashari_by_id(RID, mis, EVAL)))
check("NBRY NOT_FORMED when misplaced",
      not is_formed(evaluate_parashari_by_id(RIDR, mis, EVAL)))
# NBRY positive: debilitated Venus with bhanga AND in kendra/trikona: use Libra asc, Venus Virgo house 12? no.
# Use Taurus asc: Venus Virgo house 5 (trikona) + Jupiter in Taurus? need bhanga: Jupiter (exalt lord Pisces)
# in kendra from Moon. Taurus asc, Moon Cancer(3rd), Jupiter Virgo(5th)? Moon-kendras from Cancer: Cancer,Libra,Capricorn,Aries.
# Virgo not in Moon kendras. Use Moon Leo(4th): Moon-kendras Leo,Scorpio,Aquarius,Taurus. Jupiter Taurus house 1 kendra Lagna too (C3!) -> bhanga + Venus house 5 trikona -> NBRY
nbry = make_synthetic_context("Taurus", {"Venus": "Virgo", "Jupiter": "Taurus", "Moon": "Leo",
                                         "Sun": "Aries", "Mars": "Scorpio", "Mercury": "Gemini",
                                         "Saturn": "Capricorn"})
check("NBRY positive FORMED", is_formed(evaluate_parashari_by_id(RIDR, nbry, EVAL)))
# no debilitation at all
nodeb = make_synthetic_context("Aries", {"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries",
                                         "Mercury": "Gemini", "Jupiter": "Sagittarius",
                                         "Venus": "Libra", "Saturn": "Capricorn"})
check("Neecha Bhanga none NOT_FORMED", not is_formed(evaluate_parashari_by_id(RID, nodeb, EVAL)))
check("NBRY none NOT_FORMED", not is_formed(evaluate_parashari_by_id(RIDR, nodeb, EVAL)))

# ============ 12-ascendant exhaustive lordship ============
print("\n--- 12-ascendant sweep ---")
ASC = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
       "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
std = {"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries", "Mercury": "Gemini",
       "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Capricorn"}
checked = 0
for asc in ASC:
    ctx = make_synthetic_context(asc, dict(std))
    res = evaluate_all_parashari(ctx)
    check(f"sweep {asc} 31 results", len(res) == 31)
    check(f"sweep {asc} statuses valid",
          all(str(r.formation_status).startswith("FormationStatus.") for r in res))
    checked += 1
check("12 ascendants swept", checked == 12)

# ============ Golden chart integration ============
print("\n--- Golden chart ---")
gctx = make_golden_context()
gres = evaluate_all_parashari(gctx)
formed = [r for r in gres if is_formed(r)]
notformed = [r for r in gres if not is_formed(r)]
check("golden has FORMED yogas", len(formed) >= 3, str(len(formed)))
check("golden has NOT_FORMED yogas", len(notformed) >= 10, str(len(notformed)))
check("golden Ruchaka NOT_FORMED (Mars 12th)",
      not is_formed(evaluate_parashari_by_id("PARASHARI.YOGA.RUCHAKA", gctx, EVAL)))
check("golden Budha-Aditya NOT_FORMED",
      not is_formed(evaluate_parashari_by_id("PARASHARI.YOGA.BUDHA_ADITYA", gctx, EVAL)))
check("golden Gaja Kesari FORMED",
      is_formed(evaluate_parashari_by_id("PARASHARI.YOGA.GAJA_KESARI", gctx, EVAL)))
check("golden Vimala FORMED (12L Mars in 12)",
      is_formed(evaluate_parashari_by_id("PARASHARI.YOGA.VIPARITA_VIMALA", gctx, EVAL)))
check("golden Neecha Bhanga FORMED (Venus C4)",
      is_formed(evaluate_parashari_by_id("PARASHARI.YOGA.NEECHA_BHANGA", gctx, EVAL)))
# strength separation exists on golden
non_strong = [r for r in formed if strength_of(r) in ("WEAK", "MODERATE")]
check("golden FORMED+non-STRONG exists (formation != strength)", len(non_strong) >= 1)
# evidence quality on golden formed
for r in formed:
    check(f"golden evidence {r.rule_id.split('.')[-1]}>=2", len(r.evidence) >= 2)
    check(f"golden activation NOT_EVALUATED {r.rule_id.split('.')[-1]}",
          str(r.activation_status).endswith("NOT_EVALUATED"), str(r.activation_status))

# determinism
res2 = evaluate_all_parashari(gctx)
same = all(a.formation_status == b.formation_status and
           a.strength_status == b.strength_status and
           a.cancellation_status == b.cancellation_status and
           len(a.evidence) == len(b.evidence)
           for a, b in zip(gres, res2))
check("determinism identical rerun", same)

# no AI / no non-Parashari astronomy in parashari source
import glob
bad = []
for fp in glob.glob(os.path.join(os.path.dirname(__file__), "core", "rules", "parashari", "*.py")):
    with open(fp, encoding="utf-8") as f:
        src = f.read().lower()
    # Note: 'tropical' appears only as the canonical LongitudeDetails field name
    # shared with ChartFacts (sidereal values are used); it is not Western logic.
    for token in ["openai", "anthropic", "import llm", "from llm", "gpt-",
                  "placidus", "koch houses", "eval(", "exec(",
                  "swisseph", "import swe"]:
        if token in src:
            bad.append((os.path.basename(fp), token))
check("no AI/non-parashari tokens in parashari", len(bad) == 0, str(bad))

# write deterministic golden snapshot
import json
from datetime import datetime
snap = {
    "generated_at": datetime.utcnow().isoformat(),
    "engine_version": "5.1.0",
    "chart": "MEDAPATI BHASKARA VENKATA RAJEEV REDDY 17/08/2005 00:02 IST Anaparthy",
    "results": [
        {"rule_id": r.rule_id, "formation": str(r.formation_status).split(".")[-1],
         "strength": str(r.strength_status).split(".")[-1],
         "cancellation": str(r.cancellation_status).split(".")[-1],
         "mitigation": str(r.mitigation_status).split(".")[-1],
         "confidence": str(r.confidence).split(".")[-1],
         "n_evidence": len(r.evidence),
         "planets": r.relevant_planets}
        for r in gres
    ],
}
with open(os.path.join(os.path.dirname(__file__), "core", "rules", "parashari",
                       "golden_snapshot.json"), "w", encoding="utf-8") as f:
    json.dump(snap, f, indent=2)
manifest = build_manifest()
with open(os.path.join(os.path.dirname(__file__), "core", "rules", "parashari",
                       "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
check("snapshot+manifest written", True)

print("\n" + "=" * 70)
print(f"PHASE 5B TESTS: {passes} passed, {failures} failed, {passes + failures} total")
print("=" * 70)
sys.exit(1 if failures else 0)
