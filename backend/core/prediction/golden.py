"""
Phase 8 — golden fixture construction.

Builds PredictionInput entry-dicts from canonical engines on the golden
chart (fixture setup, not prediction reasoning) by reusing the Phase 7
canonical bundle, 6E catalogue manifests (ancestry/verification), and
canonical dasha timelines for all three Chara profiles.

NOTE: this module invokes canonical calculators to CONSTRUCT fixtures. It is
not on any prediction execution path; the static calculation-import audit
(§55) scopes to prediction implementation modules only, with this exclusion
documented here and in the security report.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .models import PredictionInput

CHARA_PROFILES = (
    "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL",
    "CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED",
    "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS",
)

GOLDEN_REQUEST_START = "2026-01-01T00:00:00Z"
GOLDEN_REQUEST_END = "2027-01-01T00:00:00Z"


def _enum(value: Any) -> str:
    return str(getattr(value, "value", value))


def build_golden_entry(bundle: Any = None) -> Dict[str, Any]:
    """Assemble the golden PredictionInput entry + canonical bundle."""
    from core.agents.golden import build_canonical_bundle
    from core.jaimini.dasha import calculate_jaimini_dasha
    from core.jaimini.dasha.profile import JaiminiDashaProfile
    from core.rules.dynamic.knowledge import find_conflicts, get_rule_catalogue

    from .catalogue import catalogue_rule_versions
    from .models import SuppliedConflict

    bundle = bundle or build_canonical_bundle()
    rule_results = bundle.rule_results or {}
    outcomes: List[Dict[str, Any]] = []

    def _rule(rule_id: str, tradition: str, formation: str, activation: str,
              evidence: List[str], system: str) -> Dict[str, Any]:
        return {"rule_id": rule_id, "rule_version": "1.0.0",
                "tradition": tradition, "system": system,
                "formation": formation, "activation": activation,
                "evidence_ids": list(evidence), "source_ids": [],
                "verification": "", "lifecycle": "ACTIVE", "depends_on": []}

    for result in rule_results.get("parashari", []) or []:
        outcomes.append(_rule(result.rule_id, _enum(result.tradition),
                             _enum(result.formation_status),
                             _enum(result.activation_status),
                             [f"classic-ev:{result.rule_id}:{i:02d}"
                              for i in range(len(result.evidence or []))],
                             "YOGA"))
    dosha_set = rule_results.get("doshas")
    for item in getattr(dosha_set, "dosha_results", []) or []:
        outcomes.append(_rule(getattr(item, "dosha_id", "UNKNOWN"),
                             str(getattr(item, "tradition", "")),
                             str(getattr(item, "formation_status", "")),
                             str(getattr(item, "activation_status", "")),
                             [], "DOSHA"))
    evaluation = rule_results.get("jaimini_yogas")
    for item in getattr(evaluation, "results", []) or []:
        origin = getattr(item, "origin_label", "TRADITION_DEPENDENT")
        tradition = ("JAIMINI_CLASSICAL" if origin == "CLASSICAL_JAIMINI"
                     else "TRADITION_DEPENDENT")
        outcomes.append(_rule(
            item.rule_id, tradition,
            "FORMED" if getattr(item, "formed", False) else "NOT_FORMED",
            "", [f"classic-ev:{item.rule_id}:{i:02d}"
                 for i in range(len(getattr(item, "evidence", []) or []))],
            "JAIMINI"))
    # Developer-rule demonstration outcome (keeps its UNVERIFIED label).
    outcomes.append({"rule_id": "CUSTOM.NATAL.TEST", "rule_version": "1.0.0",
                     "tradition": "CUSTOM_DEVELOPER", "system": "CUSTOM",
                     "formation": "FORMED", "activation": "",
                     "evidence_ids": [], "source_ids": ["DEV-6E-SYNTHETIC"],
                     "verification": "USER_SUPPLIED", "lifecycle": "ACTIVE",
                     "depends_on": ["natal.Mars.sign"]})
    meta = catalogue_rule_versions([o["rule_id"] for o in outcomes])
    for outcome in outcomes:
        info = meta.get(outcome["rule_id"], {})
        if info:
            outcome["rule_version"] = info.get("rule_version", outcome["rule_version"])
            outcome["depends_on"] = info.get("depends_on", [])
            if not outcome["verification"]:
                outcome["verification"] = info.get("verification", "")
            if outcome["rule_id"].startswith("DOSHA."):
                # DoshaResult carries DoshaTradition; canonical tradition
                # comes from the accepted catalogue entry.
                outcome["tradition"] = info.get("tradition", outcome["tradition"])

    periods: List[Dict[str, Any]] = []
    timeline = bundle.dasha_state["dynamic_state"].dasha.get("timeline", {})
    for md in timeline.get("mahadashas", []) or []:
        period = md.get("period", {})
        periods.append({"system": "VIMSHOTTARI", "profile": "VIMSHOTTARI_DEFAULT",
                        "level": "MD", "key": str(period.get("lord", "")),
                        "start_iso": str(period.get("start_utc_iso", "")),
                        "end_iso": str(period.get("end_utc_iso", "")),
                        "fingerprint": "canonical-vimshottari"})
        for ad in md.get("antar_dashas", []) or []:
            sub = ad.get("period", {})
            periods.append({"system": "VIMSHOTTARI", "profile": "VIMSHOTTARI_DEFAULT",
                            "level": "AD",
                            "key": f"{period.get('lord', '')}/{sub.get('lord', '')}",
                            "start_iso": str(sub.get("start_utc_iso", "")),
                            "end_iso": str(sub.get("end_utc_iso", "")),
                            "fingerprint": "canonical-vimshottari"})
    for profile_method in CHARA_PROFILES:
        profile = JaiminiDashaProfile.from_method(profile_method)
        result = calculate_jaimini_dasha(bundle.chart_facts,
                                         bundle.jaimini_facts, profile)
        for item in result.periods or []:
            periods.append({"system": "CHARA", "profile": profile_method,
                            "level": "MD", "key": str(item.sign),
                            "start_iso": str(item.start_utc_iso),
                            "end_iso": str(item.end_utc_iso),
                            "fingerprint": "canonical-chara"})
    transit = bundle.transit_state
    transit_facts = {planet: str(getattr(position, "sign", position))
                     for planet, position in
                     sorted((getattr(transit, "planets", {}) or {}).items())}
    supplied_conflicts = [
        SuppliedConflict(conflict_id=c.conflict_id, rule_a=c.rule_a,
                         rule_b=c.rule_b, system_a=c.tradition_a,
                         system_b=c.tradition_b,
                         detail="6E catalogue same-proposition conflict.",
                         status=c.status)
        for c in find_conflicts(get_rule_catalogue())]
    entry_input = PredictionInput(
        chart_fingerprint="golden-chart",
        calculation_profile="DEFAULT",
        rule_outcomes=[], dasha_periods=[], transit_facts=transit_facts,
        transit_events=[], has_dasha=True, has_transit=True,
        has_jaimini=True, has_strength=True, conflicts=[],
        evidence_ids=[], sources={})
    entry: Dict[str, Any] = {
        "outcomes": outcomes,
        "periods": periods,
        "transit_facts": transit_facts,
        "transit_events": [],
        "has_dasha": True, "has_transit": True, "has_jaimini": True,
        "has_strength": True,
        "conflicts": supplied_conflicts,
        "input_fingerprint": entry_input.fingerprint(),
        "bundle": bundle,
    }
    return entry


def golden_request(**overrides: Any) -> Dict[str, Any]:
    from .models import PredictionRequest
    args: Dict[str, Any] = {
        "request_id": "GOLDEN-REQ-8", "chart_fingerprint": "golden-chart",
        "event_types": [], "event_ids": [],
        "prediction_profile": "PREDICTION_DEFAULT_V1",
        "start": GOLDEN_REQUEST_START, "end": GOLDEN_REQUEST_END,
        "requested_timing_precision": "DATE_RANGE", "traditions": [],
        "dasha_profiles": list(CHARA_PROFILES),
        "include_alternatives": True, "include_conflicts": True, "notes": "",
    }
    args.update(overrides)
    return PredictionRequest(**args)
