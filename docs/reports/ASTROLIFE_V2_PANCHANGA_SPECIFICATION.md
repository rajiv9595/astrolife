# Astrolife V2 — Panchanga Specification (Phase 3)

**Version**: 1.0  
**Date**: 2026-09-02  
**Engine**: `backend/core/calculation/panchanga.py`  
**Implements**: Step 7,8,9,10,11,12,13,24

---

## 1. Five Limbs

| Limb | Sanskrit | Angular Definition | Division | Count |
|------|----------|--------------------|----------|-------|
| Vara | Vāra | Weekday from local civil date | 7 | 7 |
| Tithi | Tithī | `(Moon - Sun) mod 360 / 12°` | 12° | 30 |
| Nakshatra | Nakṣatra | `Moon sidereal / 13°20′` | 13°20′ (13.333°) | 27 |
| Yoga | Nitya-Yoga | `(Moon + Sun) mod 360 / 13°20′` | 13°20′ | 27 |
| Karana | Karaṇa | `Moon - Sun / 6°` half-tithi, **60-sequence** | 6° | 60 (11 unique) |
| + | Sunrise/Sunset | SWE `rise_trans` | — | daily |

Plus Paksha, Sun/Moon longitudes, Ayanamsha.

All longitudes are **sidereal** (Lahiri) per profile.

---

## 2. Formulas

### 2.1 Tithi

```
diff = (Moon_sid - Sun_sid) mod 360   # 0..360
tithi_val = diff / 12.0               # 0..30
index0  = floor(tithi_val + 1e-9)     # 0..29 (epsilon snap at boundary)
name    = TITHI_NAMES[index0]         # 30 names: Pratipada(0)..Amavasya(29)
paksha  = "Shukla Paksha" if index0<15 else "Krishna Paksha"
fraction = tithi_val - index0         # 0..1 elapsed within tithi
percent  = fraction*100
degrees_elapsed = fraction*12
degrees_left    = (1-fraction)*12
```

Names index: 0 Pratipada (Shukla), 14 Purnima, 15 Pratipada (Krishna), 29 Amavasya.

**Boundaries**: Tithi `k` spans angular interval `[k*12°, (k+1)*12°)`.  
**Start/end times**: found by solving `diff(jd) = boundary_angle` via bisection (see §7).

Output `TithiInfo`: `index 1..30`, `index0`, `name`, `paksha`, `fraction_elapsed`, `percent_elapsed`, `degrees_left`, `angular_distance=diff`, optionally `start_jd/end_jd` + `start_utc_iso/end_utc_iso`.

---

### 2.2 Karana — 60 Half-Tithi Sequence (Corrected)

**Classical rule**: 60 karanas per lunar month = 30 tithis × 2 half-tithis, each `6°` of Moon-Sun angular distance. Only 11 unique names, but 4 are *fixed* (Sthira) appearing only at cycle ends, 7 *movable* (Chara) repeating.

**Incorrect (prohibited)**:

```
int(diff/6) % 11   # WRONG — treats fixed karanas as movable everywhere
```

**Correct**:

First define ordered 60-element sequence (Drik Panchang / BPHS / JHora convention, documented):

```
index: karana
 0      Kimstughna   (fixed) — Shukla Pratipada first half
 1      Bava         \
 2      Balava        |
 3      Kaulava       |
 4      Taitila       | 8 repeats of Bava..Vishti (7 movable) covering indices 1..56
 5      Gara          |
 6      Vanija        |
 7      Vishti(Bhadra)|
 ... repeated ...
 57     Shakuni      (fixed) — Krishna Chaturdashi 2nd half / Amavasya etc.
 58     Chatushpada  (fixed)
 59     Naga         (fixed)
```

Construction:

```python
movable = ["Bava","Balava","Kaulava","Taitila","Gara","Vanija","Vishti"]
seq = ["Kimstughna"]
for _ in range(8): seq.extend(movable)  # 56
seq += ["Shakuni","Chatushpada","Naga"]  # 60
```

Lookup:

```
idx60 = floor(diff / 6 + 1e-9) % 60   # 0..59
name  = KARANA_SEQUENCE_60[idx60]
is_fixed = name in {"Kimstughna","Shakuni","Chatushpada","Naga"}
unique_index = KARANA_NAMES_11.index(name)  # 0..10 for legacy compat
fraction = (diff - idx60*6)/6
```

**Start/end**: Karana boundaries are `idx60*6°` and `(idx60+1)*6°` — same root finder as Tithi but with 6° step.

Output `KaranaInfo`: `index_60 0..59`, `name`, `unique_index 0..10`, `is_fixed/is_movable`, `half_tithi_fraction`, `angular_distance`, dates.

**Tradition variant**: Some texts place Kimstughna at 59 instead of 0, rotating sequence (equivalent under mod 60). Choice documented in code as `KARANA_SEQUENCE_60` comment; switching requires reordering list only.

---

### 2.3 Nakshatra (Panchanga)

```
lon = Moon_sid % 360
nak_size = 360/27 = 13.333...
nak_float = lon / nak_size
idx0 = floor(nak_float + 1e-9)  # 0..26
fraction = nak_float - idx0
name  = NAKSHATRA_NAMES[idx0]
lord  = NAKSHATRA_LORDS[idx0]  # Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury ×3
pada  = floor(fraction*4 +1e-9)+1  # 1..4
start_lon = idx0 * nak_size
end_lon   = start_lon + nak_size
degree_within = lon - start_lon  # 0..13.333
```

**Start/end times**: moon sidereal crossing `lon = start_lon` and `end_lon` — solved by `_bracket_and_find_moon_boundary` via SWE moon lon root find (Step 10). Not fixed duration (moon speed varies ~11-15°/day, duration 0.9-1.1 days).

Output `NakshatraInfo` includes `percent_elapsed`, `start_jd/end_jd` etc.

Uses canonical sidereal Moon — not independent calculation for *natal* nakshatra (birth chart reads `ChartFacts`). For panchanga at `evaluation_datetime`, moon lon is computed at that JD (correct to compute, as panchanga is time-dependent).

---

### 2.4 Yoga (Nitya)

```
total = (Sun_sid + Moon_sid) % 360
yoga_size = 360/27 = 13.333...
yoga_val = total / yoga_size
idx0 = floor(yoga_val + 1e-9) # 0..26
name = NITHYA_YOGA_NAMES[idx0]  # Vishkumbha(0)..Vaidhriti(26)
fraction = yoga_val - idx0
```

Boundaries `k*13.333°` on Sum. Root find via `_bracket_and_find_yoga_boundary`.

Output `YogaInfo`.

---

### 2.5 Vara (Weekday)

Derived from **local civil date** of evaluation moment (Step 12):

```
local_dt = evaluation_datetime.astimezone(tz)  # tz from target location
weekday_index = local_dt.weekday()  # 0=Mon ...6=Sun (ISO)
weekday_name  = ["Monday",...]
local_date    = local_dt.date().isoformat()
```

**UTC rollover bug prevented**: Uses local calendar date, not UTC date. E.g. birth 00:02 IST 2005-08-17 is 2005-08-16 18:32 UTC — UTC date would be 16th (Tuesday) but local civil is 17th Wednesday; code uses local.

**Vedic sunrise flag**: If before sunrise of that civil date, `is_vedic_sunrise_based=True` (day hasn't started in sunrise-based reckoning). Documented but civil vara is primary; sunrise-based variant noted for transparency.

Output `VaraInfo`.

---

### 2.6 Sunrise / Sunset

For local civil date containing `evaluation_datetime`:

```
midnight_local = local_dt.replace(0,0,0,0)
midnight_utc = midnight_local.astimezone(UTC)
jd_start = julday(midnight_utc)  # 00:00 local → JD
set_topo(lon, lat, 0)
geopos = (lon, lat, 0)
res_rise = swe.rise_trans(jd_start, SUN, CALC_RISE, geopos, 0,0, FLG_SWIEPH)
res_set  = swe.rise_trans(jd_start, SUN, CALC_SET,  geopos, 0,0, FLG_SWIEPH)
jd_rise = res_rise[1][0] if status 0 else None
jd_set  = res_set[1][0]  if status 0 else None
```

Note on refraction: called with `atpress=0, attemp=0` (SWE means default stdd refraction? Docs: 0 uses default 1013.25 mbar /15°C for refraction). This is documented in audit; most panchanga engines use standard refraction — we follow SWE default by passing 0 per library convention (means “use default”). Polar handling: if status !=0 or exception, `polar_case=True` and note set, `sunrise_jd=None`.

Returns both `jd`, `UTC iso`, `local iso`, `local formatted "%I:%M %p"`, plus `polar_case` flag.

Requires `latitude`, `longitude`, `timezone`, `evaluation date` — all explicit.

---

## 3. Inputs

```
calculate_panchanga(
    evaluation_datetime: datetime,  # explicit, aware or naive (assumed tz local)
    latitude: float,
    longitude: float,
    tz_name: str,   # IANA e.g. "Asia/Kolkata"
    profile: Optional[CalculationProfile] = None,  # zodiac, ayanamsha, node
) -> PanchangaDetails
```

Also individual helpers `compute_tithi_info(moon_lon, sun_lon, jd_ut, profile)` etc. for legacy path.

---

## 4. Outputs — PanchangaDetails

| Field | Type |
|-------|------|
| `evaluation_jd`, `evaluation_utc_iso`, `evaluation_local_iso` | eval moment JDs |
| `location` | `{latitude, longitude, timezone}` |
| `tithi` | `TithiInfo` |
| `karana` | `KaranaInfo` (index_60 + unique) |
| `nakshatra` | `NakshatraInfo` |
| `yoga` | `YogaInfo` |
| `vara` | `VaraInfo` |
| `sunrise_sunset` | `SunriseSunsetInfo` |
| `sun_sidereal`, `moon_sidereal`, `ayanamsha`, `ayanamsha_system` | raw astronomy |

All ISO use UTC `Z`.

---

## 5. Time Scales & Timezone Handling

- **Julian Day** UT-based via `swe.julday` and `swe.revjul` (Gregorian calendar).
- **Evaluation**: `evaluation_datetime` → JD(UT) via `tz → UTC → julday`.
- **Lons** at evaluation JD via `swe.calc_ut` tropical - ayanamsha = sidereal.
- **Vara**: civil date uses `pytz` local conversion — prevents UTC rollover error.
- **Sunrise**: computed for *civil date* containing evaluation, not JD's UTC date.

---

## 6. Precision

- **Internal**: Float64 doubles; JD comparison with half-open intervals as needed.
- **Boundaries**: solved to `tol_days = 0.5/86400` (~0.5 sec) via bisection. Internal JD full precision, display ISO rounded only for output.
- **Epsilon**: `int(floor(val+1e-9))` snap at exact `k*12°` etc. absorbs binary FP error (e.g. `diff=12.000000000001` → index 1 not 0 due to ~1e-12 representation).
- **Longitude**: normalized `%360` before division.

---

## 7. Boundary Handling & Root Finding

Rather than assuming fixed 24h duration, **interpolate**:

Algorithm per Step 19:

```
1. At jd_center = evaluation_jd, compute current limb index k (e.g. tithi k).
2. Target boundaries: start = k*unit, end = (k+1)*unit (mod 360).
3. Bracket: sample angles at jd_center ±2 days in 0.5-day steps, find interval [lo,hi] where target lies between lo_val and hi_val (handling 360 wrap).
4. Refine: bisection on monotonic unwrapped angle until |hi-lo| < tol_days (~0.5s) → jd_boundary.
```

Implemented helpers: `_bracket_and_find_tithi_boundary`, `_bracket_and_find_yoga_boundary`, `_bracket_and_find_moon_boundary`, `_find_crossing`. Wrap handling via unwrapped angle (+360 if needed).

Tests include midnight crossover, sunrise boundary, Tithi/Nakshatra/Yoga/Karana exact boundary ± microsecond.

---

## 8. Known Tradition-Dependent Areas

| Area | Default | Alternative | How to switch |
|------|---------|-------------|--------------|
| Karana fixed placement | Kimstughna at 0, Shakuni58 Chatushpada59 Naga59? Actually Kim 0 Shakuni57 Chatushpada58 Naga59 | Rotate list: some schools put Kimstughna at 59, Shakuni at 57 still same but rotated — effectively same 60 cycle with different labelling of which half is which | Edit `KARANA_SEQUENCE_60` ordering |
| Sunrise definition | SWE `rise_trans` geometric + refraction default (0,0) | Horizon with altitude/pressure corrected differently / center vs upper limb | Pass non-zero `atpress/attemp` via profile (future) |
| Vara sunrise vs midnight | Civil midnight primary; sunrise flag documented | Vedic sunrise-based vara (day starts at sunrise) as primary | Use `is_vedic_sunrise_based` to choose (consumer decides) |

No other limb has material tradition variance.

---

## 9. Testing

`backend/test_panchanga_phase3.py` / comprehensive:

- Tithi: normal day 2026-09-02, midnight crossover, boundary at 12° multiples, Shukla/Krishna Paksha split, percent elapsed 0..100
- Karana: exhaustive 60 positions check (each diff 0..360 at 6° midpoints), fixed vs movable flags
- Nakshatra: 27 names, Pada 1..4, boundary at 13°20′, elapsed percent
- Yoga: 27 names, boundaries at 13°20′, sum wrap
- Vara: UTC rollover test (00:02 IST vs UTC date), sunrise flag
- Sunrise/sunset: comparison for Anaparthy vs Delhi vs Svalbard polar case, local vs UTC iso consistency
