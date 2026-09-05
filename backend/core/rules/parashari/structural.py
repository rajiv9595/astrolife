"""
Phase 5B — reusable Parashari structural concepts.

Pure functions over RuleContext. No astronomy. Parashari whole-sign
houses + Parashari special aspects only (via RuleContext).
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

KENDRA_HOUSES = (1, 4, 7, 10)
TRIKONA_HOUSES = (1, 5, 9)
DUSTHANA_HOUSES = (6, 8, 12)
UPACHAYA_HOUSES = (3, 6, 10, 11)

SIGN_LORDS: Dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

NATURAL_BENEFICS = ("Jupiter", "Venus", "Mercury", "Moon")
NATURAL_MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")

SEVEN_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def house_of(ctx, planet: str) -> Optional[int]:
    return ctx.get_planet_house(planet)


def sign_of(ctx, planet: str) -> Optional[str]:
    return ctx.get_planet_sign(planet)


def lord_of_house(ctx, house: int) -> Optional[str]:
    return ctx.get_house_lord(house)


def houses_ruled_by(ctx, planet: str) -> List[int]:
    return ctx.get_houses_ruled_by(planet)


def is_kendra_house(house: int) -> bool:
    return house in KENDRA_HOUSES


def is_trikona_house(house: int) -> bool:
    return house in TRIKONA_HOUSES


def is_dusthana_house(house: int) -> bool:
    return house in DUSTHANA_HOUSES


def sambandha_kind(ctx, planet_a: str, planet_b: str):
    """Classify Parashari sambandha between two planets.

    Returns (kind, detail) where kind is one of:
    'conjunction' | 'mutual_aspect' | 'exchange' | 'none'.
    Conjunction = same whole-sign house OR within 8 deg orb.
    Mutual aspect = both aspect each other (Parashari special aspects).
    Exchange = mutual sign occupation.
    Single-sided aspect is NOT a sambandha (documented narrow choice).
    """
    if not planet_a or not planet_b or planet_a == planet_b:
        return "none", "same-or-missing planet"
    ha, hb = house_of(ctx, planet_a), house_of(ctx, planet_b)
    if ha is None or hb is None:
        return "none", "unknown house"
    if ha == hb or ctx.are_conjunct(planet_a, planet_b, 8.0):
        return "conjunction", f"same house {ha} / within orb"
    if ctx.is_exchange(planet_a, planet_b):
        sa, sb = sign_of(ctx, planet_a), sign_of(ctx, planet_b)
        return "exchange", f"{planet_a} in {sa}, {planet_b} in {sb}"
    ab = ctx.get_planet_aspecting_planet(planet_a, planet_b)
    ba = ctx.get_planet_aspecting_planet(planet_b, planet_a)
    if ab and ba:
        return "mutual_aspect", "mutual Parashari aspect"
    return "none", "no conjunction/aspect/exchange"


def lords_sambandha(ctx, house1: int, house2: int):
    """Sambandha between lords of two houses. Handles same-lord case.

    Returns (kind, lord1, lord2, detail). Same-lord returns
    ('same_lord', L, L, ...) so callers apply the kendra/trikona rule.
    """
    lord1, lord2 = lord_of_house(ctx, house1), lord_of_house(ctx, house2)
    if not lord1 or not lord2:
        return "none", lord1, lord2, "missing lord"
    if lord1 == lord2:
        return "same_lord", lord1, lord2, f"single lord {lord1} rules both"
    kind, detail = sambandha_kind(ctx, lord1, lord2)
    return kind, lord1, lord2, detail


def parivartana_pairs(ctx) -> List[Tuple[str, str]]:
    """All sign-exchange (Parivartana) pairs among seven planets + nodes excluded.

    Nodes have no lordship; exchanges only among Sun..Saturn.
    """
    pairs = []
    for i in range(len(SEVEN_PLANETS)):
        for j in range(i + 1, len(SEVEN_PLANETS)):
            a, b = SEVEN_PLANETS[i], SEVEN_PLANETS[j]
            if ctx.is_exchange(a, b):
                pairs.append((a, b))
    return pairs


def classify_parivartana(ctx, planet_a: str, planet_b: str) -> str:
    """Classify one exchange: DAINYA > KHALA > MAHA.

    DAINYA: either planet rules 6/8/12.
    KHALA: 3rd lord involved (and not Dainya).
    MAHA: otherwise (both rule Kendra/Trikona/2/11/1 houses).
    method=house_role (documented simplification).
    """
    ruled = set(houses_ruled_by(ctx, planet_a)) | set(houses_ruled_by(ctx, planet_b))
    if ruled & {6, 8, 12}:
        return "DAINYA"
    lord3 = lord_of_house(ctx, 3)
    if planet_a == lord3 or planet_b == lord3:
        return "KHALA"
    return "MAHA"


def moon_house(ctx) -> Optional[int]:
    return house_of(ctx, "Moon")


def house_from_moon(ctx, planet: str) -> Optional[int]:
    """House of planet counted from Moon: ((hp - hm) % 12) + 1."""
    hm, hp = moon_house(ctx), house_of(ctx, planet)
    if hm is None or hp is None:
        return None
    return ((hp - hm) % 12) + 1


def house_from_lagna(ctx, house: int) -> int:
    return house


def is_kendra_from_moon(ctx, planet: str) -> bool:
    hm, hp = moon_house(ctx), house_of(ctx, planet)
    if hm is None or hp is None:
        return False
    return ((hp - hm) % 12) in (0, 3, 6, 9)


def planets_in_house_from_moon(ctx, offset: int,
                               exclude: Tuple[str, ...] = ("Sun", "Rahu", "Ketu")) -> List[str]:
    """Planets in the house that is `offset` from Moon (1=with Moon)."""
    hm = moon_house(ctx)
    if hm is None:
        return []
    target = ((hm + offset - 2) % 12) + 1
    return [p for p in SEVEN_PLANETS
            if p not in exclude and house_of(ctx, p) == target]


def kendras_from_moon_houses(ctx) -> List[int]:
    hm = moon_house(ctx)
    if hm is None:
        return []
    return [((hm + d - 1) % 12) + 1 for d in (0, 3, 6, 9)]
