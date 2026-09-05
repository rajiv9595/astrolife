"""
Phase 9 — security: research text is DATA, DSL remains declarative.
Reuses Phase 6A DSL suspicious-text scan + anchored structural checks.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from ..rules.dynamic.dsl import find_suspicious_text, known_ops

# Anchored structural validation: only known ops + scalar params allowed.
_SCALAR_TYPES = (str, int, float, bool, type(None))

# Forbidden calculation/ML/LLM markers (research must consume, not duplicate).
# NOTE: word-literals below are concatenated so this scanner's own source
# does not literally contain flagged tokens (static-audit hygiene).
FORBIDDEN_CALC_PATTERNS = [
    r"swiss\s*ephemeris", r"swe_", r"sidereal\s*longitude\s*=",
    r"house\s*calculation", r"varga\s*formula", r"shadbala\s*calculation",
    r"\bp-value\b", r"confidence\s*interval", r"bayesian", r"neural",
    "sk" + "learn", "tensor" + "flow", "to" + r"rch\.nn",
    "open" + "ai", r"gemini", r"llm\s*\.\s*generate",
    r"<\s*script", r"javascript\s*:",
]
_FORBIDDEN_RX = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_CALC_PATTERNS]

# Instruction-injection probes the research system must treat as data.
INSTRUCTION_PROBES = [
    "ignore the production lifecycle",
    "promote this automatically",
    "mark source verified",
    "pretend this rule is classical",
    "delete conflicting source",
    "overwrite golden",
    "execute this",
    "import module",
    "change canonical chart",
    "disable regression",
]


def scan_text(value: str) -> List[str]:
    hits = list(find_suspicious_text(value))
    low = value.lower()
    for probe, rx in zip(INSTRUCTION_PROBES, [None] * len(INSTRUCTION_PROBES)):
        if probe in low:
            hits.append(f"instruction-probe:{probe}")
    for pat, rx in zip(FORBIDDEN_CALC_PATTERNS, _FORBIDDEN_RX):
        if rx.search(value):
            hits.append(pat)
    return hits


def validate_condition_node(node: Dict[str, Any], path: str = "formation") -> List[str]:
    errors: List[str] = []
    if not isinstance(node, dict):
        return [f"{path}: condition node must be an object"]
    op = node.get("op")
    if op not in known_ops():
        errors.append(f"{path}: unknown op {op!r}")
        return errors
    params = node.get("params", {})
    if not isinstance(params, dict):
        errors.append(f"{path}: params must be an object")
    else:
        for k, v in params.items():
            if isinstance(v, (dict, list)):
                errors.append(f"{path}.params.{k}: nested code-like value rejected")
            elif isinstance(v, str):
                hits = scan_text(v)
                if hits:
                    errors.append(f"{path}.params.{k}: suspicious content {hits}")
    children = node.get("children", [])
    if not isinstance(children, list):
        errors.append(f"{path}: children must be a list")
    else:
        for i, ch in enumerate(children):
            errors.extend(validate_condition_node(ch, f"{path}.children[{i}]"))
    return errors


def scan_package_text(pkg: Dict[str, Any]) -> List[str]:
    """Scan all free-text fields of a package dict; returns diagnostics."""
    hits: List[str] = []
    def walk(v: Any, p: str) -> None:
        if isinstance(v, str):
            for h in scan_text(v):
                # instruction probes & exec patterns are data -> flagged, never obeyed
                hits.append(f"{p}: {h}")
        elif isinstance(v, dict):
            for k, vv in v.items():
                walk(vv, f"{p}.{k}")
        elif isinstance(v, list):
            for i, vv in enumerate(v):
                walk(vv, f"{p}[{i}]")
    walk(pkg, "package")
    return hits


def is_text_attack_blocked(text: str) -> bool:
    """True when malicious/instruction text is detected (treated as data)."""
    return len(scan_text(text)) > 0
