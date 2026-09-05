"""
Dosha Catalog — Astrolife V2 Phase 5C

Aggregates all dosha rules, collects formation evaluators,
creates the dosha evaluator, provides manifest generation.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any

from ..evaluator import RuleEvaluator, EvaluationConfig
from ..registry import RuleRegistry
from ..enums import RuleCategory
from . import manglik, kemadruma, kala_sarpa, pitru
from .models import DoshaResult, DoshaEvaluationSet, DoshaProvenance


def _collect_formation_evaluators() -> Dict:
    """Collect all dosha formation evaluators from modules."""
    ev: Dict = {}
    ev.update(manglik.MANGLIK_FORMATION_EVALUATORS)
    ev.update(kemadruma.KEMADRUMA_FORMATION_EVALUATORS)
    ev.update(kala_sarpa.KALA_SARPA_FORMATION_EVALUATORS)
    ev.update(pitru.PITRU_FORMATION_EVALUATORS)
    return ev


FORMATION_EVALUATORS: Dict = _collect_formation_evaluators()


def build_dosha_catalog() -> List:
    """Build the complete list of dosha RuleDefinitions."""
    rules = []
    rules.extend(manglik.MANGLIK_RULES)
    rules.extend(kemadruma.KEMADRUMA_RULES)
    rules.extend(kala_sarpa.KALA_SARPA_RULES)
    rules.extend(pitru.PITRU_RULES)
    return rules


DOSHA_RULE_IDS: List[str] = [r.metadata.rule_id for r in build_dosha_catalog()]


def get_dosha_rules() -> List:
    return build_dosha_catalog()


def create_dosha_evaluator() -> RuleEvaluator:
    """
    Create a RuleEvaluator configured for dosha evaluation.
    
    Configuration:
    - formation: YES (custom evaluators)
    - strength: NO (evaluated separately via severity engine)
    - activation: NO (NOT_EVALUATED by design — no prediction yet)
    - cancellation: YES (custom evaluators)
    - mitigation: YES (custom evaluators)
    - evidence: YES
    """
    custom = dict(FORMATION_EVALUATORS)
    # Cancellation evaluators (shared names across modules)
    custom["manglik_cancellation"] = manglik.manglik_cancellation
    custom["manglik_mitigation"] = manglik.manglik_mitigation
    custom["kemadruma_cancellation"] = kemadruma.kemadruma_cancellation
    custom["kemadruma_mitigation"] = kemadruma.kemadruma_mitigation
    custom["kala_sarpa_cancellation"] = kala_sarpa.kala_sarpa_cancellation
    custom["kala_sarpa_mitigation"] = kala_sarpa.kala_sarpa_mitigation
    custom["pitru_cancellation"] = pitru.pitru_cancellation
    custom["pitru_mitigation"] = pitru.pitru_mitigation

    config = EvaluationConfig(
        evaluate_formation=True,
        evaluate_strength=False,  # severity evaluated separately
        evaluate_activation=False,  # NOT_EVALUATED by design
        evaluate_cancellation=True,
        evaluate_mitigation=True,
        collect_evidence=True,
        collect_trace=False,
    )
    return RuleEvaluator(config=config, custom_evaluators=custom)


def _severity_for_dosha(ctx, rule_id: str, formed: bool, evidence: list):
    """Dispatch to the appropriate severity evaluator."""
    if "MANGLIK" in rule_id:
        return manglik.manglik_severity(ctx, formed, evidence)
    elif "KEMADRUMA" in rule_id:
        return kemadruma.kemadruma_severity(ctx, formed, evidence)
    elif "KALA_SARPA" in rule_id:
        return kala_sarpa.kala_sarpa_severity(ctx, formed, evidence)
    elif "PITRU" in rule_id:
        return pitru.pitru_severity(ctx, formed, evidence)
    from .enums import DoshaSeverity
    return DoshaSeverity.UNKNOWN


def evaluate_dosha_by_id(
    rule_id: str, context, evaluator=None
) -> Optional[DoshaResult]:
    """Evaluate a single dosha by rule ID."""
    evaluator = evaluator or create_dosha_evaluator()
    rules = {r.metadata.rule_id: r for r in build_dosha_catalog()}
    rule = rules.get(rule_id)
    if rule is None:
        return None

    result = evaluator.evaluate(rule, context)

    # Evaluate severity separately
    formed = getattr(result.formation_status, "value", str(result.formation_status)) == "FORMED"
    severity = _severity_for_dosha(context, rule_id, formed, result.evidence)

    return DoshaResult(
        dosha_id=result.rule_id,
        dosha_name=result.rule_name,
        dosha_version=result.rule_version,
        category="GENERAL",
        tradition=result.tradition.value if hasattr(result.tradition, "value") else str(result.tradition),
        method=result.method,
        formation_status=result.formation_status.value if hasattr(result.formation_status, "value") else str(result.formation_status),
        severity_status=severity.value if hasattr(severity, "value") else str(severity),
        cancellation_status=result.cancellation_status.value if hasattr(result.cancellation_status, "value") else str(result.cancellation_status),
        mitigation_status=result.mitigation_status.value if hasattr(result.mitigation_status, "value") else str(result.mitigation_status),
        activation_status=result.activation_status.value if hasattr(result.activation_status, "value") else str(result.activation_status),
        confidence=result.confidence.value if hasattr(result.confidence, "value") else str(result.confidence),
        evidence=[
            {
                "evidence_type": e.evidence_type.value if hasattr(e.evidence_type, "value") else str(e.evidence_type),
                "subject": e.subject,
                "value": e.value,
                "expected": e.expected,
                "actual": e.actual,
                "source": e.source,
                "significance": e.significance,
                "details": e.details,
            }
            for e in (result.evidence or [])
        ],
        relevant_planets=result.relevant_planets,
        relevant_houses=result.relevant_houses,
        relevant_vargas=result.relevant_vargas,
        provenance=DoshaProvenance(
            source_type=result.provenance.source_type.value if hasattr(result.provenance.source_type, "value") else str(result.provenance.source_type),
            source_name=result.provenance.source_name,
            source_reference=result.provenance.source_reference,
            tradition=result.provenance.tradition.value if hasattr(result.provenance.tradition, "value") else str(result.provenance.tradition),
            method=result.provenance.method,
            implementation_version=result.provenance.implementation_version,
            notes=result.provenance.notes,
        ),
        notes=result.notes,
    )


def evaluate_all_doshas(context, evaluator=None) -> DoshaEvaluationSet:
    """Evaluate all doshas against a context."""
    evaluator = evaluator or create_dosha_evaluator()
    rules = build_dosha_catalog()
    results = []
    for rule in rules:
        result = evaluate_dosha_by_id(rule.metadata.rule_id, context, evaluator)
        if result is not None:
            results.append(result)

    formed = sum(1 for r in results if r.is_formed())
    cancelled = sum(1 for r in results if r.is_cancelled())
    mitigated = sum(1 for r in results if r.is_mitigated())

    return DoshaEvaluationSet(
        dosha_results=results,
        total_doshas=len(results),
        formed_count=formed,
        cancelled_count=cancelled,
        mitigated_count=mitigated,
    )


def register_dosha_rules(registry: Optional[RuleRegistry] = None) -> int:
    """Register all dosha rules with the rule registry."""
    registry = registry or RuleRegistry()
    n = 0
    for rule in build_dosha_catalog():
        try:
            if registry.register(rule, source="doshas_5c"):
                n += 1
        except ValueError:
            pass
    return n


def build_manifest() -> List[Dict]:
    """Build machine-readable manifest of all dosha rules."""
    items = []
    for r in build_dosha_catalog():
        m = r.metadata
        items.append({
            "dosha_id": m.rule_id,
            "name": m.name,
            "category": m.category.value if hasattr(m.category, "value") else str(m.category),
            "tradition": m.tradition.value if hasattr(m.tradition, "value") else str(m.tradition),
            "method": m.provenance.method,
            "version": m.rule_version,
            "status": m.status.value if hasattr(m.status, "value") else str(m.status),
            "source": m.provenance.source_name,
            "source_reference": m.provenance.source_reference,
            "confidence": m.confidence.value if hasattr(m.confidence, "value") else str(m.confidence),
        })
    return items
