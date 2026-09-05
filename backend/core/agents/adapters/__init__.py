"""Phase 7 — adapters package."""
from .base import AgentModelAdapter
from .mock import DeterministicMockAdapter

__all__ = ["AgentModelAdapter", "DeterministicMockAdapter"]
