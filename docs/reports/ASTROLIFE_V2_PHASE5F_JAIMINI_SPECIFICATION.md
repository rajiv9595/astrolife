# ASTROLIFE V2 — PHASE 5F: JAIMINI SPECIFICATION (HARDENING + INTEGRATION)

**Version:** 1.0.0 (`jaimini-integration/1.0.0`)
**Status:** IMPLEMENTED & VALIDATED
**Nature:** Hardening + integration. No prediction, no dashas, no timing, no AI.

---

## 1. Layer Boundary

```
ChartFacts → VargaFacts(D9) → JaiminiFacts → JaiminiRuleResults → JaiminiEvaluation
   (Ph1)        (Ph2)            (5D)             (5E)                  (5F NEW)
```

5F consumes upstream read-only (verified: upstream dumps byte-identical after
evaluation), recalculates nothing, takes no strength/transit/dasha inputs
(`evaluate_jaimini` has no such parameter — signature-tested).

## 2. New Modules (`backend/core/jaimini/`)

| File | Provides |
| :--- | :--- |
| `evidence.py` | `JaiminiEvidenceGraph`, tiers, `build_evidence_graph` |
| `dependencies.py` | `RuleDependency(Spec)`, 12 declared specs, `dependency_covered`, `detect_dependency_cycles` |
| `conflicts.py` | `RuleConflict`, 5 classes, `analyze_conflicts` (report-only) |
| `rule_validators.py` | `validate_evidence_completeness`, `validate_rule_provenance` |
| `integration.py` | `JaiminiIntegrationProfile`, `JaiminiEvaluation`, `evaluate_jaimini`, UNKNOWN synthesis, policy audit |

## 3. Public API

`evaluate_jaimini(chart_facts, jaimini_facts, varga_facts, profile=None)` →
`JaiminiEvaluation{profile, rules(sorted by rule_id), formed/not_formed/unknown
id lists, conflicts, dependencies, evidence_graph, provenance_summary,
limitations, total}`. 5E `evaluate_jaimini_yogas` unchanged and compatible.

## 4. Policies

* Varga: only the 2 declared D9 rules consume D9 (strip-D9 invariance tested
  for the other 10; missing D9 → UNKNOWN).
* Strength: `strength_dependencies == []` for all rules; policy validator
  rejects any declaration; no strength parameter exists.
* Parashari/Western: no imports except the sanctioned structural constants;
  no hybrid rules; import-scan tested.
* Provenance: UNVERIFIED/TRADITION_DEPENDENT enforced by validator; VERIFIED
  claims rejected.

## 5. UNKNOWN & Tradition Handling

Missing required input → `formation_status == UNCERTAIN`, `formed == False`,
missing-dependency explanation (never NOT_FORMED; confidence never affects
formation). `origin_labels` filter evaluates CLASSICAL_JAIMINI (5) /
TRADITION_DEPENDENT (7) / ALL (12) subsets with consistent formed subsets.

## 6. Determinism & Performance

Timestamp-free models, stable string node IDs, sorted orderings; 50×
byte-identical JSON. Measured golden: cold ≈0.002 s, repeated ≈0.002 s,
graph ≈0.001 s, conflicts ≈0.00007 s. No optimization claimed.
