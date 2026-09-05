"""
Phase 5B — synthetic fixture helper.

Builds a fully canonical RuleContext from a chosen Ascendant + planet signs
without touching Swiss Ephemeris: ChartFacts are constructed directly, then
the validated Phase 4 strength pipeline and Phase 2 Varga engine derive
StrengthReport + VargaFacts deterministically. Strength/dignity are therefore
authentic, never hand-faked.
"""
from __future__ import annotations
from typing import Dict, Optional, Tuple, Union

GOLDEN_BIRTH = {
    "year": 2005, "month": 8, "day": 17,
    "hour": 0, "minute": 2, "second": 0,
    "lat": 16.93407, "lon": 81.95522, "tz_name": "Asia/Kolkata",
    "location_name": "Anaparthy", "country_name": "India",
}

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _sign_id(name: str) -> int:
    return SIGNS.index(name) + 1


def make_synthetic_context(asc_sign: str,
                           placements: Dict[str, Union[str, Tuple[str, float]]],
                           include_nodes: bool = True):
    """Create a RuleContext with chosen D1 signs.

    placements: planet -> sign name OR (sign name, degree 0..30).
    Houses follow whole-sign from ascendant. Longitude = sign base + degree
    (default 15 deg mid-sign). Rahu/Ketu default to Pisces/Virgo unless given.
    """
    from core.calculation.models import (
        ChartFacts, PlanetData, HouseData, AscendantData, SignPosition,
        NakshatraPosition, LongitudeDetails, Location, TimeDetails, AyanamshaDetails,
    )
    from core.calculation.config import DEFAULT_PROFILE
    from core.calculation.nakshatra import get_nakshatra_from_longitude
    from core.strength.pipeline import generate_strength_report
    from core.calculation.varga import calculate_all_vargas
    from ..context import RuleContext

    asc_id = _sign_id(asc_sign)
    asc_lon = (asc_id - 1) * 30.0 + 10.0

    def _house_for(sign_id: int) -> int:
        return ((sign_id - asc_id) % 12) + 1

    planets: Dict[str, PlanetData] = {}
    norm: Dict[str, Tuple[str, float]] = {}
    for planet, spec in placements.items():
        if isinstance(spec, tuple):
            norm[planet] = (spec[0], float(spec[1]))
        else:
            norm[planet] = (spec, 15.0)
    if include_nodes:
        norm.setdefault("Rahu", ("Pisces", 15.0))
        norm.setdefault("Ketu", ("Virgo", 15.0))

    for planet, (sign, deg) in norm.items():
        sid = _sign_id(sign)
        lon = (sid - 1) * 30.0 + deg
        planets[planet] = PlanetData(
            id=planet, name=planet,
            longitude=LongitudeDetails(tropical=lon, sidereal=lon),
            latitude=0.0, distance=1.0, speed=1.0, retrograde=False,
            sign=SignPosition(id=sid, name=sign, degree=deg),
            house=_house_for(sid),
            nakshatra=get_nakshatra_from_longitude(lon),
        )

    houses = {}
    for h in range(1, 13):
        sid = ((asc_id + h - 2) % 12) + 1
        houses[h] = HouseData(id=h, sign=SignPosition(id=sid, name=SIGNS[sid - 1], degree=0.0))

    chart_facts = ChartFacts(
        calculation_profile=DEFAULT_PROFILE,
        location=Location(name="Synthetic", country="Test",
                          latitude=0.0, longitude=0.0, timezone="UTC"),
        time=TimeDetails(local_datetime="2000-01-01T00:00:00",
                         timezone="UTC", utc_datetime="2000-01-01T00:00:00",
                         julian_day=2451545.0),
        ayanamsha=AyanamshaDetails(system="TEST", swiss_mode="TEST", value=24.0),
        ascendant=AscendantData(
            longitude=LongitudeDetails(tropical=asc_lon, sidereal=asc_lon),
            sign=SignPosition(id=asc_id, name=asc_sign, degree=10.0),
            nakshatra=get_nakshatra_from_longitude(asc_lon)),
        planets=planets, houses=houses,
        metadata={"synthetic": True},
    )
    strength_report = generate_strength_report(chart_facts)
    varga_facts = calculate_all_vargas(chart_facts, DEFAULT_PROFILE)
    return RuleContext(chart_facts=chart_facts, strength_report=strength_report,
                       varga_facts=varga_facts, dynamic_state=None,
                       evaluation_datetime=None)


def make_golden_context():
    """Golden chart RuleContext via the canonical pipeline (no synthesis)."""
    from core.calculation.pipeline import generate_chart_facts
    from core.calculation.config import DEFAULT_PROFILE
    from core.strength.pipeline import generate_strength_report
    from core.calculation.varga import calculate_all_vargas
    from ..context import RuleContext

    b = GOLDEN_BIRTH
    cf = generate_chart_facts(
        year=b["year"], month=b["month"], day=b["day"], hour=b["hour"],
        minute=b["minute"], second=b["second"], lat=b["lat"], lon=b["lon"],
        tz_name=b["tz_name"], location_name=b["location_name"],
        country_name=b["country_name"], profile=DEFAULT_PROFILE)
    sr = generate_strength_report(cf)
    vf = calculate_all_vargas(cf, DEFAULT_PROFILE)
    return RuleContext(chart_facts=cf, strength_report=sr,
                       varga_facts=vf, dynamic_state=None, evaluation_datetime=None)
