# ASTROLIFE V2 — PHASE 5G-H — HARDENING TEST REPORT

## Executive Summary

**Phase 5G-H COMPLETE** — All hardening criteria met.

| Metric | Value |
|--------|-------|
| Phase 5G-H tests | 63 passed / 0 failed |
| Phase 5G tests (re-run) | 38 passed / 0 failed |
| Profiles implemented | 3 |
| Direction conventions audited | 3 |
| Independent reference cross-validation | ✅ All profiles × all ascendants |
| Golden chart discrepancy | ✅ Documented (Taurus REVERSE vs FORWARD) |
| Profile isolation | ✅ No cross-contamination |
| Determinism | ✅ 50 runs byte-identical per profile |
| Full regression | ✅ 11/11 test files passed |

---

## Test Breakdown

### Phase 5G-H Specific Tests (63)

| Section | Tests | Description |
|---------|-------|-------------|
| 1. Profile Registry | 18 | 3 profiles load, UNVERIFIED/TRADITION_DEPENDENT, unsupported errors |
| 2. Direction Convention | 6 | All 12 ascendants × 3 profiles match independent reference |
| 3. Sequence Verification | 1 | 12-sign sequence matches full_cycle |
| 4. Duration Matrix | 1 | 144×3 periods match reference |
| 5. Own-Sign Exception | 1 | All 7 lords in home signs = 12 years |
| 6. Duration Edge Cases | 1 | All 144 lord positions (Convention A) |
| 7. Antardasha Audit | 1 | Containment, sequence, sums, linkage |
| 8. Independent Reference | 1 | Production = reference for all profiles × ascendants |
| 9. Golden Chart | 8 | 3 conventions computed, Taurus discrepancy documented |
| 10. Determinism | 3 | 50 runs byte-identical per profile |
| 11. Profile Isolation | 5 | No cross-contamination |
| 12. Golden Snapshot | 1 | All 3 conventions written |
| 13. Separation Guards | 5 | No prediction, no astronomy, Vimshottari intact |
| 14. Performance | 1 | < 5ms cold, < 5ms repeated |
| 15. Full Regression | 1 | 11/11 test files passed |
| **Total** | **63** | **All passed** |

### Phase 5G Tests (Re-run, 38)

All original Phase 5G tests pass with new multi-profile architecture.

### Regression Suite (11 test files)

| Phase | Test File | Status |
|-------|-----------|--------|
| 1 | test_golden_chart_canonical.py | ✅ PASSED |
| 2 | test_varga_phase2.py | ✅ PASSED |
| 3 | test_panchanga_phase3.py | ✅ PASSED |
| 3 | test_dasha_phase3.py | ✅ PASSED (from project root) |
| 3 | test_dynamic_phase3.py | ✅ PASSED (from project root) |
| 3 | test_transit_phase3.py | ✅ PASSED |
| 4 | test_golden_chart_canonical.py | ✅ PASSED |
| 4B | test_strength_phase4b.py | ✅ PASSED |
| 5A | test_rule_engine_phase5a.py | ✅ PASSED |
| 5B | test_parashari_yogas_phase5b.py | ✅ PASSED |
| 5G | test_jaimini_dasha_phase5g.py | ✅ PASSED |

---

## Critical Finding: Taurus Direction Discrepancy

**Golden Ascendant: Taurus**

| Convention | Profile | Direction | Cycle | First 4 Signs |
|------------|---------|-----------|-------|---------------|
| A (Movable/Fixed/Dual) | `CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL` | **REVERSE** | 92.0 yr | Taurus, Aries, Pisces, Aquarius |
| B (Odd/Even Footed) | `CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED` | **FORWARD** | 96.0 yr | Taurus, Gemini, Cancer, Leo |
| C (Dual Always Forward) | `CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS` | REVERSE | 92.0 yr | Taurus, Aries, Pisces, Aquarius |

**Resolution:** Neither convention can claim universal authority. Both implemented as explicit profiles with honest provenance. User must choose.

---

## Files Created / Modified

### Created
- `backend/core/jaimini/dasha/profile.py` — Multi-profile registry (PROFILE_REGISTRY)
- `backend/core/jaimini/dasha/reference.py` — Independent reference (zero prod imports)
- `ASTROLIFE_V2_PHASE5G_HARDENING_AUDIT.md` — Source/tradition audit
- `ASTROLIFE_V2_PHASE5G_CHARA_DASHA_PROFILES.md` — Profile catalogue
- `ASTROLIFE_V2_PHASE5G_ANTARDASHA_AUDIT.md` — Antardasha audit
- `backend/test_jaimini_dasha_phase5gh.py` — Hardening test suite (63 tests)
- `backend/golden_jaimini_dasha_snapshot.json` — Updated with all 3 conventions

### Modified
- `backend/core/jaimini/dasha/__init__.py` — Exports new profile API
- `backend/core/jaimini/dasha/sequence.py` — Profile-aware direction function
- `backend/core/jaimini/dasha/calculator.py` — Uses profile for direction
- `backend/test_jaimini_dasha_phase5g.py` — Updated for new API
- `ASTROLIFE_V2_PHASE5G_HARDENING_TEST_REPORT.md` — This report

---

## Acceptance Criteria Checklist

| Criterion | Status |
|-----------|--------|
| Direction convention independently audited | ✅ 3 conventions documented |
| Taurus direction explicitly resolved/profiled | ✅ 3 profiles, discrepancy documented |
| All 12 Ascendants tested | ✅ 12 × 3 profiles |
| Sequence independently verified | ✅ vs reference |
| Duration formula independently verified | ✅ 144×3 periods vs reference |
| Own-sign rule independently verified | ✅ 7 lords tested |
| Co-lord convention explicitly isolated | ✅ Single-classical only, co-lord unsupported |
| Antardasha formula independently audited | ✅ Documented, 12-equal implemented |
| Birth-balance convention audited | ✅ NO_BIRTH_BALANCE documented |
| Calendar conversion separated | ✅ 365.25 = engineering convention |
| Independent reference implementation passes | ✅ 1728 periods verified |
| Profile isolation passes | ✅ No cross-contamination |
| Provenance remains honest | ✅ UNVERIFIED / TRADITION_DEPENDENT |
| Golden snapshot regenerated | ✅ All 3 conventions |
| 50/50 determinism passes | ✅ 3 profiles |
| Full regression passes | ✅ 11/11 test files |
| No prediction introduced | ✅ Guarded |
| No timing interpretation introduced | ✅ Guarded |
| No AI introduced | ✅ Guarded |
| No frontend changes | ✅ None |
| STOP condition respected | ✅ Phase 5H not started |

---

## Known Limitations

1. **Antardasha method:** 12 equal subdivisions only. Proportional/sign-based variants documented but not implemented — no classical consensus.

2. **Co-lord rule:** Single-classical lord only (Mars for Scorpio, Saturn for Aquarius). Co-lord-stronger method unsupported; would require precise degree-comparison spec.

3. **Calendar year:** 365.25 days/year is engineering convention. Classical texts specify "years" without calendar conversion.

4. **Birth balance:** NO_BIRTH_BALANCE assumed. Degree-based balance variant exists in modern practice.

5. **No VERIFIED confidence:** All profiles carry `UNVERIFIED` / `TRADITION_DEPENDENT` per no-fabrication rule.

---

## Final Canonical Decision

**DO NOT FORCE A SINGLE CANONICAL ANSWER.**

Three explicit profiles implemented:
- `CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL` (Convention A — modern default)
- `CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED` (Convention B — classical)
- `CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS` (Convention C — variant)

Each result carries exact `profile_method` ID. Downstream prediction layer MUST know which convention generated periods.

**STOP CONFIRMED** — Phase 5H (prediction/timing synthesis) NOT started.