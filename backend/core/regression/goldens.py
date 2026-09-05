"""
Phase 10 — golden chart registry: 1 canonical + 12 synthetic ascendant
charts. Synthetic inputs are explicit (date/time/location); expected
ascendant signs established via the canonical pipeline at freeze time
(HISTORICAL_ACCEPTED) and re-verified on every run.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

GOLDEN_BIRTH = {
    "year": 2005, "month": 8, "day": 17, "hour": 0, "minute": 2, "second": 0,
    "lat": 16.93407, "lon": 81.95522, "tz_name": "Asia/Kolkata",
    "location_name": "Anaparthy", "country_name": "India",
}

# Synthetic ascendant sweep: same date/place, documented times.
# Expected signs/longitudes frozen from the canonical pipeline (see
# golden_data.json provenance HISTORICAL_ACCEPTED).
SYNTHETIC_ASCENDANTS = [
    {"chart_id": "SYN.ARIES", "hour": 22, "minute": 0, "expected_asc_sign": "Aries"},
    {"chart_id": "SYN.TAURUS", "hour": 0, "minute": 0, "expected_asc_sign": "Taurus"},
    {"chart_id": "SYN.GEMINI", "hour": 1, "minute": 30, "expected_asc_sign": "Gemini"},
    {"chart_id": "SYN.CANCER", "hour": 4, "minute": 0, "expected_asc_sign": "Cancer"},
    {"chart_id": "SYN.LEO", "hour": 6, "minute": 0, "expected_asc_sign": "Leo"},
    {"chart_id": "SYN.VIRGO", "hour": 8, "minute": 0, "expected_asc_sign": "Virgo"},
    {"chart_id": "SYN.LIBRA", "hour": 10, "minute": 0, "expected_asc_sign": "Libra"},
    {"chart_id": "SYN.SCORPIO", "hour": 12, "minute": 30, "expected_asc_sign": "Scorpio"},
    {"chart_id": "SYN.SAGITTARIUS", "hour": 14, "minute": 30, "expected_asc_sign": "Sagittarius"},
    {"chart_id": "SYN.CAPRICORN", "hour": 16, "minute": 30, "expected_asc_sign": "Capricorn"},
    {"chart_id": "SYN.AQUARIUS", "hour": 18, "minute": 30, "expected_asc_sign": "Aquarius"},
    {"chart_id": "SYN.PISCES", "hour": 20, "minute": 0, "expected_asc_sign": "Pisces"},
]


def registry_entries() -> List[Dict[str, Any]]:
    entries = [{"chart_id": "GOLDEN.TAURUS_CANONICAL", **{k: v for k, v in GOLDEN_BIRTH.items()},
                "expected_asc_sign": "Taurus",
                "provenance": "ASTROLIFE_V2_PHASE1_TEST_REPORT (accepted)"}]
    for s in SYNTHETIC_ASCENDANTS:
        entries.append({
            "chart_id": s["chart_id"], "year": 2005, "month": 8, "day": 17,
            "hour": s["hour"], "minute": s["minute"], "second": 0,
            "lat": 16.93407, "lon": 81.95522, "tz_name": "Asia/Kolkata",
            "location_name": "Anaparthy", "country_name": "India",
            "expected_asc_sign": s["expected_asc_sign"],
            "provenance": "HISTORICAL_ACCEPTED (frozen canonical run, Phase 10)",
        })
    return entries


def get_chart(chart_id: str) -> Optional[Dict[str, Any]]:
    for e in registry_entries():
        if e["chart_id"] == chart_id:
            return e
    return None
