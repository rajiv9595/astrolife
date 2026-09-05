# Astrolife V2 — Phase 6C Testing & Verification Specification

## 1. Overview
The Developer Rule Lab enforces declarative, auditable, and deterministic test execution for dynamic rules.

### Core Testing Mandates
1. **No Executable Code in Fixtures**: Test fixtures are purely declarative structures (`RuleTestCase`), specifying inputs and expected outputs as data.
2. **Zero Tests = Tested is Disallowed**: A rule cannot advance to `TESTED` state without executing at least one test case (`minimum_tests >= 1`).
3. **Golden Tests Immutability**: Tests designated with `is_golden = True` execute against immutable synthetic or real canonical chart facts. Expected values must never be silently mutated to make a test pass.
4. **Deterministic Fingerprints**: Every test execution produces a 64-character SHA-256 fingerprint derived from sorted test outcomes and rule states.

---

## 2. Test Case Specification (`RuleTestCase`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `test_id` | `str` | Unique declarative identifier (e.g. `TC01_FORMED`). |
| `description` | `str` | Human-readable specification of what is being tested. |
| `input_fixture` | `Dict[str, Any]` | Map of fact paths to values (e.g. `{"natal.Mars.sign": "Aries"}`). |
| `expected_formation` | `str` | Expected formation outcome: `FORMED`, `NOT_FORMED`, or `UNKNOWN`. |
| `expected_cancellation`| `str` | Expected cancellation: `CANCELLED`, `NOT_CANCELLED`, or `UNKNOWN`. |
| `expected_mitigation` | `str` | Expected mitigation: `MITIGATED`, `NOT_MITIGATED`, or `UNKNOWN`. |
| `expected_final_state` | `str` | Expected combined final state. |
| `expected_unknown_invalid` | `Optional[str]` | Specific check for `UNKNOWN` or `INVALID` diagnostics. |
| `expected_evidence` | `Optional[List[str]]` | Assert that specific evidence node IDs are produced. |
| `expected_dependencies` | `Optional[List[str]]` | Assert that specific fact dependencies are declared. |
| `is_golden` | `bool` | Flag designating the test as an immutable benchmark. |

---

## 3. Test Runner Workflow (`run_rule_tests`)
1. **Minimum Check**: Asserts `len(rule_package.test_cases) >= minimum_tests`. If zero, raises `LifecycleTransitionError`.
2. **Execution**:
   - Synthesizes a fact resolver from `input_fixture` or evaluates against canonical context.
   - Evaluates rule semantics independently (`formation`, `cancellation`, `mitigation`).
   - Compares actual outcomes to expectations.
   - Compiles structured diagnostic messages for any mismatch.
3. **Report Generation**:
   - Returns `RuleTestReport` with `total`, `passed`, `failed`, `skipped`, `diagnostics`, and `execution_fingerprint`.

---

## 4. Golden Test Integration
Two types of golden tests are supported:
1. **Synthetic Golden Fixtures**: Hand-crafted edge cases validating specific combinations (e.g. `DEMO.CUSTOM.SYNTHETIC_GOLDEN` asserting Mars in Aries formation and Mars conjunct Saturn cancellation).
2. **Real Golden Chart Fixtures**: Tests running against the canonical golden chart facts (1985-10-25 05:30 IST).
