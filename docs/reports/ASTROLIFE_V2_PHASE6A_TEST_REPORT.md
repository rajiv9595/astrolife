# ASTROLIFE V2 — PHASE 6A: TEST REPORT

**Date:** 2026-09-04
**Status:** ALL TESTS PASSED — ZERO REGRESSIONS
**Runner:** `backend/test_dynamic_rules_phase6a.py` (48 / 48)

---

## 1. Phase 6A Results: 48 / 48 explicit checks

| Section | Checks | Result |
| :--- | :--- | :--- |
| 1. Schema (version stamp, stable ID, 22 primitives, composition set) | 4 | PASS |
| 2. Serialization (round-trip bytes, order-insensitive lists, no timestamps) | 4 | PASS |
| 3. Primitives (all 22 TRUE/FALSE, AT_LEAST/EXACTLY/AT_MOST/NOT) | 6 | PASS |
| 4. UNKNOWN & separation (missing⇒UNKNOWN, independent states, golden FORMED, evidence) | 7 | PASS |
| 5. Provenance (golden clean, USER_SUPPLIED held, VERIFIED-without-evidence rejected) | 3 | PASS |
| 6. Versioning & registry (semver, register, immutability, v1.1.0 path, listing, latest, filters, deprecate, cycles) | 10 | PASS |
| 7. Dependencies & firewall (undeclared flagged, JAIMINI⊘western, vocab, op, dep, self-cycle) | 6 | PASS |
| 8. Security (11 payload classes rejected, no prose false positives, inert equality) | 3 | PASS |
| 9. Tradition isolation (WESTERN⊘jaimini, category filter) | 2 | PASS |
| 10. Determinism (50 runs identical) | 1 | PASS |

Golden synthetic rule `DEMO.CUSTOM.SYNTHETIC_GOLDEN` (CUSTOM_DEVELOPER /
USER_SUPPLIED / UNVERIFIED, no classical claims) exercises formation,
cancellation, mitigation, D9 + rule dependencies, evidence, and UNKNOWN.

## 2. Complete Regression Accounting

| Suite | Runner | Result | Status |
| :--- | :--- | :--- | :--- |
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
| **Executed total** | | **103,504 / 103,504** | |
| Phase 4 Strength Golden | (no standalone runner) | 7 / 7 | CARRIED FORWARD |
| Phase 5H-H | (docs only, no test file) | — | NOT EXECUTED |
| **Grand total (tests)** | | **103,511 / 103,511** | |

\* Pre-existing cwd-relative path quirk. `test_timing_engine.py` is
pytest-style (direct execution is a silent no-op); run via
`python -m pytest test_timing_engine.py -q`.

Arithmetic: 48+38+63+57+62+143+39+19,692+423+788+87+185+355+157+57+81,283+27
= 103,504; +7 carried = 103,511. No double-counting, no omissions.

## 3. File Discipline

Created: `core/rules/dynamic/` (7 files), `backend/test_dynamic_rules_phase6a.py`,
4 docs. Modified: none in accepted layers (tracked `app.py`/`calculations.py`
diffs pre-date 6A). Deleted: none.

## 4. Limitations

Resolver is caller-supplied (6A defines the contract, not canonical bindings);
cycle validation is single-level in `validate_rule`, multi-level in registry;
`effective_from` is author-supplied immutable metadata (not a clock).
