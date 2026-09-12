"""
Production prediction transit-hotfix regression tests (additive, network-free).

Covers required tests prediction 9-15:
 9. Production prediction route reaches evaluate_prediction().
10. Transit signal is created from canonical dynamic state.
11. Exact transit event timestamps are preserved.
12. Windowless transit facts do not become exact timing events.
13. Missing transit remains UNKNOWN/non-fabricated.
14. Existing Dasha activation remains intact.
15. (Phase 8 suite green — verified in Part H run.)

Style follows existing phase scripts: check() + summary + sys.exit.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.routes import prediction as pred_route  # noqa: E402
from backend.core.calculation.pipeline import generate_chart_facts  # noqa: E402
from backend.core.calculation.dynamic import get_dynamic_state  # noqa: E402
from backend.core.prediction.pipeline import evaluate_prediction  # noqa: E402
from backend.core.prediction.models import PredictionRequest  # noqa: E402
from backend.core.prediction.signals import transit_signals  # noqa: E402
from backend.core.prediction.golden import build_golden_entry, golden_request  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

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
print("PRODUCTION PREDICTION TRANSIT HOTFIX — REGRESSION TESTS")
print("=" * 70)

BIRTH = dict(year=2005, month=8, day=17, hour=0, minute=2, second=0,
             lat=16.93407, lon=81.95522, tz="Asia/Kolkata")
EVAL = datetime(2026, 1, 1, tzinfo=timezone.utc)

facts = generate_chart_facts(year=BIRTH["year"], month=BIRTH["month"], day=BIRTH["day"],
                             hour=BIRTH["hour"], minute=BIRTH["minute"], second=BIRTH["second"],
                             lat=BIRTH["lat"], lon=BIRTH["lon"], tz_name=BIRTH["tz"])
state = get_dynamic_state(facts, EVAL, include_events=True, event_window_days=30)
state_d = state.model_dump()

# 9. Production route reaches evaluate_prediction (wrap real engine, assert called)
import backend.core.prediction.pipeline as pipe_mod
seen = {}
real_eval = pipe_mod.evaluate_prediction


def _spy(request, entry):
    seen["called"] = True
    seen["has_transit"] = entry.get("has_transit")
    seen["n_facts"] = len(entry.get("transit_facts", {}))
    return real_eval(request, entry)


pipe_mod.evaluate_prediction = _spy
# pred_route.evaluate imported evaluate_prediction inside function from backend...pipeline,
# so patch that module object too.
import backend.core.prediction.pipeline as pipe_backend  # same module object
try:
    req = pred_route.PredictionEvaluateRequest(
        year=2005, month=8, day=17, hour=0, minute=2, tz="Asia/Kolkata",
        lat=16.93407, lon=81.95522,
        evaluation_datetime="2026-01-01T00:00:00Z",
        start="2026-01-01T00:00:00Z", end="2027-01-01T00:00:00Z")
    out = pred_route.evaluate(req)
    check("9 route reaches evaluate_prediction", seen.get("called") is True)
    check("9 route returns candidates", isinstance(out.get("candidates"), list))
    check("9 route provenance",
          (out.get("provenance") or {}).get("source") == "canonical_transit_engine", f"{out.get('provenance')}")
    check("9 route evaluation datetimes",
          bool(out.get("evaluation_utc_iso")) and bool(out.get("evaluation_datetime")), f"{out}")
    check("9 route transit available", out.get("transit_available") is True)
finally:
    pipe_mod.evaluate_prediction = real_eval
    pipe_backend.evaluate_prediction = real_eval

# 10. Transit signal created from canonical dynamic state
entry = pred_route.build_production_entry(state_d)
check("10 transit_facts from snapshot", len(entry.get("transit_facts", {})) >= 7,
      f"{entry.get('transit_facts')}")
sigs = transit_signals(entry["transit_facts"], entry["transit_events"], entry["has_transit"])
check("10 transit signals ACTIVE",
      len(sigs) > 0 and all(s.source_system == "TRANSIT" and s.status == "ACTIVE" for s in sigs
                            if s.source_id != "transit-unavailable"),
      f"{len(sigs)} signals")

# 11. Exact transit event timestamps preserved verbatim
dyn_events = [e for e in (state_d.get("events") or []) if isinstance(e, dict) and e.get("utc_iso")]
mapped = {(e["planet"], e["kind"], e["timestamp_iso"]) for e in entry["transit_events"]}
expected = {(e.get("transit_planet"), e.get("type"), e.get("utc_iso")) for e in dyn_events}
check("11 timestamps preserved", mapped == expected and len(mapped) > 0,
      f"mapped={len(mapped)} expected={len(expected)}")

# 12. Windowless facts never become exact timing events
state_noev = get_dynamic_state(facts, EVAL, include_events=False).model_dump()
entry_noev = pred_route.build_production_entry(state_noev)
check("12 no events without window", entry_noev["transit_events"] == [],
      f"{entry_noev['transit_events'][:1]}")
check("12 facts still present", len(entry_noev["transit_facts"]) >= 7)
req12 = PredictionRequest(request_id="T12", chart_fingerprint="live-chart",
                          prediction_profile="PREDICTION_DEFAULT_V1",
                          start="2026-01-01T00:00:00Z", end="2027-01-01T00:00:00Z")
res12 = evaluate_prediction(req12, entry_noev)
exact_windows = [w for c in res12.candidates for w in c.windows if w.precision == "EXACT"]
check("12 no EXACT windows from windowless facts", len(exact_windows) == 0,
      f"{len(exact_windows)} exact windows")

# 13. Missing transit => UNKNOWN, never fabricated
miss = transit_signals({}, [], False)
check("13 missing transit UNKNOWN",
      len(miss) == 1 and miss[0].status == "UNKNOWN"
      and miss[0].provenance.get("origin") == "missing-transit-layer", f"{miss}")
entry_miss = dict(entry_noev, has_transit=False, transit_facts={})
res_miss = evaluate_prediction(req12, entry_miss)
check("13 missing transit unknown recorded",
      "transit:transit-unavailable" in (res_miss.unknowns or []), f"{res_miss.unknowns}")

# 14. Dasha activation intact on golden entry
gentry = build_golden_entry()
gres = evaluate_prediction(golden_request(), gentry)
check("14 golden candidates exist", len(gres.candidates) > 0)
check("14 dasha activation present",
      any(c.activation_status == "ACTIVE" for c in gres.candidates),
      f"{sorted({c.activation_status for c in gres.candidates})}")

print("\n" + "=" * 70)
print(f"RESULTS: Total {passes + failures} | Passed {passes} | Failed {failures}")
print("=" * 70)
if failures > 0:
    sys.exit(1)
print("ALL PREDICTION TRANSIT HOTFIX TESTS PASSED")
sys.exit(0)
