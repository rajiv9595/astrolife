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
            "sthana_bala": round(float(getattr(sthana, "total", 0.0) or 0.0), 1),
            "dig_bala": round(float(getattr(dig_bala, "value", 0.0) or 0.0), 1),
            "kaala_bala": round(float(getattr(kala, "total", 0.0) or 0.0), 1),
            "chesta_bala": round(float(getattr(chesta, "value", 0.0) or 0.0), 1),
            "naisargika_bala": round(float(getattr(naisargika, "value", 0.0) or 0.0), 1),
            "drig_bala": round(float(getattr(drig, "value", 0.0) or 0.0), 1),
            "total_virupas": getattr(result, "total_virupas", None),
            "total_rupas": getattr(result, "total_rupas", None),
            "minimum_rupas": getattr(result, "minimum_rupas", None),
            "ratio": getattr(result, "ratio", None),
            "status": status,
            "strength_level": STATUS_LEVEL.get(status, "Low"),
        }

    return payload
