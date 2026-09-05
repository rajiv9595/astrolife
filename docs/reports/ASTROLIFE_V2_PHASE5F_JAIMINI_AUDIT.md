# ASTROLIFE V2 — PHASE 5F: JAIMINI HARDENING + INTEGRATION AUDIT

**Date:** 2026-09-04
**Scope:** Pre-implementation audit for Phase 5F (hardening + integration; no prediction)
**Status:** Audit Complete — Ready for Implementation
**Prior phases:** 5D/5D-H/5E COMPLETE and accepted (no redesign).

---

## 1. Current Architecture

```
ChartFacts (Phase 1) ──→ VargaFacts D9 (Phase 2) ──→ JaiminiFacts (5D/5D-H)
                                                       ↓
                              JaiminiYogaEvaluation: 12 JAI.* results (5E)
```

* 5D foundation (`core/jaimini/*.py`): deterministic facts, UNVERIFIED
  provenance, validators; golden snapshot 3-fact + 12-pada state.
* 5E rules (`core/jaimini/rules/`, 10 files): 12 yogas, timestamp-free
  `JaiminiRuleResult` (formation/cancellation/mitigation/quality split),
  `evaluate_jaimini_yogas`; golden yoga snapshot (3/12 formed).
* 5A generic engine: enums + `Provenance` reused; `RuleResult`/`Condition`
  tree intentionally not reused (timestamps, overkill).
* Consumers: legacy `backend/jaimini.py` + `routes/astro.py` + `JaiminiCard.jsx`
  (untouched by 5E/5F).

## 2. Reusable Infrastructure

5A enums (`RuleCategory.JAIMINI`, `RuleTradition.JAIMINI`, formation/
cancellation/mitigation/quality, `ConfidenceLevel.TRADITION_DEPENDENT`,
`SourceType.UNVERIFIED`); 5A `Provenance` shape; 5E catalogue + evaluators +
`JaiminiYogaProfile`; 5D `JaiminiContext`; `structural.py` constant tuples;
varga D9 accessors in 5E predicates.

## 3. Duplicated / Missing Infrastructure (5F closes the gaps)

* No explicit rule→fact dependency metadata (deps hidden in evaluator code).
* No evidence graph (per-rule evidence lists exist but are unlinked).
* No conflict analysis, no tradition-subset filtering, no UNKNOWN state
  (evaluators assume complete inputs), no completeness/provenance validators,
  no integration aggregate. Nothing here duplicates 5A: 5A validators target
  `RuleDefinition`/`Condition` trees, not Jaimini fact predicates.

## 4. Integration Boundaries (enforced, not aspirational)

Upstream (read-only): ChartFacts D1, varga D9, JaiminiFacts. 5F adds no
strength/transit/dasha inputs; `evaluate_jaimini` takes no strength param
(asserted by test). Jaimini never writes upstream. Varga allowed ONLY for the
2 declared D9 rules (perturbation-tested); strength deps default `[]` with a
validator rejecting undeclared access. Parashari aspect/yoga results never
consumed (import scan-tested); no TRADITION_HYBRID rules created in 5F.

## 5. Contamination Risks

R1: D9 leaking into non-D9 rules → closed by declared `varga_dependencies` +
    strip-D9 invariance test. R2: Parashari drishti import → closed by scan
    test (only `get_sign_rashi_drishti` + precomputed maps). R3: 7k/8k mixing
    → existing 5E ValueError guard, re-tested. R4: timestamps/random IDs in
    graph → stable string IDs only, byte-compared. R5: dict-ordering
    nondeterminism → all outputs sorted by explicit keys.

## 6. Deterministic Requirements

Stable evidence node/edge IDs, sorted orderings everywhere, timestamp-free
models, 50-iteration byte-identical JSON, snapshot round-trip equality.

## 7. Proposed 5F Changes (new files only)

`core/jaimini/evidence.py` (graph + tiers + completeness validator),
`core/jaimini/dependencies.py` (per-rule declarations, varga/strength policy,
cycle detection), `core/jaimini/conflicts.py` (report-only conflict classes),
`core/jaimini/integration.py` (`JaiminiIntegrationProfile`,
`evaluate_jaimini()` aggregate, UNKNOWN synthesis, tradition filter,
provenance validator), `core/jaimini/rule_validators.py` (kept separate from
accepted `validators.py`), `backend/test_jaimini_integration_phase5f.py`,
`backend/golden_jaimini_evidence_snapshot.json`, 5 docs.

## 8. Explicitly Excluded

Dashas, timing, predictions, scores, AI/NL, frontend, Rule Lab, ML,
hybrid-tradition rules, strength-consuming rules, any upstream rewrite. Upstream
defect → STOP and report.
