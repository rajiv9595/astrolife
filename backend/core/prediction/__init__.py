"""Phase 8 — prediction package public surface (§59 API)."""
from core.prediction.activation import evaluate_event_activation
from core.prediction.candidates import (
    deduplicate_candidates,
    generate_event_candidates,
)
from core.prediction.catalogue import (
    catalogue_rule_versions,
    catalogue_snapshot_fingerprint,
)
from core.prediction.convergence import calculate_convergence
from core.prediction.event_definitions import (
    EventDefinition,
    get_event_definition,
    list_event_definitions,
    list_event_versions,
)
from core.prediction.event_rules import EventRule, evaluate_event_rule, event_rule_for
from core.prediction.event_types import EVENT_CATEGORIES
from core.prediction.formation import evaluate_event_formation
from core.prediction.models import (
    CANDIDATE_RANKS,
    CONVERGENCE_LEVELS,
    EVIDENCE_STATES,
    HYPOTHESIS_STATUSES,
    PRECISION_UNKNOWN,
    PRECISIONS,
    RESULT_STATUSES,
    SIGNAL_TYPES,
    SOURCE_SYSTEMS,
    DashaPeriodInput,
    EventHypothesis,
    EventSignal,
    PredictionInput,
    PredictionProfile,
    PredictionRequest,
    PredictionResult,
    RuleOutcomeInput,
    SuppliedConflict,
    TimingWindow,
    TransitEventInput,
    SUPPORTED_RANGE_END,
    SUPPORTED_RANGE_START,
)
from core.prediction.pipeline import (
    evaluate_prediction,
    measure_prediction_performance,
    prediction_to_agent_summaries,
)
from core.prediction.profiles import (
    developer_rule_flags,
    eligible_rule_outcomes,
    get_prediction_profile,
    list_prediction_profiles,
    rejected_rule_outcomes,
)
from core.prediction.provenance import (
    build_hypothesis_provenance,
    get_prediction_provenance,
    get_prediction_snapshot,
)
from core.prediction.signals import generate_event_signals
from core.prediction.validation import validate_prediction_result
from core.prediction.windows import (
    clip,
    contains,
    distance,
    intersect,
    overlap,
    union,
)

__all__ = [
    "evaluate_event_activation",
    "deduplicate_candidates",
    "generate_event_candidates",
    "catalogue_rule_versions",
    "catalogue_snapshot_fingerprint",
    "calculate_convergence",
    "EventDefinition",
    "get_event_definition",
    "list_event_definitions",
    "list_event_versions",
    "EventRule",
    "evaluate_event_rule",
    "event_rule_for",
    "EVENT_CATEGORIES",
    "evaluate_event_formation",
    "CANDIDATE_RANKS",
    "CONVERGENCE_LEVELS",
    "EVIDENCE_STATES",
    "HYPOTHESIS_STATUSES",
    "PRECISION_UNKNOWN",
    "PRECISIONS",
    "RESULT_STATUSES",
    "SIGNAL_TYPES",
    "SOURCE_SYSTEMS",
    "DashaPeriodInput",
    "EventHypothesis",
    "EventSignal",
    "PredictionInput",
    "PredictionProfile",
    "PredictionRequest",
    "PredictionResult",
    "RuleOutcomeInput",
    "SuppliedConflict",
    "TimingWindow",
    "TransitEventInput",
    "SUPPORTED_RANGE_END",
    "SUPPORTED_RANGE_START",
    "evaluate_prediction",
    "measure_prediction_performance",
    "prediction_to_agent_summaries",
    "developer_rule_flags",
    "eligible_rule_outcomes",
    "get_prediction_profile",
    "list_prediction_profiles",
    "rejected_rule_outcomes",
    "build_hypothesis_provenance",
    "get_prediction_provenance",
    "get_prediction_snapshot",
    "generate_event_signals",
    "validate_prediction_result",
    "calculate_timing_windows",
    "clip",
    "contains",
    "distance",
    "intersect",
    "overlap",
    "union",
]


def calculate_timing_windows(signals: list, profile: str) -> list:
    """API helper (§59): wrap active signals as clipped timing windows."""
    from core.prediction.candidates import _signal_windows
    return _signal_windows(list(signals), profile)
