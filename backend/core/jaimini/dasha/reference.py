"""
Phase 5G-H — Independent Reference Implementation for Chara Dasha.

Pure Python, zero imports from production modules. Re-derives all calculations
from profile specifications using local sign tables only.

This module exists SOLELY for cross-validation. It must never be imported
by production code.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Literal, Any
from dataclasses import dataclass, field
from copy import deepcopy

# ============================================================
# Local Sign Tables (no external dependencies)
# ============================================================

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_TO_IDX = {s: i for i, s in enumerate(SIGNS)}

CLASSICAL_SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}

SIGN_TYPES = {
    "Aries": "Movable", "Taurus": "Fixed", "Gemini": "Dual",
    "Cancer": "Movable", "Leo": "Fixed", "Virgo": "Dual",
    "Libra": "Movable", "Scorpio": "Fixed", "Sagittarius": "Dual",
    "Capricorn": "Movable", "Aquarius": "Fixed", "Pisces": "Dual",
}

# Odd/Even footed (direct/indirect) - Convention B
ODD_FOOTED_DIRECT = {"Aries", "Taurus", "Gemini", "Libra", "Scorpio", "Sagittarius"}
EVEN_FOOTED_INDIRECT = {"Cancer", "Leo", "Virgo", "Capricorn", "Aquarius", "Pisces"}


# ============================================================
# Direction Rules
# ============================================================

def direction_convention_a(start_sign: str) -> str:
    """
    Convention A: Movable/Fixed/Dual Parity
    Movable -> FORWARD, Fixed -> REVERSE, Dual -> odd=FORWARD, even=REVERSE
    """
    stype = SIGN_TYPES[start_sign]
    if stype == "Movable":
        return "FORWARD"
    if stype == "Fixed":
        return "REVERSE"
    # Dual: odd-numbered in zodiac (1-indexed) = FORWARD
    num = SIGN_TO_IDX[start_sign] + 1
    return "FORWARD" if num % 2 == 1 else "REVERSE"


def direction_convention_b(start_sign: str) -> str:
    """
    Convention B: Odd/Even Footed (Direct/Indirect)
    Odd-footed (Direct) -> FORWARD, Even-footed (Indirect) -> REVERSE
    """
    if start_sign in ODD_FOOTED_DIRECT:
        return "FORWARD"
    if start_sign in EVEN_FOOTED_INDIRECT:
        return "REVERSE"
    raise ValueError(f"Unknown sign: {start_sign}")


def direction_convention_c(start_sign: str) -> str:
    """
    Convention C: Movable/Fixed/Dual (Dual always FORWARD)
    """
    stype = SIGN_TYPES[start_sign]
    if stype == "Movable":
        return "FORWARD"
    if stype == "Fixed":
        return "REVERSE"
    return "FORWARD"  # Dual always forward


# ============================================================
# Sequence Generation
# ============================================================

def step(sign: str, direction: str, n: int = 1) -> str:
    """Move n signs in direction from sign."""
    idx = SIGN_TO_IDX[sign]
    delta = n if direction == "FORWARD" else -n
    return SIGNS[(idx + delta) % 12]


def full_cycle(start_sign: str, direction: str) -> List[str]:
    """All 12 signs exactly once from start_sign in direction."""
    seq = [start_sign]
    cur = start_sign
    for _ in range(11):
        cur = step(cur, direction)
        seq.append(cur)
    return seq


def get_direction(profile: str, start_sign: str) -> str:
    """Get direction for a profile and start sign."""
    if profile == "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL":
        return direction_convention_a(start_sign)
    elif profile == "CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED":
        return direction_convention_b(start_sign)
    elif profile == "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS":
        return direction_convention_c(start_sign)
    else:
        raise ValueError(f"Unknown profile: {profile}")


# ============================================================
# Duration Calculation
# ============================================================

def inclusive_distance(from_sign: str, to_sign: str, direction: str) -> int:
    """Inclusive house count from from_sign to to_sign in direction."""
    a, b = SIGN_TO_IDX[from_sign], SIGN_TO_IDX[to_sign]
    if direction == "FORWARD":
        return ((b - a) % 12) + 1
    return ((a - b) % 12) + 1


@dataclass
class RefDurationEvidence:
    reference_sign: str
    lord: str
    lord_sign: str
    distance_houses: int
    direction: str
    exception: str
    duration_years: float


def duration_for_sign(
    period_sign: str,
    planet_sign_map: Dict[str, str],
    direction: str,
    co_lord_method: str = "SINGLE_CLASSICAL"
) -> RefDurationEvidence:
    """
    Calculate duration for a period sign.
    
    Args:
        period_sign: The sign whose dasha period we're calculating
        planet_sign_map: Dict mapping planet -> sign (e.g., {"Mars": "Aries"})
        direction: "FORWARD" or "REVERSE"
        co_lord_method: "SINGLE_CLASSICAL" or "CO_LORD_STRONGER" (not fully implemented)
    """
    if co_lord_method != "SINGLE_CLASSICAL":
        raise NotImplementedError(f"Co-lord method {co_lord_method} not in reference")
    
    lord = CLASSICAL_SIGN_LORDS[period_sign]
    lord_sign = planet_sign_map.get(lord)
    
    if lord_sign is None:
        raise ValueError(f"Lord {lord} of {period_sign} not found in planet_sign_map")
    
    if lord_sign == period_sign:
        # Own sign exception
        return RefDurationEvidence(
            reference_sign=period_sign,
            lord=lord,
            lord_sign=lord_sign,
            distance_houses=1,
            direction=direction,
            exception="OWN_SIGN_TWELVE",
            duration_years=12.0
        )
    
    dist = inclusive_distance(period_sign, lord_sign, direction)
    return RefDurationEvidence(
        reference_sign=period_sign,
        lord=lord,
        lord_sign=lord_sign,
        distance_houses=dist,
        direction=direction,
        exception="NONE",
        duration_years=float(dist)
    )


# ============================================================
# Antardasha Calculation
# ============================================================

@dataclass
class RefAntardasha:
    sign: str
    duration_years: float
    start_offset_years: float
    end_offset_years: float


def antardashas_equal_12(parent_sign: str, parent_duration: float, direction: str) -> List[RefAntardasha]:
    """
    Convention: 12 equal antardashas from parent sign in sequence direction.
    """
    seq = full_cycle(parent_sign, direction)
    each = parent_duration / 12.0
    result = []
    for i, sign in enumerate(seq):
        result.append(RefAntardasha(
            sign=sign,
            duration_years=each,
            start_offset_years=i * each,
            end_offset_years=(i + 1) * each
        ))
    return result


def antardashas_proportional(
    parent_sign: str, 
    parent_duration: float, 
    direction: str,
    mahadasha_durations: Dict[str, float]
) -> List[RefAntardasha]:
    """
    Convention: Antardasha durations proportional to mahadasha sign durations.
    Each antardasha gets: parent_duration * (sign_mahadasha_duration / total_cycle)
    """
    seq = full_cycle(parent_sign, direction)
    total_cycle = sum(mahadasha_durations.values())
    result = []
    offset = 0.0
    for sign in seq:
        dur = parent_duration * (mahadasha_durations[sign] / total_cycle)
        result.append(RefAntardasha(
            sign=sign,
            duration_years=dur,
            start_offset_years=offset,
            end_offset_years=offset + dur
        ))
        offset += dur
    return result


# ============================================================
# Complete Dasha Calculation
# ============================================================

@dataclass
class RefPeriod:
    period_id: str
    sign: str
    duration_years: float
    duration_evidence: RefDurationEvidence
    start_offset_years: float
    end_offset_years: float
    antardashas: List[RefAntardasha] = field(default_factory=list)


@dataclass
class RefDashaResult:
    profile: str
    starting_sign: str
    direction: str
    periods: List[RefPeriod]
    total_years: float
    status: str = "COMPUTED"
    birth_anchor_offset: float = 0.0  # NO_BIRTH_BALANCE = 0


def calculate_chara_dasha_reference(
    ascendant_sign: str,
    planet_sign_map: Dict[str, str],
    profile: str,
    antardasha_method: str = "TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT",
    co_lord_method: str = "SINGLE_CLASSICAL",
    birth_balance: str = "NO_BIRTH_BALANCE",
    days_per_year: float = 365.25
) -> RefDashaResult:
    """
    Independent reference calculation for Chara Dasha.
    
    Args:
        ascendant_sign: Starting sign (Lagna)
        planet_sign_map: Dict[planet, sign] for all 7 classical planets + Rahu/Ketu
        profile: Profile identifier
        antardasha_method: Antardasha convention
        co_lord_method: Co-lord handling
        birth_balance: Birth balance convention
        days_per_year: Calendar conversion
    
    Returns:
        RefDashaResult with all periods, durations, antardashas
    """
    # 1. Get direction
    direction = get_direction(profile, ascendant_sign)
    
    # 2. Full cycle sequence
    sequence = full_cycle(ascendant_sign, direction)
    
    # 3. Calculate mahadasha durations
    periods = []
    offset = 0.0
    mahadasha_durations = {}
    
    for i, sign in enumerate(sequence):
        ev = duration_for_sign(sign, planet_sign_map, direction, co_lord_method)
        dur = ev.duration_years
        mahadasha_durations[sign] = dur
        
        period = RefPeriod(
            period_id=f"{sign}_MD",
            sign=sign,
            duration_years=dur,
            duration_evidence=ev,
            start_offset_years=offset,
            end_offset_years=offset + dur
        )
        periods.append(period)
        offset += dur
    
    total_years = offset
    
    # 4. Calculate antardashas
    for period in periods:
        if antardasha_method == "TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT":
            period.antardashas = antardashas_equal_12(
                period.sign, period.duration_years, direction
            )
        elif antardasha_method == "PROPORTIONAL_TO_SIGN_DURATIONS":
            period.antardashas = antardashas_proportional(
                period.sign, period.duration_years, direction, mahadasha_durations
            )
        else:
            raise NotImplementedError(f"Antardasha method {antardasha_method} not in reference")
    
    return RefDashaResult(
        profile=profile,
        starting_sign=ascendant_sign,
        direction=direction,
        periods=periods,
        total_years=total_years,
        status="COMPUTED",
        birth_anchor_offset=0.0 if birth_balance == "NO_BIRTH_BALANCE" else 0.0
    )


# ============================================================
# Validation Helpers
# ============================================================

def validate_ref_result(result: RefDashaResult) -> List[str]:
    """Validate a reference result. Returns list of error messages."""
    errors = []
    
    # Check 12 periods
    if len(result.periods) != 12:
        errors.append(f"Expected 12 periods, got {len(result.periods)}")
    
    # Check all signs present exactly once
    signs = [p.sign for p in result.periods]
    if set(signs) != set(SIGNS):
        errors.append(f"Signs don't cover all 12: {set(SIGNS) - set(signs)}")
    if len(signs) != len(set(signs)):
        errors.append("Duplicate signs in sequence")
    
    # Check sequence order matches direction
    expected_seq = full_cycle(result.starting_sign, result.direction)
    if signs != expected_seq:
        errors.append(f"Sequence mismatch: expected {expected_seq}, got {signs}")
    
    # Check durations match evidence
    for p in result.periods:
        if abs(p.duration_years - p.duration_evidence.duration_years) > 1e-9:
            errors.append(f"Duration mismatch for {p.sign}")
    
    # Check antardashas
    for p in result.periods:
        if len(p.antardashas) != 12:
            errors.append(f"Expected 12 antardashas for {p.sign}, got {len(p.antardashas)}")
        ant_sum = sum(a.duration_years for a in p.antardashas)
        if abs(ant_sum - p.duration_years) > 1e-9:
            errors.append(f"Antardasha sum {ant_sum} != parent {p.duration_years} for {p.sign}")
        # Check containment
        if abs(p.antardashas[0].start_offset_years) > 1e-9:
            errors.append(f"First antardasha doesn't start at 0 for {p.sign}")
        if abs(p.antardashas[-1].end_offset_years - p.duration_years) > 1e-9:
            errors.append(f"Last antardasha doesn't end at parent for {p.sign}")
    
    # Check total
    if abs(result.total_years - sum(p.duration_years for p in result.periods)) > 1e-9:
        errors.append(f"Total years mismatch: {result.total_years}")
    
    return errors


# ============================================================
# Profile Configurations
# ============================================================

PROFILE_CONFIGS = {
    "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL": {
        "direction_rule": "MOVABLE_FORWARD_FIXED_REVERSE_DUAL_PARITY",
        "duration_rule": "INCLUSIVE_LORD_DISTANCE_WITH_OWN_SIGN_TWELVE",
        "antardasha_rule": "TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT",
        "co_lord_rule": "SINGLE_CLASSICAL",
        "birth_balance": "NO_BIRTH_BALANCE",
        "year_model": "MEAN_JULIAN_YEAR",
        "days_per_year": 365.25,
        "source_reference": "UNVERIFIED",
        "confidence": "TRADITION_DEPENDENT",
        "direction_fn": direction_convention_a,
    },
    "CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED": {
        "direction_rule": "ODD_FOOTED_FORWARD_EVEN_FOOTED_REVERSE",
        "duration_rule": "INCLUSIVE_LORD_DISTANCE_WITH_OWN_SIGN_TWELVE",
        "antardasha_rule": "TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT",
        "co_lord_rule": "SINGLE_CLASSICAL",
        "birth_balance": "NO_BIRTH_BALANCE",
        "year_model": "MEAN_JULIAN_YEAR",
        "days_per_year": 365.25,
        "source_reference": "UNVERIFIED",
        "confidence": "TRADITION_DEPENDENT",
        "direction_fn": direction_convention_b,
    },
    "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS": {
        "direction_rule": "MOVABLE_FORWARD_FIXED_REVERSE_DUAL_FORWARD",
        "duration_rule": "INCLUSIVE_LORD_DISTANCE_WITH_OWN_SIGN_TWELVE",
        "antardasha_rule": "TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT",
        "co_lord_rule": "SINGLE_CLASSICAL",
        "birth_balance": "NO_BIRTH_BALANCE",
        "year_model": "MEAN_JULIAN_YEAR",
        "days_per_year": 365.25,
        "source_reference": "UNVERIFIED",
        "confidence": "TRADITION_DEPENDENT",
        "direction_fn": direction_convention_c,
    },
}


def get_profile_config(profile: str) -> Dict:
    if profile not in PROFILE_CONFIGS:
        raise ValueError(f"Unknown profile: {profile}")
    return deepcopy(PROFILE_CONFIGS[profile])


# ============================================================
# CLI / Test Entry Point
# ============================================================

if __name__ == "__main__":
    # Quick self-test
    print("=== Independent Reference Self-Test ===\n")
    
    # Golden chart planet positions
    golden_planets = {
        "Sun": "Leo",
        "Moon": "Sagittarius",
        "Mars": "Aries",
        "Mercury": "Cancer",
        "Jupiter": "Virgo",
        "Venus": "Virgo",
        "Saturn": "Cancer",
        "Rahu": "Pisces",
        "Ketu": "Virgo",
    }
    
    for profile_id in PROFILE_CONFIGS:
        print(f"\n--- Profile: {profile_id} ---")
        config = get_profile_config(profile_id)
        result = calculate_chara_dasha_reference(
            ascendant_sign="Taurus",
            planet_sign_map=golden_planets,
            profile=profile_id
        )
        print(f"  Direction: {result.direction}")
        print(f"  Sequence: {result.starting_sign} -> {' -> '.join([p.sign for p in result.periods[1:5]])} ...")
        print(f"  First 3 durations: {[f'{p.duration_years:.1f}' for p in result.periods[:3]]}")
        print(f"  Total cycle: {result.total_years:.1f} years")
        
        errors = validate_ref_result(result)
        if errors:
            print(f"  VALIDATION ERRORS: {errors}")
        else:
            print("  Validation: PASS")
    
    print("\n=== All reference profiles tested ===")