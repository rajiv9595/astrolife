"""
Astrolife V2 — Phase 5A: Deterministic Astrology Rule Engine Foundation

Package exports for the rule engine.
"""
from .enums import (
    RuleCategory, RuleTradition, RuleStatus,
    FormationStatus, StrengthStatus, ActivationStatus,
    CancellationStatus, MitigationStatus, ConfidenceLevel,
    SourceType, EvidenceType, LogicalOperator
)

from .models import (
    Provenance, RuleMetadata, Evidence, ActivationRule,
    CancellationRule, MitigationRule, Condition, RuleDefinition,
    RuleResult, RuleContextModel, EvaluationResult,
    ConditionEvaluationResult, RuleEvaluationTrace
)

from .context import RuleContext, PlanetPosition, HouseInfo

from .conditions import (
    BaseCondition, PrimitiveCondition, ConditionRegistry,
    AllOf, AnyOf, Not,
    PlanetInSign, PlanetInHouse, PlanetInKendra, PlanetInTrikona,
    PlanetInDusthana, PlanetOwnsHouse, PlanetExalted, PlanetDebilitated,
    PlanetInOwnSign, PlanetInMoolatrikona, PlanetsConjunct,
    PlanetAspectsPlanet, PlanetAspectsHouse, LordOfHouseInHouse,
    LordsConjunct, LordsMutuallyConnected, ExchangeOfSigns,
    BeneficPlanet, MaleficPlanet, FunctionalBenefic, FunctionalMalefic,
    Yogakaraka, StrongPlanet, WeakPlanet, PlanetInVargaSign,
    PlanetAboveStrengthThreshold, PlanetBelowStrengthThreshold,
    condition_to_dict
)

from .registry import RuleRegistry, RegistryEntry, get_registry, set_registry

from .evaluator import RuleEvaluator, EvaluationConfig, create_default_evaluator

from .evidence import EvidenceBuilder, format_evidence_for_display, format_evidence_for_json, EvidenceValidator

from .activation import (
    ActivationEvaluator, DefaultActivationEvaluator,
    DashaActivationEvaluator, TransitActivationEvaluator,
    PanchangaActivationEvaluator, CombinedActivationEvaluator
)

from .cancellation import (
    CancellationEvaluator, DefaultCancellationEvaluator,
    NeechaBhangaCancellationEvaluator, KemadrumaCancellationEvaluator,
    ManglikCancellationEvaluator, RajaYogaCancellationEvaluator
)

from .mitigation import (
    MitigationEvaluator, DefaultMitigationEvaluator,
    BeneficAssociationMitigationEvaluator, DignityMitigationEvaluator,
    HousePositionMitigationEvaluator, VargaMitigationEvaluator,
    CombinedMitigationEvaluator
)

from .provenance import (
    ProvenanceRecord, ProvenanceRegistry, ClassicalSource,
    create_provenance_from_rule, validate_provenance, format_provenance_for_display
)

from .validators import (
    ValidationError, ValidationWarning,
    validate_rule_id, validate_rule_version, validate_rule_metadata,
    validate_rule_definition, validate_registry_integrity,
    validate_condition_compatibility, validate_all_rules
)

from .demo_rules import (
    populate_demo_rules, get_demo_rules, create_demo_raja_yoga_9_10,
    create_demo_gaja_kesari, create_demo_yogakaraka, create_demo_ruchaka
)

__all__ = [
    # Enums
    "RuleCategory", "RuleTradition", "RuleStatus",
    "FormationStatus", "StrengthStatus", "ActivationStatus",
    "CancellationStatus", "MitigationStatus", "ConfidenceLevel",
    "SourceType", "EvidenceType", "LogicalOperator",
    
    # Models
    "Provenance", "RuleMetadata", "Evidence", "ActivationRule",
    "CancellationRule", "MitigationRule", "Condition", "RuleDefinition",
    "RuleResult", "RuleContextModel", "EvaluationResult",
    "ConditionEvaluationResult", "RuleEvaluationTrace",
    
    # Context
    "RuleContext", "PlanetPosition", "HouseInfo",
    
    # Conditions
    "BaseCondition", "PrimitiveCondition", "ConditionRegistry",
    "AllOf", "AnyOf", "Not",
    "PlanetInSign", "PlanetInHouse", "PlanetInKendra", "PlanetInTrikona",
    "PlanetInDusthana", "PlanetOwnsHouse", "PlanetExalted", "PlanetDebilitated",
    "PlanetInOwnSign", "PlanetInMoolatrikona", "PlanetsConjunct",
    "PlanetAspectsPlanet", "PlanetAspectsHouse", "LordOfHouseInHouse",
    "LordsConjunct", "LordsMutuallyConnected", "ExchangeOfSigns",
    "BeneficPlanet", "MaleficPlanet", "FunctionalBenefic", "FunctionalMalefic",
    "Yogakaraka", "StrongPlanet", "WeakPlanet", "PlanetInVargaSign",
    "PlanetAboveStrengthThreshold", "PlanetBelowStrengthThreshold",
    "condition_to_dict",
    
    # Registry
    "RuleRegistry", "RegistryEntry", "get_registry", "set_registry",
    
    # Evaluator
    "RuleEvaluator", "EvaluationConfig", "create_default_evaluator",
    
    # Evidence
    "EvidenceBuilder", "format_evidence_for_display", "format_evidence_for_json", "EvidenceValidator",
    
    # Activation
    "ActivationEvaluator", "DefaultActivationEvaluator",
    "DashaActivationEvaluator", "TransitActivationEvaluator",
    "PanchangaActivationEvaluator", "CombinedActivationEvaluator",
    
    # Cancellation
    "CancellationEvaluator", "DefaultCancellationEvaluator",
    "NeechaBhangaCancellationEvaluator", "KemadrumaCancellationEvaluator",
    "ManglikCancellationEvaluator", "RajaYogaCancellationEvaluator",
    
    # Mitigation
    "MitigationEvaluator", "DefaultMitigationEvaluator",
    "BeneficAssociationMitigationEvaluator", "DignityMitigationEvaluator",
    "HousePositionMitigationEvaluator", "VargaMitigationEvaluator",
    "CombinedMitigationEvaluator",
    
    # Provenance
    "ProvenanceRecord", "ProvenanceRegistry", "ClassicalSource",
    "create_provenance_from_rule", "validate_provenance", "format_provenance_for_display",
    
    # Validators
    "ValidationError", "ValidationWarning",
    "validate_rule_id", "validate_rule_version", "validate_rule_metadata",
    "validate_rule_definition", "validate_registry_integrity",
    "validate_condition_compatibility", "validate_all_rules",

    # Demo Rules
    "populate_demo_rules", "get_demo_rules", "create_demo_raja_yoga_9_10",
    "create_demo_gaja_kesari", "create_demo_yogakaraka", "create_demo_ruchaka",
]

__version__ = "5.0.0"