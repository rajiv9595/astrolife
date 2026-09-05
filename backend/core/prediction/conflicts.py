"""
Phase 8 — conflict engine (§19) and uncertainty engine (§§20, 28, 38).

Conflicts: ACTIVE-vs-INACTIVE across systems and FORMED-vs-NOT_FORMED across
rules propagate as CONFLICTED with ids/systems/rules/windows/provenance. No
winner is forced. Unknowns: missing layers propagate; MISSING is never
NOT_FORMED, INACTIVE, or NO_EVENT. Evidence completeness is categorical.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .models import (
    CONFLICTED,
    EVIDENCE_CONFLICTED,
    EVIDENCE_COMPLETE,
    EVIDENCE_INSUFFICIENT,
    EVIDENCE_PARTIAL,
    FORMED,
    NOT_FORMED,
    UNKNOWN,
)


def detect_conflicts(groups: Dict[str, List[Any]],
                     supplied: List[Any],
                     formation_policy: str = "ANY") -> List[Dict[str, Any]]:
    """Returns conflict records {conflict_id, systems, rules, windows, provenance}.

    A FORMED-vs-NOT_FORMED split is a genuine conflict only under an ALL
    formation policy (members must agree) or for same-proposition pairs
    supplied authoritatively (e.g. 6E catalogue conflicts). Under ANY policy,
    disagreement is normal family behavior, not conflict.
    """
    records = []
    family = set()
    for signal in groups.get("formation", []):
        family.add(signal.source_id)
    for entry in supplied:
        if isinstance(entry, dict):
            rule_a, rule_b = entry.get("rule_a", ""), entry.get("rule_b", "")
        else:
            rule_a, rule_b = getattr(entry, "rule_a", ""), getattr(entry, "rule_b", "")
        if rule_a not in family and rule_b not in family:
            continue
        if isinstance(entry, dict):
            system_a, system_b = entry.get("system_a", ""), entry.get("system_b", "")
            cid = entry.get("conflict_id", "")
        else:
            system_a, system_b = getattr(entry, "system_a", ""), getattr(entry, "system_b", "")
            cid = getattr(entry, "conflict_id", "")
        records.append({
            "conflict_id": cid,
            "systems": sorted({system_a, system_b}),
            "rules": sorted({rule_a, rule_b}),
            "windows": [],
            "provenance": {"origin": "supplied-conflict"}})
    formations: Dict[str, List[str]] = {}
    for signal in groups.get("formation", []):
        if signal.status in (FORMED, NOT_FORMED):
            formations.setdefault(signal.status, []).append(signal.source_id)
    if (FORMED in formations and NOT_FORMED in formations
            and formation_policy == "ALL"):
        records.append({
            "conflict_id": "CONFLICT:formation-split",
            "systems": sorted({s.split(".")[0] for s in
                               formations[FORMED] + formations[NOT_FORMED]}),
            "rules": sorted(formations[FORMED] + formations[NOT_FORMED]),
            "windows": [],
            "provenance": {"origin": "formation-disagreement"}})
    activity: Dict[str, List[str]] = {}
    for name in ("dasha", "jaimini_dasha", "transit"):
        for signal in groups.get(name, []):
            if signal.status in ("ACTIVE", "INACTIVE"):
                activity.setdefault(signal.status, []).append(
                    f"{name}:{signal.source_id}")
    if "ACTIVE" in activity and "INACTIVE" in activity:
        records.append({
            "conflict_id": "CONFLICT:activity-split",
            "systems": ["DASHA", "TRANSIT"],
            "rules": [],
            "windows": [s.active_from for s in groups.get("dasha", [])[:1]],
            "provenance": {"origin": "activity-disagreement"}})
    return sorted(records, key=lambda r: r["conflict_id"])


def collect_unknowns(groups: Dict[str, List[Any]],
                     formation: Dict[str, Any],
                     activation: Dict[str, Any]) -> List[str]:
    unknowns: List[str] = []
    unknowns.extend(f"formation:{rule}" for rule in formation.get("unknowns", []))
    unknowns.extend(activation.get("unknowns", []))
    for name, signals in sorted(groups.items()):
        for signal in signals:
            if signal.status == UNKNOWN:
                unknowns.append(f"{name}:{signal.source_id}")
    return sorted(set(unknowns))


def evidence_state(required_present: bool, optional_missing: List[str],
                   has_conflicts: bool, has_unknowns: bool) -> str:
    if has_conflicts:
        return EVIDENCE_CONFLICTED
    if not required_present or has_unknowns:
        return EVIDENCE_INSUFFICIENT
    if optional_missing:
        return EVIDENCE_PARTIAL
    return EVIDENCE_COMPLETE
