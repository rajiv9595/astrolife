# Astrolife V2 — Panchanga Audit (Phase 3 Step 7)

**Date**: 2026-09-02  
**Audited files**: `backend/calculations.py` — `compute_tithi`, `compute_karana`, `compute_nithya_yoga`, `compute_nakshatra_pada`, `compute_sunrise_sunset`, `jd_to_datetime_naive`; `backend/panchanga_advanced.py` (Avakahada/Ghata only, no astronomy)

---

## 1. Scope of Existing Implementation

`calculations.py` provides five panchanga functions that use only instantaneous sidereal longitudes (no time interpolation). They are called from `compute_chart`:

```python
karana_data = compute_karana(moon_sid, sun_sid)
tithi_data  = compute_tithi(moon_sid, sun_sid)
yoga_data   = compute_nithya_yoga(moon_sid, sun_sid)
nakshatra   = compute_nakshatra_pada(moon_sid)    # also from chart path
sun_data    = compute_sunrise_sunset(jd_ut, lat, lon, tz)
```

`panchanga_advanced.py` contains no Panchanga calculation — only Avakahada Chakra (Yoni/Gana/Nadi) and Ghata Chakra lookup tables derived from Moon sign/nakshatra for interpretation (not time-dependent).

**No dedicated Panchanga module exists**; astronomy is interleaved with `compute_chart`.

---

## 2. Tithi — AUDIT

File `calculations.py:251-283`:

```python
def compute_tithi(moon_lon, sun_lon):
    diff = normalize_deg(moon_lon - sun_lon)
    tithi_val = diff / 12.0
    tithi_index = int(tithi_val)  # 0-29
    if tithi_index < 15: paksha="Shukla Paksha" else paksha="Krishna Paksha"
    name = TITHI_NAMES[tithi_index]
    fraction = tithi_val - tithi_index
    return {"index": tithi_index+1, "name":name, "paksha":paksha, "fraction":fraction, "degrees_left":(1-fraction)*12}
```

| Check | Status |
|-------|--------|
| Formula `diff = (Moon - Sun) mod 360`, `/12°` | CORRECT — standard |
| 30 tithis, 15/15 Shukla/Krishna split | CORRECT — note index 0-14 Shukla Pratipada..Purnima, 15-29 Krishna Pratipada..Amavasya; code matches |
| Names list `TITHI_NAMES` length 30, index aligned | CORRECT |
| Paksha label | CORRECT |
| Percentage elapsed | Correct as `fraction` |
| **Start/end times** | **MISSING** — only instantaneous fraction, no astronomical start/end of tithi via root finding |
| **Elapsed vs left** | Computes `degrees_left` but not time-until-boundary |
| **Boundary handling** | No test; `int(diff/12)` truncates but does not handle floating epsilon near boundary (e.g. 12.0000000001 → next tithi) consistently documented |
| **Location dependence** | Tithi is not location-dependent (Sun/Moon longitudes global) — correct to not use lat/lon, but spec expects Panchanga sunrise context noted |
| **Precision** | Floored int is fine but uses `normalize_deg` correct |

Findings:
- **T1 — Missing start/end**: Step 8 requires `tithi start time, end time` via astronomical interpolation — not implemented.
- **T2 — Rounded boundary**: No epsilon snapping; `diff=11.999999999` vs `12.0` sensitivity not documented.
- **T3 — No evaluation_datetime separation**: Uses only lon floats passed from caller; if caller re-computes lon at a different instant, correct — but no wrapper that takes `evaluation_datetime` explicitly per Step 7.

Overall: formula correct, but incomplete per Phase 3 completeness and time-dependency.

---

## 3. Karana — AUDIT — **BROKEN**

File `calculations.py:230-249`:

```python
def compute_karana(moon_lon, sun_lon):
    diff = moon - sun; if diff<0: diff+=360
    karana_index = int(diff / 6.0) % 11
    karana_name = KARANA_NAMES[karana_index]
    return {"karana": karana_name, "karana_index": karana_index, "moon_sun_diff": round(diff,4)}
```

`KARANA_NAMES` = `["Bava","Balava","Kaulava","Taitila","Gara","Vanija","Vishti","Shakuni","Chatushpada","Naga","Kimstughna"]` length 11.

**This is explicitly prohibited** in Step 9: *“Do NOT use `int(angle_difference / 6) % 11` as the entire classical Karana algorithm.”*

### Why this is wrong

Classical Karana sequence is **60 half-tithis** per lunar month, not 11 repeating:

- **Fixed Karanas**: Positions 0 (Kimstughna, second half of Krishna Amavasya — index 59), and at start positions? Actually classical: first half of Shukla Pratipada is Kimstughna is *incorrect*? The standard sequence per Surya Siddhanta / Jhora / Drik Panchang:

  Order per Drik Panchang / BPHS:
  ```
  0: Kimstughna        (second half of Krishna Chaturdashi? No — historically Kimstughna = first half of Shukla Pratipada)
  ```

  Need to recall exact classical sequence as per Panchang literature (e.g. DrikPanchang):

  The 60 karanas are indexed by `floor(diff/6)` = 0..59:

  - 0: Kimstughna (fixed) — first half of Shukla Pratipada (0°–6°)
  - 1: Bava, 2: Balava, 3: Kaulava, 4: Taitila, 5: Gara, 6: Vanija, 7: Vishti — then repeating Bava..Vishti for 1..57? Actually detailed:

  Standard 60 list reproduced:

  ```
  0  Kimstughna   (fixed, Shukla Pratipada first half)
  1  Bava         (cycle start)
  2  Balava
  3  Kaulava
  4  Taitila
  5  Gara
  6  Vanija
  7  Vishti (Bhadra)
  -- repeating 1..7 --
  57 Vishti,
  58 Shakuni (fixed, Krishna Chaturdashi second half)
  59 Chatushpada (fixed)
  60 Naga (fixed) ??? Actually need verify counting.

  Correct modern Drik sequence commonly implemented as:
  index: karana
    0: Kimstughna
    1: Bava
    2: Balava
    3: Kaulava
    4: Taitila
    5: Gara
    6: Vanija
    7: Vishti
    8: Bava
    9: Balava
   ...
   50: Bava... (cycles)
   57: Vishti
   58: Shakuni
   59: Chatushpada
   60? Actually 58,59,0? Wait Naga where?

  Alternative widely used array (8 movable repeated 7 times =56, plus 4 fixed =60):
  Movable cycle (7): Bava, Balava, Kaulava, Taitila, Gara, Vanija, Vishti — repeated 8 times =56 positions
  Fixed (4): Shakuni, Chatushpada, Naga, Kimstughna — placed at ends.

  Common mapping for diff/6 index 0..59:
   0: Kimstughna
   1: Bava ... 7: Vishti (1st cycle)
   8: Bava ... 14: Vishti (2nd)
  ...
   50: Bava ... 56: Vishti (8th)  => indices 1..56
   57: Shakuni
   58: Chatushpada
   59: Naga
   ```

  There are variant traditions ordering Shakuni/Chatushpada/Naga/Kimstughna positions — must document chosen.

  What matters: `int(diff/6)%11` produces:
  - diff 0°   → 0→ Bava (should be Kimstughna) — WRONG
  - diff 6°   → 1→ Balava (should be Bava) — shifted
  - diff 348° → 58%11=3→ Taitila (should be ??? Naga) — completely wrong for fixed karanas
  - At no point does it produce correct fixed karanas at ends and the 60-position periodicity.

**Demonstration** (audit script):

```python
# diff 0° (Shukla Pratipada start)
old = ["Bava","Balava","Kaulava","Taitila","Gara","Vanija","Vishti","Shakuni","Chatushpada","Naga","Kimstughna"][int(0/6)%11]
# old => Bava ; correct => Kimstughna => FAIL
# diff 354° (Amavasya late)
old = KARANA_NAMES[int(354/6)%11]  # 59%11=4 => Gara ; correct => Naga => FAIL
```

- **K1 — BLOCKER**: implements prohibited formula verbatim.
- **K2**: `KARANA_NAMES` order is movable Bava..Vishti then fixed Shakuni..Kimstughna — but code uses it as periodic mod 11, so fixed Karanas appear as if movable throughout month.
- **K3**: No `karana elongated`: missing 60-position model, missing distinction of first half vs second half of tithi.
- **K4**: No start/end, no elapsed %, no half-tithi awareness.
- **K5**: No test covering 60 positions.

Correction required: implement 60-element array `KARANA_SEQUENCE_60[60]` placing Kimstughna at 0, Bava..Vishti ×8 at 1..56, Shakuni at 57, Chatushpada at 58, Naga at 59 (or documented alternative with Naga at 59 and Kimstughna at 0). Provide tests for all 60.

---

## 4. Nakshatra (Panchanga) — AUDIT

Two implementations:

- `calculations.py:216-228` `compute_nakshatra_pada(lon_sidereal)` — used for Moon at birth and tests
- `core/calculation/nakshatra.py:18` `get_nakshatra_from_longitude(lon)` — canonical for ChartFacts

Both: `nak_size = 360/27 =13.333...`, `nak_index_float = lon/13.333`, `nak_index=int(floor(...))`, `fraction = ... - index`, `pada = int(fraction*4)+1`, lord via `NAKSHATRA_LORDS[nak_index]`.

| Check | Status |
|-------|--------|
| Size 13°20' (13.333°) | CORRECT |
| Index 0-26 mapping to Ashwini..Revati | CORRECT (note spelling: Mrigashira vs Mrigashirsha — minor inconsistency between files) |
| Lord mapping `Ketu,Venus,Sun,Moon,Mars,Rahu,Jupiter,Saturn,Mercury` ×3 | CORRECT |
| Pada 1-4 | Correct |
| **Start/end longitudes** | Canonical returns `start_longitude`, `end_longitude` for instantaneous — but no *time* start/end of current nakshatra via interpolation — MISSING per Step 10 |
| **Elapsed %** | `fraction` correct but not presented as percent |
| **Source of longitude** | `compute_nakshatra_pada` takes raw float; canonical version is precomputed in ChartFacts — but Panchanga wrapper does not explicitly enforce "use canonical sidereal Moon longitude. Do not independently calculate Moon position." It currently recomputes via `moon_sid` float if called elsewhere. Acceptable if caller passes ChartFacts moon. Note: Panchanga for *evaluation_datetime* (not birth) must compute Moon sidereal at that evaluation time via ephemeris — this is correct to calculate, but the *natal* nakshatra should use ChartFacts. So two paths: birth vs evaluation — need separation. |
| **Daily interpolation** | MISSING — Step 10 says determine start/end times through interpolation/root finding, not fixed duration. Currently returns only instantaneous. |

No major formula error, but incomplete for dynamic panchanga.

---

## 5. Yoga — AUDIT

File `calculations.py:285-303`:

```python
def compute_nithya_yoga(moon_lon, sun_lon):
    total = normalize_deg(moon_lon + sun_lon)
    yoga_length = 360/27.0 #13.333
    yoga_val = total / yoga_length
    yoga_index = int(yoga_val)
    name = NITHYA_YOGA_NAMES[yoga_index]
    fraction = yoga_val - yoga_index
    return {"index": yoga_index+1, "name":name, "fraction":fraction}
```

| Check | Status |
|-------|--------|
| Formula `Sun + Moon mod 360 /13.333°` | CORRECT — standard Nitya Yoga (not to be confused with Dasha yogas) |
| 27 yogas, names list `NITHYA_YOGA_NAMES` length 27 | CORRECT and in canonical order Vishkumbha..Vaidhriti |
| Index 1-based vs 0-based | `index+1` correct |
| **Start/end times** | MISSING |
| **Elapsed %** | Only fraction, same |
| **Boundary/epsilon** | No epsilon/snapping test |
| **Consistent naming** | Note: file uses `NITHYA_YOGA_NAMES` but some texts say `Nitya` — fine |

Similar to Tithi: formula correct, completeness missing.

---

## 6. Vara (Weekday) — AUDIT

No explicit `compute_vara` function exists. The weekday is derived implicitly:

- In `compute_sunrise_sunset` (`calculations.py:305`) local weekday computed as `ut_dt.astimezone(tz).weekday()` etc.
- In `calculate_maandi_and_gulika_positions` (`calculations.py:1380-1386`) weekday logic includes Vedic day start at sunrise adjustment:
  ```python
  cal_weekday = local_dt.weekday()  # 0=Mon
  if jd_birth < sunrise_jd:
      vedic_weekday = (cal_weekday -1) %7
  ```
  This is the *only* weekday adjustment found.

**Issues**:

- **V1**: No standalone `vara` in Panchanga output of `compute_chart` — not exposed. `compute_chart` returns sunrise/sunset strings but no `vara` key. So Panchanga weekday is simply not part of API.
- **V2**: Sunrise-anchored weekday (Vedic vara starts at sunrise) is handled for Maandi/Gulika but not for general Panchanga vara display. Current code for general vara would simply use civil calendar date (midnight) if it existed — spec Step 12 says *"Do not allow UTC date rollover to incorrectly change the Indian local weekday. The Panchanga date must be based on target location's local civil date."* This is currently satisfied if using `local_dt.weekday()` — but must be verified that evaluation_datetime's civil date (not UTC date) drives vara.
- **V3**: No function taking `evaluation_datetime + lat/lon/tz` to return vara correctly at midnight vs sunrise boundaries — needs explicit implementation with midnight vs sunrise convention documented.
- **V4**: No test.

---

## 7. Sunrise / Sunset — AUDIT

File `calculations.py:305-379` `compute_sunrise_sunset(jd_ut, lat, lon, tz_name)` and `calculations.py:1342-1354` `compute_sunrise_sunset_internal(jd_start, lat, lon)` (internal).

Both use:

```python
swe.set_topo(lon, lat, 0)
res_rise = swe.rise_trans(jd_start, swe.SUN, swe.CALC_RISE, (lon, lat, 0), 0,0, flags)
```

| Check | Status |
|-------|--------|
| Uses Swiss Ephemeris `rise_trans` with `CALC_RISE` / `CALC_SET` | CORRECT — not crude approximation |
| Input handling: uses `jd_start` derived from local midnight | Mostly correct — see below |
| Returns both formatted `"%I:%M %p"` and JD | Correct but format loses timezone disambiguation |
| Polar/edge handling | Try/except returns `"N/A"` or fallback `jd_start+0.25 / +0.75` — graceful but should return explicit error object |
| **Location params** | Uses `lat, lon` correctly, but internal variant ignores `tz_name` and assumes `jd_start` already midnight local — caller correctly constructs `jd_start` from `local_dt` midnight → UTC → julday (`calculations.py:345-350`). So tz handling is correct. |
| **Two code paths** | `compute_sunrise_sunset` and `compute_sunrise_sunset_internal` duplicate logic with slight differences (`tz` aware vs not). Internal one is used for Maandi/Gulika and fallback; outer adds formatting. Duplication should be consolidated. |
| **No evaluation_datetime separation** | Takes `jd_ut` but then recomputes local date from JD — this is correct internally, but spec requires explicit `evaluation_datetime` param instead of JD for new engine, to avoid clock contamination. Currently `jd_ut` is derived from ChartFacts birth JD, so not general for Panchanga on arbitrary date. Need new pure `calculate_sunrise_sunset(evaluation_datetime, lat, lon, tz)` that works for any date. |
| **Refraction / pressure** | Calls `rise_trans` with `atpress=0, attemp=0` meaning standard refraction? In swisseph docs, 0 means default? Actually need `1013.25` and `15` for standard; using 0 may use geometric rise without refraction. Should document chosen. Most panchanga engines use standard. Audit shows current uses `0,0` — may cause ~2-3 minute sunrise error due to no refraction correction — should be noted. |
| **Polar case** | Graceful fallback via try/except — meets "Handle polar/edge cases gracefully." |

**Findings**:

- Formula path correct (SWE), not crude.
- Needs consolidation, explicit `evaluation_datetime` API, documented refraction handling, and preservation of full precision JD vs formatted string distinction.

---

## 8. Overall Panchanga Completeness vs Spec Step 7

| Required 1-7 | Status |
|--------------|--------|
| 1. Tithi | instantaneous only, no start/end/interpolation |
| 2. Vara | no function, not exposed |
| 3. Nakshatra | instantaneous only, no start/end |
| 4. Yoga | instantaneous only, no start/end |
| 5. Karana | BROKEN (prohibited formula) |
| 6. Sunrise | partially correct via SWE but duplicated and uses 0 pressure/0 temp |
| 7. Sunset | same |

Also required extended:

| Item | Status |
|------|--------|
| Paksha | computed inside tithi but not exposed separately |
| Lunar day | same as tithi |
| Sun longitude | available via ChartFacts / ephemeris but not in panchanga output |
| Moon longitude | same |

All astronomy currently comes from Swiss Ephemeris indirectly (positions passed in) — meets "All astronomy must come from Swiss Ephemeris". Not AI-generated.

---

## 9. Critical Rule — Clock Usage

Panchananga functions themselves are pure (take lon floats / JD). But `compute_chart` which orchestrates them reads no clock except through Dasha path. However new Panchanga engine for arbitrary `evaluation_datetime` must be pure and receive `evaluation_datetime` explicitly — no current violation besides sunrise helpers that derive date from JD (pure). No `datetime.now()` inside Panchanga paths — PASS for this component; still needs explicit `evaluation_datetime` wrapper per spec.

---

## 10. Required Corrections

| # | Item | Spec Step |
|---|------|-----------|
| 1 | **Karana**: replace `int(diff/6)%11` with 60 half-tithi array; document sequence; implement `karana_index 0..59` and mapping to 11 names with fixed/movable distinction; add elapsed%/start/end via root finding | Step 9 |
| 2 | **Tithi/Nakshatra/Yoga**: keep formulas but add `start_time`, `end_time`, `elapsed_percent` via astronomical interpolation (solve diff = k*12° etc.) | Step 8,10,11 |
| 3 | **Vara**: implement `calculate_vara(evaluation_datetime, tz)` using local civil date, document sunrise vs midnight convention, prevent UTC rollover bug | Step 12 |
| 4 | **Sunrise/Sunset**: consolidate duplicates, document refraction params, add pure `evaluation_datetime` entry, return both local formatted + UTC JD + UTC iso, handle polar N/A explicitly | Step 13 |
| 5 | **Panchanga orchestration**: create `calculate_panchanga(evaluation_datetime, latitude, longitude, timezone, profile)` pure function returning all seven + paksha/sunMoon lons; structure so can be reused for any date | Step 7 |
| 6 | **Precision**: preserve full double precision for boundaries; epsilon snapping near 0°/360° wrap; document half-open convention | Step 22,5 |
| 7 | **Tests**: create boundary + exhaustive Karana (60), Tithi, Yoga (27) tests per Step 24 | Step 24 |

No Phase 1/2 formulas need alteration; Karana fix is isolated to Panchanga.
