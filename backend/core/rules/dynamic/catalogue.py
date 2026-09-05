"""
Phase 6C — Rule catalogue and search operations.

Backend catalogue operations with deterministic output:
  list_rules(), get_rule(), get_version(), list_versions(),
  search_rules(), filter_by_tradition(), filter_by_category(),
  filter_by_status(), filter_by_provenance(), filter_by_validation_status().

All output is deterministic (sorted by rule_id then version).
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Union

from .registry import DynamicRuleRegistry
from .rule_package import RulePackage
from .schema import DynamicRuleDefinition


RuleItem = Union[DynamicRuleDefinition, RulePackage]


def _to_rule(item: RuleItem) -> DynamicRuleDefinition:
    if isinstance(item, RulePackage):
        return item.rule
    return item


def _sort_key(item: RuleItem) -> tuple[str, str]:
    r = _to_rule(item)
    return (r.identity.rule_id, r.identity.rule_version)


def list_rules(
    registry: DynamicRuleRegistry,
    tradition: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    provenance: Optional[str] = None,
) -> List[DynamicRuleDefinition]:
    """List rules from registry, optionally filtered. Deterministic ordering by rule_id then version."""
    out = registry.list_all()
    if tradition:
        out = [r for r in out if r.classification.tradition == tradition]
    if category:
        out = [r for r in out if r.classification.category == category]
    if status:
        out = [r for r in out if r.lifecycle.status == status]
    if provenance:
        out = [r for r in out if r.provenance.source_reference.verification_status == provenance]
    out.sort(key=_sort_key)
    return out


def get_rule(registry: DynamicRuleRegistry, rule_id: str) -> Optional[DynamicRuleDefinition]:
    """Get the latest version of a rule by rule_id."""
    return registry.get(rule_id)


def get_version(
    registry: DynamicRuleRegistry,
    rule_id: str,
    version: str,
) -> Optional[DynamicRuleDefinition]:
    """Get a specific exact version of a rule."""
    return registry.get(rule_id, version)


def list_versions(
    registry: DynamicRuleRegistry,
    rule_id: str,
) -> List[str]:
    """List all registered versions of a rule, sorted by semver."""
    return registry.list_versions(rule_id)


def search_rules(
    pattern: str,
    registry: DynamicRuleRegistry,
) -> List[DynamicRuleDefinition]:
    """Search rules by substring pattern matching rule_id, rule_name, or description."""
    all_rules = registry.list_all()
    pat_lower = pattern.lower()
    matches = [
        r for r in all_rules
        if pat_lower in r.identity.rule_id.lower()
        or pat_lower in r.identity.rule_name.lower()
        or pat_lower in (r.identity.description or "").lower()
    ]
    matches.sort(key=_sort_key)
    return matches


def filter_by_tradition(
    rules: Sequence[RuleItem],
    tradition: str,
) -> List[RuleItem]:
    """Filter rules by tradition. Returns deterministic sorted list."""
    filtered = [r for r in rules if _to_rule(r).classification.tradition == tradition]
    return sorted(filtered, key=_sort_key)


def filter_by_category(
    rules: Sequence[RuleItem],
    category: str,
) -> List[RuleItem]:
    """Filter rules by category. Deterministic sorted output."""
    filtered = [r for r in rules if _to_rule(r).classification.category == category]
    return sorted(filtered, key=_sort_key)


def filter_by_status(
    rules: Sequence[RuleItem],
    status: str,
) -> List[RuleItem]:
    """Filter rules by lifecycle status. Deterministic sorted output."""
    filtered = [r for r in rules if _to_rule(r).lifecycle.status == status]
    return sorted(filtered, key=_sort_key)


def filter_by_provenance(
    rules: Sequence[RuleItem],
    verification: str,
) -> List[RuleItem]:
    """Filter rules by provenance verification status. Deterministic sorted output."""
    filtered = [
        r for r in rules
        if _to_rule(r).provenance.source_reference.verification_status == verification
    ]
    return sorted(filtered, key=_sort_key)


def filter_by_validation_status(
    rules: Sequence[RuleItem],
    validation_status: str,
) -> List[RuleItem]:
    """Filter rules by validation status. Deterministic sorted output."""
    filtered = [
        r for r in rules
        if _to_rule(r).validation.validation_status == validation_status
    ]
    return sorted(filtered, key=_sort_key)