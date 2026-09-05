# ASTROLIFE V2 — PHASE 9 — PROVENANCE

## Chain
ResearchExperiment → ResearchRule → Applicability → RuleResult →
Canonical Facts → Evidence / Claims / Sources. Exact package/rule/profile/
fixture versions plus canonical input, catalogue, evidence, dependency, and
output fingerprints are preserved per experiment.

## Research graph
Nodes: RESEARCH_PACKAGE, RESEARCH_RULE, HYPOTHESIS, EXPERIMENT, FIXTURE,
OBSERVATION, COMPARISON, PROMOTION_REQUEST. Edges: TESTS, USES, SUPPORTS,
CONTRADICTS, COMPARES, DEPENDS_ON, DERIVED_FROM, PROPOSES, PROMOTES.
Deterministic ordering + fingerprint. Extends Phase 6D concepts; the
Phase 6D EvidenceGraph is untouched.

## Snapshots
Immutable: package, rules, versions, sources, evidence, dependencies,
fixtures, experiments, results + fingerprint. Serialized canonical JSON
round-trips byte-identically (tested).

## Hypotheses & notebook
`hypothesis_id`, statement, assumptions, rule/evidence/fixture ids,
expected/observed behavior, status (OPEN, SUPPORTED_BY_EXPERIMENT,
INCONCLUSIVE, CONTRADICTED, REJECTED). Notebook holds title, hypothesis,
objective, package/rule/fixture/experiment/comparison refs, observations
(tagged RESEARCH_OBSERVATION), conflicts, conclusions, developer notes,
provenance, fingerprint. SUPPORTED_BY_EXPERIMENT ≠ classical truth.

## No silent classical authority
Passing tests do not create classical authority. Promoted developer rules
remain USER_SUPPLIED / CUSTOM_DEVELOPER / EXPERIMENTAL until source and
evidence states independently warrant reclassification. No provenance is
fabricated; UNVERIFIED stays visible.

## Immutability proof
Before/after each experiment: production catalogue/rules, ChartFacts,
VargaFacts, Dasha, Transit, Strength, Jaimini, EvidenceGraph,
KnowledgeGraph fingerprints identical (canonical-digest comparison tests).
No live current time in canonical identity or results.
