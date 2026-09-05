# ASTROLIFE V2 — PHASE 9 — COMPARISON

## Technique matrix (`compare_research_rules`)
Per technique: `technique_id`, `version`, `tradition`, `profile`,
`fixtures_tested`, `formed`, `not_formed`, `unknown`, `conflicted`,
`timing_matches`, `timing_mismatches`, `source_state`, `evidence_state`,
`dependency_state`. All values traceable to per-fixture outcomes; no
automatic superiority verdict.

## Method comparison
Accepted-method variants (e.g. Chara Dasha MOVABLE_FIXED_DUAL vs
ODD_EVEN_FOOTED vs MOVABLE_FIXED_DUAL_ALWAYS) are preserved side by side.
Divergence reports METHOD_DIFFERENCE, not BUG, unless independently proven.

## Conflict research
Rule×rule, source×source, tradition×tradition, profile×profile,
version×version, timing×timing disagreements are surfaced as CONTESTED and
never auto-resolved. Source-conflict experiments keep both sources.

## Version experiments
`diff_rule_versions(old, new)` reports changed formation/cancellation/
mitigation/activation/dependencies/applicability/evidence/timing +
version pair. Old versions are never overwritten.

## Coverage (`coverage_report`)
Required vs available input_facts/Varga/Dasha/Transit/Strength/Jaimini/rule
deps with missing lists. Missing coverage ⇒ UNKNOWN, never rule failure.

## Matrices
- Applicability: RULE×FIXTURE×TRADITION×PROFILE →
  APPLICABLE/NOT_APPLICABLE/UNKNOWN/INVALID (Phase 6E semantics).
- Evidence: RULE×SOURCE×CLAIM×EVIDENCE →
  VERIFIED/UNVERIFIED/CONTESTED/USER_SUPPLIED/MISSING (no score).
- Dependency: RULE×DEPENDENCY →
  RESOLVED/MISSING/INVALID/CONFLICTED/UNAVAILABLE (canonical resolver
  semantics reused).
