"""
Phase 8 — immutable versioned PredictionProfiles (§34) + 6E catalogue
integration (§§39–40).

Profiles declare traditions, event rules, dasha/transit systems, and the
convergence/conflict/uncertainty/window policies. Catalogue helpers admit
only ACTIVE, valid-version, applicable rules; deprecated/disabled rules never
participate silently; UNVERIFIED developer rules keep their visible label in
provenance.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import PredictionProfile

DEFAULT_PROFILE_ID = "PREDICTION_DEFAULT_V1"


def _profile(profile_id: str, version: str, traditions: List[str],
             events: List[str], dasha: List[str]) -> PredictionProfile:
    return PredictionProfile(
        profile_id=profile_id, version=version, traditions=traditions,
        event_rules=events, dasha_systems=dasha,
        transit_systems=["CANONICAL_TRANSIT"],
        convergence_policy={"strong_threshold": 4},
        conflict_policy={"mode": "PROPAGATE"},
        uncertainty_policy={"missing_is_negative": False},
        window_policy={"default_precision": "DASHA_RANGE",
                       "allow_union_on_disjoint": True})


PROFILES: Dict[str, PredictionProfile] = {
    DEFAULT_PROFILE_ID: _profile(
        DEFAULT_PROFILE_ID, "1.0.0",
        ["PARASHARI_CLASSICAL", "JAIMINI_CLASSICAL", "TRADITION_DEPENDENT",
         "MODERN_COMMON", "CUSTOM_DEVELOPER"],
        ["EV.MARRIAGE.V1", "EV.RELATIONSHIP.V1", "EV.WEALTH.V1",
         "EV.CAREER.V1", "EV.EDUCATION.V1", "EV.HEALTH.V1", "EV.CUSTOM.V1"],
        ["VIMSHOTTARI", "CHARA"]),
    "PREDICTION_PARASHARI_V1": _profile(
        "PREDICTION_PARASHARI_V1", "1.0.0", ["PARASHARI_CLASSICAL"],
        ["EV.WEALTH.V1", "EV.CAREER.V1", "EV.EDUCATION.V1"],
        ["VIMSHOTTARI"]),
    "PREDICTION_JAIMINI_V1": _profile(
        "PREDICTION_JAIMINI_V1", "1.0.0", ["JAIMINI_CLASSICAL"],
        ["EV.MARRIAGE.V1", "EV.RELATIONSHIP.V1"],
        ["CHARA"]),
}


def get_prediction_profile(profile_id: str) -> PredictionProfile:
    profile = PROFILES.get(profile_id)
    if profile is None:
        raise KeyError(f"Unknown prediction profile {profile_id!r}")
    return profile


def list_prediction_profiles() -> List[PredictionProfile]:
    return [PROFILES[key] for key in sorted(PROFILES)]


def eligible_rule_outcomes(outcomes: List[Any], traditions: List[str]) -> List[Any]:
    """Admit only ACTIVE-lifecycle outcomes within profile traditions. (§39)"""
    eligible = []
    for outcome in outcomes:
        lifecycle = outcome.get("lifecycle", "ACTIVE")
        if lifecycle not in ("ACTIVE", "ENABLED"):
            continue
        tradition = outcome.get("tradition", "")
        if traditions and tradition not in traditions:
            continue
        eligible.append(outcome)
    return eligible


def rejected_rule_outcomes(outcomes: List[Any], traditions: List[str]) -> List[Dict[str, Any]]:
    """Deprecated/disabled/mismatched outcomes, listed explicitly, never silent."""
    rejected = []
    for outcome in outcomes:
        lifecycle = outcome.get("lifecycle", "ACTIVE")
        tradition = outcome.get("tradition", "")
        if lifecycle not in ("ACTIVE", "ENABLED"):
            rejected.append({"rule_id": outcome.get("rule_id", ""),
                             "reason": f"lifecycle {lifecycle}"})
        elif traditions and tradition not in traditions:
            rejected.append({"rule_id": outcome.get("rule_id", ""),
                             "reason": f"tradition {tradition} outside profile"})
    return sorted(rejected, key=lambda r: r["rule_id"])


def developer_rule_flags(outcomes: List[Any]) -> Dict[str, str]:
    """Visible USER_SUPPLIED/CUSTOM labels preserved into provenance. (§40)

    Classical UNVERIFIED provenance is a separate state and is never
    mislabeled as developer-supplied.
    """
    flags = {}
    for outcome in outcomes:
        verification = outcome.get("verification", "")
        if verification in ("USER_SUPPLIED", "CUSTOM"):
            flags[outcome.get("rule_id", "")] = verification
    return flags
