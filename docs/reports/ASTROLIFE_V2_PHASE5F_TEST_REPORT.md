# ASTROLIFE V2 — PHASE 5F: TEST REPORT

**Date:** 2026-09-04
**Status:** ALL TESTS PASSED — ZERO REGRESSIONS
**Runner:** `backend/test_jaimini_integration_phase5f.py` (57 / 57)

---

## 1. Phase 5F Results: 57 / 57 explicit checks

| Section | Checks | Result |
| :--- | :--- | :--- |
| A. Golden cross-system audit (karakas, Karakamsha/Swamsa, AL/UL, formed set, graph tiers) | 9 | PASS |
| B/C. Positive & negative (formation link, failing evidence) | 4 | PASS |
| D. UNKNOWN semantics (D9-strip envelope, UNCERTAIN≠NOT_FORMED, subset drop, missing_inputs) | 6 | PASS |
| E. Dependencies (spec coverage, acyclicity, synthetic cycle, policy, zero strength) | 5 | PASS |
| F. Conflicts (golden 3×DIFFERENT_DIMENSIONS, report-only, 3 synthetic classes) | 5 | PASS |
| G. Tradition isolation (5/7 subsets, consistency, profile record) | 4 | PASS |
| H/I. Validators (golden clean, 3 synthetic rejections) | 5 | PASS |
| J/K. Determinism 50×, node order, snapshot write + 3 round-trips | 6 | PASS |
| L. Boundaries (read-only upstream, D9 invariance, no strength param, import scan, no-prediction vocab, 5E compat) | 6 | PASS |
| M. Exhaustive (12 asc + AK ref + validators + UNKNOWN envelope; 144 pairs + zero contradictions; tradition perms) | 3 | PASS |
| N. Performance (cold ≈0.002 s, repeated ≈0.002 s, graph ≈0.001 s, conflicts ≈0.00007 s) | 1 | PASS |

Systematic volumes: 144 AK/AmK pairs × full 5F eval; 12 ascendants × full eval
× validators × UNKNOWN envelope; 50 determinism iterations. Golden evidence
graph: 64 nodes / 220 edges. Snapshot:
`backend/golden_jaimini_evidence_snapshot.json` (engine-written, round-trip
verified on formed/unknown/graph-nodes).

## 2. Complete Regression Accounting (all EXECUTED this pass except as noted)

| Suite | Runner | Result | Status |
| :--- | :--- | :--- | :--- |
| Phase 5F (integration) | `backend/test_jaimini_integration_phase5f.py` | 57 / 57 | EXECUTED |
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
| **Executed total** | | **103,298 / 103,298** | |
| Phase 4 Strength Golden | (no standalone runner) | 7 / 7 | CARRIED FORWARD |
| **Grand total** | | **103,305 / 103,305** | |

\* Pre-existing cwd-relative path quirk; invoked from repo root. Nothing
silently excluded.

Arithmetic: 57+62+143+39+19,692+423+788+81,283+27+87+185+355+157 = 103,298;
+7 carried = 103,305. No double-counting, no omissions.

## 3. File Discipline

Created: `core/jaimini/evidence.py`, `dependencies.py`, `conflicts.py`,
`rule_validators.py`, `integration.py`,
`backend/test_jaimini_integration_phase5f.py`,
`backend/golden_jaimini_evidence_snapshot.json`, 5 docs (audit,
specification, evidence model, conflict model, test report). Modified: none
in accepted layers (tracked diffs in `backend/app.py`/`calculations.py`
pre-date Phase 5F). Deleted: none.

## 4. Limitations

UNKNOWN only triggers on genuinely absent inputs (complete charts rarely hit
it); conflict pairs are the 3 declared same-proposition pairs; APPARENT_
CONTRADICTION unpopulated; performance numbers are single-machine
observations, not benchmarks.
