"""
TIMING_AGENT — explains ALREADY-COMPUTED timing structures (Phase 8 prep).

Reads: dasha, transit, timing, applicability, evidence, conflicts, sources.
Restates supplied candidates (id, kind, window, basis rules). Never derives
dates, never extends windows, never predicts outcomes. Missing timing input
yields UNKNOWN, never invention.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..agent_contract import TIMING_AGENT, get_contract
from ..agent_models import SUPPORTED
from ..agent_provenance import conflict_findings, relevant_conflicts
from ..agent_validation import applicability_gate
from . import _shared as shared

CONTRACT = get_contract(TIMING_AGENT)
PREFIX = "TIME"
TRADITION = "TRADITION_DEPENDENT"


def build_draft(context: Any, sub_results: List[Any] | None = None) -> Dict[str, Any]:
    gate = applicability_gate(context, CONTRACT)
    if gate["verdict"] == "INVALID":
        return shared.assemble_draft(
            TIMING_AGENT, context, "INVALID", [], [], [],
            "Tradition gate failed; timing execution refused.")
    if gate["verdict"] == "UNKNOWN":
        findings = [shared.unknown_finding(PREFIX, i, name, TRADITION)
                    for i, name in enumerate(gate["missing"])]
        findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
        return shared.assemble_draft(
            TIMING_AGENT, context, "UNKNOWN", findings, [], [],
            "No supplied timing candidates exist; no timing is invented.")
    findings: List[Dict[str, Any]] = []
    facts_used: List[str] = []
    for index, candidate in enumerate(sorted(context.timing,
                                            key=lambda c: c.candidate_id)):
        key = f"timing.{candidate.candidate_id}"
        findings.append({
            "finding_id": f"{PREFIX}-FACT-{index:03d}",
            "type": "FACT",
            "statement": (
                f"Supplied input records timing candidate "
                f"{candidate.candidate_id} of kind {candidate.kind} with "
                f"window {candidate.window}."),
            "data": {"fact_key": key, "value": candidate.window,
                     "kind": candidate.kind,
                     "basis_rule_ids": sorted(candidate.basis_rule_ids)},
            "supporting_inputs": [key],
            "evidence_ids": [],
            "rule_ids": sorted(candidate.basis_rule_ids),
            "confidence_label": "CANONICAL",
            "tradition": TRADITION,
            "provenance": {"origin": "supplied-timing",
                           "candidate_id": candidate.candidate_id},
        })
        facts_used.append(key)
    basis = sorted({r for c in context.timing for r in c.basis_rule_ids})
    if context.timing:
        findings.append(shared.interpretation_finding(
            PREFIX, 0,
            f"Supplied timing input lists {len(context.timing)} candidate(s) "
            f"with precomputed windows; windows are restated exactly as "
            f"supplied and no outcome is stated.",
            facts_used, basis, TRADITION))
    if not context.dasha:
        findings.append(shared.unknown_finding(PREFIX, 90, "dasha", TRADITION))
    if not context.transit:
        findings.append(shared.unknown_finding(PREFIX, 91, "transit", TRADITION))
    findings += shared.injection_warnings(PREFIX, context.question, TRADITION)
    conflicts = relevant_conflicts(context, basis)
    status = "SUCCESS"
    if gate["verdict"] == "PARTIAL":
        status = "PARTIAL"
    if conflicts:
        status = "CONFLICTED"
        findings += conflict_findings(PREFIX, conflicts, TRADITION)
    summary = (f"Timing explanation over {len(context.timing)} supplied "
               f"candidate(s); no dates derived, no outcomes stated.")
    return shared.assemble_draft(
        TIMING_AGENT, context, status, findings, facts_used, basis,
        summary, conflicts=conflicts,
        extra_evidence=sorted(set(context.evidence_ids)))
