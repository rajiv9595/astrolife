"""
Phase 5H — Convergence Classifier.

Classifies the structural convergence level of a candidate based on
how many independent conditions are simultaneously active.

NOT probability. Structural labels only.
"""
from __future__ import annotations

from typing import List

from core.jaimini.candidates import ConvergenceLevel

from .models import DashaActivationRecord, TransitConditionRecord


def classify_convergence(
    dasha_activations: List[DashaActivationRecord],
    transit_conditions: List[TransitConditionRecord],
) -> str:
    """Classify convergence based on active conditions.

    Returns one of: SINGLE_CONDITION, DOUBLE_CONDITION, MULTI_CONDITION.

    Classification logic:
    - SINGLE_CONDITION: dasha activation only, no transit conditions met
    - DOUBLE_CONDITION: dasha + exactly 1 transit condition met
    - MULTI_CONDITION: dasha + 2+ transit conditions met, or
      dasha + 1 transit + multiple dasha levels active
    """
    n_dasha = len(dasha_activations)
    n_transit = len(transit_conditions)

    if n_transit == 0:
        return ConvergenceLevel.SINGLE_CONDITION.value
    elif n_transit == 1 and n_dasha <= 1:
        return ConvergenceLevel.DOUBLE_CONDITION.value
    else:
        return ConvergenceLevel.MULTI_CONDITION.value


def convergence_from_counts(
    n_dasha_levels: int,
    n_transit_conditions: int,
) -> str:
    """Classify convergence from pre-computed counts.

    Useful for testing and pipelines that already have counts.
    """
    if n_transit_conditions == 0:
        return ConvergenceLevel.SINGLE_CONDITION.value
    elif n_transit_conditions == 1 and n_dasha_levels <= 1:
        return ConvergenceLevel.DOUBLE_CONDITION.value
    else:
        return ConvergenceLevel.MULTI_CONDITION.value
