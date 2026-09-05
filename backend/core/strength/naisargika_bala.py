"""
Naisargika Bala Calculation - Classical Parashari Implementation

Naisargika Bala (Natural Strength) - Fixed inherent strength of each planet.
Traditional values in Virupas (out of 60).
"""
from core.strength.models import NaisargikaBala
from core.strength.profile import StrengthCalculationProfile, NAISARGIKA_BALA
from core.calculation.pipeline import ChartFacts


def calculate_naisargika_bala(
    planet: str,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile
) -> NaisargikaBala:
    """
    Calculate Naisargika Bala - fixed natural strength.
    
    Classical values (Parashara BPHS):
    Sun: 60 virupas
    Moon: 51.43 virupas (360/7)
    Venus: 42.86 virupas (300/7)
    Jupiter: 34.29 virupas (240/7)
    Mercury: 25.71 virupas (180/7)
    Mars: 17.14 virupas (120/7)
    Saturn: 8.57 virupas (60/7)
    
    These are fixed and do not change based on chart.
    """
    traditional_value = NAISARGIKA_BALA.get(planet, 0.0)
    
    return NaisargikaBala(
        value=round(traditional_value, 4),
        maximum=60.0,
        unit="virupas",
        traditional_value=traditional_value,
        classification="CLASSICAL",
        description=f"Fixed natural strength per Parashara: {traditional_value} virupas"
    )