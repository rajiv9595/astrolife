"""
Phase 10 — boundary matrix helpers. Structural expectations (index range,
sign validity, determinism, EPSILON stability) plus frozen-sign lookup
against golden_data.json. Never changes accepted EPSILON semantics.
"""
from __future__ import annotations

from typing import Any, Dict, List

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def sign_from_longitude(longitude: float) -> str:
    lon = float(longitude) % 360.0
    return SIGNS[int(lon // 30.0) % 12]


def check_index_range(division: int, idx: int) -> bool:
    return 0 <= idx < division


def check_sign_valid(sign: str) -> bool:
    return sign in SIGNS
