"""
Phase 10 — comparators. Every numerical comparison declares exact /
absolute / angular-modulo tolerance. Categorical values: exact only.
No rounding before comparison; report expected/actual/difference/tolerance.
"""
from __future__ import annotations

from typing import Any

from .models import CompareResult, Tolerance


def _angular_diff(a: float, b: float) -> float:
    d = abs(float(a) - float(b)) % 360.0
    return min(d, 360.0 - d)


def compare(golden_id: str, expected: Any, actual: Any,
            tolerance: Tolerance, failure_class: str) -> CompareResult:
    kind = tolerance.kind
    if kind == "exact":
        passed = expected == actual
        diff = None if passed else f"{expected!r} != {actual!r}"
    elif kind == "absolute":
        try:
            diff = abs(float(actual) - float(expected))
        except (TypeError, ValueError):
            return CompareResult(golden_id=golden_id, passed=False, expected=expected,
                                 actual=actual, difference="non-numeric",
                                 tolerance=tolerance, failure_class=failure_class)
        passed = diff <= float(tolerance.value)
    elif kind == "angular":
        try:
            diff = _angular_diff(expected, actual)
        except (TypeError, ValueError):
            return CompareResult(golden_id=golden_id, passed=False, expected=expected,
                                 actual=actual, difference="non-numeric",
                                 tolerance=tolerance, failure_class=failure_class)
        passed = diff <= float(tolerance.value)
    else:
        return CompareResult(golden_id=golden_id, passed=False, expected=expected,
                             actual=actual, difference=f"bad tolerance kind {kind!r}",
                             tolerance=tolerance, failure_class="TEST_INFRASTRUCTURE_FAILURE")
    return CompareResult(golden_id=golden_id, passed=passed, expected=expected,
                         actual=actual, difference=diff, tolerance=tolerance,
                         failure_class="UNKNOWN" if passed else failure_class)


def compare_exact(golden_id: str, expected: Any, actual: Any, failure_class: str) -> CompareResult:
    return compare(golden_id, expected, actual, Tolerance(kind="exact"), failure_class)


def compare_abs(golden_id: str, expected: float, actual: float,
                tol: float, failure_class: str) -> CompareResult:
    return compare(golden_id, expected, actual, Tolerance(kind="absolute", value=tol), failure_class)


def compare_angular(golden_id: str, expected: float, actual: float,
                    tol: float, failure_class: str) -> CompareResult:
    return compare(golden_id, expected, actual, Tolerance(kind="angular", value=tol), failure_class)
