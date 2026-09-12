"""
Astrolife — Migration #3B Implementation: Category C Yoga tests.

Focused coverage for the 31 canonical Category C rules:
registration, metadata, positive/negative formation, boundary cases,
Evidence, Provenance, determinism, source tagging, merge precedence,
no duplicate IDs, no legacy override of canonical results.
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
from core.rules.parashari.classical_yogas import (
    CLASSICAL_YOGA_RULE_IDS, FORMATION_EVALUATORS,
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
print("MIGRATION #3B — CATEGORY C YOGA TESTS (31 rules)")
print("=" * 70)

# ============ 0. Registration ============
print("\n--- 0. Registration ---")
check("31 Category C rule IDs", len(CLASSICAL_YOGA_RULE_IDS) == 31,
      str(len(CLASSICAL_YOGA_RULE_IDS)))
check("catalog has 77 rules (62 + 15 Category D, Migration #3C)", len(build_parashari_catalog()) == 77,
      str(len(build_parashari_catalog())))
check("PARASHARI_RULE_IDS has 77", len(PARASHARI_RULE_IDS) == 77)
check("rule IDs unique (77)", len(set(PARASHARI_RULE_IDS)) == 77)
check("31 formation evaluators registered",
      all(f"parashari_{rid.split('.')[-1].lower()}_formation" in FORMATION_EVALUATORS
          for rid in CLASSICAL_YOGA_RULE_IDS))
check("no canonical ID collides with legacy slug",
      not any("." not in rid for rid in PARASHARI_RULE_IDS))

EXPECTED_IDS = [
    "PARASHARI.YOGA.AKHANDA_SAMRAJYA", "PARASHARI.YOGA.BHAGYA",
    "PARASHARI.YOGA.CHAMARA", "PARASHARI.YOGA.CHHATRA",
    "PARASHARI.YOGA.DHENU", "PARASHARI.YOGA.GANDHARVA",
    "PARASHARI.YOGA.GO", "PARASHARI.YOGA.HARA",
    "PARASHARI.YOGA.HARI", "PARASHARI.YOGA.JALADHI",
    "PARASHARI.YOGA.KAHALA", "PARASHARI.YOGA.KALANIDHI",
    "PARASHARI.YOGA.KAMA", "PARASHARI.YOGA.KHYATHI",
    "PARASHARI.YOGA.KUSUMA", "PARASHARI.YOGA.MALA",
    "PARASHARI.YOGA.MUSALA", "PARASHARI.YOGA.PARIJATA",
    "PARASHARI.YOGA.PARVATA", "PARASHARI.YOGA.PUSHKALA",
    "PARASHARI.YOGA.RAJA_LAKSHANA", "PARASHARI.YOGA.RAVI",
    "PARASHARI.YOGA.SHAKATA", "PARASHARI.YOGA.SHAURYA",
    "PARASHARI.YOGA.SHIVA", "PARASHARI.YOGA.SRINATHA",
    "PARASHARI.YOGA.SUPARIJATA", "PARASHARI.YOGA.UBHAYACHARI",
    "PARASHARI.YOGA.VASI", "PARASHARI.YOGA.VESI",
    "PARASHARI.YOGA.VISHNU",
]
check("exact 31 rule IDs", CLASSICAL_YOGA_RULE_IDS == EXPECTED_IDS,
      str(set(CLASSICAL_YOGA_RULE_IDS) ^ set(EXPECTED_IDS)))

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
    check(f"{m.rule_id} source_reference present", bool(m.provenance.source_reference))
    check(f"{m.rule_id} method recorded", bool(m.provenance.method),
          str(m.provenance.method))
    check(f"{m.rule_id} enabled", m.enabled and str(m.status).endswith("ENABLED"))


def ev_pos(rid, asc, placements, **kw):
    ctx = make_synthetic_context(asc, placements, **kw)
    return evaluate_parashari_by_id(rid, ctx, EVAL), ctx


# ============ 2. Positive + negative formation ============
print("\n--- 2. Formation ---")
CASES = [
    # (rule_id, asc, positive placements, negative placements or None, note)
    ("PARASHARI.YOGA.AKHANDA_SAMRAJYA", "Scorpio",
     {"Moon": "Cancer", "Jupiter": "Pisces"},
     None, "Jupiter rules 2/5; L9 Moon kendra-from-self"),
    ("PARASHARI.YOGA.BHAGYA", "Aries",
     {"Jupiter": "Cancer", "Venus": "Sagittarius"},
     {"Jupiter": "Gemini", "Venus": "Capricorn"},
     "L9 strong + benefic in 9th / 9th empty"),
    ("PARASHARI.YOGA.CHAMARA", "Aries",
     {"Mars": "Capricorn"},
     {"Mars": "Leo"},
     "L1 exalted kendra aspecting lagna"),
    ("PARASHARI.YOGA.CHHATRA", "Aries",
     {"Sun": "Aries"},
     {"Sun": "Virgo"},
     "L5 exalted / L5 weak cadent"),
    ("PARASHARI.YOGA.DHENU", "Sagittarius",
     {"Saturn": "Libra"},
     {"Saturn": "Aries"},
     "L2 exalted / debilitated"),
    ("PARASHARI.YOGA.GANDHARVA", "Aries",
     {"Saturn": "Aquarius", "Sun": "Leo", "Moon": "Sagittarius"},
     {"Saturn": "Aquarius", "Sun": "Leo", "Moon": "Capricorn"},
     "L10 kama + Sun dignified + Moon 9th"),
    ("PARASHARI.YOGA.GO", "Gemini",
     {"Jupiter": ("Sagittarius", 5.0), "Mercury": "Sagittarius"},
     {"Jupiter": ("Sagittarius", 5.0), "Mercury": "Virgo"},
     "Jupiter MT with L1 / apart"),
    ("PARASHARI.YOGA.HARA", "Aries",
     {"Venus": "Taurus", "Jupiter": "Leo", "Mercury": "Capricorn",
      "Moon": "Sagittarius"},
     {"Venus": "Taurus", "Jupiter": "Leo", "Mercury": "Capricorn",
      "Moon": "Scorpio"},
     "benefics 4/8/9 from L7"),
    ("PARASHARI.YOGA.HARI", "Gemini",
     {"Moon": "Cancer", "Venus": "Leo", "Mercury": "Aquarius",
      "Jupiter": "Gemini"},
     {"Moon": "Cancer", "Venus": "Leo", "Mercury": "Aquarius",
      "Jupiter": "Taurus"},
     "benefics 2/8/12 from L2"),
    ("PARASHARI.YOGA.JALADHI", "Aries",
     {"Moon": "Taurus", "Mercury": "Cancer"},
     {"Moon": "Taurus", "Mercury": "Gemini"},
     "L4 strong + benefic in 4th"),
    ("PARASHARI.YOGA.KAHALA", "Aries",
     {"Moon": "Aries", "Jupiter": "Libra"},
     {"Moon": "Virgo", "Jupiter": "Scorpio"},
     "L4/L9 kendra / cadent"),
    ("PARASHARI.YOGA.KALANIDHI", "Virgo",
     {"Jupiter": "Capricorn", "Venus": "Capricorn"},
     {"Jupiter": "Capricorn", "Venus": "Aquarius"},
     "Jupiter 5th with Venus"),
    ("PARASHARI.YOGA.KAMA", "Taurus",
     {"Mars": "Aries"},
     {"Mars": "Cancer"},
     "L7 own / L7 debilitated cadent"),
    ("PARASHARI.YOGA.KHYATHI", "Leo",
     {"Venus": "Pisces"},
     {"Sun": "Leo", "Moon": "Cancer", "Mars": "Aries", "Mercury": "Gemini",
      "Jupiter": "Sagittarius", "Venus": "Gemini", "Saturn": "Capricorn"},
     "L10 exalted / L10 weak cadent"),
    ("PARASHARI.YOGA.KUSUMA", "Aries",
     {"Venus": "Capricorn", "Moon": "Leo", "Saturn": "Capricorn"},
     {"Venus": "Capricorn", "Moon": "Leo", "Saturn": "Aquarius"},
     "Venus kendra Moon trikona Saturn 10th"),
    ("PARASHARI.YOGA.MALA", "Aries",
     {"Jupiter": "Aries", "Venus": "Cancer", "Mercury": "Libra"},
     {"Jupiter": "Aries", "Venus": "Cancer", "Mercury": "Scorpio"},
     "benefics in 3 kendras / 2 kendras"),
    ("PARASHARI.YOGA.MUSALA", "Taurus",
     {"Venus": "Aries", "Saturn": "Aries"},
     {"Venus": "Aries", "Saturn": "Taurus"},
     "L1 12th + malefic / no malefic"),
    ("PARASHARI.YOGA.PARIJATA", "Leo",
     {"Sun": "Virgo", "Mercury": "Virgo"},
     {"Sun": "Virgo", "Mercury": "Leo"},
     "dispositor exalted or not"),
    ("PARASHARI.YOGA.PARVATA", "Aries",
     {"Sun": "Leo", "Moon": "Taurus", "Mars": "Capricorn",
      "Mercury": "Gemini", "Jupiter": "Aries", "Venus": "Libra",
      "Saturn": "Aquarius", "Rahu": "Sagittarius", "Ketu": "Gemini"},
     {"Sun": "Leo", "Moon": "Taurus", "Mars": "Capricorn",
      "Mercury": "Gemini", "Jupiter": "Aries", "Venus": "Libra",
      "Saturn": "Virgo", "Rahu": "Sagittarius", "Ketu": "Gemini"},
     "benefic kendra + 6/8 empty"),
    ("PARASHARI.YOGA.PUSHKALA", "Capricorn",
     {"Moon": "Taurus", "Venus": "Libra", "Saturn": "Libra"},
     {"Moon": "Taurus", "Venus": "Libra", "Saturn": "Scorpio"},
     "Moon-lord with L1 in kendra"),
    ("PARASHARI.YOGA.RAJA_LAKSHANA", "Aries",
     {"Jupiter": "Aries", "Venus": "Cancer", "Mercury": "Libra",
      "Moon": "Capricorn"},
     {"Jupiter": "Aries", "Venus": "Cancer", "Mercury": "Libra",
      "Moon": "Leo"},
     "four benefics kendra"),
    ("PARASHARI.YOGA.RAVI", "Taurus",
     {"Sun": "Aquarius", "Saturn": "Cancer"},
     {"Sun": "Aquarius", "Saturn": "Leo"},
     "Sun 10th + L10 3rd"),
    ("PARASHARI.YOGA.SHAKATA", "Aries",
     {"Jupiter": "Aries", "Moon": "Virgo"},
     {"Jupiter": "Aries", "Moon": "Taurus"},
     "Moon 6th from Jupiter / 2nd"),
    ("PARASHARI.YOGA.SHAURYA", "Aries",
     {"Mercury": "Virgo"},
     {"Mercury": "Pisces"},
     "L3 exalted / debilitated dusthana"),
    ("PARASHARI.YOGA.SHIVA", "Leo",
     {"Jupiter": "Aries", "Mars": "Taurus", "Venus": "Sagittarius"},
     {"Jupiter": "Aries", "Mars": "Taurus", "Venus": "Capricorn"},
     "5-9-10 chain"),
    ("PARASHARI.YOGA.SRINATHA", "Sagittarius",
     {"Mercury": "Virgo", "Sun": "Virgo"},
     {"Mercury": "Virgo", "Sun": "Libra"},
     "L7 exalted 10th + L10 with L9"),
    ("PARASHARI.YOGA.SUPARIJATA", "Aries",
     {"Saturn": "Libra"},
     {"Saturn": "Pisces"},
     "L11 exalted / weak dusthana"),
    ("PARASHARI.YOGA.UBHAYACHARI", "Aries",
     {"Sun": "Taurus", "Mercury": "Gemini", "Mars": "Aries"},
     {"Sun": "Taurus", "Mercury": "Gemini", "Mars": "Taurus"},
     "planets both sides of Sun"),
    ("PARASHARI.YOGA.VASI", "Aries",
     {"Sun": "Taurus", "Mars": "Aries"},
     {"Sun": "Taurus", "Mars": "Taurus"},
     "planet 12th from Sun"),
    ("PARASHARI.YOGA.VESI", "Aries",
     {"Sun": "Taurus", "Mercury": "Gemini"},
     {"Sun": "Taurus", "Mercury": "Taurus"},
     "planet 2nd from Sun"),
    ("PARASHARI.YOGA.VISHNU", "Aries",
     {"Jupiter": "Taurus", "Saturn": "Taurus"},
     {"Jupiter": "Taurus", "Saturn": "Gemini"},
     "L9 + L10 in 2nd"),
]

for rid, asc, pos_pl, neg_pl, note in CASES:
    res, _ = ev_pos(rid, asc, pos_pl)
    check(f"positive {rid.split('.')[-1]} FORMED", is_formed(res), note)
    check(f"positive {rid.split('.')[-1]} evidence>=1", len(res.evidence) >= 1)
    if neg_pl is not None:
        nres, _ = ev_pos(rid, asc, neg_pl)
        check(f"negative {rid.split('.')[-1]} NOT_FORMED", not is_formed(nres), note)

# Akhanda negative: Jupiter rules none of 2/5/11
ares, _ = ev_pos("PARASHARI.YOGA.AKHANDA_SAMRAJYA", "Aries",
                 {"Moon": "Taurus", "Jupiter": "Sagittarius"})
check("negative AKHANDA_SAMRAJYA NOT_FORMED", not is_formed(ares),
      "Jupiter rules none of 2/5/11 for Aries")

# ============ 3. Boundary / edge cases ============
print("\n--- 3. Boundary ---")
# Shakata 8th and 12th variants form; 7th does not
r8, _ = ev_pos("PARASHARI.YOGA.SHAKATA", "Aries",
               {"Jupiter": "Aries", "Moon": "Scorpio"})
check("boundary SHAKATA 8th FORMED", is_formed(r8))
r12, _ = ev_pos("PARASHARI.YOGA.SHAKATA", "Aries",
                {"Jupiter": "Aries", "Moon": "Pisces"})
check("boundary SHAKATA 12th FORMED", is_formed(r12))
r7, _ = ev_pos("PARASHARI.YOGA.SHAKATA", "Aries",
               {"Jupiter": "Aries", "Moon": "Libra"})
check("boundary SHAKATA 7th NOT_FORMED", not is_formed(r7))
# Ubhayachari Moon-only exclusion: Moon alone on both sides must NOT form
ru, _ = ev_pos("PARASHARI.YOGA.UBHAYACHARI", "Aries",
               {"Sun": "Taurus", "Moon": "Aries", "Mercury": "Taurus",
                "Mars": "Taurus", "Jupiter": "Taurus", "Venus": "Taurus",
                "Saturn": "Taurus"})
# 2nd from Sun (Gemini) empty here -> NOT_FORMED regardless; explicit Moon-only check:
ru2, _ = ev_pos("PARASHARI.YOGA.VESI", "Aries",
                {"Sun": "Taurus", "Moon": "Gemini", "Mercury": "Taurus",
                 "Mars": "Taurus", "Jupiter": "Taurus", "Venus": "Taurus",
                 "Saturn": "Taurus"})
check("edge VESI Moon-only NOT_FORMED", not is_formed(ru2),
      "Moon excluded from Sun yogas")
ru3, _ = ev_pos("PARASHARI.YOGA.VASI", "Aries",
                {"Sun": "Taurus", "Moon": "Aries", "Mercury": "Taurus",
                 "Mars": "Taurus", "Jupiter": "Taurus", "Venus": "Taurus",
                 "Saturn": "Taurus"})
check("edge VASI Moon-only NOT_FORMED", not is_formed(ru3),
      "Moon excluded from Sun yogas")
# Mala exactly-2 boundary already covered as negative; Kalanidhi Mercury variant
rk, _ = ev_pos("PARASHARI.YOGA.KALANIDHI", "Virgo",
               {"Jupiter": "Capricorn", "Mercury": "Capricorn"})
check("edge KALANIDHI Mercury variant FORMED", is_formed(rk))
# Kusuma trikona includes Lagna (house 1)
rk2, _ = ev_pos("PARASHARI.YOGA.KUSUMA", "Aries",
                {"Venus": "Aries", "Moon": "Aries", "Saturn": "Capricorn"})
check("edge KUSUMA Moon in Lagna-trikona FORMED", is_formed(rk2))

# ============ 4. Evidence quality ============
print("\n--- 4. Evidence ---")
from core.rules.enums import EvidenceType as ET
gctx = make_golden_context()
gres = evaluate_all_parashari(gctx)
for r in gres:
    if r.rule_id not in EXPECTED_IDS:
        continue
    check(f"evidence {r.rule_id.split('.')[-1]}>=1", len(r.evidence) >= 1)
    types = {getattr(e.evidence_type, "value", str(e.evidence_type)) for e in r.evidence}
    check(f"evidence {r.rule_id.split('.')[-1]} typed", len(types) >= 1)
    check(f"evidence {r.rule_id.split('.')[-1]} sourced",
          all(bool(getattr(e, "source", "")) for e in r.evidence))
    check(f"activation {r.rule_id.split('.')[-1]} NOT_EVALUATED",
          str(r.activation_status).endswith("NOT_EVALUATED"))

# ============ 5. Provenance ============
print("\n--- 5. Provenance ---")
for rid in EXPECTED_IDS:
    rec = ProvenanceRegistry.get(rid)
    check(f"provenance registered {rid.split('.')[-1]}", rec is not None)
    if rec is not None:
        check(f"provenance source {rid.split('.')[-1]}", bool(rec.source_name))
check("legacy fallback has no canonical provenance",
      ProvenanceRegistry.get("akhanda_samrajya_yoga") is None)
check("legacy fallback (garuda) no provenance",
      ProvenanceRegistry.get("garuda_yoga") is None)

# ============ 6. Golden chart expectations ============
print("\n--- 6. Golden ---")
GOLDEN_FORMED_NEW = {
    "PARASHARI.YOGA.AKHANDA_SAMRAJYA", "PARASHARI.YOGA.CHHATRA",
    "PARASHARI.YOGA.KALANIDHI", "PARASHARI.YOGA.KAMA",
    "PARASHARI.YOGA.SUPARIJATA", "PARASHARI.YOGA.UBHAYACHARI",
    "PARASHARI.YOGA.VASI", "PARASHARI.YOGA.VESI",
}
by_id = {r.rule_id: r for r in gres}
for rid in EXPECTED_IDS:
    exp = rid in GOLDEN_FORMED_NEW
    check(f"golden {rid.split('.')[-1]} {'FORMED' if exp else 'NOT_FORMED'}",
          is_formed(by_id[rid]) == exp)
check("golden total FORMED == 17",
      sum(1 for r in gres if is_formed(r)) == 17,
      str(sum(1 for r in gres if is_formed(r))))

# ============ 7. Determinism ============
print("\n--- 7. Determinism ---")
gres2 = evaluate_all_parashari(gctx)
same = all(a.formation_status == b.formation_status and
           a.strength_status == b.strength_status and
           a.cancellation_status == b.cancellation_status and
           len(a.evidence) == len(b.evidence)
           for a, b in zip(gres, gres2))
check("determinism identical rerun (62)", same)
# repeated single-rule evaluation
r1 = evaluate_parashari_by_id("PARASHARI.YOGA.SHIVA", gctx, EVAL)
r2 = evaluate_parashari_by_id("PARASHARI.YOGA.SHIVA", gctx, EVAL)
check("determinism single rule", str(r1.formation_status) == str(r2.formation_status)
      and len(r1.evidence) == len(r2.evidence))

# ============ 8. Adapter / source tagging / merge ============
print("\n--- 8. Adapter + merge ---")
from backend.canonical_yoga import (
    evaluate_canonical_yogas, get_covered_legacy_ids, CANONICAL_COVERS_LEGACY,
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
check("adapter includes all 31 new", new_ids == set(EXPECTED_IDS),
      str(set(EXPECTED_IDS) - new_ids))
# source tagging simulation (as canonical_response merge does)
for y in adapted:
    y["_source"] = "canonical"
check("canonical source tagging",
      all(y["_source"] == "canonical" for y in adapted))
# merge precedence: covered legacy suppressed, D/E retained
covered = get_covered_legacy_ids()
check("covered legacy count == 71", len(covered) == 71, str(len(covered)))
remaining = [i for i in LEGACY_YOGA_RULESET_IDS if i not in covered]
check("remaining legacy == 5", len(remaining) == 5, str(remaining))
CAT_D = {"astra_yoga", "asura_yoga", "bheri_yoga", "bhrigu_mangala_yoga",
         "brahma_yoga", "dama_yoga", "gola_yoga", "indra_yoga", "kedara_yoga",
         "kurma_yoga", "pasha_yoga", "sarpa_yoga", "shula_yoga", "veena_yoga",
         "yuga_yoga"}
CAT_E = {"garuda_yoga", "kalpadruma_yoga", "mahabhagya_yoga", "matsya_yoga",
         "mridanga_yoga"}
check("remaining == E (D now canonical)", set(remaining) == CAT_E,
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

# ============ 9. No-AI / no-Western tokens in new module ============
print("\n--- 9. Hygiene ---")
import glob
bad = []
fps = glob.glob(os.path.join(os.path.dirname(__file__), "core", "rules",
                             "parashari", "classical_yogas.py"))
for fp in fps:
    with open(fp, encoding="utf-8") as f:
        src = f.read().lower()
    for token in ["openai", "anthropic", "import llm", "from llm", "gpt-",
                  "placidus", "koch houses", "eval(", "exec(",
                  "swisseph", "import swe"]:
        if token in src:
            bad.append((os.path.basename(fp), token))
check("no AI/non-parashari tokens in classical_yogas", len(bad) == 0, str(bad))

print("\n" + "=" * 70)
print(f"CATEGORY C TESTS: {passes} passed, {failures} failed, {passes + failures} total")
print("=" * 70)
sys.exit(1 if failures else 0)
