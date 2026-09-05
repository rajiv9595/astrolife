"""
Transit Aspects — two separate systems, never mixed.

1. WESTERN_DEGREE_ASPECTS: Conjunction, Sextile, Square, Trine, Opposition with configurable orbs.
   Fact only, no interpretation.

2. PARASHARI_GRAHA_DRISHTI: whole-sign graha drishti per BPHS:
   Sun 7, Moon 7, Mars 4/7/8, Mercury 7, Jupiter 5/7/9, Venus 7, Saturn 3/7/10
   Rahu/Ketu configurable via CalculationProfile (default NONE, documented).
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
import math

from ..calculation.config import CalculationProfile, DEFAULT_PROFILE, NodeAspectMode
from ..calculation.models import ChartFacts
from .calculator import TransitSnapshot

# ---------------------------------------------------------------------------
# Western degree aspects
# ---------------------------------------------------------------------------
WESTERN_ASPECT_ANGLES = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}

class WesternAspect(BaseModel):
    system: str = "WESTERN"
    type: str = "DEGREE_ASPECT"
    transit_planet: str
    natal_planet: str
    aspect: str  # conjunction etc or "none"
    exact_angle: float
    orb: float
    is_active: bool
    transit_longitude: float
    natal_longitude: float

def _angular_sep(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360 - d)

def _closest_western_aspect(sep: float) -> Tuple[str, float, float]:
    """
    Return (aspect_name, exact_angle, orb_to_aspect) for nearest western aspect.
    """
    best = None
    best_orb = 1e9
    best_name = "none"
    best_angle = 0.0
    for name, angle in WESTERN_ASPECT_ANGLES.items():
        # minimal circular distance to aspect angle via sep vs angle and 360-angle? sep already <=180 so direct
        orb = abs(sep - angle)
        # also check wrap e.g. sep 350 not relevant since sep <=180
        if orb < best_orb:
            best_orb = orb
            best_name = name
            best_angle = angle
    return best_name, best_angle, best_orb

def compute_western_aspects(
    transits: TransitSnapshot,
    natal: ChartFacts,
    profile: Optional[CalculationProfile] = None,
) -> List[WesternAspect]:
    if profile is None:
        profile = DEFAULT_PROFILE
    orbs_cfg = profile.western_aspect_config.orbs if profile and hasattr(profile, "western_aspect_config") else {}
    # default orbs
    defaults = {"conjunction":8.0,"sextile":4.0,"square":6.0,"trine":6.0,"opposition":8.0}
    cfg = {**defaults, **(orbs_cfg or {})}
    result: List[WesternAspect] = []
    for t_name, t_pos in transits.planets.items():
        for n_name, n_planet in natal.planets.items():
            n_lon = float(n_planet.longitude.sidereal)  # use sidereal if profile zodiac SIDEREAL else tropical? For Western, should use tropical but we use sidereal consistently with calculation_profile zodiac — here we assume SIDEREAL for both.
            # If profile zodiac is SIDEREAL, transits already sidereal; natal sidereal matches.
            # If TROPICAL, would need tropical longitudes — TODO but default is SIDEREAL so fine.
            t_lon = float(t_pos.sidereal_longitude) if profile.zodiac.value == "SIDEREAL" else float(t_pos.tropical_longitude)
            # For natal, if tropical requested, use tropical; but natal planets have both.
            if profile.zodiac.value == "TROPICAL":
                n_lon = float(n_planet.longitude.tropical)
            sep = _angular_sep(t_lon, n_lon)
            aspect, angle, orb = _closest_western_aspect(sep)
            is_active = orb <= cfg.get(aspect, 8.0) if aspect != "none" else False
            result.append(WesternAspect(
                transit_planet=t_name,
                natal_planet=n_name,
                aspect=aspect,
                exact_angle=angle,
                orb=round(float(orb), 4),
                is_active=is_active,
                transit_longitude=t_lon,
                natal_longitude=n_lon,
            ))
    return result

# ---------------------------------------------------------------------------
# Parashari Graha Drishti — whole-sign
# ---------------------------------------------------------------------------
class ParashariAspect(BaseModel):
    system: str = "PARASHARI"
    type: str = "GRAHA_DRISHTI"
    transit_planet: str
    natal_planet: str
    transit_house_from_natal_lagna: int  # 1..12 whole-sign from natal asc
    natal_house: int
    aspected_houses: List[int]  # houses transit aspects
    aspects_natal: bool
    graha: str
    aspect_rule: str  # e.g. "7" or "4,7,8"

def _house_from_signs(natal_asc_sign_num: int, target_sign_num: int) -> int:
    return ((target_sign_num - natal_asc_sign_num) % 12) + 1

def compute_parashari_aspects(
    transits: TransitSnapshot,
    natal: ChartFacts,
    profile: Optional[CalculationProfile] = None,
) -> List[ParashariAspect]:
    if profile is None:
        profile = DEFAULT_PROFILE
    asc_sign_num = int(natal.ascendant.sign.id)
    # Build natal planet sign map
    natal_planet_signs: Dict[str, int] = {name: int(p.sign.id) for name, p in natal.planets.items()}
    natal_planet_houses: Dict[str, int] = {name: _house_from_signs(asc_sign_num, sid) for name, sid in natal_planet_signs.items()}

    cfg = profile.parashari_aspect_config if profile and hasattr(profile, "parashari_aspect_config") else None
    base_aspects = {
        "Sun": [7], "Moon": [7], "Mars": [4,7,8], "Mercury": [7], "Jupiter": [5,7,9], "Venus": [7], "Saturn": [3,7,10],
    }
    if cfg and cfg.aspects:
        base_aspects = cfg.aspects
    node_mode = cfg.node_mode if cfg else NodeAspectMode.NONE

    result: List[ParashariAspect] = []
    for t_name, t_pos in transits.planets.items():
        # skip nodes if mode NONE
        if t_name in ("Rahu","Ketu"):
            if node_mode == NodeAspectMode.NONE:
                continue
            elif node_mode == NodeAspectMode.SAME_AS_JUPITER:
                offsets = [5,7,9]
            elif node_mode == NodeAspectMode.PARASHARI_5_7_9:
                offsets = [5,7,9]
            else:
                offsets = []
            rule = "5,7,9 (jupiter-like)" if node_mode != NodeAspectMode.NONE else "none"
        else:
            offsets = base_aspects.get(t_name, [7])
            rule = ",".join(str(o) for o in offsets)

        transit_sign = int(t_pos.sign_num)
        transit_house_from_lagna = _house_from_signs(asc_sign_num, transit_sign)
        # houses this graha aspects
        aspected_houses = sorted(set(((transit_house_from_lagna + off -1 -1) %12)+1 for off in offsets))  # wait: House+offset-1 logic
        # Actually if planet is in house H, it aspects H+off-1? No: graha drishti is counted from planet's house: H aspects H+off-1? Example: Mars in 1 aspects 4 = H+3. So house offset = (H-1+off-1)%12+1 ?? Let's define: planet in house H, aspect offset k means it aspects house ((H-1+k-1)%12)+1 = (H+k-2)%12+1? For 7th aspect, planet in 1 should aspect 7: (1+7-1)=7 -> (H + off -1). For Mars 4th: (1+4-1)=4 correct. So formula (H + off -1 -1?) Let's test: H=1 off=4 => 4 expected. (1+4-1)=4 correct. H=1 off=7 =>7 correct. H=1 off=8 =>8 correct. So general: house_aspected = ((H -1 + off -1) %12)+1 ??? That would give H=1 off=4 => (0+3)%12+1=4 correct. H=1 off=7 => (0+6)%12+1=7 correct. Equivalent to H+off-1 with modulo 12 but using 0-indexed. Let's use ((H -1 + off -1)%12)+1.
        # The earlier attempt used (H + off -2) which is same.

        aspected_houses = sorted({((transit_house_from_lagna -1 + off -1) %12)+1 for off in offsets})

        for n_name, n_house in natal_planet_houses.items():
            aspects = n_house in aspected_houses
            result.append(ParashariAspect(
                transit_planet=t_name,
                natal_planet=n_name,
                transit_house_from_natal_lagna=transit_house_from_lagna,
                natal_house=n_house,
                aspected_houses=sorted(aspected_houses),
                aspects_natal=aspects,
                graha=t_name,
                aspect_rule=rule,
            ))
    return result

# ---------------------------------------------------------------------------
# Transit vs Natal relationships (house, sign, nakshatra etc)
# ---------------------------------------------------------------------------
class TransitNatalRelation(BaseModel):
    transit_planet: str
    natal_planet: str
    transit_sign: str
    natal_sign: str
    transit_house_from_lagna: int
    natal_house: int
    transit_house_from_moon: int
    transit_nakshatra: str
    natal_nakshatra: str
    angular_separation: float
    is_conjunction: bool  # orb < 8 deg
    is_opposition: bool   # orb to 180 < 8 deg

def compute_transit_natal_relations(
    transits: TransitSnapshot,
    natal: ChartFacts,
    orb_conjunction: float = 8.0,
    orb_opposition: float = 8.0,
) -> List[TransitNatalRelation]:
    asc_sign = int(natal.ascendant.sign.id)
    moon_sign = int(natal.planets["Moon"].sign.id) if "Moon" in natal.planets else asc_sign
    relations: List[TransitNatalRelation] = []
    for t_name, t_pos in transits.planets.items():
        t_sign_num = int(t_pos.sign_num)
        t_house_lagna = _house_from_signs(asc_sign, t_sign_num)
        t_house_moon = _house_from_signs(moon_sign, t_sign_num)
        for n_name, n_planet in natal.planets.items():
            n_sign_name = n_planet.sign.name
            sep = _angular_sep(float(t_pos.sidereal_longitude), float(n_planet.longitude.sidereal))
            is_conj = sep <= orb_conjunction
            is_opp = abs(sep - 180.0) <= orb_opposition
            relations.append(TransitNatalRelation(
                transit_planet=t_name,
                natal_planet=n_name,
                transit_sign=t_pos.sign,
                natal_sign=n_sign_name,
                transit_house_from_lagna=t_house_lagna,
                natal_house=int(n_planet.house),
                transit_house_from_moon=t_house_moon,
                transit_nakshatra=t_pos.nakshatra,
                natal_nakshatra=n_planet.nakshatra.name,
                angular_separation=round(float(sep),4),
                is_conjunction=is_conj,
                is_opposition=is_opp,
            ))
    return relations
