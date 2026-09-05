"""
Phase 6C — Test fixture system.

RuleTestCase is wholly declarative: no executable Python inside fixtures.
run_rule_tests executes each test case against the rule package and
returns a RuleTestReport. A rule cannot become TESTED unless required
tests pass. "Zero tests = tested" is explicitly disallowed.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Dict, List, Optional

from .evaluator import EvidenceItem, evaluate_rule
from .lifecycle import LifecycleTransitionError
from .rule_package import RulePackage, RuleTestCase, RuleTestReport
from .schema import DynamicRuleDefinition


class RuleTestExecutor:
    """Executes declarative test cases against a RulePackage."""

    def __init__(
        self,
        rule_package: RulePackage,
        context: Optional[Any] = None,
    ) -> None:
        self.pkg = rule_package
        self.rule: DynamicRuleDefinition = rule_package.rule
        self.context = context

    def run_test_case(self, tc: RuleTestCase) -> Dict[str, Any]:
        """Run a single RuleTestCase and return outcome diagnostics."""
        facts = dict(tc.input_fixture)
        declared_inputs = set(self.rule.dependencies.input_facts or [])
        declared_rule_deps = set(self.rule.dependencies.rule_dependencies or [])

        # If context is provided and requested by fixture, use context resolver
        if self.context is not None and facts.get("__use_context__", False):
            from .resolver import CanonicalFactResolver, RESOLVED
            resolver_inst = CanonicalFactResolver(self.context)

            def resolver(path: str) -> Any:
                res = resolver_inst.resolve(path)
                if res.status == RESOLVED:
                    return res.value
                return None
        else:
            def resolver(path: str) -> Any:
                if path in facts:
                    return facts[path]
                if path.startswith("rule:"):
                    dep_id = path[len("rule:"):]
                    return facts.get(path, facts.get(dep_id))
                return None

        try:
            outcome = evaluate_rule(self.rule, resolver)
        except Exception as e:
            return {
                "test_id": tc.test_id,
                "outcome": "FAIL",
                "diagnostics": [f"Test execution error: {e}"],
                "final_rule_state": "ERROR",
                "is_golden": tc.is_golden,
            }

        formation = outcome.formation if outcome.formation else "NOT_FORMED"
        cancellation = outcome.cancellation if outcome.cancellation else "NOT_CANCELLED"
        mitigation = outcome.mitigation if outcome.mitigation else "NOT_MITIGATED"

        # Determine final state
        if formation == "NOT_FORMED":
            final_state = "NOT_FORMED"
        elif formation == "UNKNOWN":
            final_state = "UNKNOWN"
        elif cancellation == "CANCELLED":
            final_state = "CANCELLED"
        elif mitigation == "MITIGATED":
            final_state = "MITIGATED"
        else:
            final_state = "FORMED"

        diagnostics: List[str] = []

        # Check expected formation
        if tc.expected_formation and formation != tc.expected_formation:
            diagnostics.append(
                f"Formation mismatch: got {formation!r}, expected {tc.expected_formation!r}"
            )

        # Check expected cancellation
        if tc.expected_cancellation and cancellation != tc.expected_cancellation:
            diagnostics.append(
                f"Cancellation mismatch: got {cancellation!r}, expected {tc.expected_cancellation!r}"
            )

        # Check expected mitigation
        if tc.expected_mitigation and mitigation != tc.expected_mitigation:
            diagnostics.append(
                f"Mitigation mismatch: got {mitigation!r}, expected {tc.expected_mitigation!r}"
            )

        # Check expected final state
        if tc.expected_final_state and final_state != tc.expected_final_state:
            diagnostics.append(
                f"Final state mismatch: got {final_state!r}, expected {tc.expected_final_state!r}"
            )

        # Check expected UNKNOWN/INVALID
        if tc.expected_unknown_invalid:
            if tc.expected_unknown_invalid == "UNKNOWN":
                if formation != "UNKNOWN" and final_state != "UNKNOWN":
                    diagnostics.append(
                        f"Expected UNKNOWN state, got formation={formation!r}, final_state={final_state!r}"
                    )
            elif tc.expected_unknown_invalid == "INVALID":
                has_invalid = any("UNDECLARED" in d or "INVALID" in d for d in outcome.diagnostics)
                if not has_invalid and final_state not in ("INVALID", "ERROR"):
                    diagnostics.append(
                        f"Expected INVALID diagnostic, but none occurred. Diagnostics: {outcome.diagnostics}"
                    )

        # Check expected evidence
        evidence_nodes = sorted({e.node for e in outcome.evidence})
        if tc.expected_evidence is not None:
            for exp in tc.expected_evidence:
                if exp not in evidence_nodes:
                    diagnostics.append(f"Missing expected evidence node: {exp}")

        # Check expected dependencies
        all_declared_deps = sorted(declared_inputs | {f"rule:{r}" for r in declared_rule_deps} | declared_rule_deps)
        if tc.expected_dependencies is not None:
            for exp in tc.expected_dependencies:
                if exp not in all_declared_deps:
                    diagnostics.append(f"Missing expected dependency declaration: {exp}")

        outcome_str = "PASS" if not diagnostics else "FAIL"
        return {
            "test_id": tc.test_id,
            "outcome": outcome_str,
            "diagnostics": diagnostics,
            "final_rule_state": final_state,
            "is_golden": tc.is_golden,
        }

    def run_all_tests(self, minimum_tests: int = 1) -> RuleTestReport:
        """Run all test cases and return a RuleTestReport."""
        test_cases = self.pkg.test_cases or []
        if len(test_cases) < minimum_tests:
            raise LifecycleTransitionError(
                f"Cannot test a package with fewer than {minimum_tests} test cases (has {len(test_cases)}). "
                "Zero tests = tested is disallowed."
            )

        total = len(test_cases)
        passed = 0
        failed = 0
        skipped = 0
        all_diagnostics: List[str] = []
        fingerprints: List[str] = []

        for tc in test_cases:
            result = self.run_test_case(tc)
            fp_entry = f"{tc.test_id}:{result['outcome']}:{result['final_rule_state']}"
            fingerprints.append(fp_entry)
            if result["outcome"] == "PASS":
                passed += 1
            elif result["outcome"] == "FAIL":
                failed += 1
            else:
                skipped += 1
            all_diagnostics.extend(result["diagnostics"])

        execution_fingerprint = hashlib.sha256(
            "".join(sorted(fingerprints)).encode("utf-8")
        ).hexdigest()

        return RuleTestReport(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            diagnostics=sorted(all_diagnostics),
            execution_fingerprint=execution_fingerprint,
        )


def run_rule_tests(
    rule_package: RulePackage,
    context: Optional[Any] = None,
    minimum_tests: int = 1,
) -> RuleTestReport:
    """Execute all test cases in a rule package and return a deterministic report."""
    executor = RuleTestExecutor(rule_package, context=context)
    return executor.run_all_tests(minimum_tests=minimum_tests)