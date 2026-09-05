"""
Phase 9 — hypotheses + research notebook. Observations stay
DEVELOPER_NOTE / RESEARCH_OBSERVATION, never canonical facts.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .models import HYPOTHESIS_STATUSES, fingerprint_of


def create_hypothesis(hypothesis_id: str, statement: str, **extra: Any) -> Dict[str, Any]:
    return {
        "hypothesis_id": hypothesis_id,
        "statement": statement,
        "assumptions": list(extra.get("assumptions", [])),
        "rule_ids": list(extra.get("rule_ids", [])),
        "evidence_ids": list(extra.get("evidence_ids", [])),
        "fixture_ids": list(extra.get("fixture_ids", [])),
        "expected_behavior": extra.get("expected_behavior", ""),
        "observed_behavior": extra.get("observed_behavior", ""),
        "status": extra.get("status", "OPEN"),
    }


def update_hypothesis(h: Dict[str, Any], observed: str, status: str) -> Dict[str, Any]:
    if status not in HYPOTHESIS_STATUSES:
        raise ValueError(f"bad hypothesis status {status!r}")
    out = dict(h)
    out["observed_behavior"] = observed
    out["status"] = status
    return out


def create_notebook(notebook_id: str, title: str = "", **extra: Any) -> Dict[str, Any]:
    nb = {
        "notebook_id": notebook_id,
        "title": title,
        "hypothesis": extra.get("hypothesis", ""),
        "objective": extra.get("objective", ""),
        "packages": list(extra.get("packages", [])),
        "rules": list(extra.get("rules", [])),
        "fixtures": list(extra.get("fixtures", [])),
        "experiments": list(extra.get("experiments", [])),
        "comparisons": list(extra.get("comparisons", [])),
        "observations": list(extra.get("observations", [])),
        "conflicts": list(extra.get("conflicts", [])),
        "conclusions": list(extra.get("conclusions", [])),
        "developer_notes": list(extra.get("developer_notes", [])),
        "provenance": dict(extra.get("provenance", {})),
    }
    # observations tagged research-only
    nb["observations"] = [{**o, "record_type": o.get("record_type", "RESEARCH_OBSERVATION")}
                          for o in nb["observations"]]
    nb["fingerprint"] = fingerprint_of({k: v for k, v in nb.items() if k != "fingerprint"})
    return nb
