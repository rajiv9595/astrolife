"""
Astrolife V2 — Phase 5G: Jaimini Dasha Calculation Foundation Tests.

Independent reference implementations below NEVER import production
calculator/sequence/duration modules; they re-derive from the profile spec
using local sign tables. Period facts only — no prediction vocabulary.
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.calculation.models import (
    ChartFacts, Location, TimeDetails, AyanamshaDetails, AscendantData,
    PlanetData, HouseData, SignPosition, NakshatraPosition, LongitudeDetails,
)
from core.calculation.config import CalculationProfile
from core.calculation.varga import calculate_all_vargas
from core.calculation.pipeline import generate_chart_facts
from core.jaimini.profile import JaiminiCalculationProfile
from core.jaimini.pipeline import generate_jaimini_facts
from core.jaimini.dasha import (
    JaiminiDashaProfile, UnsupportedDashaMethodError, IMPLEMENTED_METHOD,
    SUPPORTED_METHODS, UNSUPPORTED_METHODS, calculate_jaimini_dasha,
    validate_dasha_result, full_cycle, direction_for_start_sign,
)


total_tests = 0
passed_tests = 0
failed_tests = 0


def check(condition: bool, description: str):
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"  OK {description}")
    else:
        failed_tests += 1
        print(f"  FAIL {description}")


# ---------------------------------------------------------------------------
# Independent reference (local tables, no production imports)
# ---------------------------------------------------------------------------
REF_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
             "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
REF_LORDS = {"Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
             "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus",
             "Scorpio": "Mars", "Sagittarius": "Jupiter", "Capricorn": "Saturn",
             "Aquarius": "Saturn", "Pisces": "Jupiter"}
REF_MOV = {"Aries", "Cancer", "Libra", "Capricorn"}
REF_FIX = {"Taurus", "Leo", "Scorpio", "Aquarius"}


def ref_direction(start: str) -> str:
    if start in REF_MOV:
        return "FORWARD"
    if start in REF_FIX:
        return "REVERSE"
    return "FORWARD" if (REF_SIGNS.index(start) + 1) % 2 == 1 else "REVERSE"


def ref_step(sign: str, direction: str, n: int = 1) -> str:
    d = n if direction == "FORWARD" else -n
    return REF_SIGNS[(REF_SIGNS.index(sign) + d) % 12]


def ref_duration(sign: str, pmap: Dict[str, str], direction: str):
    lord, ls = REF_LORDS[sign], pmap[REF_LORDS[sign]]
    if ls == sign:
        return 12.0, "OWN_SIGN_TWELVE"
    a, b = REF_SIGNS.index(sign), REF_SIGNS.index(ls)
    dist = ((b - a) % 12) + 1 if direction == "FORWARD" else ((a - b) % 12) + 1
    return float(dist), "NONE"


BASE_SPEC = {
    "Sun": {"sign": "Leo", "deg": 0.0418},
    "Moon": {"sign": "Sagittarius", "deg": 17.8627},
    "Mars": {"sign": "Aries", "deg": 16.5930},
    "Mercury": {"sign": "Cancer", "deg": 14.8395},
    "Jupiter": {"sign": "Virgo", "deg": 21.8426},
    "Venus": {"sign": "Virgo", "deg": 5.6417},
    "Saturn": {"sign": "Cancer", "deg": 10.0625},
    "Rahu": {"sign": "Pisces", "deg": 22.3264},
    "Ketu": {"sign": "Virgo", "deg": 22.3264},
}


def make_chart(asc_sign: str = "Taurus", spec: Optional[Dict[str, Dict[str, Any]]] = None) -> ChartFacts:
    planets_spec = dict(BASE_SPEC)
    if spec:
        for k, v in spec.items():
            planets_spec[k] = v
    asc_idx = REF_SIGNS.index(asc_sign)
    planets_dict = {}
    for p_name, ps in planets_spec.items():
        s_idx = REF_SIGNS.index(ps["sign"])
        lon = s_idx * 30.0 + ps["deg"]
        planets_dict[p_name] = PlanetData(
            id=p_name.lower(), name=p_name,
            longitude=LongitudeDetails(tropical=lon + 24.0, sidereal=lon),
            latitude=0.0, distance=1.0, speed=1.0, retrograde=False,
            sign=SignPosition(id=s_idx + 1, name=ps["sign"], degree=ps["deg"]),
            house=((s_idx - asc_idx) % 12) + 1,
            nakshatra=NakshatraPosition(
                id=1, name="Ashwini", lord="Ketu", pada=1, fraction=0.1,
                start_longitude=0.0, end_longitude=13.33, degree_within=ps["deg"]),
        )
    houses_dict = {}
    for h in range(1, 13):
        s_idx = (asc_idx + h - 1) % 12
        houses_dict[h] = HouseData(id=h, sign=SignPosition(id=s_idx + 1, name=REF_SIGNS[s_idx], degree=0.0))
    return ChartFacts(
        calculation_profile=CalculationProfile(),
        location=Location(latitude=16.94, longitude=81.99, timezone="Asia/Kolkata"),
        time=TimeDetails(local_datetime="2005-08-17T00:02:00", timezone="Asia/Kolkata",
                         utc_datetime="2005-08-16T18:32:00Z", julian_day=2453599.2722),
        ayanamsha=AyanamshaDetails(system="LAHIRI", swiss_mode="SIDM_LAHIRI", value=23.9356),
        ascendant=AscendantData(
            longitude=LongitudeDetails(tropical=asc_idx * 30.0 + 34.0, sidereal=asc_idx * 30.0 + 10.0),
            sign=SignPosition(id=asc_idx + 1, name=asc_sign, degree=10.0),
            nakshatra=NakshatraPosition(id=3, name="Krittika", lord="Sun", pada=1, fraction=0.5,
                                        start_longitude=26.66, end_longitude=40.0, degree_within=10.0)),
        planets=planets_dict, houses=houses_dict,
    )


def pmap_of(chart: ChartFacts) -> Dict[str, str]:
    return {p: chart.planets[p].sign.name for p in chart.planets}


# ---------------------------------------------------------------------------
# 1. Profile & tradition isolation
# ---------------------------------------------------------------------------
print("\n--- 1. Profile & Tradition ---")
prof = JaiminiDashaProfile()
check(prof.method == IMPLEMENTED_METHOD, "Default method is the first implemented profile")
check(prof.method in IMPLEMENTED_METHOD, "Default method is in implemented profiles")
check(prof.source_reference == "UNVERIFIED" and prof.confidence == "TRADITION_DEPENDENT",
      "Default provenance honest (UNVERIFIED / TRADITION_DEPENDENT)")
check("CHARA_DASHA_PAKA_LAGNA_START" in UNSUPPORTED_METHODS and "STHIRA_DASHA" in UNSUPPORTED_METHODS,
      "Competing traditions listed as unsupported")
try:
    JaiminiDashaProfile(method="STHIRA_DASHA").require_supported()
    check(False, "Unsupported method raises")
except UnsupportedDashaMethodError:
    check(True, "Unsupported method raises UnsupportedDashaMethodError")
try:
    calculate_jaimini_dasha(make_chart(), None, JaiminiDashaProfile(method="NARAYANA_DASHA"))
    check(False, "Pipeline rejects unsupported method")
except UnsupportedDashaMethodError:
    check(True, "Pipeline rejects unsupported method (no silent substitution)")
check("Jaimini standard" not in JaiminiDashaProfile().method, "No vague method labels")

# ---------------------------------------------------------------------------
# 2. Starting sign (all 12) + direction + wrap-around
# ---------------------------------------------------------------------------
print("\n--- 2. Starting Sign & Sequence ---")
start_ok = True
for asc in REF_SIGNS:
    r = calculate_jaimini_dasha(make_chart(asc), None)
    if r.starting_sign != asc or r.direction != ref_direction(asc):
        start_ok = False
    if [p.sign for p in r.periods] != [ref_step(asc, ref_direction(asc), i) for i in range(12)]:
        start_ok = False
check(start_ok, "All 12 starting signs: start, direction, full 12-sign sequence vs reference")
check(full_cycle("Aries", "FORWARD")[-1] == "Pisces" and full_cycle("Aries", "REVERSE")[1] == "Pisces",
      "Wrap-around Aries<->Pisces both directions")
check(direction_for_start_sign("Gemini") == "FORWARD" and direction_for_start_sign("Virgo") == "REVERSE"
      and direction_for_start_sign("Sagittarius") == "FORWARD" and direction_for_start_sign("Pisces") == "REVERSE",
      "Dual parity rule: odd duals forward, even duals reverse")
check(direction_for_start_sign("Aries") == "FORWARD" and direction_for_start_sign("Taurus") == "REVERSE",
      "Movable forward, fixed reverse")

# ---------------------------------------------------------------------------
# 3. Duration matrix vs independent reference (12 asc x 12 signs)
# ---------------------------------------------------------------------------
print("\n--- 3. Duration Matrix ---")
dur_ok = True
own_seen = normal_seen = 0
for asc in REF_SIGNS:
    ch = make_chart(asc)
    pm = pmap_of(ch)
    r = calculate_jaimini_dasha(ch, None)
    d = ref_direction(asc)
    for p in r.periods:
        exp_dur, exp_exc = ref_duration(p.sign, pm, d)
        ev = p.duration_evidence
        if ev is None or ev.duration_years != exp_dur or ev.exception != exp_exc:
            dur_ok = False
        if ev.lord != REF_LORDS[p.sign] or ev.lord_sign != pm[REF_LORDS[p.sign]]:
            dur_ok = False
        if exp_exc == "OWN_SIGN_TWELVE":
            own_seen += 1
        else:
            normal_seen += 1
check(dur_ok, "144 period durations + lord evidence match independent reference")
check(own_seen > 0 and normal_seen > 0, f"Both exception ({own_seen}) and normal ({normal_seen}) durations covered")
# Own-sign sweep: put every lord in its own sign across fixtures
for lord, home in [("Mars", "Aries"), ("Venus", "Taurus"), ("Mercury", "Gemini"), ("Moon", "Cancer"),
                   ("Sun", "Leo"), ("Jupiter", "Sagittarius"), ("Saturn", "Capricorn")]:
    ch = make_chart("Aries", {lord: {"sign": home, "deg": 5.0}})
    r = calculate_jaimini_dasha(ch, None)
    hit = [p for p in r.periods if p.sign == home]
    if not (hit and hit[0].duration_years == 12.0 and hit[0].duration_evidence.exception == "OWN_SIGN_TWELVE"):
        dur_ok = False
check(dur_ok, "Own-sign exception verified per lord home sign")

# ---------------------------------------------------------------------------
# 4. Hierarchy, dates, boundaries, birth anchor
# ---------------------------------------------------------------------------
print("\n--- 4. Hierarchy & Dates ---")
r0 = calculate_jaimini_dasha(make_chart(), None)
check(all(len(p.antardashas) == 12 for p in r0.periods), "12 antardashas per mahadasha (144 total)")
sub_ok = True
for p in r0.periods:
    if abs(sum(c.duration_years for c in p.antardashas) - p.duration_years) > 1e-9:
        sub_ok = False
    if p.antardashas[0].start_utc_iso != p.start_utc_iso or p.antardashas[-1].end_utc_iso != p.end_utc_iso:
        sub_ok = False
    if [c.sign for c in p.antardashas] != [ref_step(p.sign, r0.direction, i) for i in range(12)]:
        sub_ok = False
    if any(c.parent_id != p.period_id for c in p.antardashas):
        sub_ok = False
check(sub_ok, "Antardasha containment, sequence, parent linkage, exact sums")
check(r0.periods[0].start_utc_iso == "2005-08-16T18:32:00Z", "Birth anchor: first period starts at birth UTC (no balance)")
check(all("T" in p.start_utc_iso and p.start_utc_iso.endswith("Z") for p in r0.periods), "Tz-aware UTC ISO dates only")
check(all(p.end_utc_iso > p.start_utc_iso for p in r0.periods), "end > start everywhere")
check(all(r0.periods[i].start_utc_iso == r0.periods[i - 1].end_utc_iso for i in range(1, 12)),
      "Contiguous half-open boundaries, no gaps/overlaps")
check(abs(r0.periods[0].duration_days - r0.periods[0].duration_years * 365.25) < 1e-6,
      "Year model 365.25 days/year explicit in conversion")

# ---------------------------------------------------------------------------
# 5. Validators + UNKNOWN + profile mismatch
# ---------------------------------------------------------------------------
print("\n--- 5. Validation & UNKNOWN ---")
check(validate_dasha_result(r0, 365.25) == [], "Golden-equivalent result validates clean")
from core.jaimini.dasha import unknown_dasha_result
u = unknown_dasha_result(JaiminiDashaProfile(), ["planet:Mars"])
check(u.status == "UNKNOWN" and u.periods == [] and validate_dasha_result(u) == [], "UNKNOWN shape validates with explanation")
try:
    from core.jaimini.profile import JaiminiCalculationProfile, CoLordMethod
    jf = generate_jaimini_facts(make_chart(), __import__(
        "core.calculation.varga", fromlist=["calculate_all_vargas"]).calculate_all_vargas(make_chart()),
        JaiminiCalculationProfile(co_lord_method=CoLordMethod.CO_LORD_STRONGER))
    calculate_jaimini_dasha(make_chart(), jf)
    check(False, "Co-lord profile mismatch raises")
except UnsupportedDashaMethodError:
    check(True, "Co-lord profile mismatch raises (lordship convention guard)")

# ---------------------------------------------------------------------------
# 6. Golden chart + snapshot + determinism + round-trip
# ---------------------------------------------------------------------------
print("\n--- 6. Golden Snapshot & Determinism ---")
gchart = generate_chart_facts(year=2005, month=8, day=17, hour=0, minute=2, second=0,
                              lat=16.9409, lon=81.9961, tz_name="Asia/Kolkata",
                              profile=CalculationProfile())
gvf = calculate_all_vargas(gchart)
gjf = generate_jaimini_facts(gchart, gvf, JaiminiCalculationProfile())
gr = calculate_jaimini_dasha(gchart, gjf)
check(gr.status == "COMPUTED" and gr.starting_sign == "Taurus" and gr.direction == "REVERSE",
      "Golden: Taurus start, REVERSE (fixed)")
check([p.sign for p in gr.periods][:4] == ["Taurus", "Aries", "Pisces", "Aquarius"],
      "Golden reverse sequence head correct")
check([p.duration_years for p in gr.periods][:3] == [9.0, 12.0, 7.0], "Golden head durations 9/12/7")
check(gr.total_years == 92.0 and gr.validation["valid"], "Golden cycle totals 92.0 years, valid")
base = gr.model_dump_json()
det_ok = all(calculate_jaimini_dasha(gchart, gjf).model_dump_json() == base for _ in range(50))
check(det_ok, "50 consecutive evaluations byte-identical")
snap_path = os.path.join(os.path.dirname(__file__), "golden_jaimini_dasha_snapshot.json")
snap = {"chart": "Golden Chart — Aug 17, 2005 00:02 AM Anaparthy",
        "engine": "jaimini-dasha/1.0.0", "evaluation": json.loads(base)}
open(snap_path, "w", encoding="utf-8").write(json.dumps(snap, indent=2))
check(os.path.exists(snap_path), "Golden dasha snapshot written by engine")
reloaded = json.load(open(snap_path, encoding="utf-8"))
fresh = calculate_jaimini_dasha(gchart, gjf)
check(reloaded["evaluation"]["periods"] == json.loads(fresh.model_dump_json())["periods"],
      "Snapshot round-trip: periods match fresh eval")
check(reloaded["evaluation"]["validation"]["valid"], "Snapshot validation recorded valid")

# ---------------------------------------------------------------------------
# 7. Guards: Vimshottari separation, no prediction, no astro
# ---------------------------------------------------------------------------
print("\n--- 7. Separation Guards ---")
from core.calculation.dasha import TOTAL_CYCLE as VIM_TOTAL
check(VIM_TOTAL == 120.0 and gr.total_years == 92.0, "Vimshottari 120-year cycle untouched and distinct")
check(gr.dasha_system == "JAIMINI_CHARA", "Dasha system explicitly JAIMINI_CHARA")
dasha_dir = os.path.join(os.path.dirname(__file__), "core", "jaimini", "dasha")
clean = True
for fn in os.listdir(dasha_dir):
    if fn.endswith(".py"):
        content = open(os.path.join(dasha_dir, fn), encoding="utf-8").read().lower()
        for tok in ["marriage will", "career will", "rich period", "dangerous period",
                    "death is indicated", "promotion is likely", "event probability",
                    "predict_events", "import openai", "chara dasha interpretation"]:
            if tok in content:
                print(f"  Forbidden token '{tok}' in {fn}")
                clean = False
check(clean, "No prediction/interpretation vocabulary in dasha package")
astro = True
for fn in os.listdir(dasha_dir):
    if fn.endswith(".py"):
        content = open(os.path.join(dasha_dir, fn), encoding="utf-8").read()
        for tok in ["import swiss", "from swe", "datetime.now", "uuid", "random"]:
            if tok in content:
                print(f"  Forbidden token '{tok}' in {fn}")
                astro = False
check(astro, "No ephemeris/clock/UUID/randomness in dasha package")
# Legacy Vimshottari still imports and runs untouched
from core.calculation.dasha import calculate_vimshottari_timeline
check(callable(calculate_vimshottari_timeline), "Vimshottari engine import intact (untouched)")

# ---------------------------------------------------------------------------
# 8. Performance
# ---------------------------------------------------------------------------
print("\n--- 8. Performance ---")
t0 = time.perf_counter()
_ = calculate_jaimini_dasha(gchart, gjf)
t_cold = time.perf_counter() - t0
t0 = time.perf_counter()
for _ in range(50):
    _ = calculate_jaimini_dasha(gchart, gjf)
t_rep = (time.perf_counter() - t0) / 50.0
print(f"  cold={t_cold:.4f}s repeated={t_rep:.4f}s")
check(t_cold < 5.0 and t_rep < 5.0, "Performance within sane bounds")

# ---------------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print(f"PHASE 5G TEST RESULTS: {passed_tests} passed, {failed_tests} failed out of {total_tests} total")
print("=" * 70)
sys.exit(1 if failed_tests else 0)
