# Astrolife V2 - Phase 1: Canonical Calculation Layer

This document describes the implementation of the single canonical calculation/truth layer for all fundamental astrological computations.

## Overview

Phase 1 establishes one authoritative structured result (`ChartFacts`) containing all canonical facts. All downstream astrology modules must consume these facts rather than performing independent calculations.

## Architecture

```
backend/core/calculation/
├── config.py         # CalculationProfile, enums (Zodiac, Ayanamsha, Node, House System)
├── models.py         # Pydantic models for ChartFacts and all sub-components
├── time_utils.py     # Timezone → UTC → Julian Day pipeline
├── ephemeris.py      # Swiss Ephemeris calculations (planets, ascendant, ayanamsha)
├── houses.py         # Whole Sign house generation
├── nakshatra.py      # Nakshatra & Pada calculation
└── pipeline.py       # generate_chart_facts() - main entry point
```

## Calculation Profile (Canonical Configuration)

```python
DEFAULT_PROFILE = CalculationProfile(
    zodiac=ZodiacSystem.SIDEREAL,
    ayanamsha=AyanamshaSystem.LAHIRI_STANDARD,
    node=NodeSystem.MEAN,
    house_system=HouseSystem.WHOLE_SIGN
)
```

## Time Pipeline (Deterministic)

**Input**: Local birth datetime + IANA timezone (e.g., `Asia/Kolkata`)
**Process**: `pytz` localization → UTC conversion → `swe.julday()`
**Output**: `TimeDetails` with:
- `local_datetime`: ISO format local time
- `timezone`: IANA name
- `utc_datetime`: ISO format UTC time
- `julian_day`: Float Julian Day (UT)

**Golden Chart Value**: `2453599.2722222223`

## Julian Day

Computed via Swiss Ephemeris `swe.julday()` with Gregorian calendar flag. No dependency on system clock.

## Lahiri Ayanamsha

**Mode**: `swe.SIDM_LAHIRI` (Swiss Ephemeris Standard Lahiri)
**Call**: `swe.get_ayanamsa_ut(jd_ut)`
**Golden Chart Value**: `23.93565836563647°`

## Swiss Ephemeris Planetary Positions

**Planets**: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn
**Flags**: `FLG_SWIEPH | FLG_SPEED`
**Returns per planet**:
- `tropical`: Raw tropical longitude
- `sidereal`: `(tropical - ayanamsha) % 360`
- `latitude`: Ecliptic latitude
- `distance`: Distance from Earth (AU)
- `speed`: Daily motion in longitude
- `retrograde`: `speed < 0`

## Mean Node (Rahu/Ketu)

**Rahu**: `swe.MEAN_NODE` with same flags as planets
**Ketu**: Exactly opposite Rahu
```
ketu_tropical = (rahu_tropical + 180) % 360
ketu_sidereal = (rahu_sidereal + 180) % 360
ketu_latitude = -rahu_latitude
ketu_speed = rahu_speed
ketu_retrograde = rahu_retrograde
```

**Golden Chart Verification**: Ketu longitude = (Rahu + 180) mod 360 ✓ (exact to 1e-10)

## Ascendant

**Method**: `swe.houses_ex(jd_ut, lat, lon, b'W')` (Whole Sign house system)
**Ascendant tropical** = `ascmc[0]`
**Ascendant sidereal** = `(tropical - ayanamsha) % 360`

**Golden Chart Value**: `39.955221668117616°` (Taurus)

## Whole Sign Houses

House 1 = Ascendant sign
House N = (Ascendant sign + N - 1) mod 12
Cusp degree = 0° for all houses

## Nakshatra & Pada

- 27 Nakshatras of 13°20' (360/27) each
- 4 Padas of 3°20' each per Nakshatra
- Lords: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury (repeating ×3)
- Calculated from **sidereal longitude**

## Canonical Facts Object (`ChartFacts`)

```python
ChartFacts(
    calculation_profile: CalculationProfile,
    location: Location,              # name, country, lat, lon, tz
    time: TimeDetails,               # local, tz, utc, jd
    ayanamsha: AyanamshaDetails,     # system, swiss_mode, value
    ascendant: AscendantData,        # longitude(trop/sid), sign, nakshatra
    planets: Dict[str, PlanetData],  # 9 planets with full details
    houses: Dict[int, HouseData],    # 1-12 with sign
    metadata: Dict                   # evaluation_datetime
)
```

### Per-Planet Data (`PlanetData`)

| Field | Type | Description |
|-------|------|-------------|
| `id`, `name` | str | Planet identifier |
| `longitude.tropical` | float | Tropical longitude (0-360) |
| `longitude.sidereal` | float | Sidereal longitude (0-360) |
| `latitude` | float | Ecliptic latitude |
| `distance` | float | Distance in AU |
| `speed` | float | Daily motion (°/day) |
| `retrograde` | bool | True if speed < 0 |
| `sign.id` | int | Sign number (1-12) |
| `sign.name` | str | Sign name |
| `sign.degree` | float | Degree within sign (0-30) |
| `house` | int | House number (1-12) |
| `nakshatra.id` | int | Nakshatra number (1-27) |
| `nakshatra.name` | str | Nakshatra name |
| `nakshatra.lord` | str | Nakshatra lord |
| `nakshatra.pada` | int | Pada (1-4) |
| `nakshatra.fraction` | float | Fraction into nakshatra (0-1) |
| `nakshatra.degree_within` | float | Degree within nakshatra |

## Integration with Legacy Code

The legacy `compute_chart()` in `backend/calculations.py` now:
1. Calls `generate_chart_facts()` for canonical values
2. Overwrites legacy fundamental values (longitude, sign, speed, retrograde) with canonical ones
3. Retains legacy-derived attributes (combust, debilitated, exalted, dasha, vargas, etc.)
4. Maintains full backward compatibility

## Golden Chart Validation

| Parameter | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Julian Day | 2453599.2722222223 | 2453599.2722222223 | ✓ |
| Ayanamsha | 23.93565836563647 | 23.93565836563647 | ✓ |
| Ascendant (sid) | 39.955221668117616 | 39.955221668117616 | ✓ |
| Ascendant Sign | Taurus | Taurus | ✓ |
| Sun (sid) | 120.042° Leo | 120.041860° Leo | ✓ |
| Moon (sid) | 257.863° Sag | 257.862785° Sag | ✓ |
| Mercury (sid) | 104.840° Can | 104.839559° Can | ✓ |
| Venus (sid) | 155.642° Vir | 155.641769° Vir | ✓ |
| Mars (sid) | 16.594° Ari | 16.593077° Ari | ✓ |
| Jupiter (sid) | 171.843° Vir | 171.842643° Vir | ✓ |
| Saturn (sid) | 100.063° Can | 100.062511° Can | ✓ |
| Rahu (sid) | 352.327° Pis | 352.326431° Pis | ✓ |
| Ketu (sid) | 172.327° Vir | 172.326431° Vir | ✓ |
| Ketu = Rahu+180 | 172.326431 | 172.326431 | ✓ |
| Moon Nakshatra | Purvashada | Purvashada | ✓ |
| Moon Pada | 2 | 2 | ✓ |

All planetary longitudes match within 0.001° tolerance.

## Determinism

Static natal chart calculations **do not depend on**:
- `datetime.now()` or `datetime.utcnow()`
- Machine timezone
- Random values

Same input → identical output (verified bitwise for JD, Ayanamsha, Moon position).

## Usage

```python
from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DEFAULT_PROFILE

facts = generate_chart_facts(
    year=2005, month=8, day=17,
    hour=0, minute=2, second=0,
    lat=16.93407, lon=81.95522,
    tz_name="Asia/Kolkata",
    location_name="Anaparthy",
    country_name="India",
    profile=DEFAULT_PROFILE
)

# Access canonical data
print(facts.ascendant.sign.name)        # "Taurus"
print(facts.planets["Sun"].longitude.sidereal)  # 120.04186
print(facts.planets["Moon"].nakshatra.name)     # "Purvashada"
print(facts.houses[1].sign.name)        # "Taurus"
```

## Files Created/Modified

### New Files (Canonical Layer)
- `backend/core/calculation/config.py`
- `backend/core/calculation/models.py`
- `backend/core/calculation/time_utils.py`
- `backend/core/calculation/ephemeris.py`
- `backend/core/calculation/houses.py`
- `backend/core/calculation/nakshatra.py`
- `backend/core/calculation/pipeline.py`

### Modified Files
- `backend/calculations.py` - Integrated canonical pipeline, maintains backward compatibility

### Test Files
- `backend/test_golden_chart_canonical.py` - Comprehensive regression tests (39 tests, all passing)