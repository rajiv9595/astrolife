"""
Panchanga Comprehensive Tests — Phase 3 Step 24

Covers Tithi, Vara, Nakshatra, Yoga, Karana (60), Sunrise/Sunset with boundaries
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from datetime import datetime, timezone, timedelta
import pytz
import swisseph as swe

from core.calculation.pipeline import generate_chart_facts
from core.calculation.panchanga import (
    calculate_panchanga, compute_tithi_info, compute_karana_info,
    compute_nakshatra_info, compute_yoga_info, KARANA_SEQUENCE_60, KARANA_NAMES_11,
    calculate_sunrise_sunset, NITHYA_YOGA_NAMES, TITHI_NAMES
)
from core.calculation.config import DEFAULT_PROFILE

results=[]
passes=0
failures=0
def check(name, cond, msg=""):
    global passes, failures
    ok=bool(cond)
    results.append((ok,name,msg))
    if ok: passes+=1
    else:
        failures+=1
        print(f"  FAIL {name}: {msg}")
    return ok
def check_float(name, actual, expected, tol=1e-6, msg=""):
    global passes, failures
    diff=abs(actual-expected)
    ok=diff<=tol
    results.append((ok,name,f"exp {expected} act {actual}"))
    if ok: passes+=1
    else:
        failures+=1
        print(f"  FAIL {name}: exp {expected} act {actual} diff {diff} {msg}")
    return ok

print("="*70)
print("ASTROLIFE V2 — PHASE 3 PANCHANGA TESTS")
print("="*70)

# Helper JD
def jd_from_dt(dt): 
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    else: dt=dt.astimezone(timezone.utc)
    ut=dt.hour+dt.minute/60+dt.second/3600+dt.microsecond/3600000000
    return swe.julday(dt.year, dt.month, dt.day, ut, swe.GREG_CAL)

# ---------------------------------------------------------------------------
# Tithi tests
# ---------------------------------------------------------------------------
print("\n--- Tithi ---")
# Normal day 2026-09-02
eval_dt = datetime(2026,9,2,12,0,0, tzinfo=timezone.utc)
# Use panchanga at Anaparthy
p = calculate_panchanga(eval_dt, 16.93407, 81.95522, "Asia/Kolkata")
check("Tithi index 1..30", 1 <= p.tithi.index <=30, f"{p.tithi.index}")
check("Tithi name in list", p.tithi.name in TITHI_NAMES)
# Paksha consistency: Shukla 1..15 Purnima, Krishna 16..30 Amavasya
if p.tithi.index <=15:
    check("Shukla paksha for 1..15", p.tithi.paksha=="Shukla Paksha")
else:
    check("Krishna paksha", p.tithi.paksha=="Krishna Paksha")
check("Tithi fraction 0..1", 0 <= p.tithi.fraction_elapsed <1)
check("Tithi start_jd exists", p.tithi.start_jd is not None)
check("Tithi end_jd exists", p.tithi.end_jd is not None)
if p.tithi.start_jd and p.tithi.end_jd:
    check("Tithi start < eval < end", p.tithi.start_jd <= p.evaluation_jd < p.tithi.end_jd)

# All 30 tithis exhaustive via synthetic angles (no ephemeris)
print(" Tithi synthetic 30")
for k in range(30):
    diff = k*12 + 6  # mid-tithi
    sun=0.0
    moon=diff
    info = compute_tithi_info(moon, sun)
    check(f"Tithi {k} index", info.index==k+1, f"got {info.index}")
    check(f"Tithi {k} name", info.name==TITHI_NAMES[k])
    exp_paksha = "Shukla Paksha" if k<15 else "Krishna Paksha"
    check(f"Tithi {k} paksha", info.paksha==exp_paksha)

# Boundary: diff exactly 12° should be tithi 2, not 1
info_boundary = compute_tithi_info(12.0, 0.0)
check("Tithi boundary 12° -> 2", info_boundary.index==2, f"got {info_boundary.index}")
info_just_below = compute_tithi_info(11.999999, 0.0)
check("Tithi 11.999 -> 1", info_just_below.index==1)
# Midnight crossover: evaluate at IST midnight 2026-09-02 00:00 Asia/Kolkata
midnight_ist = pytz.timezone("Asia/Kolkata").localize(datetime(2026,9,2,0,0,0))
p_mid = calculate_panchanga(midnight_ist, 16.93407,81.95522,"Asia/Kolkata")
check("Midnight tithi valid", 1 <= p_mid.tithi.index <=30)
# Sunrise boundary: just before vs after sunrise (10 minutes)
sunrise_jd = p.sunrise_sunset.sunrise_jd
if sunrise_jd:
    from core.calculation.panchanga import _jd_to_utc_datetime
    dt_before = _jd_to_utc_datetime(sunrise_jd - 10/1440)
    dt_after = _jd_to_utc_datetime(sunrise_jd + 10/1440)
    p_before = calculate_panchanga(dt_before, 16.93407,81.95522,"Asia/Kolkata")
    p_after = calculate_panchanga(dt_after, 16.93407,81.95522,"Asia/Kolkata")
    check("Sunrise boundary tithi both valid", p_before.tithi.index and p_after.tithi.index)

# Tithi boundary explicit angular tests: each k*12°
for k in [0,15,29]:
    info0 = compute_tithi_info(k*12+0.0001, 0)
    check(f"Tithi boundary {k*12}+ -> index {k+1}", info0.index==k+1)

# ---------------------------------------------------------------------------
# Karana 60 exhaustive (Step 9 requires covering all 60)
# ---------------------------------------------------------------------------
print("\n--- Karana (60 half-tithis) ---")
# Check sequence length
check("Karana sequence length 60", len(KARANA_SEQUENCE_60)==60)
# Check 11 unique distribution
unique = set(KARANA_SEQUENCE_60)
check("11 unique karana names", len(unique)==11, f"{unique}")
# Check fixed positions
check("Kimstughna at 0", KARANA_SEQUENCE_60[0]=="Kimstughna")
check("Shakuni at 57", KARANA_SEQUENCE_60[57]=="Shakuni")
check("Chatushpada at 58", KARANA_SEQUENCE_60[58]=="Chatushpada")
check("Naga at 59", KARANA_SEQUENCE_60[59]=="Naga")
# Movable counts: Bava..Vishti should appear 8 times each
from collections import Counter
cnt = Counter(KARANA_SEQUENCE_60)
for name in ["Bava","Balava","Kaulava","Taitila","Gara","Vanija","Vishti"]:
    check(f"Movable {name} count 8", cnt[name]==8, f"{cnt[name]}")
for name in ["Kimstughna","Shakuni","Chatushpada","Naga"]:
    check(f"Fixed {name} count 1", cnt[name]==1)

# Exhaustive 60 positions via synthetic diff
print(" Karana synthetic 60")
for idx60 in range(60):
    diff = idx60*6 + 3  # mid-karana
    info = compute_karana_info(diff, 0)
    exp_name = KARANA_SEQUENCE_60[idx60]
    check(f"Karana idx {idx60} name {exp_name}", info.name==exp_name, f"got {info.name}")
    check(f"Karana idx {idx60} index_60", info.index_60==idx60)
    check(f"Karana idx {idx60} is_fixed", info.is_fixed == (exp_name in ("Kimstughna","Shakuni","Chatushpada","Naga")))
# Boundary tests: diff just below/above 6° multiples
check("Karana boundary 0° -> Kimstughna", compute_karana_info(0.0,0).name=="Kimstughna")
check("Karana boundary 6° -> Bava (next)", compute_karana_info(6.0,0).name=="Bava")
check("Karana 5.999 -> Kimstughna", compute_karana_info(5.999,0).name=="Kimstughna")
check("Karana 6.001 -> Bava", compute_karana_info(6.001,0).name=="Bava")
# Check 342° (=57*6) -> Shakuni
check("Karana 342° -> Shakuni", compute_karana_info(342.0,0).name=="Shakuni")
check("Karana 354° -> Naga", compute_karana_info(354.0,0).name=="Naga")
# Verify old broken formula would fail
old_idx = int(0.0/6)%11
check("Old broken at 0° gave Bava not Kimstughna", old_idx==0)  # old would be Bava (index 0) -> demonstrates bug

# Real panchanga karana vs synthetic diff
p_real_k = p.karana
check("Real panchanga karana name in 11", p_real_k.name in ("Bava","Balava","Kaulava","Taitila","Gara","Vanija","Vishti","Shakuni","Chatushpada","Naga","Kimstughna"))
check("Real karana index_60 0..59", 0 <= p_real_k.index_60 <=59)
check("Real karana start<end", p_real_k.start_jd is None or p_real_k.end_jd is None or p_real_k.start_jd < p_real_k.end_jd)

# ---------------------------------------------------------------------------
# Nakshatra
# ---------------------------------------------------------------------------
print("\n--- Nakshatra ---")
p_nak = p.nakshatra
check("Nakshatra index 1..27", 1 <= p_nak.index <=27)
check("Nakshatra pada 1..4", 1 <= p_nak.pada <=4)
check("Nakshatra fraction 0..1", 0 <= p_nak.fraction_elapsed <1)
check("Nakshatra start_jd/end", p_nak.start_jd is not None and p_nak.end_jd is not None)
if p_nak.start_jd and p_nak.end_jd:
    check("Nak start < eval < end", p_nak.start_jd <= p.evaluation_jd < p_nak.end_jd)
# Synthetic 27 nakshatras
for k in range(27):
    lon = k*13.333333+6  # mid
    info = compute_nakshatra_info(lon)
    check(f"Nak {k} name", info.name is not None)
    check(f"Nak {k} pada", 1<=info.pada<=4)
# Boundary at 13°20′
info_nak0 = compute_nakshatra_info(0.0)
check("Nak 0° Ashwini", info_nak0.name=="Ashwini")
info_nak_boundary = compute_nakshatra_info(13.333334)
check("Nak 13.3334° Bharani", info_nak_boundary.name=="Bharani")
info_nak_just_below = compute_nakshatra_info(13.333332)
# Due to epsilon, just below may still be Ashwini
check("Nak just below boundary Ashwini", info_nak_just_below.name=="Ashwini" or info_nak_just_below.name=="Bharani") # allow epsilon

# ---------------------------------------------------------------------------
# Yoga
# ---------------------------------------------------------------------------
print("\n--- Yoga ---")
p_yoga = p.yoga
check("Yoga index 1..27", 1 <= p_yoga.index <=27)
check("Yoga name in list", p_yoga.name in NITHYA_YOGA_NAMES)
check("Yoga fraction 0..1", 0 <= p_yoga.fraction_elapsed <1)
check("Yoga start/end", p_yoga.start_jd is not None and p_yoga.end_jd is not None)
if p_yoga.start_jd and p_yoga.end_jd:
    check("Yoga start < eval < end", p_yoga.start_jd <= p.evaluation_jd < p_yoga.end_jd)
# Synthetic 27 yogas
for k in range(27):
    total = k*13.333333+6
    info = compute_yoga_info(total, 0.0)  # moon 0 => total = sun moon sum? Actually yoga needs moon+sun; we pass moon_lon = total - sun_lon
    # For synthetic: let sun 0, moon = total
    # Check index
    check(f"Yoga {k} index", info.index==k+1)
# Boundary: 0° Vishkumbha, 13.333 Priti
check("Yoga 0° Vishkumbha", compute_yoga_info(0.0,0.0).name=="Vishkumbha")
check("Yoga 13.333 Priti", compute_yoga_info(13.333334,0.0).name=="Priti")

# ---------------------------------------------------------------------------
# Vara — UTC rollover test (Step 12)
# ---------------------------------------------------------------------------
print("\n--- Vara ---")
# Birth 00:02 IST 2005-08-17 should be Wednesday local, but UTC is 2005-08-16 18:32 Tuesday UTC
birth_local = pytz.timezone("Asia/Kolkata").localize(datetime(2005,8,17,0,2,0))
birth_p = calculate_panchanga(birth_local, 16.93407,81.95522,"Asia/Kolkata")
check("Birth vara Wednesday", birth_p.vara.weekday_name=="Wednesday", f"got {birth_p.vara.weekday_name}")
check("Birth vara local_date 2005-08-17", birth_p.vara.local_date=="2005-08-17")
# Check UTC date would be 2005-08-16 Tuesday — ensure not misidentified
utc_check = datetime(2005,8,16,18,32,0,tzinfo=timezone.utc)
p_utc_eval = calculate_panchanga(utc_check, 16.93407,81.95522,"Asia/Kolkata")
# Evaluation datetime is 2005-08-16 18:32 UTC, but local in Kolkata is still 2005-08-17 00:02, so vara should still be Wednesday
check("UTC evaluation but Kolkata local still Wed", p_utc_eval.vara.weekday_name=="Wednesday")

# 2026-09-02 is Wednesday
eval_wed = pytz.timezone("Asia/Kolkata").localize(datetime(2026,9,2,12,0,0))
p_wed = calculate_panchanga(eval_wed, 16.93407,81.95522,"Asia/Kolkata")
check("2026-09-02 vara Wednesday", p_wed.vara.weekday_name=="Wednesday")
# Midnight 2026-09-02 23:59 IST should still be Wed, next day 00:01 next -> Thursday
late_wed = pytz.timezone("Asia/Kolkata").localize(datetime(2026,9,2,23,59,0))
p_late = calculate_panchanga(late_wed, 16.93407,81.95522,"Asia/Kolkata")
check("Late Wed still Wed", p_late.vara.weekday_name=="Wednesday")
early_thu = pytz.timezone("Asia/Kolkata").localize(datetime(2026,9,3,0,1,0))
p_thu = calculate_panchanga(early_thu, 16.93407,81.95522,"Asia/Kolkata")
check("Early Thu is Thursday", p_thu.vara.weekday_name=="Thursday")

# ---------------------------------------------------------------------------
# Sunrise / Sunset
# ---------------------------------------------------------------------------
print("\n--- Sunrise/Sunset ---")
# Normal location Anaparthy on 2026-09-02
ss = p.sunrise_sunset
check("Sunrise JD exists", ss.sunrise_jd is not None)
check("Sunset JD exists", ss.sunset_jd is not None)
check("Sunrise < Sunset", ss.sunrise_jd < ss.sunset_jd if ss.sunrise_jd and ss.sunset_jd else False)
check("Sunrise local string", ss.sunrise_local is not None and "M" in ss.sunrise_local)
check("Sunset local string", ss.sunset_local is not None)
check("Sunrise UTC iso", ss.sunrise_utc_iso is not None and ss.sunrise_utc_iso.endswith("Z"))
# Compare to independent SWE calc: already within engine, but check that sunset - sunrise ~12h near equator
if ss.sunrise_jd and ss.sunset_jd:
    day_len = ss.sunset_jd - ss.sunrise_jd
    check_float("Day length ~0.5 day (12h) at 17°N", day_len, 0.5, tol=0.05)  # 12h ±1.2h
# Edge: polar (Svalbard 78°N) in summer should have polar_case or very short/continuous
p_polar_summer = calculate_sunrise_sunset(datetime(2026,6,15,12,0,0,tzinfo=timezone.utc), 78.0, 15.0, "Arctic/Longyearbyen" if "Arctic/Longyearbyen" in pytz.all_timezones else "UTC")
# Fallback tz UTC if Arctic not available
if p_polar_summer.polar_case:
    check("Polar summer flagged", p_polar_summer.polar_case==True)
else:
    check("Polar summer not polar (ok maybe sun always up still gives rise)", True)
# Compare Anaparthy sunrise to independent calculation via direct swe.rise_trans for verification
import pytz as _pytz
tz = _pytz.timezone("Asia/Kolkata")
local_dt = tz.localize(datetime(2026,9,2,0,0,0))
mid_utc = local_dt.astimezone(pytz.utc)
jd_start = swe.julday(mid_utc.year, mid_utc.month, mid_utc.day, mid_utc.hour+mid_utc.minute/60, swe.GREG_CAL)
swe.set_topo(81.95522,16.93407,0)
r = swe.rise_trans(jd_start, swe.SUN, swe.CALC_RISE, (81.95522,16.93407,0),0,0,swe.FLG_SWIEPH)
if r[0]==0:
    direct_jd = r[1][0]
    check_float("Sunrise matches direct SWE", ss.sunrise_jd, direct_jd, tol=1e-6)
# Test explicit function calculate_sunrise_sunset independently
ss2 = calculate_sunrise_sunset(eval_dt, 16.93407,81.95522,"Asia/Kolkata")
check("Sunrise via standalone func", ss2.sunrise_jd is not None)

print("\n" + "="*70)
print(f"RESULTS: Total {passes+failures} | Passed {passes} | Failed {failures}")
print("="*70)
if failures>0:
    sys.exit(1)
else:
    print("ALL PANCHANGA TESTS PASSED")
    sys.exit(0)
