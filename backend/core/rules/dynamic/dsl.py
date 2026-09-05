"""
Phase 6A — safe declarative condition DSL.

Data-only trees. No eval/exec/lambda/import/shell. Suspicious payloads are
rejected by pattern scan (validators) and never executed (evaluator only
reads op/params/children of known primitives).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

LOGICAL_OPS = {"ALL", "ANY", "NOT", "EXACTLY_N", "AT_LEAST_N", "AT_MOST_N"}

PRIMITIVES: Dict[str, List[str]] = {
    "planet_in_sign": ["planet", "sign"],
    "planet_in_house": ["planet", "house"],
    "planet_in_varga_sign": ["planet", "varga", "sign"],
    "planet_owns_house": ["planet", "house"],
    "planets_conjunct": ["a", "b"],
    "planets_aspect": ["a", "b"],
    "rashi_drishti": ["from_sign", "to_sign"],
    "karaka_equals": ["karaka", "planet"],
    "pada_equals": ["house", "sign"],
    "planet_exalted": ["planet"],
    "planet_debilitated": ["planet"],
    "planet_in_own_sign": ["planet"],
    "planet_in_moolatrikona": ["planet"],
    "house_is_kendra": ["house"],
    "house_is_trikona": ["house"],
    "lord_in_house": ["house", "target_house"],
    "lord_of_house": ["house", "planet"],
    "dasha_active": ["system", "sign"],
    "transit_in_sign": ["planet", "sign"],
    "transit_conjunct_natal": ["transit_planet", "natal_planet"],
    "strength_threshold": ["planet", "metric", "min"],
    "rule_formed": ["rule_id"],
}

# Code-execution / shell / query payload patterns. Word-boundary anchored to
# avoid false positives on prose ("important", "execution POLICY text", ...).
SUSPICIOUS_PATTERNS: List[str] = [
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"__import__",
    r"\bsubprocess\b",
    r"os\.system",
    r"os\.popen",
    r"\blambda\b",
    r"^\s*import\s+[a-zA-Z_]",
    r"\n\s*import\s+[a-zA-Z_]",
    r";\s*import\s+[a-zA-Z_]",
    r";\s*(rm|del|drop|shutdown|reboot)\b",
    r"`[^`]*`",
    r"\$\([^)]*\)",
    r"\bSELECT\b.{0,80}\bFROM\b",
    r"__class__",
    r"__subclasses__",
    r"\bopen\s*\(",
    r"\bsocket\b",
    r"\brequests\.(get|post)\b",
    r"\burllib\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]


def find_suspicious_text(value: str) -> List[str]:
    """Return matched pattern strings for a scalar value (empty = clean)."""
    hits = []
    for pat, rx in zip(SUSPICIOUS_PATTERNS, _COMPILED):
        if rx.search(value):
            hits.append(pat)
    return hits


def known_ops() -> Set[str]:
    return set(LOGICAL_OPS) | set(PRIMITIVES.keys())
