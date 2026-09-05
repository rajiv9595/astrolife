"""
Phase 6C — Deterministic package fingerprint.

Fingerprint depends ONLY on canonical semantic content. Excludes:
  - timestamps
  - memory addresses
  - random IDs
  - machine-specific paths

Same package → same fingerprint. Modified package → different fingerprint.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from .rule_package import RulePackage


def compute_fingerprint(package: RulePackage) -> str:
    """Compute a deterministic fingerprint for a RulePackage.

    The fingerprint is derived from canonical semantic content only.
    No timestamps, no random IDs, no memory addresses, no machine-specific paths.

    Same package → same fingerprint. Modified package → different fingerprint.
    """
    canonical = package.to_canonical_dict()
    s = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def fingerprints_match(pkg1: RulePackage, pkg2: RulePackage) -> bool:
    """Check whether two RulePackages have the same fingerprint."""
    return compute_fingerprint(pkg1) == compute_fingerprint(pkg2)


def fingerprint_from_dict(data: Dict[str, Any]) -> str:
    """Compute fingerprint from a canonical dict (e.g. deserialized JSON)."""
    s = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()