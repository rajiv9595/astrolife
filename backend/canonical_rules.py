"""
Canonical Production Rules Bridge — Migration #8.

Thin production bridge to the EXISTING canonical rule architecture.

NO ASTROLOGY IS COMPUTED HERE. Every value originates from:
- backend.core.rules.registry.RuleRegistry (canonical 5A registry)
- backend.core.rules.parashari.catalog (canonical Yoga catalogue/evaluators)
- backend.core.rules.doshas.catalog (canonical Dosha catalogue/evaluators)
- backend.core.rules.dynamic.engine (canonical dynamic rule evaluation)
- backend.core.rules.dynamic.registry.DynamicRuleRegistry (dynamic registry)
- backend.core.rules.dynamic.catalogue (ACTIVE-only catalogue queries)
- backend.core.rules.context.RuleContext (canonical facts consumer)
- backend.core.rules.dynamic.context (canonical dynamic context)
- backend.core.rules.evidence / provenance (canonical serialization)

Responsibilities (projection/orchestration only):
- expose the canonical catalogues through ONE production registry view
  (reuses RuleRegistry; never a duplicate registry class)
- construct RuleContext / DynamicEvaluationContext from canonical facts
  passed in by the caller (never from response JSON, never frontend fields)
- evaluate ONLY lifecycle-ACTIVE dynamic rules (never DRAFT/TESTED/
  REVIEW_PENDING/EXPERIMENTAL); conflicts are REPORTED ONLY, never merged
- serialize RuleResult / DynamicRuleResult evidence + provenance with
  `_source: canonical` tagging for the response adapter and AI context

Security boundaries preserved:
- no eval / exec / arbitrary imports / dynamic code paths anywhere
- research:// rules NEVER enter production except through the existing
  RuleLabService activation gates (REVIEW_PENDING + APPROVED review +
  tests passed + provenance + security scan); this bridge performs no
  promotion itself and offers no promotion API
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.rules.context import RuleContext
from backend.core.rules.registry import RuleRegistry

_PRODUCTION_REGISTRY: Optional[RuleRegistry] = None

_PRODUCTION_DYNAMIC_REGISTRY = None


def get_production_rule_registry() -> RuleRegistry:
    """Return the singleton production view over the canonical catalogues.

    Populated once via the existing catalogue register functions
    (register_parashari_rules / register_dosha_rules). Reuses the canonical
    RuleRegistry class — no duplicate registry is created.
    """
    global _PRODUCTION_REGISTRY
    if _PRODUCTION_REGISTRY is None:
        registry = RuleRegistry()
        from backend.core.rules.parashari.catalog import register_parashari_rules
        from backend.core.rules.doshas.catalog import register_dosha_rules
        register_parashari_rules(registry)
        register_dosha_rules(registry)
        _PRODUCTION_REGISTRY = registry
    return _PRODUCTION_REGISTRY


def get_production_dynamic_registry():
    """Return the production DynamicRuleRegistry (starts empty).

    ACTIVE rules reach this registry ONLY through RuleLabService.activate_rule
    (existing promotion gates). Nothing in production writes here directly.
    """
    global _PRODUCTION_DYNAMIC_REGISTRY
    if _PRODUCTION_DYNAMIC_REGISTRY is None:
        from backend.core.rules.dynamic.registry import DynamicRuleRegistry
        _PRODUCTION_DYNAMIC_REGISTRY = DynamicRuleRegistry()
    return _PRODUCTION_DYNAMIC_REGISTRY


def build_production_rule_context(
    chart_facts: Any,
    strength_report: Any = None,
    varga_facts: Optional[Dict[str, Any]] = None,
    dynamic_state: Any = None,
    evaluation_datetime: Any = None,
) -> RuleContext:
    """Construct the canonical RuleContext from canonical facts.

    Facts pass straight through — never reconstructed from response JSON,
    never sourced from frontend fields, no legacy output consumed.
    """
    return RuleContext(
        chart_facts=chart_facts,
        strength_report=strength_report,
        varga_facts=varga_facts or {},
        dynamic_state=dynamic_state,
        evaluation_datetime=evaluation_datetime,
    )


def build_production_dynamic_context(
    chart_facts: Any = None,
    varga_facts: Any = None,
    strength_report: Any = None,
    vimshottari_timeline: Any = None,
    vimshottari_datetime: Any = None,
    jaimini_dasha_result: Any = None,
    jaimini_dasha_datetime: Any = None,
    transit_snapshot: Any = None,
    jaimini_facts: Any = None,
    aspect_map: Any = None,
    rule_outcomes: Any = None,
):
    """Construct the canonical DynamicEvaluationContext from canonical facts."""
    from backend.core.rules.dynamic.context import build_context
    return build_context(
        chart_facts=chart_facts,
        varga_facts=varga_facts,
        strength_report=strength_report,
        vimshottari_timeline=vimshottari_timeline,
        vimshottari_datetime=vimshottari_datetime,
        jaimini_dasha_result=jaimini_dasha_result,
        jaimini_dasha_datetime=jaimini_dasha_datetime,
        transit_snapshot=transit_snapshot,
        jaimini_facts=jaimini_facts,
        aspect_map=aspect_map,
        rule_outcomes=rule_outcomes,
    )


def evaluate_production_dynamic_rules(
    dynamic_context: Any,
    registry: Any = None,
    tradition: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate production dynamic rules with conflict REPORT-ONLY semantics.

    Only lifecycle-ACTIVE rules are eligible. Non-ACTIVE rules (DRAFT,
    VALIDATED, TESTED, REVIEW_PENDING, DISABLED, DEPRECATED, ARCHIVED,
    REJECTED) are never evaluated here. Contradictory results are reported
    via `conflicts` without choosing winners or merging outcomes.
    Missing prerequisites surface as the engine's canonical UNKNOWN /
    INVALID semantics — never coerced to FALSE, never invented.
    """
    from backend.core.rules.dynamic.catalogue import list_rules
    from backend.core.rules.dynamic.engine import evaluate_many

    reg = registry if registry is not None else get_production_dynamic_registry()
    active_rules = [r for r in list_rules(reg) if r.lifecycle.status == "ACTIVE"]
    if tradition is not None and tradition != "ALL":
        active_rules = [r for r in active_rules if r.classification.tradition == tradition]
    # Sovereign sort: registry listing is already deterministic; re-sort by
    # (rule_id, version) for a stable production contract.
    active_rules = sorted(active_rules, key=lambda r: (r.identity.rule_id, r.identity.rule_version))

    results, conflicts = evaluate_many(active_rules, dynamic_context, tradition=None)
    serialized = [_serialize_dynamic_result(r) for r in results]
    return {
        "evaluated_count": len(serialized),
        "formed_count": sum(1 for r in results if r.formation == "FORMED"),
        "unknown_count": sum(1 for r in results if r.status == "UNKNOWN"),
        "invalid_count": sum(1 for r in results if r.status == "INVALID"),
        "results": serialized,
        "conflicts": [_jsonable(c) for c in conflicts],
        "conflict_policy": "REPORTED_ONLY",
        "eligibility": "ACTIVE_ONLY",
        "_source": "canonical",
    }


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            return _jsonable(model_dump(mode="json"))
        except TypeError:
            return _jsonable(model_dump())
    return str(value)


def _serialize_dynamic_result(result: Any) -> Dict[str, Any]:
    return {
        "rule_id": result.rule_id,
        "rule_version": result.rule_version,
        "status": result.status,
        "formation": result.formation,
        "cancellation": result.cancellation,
        "mitigation": result.mitigation,
        "final_state": result.final_state,
        "diagnostics": list(result.diagnostics or []),
        "evidence_paths": list(result.evidence_paths or []),
        "dependency_paths": list(result.dependency_paths or []),
        "resolved_facts": _jsonable(dict(result.resolved_facts or {})),
        "unresolved_facts": list(result.unresolved_facts or []),
        "provenance": _jsonable(dict(result.provenance or {})),
        "evaluation_profile": result.evaluation_profile,
        "_source": "canonical",
    }


def serialize_rule_result_evidence(rule_result: Any) -> List[Dict[str, Any]]:
    """Project canonical RuleResult evidence to JSON-native dicts."""
    from backend.core.rules.evidence import format_evidence_for_json
    return format_evidence_for_json(list(getattr(rule_result, "evidence", []) or []))


def get_production_rule_coverage() -> Dict[str, Any]:
    """Describe production rule coverage from the canonical catalogues."""
    from backend.core.rules.parashari.catalog import PARASHARI_RULE_IDS
    from backend.core.rules.doshas.catalog import DOSHA_RULE_IDS
    registry = get_production_rule_registry()
    return {
        "parashari_rule_count": len(PARASHARI_RULE_IDS),
        "dosha_rule_count": len(DOSHA_RULE_IDS),
        "registered_rule_count": registry.count(),
        "parashari_rule_ids": list(PARASHARI_RULE_IDS),
        "dosha_rule_ids": list(DOSHA_RULE_IDS),
        "_source": "canonical",
    }


def build_production_rules_block(
    chart_facts: Any,
    strength_report: Any = None,
    varga_facts: Optional[Dict[str, Any]] = None,
    dynamic_state: Any = None,
    evaluation_datetime: Any = None,
    dynamic_registry: Any = None,
    tradition: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the additive production `rules` response block.

    Contains registry coverage plus the ACTIVE-only dynamic evaluation
    outcome (empty while no dynamic rule has passed the promotion gates).
    Existing yoga/dosha/jaimini/strength blocks are untouched; this block
    is purely additive metadata with `_source: canonical`.
    """
    coverage = get_production_rule_coverage()
    dynamic_context = build_production_dynamic_context(
        chart_facts=chart_facts,
        varga_facts=varga_facts,
        strength_report=strength_report,
    )
    dynamic = evaluate_production_dynamic_rules(
        dynamic_context, registry=dynamic_registry, tradition=tradition
    )
    return {
        "registry": coverage,
        "dynamic": dynamic,
        "rule_context": "canonical_facts",
        "evidence": "canonical_per_rule_result",
        "provenance": "canonical_per_rule_result",
        "_source": "canonical",
        "_engine": "canonical",
    }
