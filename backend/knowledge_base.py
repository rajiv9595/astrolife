"""
Knowledge Base for AI Astrologer.
This module loads interpreting rules and texts for the AI to use.
"""

import os
import json

# Internal storage for rule interpretations
# In a real app, this could be a database. For now, we use a simple dictionary structure.
KNOWLEDGE_BASE = {
    # General Astrology Concepts
    "concepts": {
        "Dharma Karma Adhipati": "A powerful combination of the 9th lord (Dharma) and 10th lord (Karma), indicating career success through righteous action.",
        "Gaja Kesari Yoga": "Jupiter and Moon in mutual kendras. Bestows wisdom, wealth, and a virtuous reputation.",
        "Budhaditya Yoga": "Sun and Mercury conjunction. Gives intelligence, communication skills, and administrative ability.",
        "Pancha Mahapurusha": "Five great personages yoga formed by Mars, Mercury, Jupiter, Venus, or Saturn in own/exaltation signs in kendra.",
        "Vipareeta Raja Yoga": "Lords of dusthana houses (6, 8, 12) placed in other dusthana houses. Success comes after struggle or through the misfortune of others."
    },
    
    # House Meanings for Career (10th House focused)
    "houses": {
        "1": "Self, vitality, general path in life.",
        "2": "Wealth, liquid assets, speech.",
        "6": "Service, enemies, obstacles, daily work routine.",
        "7": "Partnerships, business dealings.",
        "9": "Higher education, luck, mentors, dharma.",
        "10": "Career, reputation, public standing, authority.",
        "11": "Gains, professional network, income."
    },
    
    # Planet significations for Career
    "planets_career": {
        "Sun": "Government, authority, leadership, medicine, administration.",
        "Moon": "Public dealing, caregiving, liquids, arts, mind.",
        "Mars": "Engineering, police, military, surgery, land, logic.",
        "Mercury": "Business, writing, accounting, coding, media.",
        "Jupiter": "Teaching, law, finance, counseling, wisdom.",
        "Venus": "Arts, entertainment, luxury, women-related products.",
        "Saturn": "Labor, service, mining, oil, discipline, long-term building.",
        "Rahu": "Technology, foreign lands, innovation, unconventional career.",
        "Ketu": "Research, occult, coding, microbiology, spiritual pursuits."
    }
}

def get_knowledge_context():
    """Returns the full knowledge base context for part of the system prompt."""
    return json.dumps(KNOWLEDGE_BASE, indent=2)

def get_rule_interpretation(rule_name):
    """Specific lookup for a rule."""
    return KNOWLEDGE_BASE["concepts"].get(rule_name, "")
