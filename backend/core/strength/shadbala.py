"""
Shadbala Main Calculation - Classical Parashari Implementation

Combines all six Balas:
1. Sthana Bala (Positional)
2. Dig Bala (Directional)
3. Kala Bala (Temporal)
4. Chesta Bala (Motional)
5. Naisargika Bala (Natural)
6. Drig Bala (Aspectual)

Total in Virupas, converted to Rupas (1 Rupa = 60 Virupas)
"""
from typing import Dict, Optional
from datetime import datetime

from core.strength.models import ShadbalaResult, StrengthSystem, StrengthClassification
from core.strength.profile import StrengthCalculationProfile, DEFAULT_STRENGTH_PROFILE
from core.calculation.pipeline import ChartFacts
from core.calculation.varga import calculate_all_vargas
from core.strength.sthana_bala import calculate_sthana_bala
from core.strength.dig_bala import calculate_dig_bala
from core.strength.kala_bala import calculate_kala_bala
from core.strength.chesta_bala import calculate_chesta_bala
from core.strength.naisargika_bala import calculate_naisargika_bala
from core.strength.drig_bala import calculate_drig_bala


# Traditional minimum Shadbala requirements (in Rupas)
MINIMUM_SHADBALA_RUPAS = {
    "Sun": 6.5,
    "Moon": 6.0,
    "Mars": 5.0,
    "Mercury": 7.0,
    "Jupiter": 6.5,
    "Venus": 5.5,
    "Saturn": 5.0,
}


def calculate_shadbala(
    planet: str,
    chart_facts: ChartFacts,
    varga_results: Dict,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE,
    evaluation_datetime: Optional[datetime] = None
) -> ShadbalaResult:
    """
    Calculate complete classical Shadbala for a planet.
    
    Returns structured result with all six Bala components and totals.
    """
    
    # Calculate all six Balas
    sthana = calculate_sthana_bala(planet, chart_facts, varga_results, profile)
    dig = calculate_dig_bala(planet, chart_facts, profile)
    kala = calculate_kala_bala(planet, chart_facts, profile, evaluation_datetime)
    chesta = calculate_chesta_bala(planet, chart_facts, profile)
    naisargika = calculate_naisargika_bala(planet, chart_facts, profile)
    drig = calculate_drig_bala(planet, chart_facts, profile)
    
    # Total in Virupas
    total_virupas = (
        sthana.total +
        dig.value +
        kala.total +
        chesta.value +
        naisargika.value +
        drig.value
    )
    
    # Convert to Rupas (1 Rupa = 60 Virupas)
    total_rupas = round(total_virupas / 60.0, 4)
    
    # Minimum requirement
    minimum_rupas = MINIMUM_SHADBALA_RUPAS.get(planet, 0.0)
    ratio = round(total_rupas / minimum_rupas, 4) if minimum_rupas > 0 else 0.0
    
    # Strength status
    if ratio >= 1.0:
        status = "STRONG"
    elif ratio >= 0.8:
        status = "MODERATE"
    else:
        status = "WEAK"
    
    return ShadbalaResult(
        planet=planet,
        system=StrengthSystem.PARASHARI_SHADBALA,
        method=profile.shadbala_method.value,
        classification=StrengthClassification.CLASSICAL,
        sthana_bala=sthana,
        dig_bala=dig,
        kala_bala=kala,
        chesta_bala=chesta,
        naisargika_bala=naisargika,
        drig_bala=drig,
        total_virupas=round(total_virupas, 4),
        total_rupas=total_rupas,
        minimum_rupas=minimum_rupas,
        ratio=ratio,
        strength_status=status,
        metadata={
            "calculation_profile": profile.model_dump(),
            "evaluation_datetime": evaluation_datetime.isoformat() if evaluation_datetime else None
        }
    )


def calculate_all_shadbala(
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE,
    evaluation_datetime: Optional[datetime] = None
) -> Dict[str, ShadbalaResult]:
    """Calculate Shadbala for all 7 classical planets"""
    
    # Calculate all Vargas needed for Saptavargaja Bala
    varga_results = calculate_all_vargas(chart_facts, profile.base_profile)
    
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    results = {}
    
    for planet in planets:
        if planet in chart_facts.planets:
            results[planet] = calculate_shadbala(
                planet, chart_facts, varga_results, profile, evaluation_datetime
            )
    
    return results