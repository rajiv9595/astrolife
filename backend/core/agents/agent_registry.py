"""
Phase 7 — immutable AgentRegistry (§13): register/get/list/find-for-domain/
validate/version/snapshot with explicit versioning, deterministic ordering
and fingerprints. Functional updates: register returns a new registry.
"""
from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .agent_contract import ALL_AGENTS, AgentContract, get_contract


class AgentRegistry(BaseModel):
    agents: Dict[str, AgentContract] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}

    def register_agent(self, contract: AgentContract) -> "AgentRegistry":
        data = dict(self.agents)
        data[contract.agent_id] = contract
        return self.model_copy(update={"agents": data})

    def get_agent(self, agent_id: str) -> AgentContract:
        contract = self.agents.get(agent_id)
        if contract is None:
            raise KeyError(f"Unknown agent {agent_id!r}")
        return contract

    def list_agents(self) -> List[AgentContract]:
        return [self.agents[key] for key in sorted(self.agents)]

    def find_agents_for_domain(self, domain: str) -> List[AgentContract]:
        return sorted(
            (c for c in self.agents.values() if c.domain == domain),
            key=lambda c: c.agent_id)

    def get_agent_version(self, agent_id: str) -> str:
        return self.get_agent(agent_id).agent_version

    def validate_agent(self, agent_id: str) -> List[str]:
        notes: List[str] = []
        contract = self.agents.get(agent_id)
        if contract is None:
            return [f"unknown agent {agent_id!r}"]
        if not contract.deterministic_mode:
            notes.append("deterministic_mode must be true")
        if "PREDICT" not in contract.forbidden_operations:
            notes.append("PREDICT must be forbidden")
        if "CALCULATE" not in contract.forbidden_operations:
            notes.append("CALCULATE must be forbidden")
        if not contract.required_inputs:
            notes.append("required_inputs must be non-empty")
        if not contract.allowed_traditions:
            notes.append("allowed_traditions must be non-empty")
        return sorted(notes)

    def snapshot(self) -> Dict[str, object]:
        return {
            "agents": [
                {"agent_id": c.agent_id, "agent_version": c.agent_version,
                 "domain": c.domain,
                 "accepted_inputs": sorted(c.accepted_inputs),
                 "required_inputs": sorted(c.required_inputs),
                 "forbidden_operations": sorted(c.forbidden_operations),
                 "allowed_traditions": sorted(c.allowed_traditions)}
                for c in self.list_agents()
            ]
        }

    def fingerprint(self) -> str:
        payload = json.dumps(self.snapshot(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_default_registry() -> AgentRegistry:
    registry = AgentRegistry()
    for agent_id in ALL_AGENTS:
        registry = registry.register_agent(get_contract(agent_id))
    return registry


def registry_snapshot_round_trip(registry: AgentRegistry) -> bool:
    payload = json.dumps(registry.snapshot(), sort_keys=True, separators=(",", ":"))
    return json.loads(payload) == registry.snapshot()
