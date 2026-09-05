"""Phase 7 — agents package public surface."""
from core.agents.agent_conflicts import conflict_findings, conflict_ids, relevant_conflicts
from core.agents.agent_context import (
    AgentContext,
    AgentRequest,
    CanonicalBundle,
    KnowledgeAccessor,
)
from core.agents.agent_contract import (
    ALL_AGENTS,
    CHART_SYNTHESIS_AGENT,
    JAIMINI_AGENT,
    PARASHARI_AGENT,
    STRENGTH_AGENT,
    TIMING_AGENT,
    YOGA_DOSHA_AGENT,
    CONTRACTS,
    AgentContract,
    capability_matrix,
    get_contract,
)
from core.agents.agent_models import (
    AGENT_STATUSES,
    CANONICAL,
    CONFLICT,
    DERIVED_FACT,
    FACT,
    FINDING_TYPES,
    INTERPRETATION,
    RULE_RESULT,
    SUPPLIED_RESULT,
    SUPPORTED,
    TRADITION_DEPENDENT,
    UNKNOWN,
    UNSUPPORTED_INTERPRETATION,
    WARNING,
    AgentProvenance,
    ConflictSummary,
    ExecutionRecord,
    Finding,
    RuleResultSummary,
    TimingCandidateSummary,
)
from core.agents.agent_prompts import build_prompt
from core.agents.agent_provenance import build_provenance
from core.agents.agent_registry import (
    AgentRegistry,
    build_default_registry,
    registry_snapshot_round_trip,
)
from core.agents.agent_result import (
    AgentResult,
    finalize_result,
    invalid_result,
    validate_model_output,
)
from core.agents.agent_router import DOMAIN_ROUTES, route, route_single
from core.agents.agent_security import (
    PROMPT_FIREWALL_INSTRUCTIONS,
    find_injections,
    find_predictions,
    stable_digest,
)
from core.agents.agent_validation import (
    applicability_gate,
    validate_capability,
    validate_conflicts,
    validate_context,
    validate_provenance,
    validate_traditions,
    validate_unknowns,
)
from core.agents.orchestrator import (
    OrchestrationReport,
    bundle_digest,
    run_full_with_synthesis,
    run_request,
)

__all__ = [
    "ALL_AGENTS", "CHART_SYNTHESIS_AGENT", "JAIMINI_AGENT", "PARASHARI_AGENT",
    "STRENGTH_AGENT", "TIMING_AGENT", "YOGA_DOSHA_AGENT", "CONTRACTS",
    "AgentContract", "capability_matrix", "get_contract", "AGENT_STATUSES",
    "CANONICAL", "CONFLICT", "DERIVED_FACT", "FACT", "FINDING_TYPES",
    "INTERPRETATION", "RULE_RESULT", "SUPPLIED_RESULT", "SUPPORTED",
    "TRADITION_DEPENDENT", "UNKNOWN", "UNSUPPORTED_INTERPRETATION", "WARNING",
    "AgentProvenance", "ConflictSummary", "ExecutionRecord", "Finding",
    "RuleResultSummary", "TimingCandidateSummary", "AgentContext",
    "AgentRequest", "CanonicalBundle", "KnowledgeAccessor", "build_prompt",
    "build_provenance", "AgentRegistry", "build_default_registry",
    "registry_snapshot_round_trip", "AgentResult", "finalize_result",
    "invalid_result", "validate_model_output", "DOMAIN_ROUTES", "route",
    "route_single", "PROMPT_FIREWALL_INSTRUCTIONS", "find_injections",
    "find_predictions", "stable_digest", "applicability_gate",
    "validate_capability", "validate_conflicts", "validate_context",
    "validate_provenance", "validate_traditions", "validate_unknowns",
    "OrchestrationReport", "bundle_digest", "run_full_with_synthesis",
    "run_request",
]
