# ASTROLIFE V2 — PHASE 6A: DYNAMIC RULE KNOWLEDGE SPEC AUDIT

**Date:** 2026-09-04
**Scope:** Pre-implementation audit for Phase 6A (knowledge schema + validation contract only)
**Status:** Audit Complete — Ready for Implementation

---

## 1. What Can Be Reused (untouched)

* 5A `RuleDefinition`/`RuleMetadata`/`Condition` shape (conceptual precedent for
  formation/cancellation/mitigation separation), `RuleRegistry` version-compare
  semantics (tuple-based; mirrored, not imported for mutation), validators'
  diagnostics style (string lists → upgraded to structured diagnostics),
  `Provenance`/`SourceType`/`RuleTradition`/`ConfidenceLevel` enums as conceptual
  reference (NOT extended — accepted enums frozen).
* 5F dependency/conflict/validator patterns (metadata-level deps, report-only
  analysis, UNVERIFIED enforcement) and UNKNOWN semantics (missing ⇒ UNKNOWN).
* 5G-H multi-tradition isolation (`CharaDashaProfileID` precedent for explicit
  profile IDs) and 5H timestamp-free modeling discipline.
* `RuleContext` accessor names ground DSL fact-path vocabulary
  (`natal.{planet}.sign`, `varga.D9.{planet}`, `jaimini.*`, `dasha.*`,
  `transit.*`, `strength.*`).

## 2. What Must Be Extended (new package `backend/core/rules/dynamic/`)

New, timestamp-free, dependency-free-of-accepted-mutation: `schema.py`
(DynamicRuleDefinition + SourceReference with 7 verification states),
`dsl.py` (data-only condition trees + code-pattern rejection),
`evaluator.py` (FactResolver interface, UNKNOWN propagation, separated
formation/cancellation/mitigation), `validators.py` (structured diagnostics,
firewall, cycles), `registry.py` (DynamicRuleRegistry — new registry, accepted
`RuleRegistry` untouched), `serialization.py` (canonical byte-stable JSON).

## 3. What Must Remain Untouched

All accepted code: 5A engine/registry/evaluator/enums, parashari, doshas,
entire `core/jaimini` (incl. `timing/`, `candidates.py`, `mappings.py`,
`dasha/`, `reference.py`), calculation, varga, Vimshottari, strength,
transit, legacy `backend/jaimini.py`, routes, frontend, existing tests/snapshots.

## 4. Regression Reality (verified this pass)

Existing suites: 5G 38/38, 5G-H 63/63, 5H-timing 57/57 (pytest). Prompt-listed
"Phase 5H-H" has docs only (no test file) → will report NOT EXECUTED (docs
aren't tests), not fabricated. Dasha/Dynamic suites need repo-root invocation.

## 5. Key Design Decisions

* Dynamic rules are pure DATA (Pydantic models); evaluation resolves declared
  fact paths through a caller-supplied resolver — undeclared access rejected,
  missing facts ⇒ UNKNOWN (never FALSE).
* Firewall is an explicit per-tradition namespace table, not tribal knowledge.
* Versions immutable; supersedes/deprecated_by lifecycle; deterministic semver
  compare; duplicate version registration rejected.
* Golden synthetic rule is CUSTOM_DEVELOPER/USER_SUPPLIED/UNVERIFIED and makes
  no classical claims.
