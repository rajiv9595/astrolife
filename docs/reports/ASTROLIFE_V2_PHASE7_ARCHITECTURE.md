# ASTROLIFE V2 — PHASE 7 ARCHITECTURE

**Package:** `backend/core/agents/` (17 modules + `adapters/` + `agents/`)
**Tests:** `backend/test_agents_phase7.py` — 168/168 passed
**Principle:** deterministic truth layers (Phases 1–6E) are authoritative;
agents are a read-only interpretation layer. No second calculation engine,
no prediction, no Phase 8.

## 1. Module map

| Module | Role |
|---|---|
| `agent_models.py` | Finding (7 types), statuses (5), categorical confidence (5 labels), provenance, rule/conflict/timing summaries, execution records |
| `agent_context.py` | `AgentRequest` (question as DATA), `AgentContext` (JSON summaries + fingerprints), `CanonicalBundle` (orchestrator-side only), read-only `KnowledgeAccessor` over the 6E API |
| `agent_contract.py` | Six immutable contracts + capability matrix (READ lists, WRITE/CALCULATE empty, PREDICT forbidden) |
| `agent_result.py` | `AgentResult` schema + strict validator (rejects unknown fields, invented IDs, overrides, prediction, numeric scores — INVALID, never repaired) |
| `agent_registry.py` | Immutable functional registry: register/get/list/domain/version/snapshot/fingerprint |
| `agent_router.py` | Config-based deterministic routing incl. tradition/profile rejection |
| `agent_validation.py` | Context/applicability/capability gates; provenance/conflict/unknown post-validation |
| `agent_provenance.py` | Provenance chains reusing 6D evidence ids; conflict propagation helpers |
| `agent_conflicts.py` | Single-implementation re-export (one conflict semantics) |
| `agent_security.py` | Injection/prediction detectors, stable digests, prompt-firewall text |
| `agent_prompts.py` | Structured prompt envelopes (data for future adapters; enforcement is code) |
| `orchestrator.py` | §15 pipeline + FULL synthesis path + catalogue-unchanged seal + bundle digests |
| `adapters/base.py` | `AgentModelAdapter` ABC (no vendor) |
| `adapters/mock.py` | `DeterministicMockAdapter` (valid/invalid/predictive/fabricated_source/override_fact) |
| `agents/*_agent.py` | Six pure-function specialists exposing `CONTRACT` + `build_draft` |
| `golden.py` | Fixture construction from canonical engines (not an agent; documented static-audit exclusion) |

## 2. Data flow

```
CanonicalBundle (live objects, orchestrator only)
  -> summaries -> AgentContext (frozen, fingerprinted)
  -> route(request) -> per agent: build_prompt -> adapter.generate
  -> validate_model_output -> finalize -> provenance/conflict/unknown gates
  -> AgentResult + ExecutionRecord (+ optional synthesis over sub-results)
```

Agents never receive the bundle; mutation is structurally impossible (§28
digests identical before/after across all 8 canonical categories).

## 3. Status precedence

INVALID (bad request/output, tradition/profile refusal, prediction request) >
UNKNOWN (missing required input) > CONFLICTED (domain-relevant supplied
conflicts) > PARTIAL (optional input absent) > SUCCESS.

## 4. Determinism

Frozen models, sorted collections, sha256 fingerprints (context, output,
registry, execution record, catalogue seal), no timestamps in identity, no
randomness, no network. 50-run pipeline verification: identical routing,
input, output, provenance, serialization, final hash.
