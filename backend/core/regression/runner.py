"""
Phase 10 — runner: execute comparisons, classify failures, separate
ROOT_FAILURE from DERIVED_FAILURE (first-divergence ordering).
"""
from __future__ import annotations

from typing import Any, Dict, List

from .comparators import CompareResult

# Canonical upstream → downstream order for first-divergence analysis.
LAYER_ORDER = ["ChartFacts", "VargaFacts", "Panchanga", "Dasha", "Transit",
               "Strength", "Yoga", "Dosha", "Jaimini", "Rules", "Agents",
               "Prediction", "Research"]


class SuiteReport:
    def __init__(self) -> None:
        self.results: List[CompareResult] = []

    def add(self, r: CompareResult) -> None:
        self.results.append(r)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    def failures(self) -> List[CompareResult]:
        return [r for r in self.results if not r.passed]

    def root_vs_derived(self, layer_of: Dict[str, str]) -> Dict[str, Any]:
        """First-divergent layer = ROOT; later layers = DERIVED."""
        failed_layers = sorted({layer_of.get(r.golden_id, "UNKNOWN") for r in self.failures()},
                               key=lambda l: LAYER_ORDER.index(l) if l in LAYER_ORDER else 999)
        if not failed_layers:
            return {"roots": [], "derived": [], "first_divergent_layer": None}
        first = failed_layers[0]
        return {"roots": [r for r in self.failures() if layer_of.get(r.golden_id) == first],
                "derived": [r for r in self.failures() if layer_of.get(r.golden_id) != first],
                "first_divergent_layer": first}
