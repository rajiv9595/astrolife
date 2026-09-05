# ASTROLIFE V2 — PHASE 8 AUDIT

**Date:** 2026-09-05
**Scope:** Deterministic event-hypothesis + timing engine. No AI prediction,
no ML, no new astrology, no recalculation.

## 1. Existing timing capabilities (reused, not duplicated)

- `core/calculation/dasha.py`: `calculate_vimshottari_timeline` (120y canonical
  timelines), `get_current_dasha` (pure MD/AD/PD selector over precomputed data).
- `core/transit/`: `calculate_transit_positions` (Swiss Ephemeris outputs),
  `detect_transit_events`, relations/aspects, `TransitSnapshot` + `TransitPlanetPosition`.
- `core/jaimini/timing/`: `TemporalWindow`, `DashaActivationRecord`,
  `TransitConditionRecord`, `CandidateContext`, `CandidateEvaluation`,
  dasha/transit activation, convergence, deduplication, golden snapshots,
  profile isolation across the 3 Chara profiles.
- `core/jaimini/dasha/`: Chara Dasha under MOVABLE_FIXED_DUAL,
  ODD_EVEN_FOOTED, MOVABLE_FIXED_DUAL_ALWAYS (never merged).

## 2. Existing dasha activation

Phase 5G/5G-H records + Phase 7 agent summaries restate precomputed windows.
Phase 8 consumes supplied period rows (system/profile/level/key/start/end/
fingerprint) and only tests overlap against the request window.

## 3. Existing transit activation

Phase 3 transit facts + exact root timestamps consumed as supplied strings.
Phase 8 never calls ephemeris code; window math uses ISO comparisons only.

## 4. Existing Jaimini timing

Chara active windows per explicit profile consumed as data; profile identity
propagated into every signal/window/candidate; no fallback, no collapse.

## 5. Existing convergence structures

`core/jaimini/timing/convergence.py` + 5H `CandidateEvaluation` inform the
design, but Phase 8 implements its own dependency-aware convergence over
event signals (multi-system with ancestry tracking) — the only new
"convergence" logic, operating purely on supplied signals.

## 6. Existing candidate structures

`JaiminiEventCandidate` / `CandidateEvaluation` are referenced as prior art;
Phase 8 defines `EventHypothesis`/`EventCandidate` with formation/activation/
timing separation and categorical ranks (no numeric scores).

## 7. Existing evidence/provenance

6D `EvidenceRecord`/`EvidenceBundle`/`EvidenceGraph`, 5A `RuleResult` +
`Evidence`, 6E catalogue manifests. Phase 8 chains
prediction → hypothesis → signals → canonical results → facts → evidence,
reusing ids, never minting fake records.

## 8. Existing conflicts

`RuleConflict` (REPORTED_ONLY), 6E `KnowledgeConflict`, 5H candidate
conflicts. Phase 8 propagates ACTIVE-vs-INACTIVE and FORMED-vs-NOT_FORMED
disagreements as CONFLICTED with full provenance.

## 9. What Phase 8 adds

`backend/core/prediction/`: event taxonomy (16 categories), declarative
versioned `EventDefinition` registry (wiring accepted rule IDs only),
`EventSignal`/`TimingWindow`/`EventHypothesis`/`PredictionResult` models,
signal builders over supplied inputs, formation/activation separation,
dependency-aware convergence with correlated-signal protection, half-open
window algebra, deterministic candidate generation + dedup, categorical
ranks/confidence, immutable versioned `PredictionProfile`s, structured
`PredictionRequest`, strict validator, security firewall, language firewall
(structured-data only), golden fixtures, 15-function API.

## 10. Calculations Phase 8 does NOT own

Longitudes, houses, Vargas, Nakshatra, Panchanga, dasha dates, PD synthesis,
transit positions, root-finding, Shadbala, Bhava Bala, Vimsopaka, Avastha,
dignity, karakas, drishti, padas, UL, Karakamsha, Swamsa, yoga/dosha
formation/cancellation/mitigation/activation, event-date derivation from
prose, probabilities, ML weights, LLM calls. Missing layers yield UNKNOWN;
missing PD yields UNKNOWN (never approximated).
