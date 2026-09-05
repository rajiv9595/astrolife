# ASTROLIFE V2 — PHASE 6E APPLICABILITY

## 1. Model (§6)

`RuleApplicabilitySpec`: required_facts, optional_facts, required_vargas,
required_dasha_systems, required_transit_data, required_strength_data,
required_jaimini_data, required_rule_results, tradition_constraints,
profile_constraints, plus an optional availability-level
`applicability_condition` tree. Dynamic specs are derived from the 6B
primitive bindings, so a rule requiring `natal.jupiter.sign` + `varga.D9`
declares both, and a Jaimini Drishti rule declares `jaimini.rashi_drishti`.

## 2. States (§7) — mutually exclusive, never coerced

- **APPLICABLE**: prerequisites available, gates pass.
- **NOT_APPLICABLE**: prerequisites valid but lifecycle/tradition/profile/
  false-condition establishes non-eligibility.
- **UNKNOWN**: required information missing/unavailable.
- **INVALID**: rule/package/dependency itself invalid.

## 3. Reasons (§8) — structured codes, no prose-only verdicts

MISSING_FACT, MISSING_VARGA, MISSING_DASHA, MISSING_TRANSIT, MISSING_STRENGTH,
MISSING_JAIMINI, TRADITION_MISMATCH, PROFILE_MISMATCH, RULE_DISABLED,
RULE_DEPRECATED, DEPENDENCY_INVALID, DEPENDENCY_CONFLICT, CONDITION_FALSE,
CONDITION_TRUE, INVALID_RULE.

## 4. Evaluator (§9) → `RuleApplicabilityResult`

rule_id, rule_version, status, reasons, required_inputs, resolved_inputs,
missing_inputs, tradition, profile, evidence (resolver evidence ids),
dependencies (manifest), fingerprint. Deterministic.

## 5. Separations (§10, §11, §33)

- Applicability = eligibility to evaluate. Formation (FORMED / NOT_FORMED /
  UNKNOWN) belongs to the evaluator; tests assert both independently.
- Applicability output is only the four states. The suite scans all discovery
  output for banned predictive phrasing (`will happen`, `likely event`,
  `high probability`, `future outcome`, `life result`, `recommendation`) — absent.

## 6. Tradition filter (§12)

Queries: ALL, PARASHARI_CLASSICAL, JAIMINI_CLASSICAL, TRADITION_DEPENDENT,
MODERN_COMMON, WESTERN, CUSTOM_DEVELOPER. A JAIMINI query never silently
matches Parashari (asserted on ids and on applicability outcomes).

## 7. Profile filter (§13)

`profile_constraints` (e.g. Chara `MOVABLE_FIXED_DUAL` /
`ODD_EVEN_FOOTED` / `MOVABLE_FIXED_DUAL_ALWAYS`). A rule bound to one profile
never silently evaluates under another (PROFILE_MISMATCH → NOT_APPLICABLE).

## 8. The 13 synthetic cases (§27)

| # | Case | Status | Reason |
|---|---|---|---|
| 1 | all facts available | APPLICABLE | CONDITION_TRUE |
| 2 | missing D9 | UNKNOWN | MISSING_VARGA |
| 3 | missing strength | UNKNOWN | MISSING_STRENGTH |
| 4 | missing Vimshottari | UNKNOWN | MISSING_DASHA |
| 5 | missing transit | UNKNOWN | MISSING_TRANSIT |
| 6 | missing Jaimini | UNKNOWN | MISSING_JAIMINI |
| 7 | tradition mismatch | NOT_APPLICABLE | TRADITION_MISMATCH |
| 8 | profile mismatch | NOT_APPLICABLE | PROFILE_MISMATCH |
| 9 | disabled rule | NOT_APPLICABLE | RULE_DISABLED |
| 10 | deprecated rule | NOT_APPLICABLE | RULE_DEPRECATED |
| 11 | invalid dependency | INVALID | DEPENDENCY_INVALID |
| 12 | invalid rule identity | INVALID | INVALID_RULE |
| 13 | false applicability condition | NOT_APPLICABLE | CONDITION_FALSE |
