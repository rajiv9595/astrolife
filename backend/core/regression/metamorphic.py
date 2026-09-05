"""
Phase 10 — metamorphic invariants (deterministic relations that must hold
for ANY input, independent of frozen goldens).
"""
from __future__ import annotations

from typing import Any, Callable, Dict


def ketu_opposition_delta(rahu_before: float, rahu_after: float,
                          ketu_before: float, ketu_after: float,
                          tol: float = 1e-9) -> bool:
    """If Rahu changes by D, Ketu must change by D (mod 360)."""
    d_rahu = (float(rahu_after) - float(rahu_before)) % 360.0
    d_ketu = (float(ketu_after) - float(ketu_before)) % 360.0
    return abs(d_rahu - d_ketu) <= tol


def rollover_preserved(sign_before: str, sign_after: str,
                       lon_before: float, lon_after: float) -> bool:
    from .boundaries import sign_from_longitude
    return (sign_from_longitude(lon_before) == sign_before
            and sign_from_longitude(lon_after) == sign_after)


def same_fingerprint(fp1: str, fp2: str) -> bool:
    return fp1 == fp2
