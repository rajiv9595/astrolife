"""
Chesta Bala Calculation - Classical Parashari Implementation

Chesta Bala (Motional Strength) based on planetary speed/retrogression.
Classical method uses actual planetary velocity from Swiss Ephemeris.

Classical Parashara rules (BPHS Chapter 27):
- For retrograde planets: 60 virupas (maximum)
- For direct planets: (actual_speed / mean_speed) * 60, capped at 60
- Sun and Moon are never retrograde, so they use the direct formula
- Mean motions from classical sources (Surya Siddhanta / BPHS)
"""
from .models import ChestaBala
from .profile import StrengthCalculationProfile
from ..calculation.pipeline import ChartFacts


# Mean daily motions (degrees per day) for Chesta Bala
# These are the CLASSICAL GEOCENTRIC mean motions used in Shadbala
# Derived from long-term averages of geocentric speeds (Surya Siddhanta / modern ephemeris)
# Source: Standard Jyotish references for Chesta Bala calculation
MEAN_MOTIONS = {
    "Sun": 0.985607,     # ~1°/day (tropical year)
    "Moon": 13.176358,   # ~13°10'/day (sidereal month)
    "Mars": 0.524038,    # ~0°31'/day
    "Mercury": 1.3820,   # Mean geocentric motion (varies widely)
    "Jupiter": 0.083091, # ~5'/day
    "Venus": 1.2279,     # Mean geocentric motion (varies)
    "Saturn": 0.033460,  # ~2'/day
}


def calculate_chesta_bala(
    planet: str,
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile
) -> ChestaBala:
    """
    Calculate Chesta Bala using actual planetary speed.
    
    Classical method (Parashara BPHS Chapter 27):
    - Retrograde planets: 60 virupas (maximum)
    - Direct planets: min(60, (actual_speed / mean_speed) * 60)
    - Sun and Moon are never retrograde, so they follow direct formula
    - Speed from Swiss Ephemeris (degrees/day in longitude)
    
    Note: Mercury and Venus have variable speeds; we use their mean motion
    as reference. The ratio can exceed 1.0 for fast direct motion.
    """
    planet_data = chart_facts.planets.get(planet)
    if not planet_data:
        return ChestaBala(
            value=0.0,
            maximum=60.0,
            unit="virupas",
            speed=0.0,
            is_retrograde=False,
            method="PARASHARI_SPEED_BASED",
            classification="CLASSICAL",
            description=f"Planet {planet} not found in chart"
        )
    
    speed = planet_data.speed  # degrees per day from Swiss Ephemeris (tropical)
    is_retrograde = planet_data.retrograde
    mean_motion = MEAN_MOTIONS.get(planet, 1.0)
    
    if is_retrograde:
        # Retrograde planets get full 60 virupas
        value = 60.0
        method_desc = "Retrograde (full Chesta Bala)"
    else:
        # Direct planets: proportional to speed/mean_speed
        ratio = speed / mean_motion
        value = min(60.0, 60.0 * ratio)
        method_desc = f"Direct, speed ratio {ratio:.4f}"
    
    return ChestaBala(
        value=round(value, 4),
        maximum=60.0,
        unit="virupas",
        speed=round(speed, 6),
        is_retrograde=is_retrograde,
        method="PARASHARI_SPEED_BASED",
        classification="CLASSICAL",
        description=f"Speed: {speed:.6f}°/day, Mean: {mean_motion:.6f}°/day, Retrograde: {is_retrograde}, {method_desc}"
    )