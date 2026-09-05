"""
Core Strength Package - Classical Planetary Strength Engine

Exports:
- Models: All Pydantic models for strength results
- Profile: Configuration profiles and reference data
- Pipeline: Main entry point generate_strength_report()
- Components: Individual Bala calculators
"""
from .models import (
    StrengthClassification,
    StrengthSystem,
    SthanaBala,
    DigBala,
    KalaBala,
    ChestaBala,
    NaisargikaBala,
    DrigBala,
    ShadbalaResult,
    BhavaBalaResult,
    VimsopakaBalaResult,
    AvasthaResult,
    DignityResult,
    FunctionalStrengthResult,
    CompositeStrengthResult,
    StrengthReport,
)

from .profile import (
    StrengthCalculationProfile,
    DEFAULT_STRENGTH_PROFILE,
    EXALTATION_DATA,
    MOOLATRIKONA_DATA,
    NATURAL_FRIENDSHIP,
    DIG_BALA_HOUSES,
    NAISARGIKA_BALA,
    SIGNS,
    get_sign_index,
    normalize_deg,
)

from .shadbala import calculate_shadbala, calculate_all_shadbala
from .bhava_bala import calculate_bhava_bala
from .vimsopaka import calculate_vimsopaka_bala, calculate_all_vimsopaka
from .avastha import calculate_bala_avastha, calculate_jagratadi_avastha, calculate_all_avastha
from .dignity import calculate_dignity, calculate_all_dignities
from .functional import calculate_functional_strength, calculate_all_functional_strength
from .composite import calculate_composite_strength, calculate_all_composite_strength

__all__ = [
    # Enums
    "StrengthClassification",
    "StrengthSystem",
    # Models
    "SthanaBala",
    "DigBala",
    "KalaBala",
    "ChestaBala",
    "NaisargikaBala",
    "DrigBala",
    "ShadbalaResult",
    "BhavaBalaResult",
    "VimsopakaBalaResult",
    "AvasthaResult",
    "DignityResult",
    "FunctionalStrengthResult",
    "CompositeStrengthResult",
    "StrengthReport",
    # Profile
    "StrengthCalculationProfile",
    "DEFAULT_STRENGTH_PROFILE",
    "EXALTATION_DATA",
    "MOOLATRIKONA_DATA",
    "NATURAL_FRIENDSHIP",
    "DIG_BALA_HOUSES",
    "NAISARGIKA_BALA",
    "SIGNS",
    "get_sign_index",
    "normalize_deg",
    # Pipeline functions
    "calculate_shadbala",
    "calculate_all_shadbala",
    "calculate_bhava_bala",
    "calculate_vimsopaka_bala",
    "calculate_all_vimsopaka",
    "calculate_bala_avastha",
    "calculate_jagratadi_avastha",
    "calculate_all_avastha",
    "calculate_dignity",
    "calculate_all_dignities",
    "calculate_functional_strength",
    "calculate_all_functional_strength",
    "calculate_composite_strength",
    "calculate_all_composite_strength",
]