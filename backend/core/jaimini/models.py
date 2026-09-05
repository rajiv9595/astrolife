"""
Jaimini Data Models — Astrolife V2 Phase 5D

Pure deterministic mathematical and structural models for Jaimini calculations.
Contains no predictions, no AI logic, and no interpretations.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .profile import JaiminiCalculationProfile, KarakaMethod, RahuKarakaMethod, RashiDrishtiMethod, ArudhaMethod


# ---------------------------------------------------------------------------
# Chara Karakas Models
# ---------------------------------------------------------------------------

class KarakaItem(BaseModel):
    """Single Chara Karaka assignment."""
    karaka_name: str = Field(description="Full name, e.g. 'Atmakaraka'")
    karaka_code: str = Field(description="Abbreviation, e.g. 'AK'")
    planet: str = Field(description="Assigned planet name, e.g. 'Moon'")
    degree_in_sign: float = Field(description="Intra-sign degree 0.0-30.0")
    formatted_degree: str = Field(description="Human-readable deg min sec, e.g. '17° 51\\' 46\\\"'")
    sign: str = Field(description="D1 Sign occupied by planet")
    sign_num: int = Field(description="D1 Sign number 1-12")
    house: int = Field(description="D1 House occupied by planet 1-12")
    rank: int = Field(description="1-indexed ranking by intra-sign longitude")


class CharaKarakasReport(BaseModel):
    """Complete Chara Karaka report for a chart."""
    method: KarakaMethod
    rahu_method: RahuKarakaMethod
    karakas: Dict[str, KarakaItem] = Field(description="Keyed by Karaka code (AK, AmK, BK, MK, PK, GK, DK, PiK)")
    ordering: List[str] = Field(description="List of Karaka codes in descending order of intra-sign degree")
    planet_to_karaka: Dict[str, str] = Field(description="Map of planet name to Karaka code")
    candidate_degrees: Dict[str, float] = Field(description="Evaluated intra-sign degrees for all candidate planets")
    evidence: List[str] = Field(default_factory=list, description="Step-by-step mathematical derivation")


# ---------------------------------------------------------------------------
# Rashi Drishti (Sign Aspects) Models
# ---------------------------------------------------------------------------

class RashiDrishtiSignItem(BaseModel):
    """Rashi Drishti properties for a single sign."""
    sign_name: str
    sign_num: int
    sign_type: str = Field(description="'Movable', 'Fixed', or 'Dual'")
    aspected_signs: List[str] = Field(description="List of 3 aspected signs")
    non_aspected_signs: List[str] = Field(description="List of 8 non-aspected signs (excluding self)")
    planets_in_sign: List[str] = Field(default_factory=list, description="Planets situated in this sign")
    aspected_planets: List[str] = Field(default_factory=list, description="Planets situated in aspected signs")


class RashiDrishtiReport(BaseModel):
    """Complete Rashi Drishti sign-based aspect relationships."""
    method: RashiDrishtiMethod
    sign_aspects: Dict[str, List[str]] = Field(description="Sign -> List of aspected sign names")
    planet_aspects: Dict[str, List[str]] = Field(description="Planet -> List of aspected sign names (via occupied sign)")
    planets_aspected_by_sign: Dict[str, List[str]] = Field(description="Sign -> List of planets in aspected signs")
    planets_aspected_by_planet: Dict[str, List[str]] = Field(description="Planet -> List of planets in aspected signs")
    evidence: List[str] = Field(default_factory=list, description="Step-by-step sign aspect derivation")


# ---------------------------------------------------------------------------
# Arudha Pada & Upapada Models
# ---------------------------------------------------------------------------

class ArudhaPadaItem(BaseModel):
    """Single Arudha Pada calculation for a house."""
    house_number: int = Field(description="House number 1-12")
    pada_code: str = Field(description="e.g. 'A1', 'A2' ... 'A12', 'AL', 'UL'")
    traditional_name: str = Field(description="Traditional Sanskrit name, e.g. 'Arudha Lagna', 'Upapada Lagna'")
    source_sign: str = Field(description="Sign of the house in D1")
    source_sign_num: int = Field(description="1-12")
    house_lord: str = Field(description="Planet ruling the source house")
    lord_sign: str = Field(description="Sign occupied by the house lord in D1")
    lord_sign_num: int = Field(description="1-12")
    distance_signs: int = Field(description="Distance in signs from house to lord (0-11)")
    raw_projected_sign: str = Field(description="Sign reached before applying classical exceptions")
    raw_projected_sign_num: int = Field(description="1-12")
    exception_applied: Optional[str] = Field(default=None, description="Details of exception rule applied, if any")
    final_sign: str = Field(description="Final Arudha Pada sign")
    final_sign_num: int = Field(description="1-12")
    evidence: List[str] = Field(default_factory=list, description="Step-by-step derivation")


class UpapadaDetails(BaseModel):
    """Dedicated Upapada Lagna (UL / Gauna Pada / A12) representation."""
    source_house: int = Field(default=12, description="Derived from 12th house")
    source_sign: str
    source_sign_num: int
    lord: str
    lord_sign: str
    lord_sign_num: int
    distance_signs: int
    raw_projected_sign: str
    raw_projected_sign_num: int
    exception_applied: Optional[str] = None
    final_sign: str
    final_sign_num: int
    evidence: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Karakamsha & Swamsa Models
# ---------------------------------------------------------------------------

class KarakamshaDetails(BaseModel):
    """Deterministic Karakamsha & Swamsa fact representation."""
    atmakaraka_planet: str = Field(description="Identified Atmakaraka (AK)")
    atmakaraka_d1_sign: str = Field(description="AK sign in D1 Rashi")
    atmakaraka_d1_degree: float = Field(description="AK degree in D1 Rashi (0-30)")
    karakamsha_sign: str = Field(description="Sign occupied by AK in D9 Navamsha")
    karakamsha_sign_num: int = Field(description="D9 Sign number 1-12 of AK")
    karakamsha_navamsha_degree: float = Field(description="Degree of AK within D9 sign")
    swamsa_navamsha_lagna_sign: str = Field(description="D9 Navamsha Lagna (Ascendant sign in D9)")
    swamsa_navamsha_lagna_sign_num: int = Field(description="D9 Lagna sign number 1-12")
    evidence: List[str] = Field(default_factory=list, description="Derivation evidence")


# ---------------------------------------------------------------------------
# Provenance & Master Jaimini Facts Container
# ---------------------------------------------------------------------------

class JaiminiProvenance(BaseModel):
    """Metadata and classical source citations for Jaimini computations."""
    tradition: str = "JAIMINI"
    method: str = "CLASSICAL_ARUDHA_STANDARD"
    source_texts: List[str] = Field(default_factory=lambda: [
        "Jaimini Upadesha Sutras",
        "Brihat Parashara Hora Shastra"
    ])
    source_reference: str = "UNVERIFIED"
    version: str = "2.0.0"
    confidence: str = "UNVERIFIED"
    notes: str = "Pure deterministic mathematical and structural facts; zero prediction. Exact verse references unverified."


class JaiminiFacts(BaseModel):
    """
    Master container for all Jaimini deterministic facts.
    Independent layer cleanly segregated from Parashari facts and rules.
    """
    profile: JaiminiCalculationProfile
    chara_karakas: CharaKarakasReport
    rashi_drishti: RashiDrishtiReport
    arudha_padas: Dict[int, ArudhaPadaItem] = Field(description="Arudha Padas A1 through A12 keyed by house number 1-12")
    arudha_lagna: ArudhaPadaItem = Field(description="Arudha Lagna (AL / A1)")
    upapada: UpapadaDetails = Field(description="Upapada Lagna (UL / A12)")
    karakamsha: KarakamshaDetails = Field(description="Karakamsha & Swamsa facts")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Unified evidence collection")
    provenance: JaiminiProvenance = Field(default_factory=JaiminiProvenance)
    metadata: Dict[str, Any] = Field(default_factory=dict)
