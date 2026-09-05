"""
Demo Rules — Astrolife V2 Phase 5A

Simple demonstration rules to prove the engine architecture works.
These are NOT the full yoga catalogue - just structural proofs.

Uses Pydantic Condition model format for serializable rule definitions.
"""
from .models import (
    RuleDefinition, RuleMetadata, Provenance, ActivationRule,
    CancellationRule, MitigationRule, Condition
)
from .enums import (
    RuleCategory, RuleTradition, RuleStatus, ConfidenceLevel,
    SourceType, EvidenceType, LogicalOperator
)
from .provenance import ClassicalSource


def _cond(condition_type: str, params: dict, condition_id: str = None, operator: LogicalOperator = LogicalOperator.AND, negated: bool = False, children: list = None) -> Condition:
    """Helper to create a Condition model"""
    return Condition(
        type=condition_type,
        params=params,
        operator=operator,
        children=children or [],
        negated=negated
    )


def _all_of(condition_id: str, conditions: list) -> Condition:
    """Create an AND group condition"""
    return Condition(
        type="all_of",
        params={"condition_id": condition_id},
        operator=LogicalOperator.AND,
        children=conditions
    )


def _any_of(condition_id: str, conditions: list) -> Condition:
    """Create an OR group condition"""
    return Condition(
        type="any_of",
        params={"condition_id": condition_id},
        operator=LogicalOperator.OR,
        children=conditions
    )


def _not(condition: Condition) -> Condition:
    """Create a NOT condition"""
    condition.negated = not condition.negated
    return condition


# ==================== Demo Rule 1: Dharma Karmadhipati Yoga ====================

def create_demo_raja_yoga_9_10() -> RuleDefinition:
    """
    Demo: Dharma Karmadhipati Yoga (9th and 10th lords connected)
    
    This demonstrates:
    - Formation: 9th and 10th lords mutually connected
    - Strength: Both lords well-placed
    - Activation: 9th or 10th lord in Dasha
    - Cancellation: Either lord in Dusthana
    - Mitigation: Benefic aspect on lords
    """
    
    metadata = RuleMetadata(
        rule_id="PARASHARI.YOGA.DHARMA_KARMADHIPATI",
        rule_version="1.0.0",
        name="Dharma Karmadhipati Yoga",
        category=RuleCategory.YOGA,
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        school_method="Parashari Classical",
        status=RuleStatus.ENABLED,
        description="Conjunction, aspect, or exchange between 9th and 10th lords. Highest Raja Yoga for career and duty.",
        provenance=Provenance(
            source_type=SourceType.CLASSICAL_TEXT,
            source_name=ClassicalSource.BPHS.value,
            source_reference="BPHS Ch. 41, Vs. 33-34",
            tradition=RuleTradition.PARASHARI_CLASSICAL,
            method="Parashari Classical",
            implementation_version="1.0.0",
            notes="Classical Raja Yoga formation"
        ),
        confidence=ConfidenceLevel.VERIFIED,
        tags=["raja_yoga", "career", "9th_lord", "10th_lord"],
        enabled=True
    )
    
    # Formation: 9th and 10th lords connected
    formation = _all_of("formation_dk", [
        _cond("lords_mutually_connected", {"house1": 9, "house2": 10, "condition_id": "lords_connected_9_10"})
    ])
    
    # Strength: Both lords in good dignity or Kendra/Trikona
    strength = _all_of("strength_dk", [
        _any_of("lord9_strong", [
            _cond("planet_exalted", {"planet": "Jupiter", "condition_id": "jup_exalted"}),
            _cond("planet_in_own_sign", {"planet": "Jupiter", "condition_id": "jup_own"}),
            _cond("planet_in_kendra", {"planet": "Jupiter", "condition_id": "jup_kendra"}),
            _cond("planet_in_trikona", {"planet": "Jupiter", "condition_id": "jup_trikona"}),
        ]),
        _any_of("lord10_strong", [
            _cond("planet_exalted", {"planet": "Saturn", "condition_id": "sat_exalted"}),
            _cond("planet_in_own_sign", {"planet": "Saturn", "condition_id": "sat_own"}),
            _cond("planet_in_kendra", {"planet": "Saturn", "condition_id": "sat_kendra"}),
            _cond("planet_in_trikona", {"planet": "Saturn", "condition_id": "sat_trikona"}),
        ])
    ])
    
    # Activation: 9th or 10th lord in Dasha
    activation_rules = [
        ActivationRule(
            rule_id="activation_dk_dasha",
            description="9th or 10th lord active in Dasha",
            evaluator="default_activation"
        )
    ]
    
    # Cancellation: Either lord in Dusthana or combust
    cancellation_rules = [
        CancellationRule(
            rule_id="cancellation_dk_dusthana",
            description="9th or 10th lord in Dusthana",
            evaluator="default_cancellation",
            is_partial=True
        )
    ]
    
    # Mitigation: Benefic aspect on lords
    mitigation_rules = [
        MitigationRule(
            rule_id="mitigation_dk_benefic",
            description="Benefic aspect on 9th/10th lords",
            evaluator="default_mitigation",
            strength_impact="partial"
        )
    ]
    
    return RuleDefinition(
        metadata=metadata,
        formation_conditions=[formation],
        strength_conditions=[strength],
        activation_rules=activation_rules,
        cancellation_rules=cancellation_rules,
        mitigation_rules=mitigation_rules,
        required_evidence=[
            EvidenceType.LORDSHIP_RELATIONSHIP,
            EvidenceType.PLANET_DIGNITY,
            EvidenceType.DASHA_PERIOD
        ]
    )


# ==================== Demo Rule 2: Gaja Kesari Yoga ====================

def create_demo_gaja_kesari() -> RuleDefinition:
    """
    Demo: Gaja Kesari Yoga (Jupiter in Kendra from Moon)
    
    Demonstrates simple Kendra-from-Moon condition.
    """
    
    metadata = RuleMetadata(
        rule_id="PARASHARI.YOGA.GAJA_KESARI",
        rule_version="1.0.0",
        name="Gaja Kesari Yoga",
        category=RuleCategory.YOGA,
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        school_method="Parashari Classical",
        status=RuleStatus.ENABLED,
        description="Jupiter in Kendra (1, 4, 7, 10) from Moon. Brings fame, virtue, reputation, and wealth.",
        provenance=Provenance(
            source_type=SourceType.CLASSICAL_TEXT,
            source_name=ClassicalSource.BPHS.value,
            source_reference="BPHS Ch. 36, Vs. 1-2",
            tradition=RuleTradition.PARASHARI_CLASSICAL,
            method="Parashari Classical",
            implementation_version="1.0.0"
        ),
        confidence=ConfidenceLevel.VERIFIED,
        tags=["wealth", "fame", "jupiter", "moon", "kendra"],
        enabled=True
    )
    
    # Formation: Jupiter in Kendra from Moon
    # Note: Using available condition types - planet_in_kendra + moon_strong
    formation = _all_of("formation_gk", [
        _cond("planet_in_kendra", {"planet": "Jupiter", "condition_id": "jup_in_kendra"}),
        # Additional: Moon should be well-placed
        _any_of("moon_strong", [
            _cond("planet_exalted", {"planet": "Moon", "condition_id": "moon_exalted"}),
            _cond("planet_in_own_sign", {"planet": "Moon", "condition_id": "moon_own"}),
            _cond("planet_in_kendra", {"planet": "Moon", "condition_id": "moon_kendra"}),
        ])
    ])
    
    # Strength: Jupiter and Moon both strong
    strength = _all_of("strength_gk", [
        _cond("planet_exalted", {"planet": "Jupiter", "condition_id": "jup_exalted_str"}),
        _cond("planet_exalted", {"planet": "Moon", "condition_id": "moon_exalted_str"}),
    ])
    
    return RuleDefinition(
        metadata=metadata,
        formation_conditions=[formation],
        strength_conditions=[strength],
        required_evidence=[
            EvidenceType.KENDRA_TRIKONA,
            EvidenceType.PLANET_DIGNITY,
        ]
    )


# ==================== Demo Rule 3: Yogakaraka Demonstration ====================

def create_demo_yogakaraka() -> RuleDefinition:
    """
    Demo: Yogakaraka Planet Detection
    
    Demonstrates functional strength integration.
    """
    
    metadata = RuleMetadata(
        rule_id="PARASHARI.STRENGTH.YOGAKARAKA_DETECTION",
        rule_version="1.0.0",
        name="Yogakaraka Planet Detection",
        category=RuleCategory.STRENGTH,
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        school_method="Parashari Classical",
        status=RuleStatus.ENABLED,
        description="Identifies planets that are Yogakaraka (rule both Kendra and Trikona) for the ascendant.",
        provenance=Provenance(
            source_type=SourceType.CLASSICAL_TEXT,
            source_name=ClassicalSource.BPHS.value,
            source_reference="BPHS Ch. 34, Vs. 1-5",
            tradition=RuleTradition.PARASHARI_CLASSICAL,
            method="Parashari Classical",
            implementation_version="1.0.0"
        ),
        confidence=ConfidenceLevel.VERIFIED,
        tags=["yogakaraka", "functional_strength", "kendra", "trikona"],
        enabled=True
    )
    
    formation = _all_of("formation_yk", [
        _cond("yogakaraka", {"planet": "Mars", "condition_id": "mars_yk"}),
    ])
    
    strength = _all_of("strength_yk", [
        _cond("functional_benefic", {"planet": "Mars", "condition_id": "mars_func_benefic"}),
    ])
    
    return RuleDefinition(
        metadata=metadata,
        formation_conditions=[formation],
        strength_conditions=[strength],
        required_evidence=[
            EvidenceType.YOGAKARAKA,
            EvidenceType.FUNCTIONAL_NATURE,
        ]
    )


# ==================== Demo Rule 4: Ruchaka Yoga ====================

def create_demo_ruchaka() -> RuleDefinition:
    """
    Demo: Ruchaka Yoga (Mars in own/exaltation in Kendra)
    
    One of the Pancha Mahapurusha Yogas.
    """
    
    metadata = RuleMetadata(
        rule_id="PARASHARI.YOGA.RUCHAKA",
        rule_version="1.0.0",
        name="Ruchaka Yoga",
        category=RuleCategory.YOGA,
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        school_method="Parashari Classical",
        status=RuleStatus.ENABLED,
        description="Mars in own sign (Aries/Scorpio) or exaltation (Capricorn) in Kendra. Gives courage, leadership, military/police success.",
        provenance=Provenance(
            source_type=SourceType.CLASSICAL_TEXT,
            source_name=ClassicalSource.BPHS.value,
            source_reference="BPHS Ch. 36, Vs. 13-14",
            tradition=RuleTradition.PARASHARI_CLASSICAL,
            method="Parashari Classical",
            implementation_version="1.0.0"
        ),
        confidence=ConfidenceLevel.VERIFIED,
        tags=["pancha_mahapurusha", "mars", "kendra", "leadership"],
        enabled=True
    )
    
    formation = _all_of("formation_ruchaka", [
        _cond("planet_in_kendra", {"planet": "Mars", "condition_id": "mars_kendra"}),
        _any_of("mars_dignity", [
            _cond("planet_in_own_sign", {"planet": "Mars", "condition_id": "mars_own"}),
            _cond("planet_exalted", {"planet": "Mars", "condition_id": "mars_exalted"}),
        ])
    ])
    
    strength = _all_of("strength_ruchaka", [
        _cond("planet_exalted", {"planet": "Mars", "condition_id": "mars_exalted_str"}),
        _cond("planet_in_own_sign", {"planet": "Mars", "condition_id": "mars_own_str"}),
    ])
    
    return RuleDefinition(
        metadata=metadata,
        formation_conditions=[formation],
        strength_conditions=[strength],
        required_evidence=[
            EvidenceType.KENDRA_TRIKONA,
            EvidenceType.PLANET_DIGNITY,
        ]
    )


# ==================== Registry Population ====================

def populate_demo_rules(registry) -> int:
    """Register all demo rules in the registry"""
    rules = [
        create_demo_raja_yoga_9_10(),
        create_demo_gaja_kesari(),
        create_demo_yogakaraka(),
        create_demo_ruchaka(),
    ]
    
    registered = 0
    for rule in rules:
        try:
            registry.register(rule, source="demo")
            registered += 1
        except ValueError as e:
            print(f"Demo rule registration failed: {e}")
    
    return registered


def get_demo_rules() -> list:
    """Get all demo rules as a list"""
    return [
        create_demo_raja_yoga_9_10(),
        create_demo_gaja_kesari(),
        create_demo_yogakaraka(),
        create_demo_ruchaka(),
    ]