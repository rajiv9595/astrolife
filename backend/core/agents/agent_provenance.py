"""
Phase 7 — provenance construction and conflict propagation.

Provenance reuses Phase 6D evidence ids; no competing evidence architecture.
Conflicts propagate as CONFLICTED with structured conflict information; Phase 6
conflict semantics stay authoritative and no winner is ever selected.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .agent_models import AgentProvenance


def build_provenance(agent_id: str, context: Any, findings: List[Any]) -> AgentProvenance:
    evidence = sorted({eid for f in findings for eid in f.evidence_ids})
    sources = sorted({src for f in findings
                      for src in (f.provenance.get("source_ids", [])
                                  if isinstance(f.provenance.get("source_ids", []), list)
                                  else [])})
    chain = [{
        "finding_id": f.finding_id,
        "type": f.type,
        "supporting_inputs": sorted(f.supporting_inputs),
        "evidence_ids": sorted(f.evidence_ids),
        "rule_ids": sorted(f.rule_ids),
    } for f in sorted(findings, key=lambda x: x.finding_id)]
    return AgentProvenance(agent_id=agent_id, agent_version="7.0.0",
                           input_fingerprint=context.fingerprint(),
                           evidence_ids=evidence, source_ids=sources, chain=chain)


def relevant_conflicts(context: Any, rule_ids: List[str]) -> List[Any]:
    """Supplied conflicts touching the agent's rule ids."""
    wanted = set(rule_ids)
    out = []
    for conflict in context.conflicts:
        if conflict.rule_a in wanted or conflict.rule_b in wanted:
            out.append(conflict)
    return sorted(out, key=lambda c: c.conflict_id)


def conflict_findings(prefix: str, conflicts: List[Any], tradition: str) -> List[Dict[str, Any]]:
    """Structured CONFLICT finding payloads. No resolution, only propagation."""
    payloads = []
    for index, conflict in enumerate(conflicts):
        payloads.append({
            "finding_id": f"{prefix}-CONFLICT-{index:02d}",
            "type": "CONFLICT",
            "statement": (
                f"Supplied inputs record a {conflict.conflict_type} conflict between "
                f"{conflict.rule_a} and {conflict.rule_b}; no determination is made."),
            "data": {"rule_a": conflict.rule_a, "rule_b": conflict.rule_b,
                     "conflict_type": conflict.conflict_type,
                     "status": conflict.status, "detail": conflict.detail},
            "supporting_inputs": sorted([conflict.rule_a, conflict.rule_b]),
            "evidence_ids": [],
            "rule_ids": sorted([conflict.rule_a, conflict.rule_b]),
            "confidence_label": "TRADITION_DEPENDENT",
            "tradition": tradition,
            "provenance": {"origin": "supplied-conflict", "conflict_id": conflict.conflict_id},
        })
    return payloads


def conflict_ids(conflicts: List[Any]) -> List[str]:
    return sorted({c.conflict_id for c in conflicts})
