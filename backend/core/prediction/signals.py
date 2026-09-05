"""
Phase 8 — signal generation (§§7–13).

Every signal restates supplied canonical input. Signal IDs are deterministic
hashes of (source_system, source_type, source_id, window). No dates are
derived: dasha/transit windows are copied verbatim from supplied rows;
activation mirrors supplied activation fields; missing layers yield UNKNOWN
signals, never negative evidence.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from .models import (
    ANTARDASHA_SIGNAL,
    CONFLICTED,
    DASHA_SIGNAL,
    DOSHA_ACTIVATION_SIGNAL,
    EXCLUSION_SIGNAL,
    FORMATION_SIGNAL,
    JAIMINI_DASHA_SIGNAL,
    PRATYANTAR_SIGNAL,
    TRANSIT_SIGNAL,
    UNKNOWN,
    YOGA_ACTIVATION_SIGNAL,
    EventSignal,
)

_ACTIVE_VALUES = ("ACTIVE", "PARTIALLY_ACTIVE", "FORMED")


def _signal_id(system: str, kind: str, source: str, window: str) -> str:
    digest = hashlib.sha256(f"{system}|{kind}|{source}|{window}".encode()).hexdigest()[:12]
    return f"SIG-{digest}"


def _strength_of(outcome: Any) -> str:
    for key in ("strength_status", "strength", "dignity"):
        value = outcome.get(key, "") if isinstance(outcome, dict) else ""
        if value:
            return str(value)
    return ""


def formation_signals(definition: Any, outcomes: Dict[str, Any]) -> List[EventSignal]:
    signals = []
    for rule_id in sorted(definition.required_rule_families):
        outcome = outcomes.get(rule_id)
        if outcome is None:
            signals.append(EventSignal(
                signal_id=_signal_id("RULE", FORMATION_SIGNAL, rule_id, "missing"),
                source_system=_system_of(rule_id), source_type=FORMATION_SIGNAL,
                source_id=rule_id, status=UNKNOWN, ancestry=[],
                evidence=[], provenance={"origin": "missing-rule-outcome"}))
            continue
        signals.append(EventSignal(
            signal_id=_signal_id("RULE", FORMATION_SIGNAL, rule_id,
                                 str(outcome.get("formation", ""))),
            source_system=_system_of(rule_id), source_type=FORMATION_SIGNAL,
            source_id=rule_id,
            strength_label=_strength_of(outcome),
            status=str(outcome.get("formation", UNKNOWN)),
            ancestry=sorted(outcome.get("depends_on", [])),
            evidence=sorted(outcome.get("evidence_ids", [])),
            provenance={"origin": "supplied-rule-outcome",
                        "rule_version": str(outcome.get("rule_version", ""))}))
    return signals


def _system_of(rule_id: str) -> str:
    if rule_id.startswith("JAI."):
        return "JAIMINI"
    if rule_id.startswith("DOSHA."):
        return "DOSHA"
    if rule_id.startswith("PARASHARI."):
        return "YOGA"
    return "CUSTOM"


def activation_signals(outcomes: Dict[str, Any], wanted: List[str]) -> List[EventSignal]:
    signals = []
    for rule_id in sorted(wanted):
        outcome = outcomes.get(rule_id)
        if outcome is None:
            continue
        kind = (DOSHA_ACTIVATION_SIGNAL if _system_of(rule_id) == "DOSHA"
                else YOGA_ACTIVATION_SIGNAL)
        signals.append(EventSignal(
            signal_id=_signal_id("RULE", kind, rule_id,
                                 str(outcome.get("activation", ""))),
            source_system=_system_of(rule_id), source_type=kind,
            source_id=rule_id,
            status=str(outcome.get("activation", UNKNOWN)),
            ancestry=sorted(outcome.get("depends_on", [])),
            evidence=sorted(outcome.get("evidence_ids", [])),
            provenance={"origin": "supplied-activation"}))
    return signals


def dasha_signals(periods: List[Any], has_dasha: bool) -> List[EventSignal]:
    if not has_dasha:
        return [EventSignal(
            signal_id=_signal_id("DASHA", DASHA_SIGNAL, "unavailable", "missing"),
            source_system="DASHA", source_type=DASHA_SIGNAL,
            source_id="dasha-unavailable", status=UNKNOWN, ancestry=[],
            evidence=[], provenance={"origin": "missing-dasha-layer"})]
    signals = []
    for period in periods:
        kind = { "MD": DASHA_SIGNAL, "MAHA_DASHA": DASHA_SIGNAL,
                 "AD": ANTARDASHA_SIGNAL, "ANTARDASHA": ANTARDASHA_SIGNAL,
                 "PD": PRATYANTAR_SIGNAL, "PRATYANTAR": PRATYANTAR_SIGNAL,
                 }.get(str(period.get("level", "")).upper(), DASHA_SIGNAL)
        signals.append(EventSignal(
            signal_id=_signal_id("DASHA", kind, period.get("key", ""),
                                 period.get("start_iso", "")),
            source_system="DASHA", source_type=kind,
            source_id=period.get("key", ""),
            active_from=period.get("start_iso", ""),
            active_to=period.get("end_iso", ""),
            status="ACTIVE",
            ancestry=[f"dasha.{period.get('system', '')}.{period.get('key', '')}"],
            evidence=[], provenance={"origin": "supplied-dasha-period",
                                     "system": period.get("system", ""),
                                     "profile": period.get("profile", ""),
                                     "fingerprint": period.get("fingerprint", "")}))
    return signals


def jaimini_dasha_signals(periods: List[Any], has_jaimini: bool) -> List[EventSignal]:
    if not has_jaimini:
        return [EventSignal(
            signal_id=_signal_id("JAIMINI", JAIMINI_DASHA_SIGNAL, "unavailable", "missing"),
            source_system="JAIMINI", source_type=JAIMINI_DASHA_SIGNAL,
            source_id="jaimini-unavailable", status=UNKNOWN, ancestry=[],
            evidence=[], provenance={"origin": "missing-jaimini-layer"})]
    signals = []
    for period in periods:
        signals.append(EventSignal(
            signal_id=_signal_id("JAIMINI", JAIMINI_DASHA_SIGNAL,
                                 period.get("key", ""), period.get("start_iso", "")),
            source_system="JAIMINI", source_type=JAIMINI_DASHA_SIGNAL,
            source_id=period.get("key", ""),
            active_from=period.get("start_iso", ""),
            active_to=period.get("end_iso", ""),
            status="ACTIVE",
            ancestry=[f"jaimini.{period.get('profile', '')}.{period.get('key', '')}"],
            evidence=[], provenance={"origin": "supplied-chara-period",
                                     "profile": period.get("profile", ""),
                                     "fingerprint": period.get("fingerprint", "")}))
    return signals


def transit_signals(facts: Dict[str, str], events: List[Any],
                    has_transit: bool) -> List[EventSignal]:
    if not has_transit:
        return [EventSignal(
            signal_id=_signal_id("TRANSIT", TRANSIT_SIGNAL, "unavailable", "missing"),
            source_system="TRANSIT", source_type=TRANSIT_SIGNAL,
            source_id="transit-unavailable", status=UNKNOWN, ancestry=[],
            evidence=[], provenance={"origin": "missing-transit-layer"})]
    signals = []
    for planet in sorted(facts):
        signals.append(EventSignal(
            signal_id=_signal_id("TRANSIT", TRANSIT_SIGNAL, planet, facts[planet]),
            source_system="TRANSIT", source_type=TRANSIT_SIGNAL,
            source_id=f"transit.{planet}", status="ACTIVE",
            ancestry=[f"transit.{planet}.sign"],
            evidence=[], provenance={"origin": "supplied-transit-fact",
                                     "sign": facts[planet]}))
    for event in events:
        stamp = event.get("timestamp_iso", "") if isinstance(event, dict) else ""
        signals.append(EventSignal(
            signal_id=_signal_id("TRANSIT", TRANSIT_SIGNAL,
                                 event.get("planet", ""), stamp),
            source_system="TRANSIT", source_type=TRANSIT_SIGNAL,
            source_id=f"transit-event:{event.get('planet', '')}:{event.get('kind', '')}",
            exact_time=stamp, status="ACTIVE",
            ancestry=[f"transit.{event.get('planet', '')}.sign"],
            evidence=[], provenance={"origin": "supplied-transit-event",
                                     "fingerprint": event.get("fingerprint", "")}))
    return signals


def exclusion_signals(definition: Any, outcomes: Dict[str, Any]) -> List[EventSignal]:
    signals = []
    for rule_id in sorted(definition.exclusion_signals):
        outcome = outcomes.get(rule_id)
        if outcome is None:
            continue
        if str(outcome.get("formation", "")) == "FORMED":
            signals.append(EventSignal(
                signal_id=_signal_id("RULE", EXCLUSION_SIGNAL, rule_id, "formed"),
                source_system=_system_of(rule_id), source_type=EXCLUSION_SIGNAL,
                source_id=rule_id, status="ACTIVE",
                ancestry=sorted(outcome.get("depends_on", [])),
                evidence=sorted(outcome.get("evidence_ids", [])),
                provenance={"origin": "supplied-exclusion"}))
    return signals


def generate_event_signals(definition: Any, entry: Dict[str, Any]) -> Dict[str, List[EventSignal]]:
    """Split supplied input into named signal groups. No prose here."""
    raw = entry.get("outcomes", {})
    outcomes = ({o.get("rule_id", ""): o for o in raw} if isinstance(raw, list)
                else dict(raw))
    periods = entry.get("periods", [])
    vim_periods = [p for p in periods if p.get("system") == "VIMSHOTTARI"]
    chara_periods = [p for p in periods if p.get("system") == "CHARA"]
    return {
        "formation": formation_signals(definition, outcomes),
        "activation": activation_signals(
            outcomes, list(definition.required_rule_families)),
        "dasha": dasha_signals(vim_periods, entry.get("has_dasha", True)),
        "jaimini_dasha": jaimini_dasha_signals(
            chara_periods, entry.get("has_jaimini", True)),
        "transit": transit_signals(entry.get("transit_facts", {}),
                                   entry.get("transit_events", []),
                                   entry.get("has_transit", True)),
        "exclusion": exclusion_signals(definition, outcomes),
    }
