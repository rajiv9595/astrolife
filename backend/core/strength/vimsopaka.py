"""
Vimsopaka Bala Calculation - Classical Parashari Implementation

Vimsopaka Bala (20-point strength) - Based on dignity in multiple Vargas.
Uses the validated Varga engine from Phase 2.
"""
import sys
import os
# Add the backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from typing import Dict, List
from .models import VimsopakaBalaResult, StrengthSystem, StrengthClassification
from .profile import StrengthCalculationProfile, DEFAULT_STRENGTH_PROFILE, NATURAL_FRIENDSHIP
from ..calculation.pipeline import ChartFacts
from ..calculation.varga import calculate_all_vargas
from tables import SIGN_LORDS


def get_dignity_score(planet: str, sign: str) -> float:
    """Get dignity score for a planet in a sign (0-60 scale)"""
    from core.strength.profile import EXALTATION_DATA, MOOLATRIKONA_DATA
    
    if planet not in EXALTATION_DATA:
        return 15.0  # Neutral default
    
    ex_data = EXALTATION_DATA[planet]
    mool_data = MOOLATRIKONA_DATA.get(planet, {})
    
    # Exaltation
    if sign == ex_data["sign"]:
        return 60.0
    
    # Debilitation
    if sign == ex_data["debilitation_sign"]:
        return 0.0
    
    # Moolatrikona
    if sign == mool_data.get("sign"):
        return 45.0
    
    # Own sign
    if SIGN_LORDS.get(sign) == planet:
        return 30.0
    
    # Friend/Enemy/Neutral
    nat = NATURAL_FRIENDSHIP.get(planet, {})
    sign_lord = SIGN_LORDS.get(sign)
    
    if sign_lord in nat.get("friends", []):
        return 22.5
    if sign_lord in nat.get("enemies", []):
        return 7.5
    
    return 15.0  # Neutral


def calculate_vimsopaka_bala(
    planet: str,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE
) -> VimsopakaBalaResult:
    """
    Calculate Vimsopaka Bala for a planet.
    
    Classical method: Sum of (dignity_score * weight) across selected Vargas,
    normalized to 20-point scale.
    """
    # Calculate all Vargas
    varga_results = calculate_all_vargas(chart_facts, profile.base_profile)
    
    varga_contributions = []
    total_weighted = 0.0
    total_weight = 0.0
    
    for varga_num in profile.vimsopaka_vargas:
        weight = profile.vimsopaka_weights.get(varga_num, 1.0)
        varga_key = f"d{varga_num}"
        
        if varga_key not in varga_results:
            continue
        
        varga_data = varga_results[varga_key]
        
        # Find planet in this varga
        planet_varga = None
        for p in varga_data.get("planets", []):
            if p.get("name") == planet:
                planet_varga = p
                break
        
        if not planet_varga:
            continue
        
        varga_sign = planet_varga.get("sign")
        if not varga_sign:
            continue
        
        # Get dignity score (0-60)
        dignity_score = get_dignity_score(planet, varga_sign)
        
        # Weighted contribution
        weighted = dignity_score * weight
        total_weighted += weighted
        total_weight += weight
        
        varga_contributions.append({
            "varga": varga_num,
            "sign": varga_sign,
            "dignity_score": dignity_score,
            "weight": weight,
            "weighted_score": round(weighted, 4)
        })
    
    # Normalize to 20-point scale
    # Maximum possible = 60 * sum(weights)
    max_possible = 60.0 * total_weight if total_weight > 0 else 1.0
    score = (total_weighted / max_possible) * 20.0 if max_possible > 0 else 0.0
    score = min(20.0, max(0.0, score))
    
    ratio = score / 20.0
    
    return VimsopakaBalaResult(
        planet=planet,
        system=StrengthSystem.VIMSOPAKA,
        method="PARASHARI_CLASSICAL",
        classification=StrengthClassification.TRADITION_DEPENDENT,
        score=round(score, 4),
        maximum=20.0,
        ratio=round(ratio, 4),
        varga_contributions=varga_contributions,
        vargas_used=profile.vimsopaka_vargas,
        weights=profile.vimsopaka_weights
    )


def calculate_all_vimsopaka(
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE
) -> Dict[str, VimsopakaBalaResult]:
    """Calculate Vimsopaka Bala for all planets"""
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    results = {}
    
    for planet in planets:
        if planet in chart_facts.planets:
            results[planet] = calculate_vimsopaka_bala(planet, chart_facts, profile)
    
    return results