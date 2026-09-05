"""
Phase 9 — comparison engine: side-by-side techniques/versions with
deterministic diffs. Never declares a winner automatically.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .experiments import evaluate_fixture
from .models import fingerprint_of


def compare_research_rules(comparison_id: str, rules: List[Dict[str, Any]],
                           fixtures: List[Dict[str, Any]], profile: str = "") -> Dict[str, Any]:
    techniques: List[Dict[str, Any]] = []
    for r in sorted(rules, key=lambda x: (x.get("rule_id", ""), x.get("rule_version", ""))):
        outs = [evaluate_fixture(r, fx) for fx in sorted(fixtures, key=lambda f: f.get("fixture_id", ""))]
        techniques.append({
            "technique_id": r.get("rule_id"),
            "version": r.get("rule_version"),
            "tradition": r.get("tradition"),
            "profile": profile,
            "fixtures_tested": len(outs),
            "formed": sum(1 for o in outs if o["formation"] == "FORMED"),
            "not_formed": sum(1 for o in outs if o["formation"] == "NOT_FORMED"),
            "unknown": sum(1 for o in outs if o["formation"] == "UNKNOWN"),
            "conflicted": 0,
            "timing_matches": 0,
            "timing_mismatches": 0,
            "source_state": "UNVERIFIED",
            "evidence_state": "UNVERIFIED",
            "dependency_state": "RESOLVED",
        })
    out = {"comparison_id": comparison_id, "techniques": techniques,
           "fixture_set": sorted([f.get("fixture_id", "") for f in fixtures])}
    out["fingerprint"] = fingerprint_of(out)
    return out


def diff_rule_versions(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    diff: Dict[str, Any] = {"rule_id": old.get("rule_id")}
    for k in ("formation", "cancellation", "mitigation", "activation",
              "dependencies", "applicability", "evidence_requirements", "timing_applicability"):
        if (old.get(k) or None) != (new.get(k) or None):
            diff[f"changed_{k}"] = {"old": old.get(k), "new": new.get(k)}
    diff["version_change"] = [old.get("rule_version"), new.get("rule_version")]
    return diff


def detect_conflicts(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_fx: Dict[str, set] = {}
    for r in results:
        for o in r.get("outcomes", []):
            by_fx.setdefault(o.get("fixture_id", ""), set()).add(o.get("formation"))
    return [{"fixture_id": fx, "formations": sorted(v), "state": "CONTESTED"}
            for fx, v in sorted(by_fx.items()) if len(v) > 1]
