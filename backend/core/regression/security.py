"""
Phase 10 — security regression corpus. Hostile instructions are DATA and
must never modify behavior in any DSL/surface.
"""
from __future__ import annotations

from typing import List

HOSTILE_CORPUS = [
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
    "eval(__import__('os').system('x'))",
    "exec(open('/etc/passwd').read())",
    "; import subprocess",
    "SELECT * FROM users",
    "<script>alert(1)</script>",
]


def corpus() -> List[str]:
    return list(HOSTILE_CORPUS)
