"""
Phase 5G-H — Jaimini Dasha Profiles.

Multiple explicit profiles for competing Chara Dasha traditions.
Traditions are NEVER merged. Each profile fully specifies its conventions.
"""
from __future__ import annotations
from typing import List, Dict, Literal
from enum import Enum

from pydantic import BaseModel, Field


class CharaDashaProfileID(str, Enum):
    """Implemented Chara Dasha profiles with explicit tradition attribution."""
    # Convention A: Movable/Fixed/Dual Parity (current default)
    CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL = (
        "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL"
    )
    # Convention B: Odd/Even Footed (Direct/Indirect) - Classical
    CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED = (
        "CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED"
    )
    # Convention C: Movable/Fixed/Dual (Dual always forward) - Variant
    CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS = (
        "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS"
    )


# All implemented methods (explicit, no implicit defaults)
IMPLEMENTED_METHODS: List[str] = [m.value for m in CharaDashaProfileID]

# For backward compatibility
SUPPORTED_METHODS: List[str] = IMPLEMENTED_METHODS
IMPLEMENTED_METHOD = IMPLEMENTED_METHODS[0]  # Default

# Known-but-unsupported traditions (requesting them raises clear error)
UNSUPPORTED_METHODS: List[str] = [
    "CHARA_DASHA_PAKA_LAGNA_START",
    "CHARA_DASHA_ATMAKARAKA_START",
    "STHIRA_DASHA",
    "NARAYANA_DASHA",
    "BRAHMA_DASHA",
    "MANDOOKA_DASHA",
    "KARAKA_DASHA",
    "SUDASA_DASHA",
]


class UnsupportedDashaMethodError(ValueError):
    """Raised when a non-implemented Jaimini Dasha tradition is requested."""


# Profile metadata registry - each fully specifies its algorithm
PROFILE_REGISTRY: Dict[str, Dict] = {
    CharaDashaProfileID.CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL.value: {
        "dasha_system": "JAIMINI_CHARA",
        "tradition": "JAIMINI",
        "method": CharaDashaProfileID.CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL.value,
        "start_sign_rule": "LAGNA_START",
        "sign_progression_rule": "NATURE_DIRECTION_FROM_START",
        "year_duration_rule": "INCLUSIVE_LORD_DISTANCE_WITH_OWN_SIGN_TWELVE",
        "exception_rule": "OWN_SIGN_TWELVE",
        "subperiod_rule": "TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT",
        "direction_rule": "MOVABLE_FORWARD_FIXED_REVERSE_DUAL_PARITY",
        "direction_description": (
            "Movable (Aries, Cancer, Libra, Capricorn) -> FORWARD; "
            "Fixed (Taurus, Leo, Scorpio, Aquarius) -> REVERSE; "
            "Dual (Gemini, Virgo, Sagittarius, Pisces) -> odd zodiac# FORWARD, even REVERSE"
        ),
        "birth_balance_rule": "NO_BIRTH_BALANCE",
        "year_model": "MEAN_JULIAN_YEAR",
        "days_per_year": 365.25,
        "boundary_convention": "[start, end) half-open — start inclusive, end exclusive",
        "levels": ["MAHA_DASHA", "ANTARDASHA"],
        "source_reference": "UNVERIFIED",
        "confidence": "TRADITION_DEPENDENT",
        "version": "1.0.0",
        "notes": (
            "Convention A: Modern Jaimini texts (K.N. Rao, Sanjay Rath, V.P. Goel). "
            "Aligns with Rashi Drishti movable/fixed/dual classification. "
            "No direct sutra citation established."
        ),
    },
    CharaDashaProfileID.CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED.value: {
        "dasha_system": "JAIMINI_CHARA",
        "tradition": "JAIMINI",
        "method": CharaDashaProfileID.CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED.value,
        "start_sign_rule": "LAGNA_START",
        "sign_progression_rule": "NATURE_DIRECTION_FROM_START",
        "year_duration_rule": "INCLUSIVE_LORD_DISTANCE_WITH_OWN_SIGN_TWELVE",
        "exception_rule": "OWN_SIGN_TWELVE",
        "subperiod_rule": "TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT",
        "direction_rule": "ODD_FOOTED_FORWARD_EVEN_FOOTED_REVERSE",
        "direction_description": (
            "Odd-footed/Direct (Aries, Taurus, Gemini, Libra, Scorpio, Sagittarius) -> FORWARD; "
            "Even-footed/Indirect (Cancer, Leo, Virgo, Capricorn, Aquarius, Pisces) -> REVERSE"
        ),
        "birth_balance_rule": "NO_BIRTH_BALANCE",
        "year_model": "MEAN_JULIAN_YEAR",
        "days_per_year": 365.25,
        "boundary_convention": "[start, end) half-open — start inclusive, end exclusive",
        "levels": ["MAHA_DASHA", "ANTARDASHA"],
        "source_reference": "UNVERIFIED",
        "confidence": "TRADITION_DEPENDENT",
        "version": "1.0.0",
        "notes": (
            "Convention B: Classical commentaries (Bhatta Utpala, Neelakantha, Phaladeepika, "
            "Saravali, Jataka Parijata). 'Pada' (footed) classification distinct from "
            "movable/fixed/dual. Older and more widely attested in classical sources."
        ),
    },
    CharaDashaProfileID.CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS.value: {
        "dasha_system": "JAIMINI_CHARA",
        "tradition": "JAIMINI",
        "method": CharaDashaProfileID.CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS.value,
        "start_sign_rule": "LAGNA_START",
        "sign_progression_rule": "NATURE_DIRECTION_FROM_START",
        "year_duration_rule": "INCLUSIVE_LORD_DISTANCE_WITH_OWN_SIGN_TWELVE",
        "exception_rule": "OWN_SIGN_TWELVE",
        "subperiod_rule": "TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT",
        "direction_rule": "MOVABLE_FORWARD_FIXED_REVERSE_DUAL_FORWARD",
        "direction_description": (
            "Movable -> FORWARD; Fixed -> REVERSE; Dual -> FORWARD (always)"
        ),
        "birth_balance_rule": "NO_BIRTH_BALANCE",
        "year_model": "MEAN_JULIAN_YEAR",
        "days_per_year": 365.25,
        "boundary_convention": "[start, end) half-open — start inclusive, end exclusive",
        "levels": ["MAHA_DASHA", "ANTARDASHA"],
        "source_reference": "UNVERIFIED",
        "confidence": "TRADITION_DEPENDENT",
        "version": "1.0.0",
        "notes": (
            "Convention C: Variant found in some modern practitioners. "
            "Less classically documented than A or B."
        ),
    },
}


class JaiminiDashaProfile(BaseModel):
    """Jaimini Dasha calculation profile - fully specifies algorithm."""
    
    dasha_system: str = Field(default="JAIMINI_CHARA")
    tradition: str = Field(default="JAIMINI")
    method: str = Field(default=CharaDashaProfileID.CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL.value)
    start_sign_rule: str = Field(default="LAGNA_START")
    sign_progression_rule: str = Field(default="NATURE_DIRECTION_FROM_START")
    year_duration_rule: str = Field(default="INCLUSIVE_LORD_DISTANCE_WITH_OWN_SIGN_TWELVE")
    exception_rule: str = Field(default="OWN_SIGN_TWELVE")
    subperiod_rule: str = Field(default="TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT")
    direction_rule: str = Field(default="MOVABLE_FORWARD_FIXED_REVERSE_DUAL_PARITY")
    direction_description: str = Field(default="")
    birth_balance_rule: str = Field(default="NO_BIRTH_BALANCE")
    year_model: str = Field(default="MEAN_JULIAN_YEAR")
    days_per_year: float = Field(default=365.25)
    boundary_convention: str = Field(default="[start, end) half-open — start inclusive, end exclusive")
    levels: List[str] = Field(default_factory=lambda: ["MAHA_DASHA", "ANTARDASHA"])
    source_reference: str = Field(default="UNVERIFIED")
    confidence: str = Field(default="TRADITION_DEPENDENT")
    version: str = Field(default="1.0.0")
    notes: str = Field(default="")

    @classmethod
    def from_method(cls, method: str) -> "JaiminiDashaProfile":
        """Create profile from method ID. Raises if unsupported."""
        if method not in IMPLEMENTED_METHODS:
            if method in UNSUPPORTED_METHODS:
                raise UnsupportedDashaMethodError(
                    f"Dasha method '{method}' is known but not implemented. "
                    f"Implemented: {IMPLEMENTED_METHODS}. "
                    f"Traditions are never merged or silently substituted."
                )
            raise UnsupportedDashaMethodError(
                f"Dasha method '{method}' is not recognized. "
                f"Implemented: {IMPLEMENTED_METHODS}. "
                f"Known-but-unsupported: {UNSUPPORTED_METHODS}."
            )
        
        config = PROFILE_REGISTRY[method]
        return cls(**config)

    def require_supported(self) -> None:
        """Validate this profile is implemented."""
        if self.method not in IMPLEMENTED_METHODS:
            raise UnsupportedDashaMethodError(
                f"Dasha method '{self.method}' is not implemented. "
                f"Supported: {IMPLEMENTED_METHODS}."
            )


def direction_for_start_sign(profile: JaiminiDashaProfile, start_sign: str) -> str:
    """Get direction for a start sign under the given profile."""
    direction_rule = profile.direction_rule
    
    if direction_rule == "MOVABLE_FORWARD_FIXED_REVERSE_DUAL_PARITY":
        return _direction_convention_a(start_sign)
    elif direction_rule == "ODD_FOOTED_FORWARD_EVEN_FOOTED_REVERSE":
        return _direction_convention_b(start_sign)
    elif direction_rule == "MOVABLE_FORWARD_FIXED_REVERSE_DUAL_FORWARD":
        return _direction_convention_c(start_sign)
    else:
        raise ValueError(f"Unknown direction_rule: {direction_rule}")


# Local sign tables (no external dependency)
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_TYPES = {
    "Aries": "Movable", "Taurus": "Fixed", "Gemini": "Dual",
    "Cancer": "Movable", "Leo": "Fixed", "Virgo": "Dual",
    "Libra": "Movable", "Scorpio": "Fixed", "Sagittarius": "Dual",
    "Capricorn": "Movable", "Aquarius": "Fixed", "Pisces": "Dual",
}

ODD_FOOTED_DIRECT = {"Aries", "Taurus", "Gemini", "Libra", "Scorpio", "Sagittarius"}
EVEN_FOOTED_INDIRECT = {"Cancer", "Leo", "Virgo", "Capricorn", "Aquarius", "Pisces"}


def _direction_convention_a(start_sign: str) -> str:
    """Convention A: Movable/Fixed/Dual Parity."""
    stype = SIGN_TYPES[start_sign]
    if stype == "Movable":
        return "FORWARD"
    if stype == "Fixed":
        return "REVERSE"
    num = SIGNS.index(start_sign) + 1
    return "FORWARD" if num % 2 == 1 else "REVERSE"


def _direction_convention_b(start_sign: str) -> str:
    """Convention B: Odd/Even Footed (Direct/Indirect)."""
    if start_sign in ODD_FOOTED_DIRECT:
        return "FORWARD"
    if start_sign in EVEN_FOOTED_INDIRECT:
        return "REVERSE"
    raise ValueError(f"Unknown sign: {start_sign}")


def _direction_convention_c(start_sign: str) -> str:
    """Convention C: Movable/Fixed/Dual (Dual always FORWARD)."""
    stype = SIGN_TYPES[start_sign]
    if stype == "Movable":
        return "FORWARD"
    if stype == "Fixed":
        return "REVERSE"
    return "FORWARD"


def full_cycle(start_sign: str, direction: str) -> List[str]:
    """All 12 signs exactly once from start_sign in direction."""
    seq = [start_sign]
    cur = start_sign
    for _ in range(11):
        cur = step(cur, direction)
        seq.append(cur)
    return seq


def step(sign: str, direction: str, n: int = 1) -> str:
    idx = SIGNS.index(sign)
    delta = n if direction == "FORWARD" else -n
    return SIGNS[(idx + delta) % 12]