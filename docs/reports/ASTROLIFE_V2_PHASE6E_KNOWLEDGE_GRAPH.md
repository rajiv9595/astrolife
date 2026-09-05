# ASTROLIFE V2 — PHASE 6E KNOWLEDGE GRAPH

**Builder:** `build_knowledge_graph(catalogue)` → `KnowledgeGraph`
(canonical dict + sha256 fingerprint, 50-run deterministic).

## 1. Relation to EvidenceGraph

`EvidenceGraph` (6D) models a **single evaluation's** evidence trail
(RESULT → CONDITION → EVIDENCE → FACT → SOURCE → CLAIM). The 6E knowledge
graph models the **whole catalogue**: which rules exist, what they require,
what supports them, what conflicts with them. Complementary views; nothing
duplicated — 6E reuses resolver evidence ids as edge annotations where they
exist.

## 2. Node types (§23)

RULE, RULE_VERSION, SOURCE, EVIDENCE, CLAIM, FACT, VARGA, DASHA, TRANSIT,
STRENGTH, JAIMINI, CONFLICT, PROFILE. (CLAIM nodes attach where claim-linked
evidence exists; golden classical entries carry sources rather than claims.)

## 3. Edge types (§23)

SUPPORTS (source→version), DEPENDS_ON (version→rule), REQUIRES
(version→fact/varga/dasha), CONFLICTS_WITH (rule→conflict),
SUPERSEDES (version→version), DERIVED_FROM (version→rule), EVALUATES
(evidence→version), APPLIES_TO (fact/profile→version).

## 4. Determinism

Nodes sorted by `node_id`, edges by `(from_id, to_id, relation)`;
frozen models; canonical JSON fingerprint. Rebuilt identically across 50 runs.

## 5. Health (§22)

`RuleKnowledgeHealth` per entry: schema_valid, security_valid,
dependency_valid, provenance_valid, tests_valid, lifecycle_valid,
catalogue_valid, applicability_valid. Eight booleans; never collapsed to a
numeric score.
