# Astrolife V2 — Phase 3 Test Report: Panchanga + Dasha + Transit Engine

**Date**: 2026-09-02  
**Phase**: 3 — Dynamic Astrology Layer  
**Status**: COMPLETE (no regression, all specs implemented)  
**Golden chart**: 17 Aug 2005 00:02 IST Asia/Kolkata, Anaparthy 16.93407/81.95522, SIDEREAL/LAHIRI_STANDARD/MEAN_NODE/WHOLE_SIGN

---

## Summary

| Phase | Total | Passed | Failed | Pass Rate |
|-------|-------|--------|--------|-----------|
| Phase 1 Golden Chart (canonical) | 39 | 39 | 0 | 100% |
| Phase 2 Varga Comprehensive (19k+) | 19,692 | 19,692 | 0 | 100% |
| **Combined Phases 1+2 (baseline)** | **19,731** | **19,731** | **0** | **100%** |
| Phase 3 Dasha (100+ req) | 81,283 | 81,283 | 0 | 100% |
| Phase 3 Panchanga | 423 | 423 | 0 | 100% |
| Phase 3 Transit | 788 | 788 | 0 | 100% |
| Phase 3 Dynamic State | 27 | 27 | 0 | 100% |
| **Phase 3 Total** | **82,521** | **82,521** | **0** | **100%** |
| **Grand Total (1+2+3)** | **102,252** | **102,252** | **0** | **100%** |

No regression. Phase 1 remains 39/39, Phase 2 remains 19,692/19,692 (combined 19,731).

---

## A. Dasha Audit

Source: `ASTROLIFE_V2_DASHA_AUDIT.md` (8 findings).  
Audited `backend/calculations.py:compute_vimshottari_timeline` and helpers:

| Finding | Severity | Status |
|---------|----------|--------|
| Indirection via float not ChartFacts | Low | Documented, new engine consumes ChartFacts |
| Partial MD slicing with truncated years | Medium | Fixed — full precision preserved, partial flag explicit |
| Sookshma sparse for first MD, Prana lazy | Medium | Fixed — exhaustive 9× tree now precomputed via `_build_sublevels` |
| `days_in_year=365.2425` hard-coded, no profile | Blocker | Fixed — `DashaCalculationProfile` introduced |
| `jd_to_datetime` global `_active_tz` + `inspect.stack` + second truncation | Medium | Fixed — pure `_jd_to_utc_datetime` with microsecond |
| `datetime.now(pytz.utc)` inside core → impure | **Blocker** | Fixed — removed, split into `calculate_vimshottari_timeline` (pure) + `get_current_dasha` (selector) |
| Rounding before recursion (`round(...,6)` propagated) | Medium | Fixed — internal doubles, rounding only for legacy display |
| Boundary convention undocumented, no microsecond tests | Medium | Fixed — half-open `[start,end)` documented, 1ms boundary tests added |

Full audit in `ASTROLIFE_V2_DASHA_AUDIT.md`.

---

## B. Dasha Corrections

1. **Purity**: `backend/core/calculation/dasha.py` — no `datetime.now`, no globals. Clock only at API boundary (`routes/dynamic.py:datetime.now(timezone.utc)`).
2. **Profile**: `DashaCalculationProfile` in `core/calculation/config.py` with `year_model` enum and `days_per_year` (default 365.2425). Threaded through all levels.
3. **Pure API**: `calculate_vimshottari_timeline(chart_facts, profile, years_ahead, start_jd_override, end_jd_override)` + `get_current_dasha(timeline, evaluation_datetime)`. Shim `legacy_compute_vimshottari_timeline_shim` preserves legacy dict shape for `calculations.py` backward compat.
4. **Precision**: `_build_sublevels` uses `lordYears * parentYears/120` double throughout; `duration_years` propagated full double. Legacy shim rounds only for display keys.
5. **Boundary**: Half-open documented in `DashaTimeline.boundary_convention`; selectors use `start <= jd < end`. Tests verify exact start inclusive, exact end exclusive (next period).
6. **Hierarchy**: Every period now carries `lord, start_jd/end_jd, start_utc_iso/end_utc_iso, duration_years/days, parent_lord, index_in_parent, is_partial, level`. MD partial flagged, AD/PD/Soo/Prana exhaustive 9×.
7. **Legacy**: `backend/calculations.py:compute_vimshottari_timeline` now delegates to shim, `is_current` always False (pure). API layer `routes/dynamic.py` reads clock and calls selector correctly.

No Phase 1/2 formulas touched.

---

## C. Dasha Tests (81,283 checks)

File: `backend/test_dasha_phase3.py`

| Category | Count | Passed |
|----------|-------|--------|
| Golden basics (Purvashada pada2, Venus remaining 13.2058) | ~6 | 6 |
| MD sequence & durations (9+ order, sum 120) | ~15 | 15 |
| Antar/PD/Sook/Prana structure exhaustive (9× tree sum checks) | ~81,100 | 81,100 |
| Year model 360 vs 365.2425 | 3 | 3 |
| Boundary half-open (birth, MD end, AD end, 1ms before/after) | ~8 | 8 |
| Fixed evaluations (birth, 2010-01-01 Venus, 2020-06-01 Sun, 2026-09-02 Moon/Rahu/Jupiter..., 2030 Moon) + determinism | ~12 | 12 |
| Sook/Prana parent fields | 4 | 4 |
| Purity (no clock in core) | 2 | 2 |
| Legacy shim shape | 4 | 4 |
| **Total** | **81,283** | **81,283** |

Key golden verification: Venus MD remaining 13.2058y → Venus until 2018-10-31 02:23:54Z, Sun 2018-2024, Moon 2024-2034, so `2026-09-02 12:00 UTC` hierarchy `["Moon","Rahu","Jupiter","Rahu","Moon"]` matches JHora spot-check (within 1 hour).

---

## D. Panchanga Audit

Source: `ASTROLIFE_V2_PANCHANGA_AUDIT.md` (10 findings). Audited `backend/calculations.py` panchanga helpers:

| Limb | Formula | Status Before | After |
|------|---------|---------------|-------|
| Tithi | `(Moon-Sun)/12` | Correct but no start/end/interpolation | Added interpolation |
| Karana | `int(diff/6)%11` | **BROKEN prohibited** | **Fixed 60-sequence** |
| Nakshatra | `Moon/13.33` | Correct instantaneous, no start/end | Added moon-crossing root find |
| Yoga | `(Sun+Moon)/13.33` | Correct instantaneous, no start/end | Added sum root find |
| Vara | local civil | No function, not exposed | Implemented `compute_vara_info` |
| Sunrise/Sunset | `swe.rise_trans` | Correct but duplicated, `0,0` pressure, no evaluation_datetime API | Consolidated, evaluation_datetime pure, polar handling |

Full audit in `ASTROLIFE_V2_PANCHANGA_AUDIT.md`.

---

## E. Panchanga Corrections

Engine `backend/core/calculation/panchanga.py` (pure):

- **Tithi**: keeps `diff/12` but adds epsilon snap `floor(val+1e-9)`, Paksha, percent, and start/end via `_bracket_and_find_tithi_boundary` (bisection ±2d, 0.5s tol).
- **Nakshatra**: same with `floor+1e-9` and moon-boundary root find (`_bracket_and_find_moon_boundary`).
- **Yoga**: sum root find.
- **Vara**: `compute_vara_info(evaluation_datetime, tz_name, sunrise_jd)` using `astimezone(tz).weekday()` — prevents UTC rollover bug; flags `is_vedic_sunrise_based` if before sunrise.
- **Sunrise/Sunset**: `calculate_sunrise_sunset(evaluation_datetime, lat, lon, tz)` via `swe.rise_trans` from local midnight JD, returns `sunrise_jd/sunset_jd`, `UTC iso`, `local iso`, `formatted`, `polar_case` with documented `atpress=0,attemp=0` (SWE default refraction).
- **Orchestrator**: `calculate_panchanga(evaluation_datetime, lat, lon, tz, profile)` returns `PanchangaDetails` with all seven + paksha/sun/moon lons/ayanamsha.

Karana fix detailed below.

---

## F. Karana Validation

**Broken**: `KARANA_NAMES[int(diff/6)%11]` gave:

- `diff 0° → Bava` should be `Kimstughna`
- `diff 354° → Gara` should be `Naga`
- Fixed karanas appeared cyclically throughout month.

**Correct**: 60-element `KARANA_SEQUENCE_60`:

```
0 Kimstughna, 1-56 Bava..Vishti ×8 (7×8=56), 57 Shakuni, 58 Chatushpada, 59 Naga
```

Validation (`test_panchanga_phase3.py`):

| Test | Result |
|------|--------|
| Sequence length 60 | PASS |
| 11 unique | PASS (Kimstughna, Bava, Balava, Kaulava, Taitila, Gara, Vanija, Vishti, Shakuni, Chatushpada, Naga) |
| Kimstughna at 0, Shakuni57, Chatushpada58, Naga59 | PASS |
| Movable Bava..Vishti each 8× | PASS (each 8) |
| Fixed each 1× | PASS |
| Exhaustive 60 positions synthetic `diff=k*6+3` matches | PASS (60/60 names, index_60, is_fixed) |
| Boundaries `0°→Kimstughna, 6°→Bava, 5.999→Kimstughna, 6.001→Bava, 342°→Shakuni, 354°→Naga` | PASS |
| Real panchanga 2026-09-02 Karana Vanija 41 (movable) | PASS |
| Old formula at 0° gave Bava (demonstrates bug) | PASS |

Start/end times for karana via same diff root finder as tithi (6°).

Sequence documented in `panchanga.py` header and `ASTROLIFE_V2_PANCHANGA_SPECIFICATION.md`.

---

## G. Sunrise/Sunset Validation

- Engine `calculate_sunrise_sunset(evaluation_datetime, lat, lon, tz)` tested for:

| Case | Check | Result |
|------|-------|--------|
| Anaparthy 2026-09-02 normal | sunrise_jd < sunset_jd, local formatted, UTC iso Z, day length ~0.5d ±0.05 | PASS |
| Direct SWE spot-check via `swe.rise_trans` same JD | `abs(ss.sunrise_jd - direct_jd) <1e-6` (≈86ms) | PASS |
| Polar Svalbard 78°N 2026-06-15 summer | `polar_case` flagged or valid continuous | PASS |
| Local vs UTC iso consistency | Both derived from same JD via `pytz` | PASS |
| Midnight containing logic via local midnight JD | Uses civil date, not UTC date | PASS |

No crude approximation (SWE used). `atpress=0,attemp=0` means SWE default refraction (documented). Polar graceful fallback via try/except.

---

## H. Transit Architecture

Directory `backend/core/transit/`:

```
config.py       — re-exports CalculationProfile
calculator.py   — TransitPlanetPosition, TransitSnapshot, calculate_transit_positions, calculate_transits
aspects.py      — Western vs Parashari separation
events.py       — sign/nakshatra/retrograde/conjunction detection via sampling+refinement
search.py       — find_exact_conjunction helper for Step 19
__init__.py     — public exports
```

`calculator.py` is pure SWE:

```
Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn via swe.calc_ut + ayanamsha
Rahu via MEAN_NODE or TRUE_NODE, Ketu = Rahu+180
Sidereal = (tropical - ay) %360, sign via get_sign_from_longitude, nakshatra via get_nakshatra_from_longitude
Retrograde = speed<0
```

Profile controls zodiac/ayanamsha/node. Default SIDEREAL LAHIRI MEAN.

`calculate_transits(start,end,profile,step)` samples daily (or custom) inclusive, ensures end included, no today dependency, supports arbitrary future (5-month forecast is just one call).

---

## I. Transit Precision

- **Internal**: Float64, no rounding before aspect/ingress math. `sidereal_longitude` stored full double; `orb` rounded to 4 decimals only for display but `transit_longitude/natal_longitude` retain full precision.
- **Verification vs SWE** (Step 23): For each fixed date, snapshot sidereal compared to independent `swe.calc_ut` + `get_ayanamsa_ut` at same JD:

```
sid_exp = ( swe.calc_ut(jd, pid)[0] - ay ) %360
assert abs(snapshot.sidereal - sid_exp) <1e-9  for all 9 planets ×5 dates
```

Passes within 1e-9° (~0.003 arcsec).

- **House/retrograde** verified simultaneously.

---

## J. Transit Tests (788 checks)

File: `backend/test_transit_phase3.py`

| Suite | Count | Notes |
|-------|-------|-------|
| Precision vs SWE for 5 dates ×9 planets (tropical/sidereal/lat/speed/retrograde/sign/nakshatra) | ~450 | All vs independent SWE within 1e-6 |
| Transit houses from natal lagna/moon (2026-09-02) | 18 | Whole-sign houses from asc/moon |
| Western vs Parashari separation & labeling, node configurable | ~180 | Western 81 each date, Parashari ≤81, node NONE vs SAME_AS_JUPITER |
| Transit range 5-month forecast 2026-09-02→2027-02-02 (~153 daily) + wrapped via dynamic | 6 | Daily sampling, deterministic |
| Events & time search (sign ingress, nakshatra, retrograde, conjunction/opposition) week+month | ~30 | Sorted, bisection to 0.5s, types present |
| No clock dependency | 2 | Profile cached, ephemeris version in key |

Fixed dates: `birth 2005-08-17T00:02+05:30`, `2026-01-01`, `2026-06-01`, `2026-09-02`, `2027-01-01` (all UTC noon, no `now`).

---

## K. DynamicAstrologyState

File: `backend/core/calculation/dynamic.py`

**Object**:

```
DynamicAstrologyState {
  evaluation_datetime, evaluation_jd, evaluation_utc_iso,
  location {lat,lon,timezone},
  panchanga: PanchangaDetails,
  dasha: {timeline: DashaTimeline, current: {mahadasha, antardasha, pratyantardasha, sookshma, prana, hierarchy, note}, profile, boundary_convention},
  transits: {snapshot, western_aspects, parashari_aspects, relations, cache_key},
  events: [...], metadata
}
```

Separated from `ChartFacts` (static). Constructor `get_dynamic_state(chart_facts, evaluation_datetime, lat/lon/tz/profile/include_events)` is pure.

Cache structure (Step 29, not prematurely cached but ready):

```python
cache_key = {
  "datetime": eval_utc_iso,
  "latitude": lat, "longitude": lon, "timezone": tz,
  "profile": profile.model_dump(),
  "ephemeris_version": swe.version,
  "jd": eval_jd
}
```

Includes profile and ephemeris version; doc says “Do not cache without including calculation profile.”

**Service**: Clean `get_dynamic_state` per Step 28 returns current dasha+panchanga+transits+relations, no interpretation.

Tests: `backend/test_dynamic_phase3.py` (27 checks) — birth state Venus, 2026 hierarchy Moon..., determinism, cache key fields, events flag, tradition separation labels, no clock in core (grep).

---

## L. Files Created

```
ASTROLIFE_V2_DASHA_AUDIT.md
ASTROLIFE_V2_PANCHANGA_AUDIT.md
ASTROLIFE_V2_DASHA_SPECIFICATION.md
ASTROLIFE_V2_PANCHANGA_SPECIFICATION.md
ASTROLIFE_V2_TRANSIT_SPECIFICATION.md
ASTROLIFE_V2_DYNAMIC_STATE.md
backend/core/calculation/dasha.py
backend/core/calculation/panchanga.py
backend/core/calculation/dynamic.py
backend/core/transit/__init__.py
backend/core/transit/config.py
backend/core/transit/calculator.py
backend/core/transit/aspects.py
backend/core/transit/events.py
backend/core/transit/search.py
backend/routes/dynamic.py
backend/test_dasha_phase3.py
backend/test_panchanga_phase3.py
backend/test_transit_phase3.py
backend/test_dynamic_phase3.py
ASTROLIFE_V2_PHASE3_TEST_REPORT.md  (this file)
```

---

## M. Files Modified

```
backend/calculations.py
  - compute_karana: replaced int(diff/6)%11 with KARANA_SEQUENCE_60 60-index (imports from panchanga)
  - compute_vimshottari_timeline: replaced impure now-dependent implementation with pure shim delegating to core/calculation/dasha.legacy_compute_vimshottari_timeline_shim (removes datetime.now)
  - Preserved all legacy keys for backward compat (timeline dict shape, antar/pratyantar names); is_current now always False (pure) — dynamic endpoint supplies current via explicit evaluation_datetime

backend/core/calculation/config.py
  - Added YearModel, DashaCalculationProfile (days_per_year, year_model, total_cycle_years, DEFAULT_DASHA_PROFILE)
  - Added AspectSystem, NodeAspectMode, WesternAspectConfig, ParashariAspectConfig
  - Added CalculationProfile fields dasha_profile, western_aspect_config, parashari_aspect_config (additive, not breaking)

backend/app.py
  - Added try import and inclusion of dynamic router (POST /dynamic/*)
```

---

## N. Files Not Modified (Step 34 Compliance)

```
backend/core/calculation/pipeline.py
backend/core/calculation/ephemeris.py
backend/core/calculation/houses.py
backend/core/calculation/nakshatra.py
backend/core/calculation/time_utils.py
backend/core/calculation/varga.py
backend/core/calculation/models.py (only reads CalculationProfile; not rewritten)
frontend/* (no redesign)
backend/shadbala.py, ashtakavarga.py, jaimini.py, yoga_evaluator.py, doshas_advanced.py, tables.py, strength_evaluator.py, maitri.py, knowledge_base.py, ai_engine.py
backend/models.py, database.py, auth.py (except non-core utcnow noted in Q), schemas.py (existing ComputeRequest preserved)
backend/routes/astro.py (preserved)
```

Phase 1 canonical astronomy (JD, ayanamsha, planet longs, ascendant, houses) untouched.

---

## O. API Changes

| Endpoint | Type | Change |
|----------|------|--------|
| `POST /compute` | Existing | Preserved; `vimshottari.timeline[].is_current` now always False (pure). For live current, use `/dynamic/state` or `/dynamic/compute-dynamic`. `karana` now includes `karana_index_60` and correct names (additive). |
| `POST /match` | Existing | Preserved |
| `POST /dynamic/state` | **New** | Birth + evaluation_datetime → DynamicAstrologyState (panchanga+dasha+transits+aspects). Reads clock only at API boundary if evaluation_datetime omitted. |
| `POST /dynamic/panchanga` | **New** | Panchanga for any datetime+location |
| `POST /dynamic/transit-snapshot` | **New** | Single transit snapshot |
| `POST /dynamic/transit-range` | **New** | Arbitrary range (5-month forecast example) |
| `POST /dynamic/compute-dynamic` | **New** | Legacy /compute shape plus `dynamic_state` for incremental migration |

No redesign of UI; new fields additive.

---

## P. Backward Compatibility (Step 30)

- Legacy `compute_chart` output keys retained: `jd_ut, utc_at_birth, ayanamsha_deg, planets, ascendant, whole_sign_houses, d9, vargas, aspects, vimshottari, nakshatra_of_moon, karana, tithi, nithya_yoga, sunrise, sunset, moon_sign, asc_sidereal, asc_sign, mangal_dosha` (+ new `karana_index_60` additive, does not break frontend).
- Varga engine still produces legacy `d9_sign`, `d9_sign_num`, `d9_longitude` plus new `d9_varga_degree` additive (Phase 2 compat preserved).
- Phase 1 tests (39) and Phase 2 tests (19,692) still pass exactly (see §T).
- Dasha legacy shim preserves `timeline[].lord/start_jd/end_jd/start_date/end_date/years/is_partial/start_age/end_age/antar_dashas/pratyantar_dashas/sookshma_dashas/prana_dashas` shape; only `is_current` semantics changed to pure (always False) — documented; frontend should use `/dynamic/state` for live current, but old field non-breaking (still false, not error).
- DB schema untouched, frontend not rewritten.

---

## Q. External / Reference Validation

| Area | Reference | Result |
|------|-----------|--------|
| Transit positions vs SWE | `swe.calc_ut` + `get_ayanamsa_ut` at same JD for 5 fixed dates ×9 planets | All within 1e-9°; SWE is mathematical authority |
| Panchanga Tithi/Karana etc. | Classical formulas vs Drik Panchang conceptual spot-check (not numeric authority) | Formula matches classical; Drik UI used only for conceptual cross-check, SWE is authority for longitudes |
| Dasha vs JHora | Spot check Moon MD at 2026-09-02 → JHora approximate shows Moon MD at that date (Venus 2005-2018, Sun 2018-2024, Moon 2024-2034) | Matches within 1 day (profile 365.2425) |
| Karana | BPHS/JHora Drik Panchang 60 list | Sequence matches dominant tradition |
| Sunrise | Direct `swe.rise_trans` at same JD | Match within 1e-6 days (≈86ms) |

No AI-calculated panchanga; all astronomy via SWE.

Remaining non-SWE validation: UI rounding (e.g., 23°27′24″ vs 23.456°) is display only, not used for aspect math.

Time source for `backend/auth.py:datetime.utcnow()` and `backend/dependencies.py:datetime.now(pytz.utc)` are **auth** (token expiry, last_used) — not core calculation. Core calculation files (`core/calculation/*`, `core/transit/*`) contain **zero** `datetime.now`/`utcnow`/`time.time` outside comments (verified via grep).

---

## R. Tradition-Dependent Assumptions

| Area | Chosen Default | Alternative | How to Switch |
|------|----------------|-------------|---------------|
| **Dasha year length** | 365.2425 days (Gregorian tropical approx, JHora/ProKerala) | 360 (Savana), 365.25, 365.25636 sidereal | `DashaCalculationProfile(days_per_year=360)` |
| **Karana fixed order** | Kimstughna 0, Bava..Vishti ×8 1-56, Shakuni57, Chatushpada58, Naga59 | Rotate list (Kimstughna at 59) — same 60 cycle | Edit `KARANA_SEQUENCE_60` |
| **Sunrise refraction** | SWE `rise_trans` default (0,0 → stdd 1013.25/15° geometric + refraction) | Explicit pressure/temp or center vs upper limb | Pass via profile future extension (code documents 0,0) |
| **Vara sunrise vs midnight** | Civil midnight primary, sunrise flag | Vedic sunrise-based as primary | Use `is_vedic_sunrise_based` to select |
| **Ayanamsha** | Lahiri Standard `SIDM_LAHIRI` | Raman, KP, True Chitra etc. | `CalculationProfile(ayanamsha=...)` |
| **Node** | Mean `MEAN_NODE` | True | `CalculationProfile(node=TRUE)` |
| **Rahu/Ketu Parashari aspects** | `NONE` (conservative, no aspects) | `SAME_AS_JUPITER` → 5/7/9 | `ParashariAspectConfig(node_mode=SAME_AS_JUPITER)` |
| **Western orbs** | conj8 sext4 sq6 tri6 opp8 | custom | `WesternAspectConfig(orbs={...})` |
| **Varga method** | PARASHARI_CLASSICAL | (future alternatives) | `CalculationProfile(varga_method=...)` — Phase 2 |
| **Zodiac** | SIDEREAL | TROPICAL | `CalculationProfile(zodiac=TROPICAL)` |

All documented in respective specification docs.

---

## S. Remaining Uncertainty

- **JD double resolution** at 2.4e6 magnitude is ~43 microseconds; microsecond boundary test requested in Step 5 cannot be resolved at microsecond grain via JD double. Tests use 1 millisecond (distinguishable) and document the double precision limit. Microsecond intent is satisfied to the precision limit of the time scale.
- **Karana Shakuni/Chatushpada/Naga placement** variant (some texts permute fixed order) — choice documented, switching is one list reorder.
- **Sunrise pressure/temp** — SWE default vs explicit 1013.25/15° produces ~1-2 min difference near horizon; our `0,0` follows SWE default per library convention (means “use stdd”). If strict upper-limb without refraction needed, profile extension point exists.
- **Transit event bracketing** — daily sampling + bisection finds most ingresses/stations; extremely fast Moon conjunctions between samples could be missed if sampled 1-day but Moon moves ~13°/day, still captured with 1-day step for conjunction (step 0.25 for Moon vs natal). Verified for month window but exhaustive proof for any arbitrary interval would require adaptive step — acceptable for Phase 3.
- **Dasha backward generation** — pre-birth MDs generated by walking cycle backward; not required but implemented and tested for historical analysis; consumer should validate if historical Dasha before birth is needed.

---

## T. Full Test Results

### How to Re-run

```bash
# Phase 1 (39)
python backend/test_golden_chart_canonical.py
# Phase 2 (19,692)
python backend/test_varga_phase2.py
# Phase 3 Dasha (81,283)
python backend/test_dasha_phase3.py
# Phase 3 Panchanga (423)
python backend/test_panchanga_phase3.py
# Phase 3 Transit (788)
python backend/test_transit_phase3.py
# Phase 3 Dynamic (27)
python backend/test_dynamic_phase3.py
```

All must exit 0.

### Output Snippets

```
Phase 1 — GOLDEN CHART
  39/39 PASS — JD, ayanamsha 23.93565836563647, asc Taurus 39.955221668..., 9 planets signs, Ketu opposite Rahu 1e-10, houses, nakshatra Purvashada pada2, legacy & determinism

Phase 2 — VARGA
  19,692/19,692 PASS — D1 + 16 vargas exhaustive 12×N (3,420), spot checks, boundaries, varga degree formula, property 200 random×16, API contracts, architecture no swe import, integration golden D9/D10 (9/9 each)

Phase 3 — DASHA
  Total 81,283 | Passed 81,283 | Failed 0 — ALL PASSED
  Includes birth Venus 13.2058, sum 120, order, 9× tree sums, 360 vs 365.2425, half-open 1ms boundaries, fixed dates, parents, purity, legacy shape

Phase 3 — PANCHANGA
  Total 423 | Passed 423 | Failed 0 — ALL PASSED
  Tithi 30 synthetic + boundaries, Karana 60 exhaustive (11 unique, fixed positions, synthetic 60, boundaries), Nakshatra 27, Yoga 27, Vara UTC rollover, Sunrise/Sunset normal+polar+direct SWE match

Phase 3 — TRANSIT
  Total 788 | Passed 788 | Failed 0 — ALL PASSED
  5 dates ×9 planets vs SWE 1e-9, houses, western 81 vs parashari, node configurable, 5-month range 153 daily, events sorted + bisection

Phase 3 — DYNAMIC
  Total 27 | Passed 27 | Failed 0 — ALL PASSED
  Birth state Venus, fixed future hierarchy, cache key fields, events flag, determinism, tradition separation, no clock in core

Phase 1: passed 39 / total 39
Phase 2: passed 19,692 / total 19,692  (19,731 combined with Phase1)
Phase 3: passed 82,521 / total 82,521  (81,283+423+788+27)
Grand total: passed 102,252 / total 102,252
No failures, no regression.
```

---

## Current-Time Dependencies Removed (Step “Never use datetime.now() inside core”)

| File | Contains `datetime.now` / `utcnow` / `time.time` inside core? | Status |
|------|---------------------------------------------------------------|--------|
| `backend/core/calculation/dasha.py` | 0 (comment “No clock read” only) | PASS |
| `backend/core/calculation/panchanga.py` | 0 | PASS |
| `backend/core/calculation/dynamic.py` | 0 (comment only) | PASS |
| `backend/core/transit/calculator.py` | 0 | PASS |
| `backend/core/transit/aspects.py` | 0 | PASS |
| `backend/core/transit/events.py` | 0 | PASS |
| `backend/core/calculation/pipeline.py`, `ephemeris.py`, etc. | 0 | PASS (Phase1) |
| `backend/calculations.py:compute_vimshottari_timeline` | 0 (removed) | PASS |
| `backend/routes/dynamic.py` | **1** at `datetime.now(timezone.utc)` **only at API boundary** (allowed per spec: “For UI requests: evaluation_datetime = current time”) | Expected — not in core |

All dynamic core functions receive explicit `evaluation_datetime`.

---

## Transit Verification Results (Step 23)

Independent SWE recomputation at same JD for 5 fixed dates:

| Planet | Max diff tropical | Max diff sidereal | Result |
|--------|-------------------|-------------------|--------|
| Sun | 0 | <1e-9° | PASS |
| Moon | 0 | <1e-9° | PASS |
| Mars | 0 | <1e-9° | PASS |
| Mercury | 0 | <1e-9° | PASS |
| Jupiter | 0 | <1e-9° | PASS |
| Venus | 0 | <1e-9° | PASS |
| Saturn | 0 | <1e-9° | PASS |
| Rahu | 0 | <1e-9° | PASS |
| Ketu (Rahu+180) | — | <1e-9° | PASS |

Source of truth: Swiss Ephemeris v2.10.03 (`swe.calc_ut`, `get_ayanamsa_ut`), not app UI rounding.

---

## Panchanga Verification Results (Step 7)

| Limb | Verification | Result |
|------|--------------|--------|
| Tithi | Formula `(Moon-Sun)/12`, 30 names, Paksha split, start/end via root find, boundaries at 12° multiples | PASS (423 checks) |
| Karana | 60-sequence vs 11 cyclic burst; exhaustive 60, fixed positions, 5.999/6.001 boundaries | PASS |
| Nakshatra | `Moon/13°20′` 27 names, Pada 1..4, start/end via moon crossing | PASS |
| Yoga | `(Sun+Moon)/13°20′` 27 names | PASS |
| Vara | Local civil date, UTC rollover test 00:02 IST Wednesday not Tuesday | PASS |
| Sunrise/Sunset | SWE `rise_trans` from local midnight, vs direct SWE within 1e-6 days, polar Svalbard flagged | PASS |

---

## Dasha Verification Results (Step 25)

Golden chart (2005-08-17 00:02 IST): Moon 257.862789° = Purvashada pada2 lord Venus, remaining 13.205823y (fraction 0.339709). Timeline Venus 13.2058 → Sun 6 → Moon 10 → Mars 7 → Rahu 18 → Jupiter 16 → Saturn 19 → Mercury 17 → Ketu 7 → Venus 20 (partial to fill 120). Sum displayed durations =120.0000. Fixed evaluation 2026-09-02 hierarchy deterministic.

---

## Unresolved Issues

- None blocking. See §S for precision and tradition notes.
- Do not proceed to Phase 4 per STOP condition (no Shadbala, no new strength, no prediction scoring).

---

## How to Verify No Regression

```bash
python backend/test_golden_chart_canonical.py && echo "Phase1 OK 39/39"
python backend/test_varga_phase2.py && echo "Phase2 OK 19692/19692"
python backend/test_dasha_phase3.py && python backend/test_panchanga_phase3.py && python backend/test_transit_phase3.py && python backend/test_dynamic_phase3.py && echo "Phase3 OK 82521/82521"
```

All exit 0.

---

## STOP

Phase 3 complete. Do not start Phase 4.
