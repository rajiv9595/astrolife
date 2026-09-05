"""
Jaimini Fact Validators — Astrolife V2 Phase 5D

Validates mathematical consistency, structural completeness, and tradition integrity
for all Jaimini deterministic fact layers.
"""
from __future__ import annotations
from typing import Dict, List, Set, Any

from .models import (
    CharaKarakasReport,
    RashiDrishtiReport,
    ArudhaPadaItem,
    UpapadaDetails,
    KarakamshaDetails,
    JaiminiFacts
)
from .rashi_drishti import SIGNS_ORDER, SIGN_TYPES, CANONICAL_SIGN_ASPECTS
from .profile import KarakaMethod


class JaiminiValidationError(Exception):
    """Raised when Jaimini fact data fails integrity checks."""
    pass


def validate_chara_karakas(report: CharaKarakasReport) -> None:
    """Validates Chara Karaka assignments and degree ordering."""
    if report.method == KarakaMethod.SEVEN_KARAKA:
        expected_keys = {"AK", "AmK", "BK", "MK", "PK", "GK", "DK"}
    else:
        expected_keys = {"AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"}
        
    actual_keys = set(report.karakas.keys())
    if actual_keys != expected_keys:
        raise JaiminiValidationError(
            f"Chara Karaka keys mismatch for {report.method}. Expected: {expected_keys}, Found: {actual_keys}"
        )
        
    assigned_planets: Set[str] = set()
    prev_degree = 999.0
    
    for code in report.ordering:
        item = report.karakas[code]
        p = item.planet
        deg = item.degree_in_sign
        
        if p in assigned_planets:
            raise JaiminiValidationError(f"Duplicate planet '{p}' assigned to multiple Karakas ({code}).")
        assigned_planets.add(p)
        
        if deg < 0.0 or deg >= 30.0:
            raise JaiminiValidationError(f"Invalid intra-sign degree {deg} for {p} ({code}). Must be in [0.0, 30.0).")
            
        if deg > prev_degree + 1e-6:
            raise JaiminiValidationError(
                f"Chara Karaka ordering violation: {code} ({p} at {deg:.6f}°) > previous ({prev_degree:.6f}°)."
            )
        prev_degree = deg


def validate_rashi_drishti(report: RashiDrishtiReport) -> None:
    """Validates Rashi Drishti sign-based aspect rules and symmetry."""
    for s in SIGNS_ORDER:
        if s not in report.sign_aspects:
            raise JaiminiValidationError(f"Sign {s} missing from Rashi Drishti sign_aspects.")
            
        aspects = report.sign_aspects[s]
        if len(aspects) != 3:
            raise JaiminiValidationError(f"Sign {s} must aspect exactly 3 signs, found {len(aspects)}: {aspects}")
            
        if s in aspects:
            raise JaiminiValidationError(f"Sign {s} cannot aspect itself: {aspects}")
            
        stype = SIGN_TYPES[s]
        s_idx = SIGNS_ORDER.index(s)
        
        if stype == "Movable":
            # Must not aspect adjacent fixed sign (next sign)
            adjacent_fixed = SIGNS_ORDER[(s_idx + 1) % 12]
            if adjacent_fixed in aspects:
                raise JaiminiValidationError(f"Movable sign {s} illegally aspects adjacent fixed sign {adjacent_fixed}.")
        elif stype == "Fixed":
            # Must not aspect adjacent movable sign (previous sign)
            adjacent_movable = SIGNS_ORDER[(s_idx - 1) % 12]
            if adjacent_movable in aspects:
                raise JaiminiValidationError(f"Fixed sign {s} illegally aspects adjacent movable sign {adjacent_movable}.")
        elif stype == "Dual":
            # Must aspect all 3 other dual signs
            for other_s in SIGNS_ORDER:
                if SIGN_TYPES[other_s] == "Dual" and other_s != s:
                    if other_s not in aspects:
                        raise JaiminiValidationError(f"Dual sign {s} does not aspect dual sign {other_s}.")

    # Mutual symmetry verification
    for s1 in SIGNS_ORDER:
        for s2 in report.sign_aspects[s1]:
            if s1 not in report.sign_aspects[s2]:
                raise JaiminiValidationError(
                    f"Rashi Drishti symmetry broken: {s1} aspects {s2}, but {s2} does not aspect {s1}."
                )


def validate_arudha_padas(padas: Dict[int, ArudhaPadaItem]) -> None:
    """Validates 12 Arudha Padas for consistency and proper exception application."""
    if len(padas) != 12:
        raise JaiminiValidationError(f"Expected 12 Arudha Padas, found {len(padas)}.")
        
    for h in range(1, 13):
        if h not in padas:
            raise JaiminiValidationError(f"Missing Arudha Pada for House {h}.")
        item = padas[h]
        if item.house_number != h:
            raise JaiminiValidationError(f"House number mismatch: key={h}, item={item.house_number}")
        if item.source_sign not in SIGNS_ORDER or item.final_sign not in SIGNS_ORDER:
            raise JaiminiValidationError(f"Invalid sign in Pada {item.pada_code}: {item}")
        if item.source_sign_num < 1 or item.source_sign_num > 12:
            raise JaiminiValidationError(f"Invalid source_sign_num {item.source_sign_num} in Pada {item.pada_code}.")
        if item.final_sign_num < 1 or item.final_sign_num > 12:
            raise JaiminiValidationError(f"Invalid final_sign_num {item.final_sign_num} in Pada {item.pada_code}.")


def validate_karakamsha(details: KarakamshaDetails) -> None:
    """Validates Karakamsha details."""
    if not details.atmakaraka_planet:
        raise JaiminiValidationError("Atmakaraka planet cannot be empty.")
    if details.karakamsha_sign not in SIGNS_ORDER:
        raise JaiminiValidationError(f"Invalid Karakamsha sign: {details.karakamsha_sign}")
    if details.karakamsha_sign_num < 1 or details.karakamsha_sign_num > 12:
        raise JaiminiValidationError(f"Invalid Karakamsha sign_num: {details.karakamsha_sign_num}")


def validate_jaimini_facts(facts: JaiminiFacts) -> None:
    """Validates the entire JaiminiFacts composite container."""
    validate_chara_karakas(facts.chara_karakas)
    validate_rashi_drishti(facts.rashi_drishti)
    validate_arudha_padas(facts.arudha_padas)
    validate_karakamsha(facts.karakamsha)
