# ASTROLIFE V2 — PHASE 8 EVENT MODEL

## 1. Taxonomy (§3)

16 categories: RELATIONSHIP, MARRIAGE, CAREER, JOB_CHANGE, PROMOTION,
BUSINESS, EDUCATION, TRAVEL, RELOCATION, PROPERTY, FINANCE, CHILDREN,
HEALTH, SPIRITUAL, LEGAL, OTHER. Labels only — §31 enforced by construction:
no planet-to-event hard-coding exists anywhere (`Mars = career`-style logic
absent; static scan would flag calculation tokens, tests assert category/
definition separation).

## 2. EventDefinition (§4)

event_id, category, name, description, tradition_constraints,
required_rule_families (accepted IDs), required/optional activation signals,
exclusion_signals, timing_requirements, evidence_requirements,
formation_policy (ANY/ALL), version, lifecycle. Registry: 8 entries incl.
EV.CAREER.V1@1.0.0 + @1.1.0 for version-reproducibility proof.

Accepted-rule wiring examples: MARRIAGE → Jaimini UL/A7 rules; WEALTH →
Parashari Dhana + A2/A11; CAREER → Raja family; EDUCATION → Saraswati/
Budha-Aditya. HEALTH has zero coverage → INSUFFICIENT_RULE_COVERAGE (§57).

## 3. EventSignal (§§7–8)

signal_id (deterministic hash), source_system (8 systems), source_type
(10 types), source_id, categorical strength_label, active_from/active_to
(verbatim copies), exact_time (verbatim root), direction, status, ancestry
(canonical fact paths), evidence, provenance. No weights without a profile —
and no profile defines any.

## 4. EventHypothesis (§5)

hypothesis_id (hash), event_type/version, status + formation/activation/
timing triple, coverage, signals, supporting rules/facts/dashas/transits/
jaimini, conflicts, evidence, unknowns, exclusions, convergence, windows,
categorical rank + reason, categorical evidence state, full provenance,
input/output fingerprints. Statuses FORMED/NOT_FORMED/UNKNOWN/CONFLICTED
plus UNSUPPORTED for uncovered categories.
