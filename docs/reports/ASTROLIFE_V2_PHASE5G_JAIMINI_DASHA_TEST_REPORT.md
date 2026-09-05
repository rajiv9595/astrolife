# ASTROLIFE V2 — PHASE 5G: TEST REPORT

**Date:** 2026-09-04
**Status:** ALL TESTS PASSED — ZERO REGRESSIONS
**Runner:** `backend/test_jaimini_dasha_phase5g.py` (37 / 37)

---

## 1. Phase 5G Results: 37 / 37 explicit checks

| Section | Checks | Result |
| :--- | :--- | :--- |
| 1. Profile & tradition (defaults honest, 8 unsupported listed, rejection, no vague labels) | 5 | PASS |
| 2. Starting sign & sequence (all 12 starts/directions/sequences vs reference, wrap-around, dual parity, movable/fixed) | 4 | PASS |
| 3. Duration matrix (144 periods vs independent reference, exception+normal coverage, per-lord own-sign sweep) | 3 | PASS |
| 4. Hierarchy & dates (144 antars, containment/sums/linkage, birth anchor, tz-aware ISO, contiguity, year model) | 7 | PASS |
| 5. Validation & UNKNOWN (clean validation, UNKNOWN shape, co-lord guard) | 3 | PASS |
| 6. Golden snapshot & determinism (start/dir/sequence/durations/total, 50× identical, write + 2 round-trips) | 7 | PASS |
| 7. Separation guards (Vimshottari distinct+intact, system label, vocab scan, astro scan) | 5 | PASS |
| 8. Performance (cold ≈0.005 s, repeated ≈0.003 s) | 1 | PASS |

Systematic volumes: 12 ascendants × 12 periods reference-compared; 7
own-sign fixtures; 50 determinism iterations. Golden: Taurus/REVERSE,
9-12-7-8-7-4-8-2-3-12-8-12, 92.0-year cycle. Snapshot:
`backend/golden_jaimini_dasha_snapshot.json` (engine-written, round-trip verified).

## 2. Complete Regression Accounting (all EXECUTED this pass except as noted)

| Suite | Runner | Result | Status |
| :--- | :--- | :--- | :--- |
| Phase 5G (Jaimini dasha) | `backend/test_jaimini_dasha_phase5g.py` | 37 / 37 | EXECUTED |
| Phase 5F (integration) | `backend/test_jaimini_integration_phase5f.py` | 57 / 57 | EXECUTED |
| Phase 5E (Jaimini yogas) | `backend/test_jaimini_yogas_phase5e.py` | 62 / 62 | EXECUTED |
| Phase 5D (Jaimini foundation) | `backend/test_jaimini_phase5d.py` | 143 / 143 | EXECUTED |
| Phase 1 (Golden canonical) | `backend/test_golden_chart_canonical.py` | 39 / 39 | EXECUTED |
| Phase 2 (Vargas) | `backend/test_varga_phase2.py` | 19,692 / 19,692 | EXECUTED |
| Phase 3 Panchanga | `backend/test_panchanga_phase3.py` | 423 / 423 | EXECUTED |
| Phase 3 Transit | `backend/test_transit_phase3.py` | 788 / 788 | EXECUTED |
| Phase 3 Dasha (Vimshottari) | `backend/test_dasha_phase3.py` (repo root*) | 81,283 / 81,283 | EXECUTED |
| Phase 3 Dynamic | `backend/test_dynamic_phase3.py` (repo root*) | 27 / 27 | EXECUTED |
| Phase 4B (Strength bounds) | `backend/test_strength_phase4b.py` | 87 / 87 | EXECUTED |
| Phase 5A (Rule engine) | `backend/test_rule_engine_phase5a.py` | 185 / 185 | EXECUTED |
| Phase 5B (Parashari yogas) | `backend/test_parashari_yogas_phase5b.py` | 355 / 355 | EXECUTED |
| Phase 5C (Doshas) | `backend/test_doshas_phase5c.py` | 157 / 157 | EXECUTED |
| **Executed total** | | **103,335 / 103,335** | |
| Phase 4 Strength Golden | (no standalone runner) | 7 / 7 | CARRIED FORWARD |
| **Grand total** | | **103,342 / 103,342** | |

\* Pre-existing cwd-relative path quirk; invoked from repo root.

Arithmetic: 37+57+62+143+39+19,692+423+788+81,283+27+87+185+355+157 =
103,335; +7 carried = 103,342. No double-counting, no omissions.

## 3. File Discipline

Created: `core/jaimini/dasha/` (9 files), `backend/test_jaimini_dasha_phase5g.py`,
`backend/golden_jaimini_dasha_snapshot.json`, 4 docs. Modified: none in
accepted layers. Deleted: none.

## 4. Limitations

Single implemented method; pratyantardasha deferred; dual-direction and
own-sign-12 are profile conventions (UNVERIFIED); fractional-day date
boundaries inherit float arithmetic (validated within 1e-6 days).
