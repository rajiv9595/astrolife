"""
Phase 5H — Rule → Event Mapping Catalogue.

EXPLICIT mappings only. NO arbitrary mappings.

Do NOT implement:
  "AK strong → career"
  "UL strong → marriage"
  "AL strong → success"

unless a specific rule definition supports that relationship.

Every mapping must define:
  rule_id, event_category, activation conditions,
  timing requirements, required dasha level,
  transit requirements, evidence requirements,
  tradition/profile, confidence, provenance.

If a Jaimini rule has no defensible event mapping:
DO NOT create one.
Leave it as a rule-only result.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any

from enum import Enum
from datetime import datetime, timezone

from .candidates import (
    JaiminiEventCategory,
    JaiminiEventCandidate,
    MappingEntry,
    DashaActivation,
    ConvergenceLevel,
    ConflictType,
    TemporalPrecision,
)


# ============================================================================
# Mapping Activation Inputs
# ============================================================================

class ActivationCondition(str, Enum):
    """Declared inputs for rule activation. Only these inputs may be
    used by a mapping. No arbitrary inputs."""

    ACTIVE_DASHA_SIGN = "active_dasha_sign"
    ACTIVE_SUBPERIOD_SIGN = "active_subperiod_sign"
    TRANSIT_RELATIONSHIP = "transit_relationship"
    NATAL_SIGN_RELATIONSHIP = "natal_sign_relationship"
    KARAKAMSHA = "karakamsha"
    AL = "al"
    UL = "ul"
    RELEVANT_KARAKA = "relevant_karaka"
    RASHI_DRISHTI = "rashi_drishti"


# ============================================================================
# Event Mapping Catalogue
# ============================================================================

# Mapping registry: rule_id → list of MappingEntry
_MAPPING_REGISTRY: Dict[str, List["MappingEntry"]] = {}


def register_mapping(
    rule_id: str,
    event_category: JaiminiEventCategory,
    activation_conditions: List[ActivationCondition],
    timing_requirements: str,
    required_dasha_level: str,
    transit_requirements: str,
    evidence_requirements: List[str],
    tradition: str = "JAIMINI",
    method: str = "",
    confidence: str = "TRADITION_DEPENDENT",
    provenance: str = "UNVERIFIED",
) -> None:
    """Register an explicit rule → event mapping.

    Only mappings registered via this function will be used by the
    timing engine. No arbitrary mappings are ever created.

    rule_id must be a valid Jaimini rule ID from the Phase 5E/5F catalogue.
    Activation conditions must be from ActivationCondition enum.
    """
    entry = MappingEntry(
        rule_id=rule_id,
        event_category=event_category,
        activation_conditions=activation_conditions,
        timing_requirements=timing_requirements,
        required_dasha_level=required_dasha_level,
        transit_requirements=transit_requirements,
        evidence_requirements=evidence_requirements,
        tradition=tradition,
        method=method,
        confidence=confidence,
        provenance=provenance,
    )
    if rule_id not in _MAPPING_REGISTRY:
        _MAPPING_REGISTRY[rule_id] = []
    _MAPPING_REGISTRY[rule_id].append(entry)


def get_mappings(rule_id: str) -> List["MappingEntry"]:
    """Retrieve all mapped entries for a rule ID."""
    return _MAPPING_REGISTRY.get(rule_id, [])


def get_all_mappings() -> Dict[str, List["MappingEntry"]]:
    """Retrieve the complete mapping catalogue."""
    return _MAPPING_REGISTRY


# ============================================================================
# Pre-registered Mappings (Defensible Only)
# These must each have a classical or textual basis. No arbitrary
# planet→house or planet→outcome assumptions.
# ============================================================================

# ---------------------------------------------------------------------------
# AK + AmK Conjunction → Relationship/Marriage Events
# ---------------------------------------------------------------------------

# JAI.KARAKA.AK_AMK_CONJUNCTION
# AK and AmK conjunct → relationship events when activated by dasha/transit
register_mapping(
    rule_id="JAI.KARAKA.AK_AMK_CONJUNCTION",
    event_category=JaiminiEventCategory.RELATIONSHIP,
    activation_conditions=[
        ActivationCondition.ACTIVE_DASHA_SIGN,
        ActivationCondition.TRANSIT_RELATIONSHIP,
    ],
    timing_requirements="MAHA_DASHA",
    required_dasha_level="MAHA_DASHA",
    transit_requirements="transit-to-natal-AK-sign",
    evidence_requirements=["DIRECT_FACT", "DERIVED_FACT"],
    tradition="JAIMINI",
    method="CLASSICAL_STANDARD",
    confidence="TRADITION_DEPENDENT",
    provenance="UNVERIFIED",
)

# ---------------------------------------------------------------------------
# AK aspect to AL → Relationship events
# ---------------------------------------------------------------------------

# JAI.DRISHTI.AK_ON_AL
# AK aspects AL → relationship events
register_mapping(
    rule_id="JAI.DRISHTI.AK_ON_AL",
    event_category=JaiminiEventCategory.RELATIONSHIP,
    activation_conditions=[
        ActivationCondition.ACTIVE_DASHA_SIGN,
        ActivationCondition.RASHI_DRISHTI,
    ],
    timing_requirements="MAHA_DASHA",
    required_dasha_level="MAHA_DASHA",
    transit_requirements="transit-to-natal-AK aspect AL",
    evidence_requirements=["DIRECT_FACT", "DERIVED_FACT", "RULE_DERIVED"],
    tradition="JAIMINI",
    method="CLASSICAL_STANDARD",
    confidence="TRADITION_DEPENDENT",
    provenance="UNVERIFIED",
)

# ---------------------------------------------------------------------------
# AmK on AL → Relationship/Marriage events
# ---------------------------------------------------------------------------

# JAI.DRISHTI.AMK_ON_AL
# AmK aspects AL → relationship events
register_mapping(
    rule_id="JAI.DRISHTI.AMK_ON_AL",
    event_category=JaiminiEventCategory.RELATIONSHIP,
    activation_conditions=[
        ActivationCondition.ACTIVE_DASHA_SIGN,
        ActivationCondition.RASHI_DRISHTI,
    ],
    timing_requirements="MAHA_DASHA",
    required_dasha_level="MAHA_DASHA",
    transit_requirements="transit-to-natal-AmK aspect AL",
    evidence_requirements=["DIRECT_FACT", "DERIVED_FACT", "RULE_DERIVED"],
    tradition="JAIMINI",
    method="CLASSICAL_STANDARD",
    confidence="TRADITION_DEPENDENT",
    provenance="UNVERIFIED",
)

# ---------------------------------------------------------------------------
# AK + AmK Mutual Drishti → Relationship events
# ---------------------------------------------------------------------------

# JAI.DRISHTI.AK_AMK_MUTUAL
# AK and AmK mutual aspect → relationship events
register_mapping(
    rule_id="JAI.DRISHTI.AK_AMK_MUTUAL",
    event_category=JaiminiEventCategory.RELATIONSHIP,
    activation_conditions=[
        ActivationCondition.ACTIVE_DASHA_SIGN,
        ActivationCondition.RASHI_DRISHTI,
    ],
    timing_requirements="MAHA_DASHA",
    required_dasha_level="MAHA_DASHA",
    transit_requirements="transit-involving-AK-or-AmK",
    evidence_requirements=["DIRECT_FACT", "DERIVED_FACT", "RULE_DERIVED"],
    tradition="JAIMINI",
    method="CLASSICAL_STANDARD",
    confidence="TRADITION_DEPENDENT",
    provenance="UNVERIFIED",
)

# ---------------------------------------------------------------------------
# DK + UL Sambandha → Family/Children events
# ---------------------------------------------------------------------------

# JAI.KARAKA.DK_UL_SAMBANDHA
# DK and UL relationship → family/children events
register_mapping(
    rule_id="JAI.KARAKA.DK_UL_SAMBANDHA",
    event_category=JaiminiEventCategory.CHILDREN,
    activation_conditions=[
        ActivationCondition.ACTIVE_DASHA_SIGN,
        ActivationCondition.KARAKAMSHA,
    ],
    timing_requirements="MAHA_DASHA",
    required_dasha_level="MAHA_DASHA",
    transit_requirements="transit-to-natal-DK-or-UL",
    evidence_requirements=["DIRECT_FACT", "DERIVED_FACT"],
    tradition="JAIMINI",
    method="CLASSICAL_STANDARD",
    confidence="TRADITION_DEPENDENT",
    provenance="UNVERIFIED",
)

# ---------------------------------------------------------------------------
# AL Lord in Kendra/Trine → Career/Wealth events
# ---------------------------------------------------------------------------

# JAI.ARUDHA.AL_LORD_KENDRA_TRINE
# AL lord in kendra or trine from AL → career/wealth events
register_mapping(
    rule_id="JAI.ARUDHA.AL_LORD_KENDRA_TRINE",
    event_category=JaiminiEventCategory.CAREER,
    activation_conditions=[
        ActivationCondition.ACTIVE_DASHA_SIGN,
        ActivationCondition.NATAL_SIGN_RELATIONSHIP,
    ],
    timing_requirements="MAHA_DASHA",
    required_dasha_level="MAHA_DASHA",
    transit_requirements="transit-to-natal-AL-lord",
    evidence_requirements=["DIRECT_FACT", "DERIVED_FACT"],
    tradition="JAIMINI",
    method="CLASSICAL_STANDARD",
    confidence="TRADITION_DEPENDENT",
    provenance="UNVERIFIED",
)

# ---------------------------------------------------------------------------
# A2 + A11 Dhana Yoga → Wealth events
# ---------------------------------------------------------------------------

# JAI.ARUDHA.DHANA_A2_A11
# A2 and A11 mutual aspect/relation → wealth events
register_mapping(
    rule_id="JAI.ARUDHA.DHANA_A2_A11",
    event_category=JaiminiEventCategory.WEALTH,
    activation_conditions=[
        ActivationCondition.ACTIVE_DASHA_SIGN,
        ActivationCondition.RASHI_DRISHTI,
    ],
    timing_requirements="MAHA_DASHA",
    required_dasha_level="MAHA_DASHA",
    transit_requirements="transit-involving-A2-or-A11",
    evidence_requirements=["DIRECT_FACT", "DERIVED_FACT", "RULE_DERIVED"],
    tradition="JAIMINI",
    method="CLASSICAL_STANDARD",
    confidence="TRADITION_DEPENDENT",
    provenance="UNVERIFIED",
)

# ---------------------------------------------------------------------------
# A7 + UL Alignment → Family events
# ---------------------------------------------------------------------------

# JAI.ARUDHA.A7_UL_ALIGNMENT
# A7 and UL same sign → family events
register_mapping(
    rule_id="JAI.ARUDHA.A7_UL_ALIGNMENT",
    event_category=JaiminiEventCategory.FAMILY,
    activation_conditions=[
        ActivationCondition.ACTIVE_DASHA_SIGN,
        ActivationCondition.KARAKAMSHA,
    ],
    timing_requirements="MAHA_DASHA",
    required_dasha_level="MAHA_DASHA",
    transit_requirements="transit-to-natal-A7-or-UL",
    evidence_requirements=["DIRECT_FACT", "DERIVED_FACT"],
    tradition="JAIMINI",
    method="CLASSICAL_STANDARD",
    confidence="TRADITION_DEPENDENT",
    provenance="UNVERIFIED",
)

# ---------------------------------------------------------------------------
# Karakamsha Benefic Occupancy → Spiritual events
# ---------------------------------------------------------------------------

# JAI.KARAKAMSHA.BENEFIC_OCCUPANCY
# Benefic in Karakamsha sign → spiritual events
register_mapping(
    rule_id="JAI.KARAKAMSHA.BENEFIC_OCCUPANCY",
    event_category=JaiminiEventCategory.SPIRITUAL,
    activation_conditions=[
        ActivationCondition.ACTIVE_DASHA_SIGN,
        ActivationCondition.KARAKAMSHA,
    ],
    timing_requirements="MAHA_DASHA",
    required_dasha_level="MAHA_DASHA",
    transit_requirements="transit-in-karakamsha-sign",
    evidence_requirements=["DIRECT_FACT", "DERIVED_FACT", "RULE_DERIVED"],
    tradition="JAIMINI",
    method="CLASSICAL_STANDARD",
    confidence="TRADITION_DEPENDENT",
    provenance="UNVERIFIED",
)

# ---------------------------------------------------------------------------
# No mapping created for rules without defensible event relationships.
# The following JAI rules have NO event mapping (intentionally left out):
# - JAI.KARAKA.AK_KENDRA_FROM_AL
# - JAI.KARAKA.DK_UL_SAMBANDHA (already mapped above with children category)
# Any rule not explicitly registered above remains rule-only.
# ---------------------------------------------------------------------------


def load_default_mappings() -> None:
    """Load all pre-registered mappings. Called once at engine init."""
    # All mappings are registered at module import time via
    # the register_mapping() calls above.
    pass


# Auto-load on import
_load_guard = False


def _ensure_loaded() -> None:
    global _load_guard
    if not _load_guard:
        _load_guard = True
        load_default_mappings()


ensure_loaded = _ensure_loaded


# ============================================================================
# Catalogue Query Functions
# ============================================================================

def find_mappings_for_category(
    category: JaiminiEventCategory,
) -> Dict[str, List["MappingEntry"]]:
    """Find all mappings that produce a given event category."""
    result: Dict[str, List["MappingEntry"]] = {}
    for rid, entries in _MAPPING_REGISTRY.items():
        for entry in entries:
            if entry.event_category == category:
                if rid not in result:
                    result[rid] = []
                result[rid].append(entry)
    return result


def find_mappings_with_activation(
    rule_id: str,
    active_condition: ActivationCondition,
) -> List["MappingEntry"]:
    """Find mappings for a rule that require a specific activation condition."""
    mappings = get_mappings(rule_id)
    return [
        m for m in mappings
        if active_condition in m.activation_conditions
    ]


# ---------------------------------------------------------------------------
# CRITICAL: No arbitrary mappings.
# ---------------------------------------------------------------------------

# The following patterns are EXPLICITLY FORBIDDEN and must NOT be added:
# - "AK strong → career" without a rule supporting it
# - "UL strong → marriage" without a rule supporting it
# - "AL strong → success" without a rule supporting it
# - Any mapping that infers outcome probabilities
# - Any mapping using Western degree aspects or Parashari Graha Drishti
#   unless explicitly declared in the mapping's transit_requirements
# - Any mapping using arbitrary scores (event_score, probability, strength)
#
# Every mapping MUST be registered via register_mapping() and must have
# a defensible classical or textual basis.
# ---------------------------------------------------------------------------


# Ensure mappings are loaded when this module is imported
_ensure_loaded()