# ASTROLIFE V2 — PHASE 5H TIMING + EVENT-CANDIDATE ENGINE: REPOSITORY AUDIT

## Status
Phase 5H timing engine scaffolding exists (candidates.py, mappings.py). Timing engine
logic (dasha activation, transit activation, convergence, candidate building, pipeline)
does not yet exist. This audit covers all reusable infrastructure and the implementation plan.

---

## 1. Reusable Infrastructure (Complete, Accepted)

### Phase 5D — Jaimini Facts
- `backend/core/jaimini/models.py` — `JaiminiFacts`, `CharaKarakasReport`, `KarakaItem`, `ArudhaPadaItem`, `UpapadaDetails`, `KarakamshaDetails`, `RashiDrishtiReport`
- `backend/core/jaimini/pipeline.py` — `generate_jaimini_facts(chart_facts, varga_facts, profile) -> JaiminiFacts`
- `backend/core/jaimini/profile.py` — `JaiminiCalculationProfile` (KarakaMethod, RashiDrishtiMethod, ArudhaMethod, UpapadaMethod, CoLordMethod)
- `backend/core/jaimini/context.py` — `JaiminiContext` (read-only convenience wrapper)

### Phase 5E — Jaimini Rules
- `backend/core/jaimini/rules/models.py` — `JaiminiRuleResult`, `FormationEvidenceItem`, `YogaOutcome`, `JaiminiYogaEvaluation`
- `backend/core/jaimini/rules/catalogue.py` — `get_catalogue()` returns 12 rule specs with `JAIMINI_RULE_CATALOGUE` list
- `backend/core/jaimini/rules/evaluators.py` — per-rule evaluator functions

### Phase 5F — Jaimini Integration
- `backend/core/jaimini/integration.py` — `evaluate_jaimini(chart_facts, jaimini_facts, varga_facts, profile) -> JaiminiEvaluation` — full pipeline producing rules, evidence, conflicts, dependencies
- `backend/core/jaimini/evidence.py` — `build_evidence_graph()` producing `JaiminiEvidenceGraph` with `EvidenceNode`/`EvidenceEdge` (tiers: DIRECT_FACT, DERIVED_FACT, RULE_DERIVED)
- `backend/core/jaimini/dependencies.py` — `RuleDependencySpec`, `DEPENDENCY_SPECS` registry, `detect_dependency_cycles()`
- `backend/core/jaimini/conflicts.py` — `analyze_conflicts()`, `RuleConflict` model with conflict classes (DIRECT_CONTRADICTION, DIFFERENT_DIMENSIONS, TRADITION_VARIANT, INSUFFICIENT_INFORMATION)

### Phase 5G — Jaimini Dasha
- `backend/core/jaimini/dasha/models.py` — `JaiminiDashaPeriod` (period_id, level, sign, start_utc_iso, end_utc_iso, duration_years, antardashas), `JaiminiDashaResult`
- `backend/core/jaimini/dasha/pipeline.py` — `calculate_jaimini_dasha(chart_facts, jaimini_facts, profile) -> JaiminiDashaResult`
- `backend/core/jaimini/dasha/profile.py` — `CharaDashaProfileID` enum (3 profiles: MOVABLE_FIXED_DUAL, ODD_EVEN_FOOTED, MOVABLE_FIXED_DUAL_ALWAYS), `JaiminiDashaProfile`, `PROFILE_REGISTRY`, `full_cycle()`, `step()`
- `backend/core/jaimini/dasha/validators.py` — `validate_dasha_result()`
- `backend/core/jaimini/dasha/duration.py` — duration calculation logic
- `backend/core/jaimini/dasha/sequence.py` — sign sequence progression
- `backend/core/jaimini/dasha/reference.py` — reference data

### Phase 5H Scaffolding (Partial — models + mappings only)
- `backend/core/jaimini/candidates.py` — `JaiminiEventCandidate`, `JaiminiTimingEvaluation`, `DashaActivation`, `MappingEntry`, `JaiminiEventCategory`, `TemporalPrecision`, `ConvergenceLevel`, `ConflictType`
- `backend/core/jaimini/mappings.py` — `MappingEntry` registration, `ActivationCondition` enum, `_MAPPING_REGISTRY`, `register_mapping()`, `get_mappings()`, `get_all_mappings()`, `find_mappings_for_category()`, pre-registered 10 rule→event mappings

### Transit (Phases 3/5B)
- `backend/core/transit/calculator.py` — `TransitSnapshot`, `TransitPlanetPosition`, `calculate_transit_positions(eval_dt, profile) -> TransitSnapshot`
- `backend/core/transit/events.py` — `TransitEvent`, `detect_transit_events(natal, start, end, profile) -> List[TransitEvent]` (sign ingress, nakshatra ingress, retrograde/direct station, exact conjunction/opposition)
- `backend/core/transit/aspects.py` — `WesternAspect`, `ParashariAspect`, `TransitNatalRelation`, `compute_western_aspects()`, `compute_parashari_aspects()`, `compute_transit_natal_relations()`
- `backend/core/transit/search.py` — `find_exact_conjunction()`, bisection root-finding

### Phase 5A — Rule Infrastructure
- `backend/core/rules/enums.py` — `FormationStatus`, `StrengthStatus`, `CancellationStatus`, `MitigationStatus`, `ConfidenceLevel`, `SourceType`, `RuleCategory`, `RuleTradition`
- `backend/core/rules/context.py` — `RuleContext`

---

## 2. Bug Found in Scaffolding

### `JaiminiEventCategory.FAMILY` missing from enum
- `mappings.py:292` references `JaiminiEventCategory.FAMILY` but the enum in `candidates.py` does not define `FAMILY`.
- **Fix required before any timing engine code imports `mappings.py`.**
- Add `FAMILY = "FAMILY"` to `JaiminiEventCategory`.

---

## 3. Timing Engine Architecture

### 3.1 Core Data Flow

```
Input:
  JaiminiEvaluation (rules + evidence + conflicts + dependencies)
  JaiminiDashaResult (periods with start/end, nested antardashas)
  TransitSnapshot / TransitEvent[] (transit positions/events)
  JaiminiEventCategory filter (optional)
  Evaluation range [start, end]

Processing:
  1. DASHA ACTIVATION: For each dasha period (maha + antardasha) intersecting
     evaluation range → determine which rules are "active" during that period
     (rule must FORMED in JaiminiEvaluation).
  2. TRANSIT ACTIVATION: For each candidate window → check if transit conditions
     from the mapping's transit_requirements are met (sign ingress, conjunction,
     aspect to relevant natal points).
  3. CONVERGENCE: Count how many independent conditions are active:
     SINGLE_CONDITION (dasha only), DOUBLE_CONDITION (dasha + 1 transit),
     MULTI_CONDITION (dasha + 2+ transits or dasha + transit + rule dependency).
  4. CANDIDATE BUILDING: Construct JaiminiEventCandidate with full evidence,
     temporal precision, provenance, profile isolation.
  5. DEDUPLICATION: Merge overlapping candidates with same rule set + category.
  6. CONFLICT REPORTING: Cross-reference candidate conflicts from Phase 5F infra.
  7. PROFILE ISOLATION: Never merge periods from different Chara Dasha profiles.
```

### 3.2 Temporal Precision Model

| Precision   | Derivation |
|-------------|-----------|
| EXACT       | Transit event time (ingress, station) within candidate window — peak = event time |
| DAY         | Dasha boundary known to day precision; no finer transit event |
| WINDOW      | Overlap of dasha period + evaluation range |
| APPROXIMATE | Multiple dasha levels with day-level boundaries |
| UNKNOWN     | Insufficient data to determine precision |

### 3.3 Evidence Provenance for Candidates

Each candidate must carry:
- `rule_ids`: which FORMED rules activated this candidate
- `dasha_period_ids`: which dasha periods define the time window
- `transit_condition_ids`: which transit conditions are met
- `evidence`: list of evidence paths from canonical facts (reusing Phase 5F evidence graph tier labels)
- `dependencies`: explicit dependency chain
- `conflicts`: conflict type IDs from Phase 5F analysis
- `profile`: exact JaiminiDashaProfileID string (no implicit defaults)

### 3.4 Candidate ID Format

```
{profile_id}:{event_category}:{start_utc_iso}:{end_utc_iso}
```

Deterministic, reproducible, collision-free for a given profile+range.

### 3.5 Candidate Status Lifecycle

```
ACTIVE   → candidate window overlaps current time (determined at query time)
SATISFIED → all conditions confirmed at a specific timestamp
EXPIRED  → candidate window ended without confirmation
```

Status is a read-only classification, never mutated by the engine.

---

## 4. Files to Create

```
backend/core/jaimini/timing/__init__.py
backend/core/jaimini/timing/models.py          — TemporalWindow, CandidateContext, CandidateEvaluation
backend/core/jaimini/timing/dasha_activation.py — DashaActivationEngine
backend/core/jaimini/timing/transit_activation.py — TransitActivationEngine
backend/core/jaimini/timing/convergence.py     — ConvergenceClassifier
backend/core/jaimini/timing/candidates.py      — CandidateBuilder
backend/core/jaimini/timing/deduplication.py   — CandidateDeduplicator
backend/core/jaimini/timing/conflicts.py       — CandidateConflictReporter
backend/core/jaimini/timing/pipeline.py        — evaluate_jaimini_timing() — full pipeline
backend/core/jaimini/timing/profile_isolation.py — ProfileIsolationGuard
backend/core/jaimini/timing/golden.py          — Golden snapshot capture + regression
```

## 5. Files to Modify

```
backend/core/jaimini/candidates.py — Add FAMILY to JaiminiEventCategory enum
```

## 6. Test Plan

- Unit tests for each timing module (dasha activation, transit activation, convergence, candidate building, deduplication, conflict reporting)
- Integration test: full pipeline from JaiminiFacts + DashaResult + TransitSnapshot → JaiminiTimingEvaluation
- Golden snapshot regression: full evaluation of golden chart, byte-identical JSON, 50-run determinism check
- Profile isolation test: evaluations from different profiles never share candidates
- Boundary tests: empty rule set, empty dasha, overlapping windows, zero-duration periods
- Upstream regression: all Phase 1-5G tests pass

---

## 7. Implementation Priority

1. Fix FAMILY enum bug
2. `timing/models.py` — temporal models
3. `timing/dasha_activation.py` — dasha window intersection
4. `timing/transit_activation.py` — transit condition check
5. `timing/convergence.py` — convergence classification
6. `timing/candidates.py` — candidate builder
7. `timing/deduplication.py` — dedup + merge
8. `timing/conflicts.py` — conflict reporting
9. `timing/pipeline.py` — full pipeline
10. `timing/profile_isolation.py` — profile guard
11. `timing/golden.py` — golden snapshots
12. `timing/__init__.py` — public API
13. Tests
14. Regression
