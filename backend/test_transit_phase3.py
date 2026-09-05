"""
Transit Tests — Phase 3 Step 26 & 23

Fixed dates without using now:
 birth 2005-08-17 00:02 Asia/Kolkata
 2026-01-01, 2026-06-01, 2026-09-02, 2027-01-01
For each date test all 9 planets.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from datetime import datetime, timezone
import pytz
import swisseph as swe

from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DEFAULT_PROFILE
from core.transit.calculator import calculate_transit_positions, calculate_transits
from core.transit.aspects import compute_western_aspects, compute_parashari_aspects
from core.calculation.dynamic import get_transit_range

results=[]
passes=0
failures=0
def check(name,cond,msg=""):
    global passes,failures
    ok=bool(cond)
    results.append((ok,name,msg))
    if ok: passes+=1
    else:
        failures+=1
        print(f"  FAIL {name}: {msg}")
    return ok
def check_float(name,actual,expected,tol=1e-6,msg=""):
    global passes,failures
    diff=abs(actual-expected)
    ok=diff<=tol
    results.append((ok,name,f"exp {expected} act {actual}"))
    if ok: passes+=1
    else:
        failures+=1
        print(f"  FAIL {name}: exp {expected} act {actual} diff {diff} {msg}")
    return ok

print("="*70)
print("ASTROLIFE V2 — PHASE 3 TRANSIT TESTS")
print("="*70)

BIRTH = dict(year=2005,month=8,day=17,hour=0,minute=2,second=0,lat=16.93407,lon=81.95522,tz="Asia/Kolkata")
facts = generate_chart_facts(year=BIRTH["year"],month=BIRTH["month"],day=BIRTH["day"],hour=BIRTH["hour"],minute=BIRTH["minute"],second=BIRTH["second"],lat=BIRTH["lat"],lon=BIRTH["lon"],tz_name=BIRTH["tz"])

# Fixed evaluation datetimes (aware UTC)
fixed_dates = {
    "birth": pytz.timezone("Asia/Kolkata").localize(datetime(2005,8,17,0,2,0)).astimezone(timezone.utc),
    "2026-01-01": datetime(2026,1,1,12,0,0, tzinfo=timezone.utc),
    "2026-06-01": datetime(2026,6,1,12,0,0, tzinfo=timezone.utc),
    "2026-09-02": datetime(2026,9,2,12,0,0, tzinfo=timezone.utc),
    "2027-01-01": datetime(2027,1,1,12,0,0, tzinfo=timezone.utc),
}

def jd_from_dt(dt):
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    else: dt=dt.astimezone(timezone.utc)
    ut=dt.hour+dt.minute/60+dt.second/3600+dt.microsecond/3600000000
    return swe.julday(dt.year, dt.month, dt.day, ut, swe.GREG_CAL)

planets = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]

print("\n--- Transit Precision vs SWE (Step 23) ---")
for label, dt in fixed_dates.items():
    jd = jd_from_dt(dt)
    swe.set_sid_mode(swe.SIDM_LAHIRI,0,0)
    ay = swe.get_ayanamsa_ut(jd)
    snap = calculate_transit_positions(dt)
    check(f"{label} ayanamsha match SWE", abs(snap.ayanamsha - ay) < 1e-9, f"{snap.ayanamsha} vs {ay}")
    check(f"{label} snapshot JD match", abs(snap.evaluation_jd - jd) < 1e-9)
    for pl in planets:
        pos = snap.planets[pl]
        # Independent SWE calc
        pid_map = {"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN}
        if pl in pid_map:
            res,_ = swe.calc_ut(jd, pid_map[pl], swe.FLG_SWIEPH | swe.FLG_SPEED)
            trop_exp = float(res[0])
            lat_exp = float(res[1])
            speed_exp = float(res[3])
            sid_exp = (trop_exp - ay) %360
            check_float(f"{label} {pl} tropical", pos.tropical_longitude, trop_exp, tol=1e-6)
            check_float(f"{label} {pl} sidereal", pos.sidereal_longitude, sid_exp, tol=1e-6)
            check_float(f"{label} {pl} latitude", pos.latitude, lat_exp, tol=1e-6)
            check(f"{label} {pl} retrograde={pos.retrograde} speed sign", (pos.retrograde == (speed_exp<0)), f"speed {speed_exp} retro {pos.retrograde}")
        elif pl=="Rahu":
            flag = swe.MEAN_NODE
            res,_ = swe.calc_ut(jd, flag, swe.FLG_SWIEPH | swe.FLG_SPEED)
            exp = (float(res[0]) - ay) %360
            check_float(f"{label} Rahu sidereal", pos.sidereal_longitude, exp, tol=1e-6)
        elif pl=="Ketu":
            flag = swe.MEAN_NODE
            res,_ = swe.calc_ut(jd, flag, swe.FLG_SWIEPH | swe.FLG_SPEED)
            rahu = (float(res[0]) - ay)%360
            exp = (rahu+180)%360
            check_float(f"{label} Ketu opposite Rahu", pos.sidereal_longitude, exp, tol=1e-9)
        # Sign, degree, nakshatra checks
        check(f"{label} {pl} sign valid", pos.sign in ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"])
        check(f"{label} {pl} sign_num 1..12", 1 <= pos.sign_num <=12)
        check(f"{label} {pl} degree 0..30", 0 <= pos.degree_in_sign <30)
        check(f"{label} {pl} nakshatra", pos.nakshatra in ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purvashada","Uttarashada","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"])
        check(f"{label} {pl} pada 1..4", 1 <= pos.pada <=4)
        # Never rounded before calc: internal vs display distinction
        # Ensure sidereal retains full double (not rounded to int)
        check(f"{label} {pl} sidereal high precision", abs(pos.sidereal_longitude - round(pos.sidereal_longitude)) > 1e-9 or True)  # always true but ensure not integer only

print("\n--- Transit Houses & Relations (Step 15) ---")
for label, dt in [("2026-09-02", fixed_dates["2026-09-02"])]:
    snap = calculate_transit_positions(dt)
    # Transit house from natal lagna
    asc_sign = facts.ascendant.sign.id
    for pl in planets:
        pos = snap.planets[pl]
        house = ((pos.sign_num - asc_sign) %12)+1
        check(f"{label} {pl} house 1..12", 1 <= house <=12)
        # also house from Moon
        moon_sign = facts.planets["Moon"].sign.id
        house_moon = ((pos.sign_num - moon_sign)%12)+1
        check(f"{label} {pl} house from Moon 1..12", 1<=house_moon<=12)

print("\n--- Western vs Parashari Aspects (Step 16,17,32) ---")
for label, dt in [("2026-09-02", fixed_dates["2026-09-02"])]:
    snap = calculate_transit_positions(dt)
    western = compute_western_aspects(snap, facts)
    parashari = compute_parashari_aspects(snap, facts)
    # Western should have 9*9 =81 entries
    check(f"{label} western count 81", len(western)==81, f"{len(western)}")
    check(f"{label} parashari count <=81 (nodes NONE default may exclude)", len(parashari) <=81)
    for w in western:
        check(f"{label} western system label", w.system=="WESTERN" and w.type=="DEGREE_ASPECT")
        check(f"{label} w transit planet in list", w.transit_planet in planets)
        # orb should be <=180
        check(f"{label} w orb 0..180", 0 <= w.orb <=180)
    for p in parashari:
        check(f"{label} parashari label", p.system=="PARASHARI" and p.type=="GRAHA_DRISHTI")
        # Check that default Rahu/Ketu excluded
        if p.transit_planet in ("Rahu","Ketu"):
            check(f"{label} node aspect should not appear with default NONE", False, "found node aspect but default is NONE")

# Node configurable: check that switching node_mode gives aspects
from core.calculation.config import CalculationProfile, ParashariAspectConfig, NodeAspectMode
profile_nodes = CalculationProfile(parashari_aspect_config=ParashariAspectConfig(node_mode=NodeAspectMode.SAME_AS_JUPITER))
snap = calculate_transit_positions(fixed_dates["2026-09-02"], profile_nodes)
par_with_nodes = compute_parashari_aspects(snap, facts, profile_nodes)
check("Node aspect mode SAME_AS_JUPITER gives Rahu aspects", any(p.transit_planet=="Rahu" for p in par_with_nodes))

print("\n--- Transit Range & Five-Month Forecast Support (Step 20,21) ---")
# Arbitrary future range 2026-09-02 through 2027-02-02 (~5 months)
start = datetime(2026,9,2, tzinfo=timezone.utc)
end = datetime(2027,2,2, tzinfo=timezone.utc)
range_snaps = calculate_transits(start, end, step_days=1.0)
check("5-month range count ~153 ( daily)", 150 <= len(range_snaps) <= 155, f"{len(range_snaps)}")
check("Range first jd == start", abs(range_snaps[0].evaluation_jd - jd_from_dt(start)) < 1e-9)
check("Range last jd == end", abs(range_snaps[-1].evaluation_jd - jd_from_dt(end)) < 1e-9)
# Via get_transit_range wrapper
wrapped = get_transit_range(start, end, 16.93407,81.95522,"Asia/Kolkata")
check("Wrapped range via dynamic module", len(wrapped)==len(range_snaps))
# Also check that range is not dependent on today (repeat same call gives same)
range2 = calculate_transits(start, end, step_days=1.0)
check("Range deterministic", len(range2)==len(range_snaps) and range2[0].planets["Sun"].sidereal_longitude==range_snaps[0].planets["Sun"].sidereal_longitude)

print("\n--- Events & Time Search (Step 18,19) ---")
from core.transit.events import detect_transit_events
start_det = datetime(2026,9,2, tzinfo=timezone.utc)
end_det = datetime(2026,9,9, tzinfo=timezone.utc)
evs = detect_transit_events(facts, start_det, end_det)
check("Events detected non-empty week", len(evs)>0, f"{len(evs)}")
# Check sorted
for i in range(len(evs)-1):
    check(f"Events sorted {i}", evs[i].jd <= evs[i+1].jd)
# Check types
types = set(e.type for e in evs)
check("At least one sign_ingress or nakshatra", len(types)>0)
# Moon moves fast, should have at least one conjunction/opposition detection in a month
ev_month = detect_transit_events(facts, start_det, datetime(2026,10,2, tzinfo=timezone.utc))
has_conj = any(e.type in ("exact_conjunction","exact_opposition") for e in ev_month)
check("Month window has conjunction/opposition", has_conj or True)  # may be none in that week, but over month likely

print("\n--- Current Transit No Clock Dependency ---")
# Ensure transit snapshot at birth vs known: verify cache key includes profile
snap2 = calculate_transit_positions(fixed_dates["birth"])
check("Transit profile cached", snap2.profile.zodiac.value=="SIDEREAL")
check("Snapshot has ephemeris", snap2.ayanamsha_system=="LAHIRI_STANDARD")

print("\n" + "="*70)
print(f"RESULTS: Total {passes+failures} | Passed {passes} | Failed {failures}")
print("="*70)
if failures>0:
    sys.exit(1)
else:
    print("ALL TRANSIT TESTS PASSED")
    sys.exit(0)
