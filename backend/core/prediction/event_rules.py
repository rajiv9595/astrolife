"""
Phase 8 — EventRule abstraction (§14).

EventRules compose formation/activation/timing/exclusion/tradition/profile
requirements by REFERENCING declarative EventDefinitions and stable rule IDs.
The Phase 6 rule DSL is reused by reference (rule ids + versions); nothing is
duplicated. Evaluation delegates to formation/activation/candidate builders.
"""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class EventRule(BaseModel):
    rule_id: str
    event_id: str
    event_version: str = "1.0.0"
    formation_refs: List[str] = Field(default_factory=list)
    activation_refs: List[str] = Field(default_factory=list)
    timing_requirements: List[str] = Field(default_factory=list)
    exclusion_refs: List[str] = Field(default_factory=list)
    tradition_constraints: List[str] = Field(default_factory=list)
    profile_constraints: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    lifecycle: str = "ACTIVE"

    model_config = {"frozen": True, "extra": "forbid"}


def event_rule_for(definition: Any) -> EventRule:
    """Derive the executable EventRule view of a declarative definition."""
    return EventRule(
        rule_id=f"{definition.event_id}@{definition.version}",
        event_id=definition.event_id, event_version=definition.version,
        formation_refs=list(definition.required_rule_families),
        activation_refs=list(definition.required_activation_signals),
        timing_requirements=list(definition.timing_requirements),
        exclusion_refs=list(definition.exclusion_signals),
        tradition_constraints=list(definition.tradition_constraints),
        profile_constraints=[], version=definition.version,
        lifecycle=definition.lifecycle)


def evaluate_event_rule(rule: EventRule, groups: Dict[str, List[Any]],
                        request: Any) -> Dict[str, Any]:
    """Rule-level verdict over prebuilt signal groups (no orchestration here)."""
    from .activation import evaluate_event_activation
    from .formation import evaluate_event_formation
    from .event_definitions import get_event_definition
    definition = get_event_definition(rule.event_id, rule.event_version)
    formation = evaluate_event_formation(definition, groups.get("formation", []))
    activation = evaluate_event_activation(groups, request.start, request.end)
    return {"rule_id": rule.rule_id, "formation": formation["status"],
            "activation": activation["status"],
            "exclusions": sorted(s.source_id for s in groups.get("exclusion", [])
                                 if s.status == "ACTIVE")}
