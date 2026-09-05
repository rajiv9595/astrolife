# Astrolife V2 — Phase 6C Repository Audit & Component Inventory

## 1. Executive Summary
Phase 6C introduces the **Developer Rule Management Backend / Developer Rule Lab** domain layer for Astrolife V2. It builds an explicit, auditable, and deterministic lifecycle around declarative dynamic rules created by developers and domain experts.

Following the project principles:
- **Zero AI**: No natural-language-to-rule generation, no automatic astrology rule generation, no automatic source verification, no prediction, no probability scoring, no AI agents.
- **Backend/Domain Infrastructure Only**: No frontend UI built in this phase; purely domain logic, services, validators, test runners, and audit logging.
- **Protected Calculation Engines**: Canonical astronomy, vargas (D1–D60), Vimshottari/Chara dasha timelines, Shadbala/strength calculations, transits, and Jaimini karakas/padas remain untouched.

---

## 2. Reused Infrastructure
The following accepted infrastructure from Phase 6A, Phase 6B, and earlier calculation phases was completely reused without duplication:

| Component | Source File | Reused Functionality |
| :--- | :--- | :--- |
| `DynamicRuleDefinition` | `core/rules/dynamic/schema.py` | Canonical rule schema: identity, classification, provenance, semantics, dependencies, evidence, lifecycle, validation. |
| `DynamicRuleRegistry` | `core/rules/dynamic/registry.py` | Immutable versioned registry, duplicate rejection, graph cycle detection. |
| `CanonicalFactResolver` | `core/rules/dynamic/resolver.py` | Typed fact resolution (`RESOLVED`, `MISSING`, `INVALID`, `UNAVAILABLE`) over canonical astrology facts. |
| `DynamicEvaluationContext` | `core/rules/dynamic/context.py` | Container for canonical chart facts, vargas, strengths, dashas, transits, and Jaimini. |
| `evaluate_dynamic_rule` | `core/rules/dynamic/engine.py` | Firewall-checked, declared-dependency-enforced dynamic rule evaluator. |
| `validate_rule` | `core/rules/dynamic/validators.py` | Static rule validator for vocabulary, conditions, provenance, firewall, and dependencies. |
| `find_suspicious_text` | `core/rules/dynamic/dsl.py` | Security pattern boundary detecting executable payloads (eval, exec, subprocess, SQL, shell). |
| Canonical Calculation Pipeline | `core/calculation/pipeline.py` | `generate_chart_facts`, `calculate_all_vargas`, `calculate_vimshottari_timeline`, etc. |

---

## 3. Extended Infrastructure
The following components were extended to support the full Phase 6C lifecycle:

| Component | File | Nature of Extension |
| :--- | :--- | :--- |
| `STATUSES` | `core/rules/dynamic/validators.py` | Extended from `{"ACTIVE", "DEPRECATED", "SUPERSEDED", "DRAFT"}` to include all legal lifecycle states: `VALIDATED`, `TESTED`, `REVIEW_PENDING`, `DISABLED`, `ARCHIVED`, `REJECTED`. |
| Pydantic v2 Compatibility | `core/rules/dynamic/import_export.py` | Renamed `json` field in `ExportResult` to `json_payload` (with backward-compatible property) to eliminate Pydantic v2 shadowing warnings. |

---

## 4. New Phase 6C Modules
The following modules compose the Developer Rule Lab domain layer:

| New Module | File Path | Responsibilities |
| :--- | :--- | :--- |
| `lifecycle.py` | `core/rules/dynamic/lifecycle.py` | State machine governing the 9 legal states and 12 legal transitions. Prevents silent activation (`DRAFT -> ACTIVE` raises `LifecycleTransitionError`). |
| `rule_package.py` | `core/rules/dynamic/rule_package.py` | `RulePackage` abstraction binding rule definition, test cases, reports, metadata, canonical serialization, `create_rule_draft()`, and `RuleHealth`. |
| `test_fixture.py` | `core/rules/dynamic/test_fixture.py` | Declarative `RuleTestCase` executor and `run_rule_tests()`. Rejects "zero tests = tested". Generates deterministic execution fingerprints. |
| `activation.py` | `core/rules/dynamic/activation.py` | Safe activation gate (`activate_rule()`) requiring valid schema, zero test failures, valid provenance, no dependency cycles, clean security scan, and review approval. Deactivation: `disable_rule()`, `deprecate_rule()`, `archive_rule()`. |
| `review.py` | `core/rules/dynamic/review.py` | `RuleReviewRecord` and `ReviewWorkflow` supporting `APPROVED`, `REJECTED`, `REQUEST_CHANGES`, `DEFERRED`. Approval is explicit and never inferred from test passes. |
| `audit.py` | `core/rules/dynamic/audit.py` | Append-only immutable `AuditLog` recording every lifecycle mutation event with deterministic audit identifiers and payloads. |
| `fingerprint.py` | `core/rules/dynamic/fingerprint.py` | Deterministic SHA-256 canonical package fingerprinting excluding timestamps, memory addresses, random IDs, and paths. |
| `diff.py` | `core/rules/dynamic/diff.py` | Deterministic semantic diffing (`compare_rule_versions()`) categorizing changes across condition trees, dependencies, provenance, tradition, cancellation, mitigation, and metadata. |
| `import_export.py` | `core/rules/dynamic/import_export.py` | Safe canonical JSON export and import with pre-registration schema validation, security scanning, and duplicate version conflict rejection. |
| `catalogue.py` | `core/rules/dynamic/catalogue.py` | Deterministic querying, filtering (by tradition, category, status, provenance, validation status), and substring searching. |
| `source.py` | `core/rules/dynamic/source.py` | Multi-source attachment (`PRIMARY`, `SECONDARY`, `SUPPORTING`, `CONFLICTING`). Forbids auto-upgrading `UNVERIFIED -> VERIFIED`. Preserves conflicting sources as `CONTESTED`. |
| `preview.py` | `core/rules/dynamic/preview.py` | Inspection tools `preview_rule_dependencies()` and `preview_rule_evidence()` mapping rules to facts and canonical sources without interpretation. |
| `service.py` | `core/rules/dynamic/service.py` | Unified `RuleLabService` domain coordinator providing the high-level developer API. |
| `test_dynamic_rules_phase6c.py` | `test_dynamic_rules_phase6c.py` | Comprehensive test suite containing 115 checks with 100% pass rate. |
