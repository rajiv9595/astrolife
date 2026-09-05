"""
Phase 8 — activation engine (§§6, 9–13).

Activation answers ONLY whether supplied dasha/transit/activation signals
overlap the request window. Absent activation data is UNKNOWN, never
INACTIVE. Formation truth is never consulted here (separation, §6).
"""
from __future__ import annotations

from typing import Any, Dict, List

from .models import UNKNOWN
from .windows import clip, parse_iso

_ACTIVE = ("ACTIVE", "PARTIALLY_ACTIVE", "FORMED")


def _overlaps(signal: Any, start_iso: str, end_iso: str) -> bool:
    if signal.exact_time:
        point = parse_iso(signal.exact_time)
        start, end = parse_iso(start_iso), parse_iso(end_iso)
        if point is None or start is None:
            return False
        if end is None:
            return start <= point
        return start <= point < end
    if not signal.active_from:
        return False
    sig_start, sig_end = parse_iso(signal.active_from), parse_iso(signal.active_to)
    req_start, req_end = parse_iso(start_iso), parse_iso(end_iso)
    if sig_start is None or req_start is None:
        return False
    latest_start = max(sig_start, req_start)
    ends = [e for e in (sig_end, req_end) if e is not None]
    if not ends:
        return True
    return latest_start < min(ends)


def evaluate_event_activation(groups: Dict[str, List[Any]], start_iso: str,
                              end_iso: str) -> Dict[str, Any]:
    """Returns {status, active_signals, unknowns}.

    Rule-activation signals (tradition-level ACTIVE) count as active without
    a window; dasha/Jaimini/transit signals need request-window overlap.
    Windowless transit fact context is ignored for activation (it carries no
    timing content). Absent layers are UNKNOWN, never INACTIVE.
    """
    unknowns: List[str] = []
    active: List[Any] = []
    rule_active = False
    rule_present = False
    timed_present = False
    timed_overlap = False
    for signal in groups.get("activation", []):
        origin = signal.provenance.get("origin", "")
        if origin.startswith("missing-"):
            unknowns.append(f"activation:{signal.source_id}")
        elif signal.status in _ACTIVE:
            rule_active = True
            rule_present = True
            active.append(signal)
        else:
            rule_present = True
    for name in ("dasha", "jaimini_dasha", "transit"):
        for signal in groups.get(name, []):
            origin = signal.provenance.get("origin", "")
            if origin.startswith("missing-"):
                unknowns.append(f"{name}:{signal.source_id}")
                continue
            if not signal.active_from and not signal.exact_time:
                continue
            timed_present = True
            if signal.status in _ACTIVE and _overlaps(signal, start_iso, end_iso):
                timed_overlap = True
                active.append(signal)
    if rule_active or timed_overlap:
        status = "ACTIVE"
    elif timed_present:
        status = "INACTIVE"
    else:
        status = UNKNOWN
    return {"status": status, "active_signals": active,
            "unknowns": sorted(set(unknowns))}
