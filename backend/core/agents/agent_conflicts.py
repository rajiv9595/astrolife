"""
Phase 7 — conflict helpers re-exported from the provenance layer.

Kept as a separate module per the file-discipline list; all logic lives in
agent_provenance so conflict semantics have exactly one implementation.
"""
from __future__ import annotations

from .agent_provenance import conflict_findings, conflict_ids, relevant_conflicts

__all__ = ["conflict_findings", "conflict_ids", "relevant_conflicts"]
