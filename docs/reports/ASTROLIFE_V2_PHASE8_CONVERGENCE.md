# ASTROLIFE V2 — PHASE 8 CONVERGENCE

## 1. Independence rule (§§16–18)

Two signals are independent iff source systems differ AND canonical ancestry
(6E `input_facts` paths) is disjoint. Greedy deterministic grouping in
(source_system, source_id) order; group count = independent-system count.

Proven by test: Rule A + Rule B on `natal.jupiter.sign` → SINGLE_SYSTEM with
the duplicate exposed, never TWO_SYSTEM.

## 2. Levels (§17)

NONE (0) / SINGLE_SYSTEM (1) / TWO_SYSTEM (2) / MULTI_SYSTEM (3) /
STRONG_MULTI_SYSTEM (≥ threshold, default 4 from profile
`convergence_policy`). Results expose contributing signals, independent
systems, full dependency graph, excluded duplicates, conflicts. No
probability mapping exists — asserted by scan.

## 3. Method note

Ancestry reuses 6E catalogue manifests, resolved to exact rule versions in
`catalogue_rule_versions`. Correlated signals group; cross-system signals
with disjoint ancestry converge. Derived CONVERGENCE_SIGNAL summaries
(source_system CUSTOM) are excluded from independence counting.
