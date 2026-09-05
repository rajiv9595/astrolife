# ASTROLIFE V2 — PHASE 6B: ARCHITECTURE

**Package additions:** `core/rules/dynamic/` + `namespace.py`, `context.py`,
`resolver.py`, `bindings.py`, `results.py`, `engine.py` (6A files untouched).
**Status:** IMPLEMENTED & VALIDATED · **Profile:** `6B/1.0.0`

## 1. Flow

DynamicRuleDefinition → 6A validation → binding coverage check (INVALID on
undeclared paths) → CanonicalFactResolver → 6A evaluator (UNKNOWN propagates
per-tree) → DynamicRuleResult → audit → optional conflict aggregation.

## 2. Components

* `DynamicEvaluationContext`: canonical sources only (ChartFacts, VargaFacts,
  StrengthReport, Vimshottari timeline + explicit datetime, Chara result +
  explicit datetime, TransitSnapshot, JaiminiFacts, caller aspect map, caller
  rule-outcome map). No computation, no clock.
* `CanonicalFactResolver`: `FactResolution{path,status,value,value_type,
  source_layer,source_id,evidence_id,dependency_id}`; statuses RESOLVED /
  MISSING / INVALID / UNAVAILABLE (layer-absent ⇒ UNAVAILABLE). Dasha activity
  is containment over canonical timelines via `get_current_dasha`; dignity
  mapped to EXALTED/DEBILITATED/OWN/MOOLATRIKONA; houses validated (1–12),
  padas (1–4).
* `bindings.required_paths`: all 22 primitives mapped; `lord_in_house`
  declares lordship + all nine planet-house paths (data-dependent lord, no
  globs). `dasha_active` reads `dasha.{system}.active_sign` (lord for
  Vimshottari, sign for Chara — validator accepts both vocabularies).
* `DynamicRuleResult`: status FORMED|NOT_FORMED|UNKNOWN|INVALID;
  final_state adds FORMED_CANCELLED/FORMED_MITIGATED; resolved/unresolved maps,
  evidence/dependency paths, provenance, profile. No scores, no timestamps.
* Engine: `evaluate_dynamic_rule`, `evaluate_dynamic_rule_by_id`,
  `evaluate_many` (tradition filter + report-only conflicts on shared
  derived_facts), `audit_dynamic_rule_evaluation` (undeclared, missing,
  firewall, drift, unexplained UNKNOWN/INVALID). Rule-existence checks stay
  registry-side (engine documents the split).

## 3. Firewall Summary

Astronomy: import scan (no swisseph/clock/UUID/random); resolver constructs no
VargaPosition and calls no calculator. Varga/Dasha/Transit/Jaimini: read-only
canonical outputs; missing layers ⇒ UNAVAILABLE⇒UNKNOWN. Tradition firewall
re-checked on accessed paths.
