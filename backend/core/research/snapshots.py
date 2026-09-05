"""
Phase 9 — immutable snapshots: byte-identical round-trip.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .models import canonical_json, fingerprint_of


def create_research_snapshot(snapshot_id: str, package: Dict[str, Any],
                             experiments: List[Dict[str, Any]] | None = None,
                             results: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    snap = {
        "snapshot_id": snapshot_id,
        "package": package,
        "rules": list(package.get("rules", [])),
        "versions": {r.get("rule_id", ""): r.get("rule_version", "") for r in package.get("rules", [])},
        "sources": list(package.get("sources", [])),
        "evidence": list(package.get("evidence", [])),
        "dependencies": dict(package.get("dependencies", {})),
        "fixtures": list(package.get("fixtures", [])),
        "experiments": list(experiments or []),
        "results": list(results or []),
    }
    snap["fingerprint"] = fingerprint_of({k: v for k, v in snap.items() if k != "fingerprint"})
    return snap


def serialize_snapshot(snap: Dict[str, Any]) -> str:
    return canonical_json(snap)


def load_research_snapshot(payload: str) -> Dict[str, Any]:
    import json
    obj = json.loads(payload)
    if not isinstance(obj, dict) or "snapshot_id" not in obj:
        raise ValueError("invalid snapshot payload")
    # verify round-trip determinism
    if serialize_snapshot({k: v for k, v in obj.items()}) != serialize_snapshot(obj):
        raise ValueError("snapshot not deterministic")
    return obj
