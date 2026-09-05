"""
Phase 10 — golden end-to-end snapshot builder. Calls canonical pipelines
once, strips volatile fields, fingerprints. No prose generation.
"""
from __future__ import annotations

from typing import Any, Dict

from .fingerprints import snapshot_fingerprint


def build_end_to_end_snapshot(layers: Dict[str, Any]) -> Dict[str, Any]:
    snap = {"layers": layers}
    snap["fingerprint"] = snapshot_fingerprint(layers)
    return snap
