"""
Phase 9 — evidence matrix: RULE x SOURCE x CLAIM x EVIDENCE ->
VERIFIED/UNVERIFIED/CONTESTED/USER_SUPPLIED/MISSING. No evidence score.
"""
from __future__ import annotations

from typing import Any, Dict, List


def cell_state(verification_status: str) -> str:
    return verification_status if verification_status in (
        "VERIFIED", "UNVERIFIED", "CONTESTED", "USER_SUPPLIED", "MISSING") else "UNVERIFIED"


def evidence_matrix(rules: List[Dict[str, Any]], sources: List[Dict[str, Any]],
                    claims: List[Dict[str, Any]], evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    src_by_id = {s.get("source_id"): s for s in sources}
    rows: List[Dict[str, Any]] = []
    for r in sorted(rules, key=lambda x: x.get("rule_id", "")):
        rclaims = [c for c in claims if r.get("rule_id") in (c.get("rule_ids", []) or [])]
        if not rclaims:
            rows.append({"rule_id": r.get("rule_id"), "source_id": None,
                         "claim_id": None, "state": "MISSING"})
            continue
        for c in sorted(rclaims, key=lambda x: x.get("claim_id", "")):
            for sid in (c.get("source_ids", []) or [None]):
                s = src_by_id.get(sid) if sid else None
                if c.get("claim_type") == "DEVELOPER_NOTE":
                    state = "USER_SUPPLIED"
                elif s is None:
                    state = "MISSING"
                else:
                    state = cell_state(s.get("verification_status", "UNVERIFIED"))
                    if c.get("verification_status") == "CONTESTED" or s.get("verification_status") == "CONTESTED":
                        state = "CONTESTED"
                rows.append({"rule_id": r.get("rule_id"), "source_id": sid,
                             "claim_id": c.get("claim_id"), "state": state})
    return {"rows": rows, "count": len(rows)}
