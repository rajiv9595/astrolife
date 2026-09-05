"""
Phase 10 — controlled mutation testing on in-memory copies only.
Production files are never mutated. The suite must detect each mutation.
"""
from __future__ import annotations

import copy
from typing import Any, Callable, Dict, List


def mutate(mapping: Dict[str, Any], path: List[str], new_value: Any) -> Dict[str, Any]:
    out = copy.deepcopy(mapping)
    node = out
    for p in path[:-1]:
        node = node[p]
    node[path[-1]] = new_value
    return out


def detect_mutation(check: Callable[[Dict[str, Any]], bool],
                    original: Dict[str, Any], mutated: Dict[str, Any]) -> bool:
    """True when the check passes on original but fails on mutated."""
    return bool(check(original)) and not bool(check(mutated))
