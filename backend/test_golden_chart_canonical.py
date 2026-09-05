"""
Phase 1: Comprehensive Golden Chart Regression Test
Tests the canonical pipeline against the golden chart baseline values.
"""
import sys
import json
from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DEFAULT_PROFILE
from calculations import compute_chart

TOL = 1e-4  # Tolerance for floating point comparison

# Golden chart birth data
BIRTH = {
    "year": 2005, "month": 8, "day": 17,
    "hour": 0, "minute": 2, "second": 0,
    "lat": 16.93407, "lon": 81.95522, "tz": "Asia/Kolkata"
}

# Expected baseline from ASTROLIFE_V2_GOLDEN_CHART.md
EXPECTED_AYANAMSHA = 23.93565836563647
EXPECTED_ASC_SIDEREAL = 39.955221668117616
EXPECTED_ASC_SIGN = "Taurus"

EXPECTED_PLANETS = {
    "Sun":     {"sidereal": 120.042, "sign": "Leo"},
    "Moon":    {"sidereal": 257.863, "sign": "Sagittarius"},
    "Mercury": {"sidereal": 104.840, "sign": "Cancer"},
    "Venus":   {"sidereal": 155.642, "sign": "Virgo"},
    "Mars":    {"sidereal": 16.594, "sign": "Aries"},
    "Jupiter": {"sidereal": 171.843, "sign": "Virgo"},
    "Saturn":  {"sidereal": 100.063, "sign": "Cancer"},
    "Rahu":    {"sidereal": 352.327, "sign": "Pisces"},
    "Ketu":    {"sidereal": 172.327, "sign": "Virgo"},
}

results = []
failures = 0

def check(name, actual, expected, tol=TOL, is_string=False):
    global failures
    if is_string:
        passed = actual == expected
        diff = "N/A"
    else:
        diff = abs(actual - expected)
        passed = diff <= tol
    status = "PASS" if passed else "FAIL"
    if not passed:
        failures += 1
    results.append({
        "test": name,
        "expected": expected,
        "actual": actual,
        "diff": diff,
        "tolerance": tol if not is_string else "exact",
        "status": status
    })

print("=" * 70)
print("ASTROLIFE V2 - PHASE 1: GOLDEN CHART REGRESSION TEST")
print("=" * 70)

# --- TEST 1: Canonical Pipeline ---
print("\n--- Test Suite 1: Canonical Pipeline (generate_chart_facts) ---")
facts = generate_chart_facts(
    year=BIRTH["year"], month=BIRTH["month"], day=BIRTH["day"],
    hour=BIRTH["hour"], minute=BIRTH["minute"], second=BIRTH["second"],
    lat=BIRTH["lat"], lon=BIRTH["lon"], tz_name=BIRTH["tz"],
    location_name="Anaparthy", country_name="India"
)

# 1. Timezone
check("Time / Timezone", facts.time.timezone, "Asia/Kolkata", is_string=True)

# 2. UTC conversion (deterministic)
check("Time / UTC datetime", facts.time.utc_datetime.startswith("2005-08-16T18:32:00"), True, is_string=True)

# 3. Julian Day
check("Time / Julian Day", facts.time.julian_day, 2453599.2722222223)

# 4. Lahiri Ayanamsha
check("Ayanamsha / Lahiri value", facts.ayanamsha.value, EXPECTED_AYANAMSHA)
check("Ayanamsha / system", facts.ayanamsha.system, "LAHIRI_STANDARD", is_string=True)
check("Ayanamsha / swiss_mode", facts.ayanamsha.swiss_mode, "SIDM_LAHIRI", is_string=True)

# 5. Ascendant
check("Ascendant / sidereal longitude", facts.ascendant.longitude.sidereal, EXPECTED_ASC_SIDEREAL)
check("Ascendant / sign", facts.ascendant.sign.name, EXPECTED_ASC_SIGN, is_string=True)

# 6-14. Planets
for p_name, expected in EXPECTED_PLANETS.items():
    planet = facts.planets.get(p_name)
    if planet is None:
        check(f"Planet {p_name} / exists", False, True, is_string=True)
        continue
    check(f"Planet {p_name} / sidereal longitude", planet.longitude.sidereal, expected["sidereal"], tol=0.01)
    check(f"Planet {p_name} / sign", planet.sign.name, expected["sign"], is_string=True)

# 15. Ketu is exactly opposite Rahu
rahu_sid = facts.planets["Rahu"].longitude.sidereal
ketu_sid = facts.planets["Ketu"].longitude.sidereal
expected_ketu = (rahu_sid + 180.0) % 360.0
check("Ketu / exactly opposite Rahu", ketu_sid, expected_ketu, tol=1e-10)

# 16. Houses (Whole Sign from Ascendant)
check("Houses / House 1 sign", facts.houses[1].sign.name, EXPECTED_ASC_SIGN, is_string=True)

# 17. Nakshatra
check("Moon Nakshatra / name", facts.planets["Moon"].nakshatra.name, "Purvashada", is_string=True)

# 18. Pada
check("Moon Nakshatra / pada", facts.planets["Moon"].nakshatra.pada, 2, is_string=True)

# --- TEST 2: Legacy compute_chart backward compatibility ---
print("\n--- Test Suite 2: Legacy compute_chart backward compatibility ---")
legacy = compute_chart(
    year=BIRTH["year"], month=BIRTH["month"], day=BIRTH["day"],
    hour=BIRTH["hour"], minute=BIRTH["minute"], second=BIRTH["second"],
    tz=BIRTH["tz"], lat=BIRTH["lat"], lon=BIRTH["lon"]
)

check("Legacy / ayanamsha_deg", legacy["ayanamsha_deg"], EXPECTED_AYANAMSHA)
check("Legacy / ascendant sign", legacy["ascendant"]["sign"], EXPECTED_ASC_SIGN, is_string=True)
check("Legacy / Sun sign", legacy["planets"]["Sun"]["sign_manual"], "Leo", is_string=True)
check("Legacy / Moon sign", legacy["planets"]["Moon"]["sign_manual"], "Sagittarius", is_string=True)
check("Legacy / has dasha", legacy.get("vimshottari") is not None, True, is_string=True)
check("Legacy / has nakshatra", legacy.get("nakshatra_of_moon") is not None, True, is_string=True)

# --- TEST 3: Determinism ---
print("\n--- Test Suite 3: Determinism (two runs produce identical results) ---")
facts2 = generate_chart_facts(
    year=BIRTH["year"], month=BIRTH["month"], day=BIRTH["day"],
    hour=BIRTH["hour"], minute=BIRTH["minute"], second=BIRTH["second"],
    lat=BIRTH["lat"], lon=BIRTH["lon"], tz_name=BIRTH["tz"]
)
check("Determinism / JD identical", facts.time.julian_day, facts2.time.julian_day, tol=0)
check("Determinism / Ayanamsha identical", facts.ayanamsha.value, facts2.ayanamsha.value, tol=0)
check("Determinism / Moon sidereal identical", facts.planets["Moon"].longitude.sidereal, facts2.planets["Moon"].longitude.sidereal, tol=0)

# --- REPORT ---
print("\n" + "=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
print("-" * 70)
for r in results:
    marker = "OK" if r["status"] == "PASS" else "FAIL"
    print(f"  {marker} {r['test']}: {r['status']} (expected={r['expected']}, actual={r['actual']}, diff={r['diff']})")
print("-" * 70)

if failed > 0:
    print(f"\n*** {failed} TESTS FAILED ***")
    sys.exit(1)
else:
    print(f"\nALL {passed} TESTS PASSED")
    sys.exit(0)
