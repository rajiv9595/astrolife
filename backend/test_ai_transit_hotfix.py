"""
AI transit hotfix regression tests (additive, network-free).

Covers required tests AI 1-8, 16-18:
 1. AI context contains current transit snapshot.
 2. AI context contains transit-natal relationships.
 3. AI context contains evaluation_datetime.
 4. AI context contains provenance.
 5. Historical evaluation datetime produces different transit state.
 6. Future evaluation datetime is passed unchanged.
 7. AI does not calculate transit independently (no SWE in ai_routes;
     canonical equality with the transit engine).
 8. Missing transit produces explicit unavailable state, never fabricated.
16. Golden chart + known evaluation datetime receives canonical facts.
17. Existing /ai/analyze route works with and without transit (Gemini stubbed).
18. Existing /ai/expert_report route works with and without transit (Gemini stubbed).

Style follows existing phase scripts: check() + summary + sys.exit.
No network: ai_engine calls are stubbed; only local SWE canonical engines run.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone  # noqa: E402

import ai_transit_context as atc  # noqa: E402
from core.transit.calculator import calculate_transit_positions  # noqa: E402

passes = 0
failures = 0


def check(name, cond, msg=""):
    global passes, failures
    if bool(cond):
        passes += 1
    else:
        failures += 1
        print(f"  FAIL {name}: {msg}")


print("=" * 70)
print("AI TRANSIT HOTFIX — REGRESSION TESTS")
print("=" * 70)

BIRTH = dict(year=2005, month=8, day=17, hour=0, minute=2, second=0,
             lat=16.93407, lon=81.95522, tz="Asia/Kolkata")
EVAL_ISO = "2026-01-01T00:00:00Z"

# 1. Snapshot present (9 canonical planets with signs)
section = atc.build_canonical_transit_section(**BIRTH, evaluation_iso=EVAL_ISO)
planets = ((section.get("CURRENT_TRANSITS") or {}).get("planets") or {})
check("1 snapshot has 9 planets", len(planets) == 9, f"{sorted(planets)}")
check("1 snapshot planets have signs",
      all(isinstance(p.get("sign"), str) and p["sign"] for p in planets.values()))

# 2. Transit-natal relationships present
relations = section.get("TRANSIT_NATAL_RELATIONS") or []
check("2 relations non-empty list", isinstance(relations, list) and len(relations) > 0,
      f"type={type(relations)} len={len(relations) if isinstance(relations, list) else '?'}")
if isinstance(relations, list) and relations:
    r0 = relations[0]
    check("2 relation keys", "transit_planet" in r0 and "natal_planet" in r0, f"{sorted(r0)}")

# 3. Evaluation datetime preserved
cur_eval = section.get("CURRENT_EVALUATION") or {}
check("3 evaluation_datetime present", bool(cur_eval.get("evaluation_datetime")),
      f"{cur_eval}")
check("3 evaluation_utc_iso present", bool(cur_eval.get("evaluation_utc_iso")))
check("3 evaluation not birth date", "2005-08-1" not in str(cur_eval.get("evaluation_utc_iso")),
      f"{cur_eval.get('evaluation_utc_iso')}")

# 4. Provenance block
prov = section.get("PROVENANCE") or {}
check("4 provenance source", prov.get("source") == "canonical_transit_engine", f"{prov}")
check("4 provenance system", prov.get("system") == "Swiss Ephemeris", f"{prov}")
check("4 provenance ayanamsha", prov.get("ayanamsha") == "Lahiri", f"{prov}")
check("4 provenance node", prov.get("node_mode") == "Mean Node", f"{prov}")
check("4 provenance datetimes",
      bool(prov.get("evaluation_datetime")) and bool(prov.get("evaluation_utc_iso")), f"{prov}")

# 5. Historical evaluation differs from a far-apart evaluation
hist = atc.build_canonical_transit_section(**BIRTH, evaluation_iso="2020-06-15T00:00:00Z")
hist_eval = (hist.get("CURRENT_EVALUATION") or {}).get("evaluation_utc_iso")
cur_iso = cur_eval.get("evaluation_utc_iso")
check("5 historical iso differs", hist_eval != cur_iso, f"{hist_eval} vs {cur_iso}")
hist_planets = ((hist.get("CURRENT_TRANSITS") or {}).get("planets") or {})
diff = [p for p in planets
        if (planets[p].get("sidereal_longitude"), planets[p].get("sign"))
        != (hist_planets.get(p, {}).get("sidereal_longitude"), hist_planets.get(p, {}).get("sign"))]
check("5 historical positions differ", len(diff) > 0, "identical snapshots 6y apart")

# 6. Future evaluation passed unchanged
fut = atc.build_canonical_transit_section(**BIRTH, evaluation_iso="2030-06-01T00:00:00Z")
fut_eval = (fut.get("CURRENT_EVALUATION") or {}).get("evaluation_datetime") or ""
check("6 future datetime preserved", "2030-06-01" in fut_eval, f"{fut_eval}")

# 7. No independent SWE calculation in AI layer + canonical equality
import pathlib
ai_src = pathlib.Path(os.path.dirname(os.path.abspath(__file__)), "routes", "ai_routes.py").read_text()
bad = [l for l in ai_src.splitlines()
       if ("swe." in l or "calc_ut" in l or "julday" in l)
       and not l.strip().startswith("#")]
check("7 ai_routes has no SWE math", len(bad) == 0, f"{bad}")
ctx_src = pathlib.Path(os.path.dirname(os.path.abspath(__file__)),
                       "ai_transit_context.py").read_text()
bad2 = [l for l in ctx_src.splitlines()
        if ("swe." in l or "calc_ut" in l or "julday" in l)
        and not l.strip().startswith("#")]
check("7 ai_transit_context has no SWE math", len(bad2) == 0, f"{bad2}")
direct = calculate_transit_positions(datetime(2026, 1, 1, tzinfo=timezone.utc))
direct_signs = {k: v.sign for k, v in direct.planets.items()}
ctx_signs = {k: v.get("sign") for k, v in planets.items()}
check("7 canonical equality with transit engine", direct_signs == ctx_signs,
      f"{ctx_signs} vs {direct_signs}")

# 8. Missing transit => explicit unavailable, never fabricated
un = atc.transit_unavailable_section("no-birth-params")
check("8 unavailable status", (un.get("CURRENT_TRANSITS") or {}).get("status") == "unavailable")
check("8 unavailable provenance", (un.get("PROVENANCE") or {}).get("transit_available") is False)
check("8 no fabricated signs",
      not any(isinstance(v, dict) and v.get("sign") for v in (un.get("CURRENT_TRANSITS") or {}).values()
              if isinstance(v, dict)))

# 16. Golden chart + known evaluation datetime
from core.agents.golden import GOLDEN_BIRTH, GOLDEN_DT  # noqa: E402
gsec = atc.build_canonical_transit_section(
    year=GOLDEN_BIRTH["year"], month=GOLDEN_BIRTH["month"], day=GOLDEN_BIRTH["day"],
    hour=GOLDEN_BIRTH["hour"], minute=GOLDEN_BIRTH["minute"], second=GOLDEN_BIRTH["second"],
    lat=GOLDEN_BIRTH["lat"], lon=GOLDEN_BIRTH["lon"], tz=GOLDEN_BIRTH["tz_name"],
    evaluation_iso=GOLDEN_DT.isoformat())
gplanets = ((gsec.get("CURRENT_TRANSITS") or {}).get("planets") or {})
check("16 golden snapshot present", len(gplanets) == 9, f"{sorted(gplanets)}")
gd = calculate_transit_positions(GOLDEN_DT)
check("16 golden canonical equality",
      {k: v.get("sign") for k, v in gplanets.items()} == {k: v.sign for k, v in gd.planets.items()})

# 17/18. Routes keep working with Gemini stubbed (legacy + transit paths)
from backend.routes import ai_routes  # noqa: E402

calls = {}


class _StubAI:
    def generate_analysis(self, system_prompt, user_data):
        calls["analyze"] = (system_prompt, user_data)
        return "STUB-ANALYSIS"

    def generate_expert_report(self, user_data):
        calls["expert"] = user_data
        return '{"ok": true}'


ai_routes.ai_engine = _StubAI()

legacy = ai_routes.AIRequest(query="hello", context_data={"planets": {}, "ascendant": {}})
res_legacy = ai_routes.analyze_astrology(legacy, current_user=None)
check("17 legacy analyze works", res_legacy.get("response") == "STUB-ANALYSIS", f"{res_legacy}")
check("17 legacy unavailable explicit",
      "unavailable" in str(calls["analyze"][1]), "transit status missing")

full = ai_routes.AIRequest(
    query="current career timing?", context_data={"planets": {}, "ascendant": {}},
    year=2005, month=8, day=17, hour=0, minute=2, tz="Asia/Kolkata",
    lat=16.93407, lon=81.95522, evaluation_iso=EVAL_ISO)
res_full = ai_routes.analyze_astrology(full, current_user=None)
check("17 transit analyze works", res_full.get("response") == "STUB-ANALYSIS")
check("17 transit facts reach prompt",
      "CURRENT_TRANSITS" in calls["analyze"][1] and "TRANSIT_NATAL_RELATIONS" in calls["analyze"][1])
check("17 grounding in prompt",
      "Do NOT recalculate" in calls["analyze"][0] or "Do NOT recalculate" in calls["analyze"][1]
      or "canonical" in calls["analyze"][0].lower())

legacy_rep = ai_routes.ExpertReportRequest(context_data={"planets": {}})
res_lr = ai_routes.generate_expert_report(legacy_rep, current_user=None)
check("18 legacy expert_report works", "report" in res_lr, f"{res_lr}")
full_rep = ai_routes.ExpertReportRequest(
    context_data={"planets": {}},
    year=2005, month=8, day=17, tz="Asia/Kolkata",
    lat=16.93407, lon=81.95522, evaluation_iso=EVAL_ISO)
res_fr = ai_routes.generate_expert_report(full_rep, current_user=None)
check("18 transit expert_report works", res_fr.get("report") == {"ok": True}, f"{res_fr}")
check("18 transit facts reach expert prompt", "CURRENT_TRANSITS" in calls["expert"])

print("\n" + "=" * 70)
print(f"RESULTS: Total {passes + failures} | Passed {passes} | Failed {failures}")
print("=" * 70)
if failures > 0:
    sys.exit(1)
print("ALL AI TRANSIT HOTFIX TESTS PASSED")
sys.exit(0)
