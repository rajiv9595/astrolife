"""
Phase 7 — structured AgentContext + AgentRequest + read-only KnowledgeAccessor.

Agents receive JSON-serializable summaries plus fingerprints, never live
canonical objects. The orchestrator holds the CanonicalBundle; agents cannot
reach it, so mutation is structurally impossible (proven by §28 tests).

KnowledgeAccessor wraps the Phase 6E read-only catalogue API. Agents query
through it; catalogue logic is never duplicated inside agents.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .agent_models import ConflictSummary, RuleResultSummary, TimingCandidateSummary


class AgentRequest(BaseModel):
    """Structured user request (§34). The raw question is DATA, never authority."""

    request_id: str
    question: str = ""
    requested_domains: List[str] = Field(default_factory=list)
    traditions: List[str] = Field(default_factory=list)
    profile: str = ""
    allowed_sources: List[str] = Field(default_factory=list)
    requested_output_mode: str = "STRUCTURED"

    model_config = {"frozen": True, "extra": "forbid"}


class AgentContext(BaseModel):
    """Canonical/explicitly-supplied information only (§4). All JSON-serializable."""

    chart_fingerprint: str = ""
    calculation_profile: str = ""
    facts: Dict[str, str] = Field(default_factory=dict)
    vargas: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    strength: Dict[str, str] = Field(default_factory=dict)
    dignity: Dict[str, str] = Field(default_factory=dict)
    rules: List[RuleResultSummary] = Field(default_factory=list)
    doshas: List[RuleResultSummary] = Field(default_factory=list)
    jaimini: Dict[str, str] = Field(default_factory=dict)
    jaimini_rules: List[RuleResultSummary] = Field(default_factory=list)
    dasha: Dict[str, str] = Field(default_factory=dict)
    transit: Dict[str, str] = Field(default_factory=dict)
    timing: List[TimingCandidateSummary] = Field(default_factory=list)
    applicability: Dict[str, str] = Field(default_factory=dict)
    evidence_ids: List[str] = Field(default_factory=list)
    conflicts: List[ConflictSummary] = Field(default_factory=list)
    sources: Dict[str, str] = Field(default_factory=dict)
    requested_domain: str = ""
    allowed_traditions: List[str] = Field(default_factory=list)
    profile: str = ""
    question: str = ""
    output_mode: str = "STRUCTURED"

    model_config = {"frozen": True, "extra": "forbid"}

    def fingerprint(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True,
                             separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def known_fact_keys(self) -> List[str]:
        keys = [f"facts.{k}" for k in self.facts]
        keys += [f"vargas.{v}.{p}" for v, planets in self.vargas.items() for p in planets]
        keys += [f"strength.{k}" for k in self.strength]
        keys += [f"dignity.{k}" for k in self.dignity]
        keys += [f"jaimini.{k}" for k in self.jaimini]
        keys += [f"dasha.{k}" for k in self.dasha]
        keys += [f"transit.{k}" for k in self.transit]
        keys += [f"timing.{c.candidate_id}" for c in self.timing]
        return sorted(keys)

    def known_rule_ids(self) -> List[str]:
        return sorted({r.rule_id for r in list(self.rules) + list(self.doshas)
                       + list(self.jaimini_rules)})


class CanonicalBundle(BaseModel):
    """Orchestrator-side holder for live canonical objects.

    Agents never receive this. It exists so mutation tests can fingerprint
    ChartFacts / VargaFacts / StrengthReport / JaiminiFacts / Dasha / Transit /
    rule results / evidence before and after agent execution.
    """

    model_config = {"arbitrary_types_allowed": True, "extra": "forbid"}

    chart_facts: Any = None
    varga_facts: Any = None
    strength_report: Any = None
    jaimini_facts: Any = None
    dasha_state: Any = None
    transit_state: Any = None
    rule_results: Any = None
    evidence: Any = None


class KnowledgeAccessor:
    """Read-only catalogue access for agents (§33). No duplication of 6E logic."""

    def __init__(self, catalogue: Any = None) -> None:
        if catalogue is None:
            from core.rules.dynamic.knowledge import get_rule_catalogue
            catalogue = get_rule_catalogue()
        object.__setattr__(self, "_catalogue", catalogue)

    @property
    def catalogue(self) -> Any:
        return self._catalogue

    def snapshot_fingerprint(self) -> str:
        from core.rules.dynamic.knowledge import get_catalogue_snapshot
        return get_catalogue_snapshot(self._catalogue).fingerprint()

    def get_rule(self, rule_id: str, version: Optional[str] = None) -> Any:
        from core.rules.dynamic.knowledge import get_rule
        return get_rule(self._catalogue, rule_id, version)

    def find_rules(self, **filters: Any) -> Any:
        from core.rules.dynamic.knowledge import find_rules
        return find_rules(self._catalogue, **filters)

    def find_rules_for_context(self, context: Any, mode: str = "ACTIVE_ONLY",
                               **filters: Any) -> Any:
        from core.rules.dynamic.knowledge import find_rules_for_context
        return find_rules_for_context(self._catalogue, context, mode=mode, **filters)

    def get_applicability(self, rule_id: str, version: str, context: Any) -> Any:
        from core.rules.dynamic.knowledge import (
            KnowledgeContext as KCtx6E,
            evaluate_rule_applicability,
            get_rule_version,
        )
        entry = get_rule_version(self._catalogue, rule_id, version)
        if entry is None:
            return None
        kctx = context if isinstance(context, KCtx6E) else None
        if kctx is None:
            raise TypeError("get_applicability requires a Phase 6E KnowledgeContext")
        return evaluate_rule_applicability(entry, kctx, self._catalogue)

    def find_conflicts(self) -> Any:
        from core.rules.dynamic.knowledge import find_conflicts
        return find_conflicts(self._catalogue)

    def get_rule_health(self, rule_id: str, version: str) -> Any:
        from core.rules.dynamic.knowledge import get_rule_health, get_rule_version
        entry = get_rule_version(self._catalogue, rule_id, version)
        if entry is None:
            return None
        return get_rule_health(entry, self._catalogue)

    def get_evidence(self, rule_id: str, version: str) -> List[str]:
        from core.rules.dynamic.knowledge import get_rule_version
        entry = get_rule_version(self._catalogue, rule_id, version)
        return list(entry.evidence_ids) if entry else []

    def get_dependencies(self, rule_id: str, version: str) -> Any:
        return self._catalogue.dependencies_of(rule_id, version)
