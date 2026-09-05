"""
Rule Validators — Astrolife V2 Phase 5A

Validation logic for rule definitions, metadata, and registry integrity.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any, Set
import re

from .models import RuleDefinition, RuleMetadata, Provenance
from .enums import RuleCategory, RuleTradition, RuleStatus, ConfidenceLevel, SourceType
from .provenance import validate_provenance


class ValidationError(Exception):
    """Rule validation error"""
    pass


class ValidationWarning(Exception):
    """Rule validation warning (non-blocking)"""
    pass


def validate_rule_id(rule_id: str) -> List[str]:
    """Validate rule ID format"""
    errors = []
    
    if not rule_id:
        errors.append("Rule ID is required")
        return errors
    
    # Expected format: TRADITION.CATEGORY.NAME
    # Example: PARASHARI.YOGA.GAJA_KESARI
    parts = rule_id.split(".")
    if len(parts) != 3:
        errors.append(f"Rule ID '{rule_id}' must have format TRADITION.CATEGORY.NAME (3 parts separated by dots)")
        return errors
    
    tradition_part, category_part, name_part = parts
    
    # Validate tradition part - allow common aliases
    valid_traditions = {t.value for t in RuleTradition}
    tradition_aliases = {
        "PARASHARI": "PARASHARI_CLASSICAL",
        "JAIMINI": "JAIMINI",
    }
    normalized_tradition = tradition_aliases.get(tradition_part, tradition_part)
    if normalized_tradition not in valid_traditions and tradition_part != "CUSTOM":
        errors.append(f"Rule ID tradition '{tradition_part}' not recognized. Valid: {valid_traditions}")
    
    # Validate category part
    valid_categories = {c.value for c in RuleCategory}
    if category_part not in valid_categories:
        errors.append(f"Rule ID category '{category_part}' not recognized. Valid: {valid_categories}")
    
    # Validate name part (uppercase with underscores)
    if not re.match(r'^[A-Z0-9_]+$', name_part):
        errors.append(f"Rule ID name '{name_part}' must be uppercase with underscores only")
    
    return errors


def validate_rule_version(version: str) -> List[str]:
    """Validate semantic version format"""
    errors = []
    
    if not version:
        errors.append("Rule version is required")
        return errors
    
    if not re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$', version):
        errors.append(f"Rule version '{version}' must follow semantic versioning (e.g., 1.0.0)")
    
    return errors


def validate_rule_metadata(metadata: RuleMetadata) -> List[str]:
    """Validate rule metadata"""
    errors = []
    
    # Rule ID
    errors.extend(validate_rule_id(metadata.rule_id))
    
    # Version
    errors.extend(validate_rule_version(metadata.rule_version))
    
    # Name
    if not metadata.name or not metadata.name.strip():
        errors.append("Rule name is required")
    
    # Category
    if metadata.category not in RuleCategory:
        errors.append(f"Invalid category: {metadata.category}")
    
    # Tradition
    if metadata.tradition not in RuleTradition:
        errors.append(f"Invalid tradition: {metadata.tradition}")
    
    # Status
    if metadata.status not in RuleStatus:
        errors.append(f"Invalid status: {metadata.status}")
    
    # Confidence
    if metadata.confidence not in ConfidenceLevel:
        errors.append(f"Invalid confidence level: {metadata.confidence}")
    
    # Provenance
    if not metadata.provenance:
        errors.append("Provenance is required")
    else:
        prov = metadata.provenance
        if prov.source_type not in SourceType:
            errors.append(f"Invalid source type: {prov.source_type}")
        if not prov.source_name or not prov.source_name.strip():
            errors.append("Provenance source_name is required")
        if not prov.source_reference or not prov.source_reference.strip():
            errors.append("Provenance source_reference is required")
    
    return errors


def validate_rule_definition(rule: RuleDefinition) -> tuple[List[str], List[str]]:
    """
    Validate complete rule definition.
    
    Returns:
        (errors, warnings) - errors block registration, warnings are advisory
    """
    errors = []
    warnings = []
    
    # Metadata validation
    errors.extend(validate_rule_metadata(rule.metadata))
    
    # Provenance validation
    warnings.extend(validate_provenance(rule))
    
    # Formation conditions
    if not rule.formation_conditions:
        warnings.append(f"Rule {rule.metadata.rule_id}: No formation conditions defined")
    
    # Strength conditions (optional)
    if not rule.strength_conditions:
        warnings.append(f"Rule {rule.metadata.rule_id}: No strength conditions defined")
    
    # Check for required evidence types
    if rule.required_evidence:
        for ev_type in rule.required_evidence:
            if not hasattr(ev_type, 'value'):
                warnings.append(f"Rule {rule.metadata.rule_id}: Invalid evidence type in required_evidence")
    
    # Activation rules (optional)
    if rule.activation_rules:
        for act in rule.activation_rules:
            if not act.rule_id:
                warnings.append(f"Rule {rule.metadata.rule_id}: Activation rule missing rule_id")
            if not act.evaluator:
                warnings.append(f"Rule {rule.metadata.rule_id}: Activation rule '{act.rule_id}' missing evaluator")
    
    # Cancellation rules (optional)
    if rule.cancellation_rules:
        for cancel in rule.cancellation_rules:
            if not cancel.rule_id:
                warnings.append(f"Rule {rule.metadata.rule_id}: Cancellation rule missing rule_id")
            if not cancel.evaluator:
                warnings.append(f"Rule {rule.metadata.rule_id}: Cancellation rule '{cancel.rule_id}' missing evaluator")
    
    # Mitigation rules (optional)
    if rule.mitigation_rules:
        for mit in rule.mitigation_rules:
            if not mit.rule_id:
                warnings.append(f"Rule {rule.metadata.rule_id}: Mitigation rule missing rule_id")
            if not mit.evaluator:
                warnings.append(f"Rule {rule.metadata.rule_id}: Mitigation rule '{mit.rule_id}' missing evaluator")
    
    # Custom evaluator
    if rule.custom_evaluator:
        warnings.append(f"Rule {rule.metadata.rule_id}: Uses custom evaluator '{rule.custom_evaluator}' - ensure it's registered")
    
    return errors, warnings


def validate_registry_integrity(registry: Any) -> List[str]:
    """Validate registry integrity (no duplicates, consistent indices)"""
    errors = []
    
    if not hasattr(registry, '_rules') or not hasattr(registry, '_by_id_version'):
        errors.append("Registry missing required internal structures")
        return errors
    
    # Check consistency between _rules and _by_id_version
    rule_ids_in_main = set(registry._rules.keys())
    rule_ids_in_versions = set(k.split("@")[0] for k in registry._by_id_version.keys())
    
    if rule_ids_in_main != rule_ids_in_versions:
        missing_in_main = rule_ids_in_versions - rule_ids_in_main
        missing_in_versions = rule_ids_in_main - rule_ids_in_versions
        if missing_in_main:
            errors.append(f"Rule IDs in versions but not in main: {missing_in_main}")
        if missing_in_versions:
            errors.append(f"Rule IDs in main but not in versions: {missing_in_versions}")
    
    # Check category index consistency
    if hasattr(registry, '_by_category'):
        for cat, ids in registry._by_category.items():
            for rid in ids:
                if rid not in rule_ids_in_main:
                    errors.append(f"Category index contains unknown rule_id: {rid}")
    
    # Check tradition index consistency
    if hasattr(registry, '_by_tradition'):
        for trad, ids in registry._by_tradition.items():
            for rid in ids:
                if rid not in rule_ids_in_main:
                    errors.append(f"Tradition index contains unknown rule_id: {rid}")
    
    return errors


def validate_condition_compatibility(rule: RuleDefinition) -> List[str]:
    """Validate that conditions are compatible with rule tradition/category"""
    warnings = []
    
    tradition = rule.metadata.tradition
    category = rule.metadata.category
    
    # Tradition-specific warnings
    if tradition == RuleTradition.PARASHARI_CLASSICAL:
        if category == RuleCategory.JAIMINI:
            warnings.append(f"Rule {rule.metadata.rule_id}: Jaimini category with Parashari tradition - verify compatibility")
    
    if tradition == RuleTradition.JAIMINI:
        if category == RuleCategory.YOGA:
            warnings.append(f"Rule {rule.metadata.rule_id}: Yoga category with Jaimini tradition - verify this is intentional")
    
    # Confidence vs tradition
    if tradition == RuleTradition.TRADITION_DEPENDENT:
        if rule.metadata.confidence in (ConfidenceLevel.VERIFIED, ConfidenceLevel.HIGH):
            warnings.append(f"Rule {rule.metadata.rule_id}: TRADITION_DEPENDENT but confidence is {rule.metadata.confidence.value} - consider MEDIUM or TRADITION_DEPENDENT")
    
    if tradition == RuleTradition.CUSTOM:
        if rule.metadata.confidence == ConfidenceLevel.VERIFIED:
            warnings.append(f"Rule {rule.metadata.rule_id}: CUSTOM tradition but VERIFIED confidence - this should be EXPERIMENTAL or CUSTOM")
    
    return warnings


def validate_all_rules(rules: List[RuleDefinition]) -> Dict[str, tuple[List[str], List[str]]]:
    """Validate multiple rules and return results by rule_id"""
    results = {}
    seen_ids = {}
    
    for rule in rules:
        rule_id = rule.metadata.rule_id
        version = rule.metadata.rule_version
        
        # Check for duplicate IDs with different versions
        if rule_id in seen_ids:
            if seen_ids[rule_id] != version:
                # This is OK - different versions allowed
                pass
        seen_ids[rule_id] = version
        
        errors, warnings = validate_rule_definition(rule)
        results[rule_id] = (errors, warnings)
    
    return results