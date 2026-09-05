# ASTROLIFE V2 — PHASE 9 — TEST REPORT

## Phase 9 suite: 281 / 281 PASS (`backend/test_research_phase9.py`)
41 sections: models 10, lifecycle 8, authoring 8, DSL 6, sources 6,
claims 8, evidence 6, dependencies 10, profiles 6, applicability 8,
fixtures 8, negative 6, boundary 6, experiments 10, reproducibility 4,
comparison 8, conflicts 6, versions 6, coverage 6, evidence-matrix 5,
dep-matrix 5, notebook 5, hypotheses 8, snapshots 6, import/export 6,
security 12, injection 8, catalogue 8, gates 14, review 6, promo-audit 5,
isolation 6, prediction 5, AI 4, golden 12, neg-promo 4, pos-promo 6,
immutability 6, determinism (50 runs) 4, static audit 5, regression
guards 4. Zero failures; no inflated counts (each check asserts behavior).

## Golden research package
Accepted reference + CUSTOM_DEVELOPER synthetic + EXPERIMENTAL rule,
unverified source, contested source pair (CONTESTED preserved),
rule dependency, boundary/negative/missing fixtures, comparison,
failing promotion (TESTED≠PROMOTED proven) + REVIEW_PENDING promotion.
Experimental rule never auto-promoted.

## Determinism / security / immutability
50-run golden workflow: one experiment/package/snapshot fingerprint.
Static audit of `backend/core/research/`: clean. Canonical digests before/
after experiments identical. No `datetime.now`/`time.time`, no ephemeris,
no ML/LLM in research code.

## Regression accounting (all re-executed, 0 failures)
| Suite | Executed |
|---|---|
| Phase 1 golden canonical | 39 |
| Phase 2 Varga | 19,692 |
| Phase 3 (423 + 81,283 + 27 + 788) | 82,521 |
| Phase 4B synthetic | 87 |
| Phase 5A rule engine | 185 |
| Phase 5B yogas | 355 |
| Phase 5C doshas | 157 |
| Phase 5D Jaimini | 143 |
| Phase 5E Jaimini yogas | 62 |
| Phase 5F integration | 57 |
| Phase 5G Chara Dasha | 38 |
| Phase 5G-H core (§1–14) | 62 |
| Phase 5H timing (pytest) | 57 |
| Phase 6A DSL | 48 |
| Phase 6B resolver | 51 |
| Phase 6C lab | 115 |
| Phase 6D evidence | 86 |
| Phase 6E catalogue | 105 |
| Phase 7 agents | 176 |
| Phase 8 prediction | 211 |
| Phase 9 research (NEW) | 281 |

- **EXECUTED TEST INSTANCES:** 104,528 (= 104,247 + 281)
- **UNIQUE TEST CASES:** 104,490 (= 104,209 + 281)
- **CARRIED-FORWARD:** 0
- **FAILURES:** 0 — nothing deleted/weakened/suppressed; no goldens rewritten.

## Performance (golden package, ms)
load 0.3, rule lookup 0.009, applicability 0.1, dependency graph 0.1,
fixture validation 0.0, experiment 0.9, comparison 1.3, snapshot 0.4,
promotion gates 0.5, graph 0.1. No optimization performed.
