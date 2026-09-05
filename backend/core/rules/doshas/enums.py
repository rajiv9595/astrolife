"""
Dosha Engine Enums — Astrolife V2 Phase 5C

Extended enums for dosha-specific classifications beyond the
base RuleCategory/DOSHA in enums.py.
"""
from enum import Enum


class DoshaCategory(str, Enum):
    """High-level dosha classification"""
    MARRIAGE = "MARRIAGE"
    FINANCIAL = "FINANCIAL"
    HEALTH = "HEALTH"
    ANCESTRAL = "ANCESTRAL"
    KARMIC = "KARMIC"
    GENERAL = "GENERAL"


class DoshaSeverity(str, Enum):
    """Categorical severity — no numerical scoring without validated formula"""
    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class DoshaFormationStatus(str, Enum):
    """Whether the dosha has formed"""
    NOT_FORMED = "NOT_FORMED"
    FORMED = "FORMED"
    PARTIAL = "PARTIAL"
    UNCERTAIN = "UNCERTAIN"


class DoshaCancellationStatus(str, Enum):
    """Cancellation state — independent of formation"""
    NONE = "NONE"
    PARTIAL = "PARTIAL"
    FULL = "FULL"


class DoshaMitigationStatus(str, Enum):
    """Mitigation state — independent of cancellation"""
    NONE = "NONE"
    PARTIAL = "PARTIAL"
    SIGNIFICANT = "SIGNIFICANT"


class DoshaActivationStatus(str, Enum):
    """Activation state — independent of all above"""
    NOT_EVALUATED = "NOT_EVALUATED"
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    PARTIALLY_ACTIVE = "PARTIALLY_ACTIVE"


class DoshaTradition(str, Enum):
    """Tradition classification for source attribution"""
    PARASHARI_CLASSICAL = "PARASHARI_CLASSICAL"
    TRADITION_DEPENDENT = "TRADITION_DEPENDENT"
    MODERN_PRACTICE = "MODERN_PRACTICE"
    SECONDARY = "SECONDARY"
    CUSTOM = "CUSTOM"
    UNVERIFIED = "UNVERIFIED"


class DoshaConfidence(str, Enum):
    """Confidence level for dosha implementation"""
    VERIFIED = "VERIFIED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    TRADITION_DEPENDENT = "TRADITION_DEPENDENT"
    EXPERIMENTAL = "EXPERIMENTAL"
    UNVERIFIED = "UNVERIFIED"
    CUSTOM = "CUSTOM"


class DoshaSourceType(str, Enum):
    """Source classification"""
    CLASSICAL_TEXT = "CLASSICAL_TEXT"
    SECONDARY_REFERENCE = "SECONDARY_REFERENCE"
    TRADITIONAL_PRACTICE = "TRADITIONAL_PRACTICE"
    INTERNAL = "INTERNAL"
    UNVERIFIED = "UNVERIFIED"


class ManglikReferencePoint(str, Enum):
    """Reference points for Manglik dosha evaluation"""
    LAGNA = "LAGNA"
    MOON = "MOON"
    VENUS = "VENUS"


class KalaSarpaMethod(str, Enum):
    """Method variants for Kala Sarpa evaluation"""
    SIGN_BASED = "SIGN_BASED"
    DEGREE_BASED = "DEGREE_BASED"
