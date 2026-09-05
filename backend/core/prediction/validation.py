"""
Phase 8 — strict prediction validator (§30 language firewall + schema).

Rejects: unknown fields (schema-level), certainty claims
("will definitely happen", "guaranteed", "certain", "100%", "you will"),
numeric prediction scores/probabilities, missing provenance, invented rule
references, unresolved conflicts hidden from output. Invalid results become
INVALID, never silently repaired. Human rendering guidance: candidates stay
candidates ("timing candidate", "potential window", "astrologically indicated
period", "multiple systems converge", "evidence is incomplete",
"systems conflict").
"""
from __future__ import annotations

import re
from typing import Any, List, Tuple

CERTAINTY_PATTERNS = (
    r"\bwill definitely happen\b",
    r"\bguaranteed\b",
    r"\bcertain\b",
    r"100\s*%",
    r"\byou will\b",
)

SCORE_PATTERNS = (
    r"\bprediction score\s*=",
    r"\bprobability\s*=",
    r"\bmarriage probability\b",
    r"\bcareer score\b",
    r"\b\d{1,3}\s*%\s*(chance|probability|likely)\b",
)

_COMPILED_CERTAINTY = [re.compile(p, re.IGNORECASE) for p in CERTAINTY_PATTERNS]
_COMPILED_SCORES = [re.compile(p, re.IGNORECASE) for p in SCORE_PATTERNS]


def find_certainty(text: str) -> List[str]:
    return [p for p, rx in zip(CERTAINTY_PATTERNS, _COMPILED_CERTAINTY)
            if rx.search(text or "")]


def find_scores(text: str) -> List[str]:
    return [p for p, rx in zip(SCORE_PATTERNS, _COMPILED_SCORES)
            if rx.search(text or "")]


def _texts_of(result: Any) -> List[str]:
    texts = []
    for candidate in result.candidates:
        texts.append(candidate.rank_reason or "")
        provenance = candidate.provenance
        if isinstance(provenance, dict):
            texts.append(str(provenance.get("note", "")))
        for window in candidate.windows:
            texts.append(window.uncertainty or "")
    texts.extend(result.warnings or [])
    texts.extend(result.unknowns or [])
    return texts


def validate_prediction_result(result: Any, entry: Any) -> Tuple[bool, List[str]]:
    """Returns (ok, notes). Structural + language validation."""
    notes: List[str] = []
    raw_outcomes = entry.get("outcomes", [])
    if isinstance(raw_outcomes, dict):
        raw_outcomes = list(raw_outcomes.values())
    known_rules = {o.get("rule_id", "") for o in raw_outcomes
                   if isinstance(o, dict)}
    for candidate in result.candidates:
        for rule_id in candidate.supporting_rules:
            if rule_id not in known_rules:
                notes.append(f"invented rule reference {rule_id!r}")
        if not candidate.provenance:
            notes.append(f"missing provenance {candidate.hypothesis_id!r}")
        if not candidate.input_fingerprint:
            notes.append(f"missing input fingerprint {candidate.hypothesis_id!r}")
        if candidate.output_fingerprint != candidate.compute_output_fingerprint():
            notes.append(f"output fingerprint mismatch {candidate.hypothesis_id!r}")
    for text in _texts_of(result):
        for pattern in find_certainty(text):
            notes.append(f"certainty claim {pattern!r}")
        for pattern in find_scores(text):
            notes.append(f"numeric score {pattern!r}")
    if result.output_fingerprint != result.compute_output_fingerprint():
        notes.append("result output fingerprint mismatch")
    return (len(notes) == 0, sorted(notes))
