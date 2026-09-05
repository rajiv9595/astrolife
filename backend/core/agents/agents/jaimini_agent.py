"""
JAIMINI_AGENT — Jaimini interpretation over SUPPLIED Jaimini inputs.

Reads: facts, vargas, jaimini, jaimini_rules, dasha, timing, applicability,
evidence, conflicts, sources. Never applies Parashari assumptions: only
Jaimini-tradition rule outcomes are in scope, and strength/dignity sections
are unreadable under its contract. Cross-system input is used only when it
arrives as explicitly supplied Jaimini-context data.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..agent_contract import JAIMINI_AGENT, get_contract
from ..agent_models import SUPPORTED, TRADITION_DEPENDENT
from ..agent_provenance import relevant_conflicts
from ..agent_provenance import conflict_findings
from ..agent_validation import applicability_gate
from . import _shared as shared

CONTRACT = get_contract(JAIMINI_AGENT)
PREFIX = "JAIM"
TRADITION = "JAIMINI_CLASSICAL"
IN_SCOPE = ("JAIMINI_CLASSICAL", "JAIMINI", "TRADITION_DEPENDENT")


def build_draft(context: Any, sub_results: List[Any] | None = None) -> Dict[str, Any]:
    gate = applicability_gate(context, CONTRACT)
    if gate["verdict"] == "INVALID":
        return shared.assemble_draft(
            JAIMINI_AGENT, context, "INVALID", [], [], [],
            "Tradition gate failed; Jaimini execution refused.")
    if gate["verdict"] == "UNKNOWN":
        findings = [shared.unknown_finding(PREFIX, i, name, TRADITION)
                    for i, name in enumerate(gate["missing"])]
        findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
        return shared.assemble_draft(
            JAIMINI_AGENT, context, "UNKNOWN", findings, [], [],
            "Required Jaimini inputs are absent; nothing is inferred.")
    findings: List[Dict[str, Any]] = []
    facts_used: List[str] = []
    for index, key in enumerate(sorted(context.jaimini)):
        findings.append(shared.fact_finding(PREFIX, index, f"jaimini.{key}",
                                            context.jaimini[key], TRADITION))
        facts_used.append(f"jaimini.{key}")
    scoped = [r for r in context.jaimini_rules if (r.tradition or "") in IN_SCOPE]
    out_of_scope = [r for r in context.jaimini_rules if (r.tradition or "") not in IN_SCOPE]
    rule_ids = sorted(r.rule_id for r in scoped)
    for position, summary in enumerate(sorted(scoped, key=lambda r: r.rule_id)):
        findings.append(shared.rule_finding(PREFIX, position, summary, TRADITION))
    formed = sorted(r.rule_id for r in scoped if r.formation == "FORMED")
    unknown_rules = sorted(r.rule_id for r in scoped
                           if r.formation not in ("FORMED", "NOT_FORMED"))
    if scoped:
        findings.append(shared.interpretation_finding(
            PREFIX, 0,
            f"Supplied Jaimini outcomes list {len(formed)} formed and "
            f"{len(unknown_rules)} unknown out of {len(scoped)} supplied "
            f"Jaimini rule outcomes; karaka, drishti, and pada inputs are "
            f"restated as supplied without Parashari reinterpretation.",
            facts_used + rule_ids, rule_ids, TRADITION))
    if out_of_scope:
        findings.append(shared.warning_finding(
            PREFIX, 1,
            "Non-Jaimini rule outcomes present in context were left out of "
            "Jaimini scope; no cross-tradition reinterpretation was performed.",
            TRADITION))
    if not context.dasha:
        findings.append(shared.unknown_finding(PREFIX, 90, "dasha", TRADITION))
    findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
    conflicts = relevant_conflicts(context, rule_ids)
    status = "SUCCESS"
    if gate["verdict"] == "PARTIAL":
        status = "PARTIAL"
    if conflicts:
        status = "CONFLICTED"
        findings += conflict_findings(PREFIX, conflicts, TRADITION)
    summary = (f"Jaimini synthesis over {len(facts_used)} supplied Jaimini facts "
               f"and {len(scoped)} supplied rule outcomes: {len(formed)} formed, "
               f"{len(unknown_rules)} unknown.")
    evidence = sorted({e for r in context.jaimini_rules for e in r.evidence_ids})
    return shared.assemble_draft(
        JAIMINI_AGENT, context, status, findings, facts_used, rule_ids,
        summary, conflicts=conflicts, extra_evidence=evidence)
