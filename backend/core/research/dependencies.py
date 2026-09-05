"""
Phase 9 — dependency graph reusing Phase 6 dependency semantics.
Declares fact/Varga/Dasha/Transit/Strength/Jaimini/rule/event deps,
detects missing/invalid/cycles/unsupported/profile/tradition conflicts.
"""
from __future__ import annotations

from typing import Any, Dict, List

DEP_KEYS = ("input_facts", "varga_dependencies", "dasha_dependencies",
            "transit_dependencies", "strength_dependencies",
            "jaimini_dependencies", "rule_dependencies", "event_dependencies")

SUPPORTED_FACT_HEADS = ("natal", "houses", "varga", "dasha", "transit",
                        "strength", "jaimini", "rule", "event", "dignity", "aspects")


def _fact_kind(fact: Any) -> str:
    """Classify a fact dependency: VALID_HEAD | UNSUPPORTED | INVALID."""
    if not isinstance(fact, str) or "." not in fact:
        return "INVALID"
    head = fact.split(".", 1)[0]
    return "VALID_HEAD" if head in SUPPORTED_FACT_HEADS else "UNSUPPORTED"


def normalize_dependencies(deps: Dict[str, Any]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for k in DEP_KEYS:
        v = deps.get(k, [])
        out[k] = sorted(v) if isinstance(v, list) else []
    return out


def build_dependency_graph(rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = sorted(r.get("rule_id", "") for r in rules)
    edges: List[Dict[str, str]] = []
    for r in rules:
        deps = normalize_dependencies(r.get("dependencies", {}))
        for dep in deps.get("rule_dependencies", []):
            edges.append({"from": r.get("rule_id", ""), "to": dep, "type": "DEPENDS_ON"})
    edges = sorted(edges, key=lambda e: (e["from"], e["to"]))
    return {"nodes": nodes, "edges": edges}


def detect_issues(rules: List[Dict[str, Any]],
                  known_rules: List[str] | None = None,
                  profile: str = "") -> Dict[str, Any]:
    known = set(known_rules or [])
    missing, invalid, unsupported, conflicts = [], [], [], []
    for r in rules:
        deps = normalize_dependencies(r.get("dependencies", {}))
        for dep in deps.get("rule_dependencies", []):
            if dep not in known and dep not in [x.get("rule_id") for x in rules]:
                missing.append(f"{r.get('rule_id')}: missing rule dep {dep}")
        for fact in deps.get("input_facts", []):
            kind = _fact_kind(fact)
            if kind == "INVALID":
                invalid.append(f"{r.get('rule_id')}: invalid fact dep {fact!r}")
            elif kind == "UNSUPPORTED":
                unsupported.append(f"{r.get('rule_id')}: unsupported dep {fact!r}")
        trads = (r.get("applicability", {}) or {}).get("traditions", [])
        if "PARASHARI_CLASSICAL" in trads and "JAIMINI_CLASSICAL" in trads and profile == "STRICT_SINGLE_TRADITION":
            conflicts.append(f"{r.get('rule_id')}: tradition conflict under strict profile")
    # cycle detection over rule deps
    adj = {r.get("rule_id", ""): normalize_dependencies(r.get("dependencies", {})).get("rule_dependencies", []) for r in rules}
    cycles: List[str] = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in adj}
    def dfs(n: str, stack: List[str]) -> None:
        color[n] = GRAY
        for m in adj.get(n, []):
            if m not in color:
                continue
            if color[m] == GRAY:
                cycles.append("->".join(stack + [n, m]))
            elif color[m] == WHITE:
                dfs(m, stack + [n])
        color[n] = BLACK
    for n in sorted(adj):
        if color[n] == WHITE:
            dfs(n, [])
    return {"missing": sorted(missing), "invalid": sorted(invalid),
            "cycles": sorted(cycles), "unsupported": sorted(unsupported),
            "profile_conflicts": sorted(conflicts),
            "tradition_conflicts": sorted(conflicts)}


def dependency_matrix(rules: List[Dict[str, Any]], available: List[str]) -> Dict[str, Any]:
    avail = set(available)
    rows: List[Dict[str, Any]] = []
    for r in sorted(rules, key=lambda x: x.get("rule_id", "")):
        deps = normalize_dependencies(r.get("dependencies", {}))
        cells = {}
        for k, vals in deps.items():
            for v in vals:
                if v in avail:
                    cells[f"{k}:{v}"] = "RESOLVED"
                elif k == "rule_dependencies":
                    cells[f"{k}:{v}"] = "MISSING"
                elif _fact_kind(v) != "VALID_HEAD":
                    cells[f"{k}:{v}"] = "INVALID"
                else:
                    cells[f"{k}:{v}"] = "MISSING"
        rows.append({"rule_id": r.get("rule_id"), "cells": cells})
    return {"rows": rows}
