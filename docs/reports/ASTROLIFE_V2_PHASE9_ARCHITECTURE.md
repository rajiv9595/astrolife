# ASTROLIFE V2 — PHASE 9 — ARCHITECTURE

## Pipeline
RESEARCH INPUT → EXPERIMENTAL RULE → SOURCE/CLAIM/EVIDENCE → DEPENDENCIES →
APPLICABILITY → TEST FIXTURES → VALIDATION → RESEARCH RESULTS →
COMPARISON/CONFLICT → REVIEW → OPTIONAL PROMOTION → PRODUCTION CATALOGUE.

Promotion is explicit or it does not happen.

## Namespaces
- Research: `research://package/rule/version` (isolated in-memory stores in
  `backend/core/research/{packages,rules}.py`).
- Production: `production://rule/version` (existing `RuleRegistry`,
  `RuleKnowledgeCatalogue`). No automatic registration across the boundary.

## Module map (`backend/core/research/`)
| File | Owns |
|---|---|
| `models.py` | statuses, traditions, gates, all research records, canonical JSON + sha256 |
| `packages.py` | package CRUD, fingerprint, JSON export/import |
| `rules.py` | declarative authoring, `research://` URIs, version store |
| `fixtures.py` | positive/negative/boundary/missing_input fixtures |
| `experiments.py` | deterministic runner over Phase 6A evaluator |
| `comparisons.py` | technique matrix, version diffs, contested detection |
| `coverage.py` | required-vs-available analysis (missing = UNKNOWN) |
| `applicability.py` | RULE×FIXTURE×TRADITION×PROFILE matrix |
| `evidence.py` | RULE×SOURCE×CLAIM×EVIDENCE matrix (no scores) |
| `dependencies.py` | graph, missing/invalid/cycle/unsupported/conflict detection |
| `snapshots.py` | immutable snapshots, byte-identical round-trip |
| `catalogue.py` | read-only research index |
| `promotion.py` | PromotionRequest, 12 gates, explicit promote, audit trail |
| `review.py` | APPROVE / REQUEST_CHANGES / REJECT records |
| `graph.py` | research graph (extends, never replaces EvidenceGraph) |
| `security.py` | DSL reuse + anchored checks + probe detection |
| `validation.py` | schema/security/…/lifecycle gate evaluation |
| `hypotheses.py` | hypotheses + notebook (research-tagged notes) |
| `audit.py` | immutability checks + static implementation scan |
| `golden.py` | deterministic golden package (incl. failing + pending promos) |
| `pipeline.py` | 24-function public API |

## Reuse (no duplication)
Phase 6A DSL (`known_ops`, `find_suspicious_text`, `ConditionNode`,
`DynamicRuleDefinition`, `evaluate_rule` with guarded resolver); Phase 6C
package/lifecycle/fixture patterns; Phase 6D source/claim/evidence shapes;
Phase 6E applicability four-states. Research consumes canonical outputs
through approved interfaces and duplicates no formula.

## Determinism
Canonical JSON everywhere, sorted orderings, sha256 fingerprints, no
wall-clock calls, no randomness. Golden workflow verified over 50 runs.
