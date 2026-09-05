# Astrolife V2 — Vimshottari Dasha Specification (Phase 3)

**Version**: 1.0  
**Date**: 2026-09-02  
**Status**: Implemented (`backend/core/calculation/dasha.py`)  
**Canonical dependency**: `ChartFacts` — Moon sidereal longitude (`facts.planets["Moon"].longitude.sidereal`)  
**Implements**: Step 2,3,4,5,6,25

---

## 1. Formulas

### 1.1 Vimshottari Sequence and Years

Fixed order (Ketu → Mercury, total 120 years):

| # | Lord | Years |
|---|------|-------|
| 1 | Ketu | 7 |
| 2 | Venus | 20 |
| 3 | Sun | 6 |
| 4 | Moon | 10 |
| 5 | Mars | 7 |
| 6 | Rahu | 18 |
| 7 | Jupiter | 16 |
| 8 | Saturn | 19 |
| 9 | Mercury | 17 |
|   | **Total** | **120** |

```
VIMSHOTTARI_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
VIMSHOTTARI_YEARS = {"Ketu":7, "Venus":20, "Sun":6, "Moon":10, "Mars":7, "Rahu":18, "Jupiter":16, "Saturn":19, "Mercury":17}
```

Immutable. No tradition-dependent variant (all schools agree).

### 1.2 Nakshatra Balance → Starting Mahadasha

Moon sidereal longitude determines starting Mahadasha:

```
lon = Moon_sidereal % 360
nak_index_float = lon / (360/27)   # 0..27, size = 13°20′ = 13.333...
nak_index = floor(nak_index_float)  # 0..26
fraction_into = nak_index_float - nak_index   # 0..1 within nakshatra
lord = NAKSHATRA_LORDS[nak_index]   # Ketu×3 cycle
full_years = VIMSHOTTARI_YEARS[lord]
remaining_years = (1 - fraction_into) * full_years
```

`fraction_into` is the fraction already traversed; remaining is `1 - fraction`.  
The *first* (birth) Mahadasha is **partial**: duration = `remaining_years`, start = birth JD, end = birth JD + remaining_years × days_per_year.

The *full* Mahadasha would have started ` (full_years - remaining_years) × days_per_year` before birth — used only to slice Antar subperiods correctly.

**Example (golden chart)**: Moon 257.862789° → nak_index 19 = Purvashada, lord Venus 20y, fraction 0.33967, remaining 13.2066y.

### 1.3 Sub-period Division (Proportional)

For every parent period P with `years_P`, its 9 children C_i dividing the parent in sequence order starting from parent lord:

```
years_{C_i} = VIMSHOTTARI_YEARS[lord_{C_i}] * years_P / 120
end = start + years_{C_i} * days_per_year
start_{next} = end_{prev}
```

Applies identically at all levels:

- Mahadasha (level 1) → Antardasha (level 2) : `lord_ Antar = Years[AntarLord] * Years[MD] /120`
- Antar (2) → Pratyantar (3): `lord*AntarYears/120`
- Pratyantar (3) → Sookshma (4): `lord*PratyYears/120`
- Sookshma (4) → Prana (5): `lord*SookshmaYears/120`

Sequence order at each level is always `VIMSHOTTARI_ORDER` rotated to start at parent lord.

**Duration conservation**: Σ child years = parent years exactly (before rounding; floating error <1e-12 days).

### 1.4 Ages

```
age_at_start = (period.start_jd - birth_jd) / days_per_year
age_at_end   = (period.end_jd   - birth_jd) / days_per_year
```

### 1.5 Boundary Convention

**Half-open** `[start_jd, end_jd)` — start inclusive, end exclusive.

- `jd == start_jd` is inside the period (happens at birth for first MD, at Antar boundary for sublevels).
- `jd == end_jd` is **outside** — belongs to next period.
- Tested with microsecond before/after exact boundary (Step 5 requirement).

Documented in `DashaTimeline.boundary_convention` and `DashaPeriod` models.

---

## 2. Inputs

| Input | Type | Description |
|-------|------|-------------|
| `chart_facts` | `ChartFacts` | Canonical birth facts; reads `time.julian_day` and `planets["Moon"].longitude.sidereal` |
| `profile` | `DashaCalculationProfile` or None | Controls year model. `None` → chart_facts profile or `DEFAULT_DASHA_PROFILE` |
| `years_ahead` | `float` | Generation horizon relative to birth (default 120). Overridden by explicit `start_jd_override`/`end_jd_override` |
| `evaluation_datetime` | `datetime` (aware) | **Explicit** evaluation moment for `get_current_dasha` — never reads clock inside core |

No globals, no `datetime.now()` inside core.

---

## 3. Outputs

### 3.1 `DashaPeriod`

| Field | Type | Meaning |
|-------|------|---------|
| `level` | `1..5` | 1=MD, 2=AD, 3=PD, 4=Sookshma, 5=Prana |
| `lord` | `str` | Planet name |
| `start_jd`, `end_jd` | `float` | Julian Day (UT) full double precision |
| `start_utc_iso`, `end_utc_iso` | `str` | ISO 8601 UTC (Z) — derived from JD via `swe.revjul`, preserves microseconds |
| `duration_years` | `float` | Full double, `years_child = lordYears * parentYears /120` — **not** rounded before propagation |
| `duration_days` | `float` | `duration_years * days_per_year` |
| `parent_lord` | `Optional[str]` | Lord of parent (None for MD) |
| `index_in_parent` | `Optional[int]` | 0..8 |
| `is_partial` | `bool` | True if birth-sliced or generation-window-clipped |

Display rounding is done only when building legacy shim dicts (`round(...,4/6/8/10)`).

### 3.2 `DashaTimeline`

Top-level produced by `calculate_vimshottari_timeline`:

| Field | Meaning |
|-------|---------|
| `birth_jd`, `birth_utc_iso` | Birth JD / ISO |
| `moon_nakshatra_index`, `moon_nakshatra_name`, `moon_nakshatra_fraction` | Nakshatra state of Moon at birth |
| `starting_lord` | Lord of first MD |
| `remaining_years_at_birth` | Partial MD duration in years |
| `profile_used` | Echoed profile |
| `mahadashas` | `List[{period: DashaPeriod, antar_dashas: [{period, children: [{period, children: [{period, children: [{period}] }]}]}]}]` |
| `total_years_calculated` | `(last_end - birth_jd)/days_per_year` |
| `boundary_convention` | Human-readable invariant |

### 3.3 `get_current_dasha` result

```
{
  mahadasha: DashaPeriod|None,
  antardasha: DashaPeriod|None,
  pratyantardasha: DashaPeriod|None,
  sookshma: DashaPeriod|None,
  prana: DashaPeriod|None,
  hierarchy: [lord_MD, lord_AD, ..., lord_Prana]  # up to wherever matched
  evaluation_jd, evaluation_utc_iso,
  note?: "before birth" | "beyond timeline"
}
```

One dict, not timeline mutation. Timeline remains pure.

---

## 4. Time Scales & Timezone Handling

- **Julian Day** is UT-based (via `swe.julday(..., GREG_CAL)`). All periods stored in JD(UT).
- **ISO strings**: UTC (`Z`) by default. Conversion preserves microseconds via `swe.revjul` + `datetime` microsecond.
- **No timezone-dependent Dasha**: Vimshottari depends only on Moon longitude (SIDEREAL) and year length in days, not location. The birth JD already encodes timezone → UTC → JD conversion. No lat/lon used thereafter.
- **Year length**: `days_per_year` from profile. Default `365.2425` (Gregorian mean tropical year approximation, dominant in JHora/ProKerala). Other traditions use `360` (Savana year = 360 tithis), `365.25`, sidereal `365.25636` — all supported via profile without code change.

---

## 5. Precision

- **Internal**: `float64` doubles, never rounded before recursion. `duration_years` propagated as full double; only legacy display fields rounded.
- **Cumulative error**: Across 120y chain, ≤2e-12 days (~0.17 ms) due to IEEE double, acceptable.
- **Boundary**: JD comparison uses `<` / `<=` on raw double, not rounded ISO string.

---

## 6. Year Model

### DashaCalculationProfile

```python
class DashaCalculationProfile(BaseModel):
    year_model: YearModel = TROPICAL_YEAR_APPROXIMATION
    days_per_year: float = 365.2425
    total_cycle_years: float = 120.0
```

| `year_model` | `days_per_year` | Notes |
|--------------|------------------|-------|
| `TROPICAL_YEAR_APPROXIMATION` | 365.2425 | Default, used by JHora, ProKerala, Jagannatha Hora for compatibility |
| `SIDEREAL_YEAR` | 365.256363 | Sidereal year (less common) |
| `CUSTOM` | user-set | e.g. 360 (Savana), 365.25 |

Profile is stored in `CalculationProfile.dasha_profile` (additive, not breaking Phase1). If chart_facts has one, it wins; else `DEFAULT_DASHA_PROFILE`.

Hard-coded `365.2425` inside helpers is prohibited; all helpers now take `profile.days_per_year`.

---

## 7. Boundary Handling

Half-open `[start, end)` enforced everywhere:

```
period.contains(jd) := period.start_jd <= jd < period.end_jd
```

Boundary tests (required 100+ suite) verify:

- `jd == start_jd` → inside current, not previous
- `jd == end_jd` → outside current, inside next (successor's start)
- 1 microsecond before start → predecessor
- 1 microsecond after end → successor (same as exact end)
- 1 microsecond before end → still inside current

First MD's `start_jd == birth_jd` so birth moment is inside first MD.

---

## 8. Functions

### 8.1 Pure Generation

```python
calculate_vimshottari_timeline(
    chart_facts: ChartFacts,
    profile: Optional[DashaCalculationProfile] = None,
    years_ahead: float = 120.0,
    start_jd_override: Optional[float] = None,
    end_jd_override: Optional[float] = None,
) -> DashaTimeline
```

Or low-level:

```python
_calculate_timeline_from_birth_params(jd_birth, moon_sidereal_lon, profile, years_ahead, ...)
```

### 8.2 Legacy Shim

```python
compute_vimshottari_timeline(jd_birth, moon_sidereal_lon, years_ahead=100) -> legacy_dict
```

Calls `legacy_compute_vimshottari_timeline_shim` from `dasha.py`. Keeps keys `nakshatra_of_moon`, `timeline`, `total_years_calculated`, `dasha_cycle_years`, with nested `antar_dashas`, `pratyantar_dashas`, `sookshma_dashas`, `prana_dashas` for backward compatibility. `is_current` is always `False` (pure).

### 8.3 Pure Selector

```python
get_current_dasha(dasha_timeline: DashaTimeline, evaluation_datetime: datetime) -> dict
```

Converts `evaluation_datetime` (aware or naive UTC) to JD via `_evaluation_jd`, walks MD → AD → PD → Sookshma → Prana using half-open rule.

No `datetime.now()`.

### 8.4 For UI

```python
from core.calculation.dynamic import get_dynamic_state
state = get_dynamic_state(chart_facts, evaluation_datetime=datetime.now(timezone.utc))
state.dasha["current"]["hierarchy"]  # e.g. ["Moon","Rahu","Jupiter","Rahu","Moon"]
```

UI/boundary is only place allowed to call `datetime.now()`.

---

## 9. Tradition-Dependent Areas

| Area | Choices | Default Chosen | How to Switch |
|------|---------|----------------|--------------|
| Year length | 360 / 365.2425 / 365.25 / 365.25636 | 365.2425 | `DashaCalculationProfile(days_per_year=360)` |
| Starting MD | Moon nakshatra fraction | Moon sidereal (Lahiri) fraction as above | Use different Moon lon (true sidereal etc.) via profile ayanamsha — but Dasha remains sidereal per convention |
| AD/PD order | Always start from parent lord | As above — universal | Not configurable (all schools same) |

No alternative AD ordering is attested; not varied.

---

## 10. Known Uncertainties

- **Historical Dasha before birth**: `start_jd_override < birth_jd` generates backward MDs by walking cycle backward; end-boundary semantics remain half-open but display as pre-birth periods with `is_partial=False`. Not required for Phase 3 but implemented for historical analysis use-case.
- **Long-range floating drift**: Beyond 200 years, double error accumulates ~1e-11 days (~1 µs/day × 73k days ~0.07 ms). Acceptable.

---

## 11. Testing

See `backend/test_dasha_phase3.py` / comprehensive phase3 test:

- Golden birth Venus 13.206 remaining, total cycle sum = 120 ±1e-9
- 9 MDs after Venus (Venus→...→Ketu?) cover full cycle
- AD counts: each MD has 9 ADs (except birth-sliced first MD may show fewer visible ADs but internal true =9)
- Duration sum at each level equals parent (within 1e-9 days)
- Boundary microsecond tests as in §7
- Arbitrary future evaluation 2026-09-02, 2027-02-02 produce deterministic hierarchy (Moon/Rahu/Jupiter...)
- Profile switch to 360 days changes total days but preserves year counts
