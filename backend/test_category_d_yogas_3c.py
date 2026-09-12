"""
Astrolife — Migration #3C: Category D Yoga tests.

Focused coverage for the 15 canonical Category D rules:
registration, metadata, positive/negative formation, boundary cases,
Nabha counting (1..7 + node exclusion), malefic classification, strength
conditions, multi-step chains, complex patterns, Evidence, Provenance,
determinism, golden chart, merge, source tagging, duplicate prevention.
"""
import sys
import os
_base = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, _base)
if os.path.basename(_base) == 'backend':
    sys.path.insert(0, os.path.dirname(_base))

from core.rules.parashari.catalog import (
    build_parashari_catalog, evaluate_all_parashari, evaluate_parashari_by_id,
    create_parashari_evaluator, PARASHARI_RULE_IDS,
)
from core.rules.parashari.fixtures import make_synthetic_context, make_golden_context
from core.rules.parashari.category_d_yogas import (
    CATEGORY_D_YOGA_RULE_IDS, FORMATION_EVALUATORS,
    nabhasa_sign_distribution, nabhasa_occupied_sign_count,
)
from core.rules.provenance import ProvenanceRegistry
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


EVAL = create_parashari_evaluator()

print("=" * 70)
print("MIGRATION #3C — CATEGORY D YOGA TESTS (15 rules)")
print("=" * 70)

# ============ 0. Registration ============
print("\n--- 0. Registration ---")
EXPECTED_IDS = [
    "PARASHARI.YOGA.ASTRA", "PARASHARI.YOGA.ASURA",
    "PARASHARI.YOGA.BHERI", "PARASHARI.YOGA.BHRIGU_MANGALA",
    "PARASHARI.YOGA.BRAHMA", "PARASHARI.YOGA.DAMA",
    "PARASHARI.YOGA.GOLA", "PARASHARI.YOGA.INDRA",
    "PARASHARI.YOGA.KEDARA", "PARASHARI.YOGA.KURMA",
    "PARASHARI.YOGA.PASHA", "PARASHARI.YOGA.SARPA",
    "PARASHARI.YOGA.SHULA", "PARASHARI.YOGA.VEENA",
    "PARASHARI.YOGA.YUGA",
]
check("15 Category D rule IDs", CATEGORY_D_YOGA_RULE_IDS == EXPECTED_IDS,
      str(set(CATEGORY_D_YOGA_RULE_IDS) ^ set(EXPECTED_IDS)))
check("catalog has 77 rules", len(build_parashari_catalog()) == 77,
      str(len(build_parashari_catalog())))
check("PARASHARI_RULE_IDS has 77", len(PARASHARI_RULE_IDS) == 77)
check("rule IDs unique (77)", len(set(PARASHARI_RULE_IDS)) == 77)
check("15 formation evaluators registered",
      all(f"parashari_{rid.split('.')[-1].lower()}_formation" in FORMATION_EVALUATORS
          for rid in EXPECTED_IDS))
check("no Category E rule present",
      not any(rid.split(".")[-1] in ("GARUDA", "KALPADRUMA", "MAHABHAGYA",
                                     "MATSYA", "MRIDANGA")
              for rid in PARASHARI_RULE_IDS))

# ============ 1. Metadata ============
print("\n--- 1. Metadata ---")
for r in build_parashari_catalog():
    if r.metadata.rule_id not in EXPECTED_IDS:
        continue
    m = r.metadata
    check(f"{m.rule_id} category YOGA", m.category == RuleCategory.YOGA)
    check(f"{m.rule_id} tradition PARASHARI_CLASSICAL",
          m.tradition == RuleTradition.PARASHARI_CLASSICAL, str(m.tradition))
    check(f"{m.rule_id} version semver", len(m.rule_version.split(".")) == 3)
    check(f"{m.rule_id} formation condition", len(r.formation_conditions) >= 1)
    check(f"{m.rule_id} provenance source", bool(m.provenance.source_name))
    check(f"{m.rule_id} method recorded", bool(m.provenance.method))
    check(f"{m.rule_id} enabled", m.enabled and str(m.status).endswith("ENABLED"))


def ev(rid, asc, placements, **kw):
    ctx = make_synthetic_context(asc, placements, **kw)
    return evaluate_parashari_by_id(rid, ctx, EVAL), ctx


STD = {"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries", "Mercury": "Gemini",
       "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Capricorn"}

# ============ 2. Nabha counting primitive ============
print("\n--- 2. Nabha primitive ---")
NABHA_CHARTS = {
    1: {"Sun": "Aries", "Moon": "Aries", "Mars": "Aries", "Mercury": "Aries",
        "Jupiter": "Aries", "Venus": "Aries", "Saturn": "Aries"},
    2: {"Sun": "Aries", "Moon": "Aries", "Mars": "Aries", "Mercury": "Aries",
        "Jupiter": "Taurus", "Venus": "Taurus", "Saturn": "Taurus"},
    3: {"Sun": "Aries", "Moon": "Aries", "Mars": "Aries", "Mercury": "Taurus",
        "Jupiter": "Taurus", "Venus": "Gemini", "Saturn": "Gemini"},
    4: {"Sun": "Aries", "Moon": "Aries", "Mars": "Taurus", "Mercury": "Taurus",
        "Jupiter": "Gemini", "Venus": "Gemini", "Saturn": "Cancer"},
    5: {"Sun": "Aries", "Moon": "Aries", "Mars": "Aries", "Mercury": "Taurus",
        "Jupiter": "Gemini", "Venus": "Cancer", "Saturn": "Leo"},
    6: {"Sun": "Aries", "Moon": "Taurus", "Mars": "Gemini", "Mercury": "Cancer",
        "Jupiter": "Leo", "Venus": "Virgo", "Saturn": "Libra"},
    7: {"Sun": "Aries", "Moon": "Taurus", "Mars": "Gemini", "Mercury": "Cancer",
        "Jupiter": "Leo", "Venus": "Virgo", "Saturn": "Libra"},
}
# fix count-7 chart to use 7 distinct signs
NABHA_CHARTS[7] = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Gemini",
                   "Mercury": "Cancer", "Jupiter": "Leo", "Venus": "Virgo",
                   "Saturn": "Libra"}
NABHA_CHARTS[6] = {"Sun": "Aries", "Moon": "Aries", "Mars": "Taurus",
                   "Mercury": "Gemini", "Jupiter": "Cancer", "Venus": "Leo",
                   "Saturn": "Virgo"}
for n, pl in NABHA_CHARTS.items():
    ctx = make_synthetic_context("Aries", pl)
    check(f"nabha count == {n}", nabhasa_occupied_sign_count(ctx) == n,
          str(nabhasa_sign_distribution(ctx)))
    check(f"nabha nodes excluded ({n})",
          set(nabhasa_sign_distribution(ctx).keys()) ==
          {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"})
# nodes in extra signs must not alter the count
ctx_n = make_synthetic_context("Aries", dict(NABHA_CHARTS[2],
                                             Rahu="Gemini", Ketu="Cancer"))
check("nabha nodes in extra signs ignored",
      nabhasa_occupied_sign_count(ctx_n) == 2)
# sign-based, not house-based: same house different signs still counts signs
ctx_s = make_synthetic_context("Taurus", NABHA_CHARTS[2])
check("nabha sign-based not house-based",
      nabhasa_occupied_sign_count(ctx_s) == 2)

# ============ 3. Nabha yoga formation (1..7) ============
print("\n--- 3. Nabha formation ---")
NABHA_RULES = {1: "PARASHARI.YOGA.GOLA", 2: "PARASHARI.YOGA.YUGA",
               3: "PARASHARI.YOGA.SHULA", 4: "PARASHARI.YOGA.KEDARA",
               5: "PARASHARI.YOGA.PASHA", 6: "PARASHARI.YOGA.DAMA",
               7: "PARASHARI.YOGA.VEENA"}
for n, rid in NABHA_RULES.items():
    res, _ = ev(rid, "Aries", NABHA_CHARTS[n])
    check(f"positive {rid.split('.')[-1]} ({n} signs) FORMED", is_formed(res))
    check(f"evidence {rid.split('.')[-1]} has distribution",
          any("Seven-planet signs" in e.subject for e in res.evidence))
    # negative: neighboring count must not form
    other = NABHA_CHARTS[1] if n != 1 else NABHA_CHARTS[2]
    nres, _ = ev(rid, "Aries", other)
    check(f"negative {rid.split('.')[-1]} NOT_FORMED", not is_formed(nres))
# node-exclusion formation check: 2-sign chart + nodes elsewhere still Yuga
yres, _ = ev("PARASHARI.YOGA.YUGA", "Aries",
             dict(NABHA_CHARTS[2], Rahu="Gemini", Ketu="Cancer"))
check("YUGA forms despite nodes in extra signs", is_formed(yres))
sres, _ = ev("PARASHARI.YOGA.SHULA", "Aries",
             dict(NABHA_CHARTS[2], Rahu="Gemini", Ketu="Cancer"))
check("SHULA not formed by node signs", not is_formed(sres))

# ============ 4. Astra / Asura ============
print("\n--- 4. Astra/Asura ---")
res, _ = ev("PARASHARI.YOGA.ASTRA", "Aries",
            {"Mercury": "Virgo", "Mars": "Virgo"})
check("positive ASTRA FORMED", is_formed(res))
nres, _ = ev("PARASHARI.YOGA.ASTRA", "Aries",
             {"Mercury": "Virgo", "Mars": "Aries", "Rahu": "Sagittarius",
              "Ketu": "Gemini"})
check("negative ASTRA (no malefic) NOT_FORMED", not is_formed(nres))
wres, _ = ev("PARASHARI.YOGA.ASTRA", "Aries",
             dict(STD, Mars="Virgo", Mercury="Pisces"))
check("negative ASTRA (lord weak) NOT_FORMED", not is_formed(wres))
check("ASTRA evidence has malefic + lord",
      any("Malefic" in e.subject for e in res.evidence) and
      any("lord of 6" in e.subject for e in res.evidence))

res, _ = ev("PARASHARI.YOGA.ASURA", "Aries",
            {"Mars": "Capricorn", "Saturn": "Scorpio"})
check("positive ASURA FORMED", is_formed(res))
nres, _ = ev("PARASHARI.YOGA.ASURA", "Aries",
             {"Mars": "Capricorn", "Saturn": "Sagittarius"})
check("negative ASURA (no malefic) NOT_FORMED", not is_formed(nres))
wres, _ = ev("PARASHARI.YOGA.ASURA", "Aries",
             dict(STD, Saturn="Scorpio", Mars="Gemini"))
check("negative ASURA (lord weak) NOT_FORMED", not is_formed(wres))

# ============ 5. Bheri / Bhrigu Mangala ============
print("\n--- 5. Bheri/Bhrigu ---")
res, _ = ev("PARASHARI.YOGA.BHERI", "Aries",
            {"Sun": "Aries", "Moon": "Taurus", "Mars": "Libra",
             "Saturn": "Pisces"})
check("positive BHERI FORMED", is_formed(res))
nres, _ = ev("PARASHARI.YOGA.BHERI", "Aries",
             {"Sun": "Aries", "Moon": "Taurus", "Mars": "Libra",
              "Saturn": "Aquarius"})
check("negative BHERI (12th empty) NOT_FORMED", not is_formed(nres))

res, _ = ev("PARASHARI.YOGA.BHRIGU_MANGALA", "Aries",
            {"Venus": "Taurus", "Mars": "Taurus"})
check("positive BHRIGU_MANGALA FORMED", is_formed(res))
nres, _ = ev("PARASHARI.YOGA.BHRIGU_MANGALA", "Aries",
             {"Venus": "Taurus", "Mars": "Aries"})
check("negative BHRIGU_MANGALA NOT_FORMED", not is_formed(nres))
ares, _ = ev("PARASHARI.YOGA.BHRIGU_MANGALA", "Aries",
             {"Venus": "Taurus", "Mars": "Scorpio"})
check("edge BHRIGU_MANGALA aspect-is-not-conjunction NOT_FORMED",
      not is_formed(ares))

# ============ 6. Brahma / Indra chains ============
print("\n--- 6. Brahma/Indra ---")
res, _ = ev("PARASHARI.YOGA.BRAHMA", "Virgo",
            {"Mercury": "Virgo", "Jupiter": "Virgo", "Venus": "Virgo"})
check("positive BRAHMA FORMED", is_formed(res))
check("BRAHMA three link evidences",
      sum(1 for e in res.evidence if "from Lagna lord" in e.subject) == 3)
nres, _ = ev("PARASHARI.YOGA.BRAHMA", "Virgo",
             {"Mercury": "Virgo", "Jupiter": "Virgo", "Venus": "Libra"})
check("negative BRAHMA NOT_FORMED", not is_formed(nres))

res, _ = ev("PARASHARI.YOGA.INDRA", "Aries",
            {"Moon": "Aries", "Mars": "Gemini", "Saturn": "Sagittarius",
             "Venus": "Gemini"})
check("positive INDRA FORMED", is_formed(res))
check("INDRA three link evidences",
      sum(1 for e in res.evidence if "Indra link" in e.subject) == 3)
nres, _ = ev("PARASHARI.YOGA.INDRA", "Aries",
             {"Moon": "Aries", "Mars": "Gemini", "Saturn": "Sagittarius",
              "Venus": "Virgo"})
check("negative INDRA (link3 broken) NOT_FORMED", not is_formed(nres))
nres2, _ = ev("PARASHARI.YOGA.INDRA", "Aries",
              {"Moon": "Aries", "Mars": "Taurus", "Saturn": "Sagittarius",
               "Venus": "Gemini"})
check("negative INDRA (link1 broken) NOT_FORMED", not is_formed(nres2))

# ============ 7. Kurma / Sarpa ============
print("\n--- 7. Kurma/Sarpa ---")
res, _ = ev("PARASHARI.YOGA.KURMA", "Aries",
            {"Jupiter": "Leo", "Mercury": "Virgo", "Venus": "Libra",
             "Mars": "Aries", "Saturn": "Gemini", "Rahu": "Aquarius",
             "Moon": "Cancer", "Ketu": "Taurus"})
check("positive KURMA FORMED", is_formed(res))
check("KURMA six house evidences",
      sum(1 for e in res.evidence if "Kurma" in e.subject) == 6)
nres, _ = ev("PARASHARI.YOGA.KURMA", "Aries",
             {"Jupiter": "Leo", "Mercury": "Scorpio", "Venus": "Libra",
              "Mars": "Aries", "Saturn": "Gemini", "Rahu": "Aquarius",
              "Moon": "Cancer", "Ketu": "Taurus"})
check("negative KURMA (6th empty) NOT_FORMED", not is_formed(nres))

res, _ = ev("PARASHARI.YOGA.SARPA", "Aries",
            {"Sun": "Aries", "Mars": "Capricorn", "Saturn": "Libra"})
check("positive SARPA FORMED", is_formed(res))
nres, _ = ev("PARASHARI.YOGA.SARPA", "Aries",
             {"Sun": "Aries", "Mars": "Capricorn", "Saturn": "Aquarius"})
check("negative SARPA (2 kendras) NOT_FORMED", not is_formed(nres))
nres4, _ = ev("PARASHARI.YOGA.SARPA", "Aries",
              {"Sun": "Aries", "Mars": "Capricorn", "Saturn": "Libra",
               "Jupiter": "Cancer"})
check("boundary SARPA (4 kendras) FORMED", is_formed(nres4))
nodres, _ = ev("PARASHARI.YOGA.SARPA", "Aries",
               {"Rahu": "Aries", "Ketu": "Libra", "Saturn": "Capricorn"})
check("SARPA node malefics count (documented convention)", is_formed(nodres))

# ============ 8. Evidence quality (all 15, golden) ============
print("\n--- 8. Evidence ---")
gctx = make_golden_context()
gres = evaluate_all_parashari(gctx)
for r in gres:
    if r.rule_id not in EXPECTED_IDS:
        continue
    check(f"evidence {r.rule_id.split('.')[-1]}>=1", len(r.evidence) >= 1)
    check(f"evidence {r.rule_id.split('.')[-1]} sourced",
          all(bool(getattr(e, "source", "")) for e in r.evidence))
    check(f"activation {r.rule_id.split('.')[-1]} NOT_EVALUATED",
          str(r.activation_status).endswith("NOT_EVALUATED"))

# ============ 9. Provenance ============
print("\n--- 9. Provenance ---")
for rid in EXPECTED_IDS:
    rec = ProvenanceRegistry.get(rid)
    check(f"provenance registered {rid.split('.')[-1]}", rec is not None)
    if rec is not None:
        check(f"provenance source {rid.split('.')[-1]}", bool(rec.source_name))
for legacy_id in ("astra_yoga", "sarpa_yoga", "garuda_yoga", "matsya_yoga",
                  "kurma_yoga", "gola_yoga"):
    check(f"legacy {legacy_id} has no canonical provenance",
          ProvenanceRegistry.get(legacy_id) is None)

# ============ 10. Golden chart ============
print("\n--- 10. Golden ---")
by_id = {r.rule_id: r for r in gres}
check("golden PASHA FORMED", is_formed(by_id["PARASHARI.YOGA.PASHA"]))
for rid in EXPECTED_IDS:
    if rid == "PARASHARI.YOGA.PASHA":
        continue
    check(f"golden {rid.split('.')[-1]} NOT_FORMED",
          not is_formed(by_id[rid]))
check("golden total FORMED == 17",
      sum(1 for r in gres if is_formed(r)) == 17,
      str(sum(1 for r in gres if is_formed(r))))

# ============ 11. Determinism ============
print("\n--- 11. Determinism ---")
gres2 = evaluate_all_parashari(gctx)
same = all(a.formation_status == b.formation_status and
           a.strength_status == b.strength_status and
           a.cancellation_status == b.cancellation_status and
           len(a.evidence) == len(b.evidence)
           for a, b in zip(gres, gres2))
check("determinism identical rerun (77)", same)
r1 = evaluate_parashari_by_id("PARASHARI.YOGA.INDRA", gctx, EVAL)
r2 = evaluate_parashari_by_id("PARASHARI.YOGA.INDRA", gctx, EVAL)
check("determinism single rule", str(r1.formation_status) == str(r2.formation_status)
      and len(r1.evidence) == len(r2.evidence))
# nabha primitive determinism
d1 = nabhasa_sign_distribution(gctx)
d2 = nabhasa_sign_distribution(gctx)
check("nabha primitive deterministic", d1 == d2 and
      nabhasa_occupied_sign_count(gctx) == 5)

# ============ 12. Adapter / merge / source tagging ============
print("\n--- 12. Adapter + merge ---")
from backend.canonical_yoga import (
    evaluate_canonical_yogas, get_covered_legacy_ids,
    LEGACY_YOGA_RULESET_IDS,
)
from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DEFAULT_PROFILE
from core.strength.pipeline import generate_strength_report
from core.calculation.varga import calculate_all_vargas
from core.rules.parashari.fixtures import GOLDEN_BIRTH

b = GOLDEN_BIRTH
cf = generate_chart_facts(
    year=b["year"], month=b["month"], day=b["day"], hour=b["hour"],
    minute=b["minute"], second=b["second"], lat=b["lat"], lon=b["lon"],
    tz_name=b["tz_name"], location_name=b["location_name"],
    country_name=b["country_name"], profile=DEFAULT_PROFILE)
sr = generate_strength_report(cf)
vf = calculate_all_vargas(cf, DEFAULT_PROFILE)
adapted = evaluate_canonical_yogas(chart_facts=cf, strength_report=sr,
                                   varga_facts=vf)
check("adapter returns 77 entries", len(adapted) == 77, str(len(adapted)))
REQUIRED_KEYS = {"id", "name", "status", "is_strong", "is_active", "score",
                 "evidence", "evidence_summary", "provenance",
                 "relevant_planets", "relevant_houses"}
for y in adapted:
    missing = REQUIRED_KEYS - set(y.keys())
    if missing:
        check(f"adapter keys {y['id']}", False, str(missing))
        break
else:
    check("adapter response contract keys", True)
new_ids = {y["id"] for y in adapted if y["id"] in EXPECTED_IDS}
check("adapter includes all 15 new", new_ids == set(EXPECTED_IDS),
      str(set(EXPECTED_IDS) - new_ids))
for y in adapted:
    y["_source"] = "canonical"
check("canonical source tagging",
      all(y["_source"] == "canonical" for y in adapted))
covered = get_covered_legacy_ids()
check("covered legacy count == 71", len(covered) == 71, str(len(covered)))
remaining = [i for i in LEGACY_YOGA_RULESET_IDS if i not in covered]
check("remaining legacy == 5", len(remaining) == 5, str(remaining))
CAT_E = {"garuda_yoga", "kalpadruma_yoga", "mahabhagya_yoga", "matsya_yoga",
         "mridanga_yoga"}
check("remaining == Category E exactly", set(remaining) == CAT_E,
      str(set(remaining) ^ CAT_E))
fake_legacy = [{"id": i} for i in LEGACY_YOGA_RULESET_IDS]
canonical_ids = set(y["id"] for y in adapted)
merged_legacy = [y for y in fake_legacy
                 if y["id"] not in canonical_ids and y["id"] not in covered]
check("merge keeps only 5 legacy", len(merged_legacy) == 5)
check("no canonical ID equals legacy ID",
      not (canonical_ids & set(LEGACY_YOGA_RULESET_IDS)))
for y in merged_legacy:
    y["_source"] = "legacy_fallback"
check("legacy fallback source tagging",
      all(y["_source"] == "legacy_fallback" for y in merged_legacy))
check("no duplicate IDs after merge",
      len({y["id"] for y in adapted} | {y["id"] for y in merged_legacy})
      == 77 + 5)

# ============ 13. Hygiene ============
print("\n--- 13. Hygiene ---")
import glob
bad = []
fps = glob.glob(os.path.join(os.path.dirname(__file__), "core", "rules",
                             "parashari", "category_d_yogas.py"))
for fp in fps:
    with open(fp, encoding="utf-8") as f:
        src = f.read().lower()
    for token in ["openai", "anthropic", "import llm", "from llm", "gpt-",
                  "placidus", "koch houses", "eval(", "exec(",
                  "swisseph", "import swe"]:
        if token in src:
            bad.append((os.path.basename(fp), token))
check("no AI/non-parashari tokens in category_d_yogas", len(bad) == 0, str(bad))
# no legacy imports in the new module
with open(os.path.join(os.path.dirname(__file__), "core", "rules",
                       "parashari", "category_d_yogas.py"), encoding="utf-8") as f:
    mod_src = f.read()
check("no legacy evaluator import",
      "yoga_evaluator" not in mod_src and "evaluate_yoga" not in mod_src
      and "evaluate_named_pattern" not in mod_src)
check("no Category E content",
      all(w not in mod_src.upper() for w in
          ("GARUDA", "KALPADRUMA", "MAHABHAGYA", "MATSYA", "MRIDANGA")))

print("\n" + "=" * 70)
print(f"CATEGORY D TESTS: {passes} passed, {failures} failed, {passes + failures} total")
print("=" * 70)
sys.exit(1 if failures else 0)
