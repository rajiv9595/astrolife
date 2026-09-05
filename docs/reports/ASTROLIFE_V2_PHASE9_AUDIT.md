# ASTROLIFE V2 — PHASE 9 — REPOSITORY AUDIT

## 1. Existing Rule Lab capabilities (Phase 6C)
`backend/core/rules/dynamic/`: `rule_package.py` (RulePackage, RuleTestCase,
RuleTestReport, canonical fingerprints), `test_fixture.py` (RuleTestExecutor,
zero-tests≠tested), `lifecycle.py` (DRAFT→VALIDATED→TESTED→REVIEW_PENDING→ACTIVE
state machine, no silent activation), `review.py`, `import_export.py`,
`serialization.py`, `namespace.py`, `preview.py`, `service.py`, `audit.py`.

## 2. Existing rule lifecycle
Production lifecycle: DRAFT, VALIDATED, TESTED, REVIEW_PENDING, ACTIVE,
DISABLED, DEPRECATED, ARCHIVED, REJECTED. Phase 9 adds a **separate**
research lifecycle (DRAFT, EXPERIMENTAL, VALIDATED, TESTED, REVIEW_PENDING,
APPROVED_FOR_PROMOTION, PROMOTED, REJECTED, ARCHIVED) with **no**
EXPERIMENTAL→ACTIVE edge.

## 3. Existing package/import/export
Canonical JSON (sorted keys, compact separators, no timestamps), sha256
fingerprints, schema validation on import, executable-payload rejection
(`import_export.py`, `serialization.py`, `schema.py`).

## 4. Existing test fixtures
Declarative `RuleTestCase` (formation/cancellation/mitigation/final-state
expectations, golden flag). Phase 9 extends with fixture *kinds*
(positive/negative/boundary/missing_input) and research-level expectations
(applicability, timing, conflicts, evidence state, provenance, status).

## 5. Existing source/evidence architecture (Phase 6D)
`source.py` (SourceRecord: id/category/verification/title/author/publication/
locator/quotation), `claim.py` (ClaimRecord: SOURCE/INTERPRETATION/
IMPLEMENTATION_CLAIM + DEVELOPER_NOTE with independent verification state),
`evidence_record.py`, `evidence_graph.py` (EvidenceGraph nodes/edges, never
replaced by Phase 9 — only extended with research node types).

## 6. Existing dependency architecture (Phase 6A/6B)
`RuleDependencies` (input_facts, rule/varga/dasha/transit/strength deps),
`resolver.py` (CanonicalFactResolver), `evaluator.py` (undeclared access →
diagnostic + MISSING→UNKNOWN, never FALSE). Phase 9 reuses all of it.

## 7. Existing catalogue (Phase 6E)
`knowledge.py`: RuleKnowledgeCatalogue, applicability evaluation,
knowledge graph, conflict finder, golden catalogue, snapshots. Read-only
patterns reused; research catalogue is a **separate** read-only index.

## 8. Existing applicability (Phase 6E)
APPLICABLE / NOT_APPLICABLE / UNKNOWN / INVALID with reasons. Phase 9
reuses the same four states for the RULE×FIXTURE×TRADITION×PROFILE matrix.

## 9. Existing prediction integration (Phase 8)
`backend/core/prediction/`: event definitions/rules, candidates, windows,
convergence, conflicts, provenance, uncertainty, validation. Research timing
stays research-scoped; Phase 8 semantics untouched.

## 10. What Phase 9 adds
`backend/core/research/` (22 files): research package/rule/fixture models,
hypotheses + notebook, deterministic experiment runner (raw match/mismatch
counts, never accuracy), technique/version comparison, contested-conflict
detection, coverage/applicability/evidence/dependency matrices, immutable
snapshots, 12-gate promotion firewall, review records, promotion audit
trail, research graph, security firewall, static audit, golden research
package, public pipeline API (24 functions).

## 11. What Phase 9 explicitly does NOT own
Calculation (ephemeris/houses/Vargas/Dashas/transits/Shadbala), yoga/dosha/
Jaimini formation, production catalogue mutation, statistical inference,
ML/LLM, frontend, Phase 10.
