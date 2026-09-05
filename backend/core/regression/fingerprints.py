"""
Phase 10 — fingerprints. Canonical snapshots strip volatile fields
(timestamps, evaluated_at) before hashing. No timestamps in fingerprints.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .models import sha256_of

VOLATILE_KEYS = ("evaluated_at", "evaluation_datetime", "generated_at",
                 "timestamp", "run_id", "execution_fingerprint")


def strip_volatile(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: strip_volatile(v) for k, v in sorted(obj.items()) if k not in VOLATILE_KEYS}
    if isinstance(obj, list):
        return [strip_volatile(v) for v in obj]
    return obj


def snapshot_fingerprint(obj: Any) -> str:
    return sha256_of(strip_volatile(obj))


def fingerprint_mapping(mapping: Dict[str, Any]) -> Dict[str, str]:
    return {k: snapshot_fingerprint(v) for k, v in sorted(mapping.items())}
