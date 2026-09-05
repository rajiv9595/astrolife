# ASTROLIFE V2 — PHASE 6B: EVALUATION

**Module:** `core/rules/dynamic/engine.py` (+ `results.py`).

## 1. Contract

`evaluate_dynamic_rule(rule, context)`: validate (minus registry-side
existence) → coverage check → resolve → evaluate → result. Uncovered paths ⇒
INVALID with `UNDECLARED_DEPENDENCY` diagnostics. Missing facts ⇒ per-tree
UNKNOWN (a FALSE sibling still decides ALL/ANY — no collapse). Statuses
FORMED | NOT_FORMED | UNKNOWN | INVALID; final_state refines cancelled/
mitigated formations. `evolution_profile = 6B/1.0.0` stamped on results.

## 2. By-ID, Many, Audit

`evaluate_dynamic_rule_by_id` pins exact versions (no silent upgrade).
`evaluate_many(rules, ctx, tradition?)` filters by tradition and reports
conflicts (shared derived_fact with FORMED vs NOT_FORMED) as REPORTED_ONLY
with parties + traditions. `audit_dynamic_rule_evaluation` flags undeclared
facts, missing deps, firewall breaches, dependency drift, and unexplained
UNKNOWN/INVALID.

## 3. Golden Rules & Snapshots

8 CUSTOM/USER_SUPPLIED fixtures (natal, D9, strength, Vimshottari, Jaimini,
transit, rule-dep, synthetic golden) evaluated on the real golden chart at
fixed 2026-01-01 UTC. 7 FORMED; synthetic golden honestly NOT_FORMED (Mars D9
is Leo) with UNKNOWN mitigation. Snapshots in
`backend/golden_dynamic_rule_snapshots/` (8 files), byte-identical
round-trips, 50 runs ⇒ 1 hash.

## 4. API

`evaluate_dynamic_rule(rule, context)`, `evaluate_dynamic_rule_by_id(...)`,
`evaluate_many(...)`, `audit_dynamic_rule_evaluation(...)`,
`build_context(...)`, `CanonicalFactResolver`. No frontend endpoints.
