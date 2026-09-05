"""
Strength Report Pipeline - Main Entry Point

Generates complete classical strength report from ChartFacts.
"""
from typing import Dict, Optional
from datetime import datetime

from core.strength.models import StrengthReport, StrengthSystem
from core.strength.profile import StrengthCalculationProfile, DEFAULT_STRENGTH_PROFILE
from core.calculation.pipeline import ChartFacts, generate_chart_facts
from core.calculation.varga import calculate_all_vargas
from core.strength.shadbala import calculate_all_shadbala
from core.strength.bhava_bala import calculate_bhava_bala
from core.strength.vimsopaka import calculate_all_vimsopaka
from core.strength.avastha import calculate_all_avastha
from core.strength.dignity import calculate_all_dignities
from core.strength.functional import calculate_all_functional_strength
from core.strength.composite import calculate_all_composite_strength


def generate_strength_report(
    chart_facts: ChartFacts,
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE,
    evaluation_datetime: Optional[datetime] = None,
    d9_chart_facts: Optional[ChartFacts] = None
) -> StrengthReport:
    """
    Generate complete classical strength report.
    
    This is the main entry point for Phase 4 strength calculations.
    Consumes canonical ChartFacts from Phase 1 and validated Vargas from Phase 2.
    
    Returns:
        StrengthReport with all classical components:
        - Shadbala (6 Balas) for each planet
        - Bhava Bala for each house
        - Vimsopaka Bala for each planet
        - Avastha for each planet
        - Dignity for each planet
        - Functional Strength for each planet
        - Composite (Custom) Strength for each planet
    """
    
    # Calculate all classical components
    planets_shadbala = calculate_all_shadbala(chart_facts, profile, evaluation_datetime)
    bhava_bala = calculate_bhava_bala(chart_facts, profile)
    vimsopaka = calculate_all_vimsopaka(chart_facts, profile)
    avastha = calculate_all_avastha(chart_facts, profile)
    dignity = calculate_all_dignities(chart_facts, profile)
    functional = calculate_all_functional_strength(chart_facts, profile)
    composite = calculate_all_composite_strength(chart_facts, d9_chart_facts, profile)
    
    # Build report
    report = StrengthReport(
        calculation_profile=profile.model_dump(),
        planets=planets_shadbala,
        bhava_bala=bhava_bala,
        vimsopaka=vimsopaka,
        avastha=avastha,
        dignity=dignity,
        functional_strength=functional,
        composite=composite,
        metadata={
            "generated_at": evaluation_datetime.isoformat() if evaluation_datetime else datetime.utcnow().isoformat(),
            "chart_facts_jd": chart_facts.time.julian_day,
            "ayanamsha": chart_facts.ayanamsha.value,
            "ascendant": chart_facts.ascendant.sign.name,
        }
    )
    
    return report


def generate_strength_report_from_birth(
    year: int, month: int, day: int,
    hour: int, minute: int, second: int,
    lat: float, lon: float, tz_name: str,
    location_name: str = "Unknown",
    country_name: str = "Unknown",
    profile: StrengthCalculationProfile = DEFAULT_STRENGTH_PROFILE,
    evaluation_datetime: Optional[datetime] = None
) -> StrengthReport:
    """
    Convenience function to generate strength report directly from birth data.
    
    Internally calls generate_chart_facts() then generate_strength_report().
    """
    # Generate canonical chart facts
    chart_facts = generate_chart_facts(
        year=year, month=month, day=day,
        hour=hour, minute=minute, second=second,
        lat=lat, lon=lon, tz_name=tz_name,
        location_name=location_name,
        country_name=country_name,
        profile=profile.base_profile
    )
    
    # Generate D9 chart facts for composite calculation
    from core.calculation.varga import calculate_all_vargas
    varga_results = calculate_all_vargas(chart_facts, profile.base_profile)
    
    # Create D9 ChartFacts-like object for composite
    d9_chart_facts = None
    if "d9" in varga_results:
        # We need to create a minimal ChartFacts for D9
        # For now, pass the varga results
        class D9Facts:
            def __init__(self, varga_data):
                self.planets = {}
                for p in varga_data.get("planets", []):
                    class P:
                        def __init__(self, data):
                            self.sign = type('Sign', (), {'name': data.get('sign')})()
                            self.sign.degree = 0  # D9 degrees not used for dignity
                    self.planets[p["name"]] = P(p)
        
        d9_chart_facts = D9Facts(varga_results["d9"])
    
    return generate_strength_report(chart_facts, profile, evaluation_datetime, d9_chart_facts)


# Golden Chart Test Function
def test_golden_chart_strength():
    """Test strength calculations against the golden chart"""
    
    # Golden chart birth data
    BIRTH = {
        "year": 2005, "month": 8, "day": 17,
        "hour": 0, "minute": 2, "second": 0,
        "lat": 16.93407, "lon": 81.95522, "tz_name": "Asia/Kolkata"
    }
    
    report = generate_strength_report_from_birth(**BIRTH)
    
    print("=" * 70)
    print("ASTROLIFE V2 - PHASE 4: GOLDEN CHART STRENGTH REPORT")
    print("=" * 70)
    
    for planet, shadbala in report.planets.items():
        print(f"\n--- {planet} ---")
        print(f"  Total: {shadbala.total_rupas:.4f} Rupas ({shadbala.total_virupas:.1f} Virupas)")
        print(f"  Minimum: {shadbala.minimum_rupas} Rupas, Ratio: {shadbala.ratio:.4f}, Status: {shadbala.strength_status}")
        print(f"  Sthana: {shadbala.sthana_bala.total:.1f}/{shadbala.sthana_bala.maximum:.1f}")
        print(f"  Dig: {shadbala.dig_bala.value:.1f}/{shadbala.dig_bala.maximum:.1f}")
        print(f"  Kala: {shadbala.kala_bala.total:.1f}/{shadbala.kala_bala.maximum:.1f}")
        print(f"  Chesta: {shadbala.chesta_bala.value:.1f}/{shadbala.chesta_bala.maximum:.1f}")
        print(f"  Naisargika: {shadbala.naisargika_bala.value:.1f}/{shadbala.naisargika_bala.maximum:.1f}")
        print(f"  Drig: {shadbala.drig_bala.value:.1f}/{shadbala.drig_bala.maximum:.1f}")
        
        # Dignity
        if planet in report.dignity:
            d = report.dignity[planet]
            print(f"  Dignity: {d.dignity} (Ruler: {d.ruler})")
        
        # Composite
        if planet in report.composite:
            c = report.composite[planet]
            print(f"  Composite: {c.score:.1f} ({c.label})")
    
    return report


if __name__ == "__main__":
    test_golden_chart_strength()