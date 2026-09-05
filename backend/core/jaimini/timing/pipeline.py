"""
Phase 5H — Jaimini Timing Pipeline.

Full deterministic timing evaluation:
  JaiminiEvaluation + JaiminiDashaResult + TransitSnapshot + EvaluationRange
  → JaiminiTimingEvaluation (candidates, conflicts, evidence, dependencies)

No prediction, no AI, no interpretation. Produces structured event candidates.
All datetime handling uses explicit inputs, never datetime.now() (except at
API boundary for generated_at).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ...calculation.config import CalculationProfile, DEFAULT_PROFILE
from ...calculation.models import ChartFacts
from ..candidates import JaiminiEventCandidate
from ..dasha.models import JaiminiDashaResult
from ..integration import JaiminiEvaluation
from ..mappings import (
    get_all_mappings,
    MappingEntry,
)
from ..models import JaiminiFacts
from ...rules.enums import FormationStatus

from .candidates import build_candidates
from .conflicts import report_candidate_conflicts
from .convergence import classify_convergence
from .dasha_activation import activate_dasha_periods
from .deduplication import deduplicate_candidates
from .golden import capture_golden_snapshot
from .models import (
    CandidateContext,
    CandidateEvaluation,
    DashaActivationRecord,
    TemporalWindow,
    TransitConditionRecord,
)
from .profile_isolation import ProfileIsolationGuard
from .transit_activation import activate_transits_for_mapping


def _parse_iso(iso_str: str) -> datetime:
    """Parse UTC ISO string to tz-aware datetime."""
    if not iso_str:
        return datetime(1900, 1, 1, tzinfo=timezone.utc)
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def evaluate_jaimini_timing(
    chart_facts: ChartFacts,
    jaimini_facts: JaiminiFacts,
    jaimini_evaluation: JaiminiEvaluation,
    dasha_result: JaiminiDashaResult,
    evaluation_start: datetime,
    evaluation_end: datetime,
    calc_profile: Optional[CalculationProfile] = None,
    event_categories: Optional[List[str]] = None,
    golden_path: Optional[str] = None,
) -> CandidateEvaluation:
    """Full Jaimini timing evaluation pipeline.

    Steps:
    1. Determine evaluation window
    2. For each FORMED rule with an event mapping:
       a. Find intersecting dasha periods
       b. Check transit conditions at each sample point
       c. Classify convergence
       d. Build candidate
    3. Deduplicate overlapping candidates
    4. Report candidate-level conflicts
    5. Apply profile isolation
    6. Assemble output
    """
    if calc_profile is None:
        calc_profile = DEFAULT_PROFILE

    evaluation_window = TemporalWindow(start=evaluation_start, end=evaluation_end)
    profile_id = dasha_result.profile_method

    all_mappings = get_all_mappings()
    formed_rule_ids = set(jaimini_evaluation.formed_rules)

    candidates: List[JaiminiEventCandidate] = []

    for rule_id in sorted(all_mappings.keys()):
        if rule_id not in formed_rule_ids:
            continue

        mappings = all_mappings[rule_id]
        for mapping in mappings:
            if event_categories is not None:
                if mapping.event_category.value not in event_categories:
                    continue

            dasha_activations = activate_dasha_periods(
                dasha_result, evaluation_window
            )
            if not dasha_activations:
                continue

            transit_conditions = _check_transits_for_mapping(
                mapping, evaluation_window, chart_facts, jaimini_facts, calc_profile
            )

            rule_result = jaimini_evaluation.get_by_id(rule_id) if hasattr(jaimini_evaluation, 'get_by_id') else None
            if rule_result is None:
                for r in jaimini_evaluation.rules:
                    if r.rule_id == rule_id:
                        rule_result = r
                        break

            if rule_result is None or rule_result.formation_status != FormationStatus.FORMED:
                continue

            evidence_paths = _collect_evidence_paths(rule_id, jaimini_evaluation)
            dependency_paths = _collect_dependency_paths(rule_id, jaimini_evaluation)
            conflict_ids = _collect_conflict_ids(rule_id, jaimini_evaluation)

            window = _compute_candidate_window(dasha_activations, transit_conditions)
            if window is None:
                continue

            ctx = CandidateContext(
                rule_id=rule_id,
                event_category=mapping.event_category.value,
                rule_formed=True,
                formation_status=rule_result.formation_status.value,
                dasha_activations=dasha_activations,
                transit_conditions=transit_conditions,
                mapping_tradition=mapping.tradition,
                mapping_method=mapping.method,
                mapping_confidence=mapping.confidence,
                mapping_provenance=mapping.provenance,
                mapping_source_reference=mapping.source_reference,
                evidence_paths=evidence_paths,
                dependency_paths=dependency_paths,
                conflict_ids=conflict_ids,
                profile_id=profile_id,
            )

            convergence = classify_convergence_from_counts(
                len(ctx.dasha_activations), len(ctx.transit_conditions)
            )
            candidate = build_candidates([ctx], [window], convergence)
            candidates.extend(candidate)

    candidates = deduplicate_candidates(candidates)

    # Recompute convergence after deduplication since candidates may have merged
    for c in candidates:
        n_transit = len(c.transit_condition_ids)
        n_dasha = len(c.dasha_period_ids)
        # Recreate candidate with correct convergence (frozen model)
        c_dict = c.model_dump()
        c_dict["convergence"] = classify_convergence_from_counts(n_dasha, n_transit)
        from core.jaimini.candidates import JaiminiEventCandidate
        candidates[candidates.index(c)] = JaiminiEventCandidate(**c_dict)

    candidate_conflicts = report_candidate_conflicts(candidates)

    isolation_guard = ProfileIsolationGuard()
    isolation_guard.register(profile_id, candidates)
    isolation_violations = isolation_guard.check_isolation()

    total = len(candidates)

    eval_result = CandidateEvaluation(
        profile_id=profile_id,
        candidates=candidates,
        conflicts=[
            {
                "candidate_a": cc.candidate_a_id,
                "candidate_b": cc.candidate_b_id,
                "rule_a": cc.rule_a,
                "rule_b": cc.rule_b,
                "conflict_class": cc.conflict_class,
                "detail": cc.detail,
            }
            for cc in candidate_conflicts
        ],
        evidence=_build_evidence_summary(candidates, jaimini_evaluation),
        dependencies=sorted(set(dep for c in candidates for dep in c.dependencies)),
        validation={
            "isolation_violations": isolation_violations,
            "total_candidates": total,
        },
        provenance={
            "tradition": "JAIMINI",
            "profile_id": profile_id,
            "source_reference": "UNVERIFIED",
            "confidence": "TRADITION_DEPENDENT",
        },
        evaluation_range={
            "evaluation_start": evaluation_start.isoformat(),
            "evaluation_end": evaluation_end.isoformat(),
        },
        total_candidates=total,
        generated_at="",  # API boundary only; set by caller if needed
    )

    if golden_path is not None:
        capture_golden_snapshot(eval_result, Path(golden_path))

    return eval_result


def _check_transits_for_mapping(
    mapping: MappingEntry,
    evaluation_window: TemporalWindow,
    chart_facts: ChartFacts,
    jaimini_facts: JaiminiFacts,
    calc_profile: CalculationProfile,
) -> List[TransitConditionRecord]:
    """Check transit conditions for a mapping across the evaluation window.

    Samples at daily intervals and collects all met conditions.
    """
    from datetime import timedelta

    conditions: List[TransitConditionRecord] = []
    seen_ids: set = set()

    current = evaluation_window.start
    while current <= evaluation_window.end:
        try:
            from core.transit.calculator import calculate_transit_positions
            transits = calculate_transit_positions(current, calc_profile)
            met = activate_transits_for_mapping(
                mapping, transits, chart_facts, jaimini_facts
            )
            for cond in met:
                if cond.condition_id not in seen_ids:
                    conditions.append(cond)
                    seen_ids.add(cond.condition_id)
        except Exception:
            pass
        current = current + timedelta(days=1.0)

    return conditions


def _compute_candidate_window(
    dasha_activations: List[DashaActivationRecord],
    transit_conditions: List[TransitConditionRecord],
) -> Optional[TemporalWindow]:
    """Compute the candidate window from dasha activations and transit conditions."""
    if not dasha_activations:
        return None

    windows = [
        TemporalWindow(start=a.start, end=a.end)
        for a in dasha_activations
    ]

    result = windows[0]
    for w in windows[1:]:
        inter = result.intersection(w)
        if inter is not None:
            result = inter
        else:
            result = TemporalWindow(
                start=min(result.start, w.start),
                end=max(result.end, w.end),
            )

    return result


def _collect_evidence_paths(
    rule_id: str,
    jaimini_evaluation: JaiminiEvaluation,
) -> List[str]:
    """Collect evidence paths for a rule from the JaiminiEvaluation."""
    paths: List[str] = []
    paths.append(f"rule:{rule_id}")

    for node in jaimini_evaluation.evidence_graph.nodes:
        if rule_id in node.node_id:
            paths.append(f"evidence:{node.node_id}")

    return sorted(paths)


def _collect_dependency_paths(
    rule_id: str,
    jaimini_evaluation: JaiminiEvaluation,
) -> List[str]:
    """Collect dependency paths for a rule."""
    for dep in jaimini_evaluation.dependencies:
        if dep.get("rule_id") == rule_id:
            return [
                d["fact_path"]
                for d in dep.get("dependencies", [])
            ]
    return []


def _collect_conflict_ids(
    rule_id: str,
    jaimini_evaluation: JaiminiEvaluation,
) -> List[str]:
    """Collect conflict IDs involving this rule."""
    ids: List[str] = []
    for conflict in jaimini_evaluation.conflicts:
        if conflict.rule_a == rule_id or conflict.rule_b == rule_id:
            ids.append(f"{conflict.rule_a}:{conflict.rule_b}:{conflict.conflict_class}")
    return sorted(ids)


def _build_evidence_summary(
    candidates: List[JaiminiEventCandidate],
    jaimini_evaluation: JaiminiEvaluation,
) -> Dict[str, Any]:
    """Build evidence summary for the evaluation output."""
    all_rule_ids = set()
    for c in candidates:
        all_rule_ids.update(c.rule_ids)

    return {
        "total_rules_activated": len(all_rule_ids),
        "rules_activated": sorted(all_rule_ids),
        "evidence_graph_nodes": len(jaimini_evaluation.evidence_graph.nodes),
        "evidence_graph_edges": len(jaimini_evaluation.evidence_graph.edges),
    }


def classify_convergence_from_counts(
    n_dasha: int,
    n_transit: int,
) -> str:
    """Classify convergence from counts (utility for pipeline)."""
    if n_transit == 0:
        return "SINGLE_CONDITION"
    elif n_transit == 1 and n_dasha <= 1:
        return "DOUBLE_CONDITION"
    else:
        return "MULTI_CONDITION"
