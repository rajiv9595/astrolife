"""
Phase 8 — event taxonomy (§3). EVENT CATEGORIES only.

Category labels are semantic handles. They define NO astrology by
themselves; the mapping to canonical rules lives exclusively in declarative
EventDefinitions (event_definitions.py), which reference accepted rule IDs.
"""
from __future__ import annotations

RELATIONSHIP = "RELATIONSHIP"
MARRIAGE = "MARRIAGE"
CAREER = "CAREER"
JOB_CHANGE = "JOB_CHANGE"
PROMOTION = "PROMOTION"
BUSINESS = "BUSINESS"
EDUCATION = "EDUCATION"
TRAVEL = "TRAVEL"
RELOCATION = "RELOCATION"
PROPERTY = "PROPERTY"
FINANCE = "FINANCE"
CHILDREN = "CHILDREN"
HEALTH = "HEALTH"
SPIRITUAL = "SPIRITUAL"
LEGAL = "LEGAL"
OTHER = "OTHER"

EVENT_CATEGORIES = (
    RELATIONSHIP, MARRIAGE, CAREER, JOB_CHANGE, PROMOTION, BUSINESS,
    EDUCATION, TRAVEL, RELOCATION, PROPERTY, FINANCE, CHILDREN,
    HEALTH, SPIRITUAL, LEGAL, OTHER,
)
