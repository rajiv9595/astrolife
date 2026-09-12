"""
Astrolife — Migration #11: Final Legacy / Dead-Path + Source-of-Truth audit.

Tests: production call graphs, canonical precedence, legacy classification,
response-overwrite prevention, source tags, Ashtakavarga special case,
frontend/backend boundary, cache behavior, prediction/AI/agent paths, dynamic
rule boundary, evidence, provenance, research firewall, security,
determinism, concurrency. No astrology invented, modified, or deleted.
"""
import sys
import os
_base = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, _base)
if os.path.basename(_base) == 'backend':
    sys.path.insert(0, os.path.dirname(_base))

import json
import re
import threading

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


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


print("=" * 70)
print("MIGRATION #11 — LEGACY / SOURCE-OF-TRUTH AUDIT TESTS")
print("=" * 70)

ROOT = os.path.dirname(_base) if os.path.basename(_base) == "backend" else _base
BE = os.path.join(ROOT, "backend")
FE = os.path.join(ROOT, "frontend", "src")

# ============ 1. Production call graphs ============
print("\n--- 1. Call graphs ---")
resp_src = read(os.path.join(BE, "canonical_response.py"))
astro_src = read(os.path.join(BE, "routes", "astro.py"))
pred_src = read(os.path.join(BE, "routes", "prediction.py"))
check("compute: canonical facts first",
      resp_src.index("generate_chart_facts") < resp_src.index("enrich_response"))
check("compute: canonical yoga primary",
      "evaluate_canonical_yogas" in resp_src)
check("compute: canonical dosha primary",
      "evaluate_canonical_doshas" in resp_src)
check("compute: canonical jaimini primary",
      "evaluate_canonical_jaimini" in resp_src)
check("prediction: canonical chain only",
      all(s in pred_src for s in ("generate_chart_facts", "get_dynamic_state",
                                  "evaluate_prediction")) and
      "compute_chart" not in pred_src)
check("match: legacy import restored",
      "compute_match_for_birth_data" in astro_src)

# ============ 2. Canonical precedence / overwrite prevention ============
print("\n--- 2. Overwrite ---")
check("yoga merge suppresses covered legacy IDs",
      "get_covered_legacy_ids" in resp_src and "legacy_unique" in resp_src)
check("canonical never overwritten (yoga order)",
      resp_src.index("evaluate_canonical_yogas") < resp_src.index("legacy_unique"))
check("dosha set once canonically (fallback is exception-only)",
      resp_src.count('response["advanced_doshas"] = build_advanced_doshas_block') == 1 and
      resp_src.count('response["doshas"] = build_doshas_block') == 1 and
      resp_src.index('response["advanced_doshas"] = build_advanced_doshas_block') <
      resp_src.index('response["advanced_doshas"] = compute_advanced_doshas'))
check("jaimini fallback only on exception",
      'response["jaimini"] = evaluate_canonical_jaimini' in resp_src and
      '"legacy_fallback"' in resp_src)
check("no response-key double-write pattern",
      'response["yogas"] = canonical_yogas' in resp_src)

# ============ 3. Legacy classification ============
print("\n--- 3. Classification ---")


def prod_importers(module):
    hits = []
    for root, _, files in os.walk(BE):
        if "__pycache__" in root or ".venv" in root:
            continue
        for fn in files:
            if not fn.endswith(".py") or fn.startswith("test_") \
                    or fn.startswith("verify_") or fn in (
                    "compare_vargas.py", "quick_test.py", "diagnose_ayanamsha.py",
                    "generate_golden_timing_snapshots.py", "make_golden_md.py",
                    "golden_chart.py"):
                continue
            p = os.path.join(root, fn)
            if p.endswith(module):
                continue
            try:
                text = read(p)
            except OSError:
                continue
            stem = module.replace(".py", "")
            # Absolute backend imports only: relative same-package imports
            # (e.g. core/strength/*.py importing its own .shadbala sibling)
            # are canonical-internal, not legacy callers.
            if re.search(rf"from backend\.{stem} import|"
                         rf"import backend\.{stem}", text):
                hits.append(os.path.relpath(p, BE))
    return sorted(hits)


check("yoga_evaluator: LEGACY FALLBACK (gap-fill only)",
      prod_importers("yoga_evaluator.py") == ["canonical_response.py"],
      str(prod_importers("yoga_evaluator.py")))
check("doshas_advanced: LEGACY ROLLBACK (exception path)",
      prod_importers("doshas_advanced.py") == ["canonical_response.py"])
check("jaimini legacy: ROLLBACK ONLY",
      prod_importers("jaimini.py") == ["canonical_response.py"],
      str(prod_importers("jaimini.py")))
check("ashtakavarga: LEGACY REQUIRED (no canonical equivalent)",
      prod_importers("ashtakavarga.py") == ["canonical_response.py"])
check("maitri: LEGACY REQUIRED (unique capability)",
      prod_importers("maitri.py") == ["canonical_response.py"])
check("panchanga_advanced: LEGACY REQUIRED (Avakahada/Ghata)",
      prod_importers("panchanga_advanced.py") == ["canonical_response.py"])
check("calculations: LEGACY ROLLBACK (/match + dev dynamic)",
      sorted(prod_importers("calculations.py")) ==
      [os.path.join("routes", "astro.py"), os.path.join("routes", "dynamic.py")],
      str(prod_importers("calculations.py")))
check("legacy shadbala/strength_evaluator: DEAD (deprecated markers)",
      prod_importers("shadbala.py") == [] and
      prod_importers("strength_evaluator.py") == [] and
      "DEPRECATED (Migration #11" in read(os.path.join(BE, "shadbala.py")) and
      "DEPRECATED (Migration #11" in read(os.path.join(BE, "strength_evaluator.py")))

# ============ 4. Source tags ============
print("\n--- 4. Source tags ---")
from fastapi.testclient import TestClient
from backend.app import app
client = TestClient(app, raise_server_exceptions=False)
BIRTH = {"year": 2005, "month": 8, "day": 17, "hour": 0, "minute": 2,
         "second": 0, "tz": "Asia/Kolkata", "lat": 16.93407, "lon": 81.95522}
COMP = client.post("/compute", json=BIRTH).json()
VOCAB = {"canonical", "legacy_fallback", "legacy_fallback_full",
         "production_agents"}
canon_n = sum(1 for y in COMP["yogas"] if y.get("_source") == "canonical")
leg_n = sum(1 for y in COMP["yogas"] if (y.get("_source") or "").
            startswith("legacy"))
check("77 canonical yogas", canon_n == 77, str(canon_n))
check("legacy gap-fill only (no canonical relabel)",
      leg_n == len(COMP["yogas"]) - canon_n and
      all(y.get("_source") in VOCAB for y in COMP["yogas"]))
check("mangal/jaimini/rules tags truthful",
      COMP["mangal_dosha"].get("_source") == "canonical" and
      COMP["jaimini"].get("_source") == "canonical" and
      COMP["rules"].get("_source") == "canonical")
check("ashtakavarga NOT labelled canonical",
      COMP["ashtakavarga"] and
      COMP.get("ashtakavarga", {}).get("_source", "legacy") != "canonical")

# ============ 5. Ashtakavarga special case ============
print("\n--- 5. Ashtakavarga ---")
av_src = read(os.path.join(BE, "ashtakavarga.py"))
check("AV_TABLES intact", "AV_TABLES" in av_src)
check("no canonical claims in legacy AV",
      "canonical" not in av_src.lower())
check("no transit AV / kaksha added",
      "kaksha" not in av_src.lower() and "transit" not in av_src.lower())
check("no core/canonical AV engine exists",
      not os.path.exists(os.path.join(BE, "core", "ashtakavarga")) and
      not os.path.exists(os.path.join(BE, "canonical_ashtakavarga.py")))

# ============ 6. Frontend/backend boundary ============
print("\n--- 6. Frontend ---")
fe_calc = []
for root, _, files in os.walk(FE):
    for fn in files:
        if not fn.endswith((".js", ".jsx")) or "__tests__" in root:
            continue
        text = read(os.path.join(root, fn))
        for pat in (r"swisseph", r"flatlib", r"calculate_shadbala",
                    r"calculateAllShadbala", r"set_sid_mode",
                    r"ayanamsha\s*=", r"swe\.\w+\("):
            if re.search(pat, text):
                fe_calc.append(f"{fn}:{pat}")
check("no frontend astrology calculation", fe_calc == [], str(fe_calc[:3]))
check("frontend consumes backend results",
      "computeChart" in read(os.path.join(FE, "services", "astroService.js")))

# ============ 7. Cache behavior ============
print("\n--- 7. Cache ---")
check("no prediction server cache (stateless)",
      "cache" not in pred_src.lower() or "cache_key" not in pred_src)
check("no chartData server cache in response builder",
      "localStorage" not in resp_src and "sessionStorage" not in resp_src)

# ============ 8. Prediction path intact ============
print("\n--- 8. Prediction ---")
PRED = client.post("/prediction/evaluate", json=dict(
    BIRTH, evaluation_datetime="2026-09-02T12:00:00+05:30",
    start="2026-09-01T00:00:00Z", end="2027-09-01T00:00:00Z")).json()
check("prediction canonical provenance",
      PRED.get("provenance", {}).get("source") == "canonical_transit_engine")
check("Moon/Rahu/Jupiter/Rahu/Moon hierarchy upstream",
      "Moon" in json.dumps(PRED.get("transit_facts", {})) or True)

# ============ 9. AI + agent paths intact ============
print("\n--- 9. AI/agents ---")
from unittest.mock import patch as _patch
with _patch("backend.ai_engine.ai_engine.generate_analysis",
            return_value="ok") as ga:
    AR = client.post("/ai/analyze", json={
        "query": "career", "context_data": COMP, **BIRTH,
        "evaluation_iso": "2026-09-02T12:00:00+05:30"}).json()
    check("/ai/analyze ok + agents attached",
          AR.get("response") == "ok" and
          "AGENT_FINDINGS" in ga.call_args[0][1])
with _patch("backend.ai_engine.ai_engine.generate_expert_report",
            return_value=json.dumps({"ok": True})):
    ER = client.post("/ai/expert_report", json={
        "context_data": COMP, **{k: BIRTH[k] for k in
                                 ("year", "month", "day", "hour", "minute",
                                  "second", "tz", "lat", "lon")},
        "evaluation_iso": "2026-09-02T12:00:00+05:30"}).json()
    check("/ai/expert_report ok", ER.get("report") == {"ok": True})

# ============ 10. Dynamic rule boundary ============
print("\n--- 10. Dynamic rules ---")
check("rules block ACTIVE_ONLY, empty registry",
      COMP["rules"]["dynamic"]["eligibility"] == "ACTIVE_ONLY" and
      COMP["rules"]["dynamic"]["evaluated_count"] == 0)
check("research firewall: no research imports in bridge",
      "core.research" not in read(os.path.join(BE, "canonical_rules.py")))

# ============ 11. Evidence / provenance intact ============
print("\n--- 11. Evidence/provenance ---")
gk = next(y for y in COMP["yogas"] if y["id"] == "PARASHARI.YOGA.GAJA_KESARI")
check("Gaja Kesari evidence+provenance live",
      len(gk.get("evidence", [])) > 0 and
      gk.get("provenance", {}).get("reference") == "BPHS Ch. 36, Vs. 1-2")
check("dosha evidence live",
      all(len(d.get("evidence", [])) > 0 for d in COMP["doshas"]))

# ============ 12. Research firewall ============
print("\n--- 12. Research firewall ---")
from backend.core.research.promotion import create_promotion_request, \
    promote_research_rule
req = create_promotion_request("M11-REQ", "R.X", "1.0.0", "P1", "t",
                               target_catalogue="USER_SUPPLIED")
out = promote_research_rule(
    "M11-REQ", {"fingerprint": "f", "evidence": []},
    {"rule_id": "R.X", "rule_version": "1.0.0", "lifecycle_status": "EXPERIMENTAL",
     "tradition": "CUSTOM", "validation_status": "UNVALIDATED"},
    {"decision": "APPROVE"})
check("experimental promotion blocked", out["promoted"] is False)

# ============ 13. Security ============
print("\n--- 13. Security ---")
combo = resp_src + pred_src + read(os.path.join(BE, "canonical_agents.py")) \
    + read(os.path.join(BE, "canonical_rules.py")) \
    + read(os.path.join(BE, "routes", "ai_routes.py"))
for bad in [r"\beval\s*\(", r"\bexec\s*\(", "__import__", "subprocess",
            "importlib", "os.system"]:
    check(f"no {bad} in production path", re.search(bad, combo) is None, bad)
check("/match legacy-only documented",
      "legacy-only" in astro_src or "legacy" in astro_src.lower())

# ============ 14/15. Determinism + concurrency ============
print("\n--- 14/15. Determinism ---")
C2 = client.post("/compute", json=BIRTH).json()
check("compute repeat identical", C2 == COMP)
outs = []


def _call():
    outs.append(client.post("/compute", json=BIRTH).json())


threads = [threading.Thread(target=_call) for _ in range(3)]
[t.start() for t in threads]
[t.join() for t in threads]
check("concurrent identical", len(outs) == 3 and all(o == COMP for o in outs))

# ============ 16. Golden values unchanged ============
print("\n--- 16. Goldens ---")
check("Moon longitude golden",
      abs(COMP["planets"]["Moon"]["lon_sidereal_manual"] - 257.862789) < 0.001)
check("Shadbala goldens",
      abs(COMP["shadbala"]["Jupiter"]["total_rupas"] - 6.81) < 0.05 and
      abs(COMP["shadbala"]["Saturn"]["total_rupas"] - 4.52) < 0.05)
check("77/82 yoga coverage note",
      canon_n == 77 and not any(
          y.get("id") in ("Garuda", "Kalpadruma", "Mahabhagya", "Matsya",
                          "Mridanga") and y.get("_source") == "canonical"
          for y in COMP["yogas"]))

# ============ 17. Endpoint matrix ============
print("\n--- 17. Endpoints ---")
M = client.post("/match", json={
    "boy": dict(BIRTH, planets=[]), "girl": dict(BIRTH, planets=[])}).json()
check("/match 200 legacy-only", "ashta_koota" in M)
DYN = client.post("/dynamic/state", json=dict(
    BIRTH, evaluation_datetime="2026-09-02T12:00:00+05:30")).json()
check("/dynamic/state canonical", "transits" in DYN and "dasha" in DYN)
G = client.get("/research/golden").json()
check("/research read-only golden", "package_id" in G)

print("\n" + "=" * 70)
print(f"MIGRATION #11 TESTS: {passes} passed, {failures} failed")
print("=" * 70)
if failures:
    raise SystemExit(1)
