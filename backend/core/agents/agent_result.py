"""
Phase 7 — structured AgentResult + strict model-output validator (§§7–8, 30).

The validator rejects (as INVALID, never silently repaired): unknown fields,
missing required fields, malformed provenance, unsupported finding types,
invented rule/evidence/fact IDs, prediction content, source claims without
source records, and numeric confidence.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field, ValidationError

from .agent_models import (
    AGENT_STATUSES,
    CONFIDENCE_LABELS,
    FINDING_TYPES,
    AgentProvenance,
    Finding,
)
from .agent_security import PREDICTION_PATTERNS, contains_prediction


class AgentResult(BaseModel):
    agent_id: str
    agent_version: str = "7.0.0"
    status: str = "SUCCESS"
    summary: str = ""
    findings: List[Finding] = Field(default_factory=list)
    facts_used: List[str] = Field(default_factory=list)
    rule_results_used: List[str] = Field(default_factory=list)
    interpretations: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    provenance: AgentProvenance = Field(default_factory=lambda: AgentProvenance(
        agent_id="UNSET", agent_version="7.0.0", input_fingerprint=""))
    input_fingerprint: str = ""
    output_fingerprint: str = ""

    model_config = {"frozen": True, "extra": "forbid"}

    def compute_output_fingerprint(self) -> str:
        payload = json.dumps({
            "agent_id": self.agent_id, "agent_version": self.agent_version,
            "status": self.status, "summary": self.summary,
            "findings": [f.model_dump(mode="json") for f in self.findings],
            "facts_used": sorted(self.facts_used),
            "rule_results_used": sorted(self.rule_results_used),
            "interpretations": sorted(self.interpretations),
            "unknowns": sorted(self.unknowns),
            "conflicts": sorted(self.conflicts),
            "evidence": sorted(self.evidence),
            "dependencies": sorted(self.dependencies),
            "warnings": sorted(self.warnings),
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_model_output(payload: Dict[str, Any], context: Any,
                          agent_id: str) -> Tuple[bool, List[str], Any]:
    """Strict validation of adapter output. Returns (ok, notes, AgentResult|None)."""
    notes: List[str] = []
    if not isinstance(payload, dict):
        return False, ["payload is not a mapping"], None
    try:
        result = AgentResult.model_validate(payload)
    except ValidationError as exc:
        return False, [f"schema: {e['loc']}:{e['msg']}" for e in exc.errors()], None
    if result.agent_id != agent_id:
        notes.append(f"agent_id mismatch: {result.agent_id!r} != {agent_id!r}")
    if result.status not in AGENT_STATUSES:
        notes.append(f"unsupported status {result.status!r}")
    known_rules = set(context.known_rule_ids())
    known_evidence = set(context.evidence_ids)
    known_facts = set(context.known_fact_keys())
    known_sources = set(context.sources)
    rule_table = {r.rule_id: r for r in list(context.rules) + list(context.doshas)
                  + list(context.jaimini_rules)}
    from .agents._shared import fact_value as _fact_value
    for finding in result.findings:
        if finding.type not in FINDING_TYPES:
            notes.append(f"unsupported finding type {finding.type!r}")
        for rid in finding.rule_ids:
            if rid not in known_rules:
                notes.append(f"invented rule id {rid!r}")
        for eid in finding.evidence_ids:
            if eid not in known_evidence:
                notes.append(f"invented evidence id {eid!r}")
        for key in finding.supporting_inputs:
            if key not in known_facts and key not in known_rules:
                notes.append(f"invented input reference {key!r}")
        if finding.confidence_label not in CONFIDENCE_LABELS:
            notes.append(f"unsupported confidence {finding.confidence_label!r}")
        for value in list(finding.data.values()) + [finding.statement, finding.confidence_label]:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                notes.append(f"numeric confidence/score rejected in {finding.finding_id!r}")
                break
        if contains_prediction(finding.statement):
            notes.append(f"prediction content in {finding.finding_id!r}")
        if finding.type == "FACT":
            key = finding.data.get("fact_key")
            if not key or key not in known_facts:
                notes.append(f"FACT without known fact_key in {finding.finding_id!r}")
            else:
                found, canonical = _fact_value(context, key)
                if not found or canonical != finding.data.get("value"):
                    notes.append(f"canonical override in {finding.finding_id!r}")
        if finding.type == "RULE_RESULT":
            rid = finding.data.get("rule_id")
            supplied = rule_table.get(rid or "")
            if supplied is None:
                notes.append(f"RULE_RESULT without supplied outcome in {finding.finding_id!r}")
            elif (finding.data.get("formation") != supplied.formation
                  or finding.data.get("cancellation") != supplied.cancellation
                  or finding.data.get("mitigation") != supplied.mitigation):
                notes.append(f"rule outcome mismatch in {finding.finding_id!r}")
        if finding.type == "INTERPRETATION" and not finding.supporting_inputs:
            if finding.confidence_label != "UNSUPPORTED_INTERPRETATION":
                notes.append(f"unsupported interpretation in {finding.finding_id!r}")
        for src in finding.provenance.get("source_ids", []) if isinstance(
                finding.provenance.get("source_ids", []), list) else []:
            if src not in known_sources:
                notes.append(f"source claim without record {src!r}")
    if contains_prediction(result.summary):
        notes.append("prediction content in summary")
    for text in result.interpretations:
        if contains_prediction(text):
            notes.append("prediction content in interpretations")
    if result.input_fingerprint != context.fingerprint():
        notes.append("input fingerprint mismatch")
    staged = result.model_copy(update={"input_fingerprint": context.fingerprint()})
    if result.output_fingerprint not in ("", None):
        if result.output_fingerprint != staged.compute_output_fingerprint():
            notes.append("output fingerprint mismatch")
    if notes:
        return False, notes, None
    return True, [], result


def invalid_result(agent_id: str, context: Any, notes: List[str],
                   warnings: List[str]) -> AgentResult:
    from .agent_models import AgentProvenance as _AP
    provenance = _AP(agent_id=agent_id, agent_version="7.0.0",
                     input_fingerprint=context.fingerprint())
    draft = AgentResult(agent_id=agent_id, status="INVALID",
                        summary="Adapter output rejected by strict validator.",
                        warnings=sorted(warnings),
                        provenance=provenance,
                        input_fingerprint=context.fingerprint())
    return draft.model_copy(update={"output_fingerprint": draft.compute_output_fingerprint()})


def finalize_result(draft: AgentResult, context: Any) -> AgentResult:
    """Attach fingerprints deterministically."""
    staged = draft.model_copy(update={"input_fingerprint": context.fingerprint()})
    return staged.model_copy(update={"output_fingerprint": staged.compute_output_fingerprint()})


PREDICTION_PATTERNS_EXPORT = PREDICTION_PATTERNS
