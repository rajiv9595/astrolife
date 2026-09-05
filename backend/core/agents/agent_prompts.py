"""
Phase 7 — prompt construction (§19). Prompts are DATA for a future model
adapter; Phase 7 enforcement is structural (code), never keyword filtering of
prose. The deterministic mock adapter consumes the structured payload only.
"""
from __future__ import annotations

from typing import Any, Dict

from .agent_contract import AgentContract
from .agent_security import PROMPT_FIREWALL_INSTRUCTIONS


def build_prompt(contract: AgentContract, context: Any,
                 sub_results: list | None = None) -> Dict[str, Any]:
    """Structured instruction + data envelope. Never executed, only validated."""
    return {
        "system_contract": PROMPT_FIREWALL_INSTRUCTIONS,
        "agent_id": contract.agent_id,
        "agent_version": contract.agent_version,
        "domain": contract.domain,
        "allowed_operations": sorted(contract.allowed_operations),
        "forbidden_operations": sorted(contract.forbidden_operations),
        "context": context.model_dump(mode="json"),
        "sub_results": [r.model_dump(mode="json") for r in (sub_results or [])],
    }
