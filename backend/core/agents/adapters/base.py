"""Phase 7 — model adapter abstraction (§17). No vendor hard-coded."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class AgentModelAdapter(ABC):
    """Structured in, structured out. Invalid output becomes INVALID downstream."""

    @abstractmethod
    def generate(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def model_metadata(self) -> Dict[str, str]:
        raise NotImplementedError

    def validate_output(self, payload: Dict[str, Any]) -> bool:
        return isinstance(payload, dict) and payload.get("status") in (
            "SUCCESS", "PARTIAL", "UNKNOWN", "INVALID", "CONFLICTED")
