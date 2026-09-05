"""
Phase 6B — dynamic evaluation context.

Holds canonical sources only (built by the caller from accepted engines).
No calculation, no wall clock. Evaluation datetimes are explicit data.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DynamicEvaluationContext(BaseModel):
    chart_facts: Any = Field(default=None, description="Canonical ChartFacts")
    varga_facts: Optional[Dict[str, Any]] = Field(default=None)
    strength_report: Any = Field(default=None)
    vimshottari_timeline: Any = Field(default=None)
    vimshottari_datetime: Optional[datetime] = Field(default=None)
    jaimini_dasha_result: Any = Field(default=None)
    jaimini_dasha_datetime: Optional[datetime] = Field(default=None)
    transit_snapshot: Any = Field(default=None)
    jaimini_facts: Any = Field(default=None)
    aspect_map: Optional[Dict[str, list]] = Field(
        default=None, description="Parashari aspect lists from 5A RuleContext")
    rule_outcomes: Optional[Dict[str, str]] = Field(
        default=None, description="Prior DynamicRuleOutcome formation states by rule_id")
    evaluation_profile: str = "6B/1.0.0"

    model_config = {"arbitrary_types_allowed": True, "frozen": True}


def build_context(chart_facts: Any = None, varga_facts: Any = None,
                  strength_report: Any = None, vimshottari_timeline: Any = None,
                  vimshottari_datetime: Any = None, jaimini_dasha_result: Any = None,
                  jaimini_dasha_datetime: Any = None, transit_snapshot: Any = None,
                  jaimini_facts: Any = None, aspect_map: Any = None,
                  rule_outcomes: Any = None) -> DynamicEvaluationContext:
    return DynamicEvaluationContext(
        chart_facts=chart_facts, varga_facts=varga_facts,
        strength_report=strength_report, vimshottari_timeline=vimshottari_timeline,
        vimshottari_datetime=vimshottari_datetime,
        jaimini_dasha_result=jaimini_dasha_result,
        jaimini_dasha_datetime=jaimini_dasha_datetime,
        transit_snapshot=transit_snapshot, jaimini_facts=jaimini_facts,
        aspect_map=aspect_map or {}, rule_outcomes=rule_outcomes or {},
    )
