# ASTROLIFE V2 — PHASE 9 — EXPERIMENTS

## Fixture framework
Declarative only (`fixture_id`, `description`, `chart_input_ref`, `facts`,
`expected_formation`, `expected_applicability`, `expected_timing`,
`expected_conflicts`, `expected_evidence_state`, `expected_provenance`,
`expected_status`, `fixture_kind`). Kinds: positive, negative, boundary,
missing_input. Negative/boundary/missing coverage is mandatory, not optional.

## Golden fixtures
Golden chart reused by reference; golden astronomy unaltered. Research facts
use canonical paths (`natal.{planet}.sign`, `natal.{planet}.house`, …) and
evaluate through the guarded Phase 6A resolver (undeclared → UNKNOWN).

## Boundary fixtures
Sign/degree/Nakshatra/Varga/house/Dasha/transit/conjunction/aspect
boundaries are expressible as exact facts. Phase 9 changes no boundary
formula — it only tests rules against canonical outputs.

## Historical runner
`run_research_experiment(experiment_id, package, rule, fixtures, profile)`
→ `ResearchExperimentResult`: fixtures_tested, OBSERVED_MATCH_COUNT,
OBSERVED_MISMATCH_COUNT, unknowns, conflicts, outcomes, evidence,
provenance (package/rule fingerprints + profile), summary, fingerprint.

## No fake validation
Raw deterministic counts only. The word “accuracy” appears nowhere in
results. `SUPPORTED_BY_EXPERIMENT ≠ classical truth ≠ production approval
≠ statistical truth` (no p-values, CI, Bayes, ML — §49).

## Reproducibility
Package version + rule version + profile + fixture set + canonical input
fingerprints + catalogue/evidence/dependency fingerprints + output
fingerprint. 50-run golden workflow: one identical experiment fingerprint.

## Regression lab
Package/rule/version/fixture/golden regressions with PASS/FAIL/UNKNOWN/
CONFLICT per fixture + provenance. Research failures never touch production
goldens (no “update golden” shortcut).
