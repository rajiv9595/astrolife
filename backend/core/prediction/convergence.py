"""
Phase 8 — convergence engine (§§16–17).

Counts INDEPENDENT systems (via independence.py), never raw signal counts.
Levels: NONE / SINGLE_SYSTEM / TWO_SYSTEM / MULTI_SYSTEM /
STRONG_MULTI_SYSTEM (threshold from profile convergence_policy; default 4).
Every result exposes contributors, independent systems, dependency graph,
excluded duplicates, and conflicts. No probability mapping exists.
"""
from __future__ import annotations

from typing import Any, Dict, List

from . import independence as independence_mod
from .models import (
    MULTI_SYSTEM,
    NONE,
    SINGLE_SYSTEM,
    STRONG_MULTI_SYSTEM,
    TWO_SYSTEM,
    CONVERGENCE_SIGNAL,
    EventSignal,
)


def calculate_convergence(signals: List[Any], policy: Dict[str, Any]) -> Dict[str, Any]:
    """Returns {level, independent_systems, contributing, graph, duplicates}."""
    eligible = [s for s in signals if s.status in ("ACTIVE", "FORMED")]
    groups = independence_mod.independent_groups(eligible)
    systems = sorted({s.source_system for group in groups for s in group})
    count = len(groups)
    threshold = int(policy.get("strong_threshold", 4))
    if count == 0:
        level = NONE
    elif count == 1:
        level = SINGLE_SYSTEM
    elif count == 2:
        level = TWO_SYSTEM
    elif count < threshold:
        level = MULTI_SYSTEM
    else:
        level = STRONG_MULTI_SYSTEM
    duplicates: List[str] = []
    for group in groups:
        if len(group) > 1:
            duplicates.extend(sorted(s.signal_id for s in group[1:]))
    return {
        "level": level,
        "independent_systems": systems,
        "contributing": sorted(s.signal_id for group in groups for s in group),
        "graph": independence_mod.dependency_graph(eligible),
        "duplicates": sorted(set(duplicates)),
        "group_count": count,
    }


def convergence_signal(result: Dict[str, Any], profile: str) -> EventSignal:
    import hashlib
    digest = hashlib.sha256(
        "|".join(result["contributing"]).encode()).hexdigest()[:12]
    return EventSignal(
        signal_id=f"SIG-CONV-{digest}", source_system="CUSTOM",
        source_type=CONVERGENCE_SIGNAL, source_id=f"convergence:{result['level']}",
        status="ACTIVE" if result["level"] != NONE else "INACTIVE",
        ancestry=[], evidence=[],
        provenance={"origin": "convergence-engine", "level": result["level"],
                    "profile": profile,
                    "note": "derived summary; excluded from independence counting"})
