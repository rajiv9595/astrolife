"""
AI-facing future-window projection/compaction layer.

Post-release AI context bugfix (no new astrology, no engine changes).

Problem: the canonical future-window section (backend/future_window.py) is
complete by design — e.g. a 78-day window yields ~268 exact transit events
and ~7 prediction candidates with hundreds of signals/windows each, totalling
~2-3 MB serialized (~500-800k tokens). Sending that verbatim to Gemini makes
the /ai/analyze request exceed practical context/payload limits and fail.

Architecture (required):

    Canonical future-window engine (future_window.py, UNCHANGED)
        |
        v
    complete FUTURE_WINDOW structured evidence (internal, complete)
        |
        v
    deterministic AI-facing projection/compaction (THIS MODULE)
        |
        v
    Gemini -> user-facing answer

The complete FUTURE_WINDOW remains available to backend/internal consumers
(returned by build_future_window_section; kept in-memory as
``_FUTURE_WINDOW_FULL`` on the AI context dict, excluded from the Gemini
payload). ONLY the representation sent to Gemini is bounded.

Guarantees:
- NEVER invents or infers astrological facts. Timestamps pass through
  verbatim from the canonical engine; EVENT_WINDOW is never promoted to
  EXACT; UNKNOWN/PARTIAL stay UNKNOWN/PARTIAL.
- NEVER recalculates planetary positions. Relevance scoring reads only
  categorical metadata (planet names, kinds, timestamps, dasha lords,
  candidate links) already present in the canonical output.
- Deterministic: no LLM, no clock, no randomness, no dict-order dependence.
  All selections use explicit sort keys. Repeated and concurrent runs are
  byte-identical.
- All user/event/evidence strings are treated as untrusted DATA. Projection
  rules, limits, semantics, and compaction flags are module constants —
  embedded instruction text (prompt injection) cannot alter them.

Budget rationale (documented choice):
- Gemini 2.5 Flash advertises ~1,048,576 input tokens (~4M chars), but this
  app's /ai/analyze prompt already carries natal summary + current transits
  + agent findings (~30-60 KB). A verbatim future window (~2-3 MB,
  ~500-800k tokens) blows past reliable single-request payload/latency
  limits and fails in production (observed with 265+ exact events).
- To keep the TOTAL Gemini prompt reliably under ~120 KB (~30k tokens)
  with headroom, the AI future section is capped at:

    MAX_AI_FUTURE_BYTES      = 48_000  (serialized FUTURE_WINDOW projection)
    MAX_EXACT_EVENTS_FOR_LLM = 40      (raw exact events sent to Gemini)
    MAX_SIGNALS_PER_CANDIDATE = 12
    MAX_WINDOWS_PER_CANDIDATE = 8
    MAX_SUPPORTING_PER_LIST   = 24

  Measured budget: natal summary (~8 KB) + current transits (~10 KB) +
  agent findings (~15 KB) + system/grounding prompt (~5 KB) + future
  projection (<=48 KB) ~= ~86 KB total (~21k tokens) — an order of
  magnitude below Gemini 2.5 Flash's ~1M-token input limit and inside
  reliable single-request payload/latency bounds, versus ~1.9 MB
  (~467k tokens) for the verbatim future window that failed in production.
  Typical compacted projections land at ~30-45 KB (~8-11k tokens). If the
  first pass still exceeds the byte cap, deterministic tightening floors
  apply (signals 12->8->5->3, windows 8->5->3->2, supporting 24->12->8->6,
  events 40->30->20->15).
"""

from __future__ import annotations

import copy
import json
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Deterministic limits (see budget rationale above).
# ---------------------------------------------------------------------------

MAX_EXACT_EVENTS_FOR_LLM = 40
MAX_SIGNALS_PER_CANDIDATE = 12
MAX_WINDOWS_PER_CANDIDATE = 8
MAX_SUPPORTING_PER_LIST = 24
MAX_AI_FUTURE_BYTES = 48_000

# Tightening floors used only when the byte cap is still exceeded.
_FLOOR_SIGNALS = (12, 8, 5, 3)
_FLOOR_WINDOWS = (8, 5, 3, 2)
_FLOOR_SUPPORTING = (24, 12, 8, 6)
_FLOOR_EVENTS = (40, 30, 20, 15)

# Fixed semantics text — constants, never derived from user input.
SEMANTICS_EXACT = (
    "EXACT means a canonical exact timestamp supplied by the transit "
    "root-finding engine. Use it verbatim; never invent one."
)
SEMANTICS_EVENT_WINDOW = (
    "EVENT_WINDOW (or a window with start/end and non-EXACT precision) means "
    "a time RANGE, not an exact date. Report it as a window; never collapse "
    "it to a single day."
)
SEMANTICS_UNKNOWN = (
    "UNKNOWN / PARTIAL / EVIDENCE_INSUFFICIENT means the canonical evidence "
    "is insufficient. Say so explicitly; never fill the gap with a date."
)
COMPACTION_NOTE = (
    "Exact-event and signal lists were deterministically compacted for LLM "
    "context size. Omitted events/signals EXIST in the canonical engine "
    "output; omission from this prompt is NOT evidence of absence. "
    "Never claim an omitted transit did not occur, and never invent an "
    "exact job-offer/interview/joining date: the engine cannot distinguish "
    "interview vs offer vs joining."
)
NO_RECALC_RULE = (
    "Do NOT independently recalculate planetary positions, longitudes, "
    "dashas, or transit timings. Interpret ONLY the supplied canonical "
    "evidence."
)

# Query keyword -> prediction categories (deterministic, DATA-only matching).
_CATEGORY_KEYWORDS: Tuple[Tuple[str, Set[str]], ...] = (
    ("job offer letter window by december", {"CAREER", "JOB_CHANGE", "PROMOTION", "BUSINESS"}),
    ("job", {"CAREER", "JOB_CHANGE", "PROMOTION", "BUSINESS"}),
    ("offer", {"CAREER", "JOB_CHANGE", "PROMOTION", "BUSINESS"}),
    ("career", {"CAREER", "JOB_CHANGE", "PROMOTION", "BUSINESS"}),
    ("employment", {"CAREER", "JOB_CHANGE", "PROMOTION", "BUSINESS"}),
    ("promotion", {"PROMOTION", "CAREER"}),
    ("business", {"BUSINESS", "CAREER", "FINANCE"}),
    ("interview", {"CAREER", "JOB_CHANGE"}),
    ("marriage", {"MARRIAGE", "RELATIONSHIP"}),
    ("wedding", {"MARRIAGE", "RELATIONSHIP"}),
    ("spouse", {"MARRIAGE", "RELATIONSHIP"}),
    ("relationship", {"RELATIONSHIP", "MARRIAGE"}),
    ("finance", {"FINANCE", "BUSINESS"}),
    ("money", {"FINANCE", "BUSINESS"}),
    ("wealth", {"FINANCE", "BUSINESS"}),
    ("health", {"HEALTH"}),
    ("education", {"EDUCATION"}),
    ("travel", {"TRAVEL"}),
    ("relocation", {"RELOCATION", "TRAVEL"}),
    ("property", {"PROPERTY"}),
    ("children", {"CHILDREN"}),
    ("spiritual", {"SPIRITUAL"}),
    ("legal", {"LEGAL"}),
)

_KNOWN_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)

_HIGH_VALUE_KINDS = {"exact_conjunction", "exact_opposition"}
_MEDIUM_VALUE_KINDS = {
    "retrograde_station", "direct_station", "station", "sign_ingress",
}

_SIGNAL_TIER = {
    "TRANSIT_SIGNAL_EXACT": 0,
    "TRANSIT_SIGNAL": 1,
    "DASHA_SIGNAL": 2,
    "ANTARDASHA_SIGNAL": 3,
    "PRATYANTAR_SIGNAL": 4,
    "FORMATION_SIGNAL": 5,
    "CONVERGENCE_SIGNAL": 6,
    "YOGA_ACTIVATION_SIGNAL": 7,
    "DOSHA_ACTIVATION_SIGNAL": 8,
    "JAIMINI_DASHA_SIGNAL": 9,
    "EXCLUSION_SIGNAL": 10,
}


# ---------------------------------------------------------------------------
# Helpers (pure, deterministic; inputs treated as DATA).
# ---------------------------------------------------------------------------

def _safe_str(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def _requested_categories(query: str) -> Set[str]:
    text = _safe_str(query).lower()
    out: Set[str] = set()
    for keyword, cats in _CATEGORY_KEYWORDS:
        if keyword in text:
            out |= set(cats)
    return out


def _dasha_lords(dasha_block: Any) -> Set[str]:
    lords: Set[str] = set()
    if not isinstance(dasha_block, dict):
        return lords
    hier = dasha_block.get("hierarchy")
    if isinstance(hier, list):
        for item in hier:
            for token in _safe_str(item).replace("/", " ").split():
                token = token.strip().capitalize()
                if token in _KNOWN_PLANETS:
                    lords.add(token)
    md = _safe_str(dasha_block.get("mahadasha")).strip().capitalize()
    if md in _KNOWN_PLANETS:
        lords.add(md)
    return lords


def _planets_in_text(value: str) -> Set[str]:
    found: Set[str] = set()
    for planet in _KNOWN_PLANETS:
        if planet in value:
            found.add(planet)
    return found


def _candidate_implicated_planets(candidates: List[Dict[str, Any]]) -> Set[str]:
    implicated: Set[str] = set()
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        for key in ("supporting_transits", "supporting_dashas", "supporting_facts"):
            items = cand.get(key)
            if not isinstance(items, list):
                continue
            for item in items:
                s = _safe_str(item)
                implicated |= _planets_in_text(s)
        signals = cand.get("signals")
        if isinstance(signals, list):
            for sig in signals:
                if not isinstance(sig, dict):
                    continue
                implicated |= _planets_in_text(_safe_str(sig.get("source_id")))
                for anc in (sig.get("ancestry") or []):
                    implicated |= _planets_in_text(_safe_str(anc))
    return implicated


def _signal_exact_times(candidates: List[Dict[str, Any]]) -> Set[str]:
    times: Set[str] = set()
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        signals = cand.get("signals")
        if not isinstance(signals, list):
            continue
        for sig in signals:
            if not isinstance(sig, dict):
                continue
            exact = _safe_str(sig.get("exact_time")).strip()
            if exact:
                times.add(exact)
    return times


def _requested_category_support_keys(
    candidates: List[Dict[str, Any]], requested: Set[str]
) -> Set[str]:
    keys: Set[str] = set()
    if not requested:
        return keys
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        if _safe_str(cand.get("event_type")) not in requested:
            continue
        for item in (cand.get("supporting_transits") or []):
            keys.add(_safe_str(item))
    return keys


def _event_support_key(event: Dict[str, Any]) -> str:
    planet = _safe_str(event.get("planet") or event.get("transit_planet"))
    kind = _safe_str(event.get("kind") or event.get("type"))
    if planet and kind:
        return f"transit-event:{planet}:{kind}"
    return ""


def _score_event(
    event: Dict[str, Any],
    *,
    dasha_lords: Set[str],
    implicated: Set[str],
    exact_times: Set[str],
    requested_support_keys: Set[str],
) -> int:
    planet = _safe_str(event.get("planet") or event.get("transit_planet"))
    planet = planet.strip().capitalize() if planet else ""
    natal_target = _safe_str(event.get("natal_target")).strip().capitalize()
    kind = _safe_str(event.get("kind") or event.get("type")).strip()
    stamp = _safe_str(
        event.get("timestamp_iso") or event.get("utc_iso") or event.get("exact_time")
    ).strip()
    score = 0
    if stamp and stamp in exact_times:
        score += 5  # event backs an actual candidate signal
    if planet and planet in dasha_lords:
        score += 3
    if planet and planet in implicated:
        score += 3
    if natal_target and (natal_target in dasha_lords or natal_target in implicated):
        score += 2
    if kind in _HIGH_VALUE_KINDS:
        score += 2
    elif kind in _MEDIUM_VALUE_KINDS:
        score += 1
    if requested_support_keys and _event_support_key(event) in requested_support_keys:
        score += 2
    return score


def _select_events(
    events: List[Dict[str, Any]],
    *,
    dasha_lords: Set[str],
    implicated: Set[str],
    exact_times: Set[str],
    requested_support_keys: Set[str],
    limit: int,
) -> List[Dict[str, Any]]:
    scored: List[Tuple[int, str, str, str, str, str, int]] = []
    for idx, ev in enumerate(events):
        if not isinstance(ev, dict):
            continue
        score = _score_event(
            ev,
            dasha_lords=dasha_lords,
            implicated=implicated,
            exact_times=exact_times,
            requested_support_keys=requested_support_keys,
        )
        stamp = _safe_str(
            ev.get("timestamp_iso") or ev.get("utc_iso") or ev.get("exact_time")
        )
        planet = _safe_str(ev.get("planet") or ev.get("transit_planet"))
        kind = _safe_str(ev.get("kind") or ev.get("type"))
        natal = _safe_str(ev.get("natal_target"))
        fp = _safe_str(ev.get("fingerprint"))
        scored.append((-score, stamp, planet, kind, natal, fp, idx))
    scored.sort()
    chosen_idx = [t[6] for t in scored[: max(0, limit)]]
    # Present chosen events in chronological order (deterministic).
    chosen_idx.sort(
        key=lambda i: (
            _safe_str(
                events[i].get("timestamp_iso")
                or events[i].get("utc_iso")
                or events[i].get("exact_time")
            ),
            _safe_str(events[i].get("planet") or events[i].get("transit_planet")),
            _safe_str(events[i].get("kind") or events[i].get("type")),
            _safe_str(events[i].get("fingerprint")),
        )
    )
    out: List[Dict[str, Any]] = []
    for i in chosen_idx:
        ev = events[i]
        out.append(
            {
                "planet": _safe_str(ev.get("planet") or ev.get("transit_planet")),
                "kind": _safe_str(ev.get("kind") or ev.get("type")),
                "natal_target": _safe_str(ev.get("natal_target")),
                "timestamp_iso": _safe_str(
                    ev.get("timestamp_iso") or ev.get("utc_iso") or ev.get("exact_time")
                ),
                "fingerprint": _safe_str(ev.get("fingerprint")),
            }
        )
    return out


def _signal_sort_key(sig: Dict[str, Any]) -> Tuple[int, str]:
    source_type = _safe_str(sig.get("source_type"))
    exact = _safe_str(sig.get("exact_time")).strip()
    if source_type == "TRANSIT_SIGNAL" and exact:
        tier = _SIGNAL_TIER["TRANSIT_SIGNAL_EXACT"]
    else:
        tier = _SIGNAL_TIER.get(source_type, 99)
    return (tier, _safe_str(sig.get("signal_id")))


def _compact_signal(sig: Dict[str, Any]) -> Dict[str, Any]:
    """Keep signal identity + timing verbatim; drop verbose ancestry bulk."""
    if not isinstance(sig, dict):
        return {}
    ancestry = sig.get("ancestry")
    ancestry_kept = ancestry[:2] if isinstance(ancestry, list) else []
    evidence = sig.get("evidence")
    evidence_kept = evidence[:2] if isinstance(evidence, list) else []
    return {
        "signal_id": _safe_str(sig.get("signal_id")),
        "source_system": _safe_str(sig.get("source_system")),
        "source_type": _safe_str(sig.get("source_type")),
        "source_id": _safe_str(sig.get("source_id")),
        "strength_label": _safe_str(sig.get("strength_label")),
        "active_from": _safe_str(sig.get("active_from")),
        "active_to": _safe_str(sig.get("active_to")),
        "exact_time": _safe_str(sig.get("exact_time")),
        "direction": _safe_str(sig.get("direction")),
        "status": _safe_str(sig.get("status")),
        "ancestry": [_safe_str(a) for a in ancestry_kept],
        "evidence": [_safe_str(e) for e in evidence_kept],
        "provenance": copy.deepcopy(sig.get("provenance"))
        if isinstance(sig.get("provenance"), dict)
        else {},
    }


def _compact_supporting_list(
    items: Any, *, relevant_tokens: Set[str], limit: int
) -> Tuple[List[str], int]:
    if not isinstance(items, list):
        return [], 0
    strings = [_safe_str(x) for x in items]
    total = len(strings)
    if total <= limit:
        return sorted(strings), total

    def _priority(s: str) -> Tuple[int, str]:
        boost = 0
        if s.startswith("transit-event:") or s.startswith("transit."):
            boost += 2
        for token in relevant_tokens:
            if token and token in s:
                boost += 1
                break
        return (-boost, s)

    ranked = sorted(strings, key=_priority)
    return ranked[:limit], total


def _compact_provenance(prov: Any, *, max_items: int = 3) -> Dict[str, Any]:
    """Compact candidate-level provenance bookkeeping deterministically.

    Identity scalars (event_id, profile, traditions, systems, versions,
    request_id, origins) pass through VERBATIM so provenance survives
    compaction. Giant internal bookkeeping lists (contributing signal IDs,
    duplicates_excluded, signals, facts, dependency_graph) are summarized as
    counts plus a deterministic sorted sample — they are engine internals,
    not astrological evidence, and their full form stays in the complete
    internal FUTURE_WINDOW.
    """
    if not isinstance(prov, dict):
        return {}
    out: Dict[str, Any] = {}
    for key in (
        "event_id", "profile", "traditions", "independent_systems",
        "event_version", "request_id", "signal_origins", "rule_versions",
        "conflict_records", "developer_flags",
    ):
        if key in prov:
            value = prov[key]
            out[key] = copy.deepcopy(value) if isinstance(value, (dict, list)) else value
    for key in ("contributing", "duplicates_excluded", "signals", "facts",
                "evidence", "conflicts", "unknowns"):
        value = prov.get(key)
        if isinstance(value, list):
            strings = sorted(_safe_str(x) for x in value)
            out[key + "_total"] = len(strings)
            out[key + "_sample"] = strings[:max_items]
        elif key in prov and key not in out:
            out[key] = copy.deepcopy(value)
    dep_graph = prov.get("dependency_graph")
    if isinstance(dep_graph, dict):
        out["dependency_graph_total"] = len(dep_graph)
        sample: Dict[str, Any] = {}
        for k in sorted(dep_graph.keys())[:max_items]:
            v = dep_graph[k]
            # Keep one ancestry link per sampled entry (verbatim, DATA only).
            sample[k] = v[:1] if isinstance(v, list) else _safe_str(v)
        out["dependency_graph_sample"] = sample
    return out


def _compact_candidate(
    cand: Dict[str, Any],
    *,
    relevant_tokens: Set[str],
    sent_event_stamps: Set[str],
    max_signals: int,
    max_windows: int,
    max_supporting: int,
) -> Dict[str, Any]:
    signals = cand.get("signals") if isinstance(cand.get("signals"), list) else []
    signals = [s for s in signals if isinstance(s, dict)]
    signals_sorted = sorted(signals, key=_signal_sort_key)
    signals_total = len(signals_sorted)
    kept_signals = [_compact_signal(s) for s in signals_sorted[:max_signals]]

    windows = cand.get("windows") if isinstance(cand.get("windows"), list) else []
    windows = [w for w in windows if isinstance(w, dict)]

    def _window_key(w: Dict[str, Any]) -> Tuple[int, str, str, str, str]:
        exact_events = w.get("exact_events") if isinstance(w.get("exact_events"), list) else []
        linked = any(_safe_str(e).strip() in sent_event_stamps for e in exact_events)
        precision = _safe_str(w.get("precision"))
        # Linked + EXACT first (verbatim semantics preserved), then chronological.
        return (
            0 if linked else 1,
            0 if precision == "EXACT" else 1,
            _safe_str(w.get("start")),
            _safe_str(w.get("end")),
            ",".join(sorted(_safe_str(s) for s in (w.get("source_signals") or []))),
        )

    windows_sorted = sorted(windows, key=_window_key)
    windows_total = len(windows_sorted)
    kept_windows: List[Dict[str, Any]] = []
    for w in windows_sorted[:max_windows]:
        source_signals = w.get("source_signals")
        exact_events = w.get("exact_events")
        kept_windows.append(
            {
                # Window timing passes through VERBATIM — never re-timed.
                "start": _safe_str(w.get("start")),
                "end": _safe_str(w.get("end")),
                "precision": _safe_str(w.get("precision")),
                "source_signals": [_safe_str(s) for s in source_signals[:6]]
                if isinstance(source_signals, list)
                else [],
                "exact_events": [_safe_str(e) for e in exact_events[:6]]
                if isinstance(exact_events, list)
                else [],
                "uncertainty": _safe_str(w.get("uncertainty")),
                "profile": _safe_str(w.get("profile")),
                "provenance": copy.deepcopy(w.get("provenance"))
                if isinstance(w.get("provenance"), dict)
                else {},
            }
        )

    supporting_facts, facts_total = _compact_supporting_list(
        cand.get("supporting_facts"), relevant_tokens=relevant_tokens, limit=max_supporting
    )
    supporting_transits, transits_total = _compact_supporting_list(
        cand.get("supporting_transits"),
        relevant_tokens=relevant_tokens,
        limit=max_supporting,
    )
    supporting_dashas, dashas_total = _compact_supporting_list(
        cand.get("supporting_dashas"), relevant_tokens=relevant_tokens, limit=max_supporting
    )
    evidence = cand.get("evidence") if isinstance(cand.get("evidence"), list) else []
    unknowns = cand.get("unknowns") if isinstance(cand.get("unknowns"), list) else []
    conflicts = cand.get("conflicts") if isinstance(cand.get("conflicts"), list) else []
    exclusions = cand.get("exclusions") if isinstance(cand.get("exclusions"), list) else []

    return {
        # Identity + verdict fields preserved verbatim (never re-timed/renamed).
        "hypothesis_id": _safe_str(cand.get("hypothesis_id")),
        "event_type": _safe_str(cand.get("event_type")),
        "event_version": _safe_str(cand.get("event_version")),
        "status": _safe_str(cand.get("status")),
        "formation_status": _safe_str(cand.get("formation_status")),
        "activation_status": _safe_str(cand.get("activation_status")),
        "timing_status": _safe_str(cand.get("timing_status")),
        "coverage": _safe_str(cand.get("coverage")),
        "rank": _safe_str(cand.get("rank")),
        "rank_reason": _safe_str(cand.get("rank_reason")),
        "evidence_state": _safe_str(cand.get("evidence_state")),
        "convergence": _safe_str(cand.get("convergence")),
        "windows": kept_windows,
        "windows_total": windows_total,
        "windows_sent_to_llm": len(kept_windows),
        "signals": kept_signals,
        "signals_total": signals_total,
        "signals_sent_to_llm": len(kept_signals),
        "supporting_rules": [_safe_str(x) for x in (cand.get("supporting_rules") or [])][:max_supporting]
        if isinstance(cand.get("supporting_rules"), list)
        else [],
        "supporting_facts": supporting_facts,
        "supporting_facts_total": facts_total,
        "supporting_transits": supporting_transits,
        "supporting_transits_total": transits_total,
        "supporting_dashas": supporting_dashas,
        "supporting_dashas_total": dashas_total,
        "supporting_jaimini": [_safe_str(x) for x in (cand.get("supporting_jaimini") or [])][:max_supporting]
        if isinstance(cand.get("supporting_jaimini"), list)
        else [],
        "conflicts": [_safe_str(x) for x in conflicts],
        "evidence": [_safe_str(x) for x in evidence][:max_supporting],
        "evidence_total": len(evidence),
        "unknowns": [_safe_str(x) for x in unknowns],
        "exclusions": [_safe_str(x) for x in exclusions],
        "provenance": _compact_provenance(cand.get("provenance")),
        "input_fingerprint": _safe_str(cand.get("input_fingerprint")),
        "output_fingerprint": _safe_str(cand.get("output_fingerprint")),
    }


# ---------------------------------------------------------------------------
# Agent-findings AI projection (same bug class, same layer).
# ---------------------------------------------------------------------------
# AGENT_FINDINGS is deterministic specialist-agent output over canonical
# facts, but its verbatim form (~410 KB: per-finding provenance chains,
# 300-entry evidence lists, rule/dependency bookkeeping) dominates the
# Gemini prompt for EVERY query. The compacted form below keeps every
# agent's verdict (status/summary/interpretations/findings statements/
# unknowns/conflicts/warnings/fingerprints) while summarizing verbose
# bookkeeping as counts + deterministic samples. Full findings stay
# available internally under `_AGENT_FINDINGS_FULL` (excluded from the
# Gemini payload). No astrology is modified; no facts are invented.

MAX_AGENT_FINDINGS_BYTES = 32_000
MAX_FINDINGS_PER_AGENT = 25
MAX_EVIDENCE_SAMPLE = 5
MAX_PROVENANCE_CHAIN_SAMPLE = 3


def _sample_strings(items: Any, limit: int) -> Tuple[List[str], int]:
    if not isinstance(items, list):
        return [], 0
    strings = sorted(_safe_str(x) for x in items)
    return strings[:limit], len(strings)


def _count_strings(items: Any) -> int:
    if not isinstance(items, list):
        return 0
    return len(items)


def _compact_agent_finding(f: Dict[str, Any]) -> Dict[str, Any]:
    data = f.get("data") if isinstance(f.get("data"), list) else []
    prov = f.get("provenance") if isinstance(f.get("provenance"), dict) else {}
    return {
        "finding_id": _safe_str(f.get("finding_id")),
        "type": _safe_str(f.get("type")),
        # Statement passes through VERBATIM (DATA) — never rewritten.
        "statement": _safe_str(f.get("statement")),
        "confidence_label": _safe_str(f.get("confidence_label")),
        "tradition": _safe_str(f.get("tradition")),
        "data": [
            {"fact_key": _safe_str(d.get("fact_key")),
             "value": _safe_str(d.get("value"))}
            for d in data[:4]
            if isinstance(d, dict)
        ],
        "data_total": len(data),
        # Bookkeeping ID lists travel as counts only (full form internal).
        "supporting_inputs_total": _count_strings(f.get("supporting_inputs")),
        "evidence_ids_total": _count_strings(f.get("evidence_ids")),
        "rule_ids_total": _count_strings(f.get("rule_ids")),
        "provenance_origin": _safe_str(prov.get("origin")),
        "provenance_fact_key": _safe_str(prov.get("fact_key")),
    }


def _compact_agent_result(res: Any) -> Dict[str, Any]:
    if not isinstance(res, dict):
        return {}
    findings = res.get("findings") if isinstance(res.get("findings"), list) else []
    findings = [f for f in findings if isinstance(f, dict)]
    findings_sorted = sorted(findings, key=lambda f: _safe_str(f.get("finding_id")))
    rule_used, rule_used_total = _sample_strings(
        res.get("rule_results_used"), MAX_EVIDENCE_SAMPLE
    )
    evidence, evidence_total = _sample_strings(res.get("evidence"), MAX_EVIDENCE_SAMPLE)
    deps, deps_total = _sample_strings(res.get("dependencies"), MAX_EVIDENCE_SAMPLE)
    prov = res.get("provenance") if isinstance(res.get("provenance"), dict) else {}
    chain = prov.get("chain") if isinstance(prov.get("chain"), list) else []
    chain_sorted = sorted(
        (c for c in chain if isinstance(c, dict)),
        key=lambda c: _safe_str(c.get("finding_id")),
    )
    return {
        "agent_id": _safe_str(res.get("agent_id")),
        "agent_version": _safe_str(res.get("agent_version")),
        "status": _safe_str(res.get("status")),
        "summary": _safe_str(res.get("summary")),
        "findings": [_compact_agent_finding(f)
                      for f in findings_sorted[:MAX_FINDINGS_PER_AGENT]],
        "findings_total": len(findings_sorted),
        "facts_used": res.get("facts_used") if isinstance(res.get("facts_used"), dict)
        else [_safe_str(x) for x in (res.get("facts_used") or [])][:16],
        "rule_results_used_sample": rule_used,
        "rule_results_used_total": rule_used_total,
        "interpretations": [_safe_str(x) for x in (res.get("interpretations") or [])]
        if isinstance(res.get("interpretations"), list) else [],
        "unknowns": [_safe_str(x) for x in (res.get("unknowns") or [])]
        if isinstance(res.get("unknowns"), list) else [],
        "conflicts": [_safe_str(x) for x in (res.get("conflicts") or [])]
        if isinstance(res.get("conflicts"), list) else [],
        "evidence_sample": evidence,
        "evidence_total": evidence_total,
        "dependencies_sample": deps,
        "dependencies_total": deps_total,
        "warnings": [_safe_str(x) for x in (res.get("warnings") or [])]
        if isinstance(res.get("warnings"), list) else [],
        "provenance_chain_sample": [
            {"finding_id": _safe_str(c.get("finding_id")),
             "type": _safe_str(c.get("type"))}
            for c in chain_sorted[:MAX_PROVENANCE_CHAIN_SAMPLE]
        ],
        "provenance_chain_total": len(chain_sorted),
        "input_fingerprint": _safe_str(res.get("input_fingerprint")),
        "output_fingerprint": _safe_str(res.get("output_fingerprint")),
        "_source": _safe_str(res.get("_source")),
    }


def project_agent_findings_for_ai(
    full_findings: Any, *, max_bytes: int = MAX_AGENT_FINDINGS_BYTES
) -> Dict[str, Any]:
    """Deterministic bounded AI-facing projection of AGENT_FINDINGS."""
    if not isinstance(full_findings, dict):
        return {"status": "unavailable", "_source": "production_agents_projection"}
    results = full_findings.get("results")
    compacted_results = []
    if isinstance(results, list):
        for entry in results:
            if not isinstance(entry, dict):
                continue
            inner = entry.get("result")
            compacted_results.append({
                "agent_id": _safe_str(entry.get("agent_id")),
                "result": _compact_agent_result(inner),
            })
    compacted_results.sort(key=lambda e: e.get("agent_id"))
    synthesis = full_findings.get("synthesis") if isinstance(
        full_findings.get("synthesis"), dict) else {}
    syn_inner = synthesis.get("result") if isinstance(
        synthesis.get("result"), dict) else {}
    syn_findings = syn_inner.get("findings") if isinstance(
        syn_inner.get("findings"), list) else []
    syn_findings = [f for f in syn_findings if isinstance(f, dict)]
    syn_sorted = sorted(syn_findings, key=lambda f: _safe_str(f.get("finding_id")))
    projection: Dict[str, Any] = {
        "_source": "production_agents_projection",
        "agents": full_findings.get("agents") if isinstance(
            full_findings.get("agents"), list) else [],
        "results": compacted_results,
        "results_total": len(compacted_results),
        "records": full_findings.get("records") if isinstance(
            full_findings.get("records"), list) else [],
        "rejected": full_findings.get("rejected") if isinstance(
            full_findings.get("rejected"), list) else [],
        "context_fingerprint": _safe_str(full_findings.get("context_fingerprint")),
        "registry_fingerprint": _safe_str(full_findings.get("registry_fingerprint")),
        "synthesis": {
            # Synthesis identity envelope preserved verbatim (contract:
            # synthesis.agent_id is the 6th expected agent id).
            "agent_id": _safe_str(synthesis.get("agent_id")),
            "agent_version": _safe_str(synthesis.get("agent_version")),
            "status": _safe_str(synthesis.get("status")),
            "findings": [_compact_agent_finding(f) for f in syn_sorted],
            "findings_total": len(syn_sorted),
            "unknowns": [_safe_str(x) for x in (syn_inner.get("unknowns") or [])]
            if isinstance(syn_inner.get("unknowns"), list) else [],
            "conflicts": [_safe_str(x) for x in (syn_inner.get("conflicts") or [])]
            if isinstance(syn_inner.get("conflicts"), list) else [],
            "warnings": [_safe_str(x) for x in (syn_inner.get("warnings") or [])]
            if isinstance(syn_inner.get("warnings"), list) else [],
            "interpretations": [
                _safe_str(x) for x in (syn_inner.get("interpretations") or [])]
            if isinstance(syn_inner.get("interpretations"), list) else [],
        },
        "COMPACTION": {
            "compaction_applied": True,
            "note": "Verbose agent bookkeeping (evidence lists, provenance "
                    "chains, rule/dependency details) summarized as counts + "
                    "deterministic samples for LLM context size. Verdicts and "
                    "finding statements are verbatim; omission is NOT evidence "
                    "of absence.",
        },
        "LIMITS": {"max_agent_findings_bytes": max_bytes},
    }
    size = projection_serialized_size(projection)
    # Deterministic staged tightening (statements are never dropped):
    #  1. drop per-finding data samples (keep counts);
    #  2. cap findings per agent at 8 (highest finding_id order is stable);
    #  3. verdicts-only (summaries + interpretations + counts).
    if size > max_bytes:
        for entry in compacted_results:
            for f in entry.get("result", {}).get("findings", []):
                f.pop("data", None)
        syn = projection.get("synthesis", {})
        for f in syn.get("findings", []):
            if isinstance(f, dict):
                f.pop("data", None)
        size = projection_serialized_size(projection)
    if size > max_bytes:
        for entry in compacted_results:
            res = entry.get("result", {})
            if len(res.get("findings", [])) > 8:
                res["findings"] = res["findings"][:8]
        syn = projection.get("synthesis", {})
        if len(syn.get("findings", [])) > 8:
            syn["findings"] = syn["findings"][:8]
        size = projection_serialized_size(projection)
    if size > max_bytes:
        for entry in compacted_results:
            res = entry.get("result", {})
            res["findings"] = []
        projection["synthesis"]["findings"] = []
        size = projection_serialized_size(projection)
    projection["SERIALIZED_BYTES"] = size
    projection["APPROX_TOKENS"] = size // 4
    return projection


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def project_future_window_for_ai(
    full_section: Dict[str, Any],
    query: str = "",
    *,
    max_events: int = MAX_EXACT_EVENTS_FOR_LLM,
    max_signals: int = MAX_SIGNALS_PER_CANDIDATE,
    max_windows: int = MAX_WINDOWS_PER_CANDIDATE,
    max_supporting: int = MAX_SUPPORTING_PER_LIST,
    max_bytes: int = MAX_AI_FUTURE_BYTES,
) -> Dict[str, Any]:
    """
    Deterministic AI-facing projection of a complete canonical FUTURE_WINDOW.

    Reads ``full_section`` (output of future_window.build_future_window_section)
    and returns a bounded dict safe for Gemini. The input is never mutated.
    Timestamps, statuses, precisions, evidence states, and provenance pass
    through verbatim; only LIST CARDINALITY is reduced, with explicit counts.
    """
    if not isinstance(full_section, dict):
        return {
            "FUTURE_WINDOW_STATUS": "unavailable",
            "reason": "no-canonical-section",
            "_source": "canonical-future-window-projection",
        }

    requested = _requested_categories(query)
    dasha_block = full_section.get("DASHA_AT_WINDOW_START") or {}
    dasha_lords = _dasha_lords(dasha_block)

    pred = full_section.get("PREDICTION") or {}
    candidates = pred.get("candidates") if isinstance(pred.get("candidates"), list) else []
    candidates = [c for c in candidates if isinstance(c, dict)]

    implicated = _candidate_implicated_planets(candidates)
    exact_times = _signal_exact_times(candidates)
    requested_support_keys = _requested_category_support_keys(candidates, requested)
    relevant_tokens: Set[str] = set(dasha_lords) | set(implicated)

    raw_events = full_section.get("EXACT_TRANSIT_EVENTS")
    raw_events = raw_events if isinstance(raw_events, list) else []
    total_events = len([e for e in raw_events if isinstance(e, dict)])

    sent_events = _select_events(
        [e for e in raw_events if isinstance(e, dict)],
        dasha_lords=dasha_lords,
        implicated=implicated,
        exact_times=exact_times,
        requested_support_keys=requested_support_keys,
        limit=max_events,
    )
    sent_stamps = {e["timestamp_iso"] for e in sent_events if e.get("timestamp_iso")}

    compacted_candidates = [
        _compact_candidate(
            c,
            relevant_tokens=relevant_tokens,
            sent_event_stamps=sent_stamps,
            max_signals=max_signals,
            max_windows=max_windows,
            max_supporting=max_supporting,
        )
        for c in candidates
    ]

    requested_period = copy.deepcopy(full_section.get("REQUESTED_PERIOD") or {})
    provenance = copy.deepcopy(full_section.get("PROVENANCE") or {})
    if isinstance(provenance, dict):
        provenance["projection"] = "canonical-future-window-projection"
        provenance["projection_of"] = "canonical-future-window"

    import collections as _collections

    omitted_by_kind: Dict[str, int] = dict(
        _collections.Counter(
            _safe_str(e.get("kind") or e.get("type")) or "unknown"
            for e in raw_events
            if isinstance(e, dict)
        )
    )
    sent_by_kind: Dict[str, int] = dict(
        _collections.Counter(e.get("kind") or "unknown" for e in sent_events)
    )
    for kind in list(omitted_by_kind.keys()):
        omitted_by_kind[kind] = omitted_by_kind[kind] - sent_by_kind.get(kind, 0)
        if omitted_by_kind[kind] <= 0:
            del omitted_by_kind[kind]

    compaction_applied = bool(
        total_events > len(sent_events)
        or any(
            c.get("signals_total", 0) > len(c.get("signals", []))
            or c.get("windows_total", 0) > len(c.get("windows", []))
            for c in compacted_candidates
        )
    )

    unknowns = pred.get("unknowns") if isinstance(pred.get("unknowns"), list) else []
    conflicts = pred.get("conflicts") if isinstance(pred.get("conflicts"), list) else []
    warnings = pred.get("warnings") if isinstance(pred.get("warnings"), list) else []

    projection: Dict[str, Any] = {
        "_source": "canonical-future-window-projection",
        "REQUESTED_PERIOD": requested_period,
        "future_start": _safe_str(requested_period.get("evaluation_start")),
        "future_end": _safe_str(requested_period.get("evaluation_end")),
        "FUTURE_WINDOW_STATUS": "available",
        "DASHA_AT_WINDOW_START": copy.deepcopy(dasha_block),
        # TRANSIT_FACTS are tiny (planet->sign map); always sent verbatim.
        "TRANSIT_FACTS_AT_WINDOW_START": copy.deepcopy(
            full_section.get("TRANSIT_FACTS_AT_WINDOW_START") or {}
        ),
        "EXACT_TRANSIT_EVENTS": sent_events,
        "EXACT_TRANSIT_EVENTS_COMPACTION": {
            "total_exact_events": total_events,
            "events_sent_to_llm": len(sent_events),
            "events_omitted_from_llm": max(0, total_events - len(sent_events)),
            "compaction_applied": compaction_applied,
            "omitted_by_kind": omitted_by_kind,
            "note": COMPACTION_NOTE,
        },
        "PREDICTION": {
            "status": _safe_str(pred.get("status")),
            "evidence_state": _safe_str(pred.get("evidence_state")),
            "profile": _safe_str(pred.get("profile")),
            "candidates": compacted_candidates,
            "candidates_total": len(compacted_candidates),
            "unknowns": [_safe_str(x) for x in unknowns],
            "conflicts": [_safe_str(x) for x in conflicts],
            "warnings": [_safe_str(x) for x in warnings],
        },
        "PROVENANCE": provenance,
        "SEMANTICS": {
            "EXACT": SEMANTICS_EXACT,
            "EVENT_WINDOW": SEMANTICS_EVENT_WINDOW,
            "UNKNOWN": SEMANTICS_UNKNOWN,
            "compaction_note": COMPACTION_NOTE,
            "no_independent_recalculation": NO_RECALC_RULE,
        },
        "LIMITS": {
            "max_exact_events_for_llm": max_events,
            "max_signals_per_candidate": max_signals,
            "max_windows_per_candidate": max_windows,
            "max_supporting_per_list": max_supporting,
            "max_ai_future_bytes": max_bytes,
        },
    }

    # Enforce the serialized byte budget deterministically: progressively
    # tighten list caps stage by stage until under budget (or floors hit).
    # Stages are fixed constants, so repeated/concurrent runs converge to
    # the identical projection.
    def _serialized_len(obj: Dict[str, Any]) -> int:
        return len(
            json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )

    def _rebuild(
        sig_cap: int, win_cap: int, sup_cap: int, ev_cap: int
    ) -> None:
        nonlocal sent_events, sent_stamps, compacted_candidates
        sent_events = _select_events(
            [e for e in raw_events if isinstance(e, dict)],
            dasha_lords=dasha_lords,
            implicated=implicated,
            exact_times=exact_times,
            requested_support_keys=requested_support_keys,
            limit=ev_cap,
        )
        sent_stamps = {e["timestamp_iso"] for e in sent_events if e.get("timestamp_iso")}
        compacted_candidates = [
            _compact_candidate(
                c,
                relevant_tokens=relevant_tokens,
                sent_event_stamps=sent_stamps,
                max_signals=sig_cap,
                max_windows=win_cap,
                max_supporting=sup_cap,
            )
            for c in candidates
        ]
        projection["EXACT_TRANSIT_EVENTS"] = sent_events
        projection["EXACT_TRANSIT_EVENTS_COMPACTION"].update(
            {
                "events_sent_to_llm": len(sent_events),
                "events_omitted_from_llm": max(0, total_events - len(sent_events)),
            }
        )
        projection["PREDICTION"]["candidates"] = compacted_candidates
        projection["LIMITS"].update(
            {
                "max_exact_events_for_llm": ev_cap,
                "max_signals_per_candidate": sig_cap,
                "max_windows_per_candidate": win_cap,
                "max_supporting_per_list": sup_cap,
            }
        )

    serialized_len = _serialized_len(projection)
    if serialized_len > max_bytes:
        for stage in range(
            max(
                len(_FLOOR_SIGNALS),
                len(_FLOOR_WINDOWS),
                len(_FLOOR_SUPPORTING),
                len(_FLOOR_EVENTS),
            )
        ):
            sig_cap = min(
                _FLOOR_SIGNALS[min(stage, len(_FLOOR_SIGNALS) - 1)], max_signals
            )
            win_cap = min(
                _FLOOR_WINDOWS[min(stage, len(_FLOOR_WINDOWS) - 1)], max_windows
            )
            sup_cap = min(
                _FLOOR_SUPPORTING[min(stage, len(_FLOOR_SUPPORTING) - 1)],
                max_supporting,
            )
            ev_cap = min(
                _FLOOR_EVENTS[min(stage, len(_FLOOR_EVENTS) - 1)], max_events
            )
            _rebuild(sig_cap, win_cap, sup_cap, ev_cap)
            serialized_len = _serialized_len(projection)
            if serialized_len <= max_bytes:
                break

    projection["SERIALIZED_BYTES"] = serialized_len
    projection["APPROX_TOKENS"] = serialized_len // 4
    if serialized_len > max_bytes or total_events > len(sent_events):
        projection["EXACT_TRANSIT_EVENTS_COMPACTION"]["compaction_applied"] = True
    return projection


def projection_serialized_size(projection: Dict[str, Any]) -> int:
    """Deterministic serialized size (compact JSON, sorted keys) in bytes."""
    return len(
        json.dumps(projection, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def estimate_tokens(char_count: int) -> int:
    """Rough token estimate (~4 chars/token for English/JSON)."""
    return max(0, int(char_count) // 4)


def sanitize_projection_for_test(projection: Dict[str, Any]) -> Dict[str, Any]:
    """Return a JSON-round-tripped copy (proves serializability/determinism)."""
    return json.loads(
        json.dumps(projection, sort_keys=True, separators=(",", ":"))
    )
