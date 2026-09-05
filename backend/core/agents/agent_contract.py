"""
Phase 7 — immutable agent contracts + capability declarations (§3, §23).

Each specialized agent declares READ (sections of AgentContext it may use),
WRITE: none, CALCULATE: none, PREDICT: forbidden, plus accepted/required
inputs, traditions, and policies. The router rejects out-of-capability
requests structurally.
"""
from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

CHART_SYNTHESIS_AGENT = "CHART_SYNTHESIS_AGENT"
PARASHARI_AGENT = "PARASHARI_AGENT"
JAIMINI_AGENT = "JAIMINI_AGENT"
STRENGTH_AGENT = "STRENGTH_AGENT"
YOGA_DOSHA_AGENT = "YOGA_DOSHA_AGENT"
TIMING_AGENT = "TIMING_AGENT"

ALL_AGENTS = (CHART_SYNTHESIS_AGENT, PARASHARI_AGENT, JAIMINI_AGENT,
              STRENGTH_AGENT, YOGA_DOSHA_AGENT, TIMING_AGENT)

DOMAINS = ("SYNTHESIS", "PARASHARI", "JAIMINI", "STRENGTH", "YOGA_DOSHA", "TIMING")


class AgentContract(BaseModel):
    agent_id: str
    agent_version: str = "7.0.0"
    domain: str = ""
    accepted_inputs: List[str] = Field(default_factory=list)
    required_inputs: List[str] = Field(default_factory=list)
    optional_inputs: List[str] = Field(default_factory=list)
    output_schema: str = "AgentResult/7.0.0"
    allowed_operations: List[str] = Field(default_factory=list)
    forbidden_operations: List[str] = Field(
        default_factory=lambda: ["CALCULATE", "WRITE_CANONICAL", "PREDICT",
                                 "RESOLVE_CONFLICT", "FABRICATE_SOURCE"])
    allowed_traditions: List[str] = Field(default_factory=list)
    supported_profiles: List[str] = Field(default_factory=list)
    provenance_policy: str = "CHAIN_REQUIRED"
    conflict_policy: str = "PROPAGATE_CONFLICTED"
    unknown_policy: str = "PROPAGATE_UNKNOWN"
    deterministic_mode: bool = True

    model_config = {"frozen": True, "extra": "forbid"}

    def can_read(self, section: str) -> bool:
        return section in self.accepted_inputs

    def capability(self) -> Dict[str, object]:
        return {"READ": list(self.accepted_inputs), "WRITE": [],
                "CALCULATE": [], "PREDICT": "forbidden"}


def _contract(agent_id: str, domain: str, accepted: List[str], required: List[str],
              optional: List[str], traditions: List[str],
              profiles: List[str] | None = None) -> AgentContract:
    return AgentContract(
        agent_id=agent_id, domain=domain, accepted_inputs=accepted,
        required_inputs=required, optional_inputs=optional,
        allowed_operations=["READ_CANONICAL_SUMMARY", "RESTATE_FACT",
                            "RESTATE_RULE_RESULT", "SYNTHESIZE_SUPPLIED",
                            "REPORT_UNKNOWN", "REPORT_CONFLICT"],
        allowed_traditions=traditions,
        supported_profiles=list(profiles or []))


CONTRACTS: Dict[str, AgentContract] = {
    CHART_SYNTHESIS_AGENT: _contract(
        CHART_SYNTHESIS_AGENT, "SYNTHESIS",
        ["facts", "vargas", "strength", "dignity", "rules", "doshas", "jaimini",
         "jaimini_rules", "dasha", "transit", "timing", "applicability",
         "evidence_ids", "conflicts", "sources"],
        ["facts"],
        ["vargas", "strength", "dignity", "rules", "doshas", "jaimini",
         "jaimini_rules", "dasha", "transit", "timing", "applicability",
         "evidence_ids", "conflicts", "sources"],
        ["PARASHARI_CLASSICAL", "JAIMINI_CLASSICAL", "TRADITION_DEPENDENT",
         "MODERN_COMMON", "CUSTOM_DEVELOPER"]),
    PARASHARI_AGENT: _contract(
        PARASHARI_AGENT, "PARASHARI",
        ["facts", "vargas", "strength", "dignity", "rules", "doshas", "dasha",
         "transit", "applicability", "evidence_ids", "conflicts", "sources"],
        ["facts", "rules"],
        ["vargas", "strength", "dignity", "doshas", "dasha", "transit",
         "applicability", "evidence_ids", "conflicts", "sources"],
        ["PARASHARI_CLASSICAL", "TRADITION_DEPENDENT", "MODERN_COMMON"]),
    JAIMINI_AGENT: _contract(
        JAIMINI_AGENT, "JAIMINI",
        ["facts", "vargas", "jaimini", "jaimini_rules", "dasha", "timing",
         "applicability", "evidence_ids", "conflicts", "sources"],
        ["jaimini", "jaimini_rules"],
        ["facts", "vargas", "dasha", "timing", "applicability",
         "evidence_ids", "conflicts", "sources"],
        ["JAIMINI_CLASSICAL", "TRADITION_DEPENDENT"],
        ["CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL",
         "CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED",
         "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS"]),
    STRENGTH_AGENT: _contract(
        STRENGTH_AGENT, "STRENGTH",
        ["facts", "strength", "dignity", "applicability", "evidence_ids",
         "conflicts", "sources"],
        ["strength"],
        ["facts", "dignity", "applicability", "evidence_ids", "conflicts", "sources"],
        ["PARASHARI_CLASSICAL", "TRADITION_DEPENDENT", "MODERN_COMMON",
         "CUSTOM_DEVELOPER"]),
    YOGA_DOSHA_AGENT: _contract(
        YOGA_DOSHA_AGENT, "YOGA_DOSHA",
        ["rules", "doshas", "jaimini_rules", "applicability", "evidence_ids",
         "conflicts", "sources", "facts"],
        ["rules", "doshas"],
        ["jaimini_rules", "applicability", "evidence_ids", "conflicts",
         "sources", "facts"],
        ["PARASHARI_CLASSICAL", "JAIMINI_CLASSICAL", "TRADITION_DEPENDENT",
         "MODERN_COMMON"]),
    TIMING_AGENT: _contract(
        TIMING_AGENT, "TIMING",
        ["dasha", "transit", "timing", "applicability", "evidence_ids",
         "conflicts", "sources"],
        ["timing"],
        ["dasha", "transit", "applicability", "evidence_ids", "conflicts", "sources"],
        ["PARASHARI_CLASSICAL", "JAIMINI_CLASSICAL", "TRADITION_DEPENDENT",
         "MODERN_COMMON", "CUSTOM_DEVELOPER"]),
}


def get_contract(agent_id: str) -> AgentContract:
    contract = CONTRACTS.get(agent_id)
    if contract is None:
        raise KeyError(f"Unknown agent {agent_id!r}")
    return contract


def capability_matrix() -> Dict[str, Dict[str, object]]:
    return {agent_id: c.capability() for agent_id, c in sorted(CONTRACTS.items())}
