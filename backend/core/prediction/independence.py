"""
Phase 8 — dependency-aware independence (§§16–18).

Two signals are independent iff their source systems differ AND their
causal ancestry (canonical input fact paths) is disjoint. Signals sharing
ancestry are grouped: e.g. two rules both resting on natal.jupiter.sign
contribute ONE independent system, never TWO_SYSTEM convergence.

Ancestry reuses 6E catalogue dependency manifests (input_facts), supplied
per rule outcome in PredictionInput.dependency lists.
"""
from __future__ import annotations

from typing import Any, Dict, List


def ancestry_of(signal: Any) -> List[str]:
    return sorted(signal.ancestry or [])


def are_independent(first: Any, second: Any) -> bool:
    if first.source_system == second.source_system:
        return False
    return not (set(ancestry_of(first)) & set(ancestry_of(second)))


def independent_groups(signals: List[Any]) -> List[List[Any]]:
    """Greedy deterministic grouping: correlated signals share a group.

    Signals are processed in (source_system, source_id) order; each signal
    joins the first group containing a signal it is NOT independent of,
    otherwise it opens a new group. Group count = independent system count.
    """
    ordered = sorted(signals, key=lambda s: (s.source_system, s.source_id))
    groups: List[List[Any]] = []
    for signal in ordered:
        placed = False
        for group in groups:
            if any(not are_independent(signal, member) for member in group):
                group.append(signal)
                placed = True
                break
        if not placed:
            groups.append([signal])
    return groups


def dependency_graph(signals: List[Any]) -> Dict[str, List[str]]:
    return {s.signal_id: ancestry_of(s) for s in
            sorted(signals, key=lambda s: s.signal_id)}
