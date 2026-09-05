from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from enum import Enum


class StrengthClassification(str, Enum):
    CLASSICAL = "CLASSICAL"
    TRADITION_DEPENDENT = "TRADITION_DEPENDENT"
    CUSTOM = "CUSTOM"
    APPROXIMATION = "APPROXIMATION"


class StrengthSystem(str, Enum):
    PARASHARI_SHADBALA = "PARASHARI_SHADBALA"
    BHava_BALA = "BHAVA_BALA"
    VIMSOPAKA = "VIMSOPAKA"
    AVASTHA = "AVASTHA"
    PARASHARI_DIGNITY = "PARASHARI_DIGNITY"
    PARASHARI_FUNCTIONAL = "PARASHARI_FUNCTIONAL"
    ASTROLIFE_COMPOSITE = "ASTROLIFE_COMPOSITE"


class SthanaBalaComponent(BaseModel):
    name: str
    value: float
    maximum: float
    unit: str = "virupas"
    description: str = ""
    classification: StrengthClassification = StrengthClassification.CLASSICAL


class SthanaBala(BaseModel):
    uchcha_bala: Optional[SthanaBalaComponent] = None
    saptavargaja_bala: Optional[SthanaBalaComponent] = None
    ojhayugma_bala: Optional[SthanaBalaComponent] = None
    kendradi_bala: Optional[SthanaBalaComponent] = None
    drekkana_bala: Optional[SthanaBalaComponent] = None
    total: float = 0.0
    maximum: float = 0.0
    unit: str = "virupas"
    components: List[SthanaBalaComponent] = Field(default_factory=list)


class DigBala(BaseModel):
    value: float
    maximum: float = 60.0
    unit: str = "virupas"
    ideal_house: int
    actual_house: int
    angular_distance: float
    classification: StrengthClassification = StrengthClassification.CLASSICAL
    description: str = ""


class KalaBalaComponent(BaseModel):
    name: str
    value: float
    maximum: float
    unit: str = "virupas"
    description: str = ""
    classification: StrengthClassification = StrengthClassification.CLASSICAL


class KalaBala(BaseModel):
    nathonnatha_bala: Optional[KalaBalaComponent] = None
    paksha_bala: Optional[KalaBalaComponent] = None
    tribhaga_bala: Optional[KalaBalaComponent] = None
    varsha_bala: Optional[KalaBalaComponent] = None
    masa_bala: Optional[KalaBalaComponent] = None
    dina_bala: Optional[KalaBalaComponent] = None
    hora_bala: Optional[KalaBalaComponent] = None
    ayana_bala: Optional[KalaBalaComponent] = None
    yuddha_bala: Optional[KalaBalaComponent] = None
    total: float = 0.0
    maximum: float = 0.0
    unit: str = "virupas"
    components: List[KalaBalaComponent] = Field(default_factory=list)


class ChestaBala(BaseModel):
    value: float
    maximum: float = 60.0
    unit: str = "virupas"
    speed: float
    is_retrograde: bool
    method: str = "PARASHARI"
    classification: StrengthClassification = StrengthClassification.CLASSICAL
    description: str = ""


class NaisargikaBala(BaseModel):
    value: float
    maximum: float = 60.0
    unit: str = "virupas"
    traditional_value: float
    classification: StrengthClassification = StrengthClassification.CLASSICAL
    description: str = ""


class DrigBala(BaseModel):
    value: float
    maximum: float = 60.0
    unit: str = "virupas"
    benefic_aspect_strength: float = 0.0
    malefic_aspect_strength: float = 0.0
    aspect_details: List[Dict] = Field(default_factory=list)
    classification: StrengthClassification = StrengthClassification.CLASSICAL
    description: str = ""


class ShadbalaResult(BaseModel):
    planet: str
    system: StrengthSystem = StrengthSystem.PARASHARI_SHADBALA
    method: str = "PARASHARI_CLASSICAL"
    classification: StrengthClassification = StrengthClassification.CLASSICAL

    sthana_bala: SthanaBala
    dig_bala: DigBala
    kala_bala: KalaBala
    chesta_bala: ChestaBala
    naisargika_bala: NaisargikaBala
    drig_bala: DrigBala

    total_virupas: float
    total_rupas: float
    minimum_rupas: Optional[float] = None
    ratio: Optional[float] = None
    strength_status: Optional[str] = None

    metadata: Dict = Field(default_factory=dict)


class BhavaBalaResult(BaseModel):
    house: int
    sign: str
    system: StrengthSystem = StrengthSystem.BHava_BALA
    method: str = "PARASHARI_CLASSICAL"
    classification: StrengthClassification = StrengthClassification.CLASSICAL

    bhavadhipati_bala: Optional[float] = None
    dig_bala: Optional[float] = None
    drishti_bala: Optional[float] = None
    other_components: Dict = Field(default_factory=dict)
    total: float = 0.0
    maximum: float = 0.0
    unit: str = "virupas"


class VimsopakaBalaResult(BaseModel):
    planet: str
    system: StrengthSystem = StrengthSystem.VIMSOPAKA
    method: str = "PARASHARI_CLASSICAL"
    classification: StrengthClassification = StrengthClassification.TRADITION_DEPENDENT

    score: float
    maximum: float = 20.0
    ratio: float
    varga_contributions: List[Dict] = Field(default_factory=dict)
    vargas_used: List[int] = Field(default_factory=list)
    weights: Dict = Field(default_factory=dict)


class AvasthaResult(BaseModel):
    planet: str
    system: StrengthSystem = StrengthSystem.AVASTHA
    method: str = "PARASHARI_BALA_AVASTHA"
    classification: StrengthClassification = StrengthClassification.CLASSICAL

    avastha_name: str
    avastha_index: int
    degree_range: str
    description: str = ""


class DignityResult(BaseModel):
    planet: str
    sign: str
    system: StrengthSystem = StrengthSystem.PARASHARI_DIGNITY
    method: str = "PARASHARI_CLASSICAL"
    classification: StrengthClassification = StrengthClassification.CLASSICAL

    dignity: str
    ruler: str
    relationship: str
    is_exalted: bool = False
    is_debilitated: bool = False
    is_own_sign: bool = False
    is_moolatrikona: bool = False
    moolatrikona_range: Optional[str] = None


class FunctionalStrengthResult(BaseModel):
    planet: str
    system: StrengthSystem = StrengthSystem.PARASHARI_FUNCTIONAL
    method: str = "PARASHARI_CLASSICAL"
    classification: StrengthClassification = StrengthClassification.TRADITION_DEPENDENT

    lordship: Dict = Field(default_factory=dict)
    yogakaraka: bool = False
    functional_nature: str = ""
    kendra_trikona: bool = False
    dusthana_lord: bool = False
    maraka: bool = False
    score: float = 0.0
    details: List[str] = Field(default_factory=list)


class CompositeStrengthResult(BaseModel):
    planet: str
    system: StrengthSystem = StrengthSystem.ASTROLIFE_COMPOSITE
    method: str = "ASTROLIFE_CUSTOM"
    classification: StrengthClassification = StrengthClassification.CUSTOM

    score: float
    label: str
    nature: str
    reasons: List[str] = Field(default_factory=list)
    components: Dict = Field(default_factory=dict)
    disclaimer: str = "This is a custom Astrolife composite score, not a classical Shadbala calculation."


class StrengthReport(BaseModel):
    calculation_profile: Dict
    planets: Dict[str, ShadbalaResult]
    bhava_bala: Dict[int, BhavaBalaResult] = Field(default_factory=dict)
    vimsopaka: Dict[str, VimsopakaBalaResult] = Field(default_factory=dict)
    avastha: Dict[str, Dict[str, AvasthaResult]] = Field(default_factory=dict)
    dignity: Dict[str, DignityResult] = Field(default_factory=dict)
    functional_strength: Dict[str, FunctionalStrengthResult] = Field(default_factory=dict)
    composite: Dict[str, CompositeStrengthResult] = Field(default_factory=dict)
    metadata: Dict = Field(default_factory=dict)