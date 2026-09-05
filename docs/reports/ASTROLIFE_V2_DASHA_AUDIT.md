# Astrolife V2 — Dasha Audit (Phase 3 Step 1)

**Date**: 2026-09-02  
**Audited file**: `backend/calculations.py` — `compute_vimshottari_timeline`, `calculate_antar_dasha`, `calculate_pratyantar_dasha`, `calculate_sookshma_dasha`, `calculate_prana_dasha`, helpers `jd_to_datetime`, `jd_to_local_iso`  
**Canonical source**: `backend/core/calculation/nakshatra.py` / `ChartFacts.planets["Moon"].longitude.sidereal`  
**Golden birth**: 17 Aug 2005 00:02 IST Asia/Kolkata, Moon sidereal 257.862789° = Purvashada pada 2, lord Venus

---

## 1. Mahadasha Sequence

| Item | Expected | Actual | Status |
|------|----------|--------|--------|
| Order | Ketu(7) Venus(20) Sun(6) Moon(10) Mars(7) Rahu(18) Jupiter(16) Saturn(19) Mercury(17) total 120 | `VIMSHOTTARI_ORDER` matches exactly, `VIMSHOTTARI_YEARS` matches exactly | PASS |
| Total years | 120 | sum = 120 | PASS |
| Convention | One global `VIMSHOTTARI_YEARS` dict | correct and documented | PASS |

No issue.

---

## 2. Starting Mahadasha

Formula used (`calculations.py:633-641`):
```
nak = compute_nakshatra_pada(moon_sidereal_lon)
fraction_into = nak["fraction"]  # 0..1 within 13°20' = 13.333°
remaining_years = (1 - fraction_into) * full_years[lord]
```

- `compute_nakshatra_pada` (`calculations.py:216-228`) is duplicate of canonical `core/calculation/nakshatra.py:18`. Both use `13.333°` division, `math.floor`, `NakshatraLords` same ordering — consistent.
- Canonical ChartFacts already holds `planets["Moon"].nakshatra`. The dasha code recomputes from `moon_sidereal_lon` argument instead of consuming `ChartFacts`. Step 2 says *Do NOT recalculate Moon longitude — use ChartFacts*. Current code does not read ChartFacts at all; `compute_chart` passes `moon_sid` float. This is an indirection violation (not using canonical object) and duplicates nakshatra logic.
- **Correctness**: arithmetic identical to canonical, so numeric result matches — but the indirection is non-canonical. For Purvashada (index 20, lord Venus 20y): Moon 257.862° → offset into nakshatra = 257.862 - (20*13.333...)= 257.862-266.666? Actually 20*13.333=266.666, wrap: Moon 257.862 => index 19? Need check: 257.862/13.333=19.339 => index 19 = Purvashada indeed (0-indexed 19). Fraction =0.339. So remaining Venus = 0.661*20=13.22 y. The legacy code produces this.

**Finding M1 — minor**: indirection via float param instead of ChartFacts.

---

## 3. Antar / Pratyantar / Sookshma / Prana Hierarchy

Implemented levels:

- `calculate_antar_dasha(mahadasha_lord, mahadasha_years, start_jd, days_in_year, tz_name)` — `calculations.py:456`  
  Formula `antar_years = antarLordYears * mahadashaYears /120` — correct.
  Sequence starts from mahadasha lord (`seq.index(mahadasha_lord)`) — correct.

- `calculate_pratyantar_dasha(antar_lord, antar_years, start_jd, days_in_year, tz_name)` — `calculations.py:559` also recursively generates Sookshma inside — `calculations.py:587` calls `calculate_sookshma_dasha`.

- `calculate_sookshma_dasha(pratyantar_lord, pratyantar_years, start_jd, days_in_year, tz_name)` — `calculations.py:498` formula `lord*pratyantar/120` — correct, produces `prana_dashas: []` placeholder.

- `calculate_prana_dasha(sookshma_lord, sookshma_years, start_jd, days_in_year, tz_name)` — `calculations.py:529` formula correct.

**Hierarchy**: MD → AD → PD → Sookshma → Prana — structurally present.

**Issues**:

| Issue | Description | Severity |
|-------|-------------|----------|
| H1 — Partial MD slicing | First (birth) MD is partial (`remaining_years`). Antar/Pratyantar/Sookshma for that MD are generated as *full* sequences from `mahadasha_start_jd` then clipped to `[cursor, end_jd)` window via overlap checks (`calculations.py:661-737`). This clipping creates *partial* antar periods at edges with truncated `years` computed as `(end-start)/days_in_year`. Durations sum correctly but representation creates antar periods with `start_jd` == birth JD that do not start on lord boundary (they are sliced). Traditional display often shows only the remaining portion — but spec requires each period has `lord, start, end, duration, hierarchy, parent` with full-precision parent. Sliced antar has correct parent but its `years` is truncated, not canonical lord*years/120. | MEDIUM — duration semantics conflated |
| H2 — Sookshma only for current branch | For subsequent full MDs (`calculations.py:770-781`), each antar generates full pratyantar set including full sookshma arrays. For the initial partial MD, only antars overlapping the remaining window get pratyantar, and only overlapping pratyantar get sookshma, via nested overlap filters (`calculations.py:698-726`). Result: sookshma tree is *sparse* for first MD — not exhaustive 9×9×9 =729 leaves. That is intentional lazy expansion but violates Step 4 "Each period must have hierarchy" if consumer expects uniform tree. | LOW — intentional lazy |
| H3 — Prana always lazy | Prana arrays are empty (`[]`) everywhere except current active sookshma where `calculate_prana_dasha` is called on demand at runtime (`calculations.py:837-843`). So stored timeline has no prana except for now — not deterministic for future dates if caller asks "what is prana on 2030-01-01" it would need to recompute. | MEDIUM — spec expects prana calculable without relying on now |

---

## 4. Nakshatra Balance & Year-Length Convention

- **Year model**: `days_in_year = 365.2425` hard-coded at `calculations.py:643` and threaded as argument to helpers. Not exposed as profile. Tests cannot vary year model. Documentation does not state convention. Spec Step 6 requires explicit `DashaCalculationProfile { year_model, days_per_year }`. **Violation**.
- **Total cycle**: `years_ahead * days_in_year` loop (`calculations.py:760`) with `years_ahead=100` default. No config for end date. Spec Step 3 requires `calculate_vimshottari_timeline(chart_facts, start_date, end_date)` or equivalent with explicit range — not just years_ahead.
- Balance: as above, derived from fraction — arithmetic correct.

**Finding Y1**: hard-coded 365.2425 everywhere, no `DashaCalculationProfile`.

---

## 5. Date Conversion

- Helpers: `jd_to_datetime(jd)` (`calculations.py:385`) uses `swe.revjul`, then constructs naive `datetime`, then if `_active_tz` set and caller != sunrise helper, converts UTC→local via global `_active_tz`. This uses `inspect.currentframe()` stack introspection (`calculations.py:411-413`) — extremely fragile, non-deterministic for testing, and couples time conversion to global mutable `_active_tz`.
- `jd_to_local_iso(jd, tz_name)` (`calculations.py:423`) does similar but respects `tz_name` or `_active_tz` fallback, converts UTC JD → local ISO via `pytz`. Internally truncates seconds to 59 if overflow — loses sub-second.
- Both helpers lose fractional second precision (`int(second)`). For Dasha boundaries which claim microsecond accuracy, truncation to whole second introduces ~1 s error.
- No sub-second / microsecond preservation — violates "Do not infer dates from rounded display values. Use full precision internally."

**Findings**:

| ID | Issue |
|----|-------|
| D1 | Global `_active_tz` mutable state leaks between calls, not thread-safe, relies on stack inspection |
| D2 | Second-level truncation loses microsecond precision |
| D3 | No UTC ISO vs local ISO distinction documented; callers use inconsistent helper |

---

## 6. Current Period Detection — CRITICAL RULE VIOLATION

`compute_vimshottari_timeline` does (`calculations.py:804-851`):

```python
now_utc = datetime.now(pytz.utc)           # <-- DIRECT CLOCK READ
jd_now = swe.julday(...)
for mahadasha in timeline:
    if start_jd <= jd_now < end_jd:
        mahadasha["is_current"] = True
        # nested for antar/pratyantar/sookshma ...
        prana_dashas = calculate_prana_dasha(...)  # lazy inside loop
```

- **Violates Step 3 + CRITICAL RULE**: *"Never use datetime.now() inside a core calculation function. All dynamic calculations must receive explicit evaluation_datetime."*
- This makes function **impure** — two calls with same birth data on different wall-clock times give different `is_current` flags and different prana arrays. Tests become flaky unless wall clock mocked.
- Mandatory separation `calculate_vimshottari_timeline(...)` (pure) vs `get_current_dasha(timeline, evaluation_datetime)` (selector) is **absent** — selector is embedded.
- Boundary convention used: `start_jd <= jd_now < end_jd` — i.e. start inclusive, end exclusive — which is correct half-open, but not documented anywhere. Spec Step 5 requires explicit documented convention and microsecond boundary tests — none exist.

**Finding C1 — BLOCKER**: impurity via `datetime.now()` must be removed.

---

## 7. Sookshma / Prana Duration Precision

- Formulas use floats `antaryears = lord*mdYears/120`, then `end_jd = cursor + years*days_in_year` iterating sequentially. Cumulative floating error across 120 years is <1e-9 days (~0.08 ms) if double — acceptable.
- But `years` field stored as `round(...,6)` or `round(...,8)` then recomputed for next level via rounded value? For prana, `sookshma["years"]` is rounded to 8 decimals, then passed to `calculate_prana_dasha(sookshma_lord, sookshma["years"], ...)` (`calculations.py:838-839`). Rounding before propagation introduces systematic under/overlap: e.g. sookshma 0.012345678 rounds to 0.01234568 then prana sum may not equal parentExactly. **Violation of "Never round before performing calculations. Use full precision internally. Only round for display."**

**Finding P1**: rounding before recursion breaks precision guarantee.

---

## 8. Summary of Required Corrections (Phase 3)

| # | Correction | Spec Step |
|---|------------|-----------|
| 1 | Remove `datetime.now()` from core; create pure `calculate_vimshottari_timeline(chart_facts, start_date, end_date, profile)` and separate `get_current_dasha(timeline, evaluation_datetime)` | Step 3 |
| 2 | Introduce `DashaCalculationProfile` with `days_per_year=365.2425` default and `year_model` enum; thread through all helpers, no hard-coded constant | Step 6 |
| 3 | Replace global `_active_tz` + stack inspection with explicit `tz_name` param and pure JD→datetime conversion preserving fractional seconds (use `swe.revjul` double + sub-second) | Step 3,5 |
| 4 | Consume `ChartFacts` directly (moon lon via `chart_facts.planets["Moon"].longitude.sidereal`) not recomputed; keep helper that accepts floats but primary entry is ChartFacts | Step 2 |
| 5 | Stop rounding before recursion; keep internal JD doubles; store `duration_years` full double and formatted display separately | Step 22 |
| 6 | Document boundary convention as `[start, end)` half-open, end exclusive; add microsecond boundary tests | Step 5 |
| 7 | Provide deterministic exhaustive Sookshma/Prana expansion on demand or document lazy vs eager and make prana generation available for arbitrary evaluation datetime without depending on now | Step 4 |
| 8 | Eliminate `_active_tz` global mutation | General purity |

No Phase 1 / Phase 2 formulas (JD, ayanamsha, positions, Vargas) are touched by these fixes.
