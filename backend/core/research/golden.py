"""
Phase 9 — golden research package: deterministic fixture proving the
firewall (TESTED != PROMOTED). Never auto-promotes the experimental rule.
"""
from __future__ import annotations

from typing import Any, Dict

from . import packages as _pkg
from . import rules as _rules
from .fixtures import boundary_fixture, create_fixture, missing_input_fixture, negative_fixture
from .promotion import create_promotion_request


def build_golden_package() -> Dict[str, Any]:
    _pkg.clear_store()
    _rules.clear_store()
    from .promotion import clear_all as _clear_promo
    _clear_promo()

    accepted = _rules.create_research_rule(
        "GOLDEN.ACCEPTED.SAMPLE", "1.0.0", tradition="PARASHARI_CLASSICAL",
        category="YOGA",
        formation={"op": "planet_in_sign", "params": {"planet": "Jupiter", "sign": "Pisces"}},
        applicability={"traditions": ["PARASHARI_CLASSICAL"], "profiles": ["PARASHARI_CLASSICAL"]},
        dependencies={"input_facts": ["natal.Jupiter.sign"]},
        evidence_requirements=["formation_evidence"],
        lifecycle_status="VALIDATED",
        rule_name="Golden accepted reference",
        description="Accepted-rule reference; not experimental.",
    )
    custom = _rules.create_research_rule(
        "GOLDEN.CUSTOM.SYNTHETIC", "1.0.0", tradition="CUSTOM_DEVELOPER",
        formation={"op": "planet_in_sign", "params": {"planet": "Mars", "sign": "Aries"}},
        applicability={"traditions": ["CUSTOM_DEVELOPER"], "profiles": ["PARASHARI_CLASSICAL"]},
        dependencies={"input_facts": ["natal.Mars.sign"]},
        lifecycle_status="EXPERIMENTAL",
        rule_name="Golden synthetic developer rule",
    )
    experimental = _rules.create_research_rule(
        "GOLDEN.EXPERIMENTAL.SYNTHETIC", "1.0.0", tradition="EXPERIMENTAL",
        formation={"op": "ALL", "params": {},
                   "children": [
                       {"op": "planet_in_sign", "params": {"planet": "Venus", "sign": "Taurus"}},
                       {"op": "planet_in_house", "params": {"planet": "Venus", "house": 2}},
                   ]},
        applicability={"traditions": ["EXPERIMENTAL"], "profiles": ["PARASHARI_CLASSICAL"]},
        dependencies={"input_facts": ["natal.Venus.sign", "natal.Venus.house"],
                      "rule_dependencies": ["GOLDEN.CUSTOM.SYNTHETIC"]},
        lifecycle_status="EXPERIMENTAL",
        rule_name="Golden experimental rule (never auto-promoted)",
    )
    fixtures = [
        create_fixture("FX-GOLDEN-POS", {"natal.Jupiter.sign": "Pisces"},
                       expected_formation="FORMED", expected_status="PASS"),
        negative_fixture("FX-GOLDEN-NEG", {"natal.Jupiter.sign": "Aries"},
                         description="Jupiter not in Pisces"),
        boundary_fixture("FX-GOLDEN-BOUNDARY", {"natal.Mars.sign": "Aries"},
                         expected_formation="FORMED", description="exact sign membership"),
        missing_input_fixture("FX-GOLDEN-MISSING", description="no facts supplied"),
        create_fixture("FX-EXP-POS", {"natal.Venus.sign": "Taurus", "natal.Venus.house": 2},
                       expected_formation="FORMED"),
        negative_fixture("FX-EXP-NEG", {"natal.Venus.sign": "Aries", "natal.Venus.house": 2}),
    ]
    pkg = _pkg.create_research_package(
        "GOLDEN.RESEARCH.PKG", "1.0.0", author="Astrolife Research",
        description="Golden research package (deterministic).",
        profiles=["PARASHARI_CLASSICAL"],
        rules=[accepted, custom, experimental],
        sources=[
            {"source_id": "SRC-UNVERIFIED-1", "title": "Unverified developer note",
             "tradition": "EXPERIMENTAL", "verification_status": "UNVERIFIED"},
            {"source_id": "SRC-A-1", "title": "Source A claims X",
             "tradition": "CUSTOM_DEVELOPER", "verification_status": "USER_SUPPLIED"},
            {"source_id": "SRC-B-1", "title": "Source B claims NOT X",
             "tradition": "CUSTOM_DEVELOPER", "verification_status": "CONTESTED"},
        ],
        claims=[
            {"claim_id": "CLM-A", "claim_type": "SOURCE_CLAIM",
             "statement": "Source A: Venus in Taurus in house 2 signifies X.",
             "source_ids": ["SRC-A-1"], "evidence_ids": [], "rule_ids": ["GOLDEN.EXPERIMENTAL.SYNTHETIC"],
             "tradition": "CUSTOM_DEVELOPER", "verification_status": "USER_SUPPLIED", "status": "OPEN"},
            {"claim_id": "CLM-B", "claim_type": "SOURCE_CLAIM",
             "statement": "Source B: Venus in Taurus in house 2 does not signify X.",
             "source_ids": ["SRC-B-1"], "evidence_ids": [], "rule_ids": ["GOLDEN.EXPERIMENTAL.SYNTHETIC"],
             "tradition": "CUSTOM_DEVELOPER", "verification_status": "CONTESTED", "status": "OPEN"},
            {"claim_id": "CLM-NOTE", "claim_type": "DEVELOPER_NOTE",
             "statement": "Developer observation only; not a source claim.",
             "source_ids": [], "evidence_ids": [], "rule_ids": ["GOLDEN.EXPERIMENTAL.SYNTHETIC"],
             "tradition": "EXPERIMENTAL", "verification_status": "USER_SUPPLIED", "status": "OPEN"},
        ],
        evidence=[{"evidence_id": "EV-1", "subject": "Venus/Taurus",
                   "value": "observed", "source": "fixture", "verification_status": "USER_SUPPLIED"}],
        dependencies={"note": "experimental depends on custom synthetic"},
        fixtures=fixtures,
        lifecycle="EXPERIMENTAL",
    )
    # failing promotion (incomplete evidence/review) + pending promotion
    fail_req = create_promotion_request(
        "PROMO-GOLDEN-FAIL", "GOLDEN.EXPERIMENTAL.SYNTHETIC", "1.0.0",
        "GOLDEN.RESEARCH.PKG", requested_by="researcher",
        target_catalogue="RESEARCH_STAGING", target_tradition="EXPERIMENTAL",
        target_profile="PARASHARI_CLASSICAL", source_state="UNVERIFIED",
        evidence_state="UNVERIFIED", regression_state="UNKNOWN", approval_state="PENDING")
    pend_req = create_promotion_request(
        "PROMO-GOLDEN-PENDING", "GOLDEN.CUSTOM.SYNTHETIC", "1.0.0",
        "GOLDEN.RESEARCH.PKG", requested_by="researcher",
        target_catalogue="RESEARCH_STAGING", target_tradition="CUSTOM_DEVELOPER",
        target_profile="PARASHARI_CLASSICAL", approval_state="PENDING")
    return {"package": pkg, "rules": {"accepted": accepted, "custom": custom, "experimental": experimental},
            "fail_request": fail_req, "pending_request": pend_req}
