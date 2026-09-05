"""
Phase 5E — reusable Jaimini yoga predicates.

Pure functions over canonical inputs only:
ChartFacts (D1 signs/houses) + JaiminiFacts (5D engine) + varga facts (D9).
No independent astronomical computation, no Parashari aspects, no timestamps.

Sign lords: Jaimini-owned CLASSICAL_SIGN_LORDS (identical values to the
Parashari table, kept inside the Jaimini package to avoid cross-tradition
coupling). House-frame tuples and natural benefic/malefic sets are imported
from ...rules.parashari.structural (single source, attributed here).
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from ...rules.parashari.structural import (  # noqa: F401  (re-exported single source)
    KENDRA_HOUSES,
    TRIKONA_HOUSES,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
    SEVEN_PLANETS,
)

from ..arudha import CLASSICAL_SIGN_LORDS, SIGNS
from ..rashi_drishti import get_sign_rashi_drishti


# ---------------------------------------------------------------------------
# D1 accessors (ChartFacts)
# ---------------------------------------------------------------------------

def d1_sign_of(chart_facts: Any, planet: str) -> Optional[str]:
    pdata = chart_facts.planets.get(planet)
    return pdata.sign.name if pdata is not None else None


def d1_house_of(chart_facts: Any, planet: str) -> Optional[int]:
    pdata = chart_facts.planets.get(planet)
    return pdata.house if pdata is not None else None


def planets_in_d1_sign(chart_facts: Any, sign: str) -> List[str]:
    out = []
    for pname, pdata in chart_facts.planets.items():
        if pdata.sign.name == sign:
            out.append(pname)
    return sorted(out)


# ---------------------------------------------------------------------------
# D9 accessors (varga facts; VargaPosition or dict form)
# ---------------------------------------------------------------------------

def _varga_sign(varga_entry: Any) -> Optional[str]:
    if varga_entry is None:
        return None
    if isinstance(varga_entry, dict):
        return varga_entry.get("sign")
    return getattr(varga_entry, "sign", None)


def d9_sign_of(varga_facts: Dict[str, Any], planet: str) -> Optional[str]:
    planets = (varga_facts or {}).get("planets", {})
    return _varga_sign((planets.get(planet) or {}).get("D9"))


def d9_lagna_sign(varga_facts: Dict[str, Any]) -> Optional[str]:
    asc = (varga_facts or {}).get("ascendant", {})
    return _varga_sign(asc.get("D9"))


def planets_in_d9_sign(chart_facts: Any, varga_facts: Dict[str, Any], sign: str) -> List[str]:
    out = []
    for pname in chart_facts.planets.keys():
        if d9_sign_of(varga_facts, pname) == sign:
            out.append(pname)
    return sorted(out)


# ---------------------------------------------------------------------------
# Karaka accessors (JaiminiFacts)
# ---------------------------------------------------------------------------

def karaka_planet(jaimini_facts: Any, code: str) -> Optional[str]:
    item = jaimini_facts.chara_karakas.karakas.get(code)
    return item.planet if item is not None else None


def karaka_sign(jaimini_facts: Any, code: str) -> Optional[str]:
    item = jaimini_facts.chara_karakas.karakas.get(code)
    return item.sign if item is not None else None


def karaka_degree(jaimini_facts: Any, code: str) -> Optional[float]:
    item = jaimini_facts.chara_karakas.karakas.get(code)
    return item.degree_in_sign if item is not None else None


def karaka_identity_tied(
    jaimini_facts: Any, codes: List[str], tolerance: float
) -> Tuple[bool, str]:
    """Structural cancellation check: karaka ranking uncertain when the
    involved intra-sign degrees fall within tolerance."""
    degs = [(c, karaka_degree(jaimini_facts, c)) for c in codes]
    degs = [(c, d) for c, d in degs if d is not None]
    for i in range(len(degs) - 1):
        (c1, d1), (c2, d2) = degs[i], degs[i + 1]
        if abs(d1 - d2) <= tolerance:
            return True, (
                f"Karaka identity uncertain: {c1} ({d1:.6f}°) and {c2} "
                f"({d2:.6f}°) within tolerance {tolerance}."
            )
    detail = ", ".join(f"{c}={d:.4f}°" for c, d in degs)
    return False, f"Karaka identities distinct beyond tolerance: {detail}."


# ---------------------------------------------------------------------------
# Sign-frame math (whole-sign, deterministic)
# ---------------------------------------------------------------------------

def house_of_sign_from(sign: str, ref_sign: str) -> int:
    """House number of `sign` counted from `ref_sign` (1-12)."""
    return ((SIGNS.index(sign) - SIGNS.index(ref_sign)) % 12) + 1


def is_kendra_from(sign: str, ref_sign: str) -> bool:
    return house_of_sign_from(sign, ref_sign) in KENDRA_HOUSES


def is_kendra_or_trikona_from(sign: str, ref_sign: str) -> bool:
    return house_of_sign_from(sign, ref_sign) in (set(KENDRA_HOUSES) | set(TRIKONA_HOUSES))


def sign_lord(sign: str) -> str:
    return CLASSICAL_SIGN_LORDS[sign]


# ---------------------------------------------------------------------------
# Rashi Drishti predicates (Phase 5D engine only)
# ---------------------------------------------------------------------------

def signs_in_mutual_drishti(sign_a: str, sign_b: str) -> bool:
    if sign_a == sign_b:
        return False
    return sign_b in get_sign_rashi_drishti(sign_a) and sign_a in get_sign_rashi_drishti(sign_b)


def planet_aspects_sign(jaimini_facts: Any, planet: str, sign: str) -> bool:
    return sign in (jaimini_facts.rashi_drishti.planet_aspects.get(planet) or [])


def planets_aspecting_sign(jaimini_facts: Any, sign: str) -> List[str]:
    """Planets whose occupied sign casts Rashi Drishti on `sign` (D1 scope)."""
    out = []
    for pname, aspects in jaimini_facts.rashi_drishti.planet_aspects.items():
        if sign in (aspects or []):
            out.append(pname)
    return sorted(out)


# ---------------------------------------------------------------------------
# Shared mitigation helper (D1 scope)
# ---------------------------------------------------------------------------

def benefic_support_for_sign(
    chart_facts: Any, jaimini_facts: Any, sign: str
) -> Tuple[bool, str]:
    """Supporting benefic influence on a D1 sign via occupancy or Rashi
    Drishti. Recorded as PARTIAL mitigation only; never affects formation."""
    occupants = [p for p in planets_in_d1_sign(chart_facts, sign) if p in NATURAL_BENEFICS]
    aspecters = [p for p in planets_aspecting_sign(jaimini_facts, sign) if p in NATURAL_BENEFICS]
    if occupants or aspecters:
        return True, (
            f"Supporting benefic influence on {sign}: occupants={occupants or 'none'}, "
            f"Rashi-Drishti aspecters={aspecters or 'none'}."
        )
    return False, f"No benefic occupancy or Rashi Drishti on {sign}."
