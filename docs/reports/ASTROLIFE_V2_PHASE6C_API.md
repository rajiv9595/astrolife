# Astrolife V2 — Phase 6C Developer Rule Lab Service API

## 1. Overview
The Developer Rule Lab API is exposed via the domain service `RuleLabService` in `backend/core/rules/dynamic/service.py`. It provides a clean, deterministic, and auditable interface for authoring and managing declarative rules.

---

## 2. API Method Reference

### Rule Lifecycle & Authoring
```python
service.create_rule_draft(
    rule_id: str,
    version: str,
    name: str,
    description: str,
    tradition: str,
    category: str,
    provenance: RuleProvenance,
    condition_tree: ConditionNode,
    dependencies: RuleDependencies,
    cancellation_tree: Optional[ConditionNode] = None,
    mitigation_tree: Optional[ConditionNode] = None,
    derived_facts: Optional[List[str]] = None,
    actor: str = "developer",
) -> RulePackage
```
- Creates a new rule draft in the `DRAFT` state.
- Rejects incomplete drafts missing mandatory schema fields.
- Rejects mutation of an existing version.

```python
service.validate_rule(
    rule_id: str,
    version: str,
    actor: str = "developer",
) -> ValidationReport
```
- Runs schema, DSL, vocabulary, provenance, security, and dependency validations.
- If zero errors are found, transitions rule from `DRAFT` to `VALIDATED`.

```python
service.add_test_case(
    rule_id: str,
    version: str,
    test_case: RuleTestCase,
) -> RulePackage
```
- Adds a declarative test case to the package.

```python
service.test_rule(
    rule_id: str,
    version: str,
    context: Optional[Any] = None,
    minimum_tests: int = 1,
    actor: str = "developer",
) -> RuleTestReport
```
- Executes declarative test cases.
- If all tests pass and current state is `VALIDATED`, transitions to `TESTED`.

```python
service.submit_for_review(
    rule_id: str,
    version: str,
    reviewer_type: str = "human",
    notes: str = "",
    provenance_decision: str = "",
    actor: str = "developer",
) -> RuleReviewRecord
```
- Submits a `TESTED` rule for review, transitioning it to `REVIEW_PENDING`.

```python
service.approve_rule(
    review_id: str,
    notes: str = "",
    actor: str = "reviewer",
) -> RuleReviewRecord
```
- Records an explicit `APPROVED` decision on a submitted review.

```python
service.reject_rule(
    review_id: str,
    notes: str = "",
    actor: str = "reviewer",
) -> RuleReviewRecord
```
- Records a `REJECTED` decision, transitioning rule from `REVIEW_PENDING` to `REJECTED`.

```python
service.activate_rule(
    rule_id: str,
    version: str,
    review_id: Optional[str] = None,
    actor: str = "release_manager",
) -> ActivationReport
```
- Verifies all activation gates (schema, zero test failures, valid provenance, no dependency cycles, clean security, review approved).
- Transitions rule from `REVIEW_PENDING` to `ACTIVE` and registers in `DynamicRuleRegistry`.

```python
service.disable_rule(rule_id: str, version: str, reason: str = "", actor: str = "operator") -> RulePackage
service.deprecate_rule(rule_id: str, version: str, deprecated_by: str = "", reason: str = "", actor: str = "developer") -> RulePackage
service.archive_rule(rule_id: str, version: str, reason: str = "", actor: str = "developer") -> RulePackage
```
- Transitions active rules to `DISABLED`, `DEPRECATED`, or `ARCHIVED` without deleting rule definitions or historical reproducibility.

---

### Catalogue & Search
```python
service.get_rule(rule_id: str) -> Optional[DynamicRuleDefinition]
service.get_rule_version(rule_id: str, version: str) -> Optional[DynamicRuleDefinition]
service.get_package(rule_id: str, version: Optional[str] = None) -> Optional[RulePackage]
service.list_rules(tradition: Optional[str] = None, category: Optional[str] = None, status: Optional[str] = None, provenance: Optional[str] = None) -> List[DynamicRuleDefinition]
service.list_versions(rule_id: str) -> List[str]
service.search_rules(pattern: str) -> List[DynamicRuleDefinition]
```
- All catalogue queries return deterministically sorted results (ordered by `rule_id` then `version`).

---

### Semantic Diff
```python
service.compare_rule_versions(rule_id: str, version_a: str, version_b: str) -> RuleDiff
```
- Produces a deterministic `RuleDiff` categorizing additions, removals, and modifications across condition trees, dependencies, provenance, tradition, cancellation, mitigation, and metadata.

---

### Import & Export
```python
service.export_rule_package(rule_id: str, version: str) -> ExportResult
service.import_rule_package(json_str: str, allow_identical: bool = False, actor: str = "importer") -> ImportResult
```
- Exports package to canonical JSON (sorted keys, compact separators, no timestamps/paths).
- Imports package after pre-registration schema validation, security scanning, and duplicate version conflict detection.

---

### Previews & Inspection
```python
service.preview_dependencies(rule_id: str, version: str) -> DependencyPreview
service.preview_evidence(rule_id: str, version: str) -> EvidencePreview
```
- Provides inspection of direct and indirect facts, vargas, dashas, transits, strengths, jaimini dependencies, dependency graphs, and evidence trees without interpretation.

---

### Active Rule Evaluation & Health
```python
service.evaluate_active_rule(rule_id: str, context: Any, version: Optional[str] = None, tradition: Optional[str] = None) -> DynamicRuleResult
service.get_rule_health(rule_id: str, version: str) -> RuleHealth
```
- Deterministically selects and evaluates the exact applicable `ACTIVE` rule version against canonical context facts.
- Computes comprehensive `RuleHealth` status across schema, provenance, dependencies, security, tests, regression, lifecycle, and activation.
