"""
Phase 7 — deterministic AgentRouter (§14).

Routing is configuration-based: requested domain -> authorized specialized
agent(s). No LLM decides routing. Tradition/profile mismatches are rejected
before execution. Deterministic ordering everywhere.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .agent_contract import (
    CHART_SYNTHESIS_AGENT,
    JAIMINI_AGENT,
    PARASHARI_AGENT,
    STRENGTH_AGENT,
    TIMING_AGENT,
    YOGA_DOSHA_AGENT,
    get_contract,
)

DOMAIN_ROUTES: Dict[str, List[str]] = {
    "PARASHARI": [PARASHARI_AGENT],
    "JAIMINI": [JAIMINI_AGENT],
    "STRENGTH": [STRENGTH_AGENT],
    "YOGA_DOSHA": [YOGA_DOSHA_AGENT],
    "TIMING": [TIMING_AGENT],
    "SYNTHESIS": [CHART_SYNTHESIS_AGENT],
    "FULL": [PARASHARI_AGENT, JAIMINI_AGENT, STRENGTH_AGENT,
             YOGA_DOSHA_AGENT, TIMING_AGENT, CHART_SYNTHESIS_AGENT],
}


def route(request: Any, context: Any) -> Dict[str, Any]:
    """Deterministic route. Returns {agents, notes, rejected}."""
    agents: List[str] = []
    rejected: List[str] = []
    notes: List[str] = []
    for domain in request.requested_domains:
        route_agents = DOMAIN_ROUTES.get(domain)
        if route_agents is None:
            rejected.append(f"unknown domain {domain!r}")
            continue
        for agent_id in route_agents:
            contract = get_contract(agent_id)
            blocked = [t for t in request.traditions
                       if t not in contract.allowed_traditions]
            if blocked:
                rejected.append(f"{agent_id} rejects traditions {sorted(blocked)}")
                continue
            if contract.supported_profiles and request.profile \
                    and request.profile not in contract.supported_profiles:
                rejected.append(f"{agent_id} rejects profile {request.profile!r}")
                continue
            if agent_id not in agents:
                agents.append(agent_id)
    agents = sorted(agents)
    if not agents and not rejected:
        notes.append("no domains requested")
    return {"agents": agents, "notes": sorted(notes), "rejected": sorted(rejected)}


def route_single(domain: str) -> List[str]:
    if domain not in DOMAIN_ROUTES:
        raise KeyError(f"Unknown domain {domain!r}")
    return list(DOMAIN_ROUTES[domain])
