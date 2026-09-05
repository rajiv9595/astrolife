"""
Phase 10 — coverage tracker: COVERED / PARTIAL / NOT_COVERED per area.
Gaps are reported, never hidden.
"""
from __future__ import annotations

from typing import Dict, List

AREAS = ("planets", "signs", "houses", "nakshatras", "vargas", "dasha",
         "panchanga", "transit", "strength", "yogas", "doshas", "jaimini",
         "rules", "agents", "prediction", "research")


class CoverageTracker:
    def __init__(self) -> None:
        self._hits: Dict[str, int] = {a: 0 for a in AREAS}
        self._expected: Dict[str, int] = {a: 0 for a in AREAS}

    def expect(self, area: str, n: int = 1) -> None:
        self._expected[area] = self._expected.get(area, 0) + n

    def hit(self, area: str, n: int = 1) -> None:
        self._hits[area] = self._hits.get(area, 0) + n

    def report(self) -> Dict[str, Dict[str, object]]:
        out = {}
        for a in AREAS:
            e, h = self._expected.get(a, 0), self._hits.get(a, 0)
            state = "NOT_COVERED" if h == 0 else ("COVERED" if h >= e and e > 0 else "PARTIAL")
            out[a] = {"expected": e, "hit": h, "state": state}
        return out
