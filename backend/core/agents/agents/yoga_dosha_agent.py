"""
YOGA_DOSHA_AGENT — explains supplied yoga/dosha conditions.

Reads: rules, doshas, jaimini_rules, applicability, evidence, conflicts,
sources, facts. Preserves FORMATION / CANCELLATION / MITIGATION / ACTIVATION
/ QUALITY as separate concepts. Tradition-dependent or disputed outcomes are
never converted into unquestioned facts.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..agent_contract import YOGA_DOSHA_AGENT, get_contract
from ..agent_models import SUPPORTED, TRADITION_DEPENDENT
from ..agent_provenance import conflict_findings, relevant_conflicts
from ..agent_validation import applicability_gate
from . import _shared as shared

CONTRACT = get_contract(YOGA_DOSHA_AGENT)
PREFIX = "YD"
TRADITION = "TRADITION_DEPENDENT"


def build_draft(context: Any, sub_results: List[Any] | None = None) -> Dict[str, Any]:
    gate = applicability_gate(context, CONTRACT)
    if gate["verdict"] == "INVALID":
        return shared.assemble_draft(
            YOGA_DOSHA_AGENT, context, "INVALID", [], [], [],
            "Tradition gate failed; yoga/dosha execution refused.")
    if gate["verdict"] == "UNKNOWN":
        findings = [shared.unknown_finding(PREFIX, i, name, TRADITION)
                    for i, name in enumerate(gate["missing"])]
        findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
        return shared.assemble_draft(
            YOGA_DOSHA_AGENT, context, "UNKNOWN", findings, [], [],
            "Required yoga/dosha inputs are absent; nothing is inferred.")
    findings: List[Dict[str, Any]] = []
    all_rules = list(context.rules) + list(context.doshas) + list(context.jaimini_rules)
    rule_ids = sorted(r.rule_id for r in all_rules)
    for position, summary in enumerate(sorted(all_rules, key=lambda r: r.rule_id)):
        payload = shared.rule_finding(PREFIX, position, summary, TRADITION)
        payload["data"]["quality"] = "TRADITION_DEPENDENT" if summary.tradition in (
            "TRADITION_DEPENDENT", "JAIMINI") else "STATED"
        payload["data"]["stated_as_fact"] = (
            summary.formation == "FORMED"
            and summary.cancellation in ("", "NOT_CANCELLED", "NONE")
            and summary.tradition not in ("TRADITION_DEPENDENT", "JAIMINI"))
        findings.append(payload)
    formed = sorted(r.rule_id for r in all_rules if r.formation == "FORMED")
    disputed = sorted(r.rule_id for r in all_rules
                      if r.tradition in ("TRADITION_DEPENDENT", "JAIMINI")
                      or r.formation == "UNKNOWN")
    if all_rules:
        findings.append(shared.interpretation_finding(
            PREFIX, 0,
            f"Supplied outcomes list {len(formed)} formed out of "
            f"{len(all_rules)} yoga/dosha outcomes; formation, cancellation, "
            f"mitigation, activation, and quality are preserved separately "
            f"exactly as supplied.",
            list(rule_ids), rule_ids, TRADITION))
        if disputed:
            findings.append(shared.interpretation_finding(
                PREFIX, 1,
                f"Supplied outcomes {disputed} are disputed or "
                f"tradition-dependent and are restated as such, never as "
                f"unquestioned facts.",
                disputed, disputed, TRADITION,
                confidence=TRADITION_DEPENDENT))
    findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
    conflicts = relevant_conflicts(context, rule_ids)
    status = "SUCCESS"
    if gate["verdict"] == "PARTIAL":
        status = "PARTIAL"
    if conflicts:
        status = "CONFLICTED"
        findings += conflict_findings(PREFIX, conflicts, TRADITION)
    summary = (f"Yoga/dosha synthesis over {len(all_rules)} supplied outcomes: "
               f"{len(formed)} formed, {len(disputed)} disputed or unknown.")
    evidence = sorted({e for r in all_rules for e in r.evidence_ids})
    return shared.assemble_draft(
        YOGA_DOSHA_AGENT, context, status, findings, [], rule_ids,
        summary, conflicts=conflicts, extra_evidence=evidence)
