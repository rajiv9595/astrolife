# ASTROLIFE V2 — PHASE 8 ARCHITECTURE

**Package:** `backend/core/prediction/` (21 modules)
**Tests:** `backend/test_prediction_phase8.py` — 211/211 passed
**Principle:** deterministic event-hypothesis + timing engine over supplied
canonical outputs. AI explains later; nothing here calls an LLM, ML, or any
recalculation path.

## 1. Module map

| Module | Role |
|---|---|
| `event_types.py` | 16 semantic categories (labels only, zero astrology) |
| `models.py` | Frozen schemas: signals, windows, hypotheses, profiles, requests, results |
| `event_definitions.py` | Versioned declarative registry wiring categories to accepted rule IDs |
| `event_rules.py` | Executable EventRule view (references, never a second DSL) |
| `signals.py` | Signal builders over supplied inputs (verbatim windows, hashed IDs) |
| `formation.py` | Configuration-exists verdicts; ANY/ALL policies; coverage states |
| `activation.py` | Request-window overlap verdicts; rule-activation booleans |
| `independence.py` | Ancestry-disjoint independence + deterministic grouping |
| `convergence.py` | Categorical levels over independent systems |
| `windows.py` | Half-open ISO interval algebra with honest precision |
| `candidates.py` | 10-step generation, ranking with reasons, equivalence dedup |
| `conflicts.py` | Supplied + formation/activity disagreement propagation |
| `uncertainty.py` | Single-implementation re-export (missing ≠ negative) |
| `profiles.py` | Immutable versioned PredictionProfiles + eligibility filters |
| `catalogue.py` | Read-only 6E bridge (exact versions, ancestry, snapshot seal) |
| `provenance.py` | Chain builder, result provenance, byte snapshots |
| `pipeline.py` | `evaluate_prediction` orchestration + timings + AI-compat view |
| `validation.py` | Schema + certainty/score language firewall |
| `security.py` | Hostile-instruction scan (notes are DATA) |
| `golden.py` | Fixture construction from canonical engines (documented audit exclusion) |

## 2. Canonical data flow (§1)

```
CANONICAL FACTS -> RULE/YOGA/DOSHA RESULTS -> ACTIVATION/DASHA/TRANSIT/
CHARA SIGNALS -> CONVERGENCE -> EVENT HYPOTHESIS -> TIMING WINDOW ->
EVIDENCE/PROVENANCE -> CONFLICT/UNCERTAINTY -> PREDICTION RESULT
```

Every arrow restates supplied data. The engine holds no ephemeris, no
weights, no model calls.

## 3. Separation invariants

- FORMATION (configuration exists) ≠ ACTIVATION (window overlap) ≠ TIMING
  (candidate windows). Each has independent status fields.
- EVENT_WINDOW (timing candidate active) ≠ EVENT_OUTCOME (real-world
  occurrence, never claimed).
- Candidate (structured data) ≠ certainty (forbidden language).

## 4. Determinism

Frozen models, sorted collections, sha256 IDs/fingerprints, ISO-only time,
no wall clock/randomness/network. 50-run golden verification: one canonical
fingerprint. Cross-profile/cross-tradition runs preserve distinctions.
