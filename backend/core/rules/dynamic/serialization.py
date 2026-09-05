"""
Phase 6A — canonical deterministic serialization for dynamic rules.

object → canonical JSON → object → canonical JSON is byte-identical:
sorted keys, compact separators, sorted semantically-unordered lists
(dependencies, prerequisites, derived facts, evidence lists, test
requirements). No timestamps are generated; author-supplied date strings
(effective_from) are preserved verbatim as immutable metadata.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from .schema import DynamicRuleDefinition

_SORTED_LIST_PATHS = {
    "semantics.prerequisites",
    "semantics.derived_facts",
    "dependencies.input_facts",
    "dependencies.rule_dependencies",
    "dependencies.varga_dependencies",
    "dependencies.dasha_dependencies",
    "dependencies.transit_dependencies",
    "dependencies.strength_dependencies",
    "evidence.evidence_requirements",
    "evidence.evidence_paths",
    "validation.test_requirements",
}


def _sort_lists(obj: Any, prefix: str = "") -> Any:
    if isinstance(obj, dict):
        return {k: _sort_lists(v, f"{prefix}.{k}" if prefix else k)
                for k, v in obj.items()}
    if isinstance(obj, list):
        items = [_sort_lists(v, prefix) for v in obj]
        if prefix in _SORTED_LIST_PATHS:
            try:
                return sorted(items)
            except TypeError:
                return sorted(items, key=lambda x: json.dumps(x, sort_keys=True))
        return items
    return obj


def to_canonical_json(rule: DynamicRuleDefinition) -> str:
    payload = _sort_lists(rule.model_dump(mode="json"))
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def from_canonical_json(data: str) -> DynamicRuleDefinition:
    return DynamicRuleDefinition.model_validate(json.loads(data))


def round_trip(data: str) -> str:
    return to_canonical_json(from_canonical_json(data))
