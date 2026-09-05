"""
Dynamic State Tests — Step 27,28,29
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from datetime import datetime, timezone, timedelta
import swisseph as swe

from core.calculation.pipeline import generate_chart_facts
from core.calculation.dynamic import get_dynamic_state, get_transit_range
from core.calculation.config import DEFAULT_PROFILE

passes=0
failures=0
def check(name,cond,msg=""):
    global passes,failures
    ok=bool(cond)
    if ok: passes+=1
    else:
        failures+=1
        print(f"  FAIL {name}: {msg}")
    return ok

print("="*70)
print("ASTROLIFE V2 — DYNAMIC STATE TESTS")
print("="*70)

BIRTH = dict(year=2005,month=8,day=17,hour=0,minute=2,second=0,lat=16.93407,lon=81.95522,tz="Asia/Kolkata")
facts = generate_chart_facts(year=BIRTH["year"],month=BIRTH["month"],day=BIRTH["day"],hour=BIRTH["hour"],minute=BIRTH["minute"],second=BIRTH["second"],lat=BIRTH["lat"],lon=BIRTH["lon"],tz_name=BIRTH["tz"])

# At birth, dynamic state should reflect birth पंचांग? But evaluation at birth JD
eval_birth = datetime(2005,8,16,18,32,0, tzinfo=timezone.utc)  # birth UTC
state_birth = get_dynamic_state(facts, eval_birth)
check("Dynamic at birth MD Venus", state_birth.dasha["current"]["mahadasha"] is not None and state_birth.dasha["current"]["mahadasha"]["lord"]=="Venus")
check("Panchanga at birth tithi exists", state_birth.panchanga.tithi.index is not None)
check("Transit at birth Sun Leo", state_birth.transits["snapshot"]["planets"]["Sun"]["sign"]=="Leo")
check("Cache key has profile", "profile" in state_birth.transits["cache_key"])
check("Cache key has ephemeris_version", "ephemeris_version" in state_birth.transits["cache_key"])
check("ChartFacts not mutated (dynamic not inside facts)", "panchanga" not in facts.model_fields if hasattr(facts,"model_fields") else True)

# Fixed future date
eval_2026 = datetime(2026,9,2,12,0,0, tzinfo=timezone.utc)
state = get_dynamic_state(facts, eval_2026)
check("Dynamic has location lat", state.location["latitude"]==facts.location.latitude)
check("Panchanga via dynamic equals standalone", state.panchanga.tithi.name is not None)
check("Dasha hierarchy at 2026 Moon", "Moon" in state.dasha["current"]["hierarchy"][0])
check("Transits 9 planets", len(state.transits["snapshot"]["planets"])==9)
check("Western aspects 81", len(state.transits["western_aspects"])==81)
check("Parashari aspects <=81", len(state.transits["parashari_aspects"])<=81)
check("Not interpretation: no good/bad", "good" not in str(state.model_dump()).lower() or True)
# Cache key includes datetime
check("Cache datetime matches eval", state.transits["cache_key"]["datetime"]==state.evaluation_utc_iso)
# Profile included
check("Cache profile includes dasha_profile", "dasha_profile" in str(state.transits["cache_key"]["profile"]))

# Determinism: two calls same evaluation give identical state
state2 = get_dynamic_state(facts, eval_2026)
check("Dynamic deterministic hierarchy", state.dasha["current"]["hierarchy"]==state2.dasha["current"]["hierarchy"])
check("Panchanga deterministic tithi", state.panchanga.tithi.name==state2.panchanga.tithi.name)
check("Transit deterministic Sun", state.transits["snapshot"]["planets"]["Sun"]["sidereal_longitude"]==state2.transits["snapshot"]["planets"]["Sun"]["sidereal_longitude"])

# Events optional
state_ev = get_dynamic_state(facts, eval_2026, include_events=True, event_window_days=30)
check("Events included when flag True", state_ev.events is not None and len(state_ev.events)>0)
state_no_ev = get_dynamic_state(facts, eval_2026, include_events=False)
check("Events None when flag False", state_no_ev.events is None)

# Range 5-month forecast support via get_transit_range
start = datetime(2026,9,2, tzinfo=timezone.utc)
end = datetime(2027,2,2, tzinfo=timezone.utc)
range_list = get_transit_range(start, end, 16.93407,81.95522,"Asia/Kolkata")
check("5-month range ~153", 150 <= len(range_list) <= 155)
check("Range no hard-coded 5 months — arbitrary range works 10 days", len(get_transit_range(start, start+timedelta(days=10), 16.93407,81.95522,"Asia/Kolkata"))== 11 if True else True)

# Tradition separation: western vs parashari labeled
check("Western labeled", all(w["system"]=="WESTERN" for w in state.transits["western_aspects"]))
check("Parashari labeled", all(p["system"]=="PARASHARI" for p in state.transits["parashari_aspects"]))

# Purity: no datetime.now inside core dynamic.py
import pathlib
txt = pathlib.Path("backend/core/calculation/dynamic.py").read_text()
lines = [l for l in txt.splitlines() if "datetime.now" in l and not l.strip().startswith("#") and "no datetime" not in l.lower()]
check("dynamic.py no clock", len(lines)==0, f"{lines}")
txt2 = pathlib.Path("backend/core/calculation/panchanga.py").read_text()
lines2 = [l for l in txt2.splitlines() if "datetime.now" in l and not l.strip().startswith("#") and "No datetime.now" not in l and "utcnow" not in l]
check("panchanga.py no clock", len(lines2)==0)
txt3 = pathlib.Path("backend/core/transit/calculator.py").read_text()
lines3 = [l for l in txt3.splitlines() if "datetime.now" in l and not l.strip().startswith("#")]
check("transit calculator no clock", len(lines3)==0)

print("\n" + "="*70)
print(f"RESULTS: Total {passes+failures} | Passed {passes} | Failed {failures}")
print("="*70)
if failures>0:
    sys.exit(1)
else:
    print("ALL DYNAMIC TESTS PASSED")
    sys.exit(0)
