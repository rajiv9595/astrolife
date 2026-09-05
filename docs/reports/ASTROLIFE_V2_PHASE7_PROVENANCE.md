# ASTROLIFE V2 — PHASE 7 PROVENANCE

**Rule:** every substantive conclusion chains to supplied inputs; no chain,
no factual claim. Phase 6D evidence architecture is reused; nothing competes
with it.

## 1. Chain shape

`AgentProvenance{agent_id, agent_version, input_fingerprint, evidence_ids,
source_ids, chain[]}` where each link maps
`finding_id -> supporting_inputs + evidence_ids + rule_ids`.

## 2. Enforcement points

1. Builders attach `supporting_inputs` (context fact keys / supplied rule
   ids) and `evidence_ids` (subset of `context.evidence_ids`) at construction.
2. Strict validator rejects invented rule/evidence/input references,
   FACT findings whose value differs from canonical input (override
   detection), RULE_RESULT findings diverging from supplied outcomes, and
   unsupported INTERPRETATION (unless labeled UNSUPPORTED_INTERPRETATION).
3. Post-validation (`validate_provenance`) re-checks chains and the
   input-fingerprint binding on every orchestrated result.

## 3. Evidence integration

Findings cite existing evidence ids (e.g. `classic-ev:<rule>:<nn>` fixture
keys over classical evidence lists). Validators prove no fake
EvidenceRecord can pass: invented ids -> INVALID.

## 4. Catalogue integration

`KnowledgeAccessor` reuses the 6E read-only API (`get_rule`, `find_rules`,
`find_rules_for_context`, `get_applicability`, `find_conflicts`,
`get_rule_health`, `get_evidence`, `get_dependencies`). Catalogue
fingerprints before/after every run are asserted equal (`catalogue unchanged`
seal in orchestration notes).
