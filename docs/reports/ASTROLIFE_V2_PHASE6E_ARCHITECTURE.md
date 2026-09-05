# ASTROLIFE V2 — PHASE 6E ARCHITECTURE

**Module:** `backend/core/rules/dynamic/knowledge.py` (single new module, ~950 lines)
**Exports:** additive re-export via `backend/core/rules/dynamic/__init__.py` (no existing symbol changed)
**Test suite:** `backend/test_dynamic_rules_phase6e.py` (105 checks)

## 1. Layering

```
Accepted layers (read-only, never modified)
  calculation / varga / dasha / transit / strength / parashari / dosha /
  jaimini / jaimini-dasha / timing
        │ canonical facts (ChartFacts, VargaFacts, StrengthReport,
        │  Vimshottari timeline, TransitSnapshot, JaiminiFacts)
        ▼
6A–6D infrastructure (reused, never duplicated)
  DynamicRuleDefinition · DynamicRuleRegistry · RulePackage · ConditionNode
  required_paths bindings · namespace match · FIREWALL · lifecycle tables
  CanonicalFactResolver · EvidenceBundle · EvidenceGraph · DEPENDENCY_SPECS
  SAME_PROPOSITION_PAIRS · provenance / verification · fingerprint / diff
  dsl suspicious-text scan
        ▼
6E (new, this phase)
  RuleKnowledgeEntry · RuleKnowledgeCatalogue · RuleApplicabilitySpec
  KnowledgeContext · evaluate_rule_applicability · RuleApplicabilityResult
  reverse index · KnowledgeConflict · RuleKnowledgeHealth
  KnowledgeGraph (inspection view) · CatalogueSnapshot (canonical bytes)
  build_golden_catalogue · 14-function internal API
```

## 2. Key decisions

1. **Reuse, not duplication.** Catalogue entries reference accepted objects; specs for
   dynamic rules are derived from the same `required_paths` bindings the 6B engine
   uses, so applicability and evaluation can never drift.
2. **Classical ingestion is metadata-only.** Parashari/Dosha entries declare generic
   natal availability; Jaimini entries translate 5F `DEPENDENCY_SPECS` into 6E
   requirements. No condition trees are invented, no formation logic added.
3. **Alias normalizers, not new enums.** `normalize_tradition` maps legacy
   `JAIMINI`→`JAIMINI_CLASSICAL`, `CUSTOM`→`CUSTOM_DEVELOPER`;
   `normalize_category` refines legacy `JAIMINI` by rule-id prefix
   (KARAKA / RASHI_DRISHTI / ARUDHA). Existing enums are untouched.
4. **Evaluation order is load-bearing:** identity INVALID → lifecycle gate →
   tradition isolation → profile isolation → prerequisite resolution (UNKNOWN) →
   applicability condition → APPLICABLE. UNKNOWN is never converted to
   NOT_APPLICABLE.
5. **Conflicts are REPORTED_ONLY.** Catalogue exposes conflict records with full
   identity (id, traditions, versions, type); no winner is ever selected.
6. **Health is eight booleans, never a score.** Evidence visibility is counts only.
7. **Snapshots are canonical bytes.** `sort_keys + compact separators` JSON;
   `snapshot_round_trip` asserts byte equality after deserialization.

## 3. Data flow (applicability query)

```
KnowledgeContext(dynamic=DynamicEvaluationContext, tradition, profile)
        │
        ▼
evaluate_rule_applicability(entry, context, catalogue?)
  ├─ identity regex/semver check ──────────────► INVALID / INVALID_RULE
  ├─ unknown rule-dependency targets ──────────► INVALID / DEPENDENCY_INVALID
  ├─ DISABLED ─────────────────────────────────► NOT_APPLICABLE / RULE_DISABLED
  ├─ DEPRECATED/SUPERSEDED/ARCHIVED/REJECTED ──► NOT_APPLICABLE / RULE_DEPRECATED
  ├─ non-active developmental states ──────────► NOT_APPLICABLE / RULE_DISABLED
  ├─ tradition not in allowed ─────────────────► NOT_APPLICABLE / TRADITION_MISMATCH
  ├─ profile not in constraints ───────────────► NOT_APPLICABLE / PROFILE_MISMATCH
  ├─ CanonicalFactResolver probes per requirement class
  │     natal/houses → MISSING_FACT · varga → MISSING_VARGA
  │     dasha → MISSING_DASHA · transit → MISSING_TRANSIT
  │     strength → MISSING_STRENGTH · jaimini → MISSING_JAIMINI
  │     rule outcomes → DEPENDENCY_INVALID ────► UNKNOWN (any missing)
  ├─ applicability_condition FALSE ────────────► NOT_APPLICABLE / CONDITION_FALSE
  ├─ applicability_condition UNKNOWN ──────────► UNKNOWN / MISSING_FACT
  └─ else ─────────────────────────────────────► APPLICABLE / CONDITION_TRUE
```

## 4. Determinism contract

Sorted sets/lists at every boundary (spec fields, manifests, index values,
discovery ordering by tradition/system/category/id/version, snapshot sections,
graph nodes/edges). Frozen pydantic models. No timestamps, no random IDs, no
wall clock. 50-run verification over six artefacts.

## 5. Security contract

All catalogue text (names, descriptions, sources, quotations, claims, notes,
tags) is inert data: scanned with the 6A suspicious-text patterns for health
reporting, never executed. Evaluation never mutates catalogue state
(fingerprint-before/after assertion in tests).
