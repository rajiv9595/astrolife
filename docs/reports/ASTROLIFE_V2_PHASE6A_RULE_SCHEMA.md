# ASTROLIFE V2 — PHASE 6A: RULE SCHEMA

**Package:** `backend/core/rules/dynamic/` (`schema.py`, `serialization.py`, `registry.py`)
**Schema version:** `6A/1.0.0` · **Status:** IMPLEMENTED & VALIDATED

## 1. DynamicRuleDefinition (frozen Pydantic, no timestamps)

| Block | Fields |
| :--- | :--- |
| identity | rule_id (DOT.SEPARATED.UPPERCASE), rule_version (semver, immutable), rule_name, description |
| classification | system, tradition (6 values), category, subcategory |
| provenance | SourceReference + source_type/author/title/locator, provenance_status, confidence |
| semantics | prerequisites[], formation/cancellation/mitigation ConditionNode trees, derived_facts[] |
| dependencies | input_facts[], rule_dependencies[], varga/dasha/transit/strength_dependencies[] |
| evidence | evidence_requirements[], evidence_paths[] |
| lifecycle | status (ACTIVE/DEPRECATED/SUPERSEDED/DRAFT), effective_from (author data), supersedes, deprecated_by |
| validation | validation_status, validation_notes, test_requirements[] |

## 2. Versioning & Registry

Versions immutable: duplicate (id, version) registration raises
`DuplicateVersionError`; change ⇒ new version. Deterministic semver compare;
`get` (latest), `get(id, version)`, `list_versions`, `list_all`,
`filter_by(tradition/category/verification/validation_status)`, `deprecate`
(lifecycle transition, in-place version preserved), `validate_graph`
(multi-level cycle detection). Accepted 5A `RuleRegistry` untouched.

## 3. Serialization

`to_canonical_json` / `from_canonical_json` / `round_trip`: sorted keys,
compact separators, canonical ordering of semantically-unordered lists;
round-trip byte-identical; order-insensitive equality for dependency lists;
zero generated timestamps.
