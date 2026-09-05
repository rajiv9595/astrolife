"""
Phase 8 — 6E catalogue bridge (read-only).

Resolves exact rule versions for ancestry/verification metadata and filters
applicability. The catalogue is never mutated; snapshots seal every run.
"""
from __future__ import annotations

from typing import Any, Dict, List


def catalogue_rule_versions(rule_ids: List[str]) -> Dict[str, Dict[str, str]]:
    """Exact-version metadata for supplied outcomes (reproducibility, §54)."""
    from core.rules.dynamic.knowledge import get_rule_catalogue
    catalogue = get_rule_catalogue()
    meta: Dict[str, Dict[str, str]] = {}
    for rule_id in sorted(set(rule_ids)):
        entry = catalogue.get_rule(rule_id)
        if entry is None:
            continue
        meta[rule_id] = {"rule_version": entry.rule_version,
                         "tradition": entry.tradition,
                         "lifecycle_status": entry.lifecycle_status,
                         "verification": entry.provenance_status,
                         "depends_on": sorted(
                             (entry.dependency_manifest or {}).get("input_facts", []))}
    return meta


def catalogue_snapshot_fingerprint() -> str:
    from core.rules.dynamic.knowledge import get_catalogue_snapshot, get_rule_catalogue
    return get_catalogue_snapshot(get_rule_catalogue()).fingerprint()
