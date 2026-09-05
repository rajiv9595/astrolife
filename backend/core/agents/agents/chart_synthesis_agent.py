"""
CHART_SYNTHESIS_AGENT — combines supplied sub-results without merging domains.

Agreement ("independent systems both identify X") is stated only when the
referenced findings actually exist in the supplied sub-results. Disagreement
is reported as disagreement. Conflicts are never resolved without an explicit
deterministic rule (none exists in Phase 7).
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..agent_contract import CHART_SYNTHESIS_AGENT, get_contract
from ..agent_models import SUPPORTED
from ..agent_provenance import conflict_findings, relevant_conflicts
from ..agent_validation import applicability_gate
from . import _shared as shared

CONTRACT = get_contract(CHART_SYNTHESIS_AGENT)
PREFIX = "SYN"
TRADITION = "TRADITION_DEPENDENT"


def build_draft(context: Any, sub_results: List[Any] | None = None) -> Dict[str, Any]:
    gate = applicability_gate(context, CONTRACT)
    if gate["verdict"] == "INVALID":
        return shared.assemble_draft(
            CHART_SYNTHESIS_AGENT, context, "INVALID", [], [], [],
            "Tradition gate failed; synthesis refused.")
    if gate["verdict"] == "UNKNOWN":
        findings = [shared.unknown_finding(PREFIX, i, name, TRADITION)
                    for i, name in enumerate(gate["missing"])]
        findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
        return shared.assemble_draft(
            CHART_SYNTHESIS_AGENT, context, "UNKNOWN", findings, [], [],
            "No supplied chart facts exist; nothing is synthesized.")
    findings: List[Dict[str, Any]] = []
    facts_used = [f"facts.{k}" for k in sorted(context.facts)]
    for index, key in enumerate(sorted(context.facts)):
        findings.append(shared.fact_finding(PREFIX, index, f"facts.{key}",
                                            context.facts[key], TRADITION))
    sub_results = list(sub_results or [])
    by_domain: Dict[str, List[Any]] = {}
    for result in sorted(sub_results, key=lambda r: r.agent_id):
        by_domain.setdefault(result.agent_id, []).append(result)
    shared_rules: Dict[str, List[str]] = {}
    for result in sub_results:
        for rid in result.rule_results_used:
            shared_rules.setdefault(rid, []).append(result.agent_id)
    agreements = sorted(rid for rid, agents in shared_rules.items() if len(agents) > 1)
    if agreements:
        findings.append(shared.interpretation_finding(
            PREFIX, 0,
            "Supplied sub-results from "
            + ", ".join(f"{rid} via {sorted(shared_rules[rid])}" for rid in agreements)
            + " reference the same supplied rule outcomes; each domain "
            "statement is preserved separately.",
            sorted(agreements), sorted(agreements), TRADITION))
    parashari_sub = [r for r in sub_results if r.agent_id == "PARASHARI_AGENT"]
    jaimini = [r for r in sub_results if r.agent_id == "JAIMINI_AGENT"]
    support_union = sorted({k for r in sub_results for k in
                            list(r.facts_used) + list(r.rule_results_used)})
    if parashari_sub and jaimini:
        findings.append(shared.interpretation_finding(
            PREFIX, 1,
            "Supplied Parashari and Jaimini outputs are independent domain "
            "statements; agreement is claimed only for explicitly shared "
            "supplied references above.",
            support_union, [], TRADITION))
    for result in sorted(sub_results, key=lambda r: r.agent_id):
        if result.status == "CONFLICTED":
            findings.append(shared.interpretation_finding(
                PREFIX, 90,
                f"Supplied {result.agent_id} output reports conflicts "
                f"{sorted(result.conflicts)}; the disagreement is preserved, "
                f"not resolved.",
                sorted(result.rule_results_used),
                sorted(result.rule_results_used), TRADITION))
    if not sub_results:
        rules = sorted({r.rule_id for r in
                        list(context.rules) + list(context.doshas)
                        + list(context.jaimini_rules)})
        findings.append(shared.interpretation_finding(
            PREFIX, 2,
            f"Standalone synthesis over {len(facts_used)} supplied facts and "
            f"{len(rules)} supplied rule outcomes; no sub-agent outputs were "
            f"supplied.",
            facts_used, rules, TRADITION))
    findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
    all_rule_ids = sorted({r.rule_id for r in list(context.rules)
                           + list(context.doshas) + list(context.jaimini_rules)})
    conflicts = relevant_conflicts(context, all_rule_ids)
    status = "SUCCESS"
    if gate["verdict"] == "PARTIAL":
        status = "PARTIAL"
    if conflicts:
        status = "CONFLICTED"
        findings += conflict_findings(PREFIX, conflicts, TRADITION)
    summary = (f"Chart synthesis over {len(facts_used)} supplied facts, "
               f"{len(all_rule_ids)} supplied rule outcomes, and "
               f"{len(sub_results)} supplied sub-result(s).")
    return shared.assemble_draft(
        CHART_SYNTHESIS_AGENT, context, status, findings, facts_used,
        all_rule_ids, summary, conflicts=conflicts,
        extra_evidence=sorted(set(context.evidence_ids)))
