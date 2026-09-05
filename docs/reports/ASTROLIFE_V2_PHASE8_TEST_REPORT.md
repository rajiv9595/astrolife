# ASTROLIFE V2 — PHASE 8 TEST REPORT

**Generated:** 2026-09-05
**Test file:** `backend/test_prediction_phase8.py`
**Result:** **211 / 211 PASSED** (100%; minimum required: 200)

## Section results (40 sections)

| # | Area | Tests |
|---|---|---|
| 1 | models (frozen schemas, forbid unknown fields) | 5 |
| 2 | event taxonomy (16 categories) | 6 |
| 3 | event definitions (registry, stable IDs, versions, schema) | 7 |
| 4 | formation engine (ANY/ALL, coverage, missing→UNKNOWN) | 4 |
| 5 | activation engine (overlap, absent→UNKNOWN) | 3 |
| 6 | dasha signals (MD/AD rows, verbatim windows, no PD invention) | 5 |
| 7 | transit signals (ancestry, exact roots preserved) | 4 |
| 8 | Jaimini signals + three explicit profiles | 6 |
| 9 | formation signals (systems, categorical labels) | 3 |
| 10 | convergence (levels, exposure, no probability) | 4 |
| 11 | correlated signals + independence (shared-ancestry grouping) | 7 |
| 12 | windows (intersect/union/contains/overlap/distance/clip/bounds) | 15 |
| 13 | timing window API | 1 |
| 14 | conflicts (formation-split policy, supplied propagation) | 5 |
| 15 | UNKNOWN engine (unsupported coverage, no windows) | 3 |
| 16 | exclusion signals (typed, preserved alongside support) | 3 |
| 17 | deduplication + version pinning | 6 |
| 18 | ranking (categorical, reasoned, no scores) | 4 |
| 19 | evidence completeness (categorical, no scores) | 2 |
| 20 | catalogue integration (ancestry, eligibility, dev flags) | 6 |
| 21 | developer rules (honest status, no classical authority) | 3 |
| 22 | security (9 hostile directives detected + ignored) | 12 |
| 23 | immutability (entry + 7 canonical digests + catalogue seal) | 8 |
| 24 | no live current time (implementation scan) | 1 |
| 25 | static calculation audit (29 tokens, 19 modules) | 2 |
| 26 | non-overclaim (formation w/o activation, activation w/o formation, ALL) | 3 |
| 27 | version reproducibility (1.0.0/1.1.0 pins) | 3 |
| 28 | golden end-to-end (7 candidates, fingerprints, language) | 8 |
| 29 | cross-profile (3 profiles distinct + deterministic) | 5 |
| 30 | cross-tradition (parashari/jaimini/combined provenance) | 4 |
| 31 | profiles (immutable, versioned, schema) | 4 |
| 32 | request validation (range/profile/selection/fingerprints) | 4 |
| 33 | provenance (envelope, chain completeness, snapshot) | 4 |
| 34 | EventRule abstraction | 3 |
| 35 | no scores / no ML / no LLM | 4 |
| 36 | performance (9 stage timings) | 2 |
| 37 | determinism (50 runs, byte-identical) | 2 |
| 38 | AI downstream compatibility (read-only summaries) | 3 |
| 39 | API contracts (15 functions) | 1 |
| 40 | extended selection/version/evidence coverage | 21 |
| **Total** | | **211** |

Golden chart end-to-end (2026 window): 3 PRIMARY (Career/Wealth/Custom-dev),
Marriage + Relationship NOT_FORMED with conflicts visible, Education
NOT_FORMED, Health UNSUPPORTED/INSUFFICIENT; result PARTIAL; 50 runs, one
canonical fingerprint.

## Regression accounting (§64)

All prior suites re-executed from required working directories.

| Phase | Suite | Executed | Result |
|---|---|---|---|
| 1 | test_golden_chart_canonical.py | 39 | PASS |
| 2 | test_varga_phase2.py | 19,692 | PASS |
| 3 dasha | test_dasha_phase3.py | 81,283 | PASS |
| 3 transit | test_transit_phase3.py | 788 | PASS |
| 3 panchanga | test_panchanga_phase3.py | 423 | PASS |
| 3 dynamic | test_dynamic_phase3.py | 27 | PASS |
| 4B | test_strength_phase4b.py | 87 | PASS |
| 5A | test_rule_engine_phase5a.py | 185 | PASS |
| 5B | test_parashari_yogas_phase5b.py | 355 | PASS |
| 5C | test_doshas_phase5c.py | 157 | PASS |
| 5D | test_jaimini_phase5d.py | 143 | PASS |
| 5E | test_jaimini_yogas_phase5e.py | 62 | PASS |
| 5F | test_jaimini_integration_phase5f.py | 57 | PASS |
| 5G | test_jaimini_dasha_phase5g.py | 38 | PASS (subset of 5G-H core) |
| 5G-H core | test_jaimini_dasha_phase5gh.py §1–14 | 62 | PASS (file prints 63 incl. §15 rollup) |
| 5H | test_timing_engine.py (pytest) | 57 | PASS |
| 5H-H | — | 0 | documentation-only |
| 6A | test_dynamic_rules_phase6a.py | 48 | PASS |
| 6B | test_dynamic_rules_phase6b.py | 51 | PASS |
| 6C | test_dynamic_rules_phase6c.py | 115 | PASS |
| 6D | test_dynamic_rules_phase6d.py | 86 | PASS |
| 6E | test_dynamic_rules_phase6e.py | 105 | PASS |
| 7 | test_agents_phase7.py | 176 | PASS |
| 8 | test_prediction_phase8.py | 211 | PASS |

- **EXECUTED TEST INSTANCES:** 104,247 (= preserved 104,036 baseline + 211)
- **UNIQUE TEST CASES:** 104,209 (= preserved 103,998 + 211; 5G ⊂ 5G-H dedup retained)
- **CARRIED-FORWARD:** 0
- **FAILURES:** 0 — nothing deleted/weakened/suppressed; no goldens rewritten.

## File discipline

**Created:** `backend/core/prediction/` (21 files), `backend/test_prediction_phase8.py`,
9 root docs (`PHASE8_AUDIT/ARCHITECTURE/EVENT_MODEL/CONVERGENCE/TIMING/
UNCERTAINTY/SECURITY/TEST_REPORT/FINAL_REPORT`).
**Modified:** none in protected layers (calculation, Varga, Dasha, Transit,
Strength, Parashari, Dosha, Jaimini, Jaimini Dasha, Timing, Dynamic Rules,
Knowledge Catalogue, AI Agent contracts).
**Protected-layer verification:** git diff shows no protected modifications.

## Known limitations

- PD rows flow only when canonically supplied (absent on golden → UNKNOWN).
- Transit exact events are fixture-supplied canonical roots; the engine adds none.
- `include_alternatives=False`/`include_conflicts=False` filter ranks post-hoc.
- Request `notes` ride in fingerprints but never alter candidates.
- External rendering (UI prose) is out of scope for Phase 8.
