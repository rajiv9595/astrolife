"""
Phase 8 — prediction pipeline (§§25, 35–36, 59, 61).

evaluate_prediction(request, entry): validate request range -> resolve
profile/definitions -> eligibility filter (ACTIVE lifecycle, traditions,
catalogue ACTIVE versions) -> generate candidates -> dedup -> assemble
PredictionResult with provenance + fingerprints. No prose generation; no
wall clock; no randomness. Phase 7 agents may consume results downstream
via prediction_to_agent_summaries without mutating them.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .candidates import deduplicate_candidates, generate_event_candidates
from .catalogue import catalogue_snapshot_fingerprint
from .event_definitions import get_event_definition, list_event_definitions
from .models import (
    EVIDENCE_CONFLICTED,
    EVIDENCE_INSUFFICIENT,
    EVIDENCE_PARTIAL,
    INVALID,
    PARTIAL,
    RESULT_CONFLICTED,
    RESULT_UNKNOWN,
    SUCCESS,
    SUPPORTED_RANGE_END,
    SUPPORTED_RANGE_START,
    PredictionRequest,
    PredictionResult,
)
from .profiles import (
    developer_rule_flags,
    eligible_rule_outcomes,
    get_prediction_profile,
    rejected_rule_outcomes,
)
from .provenance import get_prediction_provenance, get_prediction_snapshot
from .security import scan_request
from .validation import validate_prediction_result
from .windows import parse_iso


def _in_supported_range(request: PredictionRequest) -> bool:
    start, end = parse_iso(request.start), parse_iso(request.end)
    low, high = parse_iso(SUPPORTED_RANGE_START), parse_iso(SUPPORTED_RANGE_END)
    if start is None or end is None or low is None or high is None:
        return False
    return low <= start < end <= high


def _scope_periods(periods: List[Any], dasha_profiles: List[str]) -> List[Any]:
    """Honor requested Chara profiles; never fall back silently (§§10, 33)."""
    if not dasha_profiles:
        return list(periods)
    return [p for p in periods
            if p.get("system") != "CHARA" or p.get("profile") in dasha_profiles]


def _select_definitions(request: PredictionRequest,
                        profile: Any) -> List[Any]:
    wanted_ids = set(request.event_ids)
    wanted_cats = set(request.event_types)
    wanted_versions: Dict[str, str] = {}
    for item in list(wanted_ids):
        if "@" in item:
            ident, version = item.split("@", 1)
            wanted_versions[ident] = version
    wanted_ids = {i.split("@", 1)[0] for i in wanted_ids}
    definitions = []
    for event_id in sorted(set(profile.event_rules)):
        try:
            pinned = wanted_versions.get(event_id)
            version = None
            ident = event_id
            if "@" in event_id:
                ident, version = event_id.split("@", 1)
            definition = get_event_definition(ident, pinned or version)
        except KeyError:
            continue
        if definition.lifecycle != "ACTIVE":
            continue
        if wanted_ids and definition.event_id not in wanted_ids:
            continue
        if wanted_cats and definition.category not in wanted_cats:
            continue
        if request.traditions and not (
                set(definition.tradition_constraints) & set(request.traditions)):
            continue
        definitions.append(definition)
    return definitions


def evaluate_prediction(request: PredictionRequest,
                        entry: Dict[str, Any]) -> PredictionResult:
    """Canonical deterministic evaluation. See module docstring."""
    catalogue_before = catalogue_snapshot_fingerprint()
    warnings = scan_request(request)
    if not _in_supported_range(request):
        return _invalid(request, entry,
                        ["request window outside 1900-01-01..2100-01-01"] + warnings,
                        catalogue_before)
    try:
        profile = get_prediction_profile(request.prediction_profile)
    except KeyError:
        return _invalid(request, entry,
                        [f"unknown prediction profile {request.prediction_profile!r}"]
                        + warnings, catalogue_before)
    definitions = _select_definitions(request, profile)
    if not definitions:
        return _invalid(request, entry,
                        ["no applicable event definitions for request"] + warnings,
                        catalogue_before)
    eligible = eligible_rule_outcomes(entry.get("outcomes", []),
                                      list(profile.traditions))
    rejected = rejected_rule_outcomes(entry.get("outcomes", []),
                                      list(profile.traditions))
    scoped = dict(entry)
    scoped["outcomes"] = {o.get("rule_id", ""): o for o in eligible}
    scoped["periods"] = _scope_periods(entry.get("periods", []),
                                       list(request.dasha_profiles))
    scoped["input_fingerprint"] = entry.get("input_fingerprint", "")
    scoped["supplied_conflicts"] = entry.get("conflicts", [])
    profile_dict = {"convergence_policy": dict(profile.convergence_policy),
                    "conflict_policy": dict(profile.conflict_policy),
                    "uncertainty_policy": dict(profile.uncertainty_policy),
                    "window_policy": dict(profile.window_policy)}
    candidates = generate_event_candidates(scoped, definitions, request, profile_dict)
    candidates = deduplicate_candidates(candidates, profile.profile_id)
    dev_flags = developer_rule_flags(eligible)
    sealed = []
    for candidate in candidates:
        provenance = dict(candidate.provenance) if isinstance(
            candidate.provenance, dict) else {}
        provenance.setdefault("developer_flags", dev_flags)
        refreshed = candidate.model_copy(update={"provenance": provenance})
        sealed.append(refreshed.model_copy(
            update={"output_fingerprint": refreshed.compute_output_fingerprint()}))
    candidates = sealed
    unknowns = sorted({u for c in candidates for u in c.unknowns})
    conflicts = sorted({c for c in candidates for c in c.conflicts})
    states = {c.evidence_state for c in candidates}
    if EVIDENCE_CONFLICTED in states:
        evidence_state = EVIDENCE_CONFLICTED
    elif EVIDENCE_INSUFFICIENT in states or not candidates:
        evidence_state = EVIDENCE_INSUFFICIENT
    elif EVIDENCE_PARTIAL in states:
        evidence_state = EVIDENCE_PARTIAL
    else:
        evidence_state = "EVIDENCE_COMPLETE"
    if any(c.status == "CONFLICTED" for c in candidates):
        status = RESULT_CONFLICTED
    elif not candidates or all(c.status == "UNKNOWN" for c in candidates):
        status = RESULT_UNKNOWN
    elif any(c.status in ("UNKNOWN", "UNSUPPORTED") for c in candidates):
        status = PARTIAL
    else:
        status = SUCCESS
    result = PredictionResult(
        request=request, status=status, candidates=candidates,
        rejected_candidates=rejected, unknowns=unknowns, conflicts=conflicts,
        evidence_state=evidence_state, profile=profile.profile_id,
        input_fingerprint=entry.get("input_fingerprint", ""),
        warnings=warnings)
    result = result.model_copy(
        update={"output_fingerprint": result.compute_output_fingerprint()})
    ok, notes = validate_prediction_result(result, entry)
    if not ok:
        return _invalid(request, entry, notes + warnings, catalogue_before)
    if catalogue_snapshot_fingerprint() != catalogue_before:
        return _invalid(request, entry, ["catalogue mutated during prediction"]
                        + warnings, catalogue_before)
    return result


def _invalid(request: PredictionRequest, entry: Dict[str, Any],
             notes: List[str], catalogue_before: str) -> PredictionResult:
    void = PredictionResult(
        request=request, status=INVALID, candidates=[],
        rejected_candidates=[], unknowns=sorted(notes), conflicts=[],
        evidence_state=EVIDENCE_INSUFFICIENT, profile=request.prediction_profile,
        input_fingerprint=entry.get("input_fingerprint", ""),
        warnings=sorted(notes))
    return void.model_copy(
        update={"output_fingerprint": void.compute_output_fingerprint()})


def measure_prediction_performance(request: PredictionRequest,
                                   entry: Dict[str, Any]) -> Dict[str, float]:
    """Record-only timings (§61)."""
    timings: Dict[str, float] = {}
    mark = time.perf_counter()
    list_event_definitions()
    timings["event_definition_lookup_s"] = time.perf_counter() - mark
    profile = get_prediction_profile(request.prediction_profile)
    definitions = _select_definitions(request, profile)
    eligible = eligible_rule_outcomes(entry.get("outcomes", []),
                                      list(profile.traditions))
    scoped = dict(entry)
    scoped["outcomes"] = {o.get("rule_id", ""): o for o in eligible}
    scoped["periods"] = _scope_periods(entry.get("periods", []),
                                       list(request.dasha_profiles))
    scoped["input_fingerprint"] = entry.get("input_fingerprint", "")
    scoped["supplied_conflicts"] = entry.get("conflicts", [])
    profile_dict = {"convergence_policy": dict(profile.convergence_policy),
                    "conflict_policy": dict(profile.conflict_policy),
                    "uncertainty_policy": dict(profile.uncertainty_policy),
                    "window_policy": dict(profile.window_policy)}
    from .signals import generate_event_signals
    mark = time.perf_counter()
    groups_list = [generate_event_signals(d, scoped) for d in definitions]
    timings["signal_generation_s"] = time.perf_counter() - mark
    from .formation import evaluate_event_formation
    mark = time.perf_counter()
    for definition, groups in zip(definitions, groups_list):
        evaluate_event_formation(definition, groups["formation"])
    timings["formation_s"] = time.perf_counter() - mark
    from .activation import evaluate_event_activation
    mark = time.perf_counter()
    for groups in groups_list:
        evaluate_event_activation(groups, request.start, request.end)
    timings["activation_s"] = time.perf_counter() - mark
    from .convergence import calculate_convergence
    mark = time.perf_counter()
    for groups in groups_list:
        pool = [s for name in ("dasha", "jaimini_dasha", "transit", "activation")
                for s in groups.get(name, [])]
        calculate_convergence(pool, profile_dict["convergence_policy"])
    timings["convergence_s"] = time.perf_counter() - mark
    mark = time.perf_counter()
    generate_event_candidates(scoped, definitions, request, profile_dict)
    timings["window_and_candidate_s"] = time.perf_counter() - mark
    mark = time.perf_counter()
    candidates = generate_event_candidates(scoped, definitions, request, profile_dict)
    deduplicate_candidates(candidates, profile.profile_id)
    timings["deduplication_s"] = time.perf_counter() - mark
    mark = time.perf_counter()
    evaluate_prediction(request, entry)
    timings["full_prediction_s"] = time.perf_counter() - mark
    return timings


def prediction_to_agent_summaries(result: PredictionResult) -> List[Dict[str, str]]:
    """Downstream helper for Phase 7 agents (§41). Read-only view.

    Returns timing-style summaries without touching the canonical result.
    Agents may explain these; they must not alter candidates, windows,
    profiles, signals, conflicts, evidence, or status.
    """
    summaries = []
    for candidate in result.candidates:
        for window in candidate.windows:
            summaries.append({
                "candidate_id": candidate.hypothesis_id,
                "kind": f"EVENT_{candidate.rank}",
                "window": f"{window.start} to {window.end}",
                "detail": f"timing candidate ({candidate.rank_reason}); "
                          f"potential window, not a guaranteed outcome."})
    return summaries
