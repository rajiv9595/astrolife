"""
Transit package — pure SWE engine.

Exports for Phase 3:
 - calculate_transit_positions(evaluation_datetime, profile) -> TransitSnapshot
 - calculate_transits(start_datetime, end_datetime, profile) -> list
 - compute_western_aspects / compute_parashari_aspects / compute_transit_natal_relations
 - detect_transit_events(natal, start, end, profile) -> List[TransitEvent]
"""
from .calculator import calculate_transit_positions, calculate_transits, TransitSnapshot, TransitPlanetPosition
from .aspects import compute_western_aspects, compute_parashari_aspects, compute_transit_natal_relations, WesternAspect, ParashariAspect
from .events import detect_transit_events, TransitEvent
from .search import find_exact_conjunction

__all__ = [
    "calculate_transit_positions", "calculate_transits", "TransitSnapshot", "TransitPlanetPosition",
    "compute_western_aspects", "compute_parashari_aspects", "compute_transit_natal_relations",
    "WesternAspect", "ParashariAspect",
    "detect_transit_events", "TransitEvent",
    "find_exact_conjunction",
]
