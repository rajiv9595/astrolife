"""
Phase 8 — security (§42). Prediction inputs are DATA.

Structured requests cannot carry instructions (extra=forbid), but `notes`
free text and hostile enum values are scanned: override/fabrication/guarantee
directives become WARNING findings and are never honored. The engine has no
code path that mutates profiles, birth data, dasha rows, conflicts, or
certainty posture in response to input text.
"""
from __future__ import annotations

import re
from typing import List

HOSTILE_PATTERNS = (
    r"ignore the profile",
    r"pretend this event is formed",
    r"make the prediction positive",
    r"remove conflicts",
    r"say it is guaranteed",
    r"override the dasha",
    r"change the birth chart",
    r"treat this developer rule as classical",
    r"ignore missing transit data",
)

_COMPILED = [re.compile(p, re.IGNORECASE) for p in HOSTILE_PATTERNS]


def find_hostile_instructions(text: str) -> List[str]:
    return [p for p, rx in zip(HOSTILE_PATTERNS, _COMPILED) if rx.search(text or "")]


def scan_request(request: object) -> List[str]:
    """Collect warnings for hostile content in free-text/notes fields."""
    warnings = []
    notes = getattr(request, "notes", "") or ""
    for pattern in find_hostile_instructions(notes):
        warnings.append(f"ignored hostile instruction in notes: {pattern}")
    return sorted(warnings)
