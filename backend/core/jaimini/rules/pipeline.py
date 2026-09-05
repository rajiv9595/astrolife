"""
Phase 5E — Jaimini yoga evaluation pipeline.

Pure and deterministic: no timestamps, no randomness, no independent
astronomical computation, no I/O.
Consumes canonical ChartFacts + JaiminiFacts + varga facts only.

Signature: evaluate_jaimini_yogas(chart_facts, jaimini_facts, varga_facts,
profile=None) -> JaiminiYogaEvaluation (results ordered by rule_id).
"""
from __future__ import annotations
from typing import Any, Dict, Optional

from ...rules.enums import (
    FormationStatus,
    StrengthStatus,
    ConfidenceLevel,
    SourceType,
)

from .catalogue import get_catalogue
from .models import JaiminiRuleResult, JaiminiYogaEvaluation
from .profile import JaiminiYogaProfile


def evaluate_jaimini_yogas(
    chart_facts: Any,
    jaimini_facts: Any,
    varga_facts: Dict[str, Any],
    profile: Optional[JaiminiYogaProfile] = None,
) -> JaiminiYogaEvaluation:
    """Evaluate all (or profile-enabled) Jaimini yogas deterministically."""
    if profile is None:
        profile = JaiminiYogaProfile()

    facts_method = jaimini_facts.chara_karakas.method.value
    if profile.karaka_method != facts_method:
        raise ValueError(
            f"Karaka method mismatch: profile={profile.karaka_method} vs "
            f"JaiminiFacts={facts_method}. 7-karaka and 8-karaka results "
            f"must never mix."
        )

    enabled = (
        set(profile.enabled_rule_ids)
        if profile.enabled_rule_ids is not None
        else None
    )

    results: list[JaiminiRuleResult] = []
    for spec in sorted(get_catalogue(), key=lambda s: s.rule_id):
        if enabled is not None and spec.rule_id not in enabled:
            continue
        outcome = spec.evaluator(chart_facts, jaimini_facts, varga_facts, profile.float_tolerance)
        results.append(
            JaiminiRuleResult(
                rule_id=spec.rule_id,
                name=spec.name,
                formed=outcome.formed,
                formation_status=FormationStatus.FORMED if outcome.formed else FormationStatus.NOT_FORMED,
                quality=StrengthStatus.UNKNOWN,
                cancellation_status=outcome.cancellation_status,
                mitigation_status=outcome.mitigation_status,
                origin_label=spec.origin_label,
                method=spec.method,
                confidence=ConfidenceLevel.TRADITION_DEPENDENT,
                source_type=SourceType.UNVERIFIED,
                source_reference="UNVERIFIED",
                formation_evidence=outcome.formation_evidence,
                cancellation_evidence=outcome.cancellation_evidence,
                mitigation_evidence=outcome.mitigation_evidence,
                strength_factors=[],
                relevant_planets=outcome.relevant_planets,
                relevant_signs=outcome.relevant_signs,
                relevant_houses=outcome.relevant_houses,
                dependencies=outcome.dependencies,
                notes=outcome.notes,
                rule_version=spec.rule_version,
            )
        )

    return JaiminiYogaEvaluation(
        results=results,
        profile_method=profile.karaka_method,
        facts_karaka_method=facts_method,
        provenance={
            "tradition": "JAIMINI",
            "method": "jaimini_yoga_evaluation",
            "source_reference": "UNVERIFIED",
            "confidence": ConfidenceLevel.TRADITION_DEPENDENT.value,
            "engine_version": profile.version,
            "notes": "Deterministic rule evaluation. Conditional formation only; zero prediction logic.",
        },
        total_rules=len(results),
        formed_count=sum(1 for r in results if r.formed),
    )
