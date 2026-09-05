"""
Astrolife V2 — Phase 3 Dasha Comprehensive Test Suite
Step 25 + Step 5 boundary + Step 6 year model

Golden chart: 17 Aug 2005 00:02 IST Asia/Kolkata
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from datetime import datetime, timezone, timedelta
import math
import pytz
from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DashaCalculationProfile, YearModel
from core.calculation.dasha import calculate_vimshottari_timeline, get_current_dasha, VIMSHOTTARI_YEARS, VIMSHOTTARI_ORDER
from core.calculation.nakshatra import NAKSHATRA_NAMES
import swisseph as swe

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

def check_float(name, actual, expected, tol=1e-6, msg=""):
    diff = abs(actual-expected)
    ok = diff <= tol
    results.append((ok, name, f"exp {expected} act {actual} diff {diff}"))
    if ok:
        global passes
        passes+=1
    else:
        global failures
        failures+=1
        print(f"  FAIL {name}: expected {expected} actual {actual} diff {diff} tol {tol} {msg}")
    return ok

BIRTH = dict(year=2005, month=8, day=17, hour=0, minute=2, second=0, lat=16.93407, lon=81.95522, tz="Asia/Kolkata")
print("="*70)
print("ASTROLIFE V2 — PHASE 3 DASHA TESTS (100+ checks)")
print("="*70)

facts = generate_chart_facts(
    year=BIRTH["year"], month=BIRTH["month"], day=BIRTH["day"],
    hour=BIRTH["hour"], minute=BIRTH["minute"], second=BIRTH["second"],
    lat=BIRTH["lat"], lon=BIRTH["lon"], tz_name=BIRTH["tz"]
)
print("\n--- Golden Chart Basics ---")
check("Moon nakshatra is Purvashada", facts.planets["Moon"].nakshatra.name == "Purvashada", f"got {facts.planets['Moon'].nakshatra.name}")
check("Moon pada 2", facts.planets["Moon"].nakshatra.pada == 2)
check("Moon lord Venus", facts.planets["Moon"].nakshatra.lord == "Venus")
timeline = calculate_vimshottari_timeline(facts)
check("Starting lord Venus", timeline.starting_lord == "Venus")
check_float("Remaining years Venus", timeline.remaining_years_at_birth, 13.206, tol=0.02)  # approximate, compute precise below
# Precise remaining: fraction = 0.339...
moon_lon = facts.planets["Moon"].longitude.sidereal
nak_size = 360/27
nak_float = (moon_lon %360)/nak_size
frac = nak_float - math.floor(nak_float)
exp_rem = (1-frac)*20
check_float("Remaining precise", timeline.remaining_years_at_birth, exp_rem, tol=1e-9)
check("Boundary convention half-open", "[start_jd, end_jd)" in timeline.boundary_convention)
print(f"  -> Moon {moon_lon:.6f} frac {frac:.6f} remaining {timeline.remaining_years_at_birth:.6f}")

print("\n--- Mahadasha Sequence & Durations ---")
# First MD partial duration check
first_md = timeline.mahadashas[0]["period"]
check("First MD is partial", first_md.is_partial == True)
check("First MD lord Venus", first_md.lord == "Venus")
check_float("First MD duration years", first_md.duration_years, timeline.remaining_years_at_birth, tol=1e-9)
# Subsequent MDs should be full
for i in range(1, len(timeline.mahadashas)):
    md = timeline.mahadashas[i]["period"]
    expected_years = VIMSHOTTARI_YEARS[md.lord]
    # Last may be clipped if generation window ends? For 120 years total, last MD may be partial if window clipped. But for 120y window covering full cycle, last MD should be Mercury 17? Let's check.
    # With 120 years from birth, sum should be 120, not 120+remaining? Actually first partial Venus 13.206 + Sun6+Moon10+Mars7+Rahu18+Jupiter16+Saturn19+Mercury17+Ketu7+Venus? Need to compute sum: remaining Venus + 6+10+7+18+16+19+17+7 = 113.206? To reach 120 need continue into next Venus partial etc. So timeline should cover 120 years inclusive, last MD may be Venus again?
    # We'll just assert full unless it's the last which may be partial due to generation window
    if i == len(timeline.mahadashas)-1:
        check(f"Last MD {md.lord} duration", md.duration_years >0, f"{md.duration_years}")
    else:
        check_float(f"MD {i+1} {md.lord} full years", md.duration_years, expected_years, tol=1e-9, msg=f"md {md.lord}")

# Total years sum check
total_years_sum = sum(m["period"].duration_years for m in timeline.mahadashas)
check_float("Total MD years ~120", total_years_sum, 120.0, tol=1e-6)
# Also timeline.total_years_calculated should be ~120
check_float("Timeline total_years_calculated", timeline.total_years_calculated, 120.0, tol=0.01)

# MD order covers 120 cycle: after Venus should be Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu, Venus...
expected_order_start = ["Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury","Ketu","Venus"]
actual_order = [m["period"].lord for m in timeline.mahadashas]
for i, exp in enumerate(expected_order_start):
    if i < len(actual_order):
        check(f"MD order {i} {exp}", actual_order[i]==exp, f"got {actual_order[i]}")

print("\n--- Antar / Pratyantar / Sookshma / Prana Structure ---")
# Each MD should have 9 antars except birth-sliced first MD may have fewer visible? But internal count for full MD should be 9
# For first MD partial, sliced antars count may be <9, but we check that at least 1 and <=9
for md_entry in timeline.mahadashas:
    antars = md_entry["antar_dashas"]
    md_lord = md_entry["period"].lord
    if md_entry["period"].is_partial:
        check(f"First partial MD antars <=9", 0 < len(antars) <= 9, f"{len(antars)}")
    else:
        check(f"MD {md_lord} antar count 9", len(antars)==9, f"{len(antars)}")
    # Each antar duration sum should equal MD duration (within tolerance) for non-partial MD
    if not md_entry["period"].is_partial:
        sum_antar_years = sum(a["period"].duration_years for a in antars)
        check_float(f"MD {md_lord} antar sum == MD years", sum_antar_years, md_entry["period"].duration_years, tol=1e-9)
    for ad_entry in antars:
        ad = ad_entry["period"]
        check(f"AD {md_lord}->{ad.lord} level 2", ad.level==2)
        check(f"AD parent {ad.parent_lord}=={md_lord}", ad.parent_lord==md_lord)
        # AD children are PDs
        pds = ad_entry["children"]
        # Each AD should have 9 PDs unless it's sliced partial (birth)
        if not ad.is_partial:
            check(f"AD {ad.lord} PD count 9", len(pds)==9, f"{len(pds)}")
            sum_pd_years = sum(p["period"].duration_years for p in pds)
            check_float(f"AD {ad.lord} PD sum", sum_pd_years, ad.duration_years, tol=1e-9)
        for pd_entry in pds:
            pd = pd_entry["period"]
            check(f"PD level 3", pd.level==3)
            sooks = pd_entry["children"]
            if not pd.is_partial:
                # full PD should have 9 sookshmas
                check(f"PD {pd.lord} sook count 9", len(sooks)==9, f"{len(sooks)}")
                sum_sook = sum(s["period"].duration_years for s in sooks)
                check_float(f"PD {pd.lord} sook sum", sum_sook, pd.duration_years, tol=1e-9)
            for sook_entry in sooks:
                sook = sook_entry["period"]
                check(f"Sookshma level 4", sook.level==4)
                pranas = sook_entry["children"]
                if not sook.is_partial:
                    check(f"Sook {sook.lord} prana 9", len(pranas)==9, f"{len(pranas)}")
                    sum_prana = sum(p["period"].duration_years for p in pranas)
                    check_float(f"Sook {sook.lord} prana sum", sum_prana, sook.duration_years, tol=1e-9)
                for pr in pranas:
                    check(f"Prana level 5", pr["period"].level==5)

print("\n--- Year Model (DashaCalculationProfile) ---")
profile_360 = DashaCalculationProfile(year_model=YearModel.CUSTOM, days_per_year=360.0)
timeline_360 = calculate_vimshottari_timeline(facts, profile=profile_360, years_ahead=120)
first_360 = timeline_360.mahadashas[0]["period"]
first_std = timeline.mahadashas[0]["period"]
# durations in years same but in days different — check days
check_float("Year model 360 days shorter", first_360.duration_days, first_360.duration_years*360.0, tol=1e-9)
check_float("Standard 365 days", first_std.duration_days, first_std.duration_years*365.2425, tol=1e-9)
check("Profile days_per_year differs", first_360.duration_days != first_std.duration_days)

print("\n--- Boundary Tests (half-open [start,end)) ---")
# JD double at 2.4e6 has resolution ~50 microseconds; 1 microsecond below precision, so use 1 millisecond
# which is the practical distinguishable limit and satisfies spec intent (inclusive start, exclusive end)
from core.calculation.dasha import _jd_to_utc_datetime, _evaluation_jd
md0 = timeline.mahadashas[0]["period"]
birth_jd = timeline.birth_jd
# At birth JD exactly => inside first MD
cur_birth = get_current_dasha(timeline, _jd_to_utc_datetime(birth_jd))
check("At birth JD exactly => Venus", cur_birth["mahadasha"] is not None and cur_birth["mahadasha"].lord=="Venus")
# 1 millisecond before birth — distinguishable at JD resolution
dt_birth = _jd_to_utc_datetime(birth_jd)
dt_before = dt_birth - timedelta(milliseconds=1)
# Verify JD actually moved before (since 1ms is > resolution)
jd_before = _evaluation_jd(dt_before)
check("JD 1ms before birth is before", jd_before < birth_jd, f"jd_before {jd_before} birth {birth_jd}")
cur_before = get_current_dasha(timeline, dt_before)
check("1ms before birth => before note", cur_before.get("mahadasha") is None and "before" in cur_before.get("note",""))
# Exact end of first MD => next MD (Sun)
end_jd_md0 = md0.end_jd
dt_end = _jd_to_utc_datetime(end_jd_md0)
cur_at_end = get_current_dasha(timeline, dt_end)
second_lord = timeline.mahadashas[1]["period"].lord if len(timeline.mahadashas)>1 else None
check("At exact end => next MD Sun", cur_at_end["mahadasha"] is not None and cur_at_end["mahadasha"].lord==second_lord, f"got {cur_at_end['mahadasha'].lord if cur_at_end['mahadasha'] else None} exp {second_lord}")
# 1ms before end => still first MD
dt_before_end2 = dt_end - timedelta(milliseconds=1)
# Also verify JD actually before end
jd_before_end = _evaluation_jd(dt_before_end2)
check("JD 1ms before end is before end", jd_before_end < end_jd_md0, f"{jd_before_end} vs {end_jd_md0}")
cur_before_end = get_current_dasha(timeline, dt_before_end2)
check("1ms before end => still Venus", cur_before_end["mahadasha"] is not None and cur_before_end["mahadasha"].lord=="Venus", f"got {cur_before_end['mahadasha'].lord if cur_before_end['mahadasha'] else None}")

if len(timeline.mahadashas[0]["antar_dashas"]) >= 2:
    ad0 = timeline.mahadashas[0]["antar_dashas"][0]["period"]
    ad1 = timeline.mahadashas[0]["antar_dashas"][1]["period"]
    end_ad0 = ad0.end_jd
    dt_end_ad0 = _jd_to_utc_datetime(end_ad0)
    cur_at_ad_boundary = get_current_dasha(timeline, dt_end_ad0)
    check("AD boundary exclusive => next AD", cur_at_ad_boundary["antardasha"] is not None and cur_at_ad_boundary["antardasha"].lord==ad1.lord, f"got {cur_at_ad_boundary['antardasha'].lord if cur_at_ad_boundary['antardasha'] else None} exp {ad1.lord}")
    dt_before_ad_end = dt_end_ad0 - timedelta(milliseconds=1)
    cur_before_ad = get_current_dasha(timeline, dt_before_ad_end)
    check("1ms before AD end => still first AD", cur_before_ad["antardasha"] is not None and cur_before_ad["antardasha"].lord==ad0.lord)

print("\n--- Fixed Evaluation Dates (deterministic) ---")
# Birth exact
cur0 = get_current_dasha(timeline, _jd_to_utc_datetime(birth_jd))
check("Birth hierarchy starts Venus", "Venus" in cur0["hierarchy"][:1])
# 2005-08-17 00:02 Asia/Kolkata = birth
# 2026-09-02 12:00 UTC should be Moon/Rahu/...
eval_2026 = datetime(2026,9,2,12,0,0,tzinfo=timezone.utc)
cur2026 = get_current_dasha(timeline, eval_2026)
check("2026-09-02 MD is Moon", cur2026["mahadasha"].lord=="Moon", f"got {cur2026['mahadasha'].lord if cur2026['mahadasha'] else None}")
# Check that AD etc exist
check("2026 AD exists", cur2026["antardasha"] is not None)
check("2026 PD exists", cur2026["pratyantardasha"] is not None)
check("2026 Sook exists", cur2026["sookshma"] is not None)
check("2026 Prana exists", cur2026["prana"] is not None)
# Two calls same datetime should be identical (determinism)
cur2026_b = get_current_dasha(timeline, eval_2026)
check("Determinism 2026 hierarchy identical", cur2026["hierarchy"]==cur2026_b["hierarchy"])
# Historical: 2010-01-01 should be still Venus MD (since Venus until 2018)
hist = datetime(2010,1,1,12,0,0,tzinfo=timezone.utc)
cur2010 = get_current_dasha(timeline, hist)
check("2010-01-01 MD Venus", cur2010["mahadasha"].lord=="Venus")
# End of Sun MD boundary: Sun MD is after Venus, 6 years: Venus ends ~2018-10-? So Sun 2018-2024
sun_mid = datetime(2020,6,1,12,0,0,tzinfo=timezone.utc)
cur2020 = get_current_dasha(timeline, sun_mid)
check("2020-06-01 MD Sun", cur2020["mahadasha"].lord=="Sun")
# Moon MD 2026 already, 2030 still Moon
cur2030 = get_current_dasha(timeline, datetime(2030,1,1,12,0,0,tzinfo=timezone.utc))
check("2030-01-01 MD Moon", cur2030["mahadasha"].lord=="Moon")

print("\n--- Sookshma / Prana Hierarchy Parent Checks ---")
# For 2026, check parent fields
if cur2026["antardasha"]:
    check("AD parent is MD", cur2026["antardasha"].parent_lord==cur2026["mahadasha"].lord)
if cur2026["pratyantardasha"]:
    check("PD parent is AD", cur2026["pratyantardasha"].parent_lord==cur2026["antardasha"].lord)
if cur2026["sookshma"]:
    check("Sook parent is PD", cur2026["sookshma"].parent_lord==cur2026["pratyantardasha"].lord)
if cur2026["prana"]:
    check("Prana parent is Sook", cur2026["prana"].parent_lord==cur2026["sookshma"].lord)

print("\n--- Purity: No datetime.now inside core ---")
import pathlib
core_text = pathlib.Path("backend/core/calculation/dasha.py").read_text()
# Look for actual code datetime.now(  (ignore comments/docstrings containing "No ")
code_lines = []
for l in core_text.splitlines():
    stripped = l.strip()
    if "datetime.now(" in l and "No " not in l and not stripped.startswith("#") and '"""' not in l:
        code_lines.append(l)
check("dasha core no live clock", len(code_lines)==0, f"found {code_lines}")

print("\n--- Legacy Shim Shape ---")
from calculations import compute_vimshottari_timeline as legacy_timeline
legacy = legacy_timeline(facts.time.julian_day, facts.planets["Moon"].longitude.sidereal, years_ahead=100)
check("Legacy has nakshatra_of_moon", "nakshatra_of_moon" in legacy)
check("Legacy timeline non-empty", len(legacy["timeline"])>0)
check("Legacy first lord Venus", legacy["timeline"][0]["lord"]=="Venus")
check("Legacy is_current always False (pure)", all(not m["is_current"] for m in legacy["timeline"]))

print("\n" + "="*70)
print(f"RESULTS: Total {passes+failures} | Passed {passes} | Failed {failures}")
print("="*70)
if failures>0:
    sys.exit(1)
else:
    print("ALL DASHA TESTS PASSED")
    sys.exit(0)
