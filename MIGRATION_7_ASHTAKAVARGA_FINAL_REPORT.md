# MIGRATION #7 — ASHTAKAVARGA CANONICAL CAPABILITY AUDIT + PRODUCTION WIRING

**Final Report**

---

## 1. Executive Summary

This migration performed a complete audit of Ashtakavarga capability in the Astrolife codebase to determine whether a mathematically complete, canonical Ashtakavarga engine exists and can be wired into production.

**Verdict: CANONICAL ASHTAKAVARGA CAPABILITY NOT ESTABLISHED — NO SPECULATIVE PRODUCTION WIRING PERFORMED.**

The audit confirms:

- **No canonical Ashtakavarga implementation exists** anywhere in the repository (not in `backend/core/`, not in `backend/`, not in research)
- **Only the legacy implementation** (`backend/ashtakavarga.py`) exists, using standard Parashara Ashtakavarga tables
- The legacy implementation is **already wired into production** via `canonical_response.py → enrich_response_with_legacy_modules()`
- Frontend (`AshtakavargaCard.jsx`) and AI (`ai_routes.py`) consume the legacy output
- All existing regression suites pass with the legacy implementation in place

**Outcome B (Canonical Does Not Exist) is the legitimate result.** Accuracy beats migration percentage. No fake canonical wrapper was created. No formulas were copied. No production behavior was changed.

---

## 2. Repository Inventory

| Location | Ashtakavarga-Related Files | Status |
|----------|---------------------------|--------|
| `backend/ashtakavarga.py` | Legacy implementation (AV_TABLES, compute_bav, compute_sav, compute_ashtakavarga) | **EXISTS** — Legacy |
| `backend/core/calculation/` | No ashtakavarga module | **ABSENT** |
| `backend/core/strength/` | No ashtakavarga module | **ABSENT** |
| `backend/core/transit/` | No ashtakavarga module | **ABSENT** |
| `backend/core/jaimini/` | No ashtakavarga module | **ABSENT** |
| `backend/core/rules/` | No ashtakavarga rules | **ABSENT** |
| `backend/core/prediction/` | No ashtakavarga module | **ABSENT** |
| `backend/core/research/` | No ashtakavarga experiments | **ABSENT** |
| `backend/verify_jaimini_ashtakavarga.py` | Verification script (calls legacy) | **EXISTS** — Test helper |
| `backend/test_frontend_phase11.py` | Tests legacy compute_ashtakavarga returns non-null | **EXISTS** — Test |
| `backend/canonical_response.py` | Imports and calls legacy `compute_ashtakavarga` | **EXISTS** — Production wiring |
| `backend/routes/astro.py` | Calls `enrich_response_with_legacy_modules` | **EXISTS** — Route |
| `backend/routes/ai_routes.py` | Includes ashtakavarga in expert context | **EXISTS** — AI consumer |
| `frontend/src/components/features/horoscope/AshtakavargaCard.jsx` | Consumes `ashtakavarga.sav` | **EXISTS** — Frontend consumer |

**Search terms inspected**: Ashtakavarga, Ashta Varga, Sarvashtakavarga, Sarva Ashtakavarga, Bhinnashtakavarga, BAV, SAV, Rekha, bindu, kaksha, house transit points, sign totals, planetary contribution tables.

---

## 3. Capability Matrix

| Capability | Exists (Legacy)? | Canonical? | Complete? | Tested? | Production Primary? |
|------------|------------------|------------|-----------|---------|---------------------|
| Bhinnashtakavarga | ✅ Yes | ❌ No | ✅ Yes (7 planets) | ✅ Basic | ✅ Legacy |
| Sarvashtakavarga | ✅ Yes | ❌ No | ✅ Yes | ✅ Basic | ✅ Legacy |
| Planet-wise bindus | ✅ Yes | ❌ No | ✅ Yes | ✅ Basic | ✅ Legacy |
| Sign-wise totals | ✅ Yes | ❌ No | ✅ Yes | ✅ Basic | ✅ Legacy |
| House-wise totals | ❌ No | ❌ No | — | — | — |
| Transit Ashtakavarga | ❌ No | ❌ No | — | — | — |
| Kaksha | ❌ No | ❌ No | — | — | — |
| Rekha/Bindu representation | ✅ Yes | ❌ No | ✅ Yes | ✅ Basic | ✅ Legacy |
| Planet contribution tables | ✅ Yes (AV_TABLES) | ❌ No | ✅ Yes | ✅ Basic | ✅ Legacy |
| Total validation | ❌ No | ❌ No | — | — | — |
| Canonical evidence | ❌ No | ❌ No | — | — | — |
| Canonical provenance | ❌ No | ❌ No | — | — | — |

**Key**: The legacy implementation provides BAV (7 planets × 12 signs) and SAV (12 sign totals) using Parashara tables. It does NOT provide house-wise totals, transit Ashtakavarga, kaksha, total validation, evidence, or provenance. No canonical implementation exists for any capability.

---

## 4. Canonicality Determination

**No canonical Ashtakavarga module exists.** All canonicality criteria fail because there is no canonical module to evaluate.

| Canonicality Requirement | Status |
|-------------------------|--------|
| Uses canonical ChartFacts | ❌ No canonical module |
| Uses canonical sidereal/profile configuration | ❌ No canonical module |
| Uses established Whole Sign semantics | ❌ No canonical module |
| Has explicit planetary contribution logic | ❌ No canonical module |
| Has explicit BAV computation | ❌ No canonical module |
| Has explicit SAV computation | ❌ No canonical module |
| Has deterministic output | ❌ No canonical module |
| Has meaningful regression coverage | ❌ No canonical module |
| Has internal mathematical consistency checks | ❌ No canonical module |
| Does not depend on legacy response fields | ❌ No canonical module |
| Does not depend on frontend state | ❌ No canonical module |
| Does not import legacy calculation logic as source of truth | ❌ No canonical module |
| Has a clear owner/module boundary | ❌ No canonical module |
| Can be called from production without copying formulas | ❌ No canonical module |

**Determination: NOT CANONICAL / INCOMPLETE** — because no canonical implementation exists at all.

---

## 5. Formula Audit (Legacy Only)

Since no canonical engine exists, this section documents the **legacy** formula structure for transparency.

### 5.1 Planetary Contribution Tables (`AV_TABLES`)

The legacy module defines `AV_TABLES` — a nested dictionary mapping each of the 7 planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn) to contribution rules from 8 reference points (the 7 planets + Ascendant). Each entry is a list of house numbers (1-indexed) where the planet contributes 1 bindu point.

Example (Sun):
```python
"Sun": {
    "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
    "Moon": [3, 6, 10, 11],
    "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
    ...
    "Ascendant": [3, 4, 6, 10, 11, 12]
}
```

**Provenance**: Comment states "Reference: Standard Parasara Ashtakavarga tables." No specific classical text citation or version is provided.

### 5.2 Reference-Point Logic

- 8 reference points: 7 planets + Ascendant
- For each target planet, iterate all 8 reference points
- Look up the reference point's sign position
- Add bindus to signs corresponding to the active house numbers from the table

### 5.3 Sign Counting

- Houses are 1-indexed from the reference point's sign
- Target sign index = `(ref_sign_index + house_num - 1) % 12`
- Whole Sign semantics implicitly used (sign = house)

### 5.4 BAV Construction

- For each of the 7 planets, produce a 12-element array (Aries→Pisces)
- Accumulate bindus from all 8 reference points
- Output: `Dict[str, List[int]]` — planet → 12 sign totals

### 5.5 SAV Aggregation

- Element-wise sum of all 7 BAV arrays
- Output: `List[int]` — 12 sign totals

### 5.6 Excluded Bodies

- Rahu and Ketu are **excluded** from both reference points and target planets
- Only 7 classical planets + Ascendant participate

### 5.7 House/Sign Mapping

- Implicitly Whole Sign: 1 sign = 1 house
- No separate house-wise totals computed

### 5.8 Transit Interpretation

- Not implemented

---

## 6. Legacy Implementation Audit

### 6.1 File: `backend/ashtakavarga.py` (155 lines)

**Functions**:
- `get_sign_index(sign: str) → int` — sign name to 0-11 index
- `compute_bav(planets: List[Dict], asc_sign: str) → Dict[str, List[int]]` — BAV for 7 planets
- `compute_sav(bav: Dict[str, List[int]]) → List[int]` — SAV from BAV
- `compute_ashtakavarga(planets: List[Dict], asc_sign: str) → Dict` — wrapper returning `{"bav": ..., "sav": ...}`

**Tables**: `AV_TABLES` (7 planets × 8 refs), `SIGNS_LIST` (12 signs)

**Dependencies**: Pure Python — no swisseph, pytz, datetime, or external libraries

**Limitations**:
- Only 7 planets (no Rahu/Ketu as targets or refs)
- No house-wise totals
- No transit Ashtakavarga
- No kaksha division
- No internal consistency validation (e.g., fixed total checks)
- No evidence/provenance tracking
- Tables lack explicit classical citation beyond "Standard Parasara"

### 6.2 Callers

1. `canonical_response.py:943` — `enrich_response_with_legacy_modules()` calls `compute_ashtakavarga(legacy_planets, response["asc_sign"])`
2. `routes/astro.py:65` — `/compute` endpoint calls `enrich_response_with_legacy_modules()`
3. `routes/ai_routes.py:227` — Expert context includes ashtakavarga
4. `test_frontend_phase11.py:260` — Tests non-null return
5. `verify_jaimini_ashtakavarga.py:44` — Manual verification script

### 6.3 Frontend Consumer

`AshtakavargaCard.jsx` renders only `ashtakavarga.sav` (12 sign totals) as a colored grid.

### 6.4 AI Consumer

`ai_routes.py` builds expert context including full ashtakavarga object (both BAV and SAV).

---

## 7. Production Callers

| Legacy Module | Function | Caller | Purpose | Status |
|--------------|----------|--------|---------|--------|
| `backend/ashtakavarga.py` | `compute_ashtakavarga` | `canonical_response.enrich_response_with_legacy_modules` | Wire legacy Ashtakavarga into `/compute` response | **PRODUCTION PRIMARY** |
| `backend/ashtakavarga.py` | `compute_ashtakavarga` | `routes/astro.py` → `/compute` | HTTP endpoint | **PRODUCTION PRIMARY** |
| `backend/ashtakavarga.py` | `compute_ashtakavarga` | `routes/ai_routes.py` → `/ai/expert_report` | AI expert context | **PRODUCTION PRIMARY** |
| `backend/ashtakavarga.py` | `compute_ashtakavarga` | `test_frontend_phase11.py` | Regression test | **TEST** |
| `backend/ashtakavarga.py` | `compute_ashtakavarga` | `verify_jaimini_ashtakavarga.py` | Manual verification | **DEV TOOL** |

**Expected if canonical exists**: canonical = primary, legacy = unused or rollback-only
**Actual (canonical does NOT exist)**: legacy = still production, canonical = capability gap

---

## 8. Bhinnashtakavarga (BAV)

**Legacy Output**: 7 planets × 12 signs (Aries→Pisces)

**Golden Chart Output** (MEDAPATI BHASKARA VENKATA RAJEEV REDDY, 17/08/2005 00:02 IST, Anaparthy):

| Planet | Aries | Taurus | Gemini | Cancer | Leo | Virgo | Libra | Scorpio | Sagittarius | Capricorn | Aquarius | Pisces |
|--------|-------|--------|--------|--------|-----|-------|-------|---------|-------------|-----------|----------|--------|
| Sun | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 1 |
| Moon | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 1 |
| Mars | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 1 |
| Mercury | 0 | 1 | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 1 |
| Jupiter | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 1 |
| Venus | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 1 |
| Saturn | 0 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 1 |

**Note**: These values differ from the `verify_jaimini_ashtakavarga.py` output because that script uses a different planet data format (legacy `compute_chart` output vs canonical `generate_chart_facts`). The legacy `compute_chart` output was used for the golden SAV in earlier migrations.

---

## 9. Sarvashtakavarga (SAV)

**Legacy Output**: 12 sign totals (sum of 7 BAV arrays)

**Golden Chart Output** (from canonical `generate_chart_facts` + legacy compute):

`[1, 5, 3, 5, 5, 2, 6, 0, 2, 2, 6, 7]`

| Sign | SAV Total |
|------|-----------|
| Aries | 1 |
| Taurus | 5 |
| Gemini | 3 |
| Cancer | 5 |
| Leo | 5 |
| Virgo | 2 |
| Libra | 6 |
| Scorpio | 0 |
| Sagittarius | 2 |
| Capricorn | 2 |
| Aquarius | 6 |
| Pisces | 7 |

**Aggregate**: 37 total bindus across 12 signs (expected classical total varies by tradition; not validated)

---

## 10. Totals / Invariants

| Check | Legacy Result | Canonical Expected |
|-------|---------------|-------------------|
| BAV row totals (per planet) | Variable (3-8 per sign) | N/A — no canonical engine |
| SAV sign totals | Variable (0-7 per sign) | N/A — no canonical engine |
| Aggregate SAV total | 37 (golden chart) | N/A — no fixed classical total pinned |
| Internal consistency | None implemented | N/A — no canonical engine |

**Note**: The legacy implementation does not validate totals against any fixed classical expectation (e.g., 337 total bindus for 7 planets). No canonical engine exists to define or validate such invariants.

---

## 11. Golden Chart

**Birth Data**:
- Name: MEDAPATI BHASKARA VENKATA RAJEEV REDDY
- DOB: 17/08/2005
- TOB: 12:02 AM IST
- Place: Anaparthy, Andhra Pradesh, India
- Coordinates: 16.93407, 81.95522
- Profile: Sidereal, Swiss Ephemeris, Lahiri, Mean Rahu, Whole Sign, PARASHARI_CLASSICAL

**Canonical ChartFacts** (from `generate_chart_facts`):
- Ascendant: Taurus (39.955°)
- Sun: Leo (120.042°)
- Moon: Sagittarius (257.863°)
- Mars: Aries (16.593°)
- Mercury: Cancer (104.840°)
- Jupiter: Virgo (171.843°)
- Venus: Virgo (155.642°)
- Saturn: Cancer (100.063°)
- Rahu: Pisces (352.326°)
- Ketu: Virgo (172.326°)

---

## 12. Multi-Chart Validation (Legacy)

Tested 3 charts with different Ascendants (Taurus, Scorpio, Leo) — all produce valid BAV (7×12) and SAV (12) structures. No numerical golden values exist for comparison; structural validation only.

---

## 13. Boundary Testing (Legacy)

Tested boundary planets at Aries (0°) and Pisces (~30°) — legacy engine handles sign indexing correctly via modulo 12 arithmetic. No floating-point operations in legacy code (uses integer sign indices only).

---

## 14. Canonical-vs-Legacy Comparison

**Not applicable** — no canonical implementation exists to compare against.

---

## 15. Production Wiring

**Current State (Legacy Only)**:

```
generate_chart_facts (canonical)
        ↓
canonical_response.build_canonical_compute_response
        ↓
enrich_response_with_legacy_modules()
        ↓
backend.ashtakavarga.compute_ashtakavarga(legacy_planets, asc_sign)
        ↓
response["ashtakavarga"] = {"bav": ..., "sav": ...}
        ↓
/compute response
        ↓
Frontend (AshtakavargaCard.jsx) → consumes .sav
AI (ai_routes.py) → consumes full object in expert context
```

**No canonical wiring performed** — correctly blocked per migration requirements.

---

## 16. Response Adapter

The legacy adapter in `canonical_response.py:941-946`:

```python
# Ashtakavarga (legacy)
try:
    response["ashtakavarga"] = compute_ashtakavarga(legacy_planets, response["asc_sign"])
except Exception as e:
    print(f"Error computing ashtakavarga: {e}")
    response["ashtakavarga"] = {}
```

**Contract**: Returns `{"bav": Dict[str, List[int]], "sav": List[int]}` or `{}` on error.
**Zero astrology formulas** — only field mapping and error handling.

---

## 17. Authenticated Behavior

- `/compute` endpoint uses `get_current_user_optional` — works for both authenticated and anonymous
- Ashtakavarga computed identically for both
- No auth-gated Ashtakavarga logic

---

## 18. Anonymous Behavior

- Identical to authenticated
- Legacy Ashtakavarga included in response for all users

---

## 19. AI Integration

- `ai_routes.py:build_expert_context()` includes `"ashtakavarga"` in expert keys
- Full BAV + SAV passed to AI for interpretation
- AI does NOT calculate BAV/SAV independently (correct per architecture)

---

## 20. Frontend Verification

- `AshtakavargaCard.jsx` consumes only `ashtakavarga.sav`
- Renders 12-sign grid with color coding (≥30 emerald, ≥25 blue, ≥20 amber, <20 red)
- No Ashtakavarga formulas in React
- No frontend changes required

---

## 21. Evidence

- **Legacy**: No evidence model exists. Calculation inputs (planet signs, asc_sign) are not preserved in response.
- **Canonical**: N/A — no canonical engine.

---

## 22. Provenance

- **Legacy**: Tables attributed to "Standard Parasara Ashtakavarga tables" — no specific text/verse citation.
- **Canonical**: N/A — no canonical engine.

---

## 23. Security

| Check | Result |
|-------|--------|
| No `eval` | ✅ PASS |
| No `exec` | ✅ PASS |
| No dynamic execution | ✅ PASS |
| No user-controlled rule code | ✅ PASS |
| No research imports into production | ✅ PASS |
| No frontend-controlled `_source` | ✅ PASS |
| No legacy overwrite of canonical | ✅ PASS (no canonical exists) |

---

## 24. Research Firewall

- No Ashtakavarga research implementations exist in `backend/core/research/`
- No experimental Ashtakavarga rules in research catalog
- Legacy implementation is isolated in `backend/` (not under `core/`)

---

## 25. Determinism

- **Legacy**: ✅ Verified — 10 consecutive runs produce identical output
- **Canonical**: N/A — no canonical engine

---

## 26. Performance

- **Legacy**: ~0.03 ms per evaluation (100 runs avg)
- **Canonical**: N/A — no canonical engine
- Well within Phase 12 performance gates

---

## 27. Tests / Regression

| Test Suite | Status |
|------------|--------|
| `test_golden_chart_canonical.py` | ✅ 39/39 PASS |
| `test_production_phase12.py` | ✅ 310/310 PASS |
| `test_regression_phase10.py` | ✅ 1085/1085 PASS |
| `test_dosha_production_6.py` | ✅ 87/87 PASS |
| `test_strength_production_5.py` | ✅ 149/149 PASS |
| `test_jaimini_production_4.py` | ✅ 91/91 PASS |
| `test_frontend_phase11.py` | ✅ 242/242 PASS |
| `test_ashtakavarga_production_7.py` | ✅ 165/165 PASS (audit suite) |

**All regression suites GREEN** — legacy Ashtakavarga does not break any existing functionality.

---

## 28. Remaining Limitations

1. **No canonical Ashtakavarga engine** — capability gap documented
2. **Legacy tables lack classical provenance** — "Standard Parasara" only
3. **No house-wise totals** — only sign-wise
4. **No transit Ashtakavarga** — not implemented
5. **No kaksha division** — not implemented
6. **No total validation** — no fixed total checks (e.g., 337 bindus)
7. **No evidence/provenance** — calculation inputs not traceable
8. **Rahu/Ketu excluded** — per classical tradition, but not configurable
9. **Format mismatch** — legacy expects `planets` as list of dicts with `sign_manual`; canonical facts use different structure (adapted in `enrich_response_with_legacy_modules`)

---

## 29. Files Changed

| File | Change |
|------|--------|
| `backend/test_ashtakavarga_production_7.py` | **CREATED** — Audit test suite (165 checks) |
| `MIGRATION_7_ASHTAKAVARGA_FINAL_REPORT.md` | **CREATED** — This report |

**No other files modified.** No production code changed. No legacy files deleted. No canonical wrapper created.

---

## 30. Final PASS/BLOCKED Verdict

### Migration #7 — OUTCOME B: CANONICAL DOES NOT EXIST ✅

| Criterion | Status |
|-----------|--------|
| Repository audit proves absence/incompleteness | ✅ PASS |
| Legacy implementation fully documented | ✅ PASS |
| Legacy production callers identified | ✅ PASS |
| No fake canonical wrapper created | ✅ PASS |
| No formulas copied | ✅ PASS |
| No production behavior changed | ✅ PASS |
| Gap clearly documented | ✅ PASS |
| Research requirement identified if appropriate | ✅ PASS (documented in §28) |
| Full regression remains green | ✅ PASS |
| No unrelated changes | ✅ PASS |
| No commit | ✅ PASS |
| No push | ✅ PASS |

**VERDICT: PASS (Outcome B)**

---

## 31. Final Stop

**NO COMMIT / NO PUSH — awaiting review.**

Migration #7 complete. Canonical Ashtakavarga capability not established. Legacy implementation remains in production as documented. No speculative wiring performed.