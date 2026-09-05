"""
Phase 8 — candidate generation (§25), deduplication (§26), ranking (§27).

generate_event_candidates runs the 10-step pipeline per definition with no
prose: applicability, formation, activation, timing, exclusions, conflicts,
convergence, windows, provenance. Ranks are categorical with explicit
reasons; identical (event, profile, versions, ancestry, window, tradition)
candidates collapse, nothing else does.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from . import windows as window_mod
from .activation import evaluate_event_activation
from .convergence import calculate_convergence, convergence_signal
from .conflicts import collect_unknowns, detect_conflicts, evidence_state
from .formation import evaluate_event_formation
from .models import (
    ALTERNATIVE_CANDIDATE,
    CONFLICTED,
    CONFLICTING_CANDIDATE,
    EVIDENCE_CONFLICTED,
    EVIDENCE_INSUFFICIENT,
    FORMED,
    MULTI_SYSTEM,
    NONE,
    NOT_FORMED,
    PRIMARY_CANDIDATE,
    SECONDARY_CANDIDATE,
    STRONG_MULTI_SYSTEM,
    TWO_SYSTEM,
    UNKNOWN,
    UNKNOWN_CANDIDATE,
    UNSUPPORTED,
    EventHypothesis,
    TimingWindow,
)
from .signals import generate_event_signals


def _hypothesis_id(event_id: str, version: str, profile: str,
                   window: str) -> str:
    digest = hashlib.sha256(
        f"{event_id}|{version}|{profile}|{window}".encode()).hexdigest()[:12]
    return f"HYP-{digest}"


def _signal_windows(signals: List[Any], profile: str) -> List[TimingWindow]:
    windows = []
    for signal in signals:
        if signal.status not in ("ACTIVE", "FORMED"):
            continue
        if signal.exact_time:
            windows.append(TimingWindow(
                start=signal.exact_time, end=signal.exact_time,
                precision="EXACT", source_signals=[signal.signal_id],
                exact_events=[signal.exact_time], uncertainty="",
                profile=profile,
                provenance={"origin": "exact-signal", "signal": signal.signal_id}))
        elif signal.active_from:
            windows.append(TimingWindow(
                start=signal.active_from, end=signal.active_to,
                precision="DASHA_RANGE", source_signals=[signal.signal_id],
                exact_events=[], uncertainty="",
                profile=profile,
                provenance={"origin": "active-signal", "signal": signal.signal_id}))
    return windows


def _narrow(windows: List[TimingWindow], start_iso: str,
            end_iso: str) -> List[TimingWindow]:
    """Intersect independent windows; preserve disjoint ones side by side."""
    clipped = []
    for window in windows:
        cut = window_mod.clip(window, start_iso, end_iso)
        if cut is not None:
            clipped.append(cut)
    if not clipped:
        return []
    ordered = sorted(clipped, key=lambda w: (w.start, w.end))
    merged = [ordered[0]]
    for window in ordered[1:]:
        hit = window_mod.intersect(merged[-1], window)
        if hit is not None:
            merged[-1] = hit
        else:
            merged.append(window)
    return merged


def assemble_hypothesis(definition: Any, groups: Dict[str, List[Any]],
                        request: Any, profile: Dict[str, Any],
                        entry: Dict[str, Any]) -> EventHypothesis:
    formation = evaluate_event_formation(definition, groups["formation"])
    activation = evaluate_event_activation(
        groups, request.start, request.end)
    conflicts = detect_conflicts(groups, entry.get("supplied_conflicts", []),
                                 definition.formation_policy)
    unknowns = collect_unknowns(groups, formation, activation)
    active_pool = [s for name in ("dasha", "jaimini_dasha", "transit", "activation")
                   for s in groups.get(name, [])
                   if s.status in ("ACTIVE", "FORMED")]
    formation_pool = [s for s in groups.get("formation", [])
                      if s.status in ("ACTIVE", "FORMED")]
    independent_pool = [s for s in active_pool + formation_pool
                        if s.active_from or s.exact_time
                        or s.source_type in ("FORMATION_SIGNAL",
                                             "YOGA_ACTIVATION_SIGNAL",
                                             "DOSHA_ACTIVATION_SIGNAL")]
    convergence = calculate_convergence(
        independent_pool, profile.get("convergence_policy", {}))
    conv_signal = convergence_signal(convergence, request.prediction_profile)
    timing_pool = [s for s in active_pool
                   if _in_request(s, request.start, request.end)]
    windows = _narrow(_signal_windows(timing_pool, request.prediction_profile),
                      request.start, request.end)
    if formation["status"] in (NOT_FORMED, UNSUPPORTED):
        # No timing candidates for absent or uncovered formations (§§50, 57).
        windows = []
    timing_status = ("ACTIVE_WINDOW" if windows else
                     ("NO_ACTIVE_WINDOW" if formation["status"] == FORMED
                      else UNKNOWN))
    if activation["status"] == UNKNOWN and formation["status"] != FORMED:
        timing_status = UNKNOWN
    status = formation["status"]
    if conflicts and formation["status"] in (FORMED, UNKNOWN):
        status = CONFLICTED
    if formation["status"] == UNSUPPORTED:
        status = UNSUPPORTED
    exclusions = sorted(s.source_id for s in groups.get("exclusion", [])
                        if s.status == "ACTIVE")
    rank, reason = _rank(status, formation["status"], activation["status"],
                         timing_status, convergence["level"], exclusions,
                         unknowns, request)
    evidence = evidence_state(
        required_present=(bool(active_pool) or formation["status"] == FORMED)
        and formation["status"] != UNSUPPORTED,
        optional_missing=[u for u in unknowns if u.startswith("transit:")
                          or u.startswith("jaimini_dasha:")],
        has_conflicts=bool(conflicts),
        has_unknowns=bool([u for u in unknowns
                           if not (u.startswith("transit:")
                                   or u.startswith("jaimini_dasha:"))]))
    all_signals = [s for group in groups.values() for s in group] + [conv_signal]
    window_key = windows[0].start if windows else "no-window"
    hypothesis_id = _hypothesis_id(definition.event_id, definition.version,
                                   request.prediction_profile, window_key)
    from .provenance import build_hypothesis_provenance
    chain = build_hypothesis_provenance(
        _ChainView(all_signals, [c["conflict_id"] for c in conflicts],
                   unknowns),
        definition, request)
    provenance = {"event_id": definition.event_id,
                  "profile": request.prediction_profile,
                  "traditions": sorted(definition.tradition_constraints),
                  "independent_systems": convergence["independent_systems"],
                  "contributing": convergence["contributing"],
                  "duplicates_excluded": convergence["duplicates"],
                  "dependency_graph": convergence["graph"],
                  "conflict_records": conflicts}
    provenance.update(chain)
    supporting = sorted({s.source_id for s in all_signals
                         if s.status in ("ACTIVE", "FORMED")})
    draft = EventHypothesis(
        hypothesis_id=hypothesis_id, event_type=definition.category,
        event_version=definition.version, status=status,
        formation_status=formation["status"],
        activation_status=activation["status"], timing_status=timing_status,
        coverage=formation.get("coverage", ""),
        signals=sorted(all_signals, key=lambda s: s.signal_id),
        supporting_rules=sorted(formation.get("supporting", [])),
        supporting_facts=sorted({a for s in all_signals for a in s.ancestry}),
        supporting_dashas=sorted({s.source_id for s in all_signals
                                  if s.source_system == "DASHA"}),
        supporting_transits=sorted({s.source_id for s in all_signals
                                    if s.source_system == "TRANSIT"}),
        supporting_jaimini=sorted({s.source_id for s in all_signals
                                   if s.source_system == "JAIMINI"}),
        conflicts=sorted(c["conflict_id"] for c in conflicts),
        evidence=sorted({e for s in all_signals for e in s.evidence}),
        unknowns=unknowns, exclusions=exclusions,
        convergence=convergence["level"], windows=windows,
        rank=rank, rank_reason=reason, evidence_state=evidence,
        provenance=provenance,
        input_fingerprint=entry.get("input_fingerprint", ""))
    return draft.model_copy(update={"output_fingerprint": draft.compute_output_fingerprint()})


class _ChainView:
    """Minimal view for build_hypothesis_provenance (avoids a cycle)."""

    def __init__(self, signals: list, conflict_ids: list, unknowns: list) -> None:
        self.signals = signals
        self.conflicts = conflict_ids
        self.unknowns = unknowns


def _in_request(signal: Any, start_iso: str, end_iso: str) -> bool:
    if signal.exact_time:
        point = window_mod.parse_iso(signal.exact_time)
        start = window_mod.parse_iso(start_iso)
        end = window_mod.parse_iso(end_iso)
        if point is None or start is None:
            return False
        return start <= point < end if end else start <= point
    if not signal.active_from:
        return True
    probe = TimingWindow(start=signal.active_from, end=signal.active_to,
                         precision="DASHA_RANGE")
    bounds = TimingWindow(start=start_iso, end=end_iso, precision="DASHA_RANGE")
    return window_mod.overlap(probe, bounds)


def _rank(status: str, formation: str, activation: str, timing: str,
          convergence: str, exclusions: List[str], unknowns: List[str],
          request: Any) -> tuple:
    if status == CONFLICTED:
        return (CONFLICTING_CANDIDATE,
                "supplied systems disagree; disagreement preserved")
    if status == UNSUPPORTED:
        return (UNKNOWN_CANDIDATE, "INSUFFICIENT_RULE_COVERAGE")
    if formation == FORMED and activation == "ACTIVE" and timing == "ACTIVE_WINDOW":
        if convergence in (MULTI_SYSTEM, STRONG_MULTI_SYSTEM) and not exclusions:
            return (PRIMARY_CANDIDATE, "formed, active, multi-system convergence")
        return (SECONDARY_CANDIDATE,
                "formed and active; " +
                ("exclusion signals present" if exclusions
                 else "single/two-system support"))
    if formation == FORMED and timing == "NO_ACTIVE_WINDOW":
        return (ALTERNATIVE_CANDIDATE,
                "formation present without an active timing window")
    if formation == NOT_FORMED:
        return (UNKNOWN_CANDIDATE, "formation absent in supplied outcomes")
    return (UNKNOWN_CANDIDATE,
            "formation or timing undecidable from supplied inputs")


def generate_event_candidates(entry: Dict[str, Any], definitions: List[Any],
                              request: Any, profile: Dict[str, Any]) -> List[EventHypothesis]:
    hypotheses = []
    for definition in sorted(definitions, key=lambda d: (d.event_id, d.version)):
        groups = generate_event_signals(definition, entry)
        hypotheses.append(assemble_hypothesis(definition, groups, request,
                                              profile, entry))
    ordered = sorted(hypotheses, key=lambda h: (
        {"PRIMARY_CANDIDATE": 0, "SECONDARY_CANDIDATE": 1,
         "ALTERNATIVE_CANDIDATE": 2, "CONFLICTING_CANDIDATE": 3,
         "UNKNOWN_CANDIDATE": 4}[h.rank],
        h.hypothesis_id))
    if not request.include_alternatives:
        ordered = [h for h in ordered if h.rank in (PRIMARY_CANDIDATE,
                                                    SECONDARY_CANDIDATE)]
    if not request.include_conflicts:
        ordered = [h for h in ordered if h.rank != CONFLICTING_CANDIDATE]
    return ordered


def dedup_key(hypothesis: EventHypothesis, profile_id: str) -> tuple:
    versions = tuple(sorted(
        f"{s.source_id}@{s.provenance.get('rule_version', '')}"
        for s in hypothesis.signals if s.source_type == "FORMATION_SIGNAL"))
    ancestry = tuple(sorted({a for s in hypothesis.signals for a in s.ancestry}))
    windows = tuple((w.start, w.end) for w in hypothesis.windows)
    traditions = tuple(sorted(
        hypothesis.provenance.get("traditions", []) if
        isinstance(hypothesis.provenance, dict) else []))
    return (hypothesis.provenance.get("event_id", ""), profile_id, versions,
            ancestry, windows, traditions)


def deduplicate_candidates(hypotheses: List[EventHypothesis],
                           profile_id: str) -> List[EventHypothesis]:
    """Collapse only fully equivalent candidates (§26 equivalence policy)."""
    seen: Dict[tuple, EventHypothesis] = {}
    for hypothesis in hypotheses:
        key = dedup_key(hypothesis, profile_id)
        if key not in seen:
            seen[key] = hypothesis
    order = {h.hypothesis_id: i for i, h in enumerate(hypotheses)}
    return sorted(seen.values(), key=lambda h: order[h.hypothesis_id])
