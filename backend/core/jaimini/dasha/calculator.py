"""
Phase 5G — Dasha calculator: birth anchor, mahadashas, antardashas, dates.
Calendar conversion is explicit profile arithmetic (days_per_year, half-open
boundaries); tz-aware datetimes only.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .models import JaiminiDashaPeriod, JaiminiDashaResult
from .profile import JaiminiDashaProfile, UnsupportedDashaMethodError
from .sequence import FORWARD, REVERSE, direction_for_start_sign, full_cycle, step
from .profile import JaiminiDashaProfile
from .duration import duration_for_sign, planet_sign_map_from


def parse_birth_utc(chart_facts: Any) -> datetime:
    raw = chart_facts.time.utc_datetime
    iso = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def calculate_starting_sign(chart_facts: Any, profile: JaiminiDashaProfile) -> Dict[str, Any]:
    sign = chart_facts.ascendant.sign.name
    return {
        "input_fact": "ChartFacts.ascendant.sign",
        "derived_value": sign,
        "selected_profile": profile.method,
        "reason": "LAGNA_START: mahadasha 1 begins at the Ascendant sign",
        "final_sign": sign,
    }


def _build_antars(parent: JaiminiDashaPeriod, direction: str,
                  profile: JaiminiDashaProfile) -> List[JaiminiDashaPeriod]:
    child_years = parent.duration_years / 12.0
    child_days = parent.duration_days / 12.0
    start = datetime.fromisoformat(parent.start_utc_iso.replace("Z", "+00:00"))
    seq: List[str] = [parent.sign]
    cur = parent.sign
    for _ in range(11):
        cur = step(cur, direction)
        seq.append(cur)
    out: List[JaiminiDashaPeriod] = []
    for j, sign in enumerate(seq):
        c_start = start + timedelta(days=child_days * j)
        c_end = start + timedelta(days=child_days * (j + 1))
        out.append(JaiminiDashaPeriod(
            period_id=f"{profile.method}:A{j + 1}:{sign}:of:{parent.period_id}",
            profile_method=profile.method, level="ANTARDASHA", sign=sign,
            sequence_index=j + 1, direction=direction,
            previous_sign=seq[j - 1] if j > 0 else None,
            next_sign=seq[j + 1] if j < 11 else None,
            start_utc_iso=to_iso(c_start), end_utc_iso=to_iso(c_end),
            duration_years=child_years, duration_days=child_days,
            parent_id=parent.period_id, index_in_parent=j + 1,
            duration_evidence=None,
        ))
    # Clamp final child end exactly to parent end (float hygiene).
    out[-1].end_utc_iso = parent.end_utc_iso
    return out


def calculate_jaimini_dasha(
    chart_facts: Any,
    jaimini_facts: Optional[Any],
    profile: Optional[JaiminiDashaProfile] = None,
) -> JaiminiDashaResult:
    """Top-level 5G calculation. jaimini_facts accepted for forward
    compatibility (profile-compatibility checks) but periods derive from
    canonical D1 signs/lords only."""
    if profile is None:
        profile = JaiminiDashaProfile()
    profile.require_supported()

    if jaimini_facts is not None:
        co_lord = getattr(getattr(jaimini_facts, "profile", None), "co_lord_method", None)
        co_val = getattr(co_lord, "value", co_lord)
        if co_val is not None and co_val != "SINGLE_LORD_CLASSICAL":
            raise UnsupportedDashaMethodError(
                f"Duration lordship requires SINGLE_LORD_CLASSICAL, got {co_val}."
            )

    start_ev = calculate_starting_sign(chart_facts, profile)
    start_sign: str = start_ev["final_sign"]
    direction = direction_for_start_sign(profile, start_sign)
    pmap = planet_sign_map_from(chart_facts)
    for need in ("Mars", "Venus", "Mercury", "Moon", "Sun", "Jupiter", "Saturn"):
        if need not in pmap:
            return unknown_dasha_result(profile, [f"planet:{need} (lord sign unavailable)"])

    birth = parse_birth_utc(chart_facts)
    seq = full_cycle(start_sign, direction)
    periods: List[JaiminiDashaPeriod] = []
    cursor = birth
    for i, sign in enumerate(seq):
        dur = duration_for_sign(sign, pmap, direction)
        days = dur.duration_years * profile.days_per_year
        end = cursor + timedelta(days=days)
        periods.append(JaiminiDashaPeriod(
            period_id=f"{profile.method}:M{i + 1}:{sign}",
            profile_method=profile.method, level="MAHA_DASHA", sign=sign,
            sequence_index=i + 1, direction=direction,
            previous_sign=seq[i - 1] if i > 0 else None,
            next_sign=seq[i + 1] if i < 11 else None,
            start_utc_iso=to_iso(cursor), end_utc_iso=to_iso(end),
            duration_years=dur.duration_years, duration_days=days,
            parent_id=None, index_in_parent=None,
            duration_evidence=dur,
        ))
        cursor = end

    for parent in periods:
        parent.antardashas = _build_antars(parent, direction, profile)

    total = sum(p.duration_years for p in periods)
    return JaiminiDashaResult(
        profile_method=profile.method, status="COMPUTED",
        starting_sign=start_sign, direction=direction,
        birth_utc_iso=to_iso(birth), total_years=total, periods=periods,
        starting_sign_evidence=start_ev,
        validation={},
        provenance={
            "tradition": "JAIMINI",
            "method": profile.method,
            "source_reference": profile.source_reference,
            "confidence": profile.confidence,
            "notes": "Dasha period facts only; no timing or outcome claims.",
        },
    )


def unknown_dasha_result(profile: JaiminiDashaProfile, missing: List[str]) -> JaiminiDashaResult:
    return JaiminiDashaResult(
        profile_method=profile.method, status="UNKNOWN",
        starting_sign="", direction="", birth_utc_iso="", total_years=0.0,
        periods=[], starting_sign_evidence={},
        validation={"missing_inputs": sorted(missing)},
        provenance={
            "tradition": "JAIMINI", "method": profile.method,
            "source_reference": profile.source_reference,
            "confidence": profile.confidence,
            "notes": f"UNKNOWN: required input(s) unavailable — missing {sorted(missing)}.",
        },
    )
