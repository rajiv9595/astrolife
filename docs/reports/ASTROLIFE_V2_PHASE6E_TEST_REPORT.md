# ASTROLIFE V2 — PHASE 6E TEST REPORT

**Generated:** 2026-09-05
**Test File:** `backend/test_dynamic_rules_phase6e.py`
**Result:** **105 / 105 PASSED** (100%)

---

## Test Summary

| Section | Tests | Passed | Failed |
|---------|-------|--------|--------|
| 1. Catalogue schema | 4 | 4 | 0 |
| 2. Registration | 3 | 3 | 0 |
| 3. Versioning | 5 | 5 | 0 |
| 4. Tradition filtering + isolation | 6 | 6 | 0 |
| 5. Profile filtering + isolation | 3 | 3 | 0 |
| 6. Lifecycle filtering | 3 | 3 | 0 |
| 7. §27 applicability cases | 14 | 14 | 0 |
| 8. Applicability result shape | 4 | 4 | 0 |
| 9. Applicability != evaluation | 2 | 2 | 0 |
| 10. Applicability != prediction | 2 | 2 | 0 |
| 11. Dependency + reverse index | 10 | 10 | 0 |
| 12. Discovery ordering + modes | 5 | 5 | 0 |
| 13. Evidence / source visibility | 5 | 5 | 0 |
| 14. Conflict visibility | 4 | 4 | 0 |
| 15. Health | 3 | 3 | 0 |
| 16. Knowledge graph | 3 | 3 | 0 |
| 17. Snapshot round-trip | 3 | 3 | 0 |
| 18. Golden catalogue | 6 | 6 | 0 |
| 19. Golden chart applicability | 3 | 3 | 0 |
| 20. Security | 4 | 4 | 0 |
| 21. API contract | 1 | 1 | 0 |
| 22. Performance (record only) | 2 | 2 | 0 |
| 23. Determinism (50 runs × 6 artefacts) | 1 | 1 | 0 |
| 24. Taxonomy helpers | 4 | 4 | 0 |
| **TOTAL** | **105** | **105** | **0** |

Recorded timings (s): catalogue_load ~0.012, rule_lookup ~0.0,
dependency_lookup ~0.0002, reverse_lookup ~0.0003,
applicability_evaluation ~0.0009, golden_generation ~0.0024.

---

## Regression Accounting (§36)

All accepted suites re-executed from their required working directories
(repo root for path-sensitive suites, `backend/` for pytest timing suite).
Zero failures everywhere. Shared/superset suites handled exactly as the
corrected 6C-H baseline prescribes.

| Phase | Suite | Count | Result |
|-------|-------|-------|--------|
| Phase 1 | test_golden_chart_canonical.py | 39 | PASS |
| Phase 2 | test_varga_phase2.py | 19,692 | PASS |
| Phase 3 Dasha | test_dasha_phase3.py | 81,283 | PASS |
| Phase 3 Transit | test_transit_phase3.py | 788 | PASS |
| Phase 3 Panchanga | test_panchanga_phase3.py | 423 | PASS |
| Phase 3 Dynamic | test_dynamic_phase3.py | 27 | PASS |
| Phase 4B | test_strength_phase4b.py | 87 | PASS |
| Phase 5A | test_rule_engine_phase5a.py | 185 | PASS |
| Phase 5B | test_parashari_yogas_phase5b.py | 355 | PASS |
| Phase 5C | test_doshas_phase5c.py | 157 | PASS |
| Phase 5D | test_jaimini_phase5d.py | 143 | PASS |
| Phase 5E | test_jaimini_yogas_phase5e.py | 62 | PASS |
| Phase 5F | test_jaimini_integration_phase5f.py | 57 | PASS |
| Phase 5G | test_jaimini_dasha_phase5g.py | 38 | PASS (subset of 5G-H core) |
| Phase 5G-H core | test_jaimini_dasha_phase5gh.py §1–14 | 62 | PASS (file prints 63 incl. §15 rollup) |
| Phase 5H | test_timing_engine.py (pytest) | 57 | PASS |
| Phase 5H-H | — | 0 | documentation-only |
| Phase 6A | test_dynamic_rules_phase6a.py | 48 | PASS |
| Phase 6B | test_dynamic_rules_phase6b.py | 51 | PASS |
| Phase 6C | test_dynamic_rules_phase6c.py | 115 | PASS |
| Phase 6D | test_dynamic_rules_phase6d.py | 86 | PASS |
| Phase 6E | test_dynamic_rules_phase6e.py | 105 | PASS |

- **EXECUTED TEST INSTANCES:** 103,860 (= preserved 103,669 baseline + 86 + 105)
- **UNIQUE TEST CASES:** 103,822 (= preserved 103,631 + 86 + 105; 5G ⊂ 5G-H dedup retained)
- **CARRIED-FORWARD:** 0
- **FAILURES:** 0 (zero unexplained failures)

Historical accounting untouched: the 103,669 / 103,631 baseline is carried
forward verbatim; only the additive 6D + 6E rows are new.

---

## File Discipline (§37)

**Created:** `backend/core/rules/dynamic/knowledge.py`,
`backend/test_dynamic_rules_phase6e.py`,
`ASTROLIFE_V2_PHASE6E_{AUDIT,ARCHITECTURE,CATALOGUE,APPLICABILITY,KNOWLEDGE_GRAPH,TEST_REPORT}.md`
**Modified:** `backend/core/rules/dynamic/__init__.py` (additive re-export only)
**Protected & unmodified:** calculation, Varga, Dasha, Transit, Strength,
Parashari, Dosha, Jaimini, Jaimini Dasha, Timing semantics (verified via git;
pre-existing `app.py`/`calculations.py` workspace diffs predate this phase).

## Known Limitations

- Classical entries declare family-level availability (5F specs / generic
  natal probes), not per-rule formation preconditions — by design (§10).
- `strength.bhava.*` resolves MISSING per accepted 6B behavior; specs avoid it.
- STRENGTH/PANCHANGA/DASHA/TRANSIT/VARGA systems have taxonomy support but no
  accepted standalone rules yet.
- `get_rule(id)` without version returns latest ACTIVE explicitly; exact-version
  callers must pass the version (§20).
