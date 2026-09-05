"""
Phase 7 — DeterministicMockAdapter (§18). No network, no external API.

Modes:
  valid            — return the agent's deterministic draft unchanged.
  invalid          — drop required fields, add an unknown field.
  predictive       — append prediction phrasing to the summary.
  fabricated_source— append a finding citing an unknown source record.
  override_fact    — mutate a FACT finding's value away from canonical input.
All non-valid modes must fail strict validation downstream (INVALID).
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from .base import AgentModelAdapter


class DeterministicMockAdapter(AgentModelAdapter):
    def __init__(self, mode: str = "valid",
                 builders: Dict[str, Callable[..., Dict[str, Any]]] | None = None) -> None:
        object.__setattr__(self, "_mode", mode)
        object.__setattr__(self, "_builders", dict(builders or {}))

    @property
    def mode(self) -> str:
        return self._mode

    def model_metadata(self) -> Dict[str, str]:
        return {"model": "deterministic-mock", "version": "7.0.0",
                "mode": self._mode, "vendor": "none"}

    def generate(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        from ..agent_context import AgentContext
        agent_id = prompt.get("agent_id", "")
        builder = self._builders.get(agent_id)
        if builder is None:
            return {"agent_id": agent_id, "status": "UNKNOWN", "findings": [],
                    "unknowns": ["no builder registered for agent"]}
        context = AgentContext.model_validate(prompt.get("context", {}))
        sub_results = prompt.get("sub_results", [])
        if agent_id == "CHART_SYNTHESIS_AGENT":
            from ..agent_result import AgentResult as _AR
            subs = [_AR.model_validate(s) if isinstance(s, dict) else s
                    for s in sub_results]
            draft = builder(context, subs)
        else:
            draft = builder(context)
        if self._mode == "valid":
            return draft
        if self._mode == "invalid":
            corrupted = dict(draft)
            corrupted.pop("findings", None)
            corrupted.pop("provenance", None)
            corrupted["hacked_field"] = "not in schema"
            return corrupted
        if self._mode == "predictive":
            corrupted = dict(draft)
            corrupted["summary"] = (draft.get("summary", "")
                                    + " This will happen: a marriage prediction.")
            return corrupted
        if self._mode == "fabricated_source":
            corrupted = dict(draft)
            findings = list(corrupted.get("findings", []))
            findings.append({
                "finding_id": "MOCK-FAB-00", "type": "INTERPRETATION",
                "statement": "An invented authority supports this.",
                "data": {}, "supporting_inputs": [],
                "evidence_ids": [], "rule_ids": [],
                "confidence_label": "SUPPORTED", "tradition": "",
                "provenance": {"origin": "model-memory",
                               "source_ids": ["INVENTED-BOOK-999"]},
            })
            corrupted["findings"] = findings
            return corrupted
        if self._mode == "override_fact":
            corrupted = dict(draft)
            findings = [dict(f) for f in corrupted.get("findings", [])]
            for finding in findings:
                if finding.get("type") == "FACT":
                    data = dict(finding.get("data", {}))
                    data["value"] = "OVERRIDDEN-NONCANONICAL"
                    finding["data"] = data
                    finding["statement"] = "Overridden canonical fact."
                    break
            corrupted["findings"] = findings
            return corrupted
        return draft
