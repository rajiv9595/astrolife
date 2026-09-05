# ASTROLIFE V2 — PHASE 5D: JAIMINI REPOSITORY AUDIT

**Date:** 2026-09-04  
**Scope:** Pre-implementation audit for Phase 5D — Jaimini Foundation & Deterministic Fact Engine  
**Status:** Audit Complete — Ready for Architecture & Implementation

---

## 1. Executive Summary

This audit examines the existing codebase to identify all Jaimini-related calculations, models, routes, test suites, and frontend dependencies. The objective is to design a clean, modular, deterministic Jaimini fact layer in `backend/core/jaimini/` that strictly consumes canonical `ChartFacts` and `VargaFacts` without recalculating astronomical or divisional positions, and without breaking any legacy endpoints or UI components.

---

## 2. Inventory of Existing Jaimini Code

### 2.1 Legacy Calculation Modules
* **File:** `backend/jaimini.py`
  * **Functions:**
    * `calculate_chara_karakas(planets)`: Basic 7-karaka ranking based on `degree_in_sign_manual`. Sorts descending. Hardcoded to 7 planets.
    * `calculate_arudha_padas(planets, asc_sign)`: Calculates Padas 1–12 using basic distance and 1st/7th house exception rules.
    * `compute_jaimini_system(planets, asc_sign)`: Wrapper returning `{"chara_karakas": ..., "arudha_padas": ...}`.
  * **Status:** Legacy prototype. Lacks structured evidence, provenance, 8-karaka method, Rahu conventions, tie handling, Karakamsha, Rashi Drishti, and Pydantic validation.

### 2.2 Verification and Diagnostic Scripts
* **File:** `backend/verify_jaimini_ashtakavarga.py`
  * Imports `compute_jaimini_system` from `backend.jaimini` and runs sample calculation on Aug 17, 2005 chart.
  * Must continue to pass or be updated to maintain backward compatibility.

### 2.3 Route Endpoints
* **File:** `backend/routes/astro.py`
  * Line 11: `from backend.jaimini import compute_jaimini_system`
  * Line 84: Calls `jaimini_data = compute_jaimini_system(chart_data["planets"], chart_data["asc_sign"])`
  * Line 140: Emits `"jaimini": jaimini_data` in response dictionary.
  * **Requirement:** Must maintain identical top-level key schema (`chara_karakas`, `arudha_padas`) for API consumers while enhancing the underlying engine.

### 2.4 Frontend Components
* **File:** `frontend/src/pages/HoroscopePage.jsx`
  * Line 509: `<JaiminiCard jaimini={chartData.jaimini} />`
* **File:** `frontend/src/components/features/horoscope/JaiminiCard.jsx`
  * Consumes `jaimini.chara_karakas` (dictionary mapping Karaka name to Planet name) and `jaimini.arudha_padas` (dictionary mapping house number 1–12 to Sign name).
  * **Requirement:** Frontend must not be modified or broken; backward compatible dictionary views must be preserved.

### 2.5 Rule Engine & Strength References
* **File:** `backend/core/rules/enums.py`
  * Declares `RuleCategory` and `RuleTradition.JAIMINI`.
* **File:** `backend/core/rules/provenance.py`
  * Declares classical provenance sources including `BPHS_JAIMINI_SUTRAS` and `JAIMINI_UPADESHA_SUTRAS`.
* **Note:** Phase 5D only builds the **Fact Layer** (`JaiminiFacts`). No Jaimini rules, yogas, or dasha predictions are implemented in Phase 5D.

---

## 3. Reusable Utilities & Existing Canonical Facts

1. **`backend/core/calculation/models.py` (`ChartFacts`)**:
   * Provides validated sidereal longitudes for all 9 planets (`Sun`, `Moon`, `Mars`, `Mercury`, `Jupiter`, `Venus`, `Saturn`, `Rahu`, `Ketu`) and `Ascendant`.
   * Provides `SignPosition` (sign id 1–12, sign name, degree in sign).
   * **Rule:** Jaimini engine consumes `ChartFacts` directly. No recalculation of ayanamsha or JD.

2. **`backend/core/calculation/varga.py` (`VargaPosition`, `calculate_all_vargas`)**:
   * Provides validated `D9` Navamsha signs and degrees.
   * **Rule:** Karakamsha consumes `varga_facts["planets"][ak]["D9"]`. No recalculation of D9.

3. **Sign and Lord Mapping Constants**:
   * 12 Signs: `Aries`, `Taurus`, `Gemini`, `Cancer`, `Leo`, `Virgo`, `Libra`, `Scorpio`, `Sagittarius`, `Capricorn`, `Aquarius`, `Pisces`.
   * Sign Lords: `Aries: Mars`, `Taurus: Venus`, `Gemini: Mercury`, `Cancer: Moon`, `Leo: Sun`, `Virgo: Mercury`, `Libra: Venus`, `Scorpio: Mars` (single lord classical), `Sagittarius: Jupiter`, `Capricorn: Saturn`, `Aquarius: Saturn` (single lord classical), `Pisces: Jupiter`.

---

## 4. Duplicate & Legacy Logic Analysis

* `backend/jaimini.py` contains simplified inline pada logic without rich structured provenance or multi-method support.
* **Migration Strategy:**
  1. Build the robust, comprehensive, modular package in `backend/core/jaimini/`.
  2. Implement `backend/core/jaimini/pipeline.py` with `generate_jaimini_facts()`.
  3. Keep `backend/jaimini.py` as a backward-compatibility wrapper around the new core engine or retain its signature so that existing legacy callers (`routes/astro.py`, `verify_jaimini_ashtakavarga.py`) continue operating seamlessly without disruption.

---

## 5. Files That Must Remain Untouched

* All Phase 1 calculation engines (`calculations.py`, `ephemeris.py`, `nakshatra.py`, `panchanga.py`).
* All Phase 2 varga algorithms (`varga.py`).
* All Phase 3 dasha and transit modules (`dasha.py`, `dynamic.py`, `panchanga_advanced.py`).
* All Phase 4 / 4B strength engines (`strength/`, `shadbala.py`, `maitri.py`).
* All Phase 5A rule engine core (`core/rules/evaluator.py`, `conditions.py`, `context.py`).
* All Phase 5B Parashari yoga modules (`core/rules/parashari/`).
* All Phase 5C Dosha modules (`core/rules/doshas/`).

---

## 6. Risks & Mitigation

| Risk | Mitigation |
| :--- | :--- |
| **Tradition divergence in Chara Karakas (7 vs 8 karakas)** | Support explicit `JaiminiCalculationProfile` with `karaka_method=SEVEN_KARAKA` / `EIGHT_KARAKA`. Never hardcode a single tradition silently. |
| **Rahu retrograde intra-sign degree convention** | Support configurable `RahuKarakaMethod` (`EXCLUDED`, `DIRECT_LONGITUDE`, `INVERSE_LONGITUDE`) and document with unit tests. |
| **Floating point ties in planetary longitudes** | Implement deterministic epsilon tolerance (`1e-7`) and deterministic secondary tie-breaking with explicit evidence tracking. |
| **Rashi Drishti contamination from Parashari Graha Drishti** | Pure sign-based aspect lookup table cleanly segregated from Parashari aspect calculations. |
| **Arudha Pada exception ambiguities** | Formulate exact classical 10th-house exception rules for 1st and 7th house projections with step-by-step evidence. |
| **Swamsa vs Karakamsha conflation** | Distinguish D9 Lagna (`swamsa_navamsha_lagna`) and AK Navamsha (`karakamsha_sign`) with separate fields and documentation. |

---

## 7. Next Steps

1. Create implementation plan artifact `implementation_plan.md`.
2. Await user confirmation / proceed with execution upon approval.

---

## 8. Phase 5D-H Hardening Findings (2026-09-04, post-implementation audit)

1. **Arudha "raw Pisces" inconsistency — NOT PRESENT in engine.** The reported
   `distance 5 → raw Pisces (11th) → Capricorn` derivation does not occur in
   `backend/core/jaimini/arudha.py`: for golden A1 (Taurus, Venus in Virgo)
   the engine computes `distance_signs = 4` (5 houses inclusive),
   `raw = Capricorn`, `exception = NONE`, `final = Capricorn`, and the
   evidence strings are built from those same variables (one source of truth).
   Verified over all 144 permutations plus all A1–A12 golden padas with zero
   mismatches. No arithmetic fix required; the hardening value was the
   independent proof and the terminology clarification (inclusive house-count
   vs 0-indexed sign distance).
2. **UL expectation corrected to engine truth.** The hardening brief suggested
   UL = Leo, but the engine derives UL = Capricorn for the golden chart
   (12th-house Aries, Mars in Aries, 1st-house exception → 10th = Capricorn),
   identical to A12 as the `UL == A12` invariant requires. Leo corresponds to
   A2/A6, not A12. Nothing was hard-coded; the engine result stands.
3. **Source-label overclaim fixed.** `JaiminiProvenance` previously claimed
   `confidence = VERIFIED_CANONICAL` with Adhyaya/Pada-specific citations.
   Now: `tradition = JAIMINI`, `method = CLASSICAL_ARUDHA_STANDARD`,
   `source_reference = UNVERIFIED`, `confidence = UNVERIFIED`, with
   section-specific citations removed. Same fields mirrored into
   `JaiminiFacts.metadata` and `JaiminiCalculationProfile.source_reference`.
4. **Chara Karaka / Rahu / Drishti confirmed correct** (intra-sign ranking,
   explicit Rahu conventions, sign-only aspects with no shared Parashari
   calculation path). Golden ordering unchanged.
5. **Regression:** 103,179 / 103,179 actually executed this pass (table in the
   Phase 5D test report §5.7); 7 carried-over Phase 4 Strength Golden checks
   were not re-executed (no standalone runner) and are marked as such.
6. **No new features added.** No Yogas, Dashas, predictions, AI, or
   interpretations. STOP after Phase 5D-H observed.
