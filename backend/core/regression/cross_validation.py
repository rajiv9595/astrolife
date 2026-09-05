"""
Phase 10 — cross-layer / cross-engine consistency: the same fact must
appear identically wherever consumed. Disagreement = FAIL, no auto-resolve.
"""
from __future__ import annotations

from typing import Any, Dict, List


def check_same_longitude(planet: str, values: List[float], tol: float = 1e-9) -> bool:
    return max(values) - min(values) <= tol


def check_same_categorical(values: List[Any]) -> bool:
    return len(set(values)) == 1


def consistency_report(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    bad = [e for e in entries if not e.get("consistent")]
    return {"total": len(entries), "consistent": len(entries) - len(bad),
            "inconsistent": [e.get("name") for e in bad]}
