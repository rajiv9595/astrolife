# ASTROLIFE V2 — PHASE 7 TEST REPORT

**Generated:** 2026-09-05
**Test file:** `backend/test_agents_phase7.py`
**Adapter:** deterministic mock only (no network, no vendor)
**Result:** **176 / 176 PASSED** (100%; minimum required: 150)

## Section results

| # | Area | Tests |
|---|---|---|
| 1 | agent contracts (6 specialists, versions, forbidden ops) | 10 |
| 2 | registry (CRUD, ordering, validation, fingerprint, snapshot) | 9 |
| 3 | versioning (explicit replacement, immutability) | 3 |
| 4 | capability declarations + router capability rejection | 9 |
| 5 | context validation + fingerprints + indexes | 5 |
| 6 | router determinism (incl. FULL=6, profile rejection, errors) | 7 |
| 7 | read-only enforcement (pure functions, no bundle reach, no mutators) | 3 |
| 8 | Parashari agent | 5 |
| 9 | Jaimini agent (incl. capability blindness to strength) | 4 |
| 10 | Strength agent (classical vs custom, no formula) | 5 |
| 11 | Yoga/Dosha agent (5 preserved layers, dispute preservation) | 5 |
| 12 | Timing agent (exact windows, no outcomes) | 3 |
| 13 | Chart synthesis (agreement only on shared refs, no resolution) | 5 |
| 14 | provenance (binding, chain completeness, evidence subset) | 4 |
| 15 | evidence linkage (invented ids rejected) | 2 |
| 16 | conflict propagation (ids, no winner) | 3 |
| 17 | UNKNOWN propagation (4 missing-input cases + no hedging) | 5 |
| 18 | tradition isolation (5 context shapes) | 5 |
| 19 | profile isolation | 3 |
| 20 | prediction firewall (refusal, INVALID, banned-phrase scan) | 5 |
| 21 | source fabrication firewall | 3 |
| 22 | prompt injection (8 classes x WARNING + identical interpretations + detector) | 18 |
| 23 | invalid model output (malformed, override, garbage) | 3 |
| 24 | mock adapter (metadata, pre-check, determinism) | 4 |
| 25 | serialization (round-trip, forbid unknown fields) | 3 |
| 26 | fingerprinting (input/output/record) | 3 |
| 27 | snapshot (registry round-trip, catalogue unchanged) | 2 |
| 28 | end-to-end orchestration (6+6, timings, synthesis) | 6 |
| 29 | security posture (firewall text, structured prompts) | 3 |
| 30 | regression compatibility (6E catalogue, accessor) | 4 |
| 31 | static calculation-import audit | 3 |
| 32 | mutation test (8 canonical categories) | 8 |
| 33 | determinism (50 runs: routing/output/provenance/serialization) | 2 |
| 34 | question layer (routing ignores question text) | 1 |
| 35 | presentation separation | 2 |
| 36 | fixture matrix (incomplete/missing/fabricated/unsupported/mutation) | 8 |
| **Total** | | **176** |

## Regression accounting (§40)

All prior suites re-executed from their required working directories
(repo root for path-sensitive suites, `backend/` for the pytest timing suite).

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

- **EXECUTED TEST INSTANCES:** 104,036 (= preserved 103,860 baseline + 176)
- **UNIQUE TEST CASES:** 103,998 (= preserved 103,822 + 176; 5G ⊂ 5G-H dedup retained)
- **CARRIED-FORWARD:** 0
- **FAILURES:** 0 — zero unexplained failures; no tests deleted, weakened, or suppressed; no golden values rewritten.

## File discipline (§38)

**Created:** `backend/core/agents/` (`__init__.py`, `agent_models.py`,
`agent_contract.py`, `agent_context.py`, `agent_result.py`,
`agent_registry.py`, `agent_router.py`, `agent_validation.py`,
`agent_provenance.py`, `agent_conflicts.py`, `agent_security.py`,
`agent_prompts.py`, `orchestrator.py`, `golden.py`, `adapters/{__init__,base,mock}.py`,
`agents/{__init__,_shared,parashari,jaimini,strength,yoga_dosha,timing,chart_synthesis}_*.py`),
`backend/test_agents_phase7.py`, 7 root docs.
**Modified:** none in protected layers.
**Protected & verified unchanged:** calculation, strength, rules (+dynamic),
jaimini, timing, transit, all prior suites and golden snapshots.

## Known limitations

- Agents restate supplied summaries; verdict quality is bounded by fixture
  completeness (missing sections -> honest UNKNOWN/PARTIAL, never inference).
- Classical evidence ids are fixture-scoped keys over classical evidence
  lists (`classic-ev:<rule>:<nn>`), documented in golden.py.
- `run_full_with_synthesis` is explicit two-stage; FULL-route inline synthesis
  runs with an empty sub-result set (standalone mode).
- External LLM adapters are future work; regression pins the deterministic mock.
