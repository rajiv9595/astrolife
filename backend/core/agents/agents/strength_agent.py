"""
STRENGTH_AGENT — explains SUPPLIED strength without inventing formulas.

Reads: facts, strength, dignity, applicability, evidence, conflicts, sources.
Distinguishes CLASSICAL_STRENGTH (supplied classical report entries) from
CUSTOM_COMPOSITE (supplied custom composite entries) from INTERPRETATION.
Never derives strength from ascendant, lordship, or any other fact.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..agent_contract import STRENGTH_AGENT, get_contract
from ..agent_models import SUPPORTED
from ..agent_provenance import conflict_findings, relevant_conflicts
from ..agent_validation import applicability_gate
from . import _shared as shared

CONTRACT = get_contract(STRENGTH_AGENT)
PREFIX = "STR"
TRADITION = "PARASHARI_CLASSICAL"


def _classical_keys(context: Any) -> List[str]:
    return sorted(k for k in context.strength if k.startswith("classical."))


def _custom_keys(context: Any) -> List[str]:
    return sorted(k for k in context.strength if k.startswith("custom."))


def build_draft(context: Any, sub_results: List[Any] | None = None) -> Dict[str, Any]:
    gate = applicability_gate(context, CONTRACT)
    if gate["verdict"] == "INVALID":
        return shared.assemble_draft(
            STRENGTH_AGENT, context, "INVALID", [], [], [],
            "Tradition gate failed; strength execution refused.")
    if gate["verdict"] == "UNKNOWN":
        findings = [shared.unknown_finding(PREFIX, i, name, TRADITION)
                    for i, name in enumerate(gate["missing"])]
        findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
        return shared.assemble_draft(
            STRENGTH_AGENT, context, "UNKNOWN", findings, [], [],
            "Required strength inputs are absent; no strength is estimated.")
    findings: List[Dict[str, Any]] = []
    facts_used: List[str] = []
    for index, key in enumerate(sorted(context.strength)):
        findings.append(shared.fact_finding(PREFIX, index, f"strength.{key}",
                                            context.strength[key], TRADITION))
        facts_used.append(f"strength.{key}")
    for offset, key in enumerate(sorted(context.dignity)):
        findings.append(shared.fact_finding(PREFIX, 500 + offset, f"dignity.{key}",
                                            context.dignity[key], TRADITION))
        facts_used.append(f"dignity.{key}")
    classical = _classical_keys(context)
    custom = _custom_keys(context)
    if classical:
        supports = [f"strength.{k}" for k in classical]
        findings.append(shared.interpretation_finding(
            PREFIX, 0,
            "Supplied classical strength entries report: "
            + "; ".join(f"{k} is {context.strength[k]}" for k in classical)
            + ". These are restated from the canonical report, not derived here.",
            supports, [], TRADITION, confidence="CANONICAL"))
    if custom:
        supports = [f"strength.{k}" for k in custom]
        findings.append(shared.interpretation_finding(
            PREFIX, 1,
            "Supplied custom composite entries report: "
            + "; ".join(f"{k} is {context.strength[k]}" for k in custom)
            + ". Custom composites are kept distinct from classical strength.",
            supports, [], TRADITION))
    if classical and custom:
        findings.append(shared.interpretation_finding(
            PREFIX, 2,
            "Classical and custom strength measures are distinct inputs; "
            "neither is converted into the other.",
            [f"strength.{k}" for k in classical + custom], [], TRADITION))
    findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
    conflicts = relevant_conflicts(context, [])
    status = "SUCCESS"
    if gate["verdict"] == "PARTIAL":
        status = "PARTIAL"
    if conflicts:
        status = "CONFLICTED"
        findings += conflict_findings(PREFIX, conflicts, TRADITION)
    summary = (f"Strength synthesis over {len(classical)} classical and "
               f"{len(custom)} custom supplied entries.")
    return shared.assemble_draft(
        STRENGTH_AGENT, context, status, findings, facts_used, [],
        summary, conflicts=conflicts,
        extra_evidence=sorted(set(context.evidence_ids)))
