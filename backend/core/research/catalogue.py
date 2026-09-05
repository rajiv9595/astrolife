"""
Phase 9 — read-only research catalogue. No production mutation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import packages as _pkg
from . import rules as _rules


def get_research_package(package_id: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return _pkg.get_research_package(package_id, version)


def list_research_packages() -> List[Dict[str, Any]]:
    return _pkg.list_research_packages()


def find_research_rules(tradition: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    out = _rules.list_research_rules()
    if tradition:
        out = [r for r in out if r.get("tradition") == tradition]
    if category:
        out = [r for r in out if r.get("category") == category]
    return out


def get_research_rule(rule_id: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return _rules.get_research_rule(rule_id, version)


def get_research_version(rule_id: str, version: str) -> Optional[Dict[str, Any]]:
    return _rules.get_research_version(rule_id, version)


def find_research_dependencies(rule_id: str) -> Dict[str, Any]:
    r = get_research_rule(rule_id) or {}
    return r.get("dependencies", {})


def find_research_evidence(package_id: str) -> List[Dict[str, Any]]:
    p = get_research_package(package_id) or {}
    return list(p.get("evidence", []))


def find_research_conflicts(comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
    from .comparisons import detect_conflicts
    return []


def find_research_experiments(package_id: str) -> List[str]:
    p = get_research_package(package_id) or {}
    return list(p.get("experiments", []))


def get_research_snapshot(snapshot_id: str) -> None:
    return None
