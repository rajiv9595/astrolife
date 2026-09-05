"""
Jaimini Calculation Profile — Astrolife V2 Phase 5D

Declares configuration profile and traditions for Jaimini Fact calculations.
Never silently assumes all Jaimini traditions agree.
"""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class KarakaMethod(str, Enum):
    """Method for computing Chara Karakas."""
    SEVEN_KARAKA = "SEVEN_KARAKA"   # Classical 7 Karakas: Sun, Moon, Mars, Mer, Jup, Ven, Sat
    EIGHT_KARAKA = "EIGHT_KARAKA"   # 8 Karakas: includes Rahu, Pitrukaraka inserted


class RahuKarakaMethod(str, Enum):
    """How Rahu's degree is measured when included in Karaka calculation."""
    EXCLUDED = "EXCLUDED"                       # Rahu not included (standard 7-karaka)
    DIRECT_LONGITUDE = "DIRECT_LONGITUDE"       # lon % 30 (direct intra-sign degree)
    INVERSE_LONGITUDE = "INVERSE_LONGITUDE"     # 30 - (lon % 30) (reverse intra-sign degree for retrograde motion)


class RashiDrishtiMethod(str, Enum):
    """Method for Sign-Based Aspects (Rashi Drishti)."""
    JAIMINI_CLASSICAL = "JAIMINI_CLASSICAL"     # Movable aspects Fixed except adjacent; Fixed aspects Movable except adjacent; Dual aspects other Dual


class ArudhaMethod(str, Enum):
    """Method for calculating Arudha Padas."""
    PARASHARI_JAIMINI_STANDARD = "PARASHARI_JAIMINI_STANDARD"  # Distance projection with 10th-house exception for 1st/7th falls
    NO_EXCEPTIONS = "NO_EXCEPTIONS"                            # Pure 2x projection without exception rules (for research/synthetic)


class UpapadaMethod(str, Enum):
    """Method for calculating Upapada Lagna (UL / A12)."""
    UPAPADA_12TH_HOUSE = "UPAPADA_12TH_HOUSE"   # Arudha of the 12th house


class CoLordMethod(str, Enum):
    """Handling of dual lordships (Scorpio: Mars/Ketu; Aquarius: Saturn/Rahu)."""
    SINGLE_LORD_CLASSICAL = "SINGLE_LORD_CLASSICAL"   # Mars rules Scorpio, Saturn rules Aquarius
    CO_LORD_STRONGER = "CO_LORD_STRONGER"             # Select stronger co-lord (documented tradition)


class JaiminiCalculationProfile(BaseModel):
    """
    Dedicated profile for all Jaimini deterministic fact calculations.
    """
    karaka_method: KarakaMethod = Field(
        default=KarakaMethod.SEVEN_KARAKA,
        description="7 or 8 Chara Karaka scheme"
    )
    rahu_karaka_method: RahuKarakaMethod = Field(
        default=RahuKarakaMethod.EXCLUDED,
        description="Convention for Rahu degree in sign if included"
    )
    rashi_drishti_method: RashiDrishtiMethod = Field(
        default=RashiDrishtiMethod.JAIMINI_CLASSICAL,
        description="Rashi Drishti sign aspect tradition"
    )
    arudha_method: ArudhaMethod = Field(
        default=ArudhaMethod.PARASHARI_JAIMINI_STANDARD,
        description="Arudha Pada calculation method and exception rules"
    )
    upapada_method: UpapadaMethod = Field(
        default=UpapadaMethod.UPAPADA_12TH_HOUSE,
        description="Upapada derivation source"
    )
    co_lord_method: CoLordMethod = Field(
        default=CoLordMethod.SINGLE_LORD_CLASSICAL,
        description="Lord selection for dual lordship signs"
    )
    float_tolerance: float = Field(
        default=1e-7,
        description="Epsilon tolerance for planetary intra-sign degree equality check"
    )
    source_tradition: str = Field(
        default="Jaimini Sutras / Brihat Parasara Hora Shastra",
        description="Lineage authority label (unverified against exact verses)"
    )
    source_reference: str = Field(
        default="UNVERIFIED",
        description="Exact textual reference verification status (UNVERIFIED unless verses genuinely checked)"
    )
    version: str = Field(
        default="2.0.0",
        description="Engine implementation version"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Auxiliary profile parameters"
    )
