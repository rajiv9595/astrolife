"""Shared deterministic finding builders for Phase 7 agents.

FACT findings always carry data {"fact_key", "value"} so the strict
validator can structurally prove they restate (never override) canonical
input. RULE_RESULT findings carry the full supplied outcome for the same
reason. No astrology is computed here: only counting, sorting, restating.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..agent_models import (
    CANONICAL,
    SUPPLIED_RESULT,
    SUPPORTED,
    TRADITION_DEPENDENT,
)

STATEMENT_PREFIX = "Supplied input records"


def fact_value(context: Any, key: str) -> Any:
    """Resolve a known fact key against the context. Returns (found, value)."""
    parts = key.split(".")
    section = parts[0]
    if section == "facts":
        table = context.facts
        name = ".".join(parts[1:])
        return (name in table, table.get(name))
    if section == "vargas" and len(parts) == 3:
        table = context.vargas.get(parts[1], {})
        return (parts[2] in table, table.get(parts[2]))
    for section_name in ("strength", "dignity", "jaimini", "dasha", "transit"):
        if section == section_name:
            table = getattr(context, section_name)
            name = ".".join(parts[1:])
            return (name in table, table.get(name))
    if section == "timing" and len(parts) == 2:
        for candidate in context.timing:
            if candidate.candidate_id == parts[1]:
                return True, candidate.window
    return False, None


def fact_finding(prefix: str, index: int, key: str, value: str,
                 tradition: str) -> Dict[str, Any]:
    return {
        "finding_id": f"{prefix}-FACT-{index:03d}",
        "type": "FACT",
        "statement": f"{STATEMENT_PREFIX} {key} as {value}.",
        "data": {"fact_key": key, "value": value},
        "supporting_inputs": [key],
        "evidence_ids": [],
        "rule_ids": [],
        "confidence_label": CANONICAL,
        "tradition": tradition,
        "provenance": {"origin": "supplied-fact", "fact_key": key},
    }


def rule_finding(prefix: str, index: int, summary: Any,
                 tradition: str) -> Dict[str, Any]:
    return {
        "finding_id": f"{prefix}-RULE-{index:03d}",
        "type": "RULE_RESULT",
        "statement": (
            f"{STATEMENT_PREFIX} rule {summary.rule_id} as formation "
            f"{summary.formation}, cancellation {summary.cancellation}, "
            f"mitigation {summary.mitigation}."),
        "data": {"rule_id": summary.rule_id, "formation": summary.formation,
                 "cancellation": summary.cancellation,
                 "mitigation": summary.mitigation,
                 "activation": summary.activation},
        "supporting_inputs": [summary.rule_id],
        "evidence_ids": list(summary.evidence_ids),
        "rule_ids": [summary.rule_id],
        "confidence_label": SUPPLIED_RESULT,
        "tradition": summary.tradition or tradition,
        "provenance": {"origin": "supplied-rule-result", "rule_id": summary.rule_id},
    }


def unknown_finding(prefix: str, index: int, name: str,
                    tradition: str) -> Dict[str, Any]:
    return {
        "finding_id": f"{prefix}-UNKNOWN-{index:02d}",
        "type": "UNKNOWN",
        "statement": f"No supplied input covers {name}; no determination is made.",
        "data": {"missing": name},
        "supporting_inputs": [],
        "evidence_ids": [],
        "rule_ids": [],
        "confidence_label": "UNSUPPORTED_INTERPRETATION",
        "tradition": tradition,
        "provenance": {"origin": "missing-input", "missing": name},
    }


def warning_finding(prefix: str, index: int, text: str,
                    tradition: str) -> Dict[str, Any]:
    return {
        "finding_id": f"{prefix}-WARNING-{index:02d}",
        "type": "WARNING",
        "statement": text,
        "data": {},
        "supporting_inputs": [],
        "evidence_ids": [],
        "rule_ids": [],
        "confidence_label": SUPPORTED,
        "tradition": tradition,
        "provenance": {"origin": "security-gate"},
    }


def interpretation_finding(prefix: str, index: int, statement: str,
                           supports: List[str], rule_ids: List[str],
                           tradition: str,
                           confidence: str = SUPPORTED) -> Dict[str, Any]:
    return {
        "finding_id": f"{prefix}-INTERP-{index:02d}",
        "type": "INTERPRETATION",
        "statement": statement,
        "data": {},
        "supporting_inputs": sorted(supports),
        "evidence_ids": [],
        "rule_ids": sorted(rule_ids),
        "confidence_label": confidence,
        "tradition": tradition,
        "provenance": {"origin": "agent-synthesis"},
    }


def injection_warnings(prefix: str, question: str, tradition: str) -> List[Dict[str, Any]]:
    from ..agent_security import find_injections
    hits = find_injections(question or "")
    if not hits:
        return []
    return [warning_finding(
        prefix, 0,
        "Instruction-like language detected in user-supplied data; it was "
        "treated as inert data and ignored under the agent contract.",
        tradition)]


def assemble_draft(agent_id: str, context: Any, status: str,
                   findings: List[Dict[str, Any]], facts_used: List[str],
                   rule_ids: List[str], summary: str,
                   conflicts: List[Any] | None = None,
                   extra_evidence: List[str] | None = None) -> Dict[str, Any]:
    """Build the raw AgentResult payload. Fingerprinted by the orchestrator."""
    from ..agent_models import Finding as _Finding
    from ..agent_provenance import build_provenance, conflict_ids as _cids
    parsed = [_Finding.model_validate(f) for f in findings]
    provenance = build_provenance(agent_id, context, parsed)
    evidence = sorted(set(extra_evidence or []))
    unknowns = [f["data"]["missing"] for f in findings if f["type"] == "UNKNOWN"]
    return {
        "agent_id": agent_id, "agent_version": "7.0.0", "status": status,
        "summary": summary,
        "findings": findings,
        "facts_used": sorted(set(facts_used)),
        "rule_results_used": sorted(set(rule_ids)),
        "interpretations": sorted(f["statement"] for f in findings
                                  if f["type"] == "INTERPRETATION"),
        "unknowns": sorted(unknowns),
        "conflicts": _cids(conflicts or []),
        "evidence": evidence,
        "dependencies": sorted(set(rule_ids)),
        "warnings": sorted(f["statement"] for f in findings if f["type"] == "WARNING"),
        "provenance": provenance.model_dump(mode="json"),
        "input_fingerprint": context.fingerprint(),
        "output_fingerprint": "",
    }
