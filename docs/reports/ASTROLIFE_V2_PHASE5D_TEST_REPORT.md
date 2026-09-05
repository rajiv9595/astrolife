# ASTROLIFE V2 — PHASE 5D: TEST REPORT

**Date:** 2026-09-04  
**Status:** ALL TESTS PASSED — ZERO REGRESSIONS  
**Version:** 2.0.0  
**Phase:** 5D — Jaimini Foundation & Deterministic Fact Engine  

---

## 1. Test Summary

| Metric | Count | Status |
| :--- | :--- | :--- |
| **Phase 5D Jaimini Tests** | **143 / 143** | **PASSED (100%)** |
| Phase 1 Regression (Golden Chart) | 39 / 39 | PASSED |
| Phase 2 Regression (D1 to D60 Vargas) | 19,692 / 19,692 | PASSED |
| Phase 3 Regression (Transit Precision & Events) | 788 / 788 | PASSED |
| Phase 3 Regression (Panchanga Engine) | 423 / 423 | PASSED |
| Phase 4B Regression (Strength Boundary Tests) | 87 / 87 | PASSED |
| Phase 5A Regression (Deterministic Rule Engine) | 185 / 185 | PASSED |
| Phase 5B Regression (Parashari Yogas) | 355 / 355 | PASSED |
| Phase 5C Regression (Classical Doshas) | 157 / 157 | PASSED |
| **Total Verified Regressions** | **21,869 / 21,869** | **PASSED (100%)** |

---

## 2. Phase 5D Test Breakdown

### 2.1 Package Structure & Imports (3 tests)
* `JaiminiCalculationProfile` imports and instantiates cleanly.
* `generate_jaimini_facts` pipeline entry point available.
* `JaiminiFacts` composite container model validated.

### 2.2 Chara Karakas — 7-Karaka Method (10 tests)
* Evaluates intra-sign degrees strictly (not continuous longitude).
* Verifies descending ranking: AK (Jupiter at 28.5°), AmK (Moon at 25.2°), BK (Sun at 20.1°), MK (Mars at 15.7°), PK (Saturn at 11.3°), GK (Mercury at 6.8°), DK (Venus at 1.2°).
* Verifies Pitrukaraka (PiK) and Rahu are strictly excluded in 7-karaka scheme.
* Verifies presence of step-by-step mathematical evidence.

### 2.3 Chara Karakas — 8-Karaka Method & Rahu Conventions (6 tests)
* 8-Karaka Direct method: Rahu (29.9°) assigned to Atmakaraka; Pitrukaraka assigned to Mars (15.7°).
* 8-Karaka Inverse method: Rahu retrograde intra-sign degree ($30^\circ - 29.9^\circ = 0.1^\circ$) becomes Darakaraka; Jupiter becomes Atmakaraka.
* Verifies exact 8-karaka ordering.

### 2.4 Deterministic Tie-Breaking (3 tests)
* Evaluates synthetic chart with Sun and Moon at identical intra-sign degree (15.0000000°).
* Resolves tie deterministically using canonical Graha precedence (Sun $\succ$ Moon).
* Records explicit tie resolution evidence.

### 2.5 Jaimini Rashi Drishti — Exhaustive 12-Sign Matrix (48 tests)
* Movable signs (Aries, Cancer, Libra, Capricorn): aspect all Fixed signs except adjacent (2nd sign).
* Fixed signs (Taurus, Leo, Scorpio, Aquarius): aspect all Movable signs except adjacent (12th sign).
* Dual signs (Gemini, Virgo, Sagittarius, Pisces): aspect all other 3 Dual signs except self.
* Non-aspected verification: exactly 8 non-aspected signs verified for all 12 signs.
* 100% mutual symmetry verified across all 144 sign pairs ($12 \times 12$).
* Planetary Rashi Drishti propagation from occupied signs verified.

### 2.6 Arudha Engine & Classical 10th-House Exceptions (12 tests)
* Normal projection case: Aries Lagna, Mars in Gemini (3rd) $\to$ raw projection in Leo (5th).
* Exception Case 1 (1st house fall): Mars in 1st $\to$ raw projection in Aries $\to$ shifted 10 houses forward to Capricorn.
* Exception Case 2 (7th house fall): Mars in 4th $\to$ raw projection in Libra (7th) $\to$ shifted to Cancer (4th from Lagna / 10th from 7th).
* Exception Case 3 (1st house fall): Mars in 7th $\to$ raw projection in Aries $\to$ shifted to Capricorn.
* Exception Case 4 (7th house fall): Mars in 10th $\to$ raw projection in Libra $\to$ shifted to Cancer.

### 2.7 All 12 Arudha Padas (A1 to A12) & Upapada (39 tests)
* Generates all 12 Arudha Padas with house numbers, source signs, lords, distances, raw projections, exceptions, and final signs.
* Upapada Lagna (UL / A12): derived strictly from 12th house with dedicated evidence.

### 2.8 Karakamsha & Swamsa Facts (4 tests)
* Identifies Atmakaraka (Jupiter) and queries canonical D9 Navamsha sign (Sagittarius).
* Distinctly separates Karakamsha sign from Swamsa Navamsha Lagna sign.
* Zero recalculation of D9 or ephemerides.

### 2.9 Pipeline & Context Integration (6 tests)
* Full pipeline execution with provenance and metadata assembly.
* `JaiminiContext` property accessors (`atmakaraka`, `does_sign_aspect`, etc.).

### 2.10 Golden Chart Integration & Snapshot (5 tests)
* Evaluates canonical Golden Chart (Aug 17, 2005 00:02 AM, Anaparthy).
* Planetary degrees: Jupiter (21.84° in Virgo) $\to$ AK; Moon (17.86° in Sagittarius) $\to$ AmK; Sun (0.04° in Leo) $\to$ DK.
* Karakamsha AK verified as Jupiter.
* Snapshot written to `backend/golden_jaimini_snapshot.json`.

### 2.11 Pure Determinism & Reproducibility (1 test)
* 100 consecutive executions produce bit-for-bit identical JSON representations.

### 2.12 No-AI & No-Prediction Guard (6 tests)
* Static analysis verifies zero AI/LLM library imports or prediction tokens in `core/jaimini/`.

---

## 3. Tradition-Dependent Decisions Documented

1. **7 vs 8 Karakas**: Default profile uses classical 7-Karaka method (Rahu excluded). 8-Karaka method fully supported via `KarakaMethod.EIGHT_KARAKA`.
2. **Rahu Retrograde Degree**: Supports `EXCLUDED`, `DIRECT_LONGITUDE` ($L \pmod{30}$), and `INVERSE_LONGITUDE` ($30 - (L \pmod{30})$).
3. **Dual Lordships**: Classical single lords (Mars for Scorpio, Saturn for Aquarius) used by default (`CoLordMethod.SINGLE_LORD_CLASSICAL`).
4. **10th House Arudha Exceptions**: Method label `CLASSICAL_ARUDHA_STANDARD` (profile enum `PARASHARI_JAIMINI_STANDARD`) implemented with explicit shift to 10th house from source for 1st-house falls, and 10th from 7th (4th from source) for 7th-house falls. Exact verse references are UNVERIFIED — no Adhyaya/verse numbers are claimed.
5. **Swamsa vs Karakamsha**: Explicitly differentiated in data models (`karakamsha_sign` for AK in D9; `swamsa_navamsha_lagna_sign` for D9 Lagna).

---

## 5. Phase 5D-H Hardening Pass (2026-09-04)

### 5.1 Arudha evidence audit
* Independent reference reimplementation cross-checked against
  `calculate_single_arudha` over all 144 house-1 source-sign/lord-position
  permutations: **144/144 match** on distance, raw projection, exception, and
  final sign (24 × 1st-house exception, 24 × 7th-house exception, 96 × none).
* All A1–A12 golden-chart padas re-audited field-by-field
  (source/ lord/ lord-sign/ distance/ raw/ exception/ final): **12/12
  evidence-consistent**, no mismatches.
* Golden A1: Taurus → Venus in Virgo → 5-house inclusive count (4 signs) →
  raw Capricorn → exception NONE → final Capricorn. The engine never produced a
  "raw Pisces" intermediate; calculation == evidence == final. No arithmetic
  fix was required.

### 5.2 Exception validation
* 1st-house fall (lord in 1st/7th from source) → 10th-from-source: validated.
* 7th-house fall (lord in 4th/10th from source) → 4th-from-source: validated.
* No-exception case: raw projection unchanged: validated.
* `NO_EXCEPTIONS` profile path verified: raw == final, no exception recorded.

### 5.3 Chara Karaka / Rahu / Rashi Drishti audits
* Golden ordering confirmed on intra-sign degrees (`sidereal % 30` equals stored
  sign degrees): Jupiter 21.8426 (AK) > Moon 17.8628 (AmK) > Mars 16.5931 (BK)
  > Mercury 14.8396 (MK) > Saturn 10.0625 (PK) > Venus 5.6418 (GK) > Sun
  0.0419 (DK). Result unchanged — implementation was correct.
* 7-Karaka excludes Rahu and PiK; 8-Karaka DIRECT uses 22.3264° and INVERSE
  uses 7.6736° for golden Rahu — all explicit profile choices, never mixed.
* Rashi Drishti: 12/12 signs aspect exactly 3; 8 non-aspected each; 100%
  mutual symmetry over 144 pairs; planet→planet propagation derives strictly
  from occupied signs. `rashi_drishti.py` imports no Parashari aspect code.

### 5.4 Source-label honesty
* `JaiminiProvenance.confidence`: `VERIFIED_CANONICAL` → `UNVERIFIED`;
  specific Adhyaya/Pada citations removed from `source_texts`; added
  `tradition = JAIMINI`, `method = CLASSICAL_ARUDHA_STANDARD`,
  `source_reference = UNVERIFIED` to provenance and `JaiminiFacts.metadata`
  (plus `JaiminiCalculationProfile.source_reference`). No verse numbers claimed.

### 5.5 Golden snapshot
* `backend/golden_jaimini_snapshot.json` regenerated by the engine (via
  `test_jaimini_phase5d.py` suite 10): AL = Capricorn, UL = Capricorn
  (engine-derived, equals A12; the 1st-house exception applies), Karakamsha =
  Cancer, full Chara Karaka ordering preserved. Not hand-edited.

### 5.6 Determinism
* 100-iteration bit-for-bit check (suite 11) passes; provenance/metadata
  re-verified deterministic across runs (no timestamps or random IDs).

### 5.7 Full regression table (all suites actually executed this pass)

| Suite | Runner | Result |
| :--- | :--- | :--- |
| Phase 1 (Golden Chart canonical) | `backend/test_golden_chart_canonical.py` | 39 / 39 |
| Phase 2 (D1–D60 Vargas) | `backend/test_varga_phase2.py` | 19,692 / 19,692 |
| Phase 3 Panchanga | `backend/test_panchanga_phase3.py` | 423 / 423 |
| Phase 3 Transit | `backend/test_transit_phase3.py` | 788 / 788 |
| Phase 3 Dasha | `backend/test_dasha_phase3.py` (from repo root*) | 81,283 / 81,283 |
| Phase 3 Dynamic State | `backend/test_dynamic_phase3.py` (from repo root*) | 27 / 27 |
| Phase 4B (Strength boundaries) | `backend/test_strength_phase4b.py` | 87 / 87 |
| Phase 5A (Rule engine) | `backend/test_rule_engine_phase5a.py` | 185 / 185 |
| Phase 5B (Parashari Yogas) | `backend/test_parashari_yogas_phase5b.py` | 355 / 355 |
| Phase 5C (Doshas) | `backend/test_doshas_phase5c.py` | 157 / 157 |
| Phase 5D (Jaimini incl. 5D-H) | `backend/test_jaimini_phase5d.py` | 143 / 143 |
| **Executed total** | | **103,179 / 103,179** |

\* Pre-existing path issue: the Dasha and Dynamic suites use cwd-relative
`backend/...` paths and fail with `FileNotFoundError` when invoked from
`backend/`; they pass when invoked from the repo root. No code was changed for
this — invocation directory is recorded here.

Exact arithmetic: 39 + 19,692 + 423 + 788 + 81,283 + 27 + 87 + 185 + 355 +
157 + 143 = 103,179. Carried over without re-execution (no standalone runner):
Phase 4 Strength Golden 7 / 7 (from `ASTROLIFE_V2_PHASE4_TEST_REPORT.md`),
giving a grand total of 103,186 / 103,186 including carried-over results.
No suite was double-counted; no executed suite was omitted.

---

## 4. Known Limitations & Scope Boundaries

1. **No Jaimini Yogas**: Deferred to future Jaimini Rule Engine phase.
2. **No Jaimini Dashas**: Chara Dasha / Sthira Dasha deferred to future dasha phases.
3. **No Predictions**: Marriage, career, and event timing predictions are strictly out of scope.
