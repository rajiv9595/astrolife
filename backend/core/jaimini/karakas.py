"""
Chara Karaka Engine — Astrolife V2 Phase 5D

Calculates deterministic Chara Karakas based on planetary degrees within their respective signs.
Supports 7-Karaka and 8-Karaka schemes, explicit Rahu conventions, deterministic tie-breaking,
and step-by-step mathematical evidence.
"""
from __future__ import annotations
import math
from typing import Dict, List, Tuple, Optional, Any

from ..calculation.models import ChartFacts, PlanetData
from .profile import JaiminiCalculationProfile, KarakaMethod, RahuKarakaMethod
from .models import KarakaItem, CharaKarakasReport


# ---------------------------------------------------------------------------
# Constants & Definitions
# ---------------------------------------------------------------------------

CHARA_7_KARAKA_ORDER: List[Tuple[str, str]] = [
    ("AK", "Atmakaraka"),
    ("AmK", "Amatyakaraka"),
    ("BK", "Bhratrukaraka"),
    ("MK", "Matrukaraka"),
    ("PK", "Putrakaraka"),
    ("GK", "Gnatikaraka"),
    ("DK", "Darakaraka"),
]

CHARA_8_KARAKA_ORDER: List[Tuple[str, str]] = [
    ("AK", "Atmakaraka"),
    ("AmK", "Amatyakaraka"),
    ("BK", "Bhratrukaraka"),
    ("MK", "Matrukaraka"),
    ("PiK", "Pitrukaraka"),
    ("PK", "Putrakaraka"),
    ("GK", "Gnatikaraka"),
    ("DK", "Darakaraka"),
]

CANONICAL_PLANET_ORDER: List[str] = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"
]

SEVEN_GRAHAS: List[str] = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"
]


def format_dms(deg_float: float) -> str:
    """Format decimal degrees to D° M' S.SS\" string."""
    d = int(deg_float)
    rem_m = (deg_float - d) * 60.0
    m = int(rem_m)
    s = (rem_m - m) * 60.0
    return f"{d}° {m:02d}' {s:05.2f}\""


def compute_intra_sign_degree(
    planet_name: str,
    sidereal_lon: float,
    rahu_method: RahuKarakaMethod
) -> float:
    """
    Calculate the degree of a planet inside its occupied sign (0.0 to 30.0).
    Rahu handling is dictated by the profile method.
    """
    deg_in_sign = float(sidereal_lon) % 30.0
    
    if planet_name == "Rahu":
        if rahu_method == RahuKarakaMethod.INVERSE_LONGITUDE:
            # Rahu retrograde convention: measured from end of sign (30 - deg)
            inv_deg = (30.0 - deg_in_sign) % 30.0
            return inv_deg
        elif rahu_method == RahuKarakaMethod.DIRECT_LONGITUDE:
            return deg_in_sign
        else:
            return deg_in_sign
            
    return deg_in_sign


def calculate_chara_karakas(
    chart_facts: ChartFacts,
    profile: Optional[JaiminiCalculationProfile] = None
) -> CharaKarakasReport:
    """
    Deterministically computes Chara Karakas from canonical ChartFacts.
    
    1. Selects candidate grahas according to profile (7 or 8 karakas).
    2. Measures intra-sign longitude (0-30°) for each graha.
    3. Handles Rahu according to declared RahuKarakaMethod.
    4. Sorts descending by intra-sign degree with deterministic tie-breaking.
    5. Maps ranks to Karaka roles (AK through DK / PiK).
    6. Emits structured evidence detailing intra-sign degrees and ranking.
    """
    if profile is None:
        profile = JaiminiCalculationProfile()
        
    karaka_method = profile.karaka_method
    rahu_method = profile.rahu_karaka_method
    tolerance = profile.float_tolerance
    
    # Determine active karaka scheme and candidate planets
    if karaka_method == KarakaMethod.EIGHT_KARAKA:
        karaka_scheme = CHARA_8_KARAKA_ORDER
        candidate_planets = list(CANONICAL_PLANET_ORDER)  # 7 grahas + Rahu
    else:
        karaka_scheme = CHARA_7_KARAKA_ORDER
        candidate_planets = list(SEVEN_GRAHAS)            # 7 visible grahas
        
    candidate_data: List[Dict[str, Any]] = []
    candidate_degrees: Dict[str, float] = {}
    evidence: List[str] = [
        f"Chara Karaka scheme: {karaka_method.value}",
        f"Rahu method: {rahu_method.value}",
        f"Float tie-breaking tolerance: {tolerance}"
    ]
    
    # Extract positions from ChartFacts
    for p_name in candidate_planets:
        pdata = chart_facts.planets.get(p_name)
        if pdata is None:
            continue
            
        sid_lon = float(pdata.longitude.sidereal)
        deg_in_sign = compute_intra_sign_degree(p_name, sid_lon, rahu_method)
        candidate_degrees[p_name] = deg_in_sign
        
        sign_name = pdata.sign.name
        sign_num = pdata.sign.id
        house_num = pdata.house
        
        candidate_data.append({
            "planet": p_name,
            "degree_in_sign": deg_in_sign,
            "formatted_degree": format_dms(deg_in_sign),
            "sign": sign_name,
            "sign_num": sign_num,
            "house": house_num,
            "canonical_rank": CANONICAL_PLANET_ORDER.index(p_name) if p_name in CANONICAL_PLANET_ORDER else 99
        })
        
        evidence.append(
            f"Planet {p_name}: sign={sign_name} ({sign_num}), intra-sign degree={deg_in_sign:.6f}° ({format_dms(deg_in_sign)})"
        )
        
    # Deterministic sorting:
    # Primary: degree_in_sign descending
    # Secondary: canonical planet precedence ascending (Sun before Moon, etc.) for ties within tolerance
    def sort_key(item: Dict[str, Any]) -> Tuple[float, int]:
        # Quantize degree within tolerance for tie detection
        # We invert degree for descending sort: -deg
        return (-round(item["degree_in_sign"] / tolerance) * tolerance, item["canonical_rank"])
    
    # Check for near-equal ties
    sorted_candidates = sorted(candidate_data, key=lambda x: x["degree_in_sign"], reverse=True)
    
    # Stable secondary tie resolution
    for i in range(len(sorted_candidates) - 1):
        d1 = sorted_candidates[i]["degree_in_sign"]
        d2 = sorted_candidates[i + 1]["degree_in_sign"]
        if abs(d1 - d2) <= tolerance:
            p1 = sorted_candidates[i]["planet"]
            p2 = sorted_candidates[i + 1]["planet"]
            r1 = CANONICAL_PLANET_ORDER.index(p1)
            r2 = CANONICAL_PLANET_ORDER.index(p2)
            if r1 > r2:
                # Swap to enforce canonical Graha precedence
                sorted_candidates[i], sorted_candidates[i + 1] = sorted_candidates[i + 1], sorted_candidates[i]
                evidence.append(
                    f"Tie detected between {p1} ({d1:.6f}°) and {p2} ({d2:.6f}°). Resolved by canonical Graha precedence: {p2} > {p1}."
                )
            else:
                evidence.append(
                    f"Tie detected between {p1} ({d1:.6f}°) and {p2} ({d2:.6f}°). Canonical Graha precedence confirmed: {p1} > {p2}."
                )

    karakas: Dict[str, KarakaItem] = {}
    ordering: List[str] = []
    planet_to_karaka: Dict[str, str] = {}
    
    evidence.append("--- Final Karaka Assignments ---")
    
    for idx, (code, full_name) in enumerate(karaka_scheme):
        if idx < len(sorted_candidates):
            cand = sorted_candidates[idx]
            p_name = cand["planet"]
            deg = cand["degree_in_sign"]
            item = KarakaItem(
                karaka_name=full_name,
                karaka_code=code,
                planet=p_name,
                degree_in_sign=deg,
                formatted_degree=cand["formatted_degree"],
                sign=cand["sign"],
                sign_num=cand["sign_num"],
                house=cand["house"],
                rank=idx + 1
            )
            karakas[code] = item
            ordering.append(code)
            planet_to_karaka[p_name] = code
            evidence.append(
                f"Rank {idx + 1}: {full_name} ({code}) = {p_name} at {deg:.6f}° ({cand['formatted_degree']}) in {cand['sign']}"
            )
            
    return CharaKarakasReport(
        method=karaka_method,
        rahu_method=rahu_method,
        karakas=karakas,
        ordering=ordering,
        planet_to_karaka=planet_to_karaka,
        candidate_degrees=candidate_degrees,
        evidence=evidence
    )
