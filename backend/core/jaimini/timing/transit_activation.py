"""
Phase 5H — Transit Activation Engine.

Checks transit conditions against Jaimini mapping requirements to
determine which transit conditions are met during a candidate window.

Uses existing Phase 3/5B transit infrastructure (TransitSnapshot,
TransitEvent, ParashariAspect, WesternAspect, TransitNatalRelation).

All evaluation is deterministic; no interpretation, no probability.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.transit.calculator import TransitSnapshot, _evaluation_jd
from core.transit.events import TransitEvent, detect_transit_events
from core.transit.aspects import (
    compute_parashari_aspects,
    compute_transit_natal_relations,
    ParashariAspect,
    TransitNatalRelation,
)
from core.calculation.config import CalculationProfile, DEFAULT_PROFILE
from core.calculation.models import ChartFacts
from core.jaimini.mappings import ActivationCondition, MappingEntry

from .models import TransitConditionRecord, TemporalWindow


def _parse_iso(iso_str: str) -> datetime:
    """Parse UTC ISO string to tz-aware datetime."""
    if not iso_str:
        return datetime(1900, 1, 1, tzinfo=timezone.utc)
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _sign_of(natal: ChartFacts, planet: str) -> Optional[str]:
    """Get the natal sign of a planet."""
    pdata = natal.planets.get(planet)
    return pdata.sign.name if pdata is not None else None


def _check_transit_relationship(
    transit_planet: str,
    natal_planet: str,
    transits: TransitSnapshot,
    natal: ChartFacts,
    condition_type: str = "conjunction",
    orb: float = 8.0,
) -> Optional[TransitConditionRecord]:
    """Check if a transit-natal relationship is active."""
    t_pos = transits.planets.get(transit_planet)
    n_planet = natal.planets.get(natal_planet)
    if t_pos is None or n_planet is None:
        return None

    n_lon = float(n_planet.longitude.sidereal)
    t_lon = float(t_pos.sidereal_longitude)
    sep = abs((t_lon - n_lon) % 360.0)
    sep = min(sep, 360.0 - sep)

    is_active = False
    exact_type = condition_type

    if condition_type == "conjunction" and sep <= orb:
        is_active = True
        exact_type = "conjunction"
    elif condition_type == "opposition" and abs(sep - 180.0) <= orb:
        is_active = True
        exact_type = "opposition"
    elif condition_type == "same_sign" and t_pos.sign == n_planet.sign.name:
        is_active = True
        exact_type = "same_sign"
    elif condition_type == "aspect":
        is_active = sep <= orb
        exact_type = "aspect"

    if not is_active:
        return None

    cond_id = f"{exact_type}:{transit_planet}:{natal_planet}"
    return TransitConditionRecord(
        condition_id=cond_id,
        condition_type=exact_type,
        transit_planet=transit_planet,
        target=natal_planet,
        exact_time=None,
        window=TemporalWindow(
            start=_parse_iso(transits.evaluation_utc_iso),
            end=_parse_iso(transits.evaluation_utc_iso),
        ),
    )


def _check_rashi_drishti(
    transit_planet: str,
    natal_sign: str,
    transits: TransitSnapshot,
    jaimini_facts: Any,
) -> Optional[TransitConditionRecord]:
    """Check if transit planet's sign casts Rashi Drishti on a natal sign."""
    t_pos = transits.planets.get(transit_planet)
    if t_pos is None:
        return None

    aspects_from_transit_sign = jaimini_facts.rashi_drishti.sign_aspects.get(
        t_pos.sign, []
    )
    if natal_sign in aspects_from_transit_sign:
        cond_id = f"rashi_drishti:{transit_planet}:{natal_sign}"
        return TransitConditionRecord(
            condition_id=cond_id,
            condition_type="rashi_drishti",
            transit_planet=transit_planet,
            target=natal_sign,
            exact_time=None,
            window=TemporalWindow(
                start=_parse_iso(transits.evaluation_utc_iso),
                end=_parse_iso(transits.evaluation_utc_iso),
            ),
        )
    return None


def activate_transits_for_mapping(
    mapping: MappingEntry,
    transits: TransitSnapshot,
    natal: ChartFacts,
    jaimini_facts: Any,
    natal_signs: Optional[Dict[str, str]] = None,
) -> List[TransitConditionRecord]:
    """Check all transit conditions required by a mapping.

    Returns list of met transit conditions (may be empty).
    """
    if natal_signs is None:
        natal_signs = {}
        for pname in natal.planets:
            s = _sign_of(natal, pname)
            if s is not None:
                natal_signs[pname] = s

    conditions: List[TransitConditionRecord] = []
    met_condition_types = set()

    for ac in mapping.activation_conditions:
        if ac == ActivationCondition.TRANSIT_RELATIONSHIP:
            for pname in natal.planets:
                rec = _check_transit_relationship(
                    mapping.transit_requirements.split(":")[-1] if ":" in mapping.transit_requirements else "Sun",
                    pname,
                    transits,
                    natal,
                    "same_sign",
                )
                if rec is not None:
                    conditions.append(rec)
                    met_condition_types.add("transit_relationship")

        elif ac == ActivationCondition.RASHI_DRISHTI:
            for pname, psign in natal_signs.items():
                for tname in transits.planets:
                    rec = _check_rashi_drishti(tname, psign, transits, jaimini_facts)
                    if rec is not None:
                        conditions.append(rec)
                        met_condition_types.add("rashi_drishti")

        elif ac == ActivationCondition.KARAKAMSHA:
            kak_sign = jaimini_facts.karakamsha.karakamsha_sign
            for tname, tpos in transits.planets.items():
                if tpos.sign == kak_sign:
                    cond_id = f"karakamsha_transit:{tname}"
                    conditions.append(TransitConditionRecord(
                        condition_id=cond_id,
                        condition_type="karakamsha_transit",
                        transit_planet=tname,
                        target=kak_sign,
                        exact_time=None,
                        window=TemporalWindow(
                            start=_parse_iso(transits.evaluation_utc_iso),
                            end=_parse_iso(transits.evaluation_utc_iso),
                        ),
                    ))
                    met_condition_types.add("karakamsha")

        elif ac == ActivationCondition.NATAL_SIGN_RELATIONSHIP:
            for pname in natal.planets:
                rec = _check_transit_relationship(
                    "Sun",
                    pname,
                    transits,
                    natal,
                    "same_sign",
                )
                if rec is not None:
                    conditions.append(rec)
                    met_condition_types.add("natal_sign_relationship")

    return conditions


def activate_transits(
    mapping: MappingEntry,
    evaluation_window: TemporalWindow,
    natal: ChartFacts,
    jaimini_facts: Any,
    calc_profile: Optional[CalculationProfile] = None,
    sample_step_days: float = 1.0,
) -> List[TransitConditionRecord]:
    """Evaluate transit conditions across the evaluation window.

    Samples transit positions at sample_step_days intervals and checks
    each mapping activation condition. Returns all met conditions.
    """
    if calc_profile is None:
        calc_profile = DEFAULT_PROFILE

    from datetime import timedelta

    start_dt = evaluation_window.start
    end_dt = evaluation_window.end

    all_conditions: List[TransitConditionRecord] = []
    seen_ids: set = set()

    current = start_dt
    while current <= end_dt:
        transits = _compute_transits_at(current, calc_profile)
        if transits is not None:
            met = activate_transits_for_mapping(
                mapping, transits, natal, jaimini_facts
            )
            for cond in met:
                if cond.condition_id not in seen_ids:
                    all_conditions.append(cond)
                    seen_ids.add(cond.condition_id)
        current = current + timedelta(days=sample_step_days)

    all_conditions.sort(key=lambda c: c.condition_id)
    return all_conditions


def _compute_transits_at(
    dt: datetime,
    calc_profile: CalculationProfile,
) -> Optional[TransitSnapshot]:
    """Compute transit snapshot at a single datetime."""
    try:
        from core.transit.calculator import calculate_transit_positions
        return calculate_transit_positions(dt, calc_profile)
    except Exception:
        return None
