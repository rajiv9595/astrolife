"""Phase 10 — golden/regression framework. Calls canonical systems; duplicates none."""
from . import models, comparators, fingerprints, goldens, fixtures, runner, coverage, boundaries, metamorphic, cross_validation, mutation, security, reports, golden  # noqa: F401
from .reports import manifest, build_report, MANIFEST  # noqa: F401
from .runner import SuiteReport, LAYER_ORDER  # noqa: F401
from .comparators import compare, compare_exact, compare_abs, compare_angular  # noqa: F401
from .models import Tolerance, GoldenValue, CompareResult, Discrepancy  # noqa: F401
