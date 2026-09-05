"""
Phase 5B — Parivartana (sign-exchange) detector + Maha/Khala/Dainya rules.
"""
from __future__ import annotations
from typing import List, Tuple

from ..models import (
    RuleDefinition, RuleMetadata, Provenance, Evidence,
    CancellationRule, MitigationRule, Condition,
)
from ..enums import (
    RuleCategory, RuleTradition, RuleStatus, ConfidenceLevel,
    SourceType, EvidenceType,
)
from .structural import (
    sign_of, houses_ruled_by, parivartana_pairs, classify_parivartana,
    lord_of_house,
)


def _prov(method: str, notes: str) -> Provenance:
    return Provenance(
        source_type=SourceType.CLASSICAL_TEXT,
        source_name="Brihat Parashara Hora Shastra",
        source_reference="UNVERIFIED",
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        method=method, implementation_version="1.0.0", notes=notes,
    )


def _base(rule_id, name, desc, cls: str) -> RuleDefinition:
    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id=rule_id, rule_version="1.0.0", name=name,
            category=RuleCategory.YOGA, tradition=RuleTradition.PARASHARI_CLASSICAL,
            school_method="Parashari Classical", status=RuleStatus.ENABLED,
            description=desc,
            provenance=_prov(
                f"parivartana_{cls.lower()}",
                "Traditional attribution (UNVERIFIED exact verse). Detector: mutual sign "
                "occupation. Classification method=house_role: DAINYA if 6/8/12 lordship "
                "involved; else KHALA if 3rd lord involved; else MAHA."),
            confidence=ConfidenceLevel.HIGH,
            tags=["parivartana", cls.lower()], enabled=True),
        formation_conditions=[Condition(
            type=f"parashari_parivartana_{cls.lower()}_formation", params={})],
        strength_conditions=[], activation_rules=[],
        cancellation_rules=[CancellationRule(
            rule_id=f"{rule_id}.CANCEL", description="Generic cancellation scan",
            evaluator="parashari_cancellation_generic", is_partial=True)],
        mitigation_rules=[MitigationRule(
            rule_id=f"{rule_id}.MITIG", description="Generic mitigation scan",
            evaluator="parashari_mitigation_generic", strength_impact="partial")],
        required_evidence=[EvidenceType.EXCHANGE, EvidenceType.LORDSHIP_RELATIONSHIP],
    )


def build_maha() -> RuleDefinition:
    return _base("PARASHARI.YOGA.PARIVARTANA_MAHA", "Maha Parivartana Yoga",
                 "Sign exchange between planets ruling auspicious houses "
                 "(no 6/8/12 lordship, no 3rd lord).", "MAHA")


def build_khala() -> RuleDefinition:
    return _base("PARASHARI.YOGA.PARIVARTANA_KHALA", "Khala Parivartana Yoga",
                 "Sign exchange involving the 3rd lord (without 6/8/12 lordship).", "KHALA")


def build_dainya() -> RuleDefinition:
    return _base("PARASHARI.YOGA.PARIVARTANA_DAINYA", "Dainya Parivartana Yoga",
                 "Sign exchange involving a 6th, 8th or 12th lord.", "DAINYA")


def _formation(ctx, cls: str) -> Tuple[bool, List[Evidence]]:
    pairs = parivartana_pairs(ctx)
    ev: List[Evidence] = []
    hits = []
    for a, b in pairs:
        cat = classify_parivartana(ctx, a, b)
        ev.append(Evidence(
            evidence_type=EvidenceType.EXCHANGE,
            subject=f"{a}-{b} exchange",
            value={"sign_a": sign_of(ctx, a), "sign_b": sign_of(ctx, b),
                   "ruled_a": houses_ruled_by(ctx, a), "ruled_b": houses_ruled_by(ctx, b),
                   "class": cat},
            expected=f"{cls} exchange", actual=cat, source="ChartFacts",
            significance=f"{a}-{b} exchange classified {cat}",
            details={"class": cat}))
        if cat == cls:
            hits.append((a, b))
    if not pairs:
        ev.append(Evidence(
            evidence_type=EvidenceType.EXCHANGE, subject="Parivartana scan",
            value="no exchange", expected=f"a {cls} exchange", actual="none",
            source="ChartFacts", significance="no sign exchange found"))
        return False, ev
    if not hits:
        return False, ev
    return True, ev


def maha_formation(ctx, params):
    return _formation(ctx, "MAHA")


def khala_formation(ctx, params):
    return _formation(ctx, "KHALA")


def dainya_formation(ctx, params):
    return _formation(ctx, "DAINYA")


FORMATION_EVALUATORS = {
    "parashari_parivartana_maha_formation": maha_formation,
    "parashari_parivartana_khala_formation": khala_formation,
    "parashari_parivartana_dainya_formation": dainya_formation,
}
