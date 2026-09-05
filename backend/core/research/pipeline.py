"""
Phase 9 — public pipeline API (all outputs structured + deterministic).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import applicability as _appl
from . import audit as _audit
from . import catalogue as _cat
from . import comparisons as _cmp
from . import coverage as _cov
from . import dependencies as _dep
from . import evidence as _ev
from . import experiments as _exp
from . import graph as _graph
from . import packages as _pkg
from . import promotion as _promo
from . import review as _rev
from . import rules as _rules
from . import snapshots as _snap
from .fixtures import validate_fixture
from .hypotheses import create_hypothesis, create_notebook
from .validation import evaluate_promotion_gates

# packages
create_research_package = _pkg.create_research_package
validate_research_package = _pkg.validate_research_package
get_research_package = _pkg.get_research_package
list_research_packages = _pkg.list_research_packages

# rules
create_research_rule = _rules.create_research_rule
validate_research_rule = _rules.validate_rule
get_research_rule = _rules.get_research_rule
get_research_version = _rules.get_research_version

# experiments / comparison
run_research_experiment = _exp.run_research_experiment
compare_research_rules = _cmp.compare_research_rules


def get_research_coverage(rule: Dict[str, Any], available: Dict[str, List[str]]) -> Dict[str, Any]:
    return _cov.coverage_report(rule, available)


def get_research_applicability(rules: List[Dict[str, Any]], fixtures: List[Dict[str, Any]],
                               traditions: List[str], profiles: List[str]) -> Dict[str, Any]:
    return _appl.applicability_matrix(rules, fixtures, traditions, profiles)


def get_research_dependencies(rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"graph": _dep.build_dependency_graph(rules),
            "issues": _dep.detect_issues(rules)}


def get_research_evidence(package: Dict[str, Any]) -> Dict[str, Any]:
    return _ev.evidence_matrix(package.get("rules", []), package.get("sources", []),
                               package.get("claims", []), package.get("evidence", []))


def get_research_conflicts(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _cmp.detect_conflicts(results)


# snapshots
create_research_snapshot = _snap.create_research_snapshot
load_research_snapshot = _snap.load_research_snapshot

# promotion / review
create_promotion_request = _promo.create_promotion_request
evaluate_promotion_gates = evaluate_promotion_gates
record_review = _rev.record_review
promote_research_rule = _promo.promote_research_rule
get_promotion_audit = _promo.get_promotion_audit

# graph
get_research_graph = _graph.get_research_graph

__all__ = [
    "create_research_package", "validate_research_package", "get_research_package",
    "list_research_packages", "create_research_rule", "validate_research_rule",
    "get_research_rule", "get_research_version", "run_research_experiment",
    "compare_research_rules", "get_research_coverage", "get_research_applicability",
    "get_research_dependencies", "get_research_evidence", "get_research_conflicts",
    "create_research_snapshot", "load_research_snapshot", "create_promotion_request",
    "evaluate_promotion_gates", "record_review", "promote_research_rule",
    "get_promotion_audit", "get_research_graph", "create_hypothesis", "create_notebook",
]
