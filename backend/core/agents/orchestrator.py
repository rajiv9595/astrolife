"""
Phase 7 — orchestration layer (§15).

INPUT -> CONTEXT VALIDATION -> PREDICTION-FIREWALL -> APPLICABILITY CHECK ->
AGENT SELECTION (deterministic router) -> READ-ONLY EXTRACTION -> AGENT
EXECUTION (adapter) -> STRICT OUTPUT VALIDATION -> PROVENANCE VALIDATION ->
CONFLICT VALIDATION -> UNKNOWN VALIDATION -> STRUCTURED RESULT ->
OPTIONAL SYNTHESIS. Never mutates canonical data; the bundle is only
fingerprinted, never handed to agents.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .agent_contract import get_contract
from .agent_models import AgentProvenance, ExecutionRecord
from .agent_prompts import build_prompt
from .agent_result import finalize_result, invalid_result, validate_model_output
from .agent_router import route
from .agent_security import find_predictions, stable_digest
from .agent_validation import (
    validate_conflicts,
    validate_provenance,
    validate_unknowns,
)


class OrchestrationReport:
    def __init__(self, results: List[Any], records: List[ExecutionRecord],
                 notes: List[str], timings: Dict[str, float]) -> None:
        self.results = results
        self.records = records
        self.notes = notes
        self.timings = timings


def _refusal(agent_id: str, context: Any, reason: str) -> Any:
    from .agent_result import AgentResult
    provenance = AgentProvenance(agent_id=agent_id, agent_version="7.0.0",
                                 input_fingerprint=context.fingerprint())
    draft = AgentResult(agent_id=agent_id, status="INVALID",
                        summary=reason,
                        warnings=[reason],
                        provenance=provenance,
                        input_fingerprint=context.fingerprint())
    return draft.model_copy(update={"output_fingerprint": draft.compute_output_fingerprint()})


def run_request(request: Any, context: Any, bundle: Any, accessor: Any,
                adapter: Any, registry: Any) -> OrchestrationReport:
    timings: Dict[str, float] = {}
    mark = time.perf_counter()
    catalogue_before = accessor.snapshot_fingerprint()
    timings["context_construction_s"] = 0.0

    routing = route(request, context)
    timings["routing_s"] = time.perf_counter() - mark

    results: List[Any] = []
    records: List[ExecutionRecord] = []
    notes: List[str] = list(routing["notes"])

    prediction_hits = find_predictions(request.question or "")
    if prediction_hits:
        targets = routing["agents"] or ["ORCHESTRATOR"]
        for agent_id in sorted(targets):
            results.append(_refusal(
                agent_id, context,
                "Prediction requested; Phase 7 produces interpretation only. "
                "PREDICTION_FORBIDDEN."))
            records.append(_record(agent_id, context, results[-1], ["prediction refused"]))
        timings["orchestration_s"] = time.perf_counter() - mark
        _seal(accessor, catalogue_before, notes)
        return OrchestrationReport(results, records, sorted(notes), timings)

    if not routing["agents"]:
        notes += routing["rejected"] or ["no routable agents"]
        timings["orchestration_s"] = time.perf_counter() - mark
        _seal(accessor, catalogue_before, notes)
        return OrchestrationReport(results, records, sorted(notes), timings)

    validated: Dict[str, Any] = {}
    mark = time.perf_counter()
    validation_s = 0.0
    for agent_id in routing["agents"]:
        contract = registry.get_agent(agent_id)
        prompt = build_prompt(contract, context)
        payload = adapter.generate(prompt)
        mark_v = time.perf_counter()
        ok, output_notes, parsed = validate_model_output(payload, context, agent_id)
        if not ok:
            final = invalid_result(agent_id, context, output_notes,
                                   [f"adapter output rejected: {n}" for n in output_notes])
            final_notes = output_notes
        else:
            assert parsed is not None
            final = finalize_result(parsed, context)
            from .agent_validation import applicability_gate
            gate = applicability_gate(context, contract)
            extra = (validate_provenance(final, context)
                     + validate_conflicts(final, context)
                     + validate_unknowns(final, gate))
            final_notes = list(output_notes) + extra
            if extra:
                final = invalid_result(agent_id, context, extra,
                                       [f"post-validation failed: {n}" for n in extra])
            validation_s += time.perf_counter() - mark_v
        validated[agent_id] = final
        results.append(final)
        records.append(_record(agent_id, context, final, final_notes))
    timings["agent_execution_s"] = time.perf_counter() - mark
    timings["provenance_validation_s"] = validation_s

    timings["orchestration_s"] = timings.get("routing_s", 0.0) + timings.get(
        "agent_execution_s", 0.0)
    _seal(accessor, catalogue_before, notes)
    return OrchestrationReport(results, records, sorted(notes), timings)


def run_full_with_synthesis(request: Any, context: Any, sub_results: List[Any],
                            accessor: Any, adapter: Any,
                            registry: Any) -> Any:
    """Run the synthesis agent over already-validated sub-results."""
    contract = registry.get_agent("CHART_SYNTHESIS_AGENT")
    prompt = build_prompt(contract, context, sub_results)
    void = {"agent_id": "CHART_SYNTHESIS_AGENT", "context": prompt["context"],
            "sub_results": prompt["sub_results"]}
    payload = adapter.generate(void)
    ok, output_notes, parsed = validate_model_output(
        payload, context, "CHART_SYNTHESIS_AGENT")
    if not ok:
        return invalid_result("CHART_SYNTHESIS_AGENT", context, output_notes,
                              [f"adapter output rejected: {n}" for n in output_notes])
    assert parsed is not None
    return finalize_result(parsed, context)


def _record(agent_id: str, context: Any, result: Any,
            validation_notes: List[str]) -> ExecutionRecord:
    contract_version = "7.0.0"
    try:
        contract_version = get_contract(agent_id).agent_version
    except KeyError:
        pass
    return ExecutionRecord(
        agent_id=agent_id, agent_version=contract_version,
        context_fingerprint=context.fingerprint(),
        input_fingerprint=result.input_fingerprint,
        output_fingerprint=result.output_fingerprint,
        status=result.status,
        validation_notes=sorted(validation_notes),
        conflict_ids=sorted(result.conflicts),
        unknown_inputs=sorted(result.unknowns))


def _seal(accessor: Any, before: str, notes: List[str]) -> None:
    after = accessor.snapshot_fingerprint()
    if after != before:
        notes.append("CATALOGUE_MUTATED")
    else:
        notes.append("catalogue unchanged")


def bundle_digest(bundle: Any) -> Dict[str, str]:
    return {
        "chart_facts": stable_digest(bundle.chart_facts),
        "varga_facts": stable_digest(bundle.varga_facts),
        "strength_report": stable_digest(bundle.strength_report),
        "jaimini_facts": stable_digest(bundle.jaimini_facts),
        "dasha_state": stable_digest(bundle.dasha_state),
        "transit_state": stable_digest(bundle.transit_state),
        "rule_results": stable_digest(bundle.rule_results),
        "evidence": stable_digest(bundle.evidence),
    }
