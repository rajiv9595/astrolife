# diagnose_ayanamsha.py
import swisseph as swe
import os
from datetime import datetime
import pytz

print("=== swisseph module info ===")
print("module:", swe)
attrs = [a for a in dir(swe) if a.startswith("SIDM_") or a.startswith("SEIDM_") or a.startswith("SID_") or a.startswith("FLG_") or a.startswith("SEFLG_")]
print("Known SIDM constants and flags (subset):")
for a in attrs:
    print(" ", a, getattr(swe, a))

# show version-ish info (some builds expose __version__ or version)
print("swe.__version__:", getattr(swe, "__version__", "N/A"))

# ephe path that swisseph uses (if set)
try:
    # no direct getter; show what you've set if any
    print("No direct swe.get_ephe_path() in wrapper; please confirm EPHE_PATH in your app.")
except Exception:
    pass

# list user's ephe folder contents if known (edit path if different)
EPHE_PATH = r"C:\Users\RAJIV MEDAPATI\Documents\lifepath\backend\ephe"
print("\nListing ephe folder:", EPHE_PATH)
try:
    for f in sorted(os.listdir(EPHE_PATH)):
        p = os.path.join(EPHE_PATH, f)
        print(" ", f, os.path.getsize(p))
except Exception as e:
    print("  Cannot list ephe folder:", e)

# Compute JD for the sample input (17 Aug 2005 00:05 IST)
tz = pytz.timezone("Asia/Kolkata")
dt = tz.localize(datetime(2005,8,17,0,5,0))
dt_utc = dt.astimezone(pytz.utc)
jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

print("\nJD(UT) for 2005-08-17 00:05 IST =>", jd, "UTC:", dt_utc.isoformat())

# Show ayanamsa for several built-in modes (if present)
modes = []
for name in dir(swe):
    if name.startswith("SIDM_") or name.startswith("SE_SIDM_") or name.startswith("SEIDM_"):
        modes.append((name, getattr(swe, name)))
# Add known names manually if present
common = ["SIDM_LAHIRI", "SIDM_RAMAN", "SIDM_TRUE_CITRA", "SIDM_YUKTESHWAR", "SIDM_DELUCE", "SIDM_FAGAN_BRADLEY"]
print("\nTesting ayanamsa values for common sidemodes (if present):")
for nm in common:
    if hasattr(swe, nm):
        val = getattr(swe, nm)
        try:
            swe.set_sid_mode(val, 0, 0)
            a = swe.get_ayanamsa_ut(jd)
            print(f" {nm} -> {a:.9f} deg")
        except Exception as e:
            print(f" {nm} -> ERROR: {e}")
    else:
        print(f" {nm} -> not present")

# Also test current setting default:
try:
    # leave as-is (no mode change) and print get_ayanamsa
    adef = swe.get_ayanamsa_ut(jd)
    print("\nCurrent get_ayanamsa_ut(jd) =>", adef)
except Exception as e:
    print("get_ayanamsa_ut error:", e)
