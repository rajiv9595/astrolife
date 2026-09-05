"""
Jaimini Rashi Drishti Engine — Astrolife V2 Phase 5D

Calculates deterministic sign-based aspects (Rashi Drishti) according to classical Jaimini rules.
Segregated completely from Parashari Graha Drishti.

Classical Rules:
- Movable (Chara) signs aspect all Fixed (Sthira) signs EXCEPT the adjacent fixed sign (2nd from it).
- Fixed (Sthira) signs aspect all Movable (Chara) signs EXCEPT the adjacent movable sign (12th from it).
- Dual (Dvisvabhava) signs aspect all other Dual signs EXCEPT themselves.
"""
from __future__ import annotations
from typing import Dict, List, Set, Tuple, Optional, Any

from core.calculation.models import ChartFacts
from .profile import JaiminiCalculationProfile, RashiDrishtiMethod
from .models import RashiDrishtiSignItem, RashiDrishtiReport


# ---------------------------------------------------------------------------
# Sign Reference Tables
# ---------------------------------------------------------------------------

SIGNS_ORDER: List[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_TYPES: Dict[str, str] = {
    "Aries": "Movable",
    "Taurus": "Fixed",
    "Gemini": "Dual",
    "Cancer": "Movable",
    "Leo": "Fixed",
    "Virgo": "Dual",
    "Libra": "Movable",
    "Scorpio": "Fixed",
    "Sagittarius": "Dual",
    "Capricorn": "Movable",
    "Aquarius": "Fixed",
    "Pisces": "Dual",
}

# Pre-computed immutable canonical Rashi Drishti table
CANONICAL_SIGN_ASPECTS: Dict[str, List[str]] = {
    # Movable signs aspect all Fixed signs EXCEPT the adjacent one (the next sign)
    "Aries": ["Leo", "Scorpio", "Aquarius"],          # excludes Taurus (adjacent fixed)
    "Cancer": ["Scorpio", "Aquarius", "Taurus"],       # excludes Leo (adjacent fixed)
    "Libra": ["Aquarius", "Taurus", "Leo"],           # excludes Scorpio (adjacent fixed)
    "Capricorn": ["Taurus", "Leo", "Scorpio"],         # excludes Aquarius (adjacent fixed)

    # Fixed signs aspect all Movable signs EXCEPT the adjacent one (the previous sign)
    "Taurus": ["Cancer", "Libra", "Capricorn"],        # excludes Aries (adjacent movable)
    "Leo": ["Libra", "Capricorn", "Aries"],           # excludes Cancer (adjacent movable)
    "Scorpio": ["Capricorn", "Aries", "Cancer"],       # excludes Libra (adjacent movable)
    "Aquarius": ["Aries", "Cancer", "Libra"],          # excludes Capricorn (adjacent movable)

    # Dual signs aspect all other Dual signs EXCEPT themselves
    "Gemini": ["Virgo", "Sagittarius", "Pisces"],
    "Virgo": ["Gemini", "Sagittarius", "Pisces"],
    "Sagittarius": ["Gemini", "Virgo", "Pisces"],
    "Pisces": ["Gemini", "Virgo", "Sagittarius"],
}


def get_sign_rashi_drishti(sign_name: str) -> List[str]:
    """Returns the list of 3 signs aspected by sign_name."""
    if sign_name not in CANONICAL_SIGN_ASPECTS:
        raise ValueError(f"Invalid sign name: {sign_name}")
    return list(CANONICAL_SIGN_ASPECTS[sign_name])


def get_non_aspected_signs(sign_name: str) -> List[str]:
    """Returns the list of 8 signs NOT aspected by sign_name (excluding sign_name itself)."""
    aspected = set(get_sign_rashi_drishti(sign_name))
    aspected.add(sign_name)
    return [s for s in SIGNS_ORDER if s not in aspected]


def calculate_rashi_drishti(
    chart_facts: Optional[ChartFacts] = None,
    profile: Optional[JaiminiCalculationProfile] = None
) -> RashiDrishtiReport:
    """
    Computes complete Rashi Drishti fact matrix.
    If chart_facts is provided, also maps planetary Rashi Drishti based on occupied signs.
    """
    if profile is None:
        profile = JaiminiCalculationProfile()
        
    method = profile.rashi_drishti_method
    
    # 1. Sign aspects
    sign_aspects: Dict[str, List[str]] = {}
    for s in SIGNS_ORDER:
        sign_aspects[s] = list(CANONICAL_SIGN_ASPECTS[s])
        
    # 2. Planet positions if chart_facts provided
    planets_by_sign: Dict[str, List[str]] = {s: [] for s in SIGNS_ORDER}
    planet_signs: Dict[str, str] = {}
    
    if chart_facts is not None:
        for p_name, p_data in chart_facts.planets.items():
            s_name = p_data.sign.name
            planets_by_sign[s_name].append(p_name)
            planet_signs[p_name] = s_name

    # 3. Planet aspects and aspects on planets
    planet_aspects: Dict[str, List[str]] = {}
    planets_aspected_by_sign: Dict[str, List[str]] = {}
    planets_aspected_by_planet: Dict[str, List[str]] = {}
    
    for s in SIGNS_ORDER:
        aspected_s_list = sign_aspects[s]
        # Planets situated in aspected signs
        p_in_aspected = []
        for as_sign in aspected_s_list:
            p_in_aspected.extend(planets_by_sign[as_sign])
        planets_aspected_by_sign[s] = p_in_aspected

    for p_name, s_name in planet_signs.items():
        # Planet aspects the signs aspected by its occupied sign
        aspected_signs = list(sign_aspects[s_name])
        planet_aspects[p_name] = aspected_signs
        
        # Planet aspects all planets in those aspected signs
        aspected_planets = []
        for as_sign in aspected_signs:
            aspected_planets.extend(planets_by_sign[as_sign])
        planets_aspected_by_planet[p_name] = aspected_planets

    # Build evidence
    evidence: List[str] = [
        f"Rashi Drishti method: {method.value}",
        "Movable signs (Aries, Cancer, Libra, Capricorn) aspect Fixed signs except adjacent.",
        "Fixed signs (Taurus, Leo, Scorpio, Aquarius) aspect Movable signs except adjacent.",
        "Dual signs (Gemini, Virgo, Sagittarius, Pisces) aspect all other Dual signs."
    ]
    
    for s in SIGNS_ORDER:
        stype = SIGN_TYPES[s]
        asp_str = ", ".join(sign_aspects[s])
        evidence.append(f"Sign {s} ({stype}) aspects: [{asp_str}]")
        
    return RashiDrishtiReport(
        method=method,
        sign_aspects=sign_aspects,
        planet_aspects=planet_aspects,
        planets_aspected_by_sign=planets_aspected_by_sign,
        planets_aspected_by_planet=planets_aspected_by_planet,
        evidence=evidence
    )
