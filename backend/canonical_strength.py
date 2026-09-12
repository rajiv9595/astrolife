"""
Production adapter: canonical Phase 4 strength -> UI response shapes.

NO ASTROLOGY IS COMPUTED HERE. Every number in the rows below originates
from the canonical engine (backend/core/strength/shadbala.py and
backend/core/strength/dignity.py). This module only projects canonical
ShadbalaResult / DignityResult fields into the response keys historically
consumed by the frontend (`strengths[]` rows and the `shadbala` dict).

Authoritative calculation: backend.core.strength.shadbala.calculate_all_shadbala
"""

from typing import Any, Dict, List

CLASSICAL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
NODES = ["Rahu", "Ketu"]


def _num(value: Any, digits: int = 4) -> Any:
    """Round numeric values for stable JSON output; pass through the rest."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return round(float(value), digits)
    return value


def _source_tag() -> str:
    return "canonical"


def _enum(value: Any, default: Any = None) -> Any:
    """Serialize enums to their values (e.g. StrengthClassification.CLASSICAL
    becomes 'CLASSICAL'); pass anything else through."""
    if value is None:
        return default
    return getattr(value, "value", value)

# Canonical DignityResult.dignity -> UI nature badge text.
DIGNITY_DISPLAY = {
    "EXALTED": "Exalted",
    "MOOLATRIKONA": "Moolatrikona",
    "OWN_SIGN": "Own Sign",
    "FRIEND": "Friend Sign",
    "NEUTRAL": "Neutral",
    "ENEMY": "Enemy Sign",
    "DEBILITATED": "Debilitated",
}

# Canonical ShadbalaResult.strength_status -> UI strength label.
STATUS_LABEL = {"STRONG": "Strong", "MODERATE": "Moderate", "WEAK": "Weak"}

# Canonical status -> legacy ShadbalaCard badge levels (card unchanged).
STATUS_LEVEL = {"STRONG": "High", "MODERATE": "Medium", "WEAK": "Low"}


def build_strength_rows(shadbala: Dict[str, Any], dignity: Dict[str, Any],
                        chart_planets: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build frontend `strengths[]` rows from canonical results.

    shadbala: planet -> ShadbalaResult (canonical, 7 classical planets).
    dignity:  planet -> DignityResult (canonical).
    chart_planets: legacy chart_data["planets"] dict, used ONLY to read the
        D1 sign names of Rahu/Ketu for their informational rows. No legacy
        strength numbers are used.
    """
    rows: List[Dict[str, Any]] = []

    for planet in CLASSICAL_PLANETS:
        result = shadbala.get(planet)
        if result is None:
            continue
        dig = dignity.get(planet)

        dignity_code = getattr(dig, "dignity", "NEUTRAL") if dig is not None else "NEUTRAL"
        sign = getattr(dig, "sign", "") if dig is not None else ""
        ruler = getattr(dig, "ruler", "") if dig is not None else ""
        nature = DIGNITY_DISPLAY.get(dignity_code, "Neutral")

        status = getattr(result, "strength_status", None)
        label = STATUS_LABEL.get(status, "Moderate")
        total_rupas = float(getattr(result, "total_rupas", 0.0) or 0.0)
        minimum_rupas = getattr(result, "minimum_rupas", None)
        ratio = getattr(result, "ratio", None)

        sthana = getattr(result, "sthana_bala", None)
        dig_bala = getattr(result, "dig_bala", None)
        kala = getattr(result, "kala_bala", None)
        chesta = getattr(result, "chesta_bala", None)
        naisargika = getattr(result, "naisargika_bala", None)
        drig = getattr(result, "drig_bala", None)

        reasons = [
            f"{nature} in {sign} (lord {ruler})" if sign else f"Dignity: {nature}",
            f"Sthana Bala {getattr(sthana, 'total', 0.0):.1f} Virupas",
            f"Dig Bala {getattr(dig_bala, 'value', 0.0):.1f} Virupas",
            f"Kala Bala {getattr(kala, 'total', 0.0):.1f} Virupas",
            f"Chesta Bala {getattr(chesta, 'value', 0.0):.1f} Virupas",
            f"Naisargika Bala {getattr(naisargika, 'value', 0.0):.1f} Virupas",
            f"Drig Bala {getattr(drig, 'value', 0.0):.1f} Virupas",
            f"Shadbala total {total_rupas:.2f} Rupas"
            + (f" (minimum {minimum_rupas}, ratio {ratio})"
               if minimum_rupas is not None and ratio is not None else ""),
        ]

        rows.append({
            "planet": planet,
            "nature": nature,
            "label": label,
            "score": round(total_rupas, 2),
            "score_unit": "rupas",
            "ratio": ratio,
            "minimum_rupas": minimum_rupas,
            "status": status,
            "reasons": reasons,
        })

    # Rahu/Ketu: classical Shadbala intentionally applies only to the seven
    # classical planets. Show explicit non-evaluation instead of scores.
    for node in NODES:
        node_data = (chart_planets or {}).get(node, {}) or {}
        node_sign = node_data.get("sign_manual") or node_data.get("sign") or ""
        rows.append({
            "planet": node,
            "nature": "Shadow Node",
            "label": "Not Evaluated",
            "score": None,
            "score_unit": "rupas",
            "ratio": None,
            "minimum_rupas": None,
            "status": "NOT_EVALUATED",
            "reasons": [
                "Classical Shadbala applies to the seven classical planets (Sun-Saturn).",
                "Rahu/Ketu are shadow nodes and are not evaluated by the canonical Phase 4 engine.",
                f"D1 sign: {node_sign}." if node_sign else "D1 sign unavailable.",
            ],
        })

    return rows


def build_shadbala_payload(shadbala: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Build the `shadbala` response dict from canonical results.

    Keys intentionally mirror the legacy payload consumed by ShadbalaCard
    (strength_level High/Medium/Low, flat component Virupas, total_rupas),
    with canonical ratio/minimum/status added.
    """
    payload: Dict[str, Dict[str, Any]] = {}

    for planet in CLASSICAL_PLANETS:
        result = shadbala.get(planet)
        if result is None:
            continue

        sthana = getattr(result, "sthana_bala", None)
        dig_bala = getattr(result, "dig_bala", None)
        kala = getattr(result, "kala_bala", None)
        chesta = getattr(result, "chesta_bala", None)
        naisargika = getattr(result, "naisargika_bala", None)
        drig = getattr(result, "drig_bala", None)
        status = getattr(result, "strength_status", None)

        payload[planet] = {
            "sthana_bala": round(float(getattr(sthana, 'total', 0.0) or 0.0), 1),
            "dig_bala": round(float(getattr(dig_bala, 'value', 0.0) or 0.0), 1),
            "kaala_bala": round(float(getattr(kala, 'total', 0.0) or 0.0), 1),
            "chesta_bala": round(float(getattr(chesta, 'value', 0.0) or 0.0), 1),
            "naisargika_bala": round(float(getattr(naisargika, 'value', 0.0) or 0.0), 1),
            "drig_bala": round(float(getattr(drig, 'value', 0.0) or 0.0), 1),
            "total_virupas": getattr(result, "total_virupas", None),
            "total_rupas": getattr(result, "total_rupas", None),
            "minimum_rupas": getattr(result, "minimum_rupas", None),
            "ratio": getattr(result, "ratio", None),
            "status": status,
            "strength_level": STATUS_LEVEL.get(status, "Low"),
        }

    return payload


def build_bhava_bala_payload(bhava_bala: Dict[Any, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Project canonical BhavaBalaResult per house. No astrology; pure projection.
    Keys are strings for JSON stability.
    """
    payload: Dict[str, Dict[str, Any]] = {}

    for house, result in (bhava_bala or {}).items():
        payload[str(house)] = {
            "house": getattr(result, "house", house),
            "sign": getattr(result, "sign", None),
            "system": _enum(getattr(result, "system", None), "BHAVA_BALA"),
            "method": getattr(result, "method", None),
            "classification": _enum(getattr(result, "classification", None), ""),
            "bhavadhipati_bala": _num(getattr(result, "bhavadhipati_bala", None)),
            "dig_bala": _num(getattr(result, "dig_bala", None)),
            "drishti_bala": _num(getattr(result, "drishti_bala", None)),
            "total": _num(getattr(result, "total", None)),
            "maximum": _num(getattr(result, "maximum", None)),
            "unit": getattr(result, "unit", "virupas"),
            "_source": _source_tag(),
        }

    return payload


def build_vimsopaka_payload(vimsopaka: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Project canonical VimsopakaBalaResult per planet, preserving the weighted
    per-varga contributions as evidence. No astrology; pure projection.
    """
    payload: Dict[str, Dict[str, Any]] = {}

    for planet, result in (vimsopaka or {}).items():
        contributions = getattr(result, "varga_contributions", []) or []
        payload[planet] = {
            "planet": planet,
            "system": _enum(getattr(result, "system", None), "VIMSOPAKA"),
            "method": getattr(result, "method", None),
            "classification": _enum(getattr(result, "classification", None), ""),
            "score": _num(getattr(result, "score", None)),
            "maximum": _num(getattr(result, "maximum", 20.0)),
            "ratio": _num(getattr(result, "ratio", None)),
            "vargas_used": list(getattr(result, "vargas_used", []) or []),
            "weights": {str(k): _num(v) for k, v in
                        dict(getattr(result, "weights", {}) or {}).items()},
            "varga_contributions": [
                {"varga": c.get("varga"),
                 "sign": c.get("sign"),
                 "dignity_score": _num(c.get("dignity_score")),
                 "weight": _num(c.get("weight")),
                 "weighted_score": _num(c.get("weighted_score"))}
                for c in contributions
            ],
            "_source": _source_tag(),
        }

    return payload


def build_avastha_payload(avastha: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Project canonical AvasthaResult systems per planet. Whatever systems the
    canonical profile enabled are passed through unchanged (default: Bala).
    """
    payload: Dict[str, Dict[str, Any]] = {}

    for planet, systems in (avastha or {}).items():
        planet_entry: Dict[str, Any] = {}
        for system_name, result in (systems or {}).items():
            planet_entry[str(system_name)] = {
                "avastha_name": getattr(result, "avastha_name", None),
                "avastha_index": getattr(result, "avastha_index", None),
                "degree_range": getattr(result, "degree_range", None),
                "description": getattr(result, "description", ""),
                "method": getattr(result, "method", None),
                "classification": _enum(getattr(result, "classification", None), ""),
            }
        planet_entry["_source"] = _source_tag()
        payload[planet] = planet_entry

    return payload


def build_functional_payload(functional_strength: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Project canonical FunctionalStrengthResult per planet. Functional nature
    stays distinct from natural benefic/malefic, dignity, and Shadbala.
    """
    payload: Dict[str, Dict[str, Any]] = {}

    for planet, result in (functional_strength or {}).items():
        lordship = getattr(result, "lordship", {}) or {}
        payload[planet] = {
            "planet": planet,
            "system": _enum(getattr(result, "system", None), "PARASHARI_FUNCTIONAL"),
            "method": getattr(result, "method", None),
            "classification": _enum(getattr(result, "classification", None), ""),
            "functional_nature": getattr(result, "functional_nature", ""),
            "yogakaraka": bool(getattr(result, "yogakaraka", False)),
            "houses_ruled": list((lordship.get("houses_ruled", [])
                                  if isinstance(lordship, dict) else [])),
            "ascendant": lordship.get("ascendant") if isinstance(lordship, dict) else None,
            "kendra_trikona": bool(getattr(result, "kendra_trikona", False)),
            "dusthana_lord": bool(getattr(result, "dusthana_lord", False)),
            "maraka": bool(getattr(result, "maraka", False)),
            "score": _num(getattr(result, "score", None)),
            "details": list(getattr(result, "details", []) or []),
            "_source": _source_tag(),
        }

    return payload


def build_composite_payload(composite: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Project the canonical Astrolife CUSTOM composite per planet. The custom
    method and disclaimer travel with every entry; composite is never merged
    into Shadbala.
    """
    payload: Dict[str, Dict[str, Any]] = {}

    for planet, result in (composite or {}).items():
        payload[planet] = {
            "planet": planet,
            "system": _enum(getattr(result, "system", None), "ASTROLIFE_COMPOSITE"),
            "method": getattr(result, "method", "ASTROLIFE_CUSTOM"),
            "classification": _enum(getattr(result, "classification", None), ""),
            "score": _num(getattr(result, "score", None), 1),
            "label": getattr(result, "label", ""),
            "nature": getattr(result, "nature", ""),
            "reasons": list(getattr(result, "reasons", []) or []),
            "components": {str(k): _num(v) for k, v in
                           dict(getattr(result, "components", {}) or {}).items()},
            "disclaimer": getattr(result, "disclaimer", ""),
            "_source": _source_tag(),
        }

    return payload
