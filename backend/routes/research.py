"""
Research Lab read-only API — Phase 11 (API-only backend addition).

Exposes the frozen Phase 9 golden research package and promotion-gate
definitions for the developer Research Lab UI. READ-ONLY: no rule creation,
no promotion, no mutation of any kind. No calculation semantics changed.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/research", tags=["Research Lab (read-only)"])


@router.get("/golden")
def research_golden():
    from backend.core.research import golden as _golden
    built = _golden.build_golden_package()
    pkg = built["package"]
    return {
        "package_id": pkg["package_id"],
        "package_version": pkg["package_version"],
        "lifecycle": pkg["lifecycle"],
        "fingerprint": pkg["fingerprint"],
        "profiles": pkg["profiles"],
        "rules": [
            {
                "rule_id": r["rule_id"],
                "rule_version": r["rule_version"],
                "rule_name": r.get("rule_name", ""),
                "tradition": r["tradition"],
                "category": r.get("category", ""),
                "lifecycle_status": r["lifecycle_status"],
            }
            for r in pkg["rules"]
        ],
        "sources": pkg["sources"],
        "claims": pkg["claims"],
        "fixtures": [
            {"fixture_id": f["fixture_id"], "fixture_kind": f["fixture_kind"],
             "description": f.get("description", "")}
            for f in pkg["fixtures"]
        ],
        "promotion_requests": [
            {"request_id": built["fail_request"]["request_id"], "status": "FAILING_DEMO"},
            {"request_id": built["pending_request"]["request_id"], "status": "REVIEW_PENDING"},
        ],
        "semantics": "RESEARCH_ONLY: TESTED != PROMOTED. Experimental rules are never production truth.",
    }


@router.get("/gates")
def promotion_gates():
    from backend.core.research.models import PROMOTION_GATES
    return {
        "gates": list(PROMOTION_GATES),
        "policy": "All 12 gates must pass independently plus an explicit APPROVE review before any promotion.",
    }
