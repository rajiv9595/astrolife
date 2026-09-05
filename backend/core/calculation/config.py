from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, Dict, Union, List

class ZodiacSystem(str, Enum):
    SIDEREAL = "SIDEREAL"
    TROPICAL = "TROPICAL"

class AyanamshaSystem(str, Enum):
    LAHIRI_STANDARD = "LAHIRI_STANDARD"
    # Other systems can be added here later

class NodeSystem(str, Enum):
    MEAN = "MEAN"
    TRUE = "TRUE"

class HouseSystem(str, Enum):
    WHOLE_SIGN = "WHOLE_SIGN"
    # Placidus, Koch, etc. can be added later

class VargaMethod(str, Enum):
    PARASHARI_CLASSICAL = "PARASHARI_CLASSICAL"


class YearModel(str, Enum):
    TROPICAL_YEAR_APPROXIMATION = "TROPICAL_YEAR_APPROXIMATION"
    SIDEREAL_YEAR = "SIDEREAL_YEAR"
    CUSTOM = "CUSTOM"


class DashaCalculationProfile(BaseModel):
    """
    Controls Vimshottari Dasha year-length convention.
    Must be explicit per Phase 3 Step 6 — no silent hard-coded constant.
    Default mirrors legacy ProKerala/JHora convention: 365.2425 days/year
    (Gregorian mean tropical year approximation).
    Alternative traditions use 360 days/year (Savana) or 365.25.
    Expose via profile so tests can vary without code change.
    """
    year_model: YearModel = YearModel.TROPICAL_YEAR_APPROXIMATION
    days_per_year: float = Field(default=365.2425, description="Days per Vimshottari year, default 365.2425 (tropical approx)")
    total_cycle_years: float = Field(default=120.0, description="Total Vimshottari cycle years")


DEFAULT_DASHA_PROFILE = DashaCalculationProfile()


# Western degree aspects vs Parashari aspects separation (Phase 3 Steps 16-17)
class AspectSystem(str, Enum):
    WESTERN_DEGREE_ASPECTS = "WESTERN_DEGREE_ASPECTS"
    PARASHARI_GRAHA_DRISHTI = "PARASHARI_GRAHA_DRISHTI"


class NodeAspectMode(str, Enum):
    NONE = "NONE"
    PARASHARI_5_7_9 = "PARASHARI_5_7_9"
    SAME_AS_JUPITER = "SAME_AS_JUPITER"


class WesternAspectConfig(BaseModel):
    aspect_system: AspectSystem = AspectSystem.WESTERN_DEGREE_ASPECTS
    # orbs in degrees, per aspect
    orbs: Dict[str, float] = Field(default_factory=lambda: {
        "conjunction": 8.0,
        "sextile": 4.0,
        "square": 6.0,
        "trine": 6.0,
        "opposition": 8.0,
    })


class ParashariAspectConfig(BaseModel):
    aspect_system: AspectSystem = AspectSystem.PARASHARI_GRAHA_DRISHTI
    # house offsets (1-indexed) each graha aspects
    # Default per Step 17
    aspects: Dict[str, List[int]] = Field(default_factory=lambda: {
        "Sun": [7],
        "Moon": [7],
        "Mars": [4, 7, 8],
        "Mercury": [7],
        "Jupiter": [5, 7, 9],
        "Venus": [7],
        "Saturn": [3, 7, 10],
    })
    # Rahu/Ketu configurable — default documents convention: no aspects (NONE)
    # Alternative schools give them Jupiter-like 5/7/9; consumer can set.
    node_mode: NodeAspectMode = NodeAspectMode.NONE


class CalculationProfile(BaseModel):
    zodiac: ZodiacSystem = ZodiacSystem.SIDEREAL
    ayanamsha: AyanamshaSystem = AyanamshaSystem.LAHIRI_STANDARD
    node: NodeSystem = NodeSystem.MEAN
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN
    # Varga method: single global default or per-varga override dict
    # Examples:
    #   varga_method = "PARASHARI_CLASSICAL"
    #   varga_method = {"D9": "PARASHARI_CLASSICAL", "D10": "PARASHARI_CLASSICAL"}
    varga_method: Union[VargaMethod, Dict[str, VargaMethod], None] = Field(
        default=VargaMethod.PARASHARI_CLASSICAL,
        description="Global or per-varga Varga calculation method"
    )
    # Legacy alias — if set, merged into varga_method
    varga_methods: Optional[Dict[str, VargaMethod]] = Field(
        default=None,
        description="Deprecated per-varga override, use varga_method dict instead"
    )
    # Phase 3 profiles — additive, not breaking Phase 1/2
    dasha_profile: DashaCalculationProfile = Field(default_factory=DashaCalculationProfile)
    western_aspect_config: WesternAspectConfig = Field(default_factory=WesternAspectConfig)
    parashari_aspect_config: ParashariAspectConfig = Field(default_factory=ParashariAspectConfig)

# The standard profile for Astrolife V2
DEFAULT_PROFILE = CalculationProfile()
