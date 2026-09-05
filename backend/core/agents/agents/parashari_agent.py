"""
PARASHARI_AGENT — structured Parashari interpretation over SUPPLIED inputs.

Reads: facts, vargas, strength, dignity, rules, doshas, dasha, transit,
applicability, evidence, conflicts, sources. Restates and counts; distinguishes
FACT / RULE_RESULT / INTERPRETATION / UNKNOWN / CONFLICT. Never calculates,
never predicts, never converts tradition-dependent results into facts.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..agent_contract import PARASHARI_AGENT, get_contract
from ..agent_models import SUPPORTED, TRADITION_DEPENDENT
from ..agent_provenance import conflict_findings, conflict_ids, relevant_conflicts
from ..agent_validation import applicability_gate
from . import _shared as shared

CONTRACT = get_contract(PARASHARI_AGENT)
PREFIX = "PARA"
TRADITION = "PARASHARI_CLASSICAL"
IN_SCOPE = ("PARASHARI_CLASSICAL", "TRADITION_DEPENDENT", "MODERN_COMMON")


def _in_scope(summary: Any) -> bool:
    return (summary.tradition or "") in IN_SCOPE


def build_draft(context: Any, sub_results: List[Any] | None = None) -> Dict[str, Any]:
    gate = applicability_gate(context, CONTRACT)
    if gate["verdict"] == "INVALID":
        return shared.assemble_draft(
            PARASHARI_AGENT, context, "INVALID", [], [], [],
            "Tradition gate failed; Parashari execution refused.")
    if gate["verdict"] == "UNKNOWN":
        findings = [shared.unknown_finding(PREFIX, i, name, TRADITION)
                    for i, name in enumerate(gate["missing"])]
        findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
        return shared.assemble_draft(
            PARASHARI_AGENT, context, "UNKNOWN", findings, [], [],
            "Required Parashari inputs are absent; nothing is inferred.")
    findings: List[Dict[str, Any]] = []
    facts_used: List[str] = []
    index = 0
    for key in sorted(context.facts):
        findings.append(shared.fact_finding(PREFIX, index, f"facts.{key}",
                                            context.facts[key], TRADITION))
        facts_used.append(f"facts.{key}")
        index += 1
    scoped = [r for r in list(context.rules) + list(context.doshas) if _in_scope(r)]
    out_of_scope = [r for r in list(context.rules) + list(context.doshas) if not _in_scope(r)]
    rule_ids = sorted(r.rule_id for r in scoped)
    for position, summary in enumerate(sorted(scoped, key=lambda r: r.rule_id)):
        findings.append(shared.rule_finding(PREFIX, position, summary, TRADITION))
    formed = sorted(r.rule_id for r in scoped if r.formation == "FORMED")
    not_formed = sorted(r.rule_id for r in scoped if r.formation == "NOT_FORMED")
    unknown_rules = sorted(r.rule_id for r in scoped
                           if r.formation not in ("FORMED", "NOT_FORMED"))
    dependent = sorted(r.rule_id for r in scoped if r.tradition == "TRADITION_DEPENDENT")
    if scoped:
        supports = facts_used + rule_ids
        findings.append(shared.interpretation_finding(
            PREFIX, 0,
            f"Supplied Parashari results list {len(formed)} formed, "
            f"{len(not_formed)} not formed, and {len(unknown_rules)} unknown "
            f"out of {len(scoped)} supplied rule outcomes; formation, "
            f"cancellation, and mitigation remain separate as supplied.",
            supports, rule_ids, TRADITION))
        if dependent:
            findings.append(shared.interpretation_finding(
                PREFIX, 1,
                f"Supplied outcomes {dependent} carry TRADITION_DEPENDENT status "
                f"and are restated as supplied, not as settled facts.",
                dependent, dependent, TRADITION, confidence=TRADITION_DEPENDENT))
    dignity_note = "; ".join(f"{k} is {v}" for k, v in sorted(context.dignity.items()))
    strength_note = "; ".join(f"{k} is {v}" for k, v in sorted(context.strength.items()))
    if dignity_note or strength_note:
        supports = ([f"dignity.{k}" for k in context.dignity]
                    + [f"strength.{k}" for k in context.strength])
        findings.append(shared.interpretation_finding(
            PREFIX, 2,
            "Supplied dignity input reports: " + (dignity_note or "none")
            + ". Supplied strength input reports: " + (strength_note or "none") + ".",
            supports, [], TRADITION))
    if "dasha" in CONTRACT.optional_inputs and not context.dasha:
        findings.append(shared.unknown_finding(PREFIX, 90, "dasha", TRADITION))
    if "transit" in CONTRACT.optional_inputs and not context.transit:
        findings.append(shared.unknown_finding(PREFIX, 91, "transit", TRADITION))
    if out_of_scope:
        findings.append(shared.warning_finding(
            PREFIX, 1,
            f"{len(out_of_scope)} supplied rule outcome(s) from other traditions "
            f"were left out of Parashari scope: "
            f"{sorted(r.rule_id for r in out_of_scope)}.", TRADITION))
    findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
    conflicts = relevant_conflicts(context, rule_ids)
    status = "SUCCESS"
    if gate["verdict"] == "PARTIAL":
        status = "PARTIAL"
    if conflicts:
        status = "CONFLICTED"
        findings += conflict_findings(PREFIX, conflicts, TRADITION)
    summary = (f"Parashari synthesis over {len(facts_used)} supplied facts and "
               f"{len(scoped)} supplied rule outcomes: {len(formed)} formed, "
               f"{len(not_formed)} not formed, {len(unknown_rules)} unknown.")
    evidence = sorted({e for r in list(context.rules) + list(context.doshas)
                       for e in r.evidence_ids})
    return shared.assemble_draft(
        PARASHARI_AGENT, context, status, findings, facts_used, rule_ids,
        summary, conflicts=conflicts, extra_evidence=evidence)
