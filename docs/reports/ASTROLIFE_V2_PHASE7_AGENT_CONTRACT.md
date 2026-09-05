# ASTROLIFE V2 — PHASE 7 AGENT CONTRACT

**Source of truth:** `backend/core/agents/agent_contract.py` (frozen pydantic).

## 1. Common contract fields

agent_id, agent_version (`7.0.0`), domain, accepted_inputs, required_inputs,
optional_inputs, output_schema (`AgentResult/7.0.0`), allowed_operations,
forbidden_operations (`CALCULATE`, `WRITE_CANONICAL`, `PREDICT`,
`RESOLVE_CONFLICT`, `FABRICATE_SOURCE`), allowed_traditions,
supported_profiles (Jaimini only: the 3 Chara methods), provenance_policy
(`CHAIN_REQUIRED`), conflict_policy (`PROPAGATE_CONFLICTED`), unknown_policy
(`PROPAGATE_UNKNOWN`), deterministic_mode (`true`).

## 2. Capability matrix (READ / WRITE / CALCULATE / PREDICT)

| Agent | READ | WRITE | CALCULATE | PREDICT |
|---|---|---|---|---|
| CHART_SYNTHESIS_AGENT | facts, vargas, strength, dignity, rules, doshas, jaimini, jaimini_rules, dasha, transit, timing, applicability, evidence_ids, conflicts, sources | none | none | forbidden |
| PARASHARI_AGENT | facts, vargas, strength, dignity, rules, doshas, dasha, transit, applicability, evidence_ids, conflicts, sources | none | none | forbidden |
| JAIMINI_AGENT | facts, vargas, jaimini, jaimini_rules, dasha, timing, applicability, evidence_ids, conflicts, sources | none | none | forbidden |
| STRENGTH_AGENT | facts, strength, dignity, applicability, evidence_ids, conflicts, sources | none | none | forbidden |
| YOGA_DOSHA_AGENT | rules, doshas, jaimini_rules, applicability, evidence_ids, conflicts, sources, facts | none | none | forbidden |
| TIMING_AGENT | dasha, transit, timing, applicability, evidence_ids, conflicts, sources | none | none | forbidden |

Router rejects out-of-capability traditions/profiles before execution.

## 3. Input contract (`AgentContext`)

chart_fingerprint, calculation_profile, facts, vargas, strength, dignity,
rules, doshas, jaimini, jaimini_rules, dasha, transit, timing, applicability,
evidence_ids, conflicts, sources, requested_domain, allowed_traditions,
profile, question (data), output_mode. All JSON-serializable; `extra=forbid`.

## 4. Output contract (`AgentResult`)

agent_id, agent_version, status (SUCCESS/PARTIAL/UNKNOWN/INVALID/CONFLICTED),
summary, findings[] (FACT/DERIVED_FACT/RULE_RESULT/INTERPRETATION/UNKNOWN/
CONFLICT/WARNING with finding_id, statement/data, supporting_inputs,
evidence_ids, rule_ids, categorical confidence_label, tradition, provenance),
facts_used, rule_results_used, interpretations, unknowns, conflicts, evidence,
dependencies, warnings, provenance, input_fingerprint, output_fingerprint.
Human summary is derived presentation; findings are canonical identity.
