# Astrolife V2 — Transit Specification (Phase 3)

**Version**: 1.0  
**Date**: 2026-09-02  
**Engine**: `backend/core/transit/` — `calculator.py`, `aspects.py`, `events.py`, `search.py`  
**Implements**: Step 14,15,16,17,18,19,20,21,22,23,26

---

## 1. Purpose

Create deterministic, time-dependent transit facts (no interpretation) for any `evaluation_datetime`, using Swiss Ephemeris with profile-controlled zodiac/ayanamsha/node. Later phases will score predictions — this phase only produces facts.

---

## 2. Transit Planetary Positions (Step 14)

### 2.1 Planets

Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu

### 2.2 Quantities per Planet

| Field | Source | Description |
|-------|--------|-------------|
| `tropical_longitude` | `swe.calc_ut(..., FLG_SWIEPH+FLG_SPEED)[0]` | Ecliptic longitude tropical |
| `sidereal_longitude` | `(tropical - ayanamsha) %360` | Sidereal per profile |
| `latitude` | `res[1]` | Ecliptic latitude |
| `distance` | `res[2]` | AU |
| `speed_longitude` | `res[3]` | deg/day (negative = retrograde) |
| `retrograde` | `speed<0` | bool |
| `sign`, `sign_num`, `degree_in_sign` | via `get_sign_from_longitude(sidereal)` | SIDEREAL sign if `profile.zodiac==SIDEREAL`, else derived from tropical? Currently sidereal default; tropical supported via profile switch (uses tropical for degree/sign when profile is TROPICAL) — see note |
| `nakshatra`, `nakshatra_index`, `pada`, `nakshatra_lord` | via `get_nakshatra_from_longitude(sidereal)` | 27/ pada 1..4 |
| `ayanamsha_used` | `swe.get_ayanamsa_ut(jd)` | value at evaluation JD |

### 2.3 Calculation Profile

Defaults (used if not supplied):

```
zodiac: SIDEREAL
ayanamsha: LAHIRI_STANDARD (swe.SIDM_LAHIRI)
node: MEAN (swe.MEAN_NODE)
```

Controls:

- `zodiac == SIDEREAL` → transit longitudes are sidereal for all derived signs/nakshatras.
- `zodiac == TROPICAL` → tropical longitudes used (sidereal still stored for comparison).
- `node == MEAN` vs `TRUE` changes Rahu/Ketu.

Stored in `TransitSnapshot.profile` and `cache_key.profile`.

### 2.4 Functions

```python
calculate_transit_positions(evaluation_datetime: datetime, profile=None) -> TransitSnapshot
```

Pure — evaluation JD from explicit datetime, no clock. Also:

```python
calculate_transits(start_datetime, end_datetime, profile=None, step_days=1.0) -> List[TransitSnapshot]
```

Samples from start to end inclusive step; ensures end included. Supports arbitrary ranges (Step 20/21). No hard-coded 5 months — 5-month forecast is just `2026-09-02` through `2027-02-02` as one UI use case.

---

## 3. Transit vs Natal Relationships (Step 15)

Derived per transit–natal pair (9 × N natal planets, typically 9):

```python
compute_transit_natal_relations(transits, natal, orb_conjunction=8, orb_opposition=8)
```

Each relation:

```
transit_planet, natal_planet
transit_sign, natal_sign
transit_house_from_lagna = ((transit_sign_num - natal_asc_sign) %12)+1   # whole-sign from natal Lagna
natal_house (from natal facts)
transit_house_from_moon = ((transit_sign_num - natal_moon_sign)%12)+1
transit_nakshatra, natal_nakshatra
angular_separation = min(|t-n|%360, 360-...)
is_conjunction = sep <= 8° (configurable)
is_opposition  = |sep-180| <=8°
```

No good/bad interpretation.

---

## 4. Aspect Systems — Separated (Steps 16,17,32)

Two systems, **never mixed**, labeled via `system`/`type`:

### 4.1 Western Degree Aspects

```
aspect_system = "WESTERN_DEGREE_ASPECTS"
 поддерживаем: conjunction 0°, sextile 60°, square 90°, trine 120°, opposition 180°
orb defaults:  conj 8°, sext 4°, square 6°, trine 6°, opp 8° — configurable via WesternAspectConfig
```

Per pair:

```
sep = angular_sep(t_lon, n_lon)  # 0..180
aspect = nearest of {0,60,90,120,180} by |sep - angle|
orb = |sep - angle|
is_active = orb <= cfg.orb[aspect]
```

Model `WesternAspect`:

```
system: "WESTERN"
type: "DEGREE_ASPECT"
transit_planet, natal_planet
aspect: "conjunction"/"sextile"/...
exact_angle: 0/60/...
orb: degrees
is_active: bool
transit_longitude, natal_longitude
```

Fact only.

### 4.2 Parashari Graha Drishti

```
aspect_system = "PARASHARI_GRAHA_DRISHTI"
offsets per graha (house counts inclusive):
  Sun 7, Moon 7, Mars 4/7/8, Mercury 7, Jupiter 5/7/9, Venus 7, Saturn 3/7/10
Rahu/Ketu: configurable via ParashariAspectConfig.node_mode
```

Defaults `node_mode = NONE` (no aspects for Rahu/Ketu) — most conservative, documented explicitly. Alternatives: `PARASHARI_5_7_9` or `SAME_AS_JUPITER` gives 5/7/9 for nodes (some schools). Consumer can switch without code change.

Whole-sign methodology:

```
transit_house_from_lagna = house_of(transit_sign) from natal asc
aspected_houses = { ((H-1 + off -1)%12)+1 for off in offsets }
aspects_natal = natal_planet_house in aspected_houses
```

Model `ParashariAspect`:

```
system: "PARASHARI"
type: "GRAHA_DRISHTI"
transit_planet, natal_planet
transit_house_from_natal_lagna, natal_house
aspected_houses: List[int]
aspects_natal: bool
graha, aspect_rule: "5,7,9" etc.
```

**Do not confuse**: Graha Drishti is not degree-based; a planet aspects an entire house sign. The Western type is degree-based. Step 32 requires explicit labeling — done via `system` fields.

---

## 5. Transit Events — Deterministic Detection (Step 18)

Types (fact only):

| Event `type` | Meaning |
|--------------|---------|
| `sign_ingress` | Transit crosses 0°/30°/…/`30°*k` (sidereal) |
| `nakshatra_ingress` | Crosses `k*13°20′` |
| `retrograde_station` | Speed 0 crossing from direct → retrograde |
| `direct_station` | Speed 0 retrograde → direct |
| `exact_conjunction` | `transit_lon == natal_lon` (0°) |
| `exact_opposition` | `transit_lon == natal_lon+180°` |
| `western_aspect_exact` | Transit–natal = aspect angle within tol (via speed bracketing) |
| `parashari_aspect_change` | Transit changes house → graha drishti set changes |

Function:

```python
detect_transit_events(natal: ChartFacts, start_datetime, end_datetime, profile=None, sample_step_days=1.0) -> List[TransitEvent]
```

Sampling `1 day` (0.25 for Moon for conjunction search) then refining via bracketing.

Each `TransitEvent`:

```
type: str
transit_planet, natal_planet? (for conjunctions)
details: {from_sign, to_sign, longitude} or {target_longitude, separation} etc.
jd, utc_iso
system: "TRANSIT_EVENT_FACT"
```

Sorted by JD.

### 5.1 Time Search Precision (Step 19)

Where exactness required:

```
1. Identify approximate interval via daily sampling (bracket)
2. Refine via bisection/root-finding to tol 0.5 sec (~5.8e-6 days)  — 50-60 iterations
```

Applied to:

- conjunction/opposition: signed difference `((t_lon - target +540)%360)-180` sign change → bisection on JD.
- sign/nakshatra ingress: target = `k*unit` crossing detection + bisection on longitude.
- station: `speed(lo)*speed(hi)<0` → bisection on speed sign.

Stores full precision JD internally; ISO rounded only for display.

---

## 6. Transit Range (Step 20/21)

```python
calculate_transits(start_datetime, end_datetime, location, calculation_profile)
# In our API:
get_transit_range(start_datetime, end_datetime, lat, lon, tz, profile)
```

No dependency on “today”. UI examples:

- today → `[now, now+1d)`
- 7 days → `[now, now+7d)`
- 5 months → `[2026-09-02, 2027-02-02]` (5 months = arbitrary; no special-case code, just date arithmetic).

---

## 7. Precision (Step 22)

- Never round positions before calculating aspects/ingresses — degree separation uses full `lon_sidereal` doubles.
- Display rounding only: `orb` stored rounded to 4 decimals for readability but underlying `sep` double preserved in `transit_longitude`/`natal_longitude`.
- Internally for events, longitudes stored as `float` doubles exact to ~1e-9°.

Example:

```
internal: 23.456789123°
display: 23°27′24″ (via degree helpers, not used for aspect math)
```

---

## 8. Verification (Step 23)

For fixed dates, transit longitudes compared to **SWE direct calculation** (reference authority), not astrology app rounded UI.

Verification helper inside test:

```
jd = _evaluation_jd(evaluation_datetime)
swe.set_sid_mode(LAHIRI)
ay = get_ayanamsa_ut(jd)
lon_trop = swe.calc_ut(jd, pid)[0]
lon_sid_expected = (lon_trop - ay)%360
assert abs(snapshot.planets[pl].sidereal_longitude - lon_sid_expected) < 1e-9
```

External reference (Drik Panchang UI) may be cited for approximate manual spot-check but not authoritative; SWE is authority.

---

## 9. Inputs / Outputs

### TransitSnapshot

```
evaluation_jd, evaluation_utc_iso
profile, ayanamsha, ayanamsha_system
planets: Dict[str, TransitPlanetPosition]   # 9 entries
```

### Functions Summary

| Function | Inputs | Output |
|----------|--------|--------|
| `calculate_transit_positions(eval_dt, profile)` | explicit datetime + profile | `TransitSnapshot` |
| `calculate_transits(start, end, profile, step)` | two explicit datetimes | `List[TransitSnapshot]` |
| `compute_western_aspects(snapshot, natal, profile)` | transits + natal facts | `List[WesternAspect]` |
| `compute_parashari_aspects(snapshot, natal, profile)` | transits + natal | `List[ParashariAspect]` |
| `compute_transit_natal_relations(snapshot, natal)` |  | `List[TransitNatalRelation]` |
| `detect_transit_events(natal, start, end, profile)` | natal + two datetimes | `List[TransitEvent]` |
| `find_exact_conjunction(planet, natal_lon, lo, hi, profile)` | planet + target lon + interval | `Optional[JD]` |
| `get_transit_range(start,end,lat,lon,tz,profile)` | wrapper for 5-month forecast | `List[dict]` |

---

## 10. Tradition-Dependent Choices

| Area | Default | Alternative | How to switch |
|------|---------|-------------|--------------|
| Ayanamsha | Lahiri Standard `SIDM_LAHIRI` | Raman, KP, True Chitra etc. | `CalculationProfile(ayanamsha=...)` |
| Node | Mean | True | `CalculationProfile(node=TRUE)` |
| Rahu/Ketu aspects | NONE | 5/7/9 | `CalculationProfile(parashari_aspect_config=ParashariAspectConfig(node_mode=SAME_AS_JUPITER))` |
| Western orbs | conj 8 sext 4 sq 6 tri 6 opp 8 | custom per user | `WesternAspectConfig(orbs={...})` |
| Zodiac | Sidereal | Tropical (if needed for Western comparison) | `CalculationProfile(zodiac=TROPICAL)` |

Documented in `CalculationProfile` and test.

---

## 11. Testing

`backend/test_transit_phase3.py` / comprehensive:

Fixed dates: `2005-08-17T00:02+05:30` (birth), `2026-01-01`, `2026-06-01`, `2026-09-02`, `2027-01-01` — all aware, no `now`. For each:

- All 9 planets have tropical/sidereal, latitude, speed, retrograde bool, sign, nakshatra, pada, degree 0..30
- Sidereal = (tropical - ay) mod360 within 1e-9 (self-consistency)
- Retrograde sign matches speed sign for Mercury/Venus etc. at those dates — verified against independent SWE call
- Western aspects count: 81 pairs (9×9), orb calculation matches sep
- Parashari aspects: 81 pairs, offsets correct, node handling per mode
- Events: sign ingress for Sun (1 per ~30 days) detected; Moon nakshatra ingress ~13× per month; station for Mercury etc. — verified by bisection
- Range `2026-09-02` through `2027-02-02` (5 months) returns ~153 snapshots daily (no special case)
