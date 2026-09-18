"""
March 2027 transit-event regression (ASTROLIFE canonical event-engine fix).

Production bug: `detect_transit_events` used a wrapped signed difference
  ((lon - target + 540) % 360) - 180
with a bare `d_lo * d_hi < 0` bracket test. The +/-180 branch cut (the point
OPPOSITE the target) also yields a sign flip, so every true conjunction was
accompanied by a phantom conjunction mislabeled at its opposition point (180
deg off target) — and every true opposition by a phantom opposition. Visible
symptoms in March 2027 included same-timestamp "Moon conjunct Rahu AND Moon
conjunct Ketu" pairs (impossible: natal nodes are 180 deg apart) plus a full
set of 180-deg-off Moon conjunctions (Mar 4 Saturn, Mar 5 Mercury, Mar 6 Sun,
Mar 9 Venus, Mar 10 Jupiter/Ketu, Mar 16 Moon, Mar 23 Rahu, Mar 25 Mars).

Fix (backend/core/transit/events.py, search.py — no prompt/natal/dasha/
transit-calculator changes): reject brackets whose |d_lo - d_hi| >= 180 deg
(branch-cut jump, ~360-motion) instead of a true zero crossing (~motion).
Also fixed the `separation` detail field to measure against the actual target
(natal+180 for oppositions) instead of always against the natal longitude.

This file covers, without touching AI prompts or Gemini instructions:
  A. Canonical engine fixture (golden D1 sidereal longitudes: Rahu
     352.326431500 Pisces / Ketu 172.326431500 Virgo, matching the repo
     golden chart): all 10 March 2027 Moon-conjunction anchors within a
     strict 5-minute tolerance (observed < 1 min), planet identity,
     chronological order, no impossible Rahu+Ketu same-timestamp conjunctions,
     no 180-deg-off phantoms, separation ~0, exact total event count (82),
     and no same-pair conjunction/opposition timestamp overlap.
     NOTE: an earlier revision of this fixture used the incorrect node values
     Rahu 202.326431500 / Ketu 22.326431500; those were wrong (150 deg off the
     golden chart) and have been corrected. Natal calculation code was never
     modified to satisfy any fixture.
  B. Rahu/Ketu impossibility unit test (incl. search.py branch-cut guard).
  B. Rahu/Ketu impossibility unit test (incl. search.py branch-cut guard).
  C. Live production path (get_dynamic_state Mar 1 2027 + 30 d ->
     build_production_entry): shared-planet anchors, live-correct node times
     (live natal Rahu/Ketu 352.326/172.326 per repo golden chart), verbatim
     timestamps, March-1 starting signs, Moon/Rahu/Ketu dasha.
  D. User-question regression for "what is transit data march 2027"
     (parse_requested_range -> build_future_window_section -> AI projection):
     structured checks only (no Gemini prose): starting signs, dasha, exact
     Moon events chronological with independent Swiss Ephemeris re-verification,
     no impossible duplicates, projection preserves timestamps/identities
     verbatim.
"""
import sys
import os
_base = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, _base)
if os.path.basename(_base) == 'backend':
    sys.path.insert(0, os.path.dirname(_base))

from datetime import datetime, timezone

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


print("=" * 70)
print("MARCH 2027 TRANSIT EVENT REGRESSION")
print("=" * 70)

import swisseph as swe

try:
    from backend.core.calculation.pipeline import generate_chart_facts
    from backend.core.calculation.models import ChartFacts
    from backend.core.transit.events import detect_transit_events
    from backend.core.calculation.dynamic import get_dynamic_state
    from backend.core.transit.calculator import calculate_transit_positions
    from backend.core.transit.search import find_exact_conjunction
    from backend.routes.prediction import build_production_entry
    from backend.future_window import parse_requested_range, build_future_window_section
    from backend.ai_future_projection import project_future_window_for_ai
except ImportError:  # alternate import root (run from backend/)
    from core.calculation.pipeline import generate_chart_facts  # type: ignore
    from core.calculation.models import ChartFacts  # type: ignore
    from core.transit.events import detect_transit_events  # type: ignore
    from core.calculation.dynamic import get_dynamic_state  # type: ignore
    from core.transit.calculator import calculate_transit_positions  # type: ignore
    from core.transit.search import find_exact_conjunction  # type: ignore
    from routes.prediction import build_production_entry  # type: ignore
    from future_window import parse_requested_range, build_future_window_section  # type: ignore
    from ai_future_projection import project_future_window_for_ai  # type: ignore

BIRTH = dict(year=2005, month=8, day=17, hour=0, minute=2, second=0,
             lat=16.93407, lon=81.95522, tz="Asia/Kolkata")

# Canonical golden D1 sidereal longitudes (repo golden chart: Rahu Pisces
# 22.32643 deg = 352.326431500, Ketu Virgo 22.32643 deg = 172.326431500).
CANONICAL_NATAL = {
    "Sun": 120.041859886,
    "Moon": 257.862784835,
    "Mars": 16.593076913,
    "Mercury": 104.839559297,
    "Jupiter": 171.842642999,
    "Venus": 155.641769214,
    "Saturn": 100.062511034,
    "Rahu": 352.326431500,
    "Ketu": 172.326431500,
}

# Expected approximate UTC conjunction times, independently verified with raw
# Swiss Ephemeris (Lahiri, Mean Node): transit Moon == natal target < 1 min.
ANCHORS = [
    ("Moon", "2027-03-02T23:10:00+00:00"),
    ("Rahu", "2027-03-10T15:48:00+00:00"),
    ("Mars", "2027-03-12T11:42:00+00:00"),
    ("Saturn", "2027-03-18T10:51:00+00:00"),
    ("Mercury", "2027-03-18T18:49:00+00:00"),
    ("Sun", "2027-03-19T20:06:00+00:00"),
    ("Venus", "2027-03-22T07:50:00+00:00"),
    ("Jupiter", "2027-03-23T11:44:00+00:00"),
    ("Ketu", "2027-03-23T12:34:00+00:00"),
    ("Moon", "2027-03-30T06:59:00+00:00"),
]
# Exact deterministic contract for the March 1-31 UTC window (Swiss Ephemeris
# 2.10.03, Lahiri, Mean Node): total events and per-kind Moon counts.
EXPECTED_TOTAL_EVENTS = 82
EXPECTED_MOON_CONJ = 10
EXPECTED_MOON_OPP = 9
TOL_MIN = 5.0  # strict: observed engine error is < 1 min; do not weaken.

MARCH_START = datetime(2027, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
MARCH_END = datetime(2027, 3, 31, 0, 0, 0, tzinfo=timezone.utc)


def _parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _moon_sidereal_ut(jd):
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ay = swe.get_ayanamsa_ut(jd)
    res, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)
    return (float(res[0]) - ay) % 360.0


def _jd_of(dt):
    d = dt.astimezone(timezone.utc)
    ut = d.hour + d.minute / 60.0 + d.second / 3600.0 + d.microsecond / 3600.0 / 1_000_000.0
    return swe.julday(d.year, d.month, d.day, ut, swe.GREG_CAL)


def _moon_conjunctions(events):
    out = [e for e in events
           if e.get("transit_planet") == "Moon" and e.get("type") == "exact_conjunction"]
    return sorted(out, key=lambda e: e.get("jd", 0.0))


def _synthetic_chart(natal_map):
    chart = generate_chart_facts(year=BIRTH["year"], month=BIRTH["month"], day=BIRTH["day"],
                                 hour=BIRTH["hour"], minute=BIRTH["minute"], second=BIRTH["second"],
                                 lat=BIRTH["lat"], lon=BIRTH["lon"], tz_name=BIRTH["tz"])
    d = chart.model_dump()
    for name, lon in natal_map.items():
        d["planets"][name]["longitude"]["sidereal"] = float(lon)
    return ChartFacts(**d)


# ============ A. Canonical engine fixture (task golden longitudes) ============
print("\n--- A. Canonical Moon-conjunction anchors ---")
syn = _synthetic_chart(CANONICAL_NATAL)
check("A0. synthetic natal Rahu/Ketu 180 apart",
      abs(((float(syn.planets["Rahu"].longitude.sidereal)
            - float(syn.planets["Ketu"].longitude.sidereal)) % 360.0) - 180.0) < 1e-9)
raw = detect_transit_events(syn, MARCH_START, MARCH_END)
evs = [e.model_dump() for e in raw]
moon_conj = _moon_conjunctions(evs)
check("A1. exactly 10 Moon conjunctions in March window", len(moon_conj) == 10,
      f"got {len(moon_conj)}: {[(e.get('natal_planet'), e.get('utc_iso')) for e in moon_conj]}")

matched = [False] * len(moon_conj)
for natal_name, anchor_iso in ANCHORS:
    anchor = _parse_iso(anchor_iso)
    best = None
    for i, e in enumerate(moon_conj):
        if e.get("natal_planet") != natal_name or matched[i]:
            continue
        diff_min = abs((_parse_iso(e["utc_iso"]) - anchor).total_seconds() / 60.0)
        if best is None or diff_min < best[0]:
            best = (diff_min, i, e)
    ok = best is not None and best[0] <= TOL_MIN
    check(f"A2. Moon conj {natal_name} @ {anchor_iso} (<=5min)",
          ok, f"best={best[0]:.2f}min {best[2]['utc_iso']}" if best else "no candidate")
    if ok:
        matched[best[1]] = True
        e = best[2]
        # No 180-deg-off phantom: transit longitude must equal target.
        target = float(e["details"]["target_longitude"])
        tlon = float(e["details"]["transit_longitude"])
        wrap_sep = abs(((tlon - target + 540) % 360) - 180)
        check(f"A3. {natal_name} transit lon == target (no phantom)",
              wrap_sep < 0.05, f"target={target} tlon={tlon} sep={wrap_sep}")
        check(f"A4. {natal_name} separation ~0",
              abs(float(e["details"]["separation"])) < 0.01,
              str(e["details"]["separation"]))
        # Independent Swiss Ephemeris re-verification at reported timestamp.
        jd = _jd_of(_parse_iso(e["utc_iso"]))
        mlon = _moon_sidereal_ut(jd)
        check(f"A5. {natal_name} independently verified via SWE",
              abs(((mlon - target + 540) % 360) - 180) < 0.05,
              f"moon={mlon} target={target}")

check("A6. all 10 anchors matched exactly once", all(matched), str(matched))
isos = [e["utc_iso"] for e in moon_conj]
check("A7. chronological order", isos == sorted(isos), str(isos))
rk = {}
for e in moon_conj:
    if e.get("natal_planet") in ("Rahu", "Ketu"):
        rk.setdefault(e["utc_iso"], []).append(e["natal_planet"])
check("A8. no same-timestamp Moon-conj-Rahu + Moon-conj-Ketu",
      all(len(v) < 2 for v in rk.values()), str(rk))
check("A9. Rahu and Ketu events on distinct days",
      len({e["utc_iso"][:10] for e in moon_conj if e.get("natal_planet") in ("Rahu", "Ketu")}) == 2)
check("A10. exact total event count for March window",
      len(evs) == EXPECTED_TOTAL_EVENTS, f"got {len(evs)}")
moon_opp = sorted([e for e in evs if e.get("transit_planet") == "Moon"
                   and e.get("type") == "exact_opposition"], key=lambda e: e.get("jd", 0.0))
check("A11. exactly 9 Moon oppositions in March window", len(moon_opp) == EXPECTED_MOON_OPP,
      f"got {len(moon_opp)}: {[(e.get('natal_planet'), e.get('utc_iso')) for e in moon_opp]}")
for e in moon_opp:
    target = float(e["details"]["target_longitude"])
    jd = _jd_of(_parse_iso(e["utc_iso"]))
    mlon = _moon_sidereal_ut(jd)
    ok = abs(((mlon - target + 540) % 360) - 180) < 0.05
    check(f"A12. Moon opp {e.get('natal_planet')} independently verified (no phantom)",
          ok, f"{e.get('utc_iso')} moon={mlon} target={target}")
# No phantom opposition at a conjunction instant for the same planet pair
# (and vice versa): conj/opp timestamp sets per (transit, natal) must be disjoint.
_seen = {}
_overlap = []
for e in evs:
    if e.get("type") in ("exact_conjunction", "exact_opposition") and e.get("natal_planet"):
        key = (e.get("transit_planet"), e.get("natal_planet"), e.get("type"))
        stamp = e.get("utc_iso")
        other = "exact_opposition" if e.get("type") == "exact_conjunction" else "exact_conjunction"
        if stamp in _seen.get((e.get("transit_planet"), e.get("natal_planet"), other), set()):
            _overlap.append(key)
        _seen.setdefault(key, set()).add(stamp)
check("A13. no same-pair conj/opp timestamp overlap (phantom protection)", not _overlap,
      str(_overlap))

# ============ B. Rahu/Ketu impossibility + branch-cut guard ============
print("\n--- B. Rahu/Ketu impossibility ---")
check("B1. natal nodes 180 apart (canonical)",
      abs((CANONICAL_NATAL["Rahu"] - CANONICAL_NATAL["Ketu"]) % 360.0 - 180.0) < 1e-9)
# search.py: a window holding ONLY the opposition point must not yield a conjunction.
opp_only = find_exact_conjunction(
    "Moon", CANONICAL_NATAL["Moon"],
    datetime(2027, 3, 16, 20, 0, 0, tzinfo=timezone.utc),
    datetime(2027, 3, 16, 23, 0, 0, tzinfo=timezone.utc))
check("B2. no conjunction found at opposition point (branch-cut guard)", opp_only is None,
      str(opp_only))
true_hit = find_exact_conjunction(
    "Moon", CANONICAL_NATAL["Moon"],
    datetime(2027, 3, 2, 22, 0, 0, tzinfo=timezone.utc),
    datetime(2027, 3, 3, 0, 0, 0, tzinfo=timezone.utc))
try:
    from backend.core.transit.events import _jd_to_utc_iso as _iso_of
except ImportError:  # type: ignore
    from core.transit.events import _jd_to_utc_iso as _iso_of  # type: ignore
check("B3. true conjunction still found",
      true_hit is not None and abs(
          (_parse_iso(_iso_of(true_hit)) - _parse_iso("2027-03-02T23:10:00+00:00")
           ).total_seconds() / 60.0) < TOL_MIN,
      str(true_hit))

# ============ C. Live production path ============
print("\n--- C. Live production path (get_dynamic_state -> build_production_entry) ---")
live = generate_chart_facts(year=BIRTH["year"], month=BIRTH["month"], day=BIRTH["day"],
                            hour=BIRTH["hour"], minute=BIRTH["minute"], second=BIRTH["second"],
                            lat=BIRTH["lat"], lon=BIRTH["lon"], tz_name=BIRTH["tz"])
check("C0. live natal matches golden fixture for all 9 planets (<=0.001 deg)",
      all(abs(float(live.planets[p].longitude.sidereal) - CANONICAL_NATAL[p]) < 0.001
          for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
                    "Rahu", "Ketu")),
      "; ".join(f"{p}={float(live.planets[p].longitude.sidereal):.6f}" for p in live.planets))
check("C0b. natal engine unmodified: Rahu Pisces 22.326 / Ketu Virgo 22.326, exact opposites",
      abs(float(live.planets["Rahu"].longitude.sidereal) - 352.326431500) < 0.001 and
      abs(float(live.planets["Ketu"].longitude.sidereal) - 172.326431500) < 0.001 and
      abs(((float(live.planets["Rahu"].longitude.sidereal) -
            float(live.planets["Ketu"].longitude.sidereal)) % 360.0) - 180.0) < 1e-9 and
      int(float(live.planets["Rahu"].longitude.sidereal) // 30) == 11 and
      int(float(live.planets["Ketu"].longitude.sidereal) // 30) == 5,
      f"Rahu={float(live.planets['Rahu'].longitude.sidereal)} "
      f"Ketu={float(live.planets['Ketu'].longitude.sidereal)}")
state = get_dynamic_state(live, MARCH_START, include_events=True, event_window_days=30)
sd = state.model_dump()
live_conj = _moon_conjunctions(sd.get("events") or [])
check("C1. live path: 10 Moon conjunctions", len(live_conj) == 10,
      str([(e.get("natal_planet"), e.get("utc_iso")) for e in live_conj]))
# Shared-planet anchors must hold on the live path too (same natal longitudes).
for natal_name, anchor_iso in [a for a in ANCHORS if a[0] not in ("Rahu", "Ketu")]:
    cands = [e for e in live_conj if e.get("natal_planet") == natal_name]
    anchor = _parse_iso(anchor_iso)
    best = min((abs((_parse_iso(e["utc_iso"]) - anchor).total_seconds() / 60.0)
                for e in cands), default=None)
    check(f"C2. live Moon conj {natal_name} <=5min", best is not None and best <= TOL_MIN,
          f"best={best}")
# Live-correct node times (live natal Rahu 352.326 / Ketu 172.326 per repo golden
# chart). Independently verified: transit Moon equals natal lon at these instants.
for natal_name, expect_iso in (("Rahu", "2027-03-10T15:48:32+00:00"),
                               ("Ketu", "2027-03-23T12:34:02+00:00")):
    cands = [e for e in live_conj if e.get("natal_planet") == natal_name]
    check(f"C3. live Moon conj {natal_name} present once", len(cands) == 1,
          str([(e.get("utc_iso")) for e in cands]))
    if len(cands) == 1:
        diff = abs((_parse_iso(cands[0]["utc_iso"]) - _parse_iso(expect_iso)).total_seconds() / 60.0)
        check(f"C4. live Moon conj {natal_name} time <=5min", diff <= TOL_MIN, f"diff={diff}")
        jd = _jd_of(_parse_iso(cands[0]["utc_iso"]))
        mlon = _moon_sidereal_ut(jd)
        natal_lon = float(live.planets[natal_name].longitude.sidereal)
        check(f"C5. live {natal_name} independently verified via SWE",
              abs(((mlon - natal_lon + 540) % 360) - 180) < 0.05,
              f"moon={mlon} natal={natal_lon}")
rk_live = {}
for e in live_conj:
    if e.get("natal_planet") in ("Rahu", "Ketu"):
        rk_live.setdefault(e["utc_iso"], []).append(e["natal_planet"])
check("C6. live: no same-timestamp Rahu+Ketu conjunction", all(len(v) < 2 for v in rk_live.values()),
      str(rk_live))
check("C7. live conjunctions chronological",
      [e["utc_iso"] for e in live_conj] == sorted(e["utc_iso"] for e in live_conj))
entry = build_production_entry(sd)
prod_moon = sorted([t for t in entry.get("transit_events", [])
                    if t.get("planet") == "Moon" and t.get("kind") == "exact_conjunction"],
                   key=lambda t: t["timestamp_iso"])
check("C8. production entry preserves all 10 Moon events verbatim",
      [t["timestamp_iso"] for t in prod_moon] == [e["utc_iso"] for e in live_conj] and
      [t["natal_target"] for t in prod_moon] == [e["natal_planet"] for e in live_conj])

# ============ D. March-1 transit table (calculator untouched) ============
print("\n--- D. March 1 starting positions + Dasha ---")
snap = calculate_transit_positions(MARCH_START)
EXPECTED_SIGNS = {"Sun": "Aquarius", "Moon": "Scorpio", "Mars": "Leo",
                  "Mercury": "Capricorn", "Jupiter": "Cancer", "Venus": "Capricorn",
                  "Saturn": "Pisces", "Rahu": "Capricorn", "Ketu": "Cancer"}
for pl, sign in EXPECTED_SIGNS.items():
    check(f"D1. transit {pl} in {sign}", snap.planets[pl].sign == sign,
          f"got {snap.planets[pl].sign} lon={snap.planets[pl].sidereal_longitude:.3f}")
cur = (sd.get("dasha") or {}).get("current", {})
check("D2. Moon Mahadasha", (cur.get("mahadasha") or {}).get("lord") == "Moon",
      str((cur.get("mahadasha") or {}).get("lord")))
check("D3. Rahu Antardasha", (cur.get("antardasha") or {}).get("lord") == "Rahu",
      str((cur.get("antardasha") or {}).get("lord")))
check("D4. Ketu Pratyantardasha", (cur.get("pratyantardasha") or {}).get("lord") == "Ketu",
      str((cur.get("pratyantardasha") or {}).get("lord")))

# ============ E. User-question regression ============
print("\n--- E. 'what is transit data march 2027' structured regression ---")
import pytz as _pytz
_NOW = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)
parsed = parse_requested_range("what is transit data march 2027", _NOW, "Asia/Kolkata")
check("E1. query parses to March 2027",
      parsed is not None and parsed["future_start"].date().isoformat() == "2027-03-01" and
      parsed["future_end"].date().isoformat() == "2027-03-31", str(parsed))
check("E2. typo-tolerant variant also parses",
      parse_requested_range("what is trasit data march 2027", _NOW, "Asia/Kolkata") is not None)
sec = build_future_window_section(
    year=BIRTH["year"], month=BIRTH["month"], day=BIRTH["day"],
    hour=BIRTH["hour"], minute=BIRTH["minute"], second=BIRTH["second"],
    tz=BIRTH["tz"], lat=BIRTH["lat"], lon=BIRTH["lon"],
    range_start=parsed["future_start"], range_end=parsed["future_end"],
    label=parsed["label"])
check("E3. canonical source", sec.get("_source") == "canonical")
facts = sec.get("TRANSIT_FACTS_AT_WINDOW_START", {}) or {}
check("E4. window-start signs correct",
      all(facts.get(pl) == sign for pl, sign in EXPECTED_SIGNS.items()), str(facts))
dh = sec.get("DASHA_AT_WINDOW_START", {}) or {}
check("E5. window-start dasha Moon/Rahu hierarchy",
      dh.get("mahadasha") == "Moon" and "Rahu" in (dh.get("hierarchy") or []), str(dh))
fw_events = sec.get("EXACT_TRANSIT_EVENTS", []) or []
fw_moon = sorted([e for e in fw_events if e.get("planet") == "Moon"
                  and e.get("kind") == "exact_conjunction"],
                 key=lambda e: e["timestamp_iso"])
check("E6. future window has 10 Moon conjunctions", len(fw_moon) == 10,
      str([(e.get("natal_target"), e.get("timestamp_iso")) for e in fw_moon]))
LIVE_EXPECTED = [("Moon", "2027-03-02T23:09:41+00:00"), ("Rahu", "2027-03-10T15:48:32+00:00"),
                 ("Mars", "2027-03-12T11:41:41+00:00"), ("Saturn", "2027-03-18T10:51:00+00:00"),
                 ("Mercury", "2027-03-18T18:48:27+00:00"), ("Sun", "2027-03-19T20:05:39+00:00"),
                 ("Venus", "2027-03-22T07:49:17+00:00"), ("Jupiter", "2027-03-23T11:43:24+00:00"),
                 ("Ketu", "2027-03-23T12:34:02+00:00"), ("Moon", "2027-03-30T06:58:16+00:00")]
for (natal_name, expect_iso), e in zip(LIVE_EXPECTED, fw_moon):
    diff = abs((_parse_iso(e["timestamp_iso"]) - _parse_iso(expect_iso)).total_seconds() / 60.0)
    check(f"E7. window Moon conj {natal_name} <=5min",
          e.get("natal_target") == natal_name and diff <= TOL_MIN,
          f"{e.get('natal_target')} {e.get('timestamp_iso')} diff={diff:.2f}min")
    jd = _jd_of(_parse_iso(e["timestamp_iso"]))
    mlon = _moon_sidereal_ut(jd)
    natal_lon = float(live.planets[natal_name].longitude.sidereal)
    check(f"E8. window {natal_name} independently verified via SWE",
          abs(((mlon - natal_lon + 540) % 360) - 180) < 0.05,
          f"moon={mlon} natal={natal_lon}")
rk_fw = {}
for e in fw_moon:
    if e.get("natal_target") in ("Rahu", "Ketu"):
        rk_fw.setdefault(e["timestamp_iso"], []).append(e["natal_target"])
check("E9. window: no impossible Rahu+Ketu conjunction", all(len(v) < 2 for v in rk_fw.values()),
      str(rk_fw))
check("E10. window events chronological",
      [e["timestamp_iso"] for e in fw_moon] == sorted(e["timestamp_iso"] for e in fw_moon))
proj = project_future_window_for_ai(sec, "what is transit data march 2027")
sent = proj.get("EXACT_TRANSIT_EVENTS", []) or []
complete_keys = {(e.get("planet"), e.get("kind"), e.get("natal_target"), e.get("timestamp_iso"))
                 for e in fw_events}
check("E11. projection alters nothing (verbatim subset)",
      len(sent) > 0 and all((e.get("planet"), e.get("kind"), e.get("natal_target"),
                             e.get("timestamp_iso")) in complete_keys for e in sent),
      f"sent={len(sent)} total={len(fw_events)}")
check("E12. provenance canonical",
      (sec.get("PROVENANCE") or {}).get("source") == "canonical_transit_engine" and
      (sec.get("PROVENANCE") or {}).get("system") == "Swiss Ephemeris")

print("\n" + "=" * 70)
print(f"MARCH 2027 TESTS: {passes} passed, {failures} failed")
print("=" * 70)
if failures:
    raise SystemExit(1)
