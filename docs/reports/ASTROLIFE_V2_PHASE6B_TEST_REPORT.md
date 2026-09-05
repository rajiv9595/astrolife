# ASTROLIFE V2 — PHASE 6B: TEST REPORT

**Date:** 2026-09-04
**Status:** ALL TESTS PASSED — ZERO REGRESSIONS
**Runner:** `backend/test_dynamic_rules_phase6b.py` (51 / 51)

---

## 1. Phase 6B Results: 51 / 51 explicit checks

| Section | Checks | Result |
| :--- | :--- | :--- |
| 1. Namespace (6 layer mappings, 2 rejections) | 8 | PASS |
| 2. FactResolver (14 typed golden resolutions + provenance, INVALID, 3×UNAVAILABLE) | 6 | PASS |
| 3. Bindings (7/7 fixtures FORMED on golden chart, clean diagnostics, D9/rule-dep proof) | 4 | PASS |
| 4. Declared enforcement (declared/undeclared × fact/D9/strength/transit) | 8 | PASS |
| 5. UNKNOWN/INVALID (withheld D9/transit, invalid planet+diagnostics, non-numeric) | 6 | PASS |
| 6. Evidence/audit (paths, fact maps, provenance, clean audit, drift flagged) | 5 | PASS |
| 7. Conflicts/tradition/versions (report-only, traditions, filter, pinned version) | 4 | PASS |
| 8. Synthetic golden (honest NOT_FORMED, UNKNOWN mitigation, separate cancellation) | 3 | PASS |
| 9. Snapshots (8 files, round-trip, 50-run 1-hash) | 3 | PASS |
| 10. Firewalls/security/perf (astro scan, Varga read-only, payload, timings) | 4 | PASS |

Golden context: real ChartFacts/Varga/StrengthReport/Vimshottari/Chara/Transit/JaiminiFacts at fixed 2026-01-01 UTC. 7 binding fixtures FORMED (Mars/Aries, Jupiter D9 Cancer, Mars shadbala, Moon MD, AK Jupiter, transit Gemini, rule-dep).

## 2. Complete Regression Accounting

| Suite | Runner | Result | Status |
| :--- | :--- | :--- | :--- |
| Phase 6B (canonical eval) | `backend/test_dynamic_rules_phase6b.py` | 51 / 51 | EXECUTED |
| Phase 6A (dynamic spec) | `backend/test_dynamic_rules_phase6a.py` | 48 / 48 | EXECUTED |
| Phase 5G (Jaimini dasha) | `backend/test_jaimini_dasha_phase5g.py` | 38 / 38 | EXECUTED |
| Phase 5G-H (dasha hardening) | `backend/test_jaimini_dasha_phase5gh.py` | 63 / 63 | EXECUTED |
| Phase 5F (integration) | `backend/test_jaimini_integration_phase5f.py` | 57 / 57 | EXECUTED |
| Phase 5E (Jaimini yogas) | `backend/test_jaimini_yogas_phase5e.py` | 62 / 62 | EXECUTED |
| Phase 5D (Jaimini foundation) | `backend/test_jaimini_phase5d.py` | 143 / 143 | EXECUTED |
| Phase 1 (Golden canonical) | `backend/test_golden_chart_canonical.py` | 39 / 39 | EXECUTED |
| Phase 2 (Vargas) | `backend/test_varga_phase2.py` | 19,692 / 19,692 | EXECUTED |
| Phase 3 Panchanga | `backend/test_panchanga_phase3.py` | 423 / 423 | EXECUTED |
| Phase 3 Transit | `backend/test_transit_phase3.py` | 788 / 788 | EXECUTED |
| Phase 4B (Strength bounds) | `backend/test_strength_phase4b.py` | 87 / 87 | EXECUTED |
| Phase 5A (Rule engine) | `backend/test_rule_engine_phase5a.py` | 185 / 185 | EXECUTED |
| Phase 5B (Parashari yogas) | `backend/test_parashari_yogas_phase5b.py` | 355 / 355 | EXECUTED |
| Phase 5C (Doshas) | `backend/test_doshas_phase5c.py` | 157 / 157 | EXECUTED |
| Phase 5H (Timing, pytest) | `backend/test_timing_engine.py` | 57 / 57 | EXECUTED |
| Phase 3 Dasha (Vimshottari) | `backend/test_dasha_phase3.py` (repo root*) | 81,283 / 81,283 | EXECUTED |
| Phase 3 Dynamic | `backend/test_dynamic_phase3.py` (repo root*) | 27 / 27 | EXECUTED |
| **Executed total** | | **103,555 / 103,555** | |
| Phase 4 Strength Golden | (no standalone runner) | 7 / 7 | CARRIED FORWARD |
| Phase 5D-H | (hardening of 5D suite, no separate file) | 143 / 143 | CARRIED FORWARD (same suite) |
| Phase 5H-H | (docs only, no test file) | — | NOT EXECUTED |
| **Grand total (tests)** | | **103,562 / 103,562** | |

\* Pre-existing cwd quirk. Timing file is pytest-style.

Arithmetic: 51+48+38+63+57+62+143+39+19,692+423+788+87+185+355+157+57+81,283+27
= 103,555; +7 carried = 103,562. (5D-H shares the 5D suite file; counted once.)

## 3. File Discipline

Created: 6 files in `core/rules/dynamic/` (namespace, context, resolver,
bindings, results, engine), `backend/test_dynamic_rules_phase6b.py`,
`backend/golden_dynamic_rule_snapshots/` (8 files), 5 docs. Modified: none in
accepted layers (tracked `app.py`/`calculations.py` diffs pre-date 6B).
Deleted: none.

## 4. Limitations

Aspect maps are caller-supplied (canonical 5A output, not recomputed);
`bhava` strength explicitly unavailable; rule-existence checks are
registry-side; evaluation datetimes caller-supplied.
