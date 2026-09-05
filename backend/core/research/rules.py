"""
Phase 9 — research rules: declarative authoring reusing Phase 6A DSL ops.
research://package/rule/version namespace, never production://.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..rules.dynamic.dsl import known_ops
from .models import RESEARCH_STATUSES, RESEARCH_TRADITIONS, fingerprint_of
from .security import validate_condition_node
from .validation import validate_research_rule

_STORE: Dict[str, Dict[str, Any]] = {}


def research_uri(package_id: str, rule_id: str, version: str) -> str:
    return f"research://{package_id}/{rule_id}/{version}"


def create_research_rule(rule_id: str, rule_version: str = "0.1.0",
                         tradition: str = "EXPERIMENTAL", category: str = "CUSTOM",
                         formation: Optional[Dict[str, Any]] = None,
                         **extra: Any) -> Dict[str, Any]:
    rule: Dict[str, Any] = {
        "rule_id": rule_id,
        "rule_version": rule_version,
        "rule_name": extra.get("rule_name", rule_id),
        "description": extra.get("description", ""),
        "tradition": tradition,
        "category": category,
        "formation": formation or {"op": "planet_in_sign", "params": {"planet": "Jupiter", "sign": "Pisces"}},
        "cancellation": extra.get("cancellation"),
        "mitigation": extra.get("mitigation"),
        "activation": extra.get("activation"),
        "applicability": extra.get("applicability", {"traditions": [tradition]}),
        "dependencies": extra.get("dependencies", {"input_facts": []}),
        "evidence_requirements": list(extra.get("evidence_requirements", ["formation_evidence"])),
        "event_applicability": list(extra.get("event_applicability", [])),
        "timing_applicability": dict(extra.get("timing_applicability", {})),
        "lifecycle_status": extra.get("lifecycle_status", "EXPERIMENTAL"),
    }
    _STORE[f"{rule_id}@{rule_version}"] = rule
    return rule


def validate_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    ok, errors = validate_research_rule(rule)
    return {"valid": ok, "errors": errors, "fingerprint": fingerprint_of(rule)}


def get_research_rule(rule_id: str, rule_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if rule_version:
        return _STORE.get(f"{rule_id}@{rule_version}")
    cands = [(k, v) for k, v in _STORE.items() if k.startswith(rule_id + "@")]
    if not cands:
        return None
    return sorted(cands)[-1][1]


def get_research_version(rule_id: str, rule_version: str) -> Optional[Dict[str, Any]]:
    return _STORE.get(f"{rule_id}@{rule_version}")


def list_research_rules() -> List[Dict[str, Any]]:
    return sorted(_STORE.values(), key=lambda r: (r.get("rule_id", ""), r.get("rule_version", "")))


def rule_fingerprint(rule: Dict[str, Any]) -> str:
    return fingerprint_of(rule)


def clear_store() -> None:
    _STORE.clear()
