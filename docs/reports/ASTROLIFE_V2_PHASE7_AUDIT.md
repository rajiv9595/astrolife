# ASTROLIFE V2 — PHASE 7 AUDIT

**Date:** 2026-09-05
**Scope:** Specialized AI agent layer (interpretation/reasoning ONLY).
No prediction, no forecasting, no second calculation engine.

## 1. Existing deterministic truth layers (Phase 7 reads, never writes)

| Layer | Canonical output | Producer |
|---|---|---|
| Natal calculation | `ChartFacts` (`core/calculation/models.py`, via `pipeline.generate_chart_facts`) | Phase 1 |
| Vargas | `VargaFacts` dict (`core/calculation/varga.calculate_all_vargas`) | Phase 2 |
| Panchanga / Dasha / Transit state | `DynamicAstrologyState`, `DashaTimeline`, `TransitSnapshot` | Phase 3 |
| Classical strength | `StrengthReport` (`core/strength/pipeline.generate_strength_report`: Shadbala, Bhava Bala, Vimsopaka, Avastha, dignity, functional) | Phase 4B |
| Parashari rules | `RuleResult` (`core/rules/models.py`), 31-yoga catalogue, severity/strength grading | Phase 5A/5B |
| Doshas | `DoshaResult` set, 6-rule catalogue | Phase 5C |
| Jaimini foundation | `JaiminiFacts` (karakas, Rashi Drishti, arudha padas, AL, UL, Karakamsha, Swamsa) | Phase 5D |
| Jaimini rules | 12-rule catalogue + results | Phase 5E |
| Evidence / conflicts | `EvidenceBundle`, `EvidenceGraph`, `RuleConflict` (REPORTED_ONLY) | Phase 5F/6D |
| Jaimini Dasha | timelines under 3 explicit Chara profiles | Phase 5G/5G-H |
| Timing candidates | `CandidateEvaluation` / `JaiminiEventCandidate`, convergence, golden snapshots | Phase 5H |
| Dynamic rules | `DynamicRuleDefinition`, `DynamicRuleResult`, `DynamicEvaluationContext` | Phase 6A/6B |
| Rule Lab | `RulePackage`, lifecycle, registry, diff, fingerprints | Phase 6C |
| Knowledge catalogue | `RuleKnowledgeCatalogue`, `RuleApplicabilityResult`, `CatalogueSnapshot`, 14-function read-only API | Phase 6E |

## 2. Existing rule/evidence structures (reused)

`RuleResult`, `DynamicRuleResult`, `EvidenceRecord`, `EvidenceBundle`,
`EvidenceGraph` (+ `build_evidence_graph_from_bundle`, `trace_evaluation`),
`RuleDependencySpec` / `DEPENDENCY_SPECS`, `SAME_PROPOSITION_PAIRS` /
`RuleConflict`, `RuleProvenance` / `SourceRecord` / verification policy.

## 3. Existing applicability structures (reused)

`RuleApplicabilitySpec`, `RuleApplicabilityResult` (APPLICABLE /
NOT_APPLICABLE / UNKNOWN / INVALID + 15 reason codes), `KnowledgeContext`
(renamed on import to avoid clash), discovery modes, reverse index,
`RuleKnowledgeHealth` (8 booleans, no scores).

## 4. Existing timing structures (reused, read-only)

`CandidateEvaluation`, `JaiminiEventCandidate`, dasha/transit activation
records, convergence records, `golden_timing_snapshots/`. Phase 7 consumes
these as supplied data; it never derives dates.

## 5. Existing provenance structures (reused)

6D claim/source/evidence records + verification states
(VERIFIED / UNVERIFIED / CONTESTED / SECONDARY / TRADITIONAL / USER_SUPPLIED).
No competing evidence architecture is created.

## 6. Existing APIs suitable for AI consumption (all read-only)

- `core.rules.dynamic.build_context`, `CanonicalFactResolver`, `evaluate_dynamic_rule`
- 6E catalogue API: `get_rule_catalogue`, `find_rules`, `get_rule`,
  `get_rule_version`, `find_rules_for_context`, `evaluate_rule_applicability`,
  `find_rules_by_{fact,varga,dasha,transit,strength,jaimini_dependency,source}`,
  `find_conflicts`, `get_rule_health`, `get_catalogue_snapshot`
- Classical evaluators (`evaluate_all_parashari`, `evaluate_all_doshas`,
  Jaimini rule pipeline) — fixture construction only, never agent code.

## 7. What Phase 7 adds

`backend/core/agents/`: immutable contracts, structured `AgentContext`
(summaries + fingerprints, JSON-serializable), six specialized deterministic
agents (synthesis over supplied data only), deterministic router, immutable
registry, orchestration pipeline, model-adapter abstraction + deterministic
mock, strict output validator, provenance/conflict/unknown validators,
security firewalls (prompt-injection, prediction, source fabrication),
read-only `KnowledgeAccessor`, `AgentRequest` question layer, execution
records, golden fixture builders. Plus `backend/test_agents_phase7.py`
(≥150 checks) and 7 documentation files.

## 8. What Phase 7 does NOT own (hard boundaries)

Longitudes, ascendant, houses, Vargas, Nakshatra, Panchanga, Dasha dates,
transit positions, Shadbala, Bhava Bala, Vimsopaka, Avastha, dignity, Chara
Karakas, Rashi Drishti, Arudha Padas, Upapada, Karakamsha, Swamsa, yoga/dosha
formation, cancellation, mitigation, dasha/transit activation, event
candidates, catalogue mutation, evidence creation, conflict resolution,
probability scoring, forecasting, life-outcome prediction, recommendations.
Any request touching these computationally is refused or reported UNKNOWN;
agents restate supplied canonical outputs and mark everything else UNKNOWN.
