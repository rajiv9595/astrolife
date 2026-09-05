# Astrolife V2 — Phase 6C Rule Lifecycle Specification

## 1. Lifecycle Overview
Dynamic astrology rules in Astrolife V2 are subject to strict, auditable lifecycle control. A rule cannot be executed as an active production rule without progressing through validation, automated testing, and formal review.

---

## 2. Legal Lifecycle States
The system recognizes nine explicit lifecycle states:

1. **`DRAFT`**: Initial authoring state. Schema fields are populated, but validity and correctness are unverified. Drafts cannot be executed in production.
2. **`VALIDATED`**: Static schema, DSL grammar, provenance completeness, security scan, and dependency checks have passed with zero errors.
3. **`TESTED`**: The rule's declarative test cases have executed with 100% pass rate. "Zero tests = tested" is explicitly forbidden.
4. **`REVIEW_PENDING`**: The rule has been formally submitted for domain/expert review.
5. **`ACTIVE`**: The rule is officially registered and active in the production engine.
6. **`DISABLED`**: The rule is temporarily inactive. It is excluded from normal evaluation, but historical evaluations remain fully reproducible.
7. **`DEPRECATED`**: The rule is superseded by a newer version or marked obsolete. It is excluded from active selection unless explicitly requested.
8. **`ARCHIVED`**: The rule is permanently archived. Historical reproducibility is strictly preserved.
9. **`REJECTED`**: The rule was reviewed and rejected. It must transition back to `DRAFT` for modifications before re-entering the lifecycle.

---

## 3. Transition Matrix

| From State | To State | Legal? | Enforcement / Error |
| :--- | :--- | :--- | :--- |
| `DRAFT` | `VALIDATED` | **YES** | Requires `validate_rule()` with 0 `ERROR` diagnostics. |
| `VALIDATED` | `TESTED` | **YES** | Requires `run_rule_tests()` with >= 1 tests and 0 failures. |
| `TESTED` | `REVIEW_PENDING` | **YES** | Explicit submission by author/developer. |
| `REVIEW_PENDING` | `ACTIVE` | **YES** | Requires `RuleReviewRecord` with decision `APPROVED`. |
| `ACTIVE` | `DISABLED` | **YES** | Administrative or operational deactivation. |
| `ACTIVE` | `DEPRECATED` | **YES** | Superseded by newer version; records `deprecated_by`. |
| `DISABLED` | `ACTIVE` | **YES** | Re-enabling previously disabled rule. |
| `DEPRECATED` | `ARCHIVED` | **YES** | Final archival of deprecated version. |
| `REVIEW_PENDING` | `REJECTED` | **YES** | Reviewer decision `REJECTED`. |
| `REJECTED` | `DRAFT` | **YES** | Developer resets rule to edit and re-validate. |
| `VALIDATED` | `DRAFT` | **YES** | Rule edited; requires re-validation. |
| `TESTED` | `DRAFT` | **YES** | Rule edited; requires re-testing. |
| `DRAFT` | `ACTIVE` | **FORBIDDEN** | Raises `LifecycleTransitionError`. No silent activation. |
| `DRAFT` | `TESTED` | **FORBIDDEN** | Raises `LifecycleTransitionError`. Validation required first. |
| `VALIDATED` | `ACTIVE` | **FORBIDDEN** | Raises `LifecycleTransitionError`. Testing and review required. |
| `ARCHIVED` | `ACTIVE` | **FORBIDDEN** | Raises `LifecycleTransitionError`. Archived rules are immutable. |

---

## 4. Activation Gates
In `activate_rule()`, all of the following requirements are verified before state changes to `ACTIVE`:
1. **Schema & DSL Validation**: 0 errors returned by static validator.
2. **Test Reports**: Non-empty test suite with 0 failures (`report.failed == 0`, `report.total > 0`).
3. **Provenance Verification**: Source verification status must be one of `VERIFIED`, `USER_SUPPLIED`, `TRADITIONAL`, `SECONDARY`, `CUSTOM`.
4. **Dependency Graph Integrity**: No cycles detected across registered rules (`registry.validate_graph()`).
5. **Security Scan**: Zero suspicious executable code patterns (`find_suspicious_text()`).
6. **Explicit Review Record**: An associated `RuleReviewRecord` with decision `APPROVED` must be present.
7. **Current State**: Rule must currently reside in `REVIEW_PENDING`.

---

## 5. Historical Reproducibility
When an active rule is disabled, deprecated, or superseded:
- The rule definition is never deleted from storage.
- The rule version identifier remains immutable.
- Existing historical evaluations specifying an exact version (e.g. `1.0.0`) remain byte-for-byte reproducible.
