# Astrolife V2 — Phase 2 Varga Test Report

**Date**: 2026-09-02  
**Engine**: `backend/core/calculation/varga.py` + `backend/test_varga_phase2.py`  
**Golden chart**: 17 Aug 2005 00:02 IST Asia/Kolkata, Anaparthy 16.93407/81.95522, SIDEREAL/LAHIRI/MEAN/WHOLE_SIGN  
**Phase 1 regression**: `backend/test_golden_chart_canonical.py` (39/39)

---

## Summary

| Suite | Total | Passed | Failed | Pass Rate |
|-------|-------|--------|--------|-----------|
| Phase 1 Golden Chart (canonical) | 39 | 39 | 0 | 100% |
| Phase 2 Varga Comprehensive (`test_varga_phase2.py`) | 19,692 | 19,692 | 0 | 100% |
| **Combined** | **19,731** | **19,731** | **0** | **100%** |

Phase 2 breakdown:

| Category | Count | Passed | Failed |
|----------|-------|--------|--------|
| D1 validation (JD, ayanamsha, asc, signs, houses, Rahu/Ketu) | ~35 | 35 | 0 |
| Exhaustive segment tests (12×N per Varga) | 3,420 | 3,420 | 0 |
| Spot checks per Varga (Hora/Drekkana/…/D60) | ~85 | 85 | 0 |
| Boundary handling (EPSILON, half-open, ±eps) | ~20 | 20 | 0 |
| Varga degree distinction & formula | ~80 | 80 | 0 |
| Property tests (200 random lons ×16 Vargas ×4 props) | ~16,000 | 16,000 | 0 |
| API contracts (string/int/method, errors, profile) | ~15 | 15 | 0 |
| Architecture checks (no swe import, consumes ChartFacts) | ~5 | 5 | 0 |
| Integration (compute_chart legacy + enriched keys, golden D9/D10) | ~32 | 32 | 0 |

All 16 Vargas produce valid signs and degrees in exhaustive enumeration.

---

## Per-Varga Results

| Varga | Division | Segment size | Exhaustive combos (12×N) | Passed | Failed | Notes |
|-------|----------|--------------|--------------------------|--------|--------|-------|
| D1 Rashi | 1 | 30° | 12 | 12 | 0 | identity |
| D2 Hora | 2 | 15° | 24 | 24 | 0 | Leo/Cancer odd/even; boundaries at 15 |
| D3 Drekkana | 3 | 10° | 36 | 36 | 0 | 1st/5th/9th |
| D4 Chaturthamsa | 4 | 7.5° | 48 | 48 | 0 | Kendra chain |
| D7 Saptamsa | 7 | 4.285714° | 84 | 84 | 0 | odd same, even 7th |
| D9 Navamsa | 9 | 3.3333° | **108** | **108** | 0 | movable/fixed/dual exhaustive + degree exact |
| D10 Dasamsa | 10 | 3° | **120** | **120** | 0 | odd same, even 9th |
| D12 Dwadasamsa | 12 | 2.5° | 144 | 144 | 0 | sequential |
| D16 Shodasamsa | 16 | 1.875° | 192 | 192 | 0 | Aries/Leo/Sag start |
| D20 Vimsamsa | 20 | 1.5° | 240 | 240 | 0 | Aries/Sag/Leo start |
| D24 Siddhamsa | 24 | 1.25° | 288 | 288 | 0 | Leo/Cancer start |
| D27 Bhamsha | 27 | 1.1111° | 324 | 324 | 0 | elemental Fire→Aries etc. |
| D30 Trimsamsa | 5 irregular | 5/5/8/7/5 vs 5/7/8/5/5 | 60 (12×5) | 60 | 0 | irregular 5-slice, proportional degree |
| D40 Khavedamsa | 40 | 0.75° | 480 | 480 | 0 | odd Aries even Libra |
| D45 Akshavedamsa | 45 | 0.6667° | 540 | 540 | 0 | Aries/Leo/Sag |
| D60 Shashtiamsa | 60 | 0.5° | 720 | 720 | 0 | sequential, 0.5° sensitive |
| **Total exhaustive** | — | — | **3,420** | **3,420** | **0** | — |

Boundaries tested at every segment multiple and ±1e-6 (half-open). Example: D2 exactly 15° → second Hora; D3 10° → second drekkana; D60 every 0.5°.

---

## D1 Validation Detail

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Julian Day | 2453599.2722222223 | 2453599.2722222223 | PASS |
| Ayanamsha Lahiri | 23.93565836563647 | 23.93565836563647 | PASS |
| Asc sidereal lon | 39.955221668117616 | 39.955221668117616 | PASS |
| Asc sign | Taurus | Taurus | PASS |
| House 1 | Taurus | Taurus | PASS |
| Ketu opposite Rahu | (Rahu+180)%360 | matches 1e-10 | PASS |
| Sun sign | Leo | Leo | PASS |
| Moon sign | Sagittarius | Sagittarius | PASS |
| Mercury | Cancer | Cancer | PASS |
| Venus | Virgo | Virgo | PASS |
| Mars | Aries | Aries | PASS |
| Jupiter | Virgo | Virgo | PASS |
| Saturn | Cancer | Cancer | PASS |
| Rahu | Pisces | Pisces | PASS |
| Ketu | Virgo | Virgo | PASS |
| Houses, degrees, nakshatra/pada | — | all in range | PASS |

---

## Golden Chart — Full 16 Vargas (computed, PARASHARI_CLASSICAL)

Logged during test run via `calculate_all_vargas(facts)` — stored as baseline to validate (not oracle, but matches computation). D9/D10 cross-checked against Phase 0 golden baseline (Aries/… etc.) and match.

```
D1  Sun Leo 0.042, Moon Sag 17.863, Mars Aries 16.593, Merc Cancer 14.840, Jup Virgo 21.843, Venus Virgo 5.642, Sat Cancer 10.063, Rahu Pisces 22.326, Ketu Virgo 22.326, Asc Taurus 9.955
D2  Sun Leo 0.084, Moon Cancer 5.726, Mars Cancer 3.186, Merc Cancer 29.679, Jup Leo 13.685, Venus Cancer 11.284, Sat Cancer 20.125, Rahu Leo 14.653, Ketu Leo 14.653, Asc Cancer 19.910
D3  Sun Leo 0.126, Moon Aries 23.588, Mars Leo 19.779, Merc Scorpio 14.519, Jup Taurus 5.528, Venus Virgo 16.925, Sat Scorpio 0.188, Rahu Scorpio 6.979, Ketu Taurus 6.979, Asc Taurus 29.866
D4  Sun Leo 0.167, Moon Gemini 11.451, Mars Libra 6.372, Merc Libra 29.358, Jup Pisces 27.371, Venus Virgo 22.567, Sat Libra 10.250, Rahu Virgo 29.306, Ketu Pisces 29.306, Asc Leo 9.821
D7  Sun Leo 0.293, Moon Aries 5.039, Mars Cancer 26.152, Merc Aries 13.877, Jup Leo 2.899, Venus Aries 9.492, Sat Pisces 10.438, Rahu Aquarius 6.285, Ketu Leo 6.285, Asc Capricorn 9.687
D9  Sun Aries 0.377, Moon Virgo 10.765, Mars Leo 29.338, Merc Scorpio 13.556, Jup Cancer 16.584, Venus Aquarius 20.776, Sat Libra 0.563, Rahu Capricorn 20.938, Ketu Cancer 20.938, Asc Pisces 29.597
D10 Sun Leo 0.419, Moon Taurus 28.628, Mars Virgo 15.931, Merc Cancer 28.396, Jup Sag 8.426, Venus Gemini 26.418, Sat Gemini 10.625, Rahu Gemini 13.264, Ketu Sag 13.264, Asc Aries 9.552
D12 Sun Leo 0.502, Moon Cancer 4.353, Mars Libra 19.117, Merc Sag 28.075, Jup Taurus 22.112, Venus Scorpio 7.701, Sat Scorpio 0.750, Rahu Scorpio 27.917, Ketu Taurus 27.917, Asc Leo 29.463
D16 Sun Leo 0.670, Moon Virgo 15.805, Mars Sag 25.489, Merc Scorpio 27.433, Jup Scorpio 19.482, Venus Pisces 0.268, Sat Virgo 11.000, Rahu Scorpio 27.223, Ketu Scorpio 27.223, Asc Capricorn 9.284
D20 Sun Sag 0.837, Moon Cancer 27.256, Mars Pisces 1.862, Merc Capricorn 26.791, Jup Libra 16.853, Venus Scorpio 22.835, Sat Libra 21.250, Rahu Libra 26.529, Ketu Libra 26.529, Asc Gemini 19.104
D24 Sun Leo 1.005, Moon Libra 8.707, Mars Virgo 8.234, Merc Gemini 26.149, Jup Sag 14.223, Venus Scorpio 15.402, Sat Pisces 1.500, Rahu Sag 25.834, Ketu Sag 25.834, Asc Aquarius 28.925
D27 Sun Aries 1.130, Moon Leo 2.295, Mars Gemini 28.013, Merc Aquarius 10.668, Jup Aquarius 19.751, Venus Sag 2.328, Sat Libra 1.688, Rahu Virgo 2.814, Ketu Pisces 2.814, Asc Pisces 28.791
D30 Sun Aries 0.251, Moon Sag 29.485, Mars Sag 24.724, Merc Pisces 10.648, Jup Capricorn 11.056, Venus Virgo 2.750, Sat Virgo 21.696, Rahu Capricorn 13.959, Ketu Capricorn 13.959, Asc Virgo 21.237
D40 Sun Aries 1.674, Moon Pisces 24.511, Mars Aquarius 3.723, Merc Taurus 23.582, Jup Pisces 3.706, Venus Taurus 15.671, Sat Scorpio 12.500, Rahu Pisces 23.057, Ketu Pisces 23.057, Asc Scorpio 8.209
D45 Sun Leo 1.884, Moon Aquarius 23.825, Mars Aries 26.688, Merc Aquarius 7.780, Jup Leo 22.919, Venus Leo 13.880, Sat Cancer 2.813, Rahu Virgo 14.689, Ketu Virgo 14.689, Asc Libra 27.985
D60 Sun Leo 2.512, Moon Scorpio 21.767, Mars Capricorn 5.585, Merc Sag 20.374, Jup Aries 20.559, Venus Leo 8.506, Sat Pisces 3.751, Rahu Scorpio 19.586, Ketu Taurus 19.586, Asc Sag 27.313
```

Cross-check: D9 and D10 signs for 9 planets match `ASTROLIFE_V2_GOLDEN_CHART.md` exactly (9/9 each).

---

## Spot-Check Details (representative)

- D2: Aries 14.999→Leo, 15.0→Cancer; D2 degree 7.5→15.0 correct.
- D3: 9.999 seg0, 10.0 seg1, 19.999 seg1, 20.0 seg2.
- D7: Aries seg0 Aries, Taurus seg0 Scorpio (7th).
- D9: Aries 0→Aries, 3.34→Taurus; Taurus 0→Capricorn; Gemini 0→Libra; Leo 0→Aries — all movable/fixed/dual branches verified.
- D10: Aries 0→Aries, Taurus 0→Capricorn, Aries last segment→Capricorn.
- D16: Aries→Aries, Taurus→Leo, Gemini→Sag.
- D20: Aries→Aries, Taurus→Sag, Gemini→Leo.
- D24: Aries→Leo, Taurus→Cancer.
- D27: Fire→Aries, Earth→Cancer, Air→Libra, Water→Capricorn.
- D30: odd 2→Aries, 7→Aquarius, 14→Sag, 20→Gemini, 27→Taurus; even 2→Taurus, 8→Virgo, 15→Pisces, 22→Capricorn, 27→Scorpio.
- D40: Aries odd→Aries, Taurus even→Libra.
- D45: Aries movable→Aries, Taurus fixed→Leo, Gemini dual→Sag.
- D60: Aries 0→Aries, 0.5→Taurus, 29.9→Pisces, Taurus 0→Taurus.

---

## Boundary Handling Verification

| Division | Boundaries Tested | Epsilon Handling | Result |
|----------|-------------------|------------------|--------|
| D2 | 0,15,30 | `floor((deg+1e-9)/15)`; 15.0 correctly second Hora; 14.999999 stays first | PASS |
| D3 | 0,10,20,30 | same | PASS |
| D4 | 0,7.5,15,22.5,30 | 7.499999→seg0, 7.5→seg1, 7.5000000001→seg1 | PASS |
| D7 | multiples of 4.2857 | snapped | PASS |
| D9 | multiples of 3.33333 | 3.333 vs 3.333333 balanced; 3.34 correctly next | PASS |
| D60 | every 0.5° | 0.4999999999 handled; 0.5→next | PASS |
| D30 | 5/10/18/25 (odd) 5/12/20/25 (even) | snap within 1e-9 to cut | PASS |
| All | 30° sign wrap | clamped to last segment | PASS |

Utility `varga_segment_index(deg, division)` tested independently for D2/D3/D4/D60 clipping.

---

## Varga Degree Verification

For each exhaustive case, `varga_degree` compared to `(deg - seg*size)*division` (uniform) or proportional for D30.

- D1: `degree == deg_in_sign` ✓
- D2-D60 uniform: `abs(pos.degree - (deg - seg*size)*division) <1e-6` for all 3,360 uniform cases ✓
- D30: proportional `(residual/width)*30` ✓
- Property: all `0 ≤ degree <30` ✓ (except D30 where also, verified)
- Property: `varga_degree != source_degree` in general (not using D1 degree as Varga degree) — spot checks confirm distinct values e.g. Moon 17.86°→ D9 10.76°, D10 28.62°, D60 21.76° etc.

---

## Property Testing Results

Random 200 longitudes ×16 Vargas:

- Every lon maps to exactly one segment (segment_index always in [0,N-1]) ✓
- No invalid sign (all in SIGNS) ✓
- No invalid sign_num (1–12) ✓
- Every varga_degree in [0,30) ✓
- Longitude in [0,360) ✓
- Small delta (0.0001°) not crossing boundary does not change sign for uniform cases — exercised via exhaustive midpoints stability (not asserted as hard property to allow boundary epsilon).

---

## API & Architecture

| Test | Result |
|------|--------|
| `calculate_varga_position(lon, "D9")` string upper | PASS |
| `calculate_varga_position(lon, "d9")` lower | PASS |
| `calculate_varga_position(lon, 9)` int | PASS |
| `method="PARASHARI_CLASSICAL"` string | PASS |
| `method=VargaMethod.PARASHARI_CLASSICAL` enum | PASS |
| Invalid varga 5 raises ValueError | PASS |
| Invalid method "UNKNOWN" raises ValueError | PASS |
| `calculate_all_vargas(facts)` returns planets+ascendant with D1..D60 | PASS |
| `calculate_all_vargas(facts)` matches single-call positions | PASS |
| `varga.py` does not import `swisseph`/`swe.` | PASS (grep) |
| `varga.py` does not reference `get_ayanamsha`/`get_utc` (no recalc) | PASS |
| Per-varga profile override `{"D9":..., "D10":...}` respected | PASS |
| `compute_chart` legacy keys preserved (`d9_sign`, `d9_sign_num`, `d9_longitude`) | PASS |
| `compute_chart` new keys present (`d9_varga_degree`, `d9_segment_index`, etc.) | PASS |
| `compute_chart` ascendant enriched (`varga_degree`) | PASS |
| Golden D9/D10 integration via `compute_chart` matches Phase 0 baseline | PASS (9/9 each) |

---

## Corrections Made (Phase 2)

1. **Varga degree** — legacy `build_chart_varga` erroneously copied D1 longitude/degree into Varga position (`longitude=lon`, `asc degree=asc_sidereal`). Fixed to compute correct proportional degree inside derived sign via `(residual)*division` (or irregular mapping for D30). Legacy keys preserved for backward compatibility (`dN_longitude` still D1 lon) but new additive keys `dN_varga_degree`/`dN_varga_longitude` carry correct values. Internal `planets` entries now have `varga_degree`/`varga_longitude` distinct from `longitude`.

2. **Boundary epsilon** — legacy used raw `int(deg // size)` vulnerable to `7.499999999` FP error. Added `EPSILON=1e-9` with `floor((deg+EPSILON)/size)` and clamp; D30 cut snap within 1e-9.

3. **Unified pure engine** — replaced duplicated `navamsa_sign_num`/`dashamsha_sign_num` duplication with single `_get_varga_sign_and_segment` dispatch, exposed via `calculate_varga_position`/`calculate_all_vargas` consuming only `sidereal_longitude` (no JD/ayanamsha/Sweph).

4. **Method identifier** — added `VargaMethod` enum and `CalculationProfile.varga_method` (global or per-varga dict) with explicit propagation to every `VargaPosition.method`. All Vargas labeled `PARASHARI_CLASSICAL` with tradition alternatives documented.

5. **ChartFacts as source** — `compute_chart` now derives Vargas via `calculate_all_vargas(facts)` (primary path) rather than legacy `d1_planets` list alone. Fallback to `build_chart_varga` (which itself delegates to pure engine) if structured path fails, ensuring derivation from canonical longitudes.

6. **D30** — verified NOT replaced with 1° uniform; cut points kept as 5/10/18/25 (odd) and 5/12/20/25 (even) with proportional degree.

7. **D60** — sequential method retained as default but now labeled `TRADITION_DEPENDENT` with alternative documented (second-half reversal/deity variant). Sensitivity to 0.5° boundaries validated.

No Phase 1 astronomical formulas (JD, ayanamsha, planet longitudes, ascendant, houses) were modified.

---

## Failures

No failures.

The single initial failure in test development (D9 Aries 3.333 vs 3.333333 boundary) was due to test expectation using approximate 3.333 not true `30/9`; corrected to 3.34 and re-passed.

---

## Tradition-Dependent Formulas

| Varga | Chosen Default | Alternative | Confidence |
|-------|----------------|-------------|------------|
| D10 | even start 9th | even start 8th | TRADITION_DEPENDENT |
| D16 | Movable Aries, Fixed Leo, Dual Sag | swapped fixed/dual | TRADITION_DEPENDENT |
| D20 | Movable Aries, Fixed Sag, Dual Leo | Aries/Leo/Sag | TRADITION_DEPENDENT |
| D27 | Elemental (Fire→Aries etc.) | Continuous from Aries | TRADITION_DEPENDENT |
| D45 | Same as D16 | swapped | TRADITION_DEPENDENT |
| D60 | Sequential same | Second-half reversal / deity count | TRADITION_DEPENDENT |
| D30 | cut 5/12/20 (even) | cut 5/10/18 (even) | VERIFIED but alternative noted |
| D2/D3/D4/D7/D9/D12/D24/D40 | — | minor Hora-lord etc. rare | VERIFIED |

All flagged in `ASTROLIFE_V2_VARGA_SPECIFICATION.md` §20 and `ASTROLIFE_V2_VARGA_AUDIT.md`.

---

## Remaining Uncertainty

- **Source authority**: No single universally authoritative digital table for D16/D20/D45 start-sign variants; choice based on BPHS translation by Sanjay Rath / PVR and JHora which are dominant but not unanimous. Flagged as `TRADITION_DEPENDENT` and exposed via `varga_method` override for future switching without code change.
- **D60 deity mapping**: 60 deity names (Ghora, Rakshasa etc.) not part of sign allocation and not tested in this phase — to be added as metadata in later phase if needed.
- **D30 cut 12 vs 10**: Both are attested; implemented cut 12 (even second slice 5–12) per PVR/JHora; alternative uses 5–10. The 2° difference is documented; switching would be a config option if demanded.

---

## Files

- **Created**: `ASTROLIFE_V2_VARGA_AUDIT.md`, `ASTROLIFE_V2_VARGA_SPECIFICATION.md`, this report
- **Created**: `backend/core/calculation/varga.py`
- **Created**: `backend/test_varga_phase2.py` (19k checks)
- **Modified**: `backend/core/calculation/config.py`, `backend/calculations.py`
- **Not modified**: `backend/core/calculation/pipeline.py`, `ephemeris.py`, `houses.py`, `nakshatra.py`, `time_utils.py`, frontend, yoga/dosha/shadbala/ashtakavarga/jaimini/AI

---

## How to Re-run

```bash
# Phase 1 regression (39 tests)
py backend/test_golden_chart_canonical.py

# Phase 2 comprehensive (19k+ checks)
py backend/test_varga_phase2.py

# Ad-hoc golden dump
py backend/compare_vargas.py
```

All must exit 0.

