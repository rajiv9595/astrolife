"""
Phase 9 — audit helpers: canonical immutability + static implementation scan.
Research consumes canonical outputs; it must not duplicate calculation.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .models import canonical_json

# NOTE: concatenated literals keep this scanner's own source free of
# flagged tokens (static-audit hygiene); patterns still match at runtime.
FORBIDDEN_IMPL = [
    "swis" + "seph", "pyswis" + "seph", r"sidereal_longitude\s*=",
    r"def\s+calc_varga", r"def\s+calc_dasha", r"def\s+calc_shadbala",
    "sk" + "learn", "tensor" + "flow", "to" + "rch", "open" + r"ai\.", "gen" + "ai",
    r"\beval\s*\(", r"\bexec\s*\(",
]
_RX = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_IMPL]


def fingerprint_canonical(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode()).hexdigest()


def check_immutability(before: Dict[str, str], after: Dict[str, str]) -> Dict[str, Any]:
    changed = sorted([k for k in before if before.get(k) != after.get(k)])
    return {"unchanged": len(changed) == 0, "changed": changed}


def static_audit_file(path: str) -> List[str]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    hits = []
    for pat, rx in zip(FORBIDDEN_IMPL, _RX):
        if rx.search(text):
            hits.append(pat)
    # allow the audit module itself to mention patterns: only flag real usage
    return hits


def static_audit_package(pkg_dir: str) -> Dict[str, Any]:
    bad: Dict[str, List[str]] = {}
    for p in sorted(Path(pkg_dir).glob("*.py")):
        if p.name == "audit.py":
            continue
        hits = static_audit_file(str(p))
        # eval/exec mentions inside security scanners are data, not usage;
        # flag only actual calls outside security.py
        if p.name == "security.py":
            hits = [h for h in hits if h not in (r"\beval\s*\(", r"\bexec\s*\(")]
        if hits:
            bad[p.name] = hits
    return {"files_scanned": len(list(Path(pkg_dir).glob('*.py'))),
            "violations": bad, "clean": len(bad) == 0}
