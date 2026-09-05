# ASTROLIFE V2 — PHASE 5E: TEST REPORT

**Date:** 2026-09-04
**Status:** ALL TESTS PASSED — ZERO REGRESSIONS
**Engine version:** 1.0.0
**Runner:** `backend/test_jaimini_yogas_phase5e.py`

---

## 1. Phase 5E Results: 62 / 62 explicit checks

| Section | Checks | Result |
| :--- | :--- | :--- |
| 1. Catalogue integrity (12 IDs, UNVERIFIED refs, origin labels, no fabricated citations) | 10 | PASS |
| 2. Karaka rules (positive/negative/tie-boundary/unrelated, DK modes) | 12 | PASS |
| 3. Rashi Drishti rules (golden mutual, adjacent negative, engine cross-checks) | 5 | PASS |
| 4. Arudha/AL/UL rules (independent occupant/lord/mode math) | 4 | PASS |
| 5. Karakamsha/Swamsa separation + synthetic interchange traps | 8 | PASS |
| 6. 7k/8k isolation (Rahu-AK flow-through, mismatch ValueError, PiK safe) | 5 | PASS |
| 7. Exhaustive sweeps (12 asc, 144 pairs, dhana modes, A7-UL, D9 math) | 6 | PASS |
| 8. Golden chart + engine-generated snapshot | 6 | PASS |
| 9. Determinism (50 iterations bit-for-bit) | 1 | PASS |
| 10. Guards (no-prediction, no-astronomy, aspect purity, legacy API, subset) | 5 | PASS |

Systematic volumes behind the aggregated checks: 144 AK/AmK sign pairs × 2
rules with independent reference (288 evaluations, conjunction/mutual
disjointness enforced); 12 ascendants × full 12-rule evaluation with
formed↔status consistency and UNASSESSED quality (5 sweep sections);
50 determinism iterations; snapshot round-trip.

Golden formation: 3/12 —
`JAI.ARUDHA.AL_LORD_KENDRA_TRINE` (Saturn in Cancer, 7th from Capricorn AL),
`JAI.DRISHTI.AK_AMK_MUTUAL` (Virgo↔Sagittarius duals),
`JAI.KARAKAMSHA.BENEFIC_OCCUPANCY` (Jupiter in Cancer D9).
Snapshot: `backend/golden_jaimini_yoga_snapshot.json` (engine-written, never
hand-edited).

## 2. Complete Regression Accounting (all EXECUTED this pass except as noted)

| Suite | Runner | Result | Status |
| :--- | :--- | :--- | :--- |
| Phase 5E (Jaimini yogas) | `backend/test_jaimini_yogas_phase5e.py` | 62 / 62 | EXECUTED |
| Phase 5D (Jaimini foundation) | `backend/test_jaimini_phase5d.py` | 143 / 143 | EXECUTED |
| Phase 1 (Golden canonical) | `backend/test_golden_chart_canonical.py` | 39 / 39 | EXECUTED |
| Phase 2 (Vargas) | `backend/test_varga_phase2.py` | 19,692 / 19,692 | EXECUTED |
| Phase 3 Panchanga | `backend/test_panchanga_phase3.py` | 423 / 423 | EXECUTED |
| Phase 3 Transit | `backend/test_transit_phase3.py` | 788 / 788 | EXECUTED |
| Phase 3 Dasha | `backend/test_dasha_phase3.py` (repo root*) | 81,283 / 81,283 | EXECUTED |
| Phase 3 Dynamic | `backend/test_dynamic_phase3.py` (repo root*) | 27 / 27 | EXECUTED |
| Phase 4B (Strength bounds) | `backend/test_strength_phase4b.py` | 87 / 87 | EXECUTED |
| Phase 5A (Rule engine) | `backend/test_rule_engine_phase5a.py` | 185 / 185 | EXECUTED |
| Phase 5B (Parashari yogas) | `backend/test_parashari_yogas_phase5b.py` | 355 / 355 | EXECUTED |
| Phase 5C (Doshas) | `backend/test_doshas_phase5c.py` | 157 / 157 | EXECUTED |
| **Executed total** | | **103,241 / 103,241** | |
| Phase 4 Strength Golden | (no standalone runner) | 7 / 7 | CARRIED FORWARD from Phase 4 report |
| **Grand total** | | **103,248 / 103,248** | |

\* Pre-existing path quirk: Dasha/Dynamic suites use cwd-relative
`backend/...` paths; invoked from repo root. Nothing excluded silently.

Arithmetic: 62+143+39+19,692+423+788+81,283+27+87+185+355+157 = 103,241;
+7 carried = 103,248. No double-counting, no omissions.

## 3. File Discipline

Created: `backend/core/jaimini/rules/` (10 files: `__init__`, `profile`,
`models`, `predicates`, `catalogue`, `karaka_yogas`, `drishti_yogas`,
`arudha_yogas`, `karakamsha_yogas`, `pipeline`), 
`backend/test_jaimini_yogas_phase5e.py`,
`backend/golden_jaimini_yoga_snapshot.json`, 4 docs (audit, specification,
test report, catalogue). Modified: none of the accepted layers. Deleted:
none. (`backend/app.py` / `calculations.py` diffs pre-date Phase 5E.)

## 4. Limitations

Quality UNASSESSED for all rules; cancellation only structural (karaka tie);
D9-scope rules take no drishti mitigation; co-lord variants, Argala,
dignity-based karaka rules, dashas, and timing explicitly excluded (catalogue
doc §Excluded).
