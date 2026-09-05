"""
Phase 5B — Dhana Yogas (three separate rule IDs, sambandha required).
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
from .structural import lords_sambandha, house_of, is_kendra_house, is_trikona_house


def _prov(method: str, notes: str) -> Provenance:
    return Provenance(
        source_type=SourceType.CLASSICAL_TEXT,
        source_name="Brihat Parashara Hora Shastra",
        source_reference="UNVERIFIED",
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        method=method, implementation_version="1.0.0", notes=notes,
    )


def _base(rule_id, name, desc, method, notes, ftype, tags) -> RuleDefinition:
    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id=rule_id, rule_version="1.0.0", name=name,
            category=RuleCategory.YOGA, tradition=RuleTradition.PARASHARI_CLASSICAL,
            school_method="Parashari Classical", status=RuleStatus.ENABLED,
            description=desc, provenance=_prov(method, notes),
            confidence=ConfidenceLevel.HIGH, tags=tags, enabled=True),
        formation_conditions=[Condition(type=ftype, params={})],
        strength_conditions=[], activation_rules=[],
        cancellation_rules=[CancellationRule(
            rule_id=f"{rule_id}.CANCEL", description="Debilitation/Dusthana/malefic check",
            evaluator="parashari_cancellation_generic", is_partial=True)],
        mitigation_rules=[MitigationRule(
            rule_id=f"{rule_id}.MITIG", description="Benefic/dignity/house support",
            evaluator="parashari_mitigation_generic", strength_impact="partial")],
        required_evidence=[EvidenceType.LORDSHIP_RELATIONSHIP, EvidenceType.PLANET_DIGNITY],
    )


def build_dhana_2_11() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.DHANA_2_11", "Dhana Yoga (2nd-11th Lords)",
        "2nd and 11th lords in conjunction, mutual aspect, or exchange.",
        "sambandha_2_11",
        "Traditional attribution: BPHS/Phaladeepika Dhana chapters (UNVERIFIED exact verse). "
        "Sambandha required; bare 2+11 ownership rejected.",
        "parashari_dhana_2_11_formation", ["dhana_yoga"])


def build_dhana_5_9() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.DHANA_5_9", "Dhana Yoga (5th-9th Lords)",
        "5th and 9th (Trikona pair) lords in conjunction, mutual aspect, or exchange.",
        "sambandha_5_9",
        "Traditional attribution: BPHS/Phaladeepika Dhana chapters (UNVERIFIED exact verse).",
        "parashari_dhana_5_9_formation", ["dhana_yoga"])


def build_dhana_lagna() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.DHANA_LAGNA_WEALTH", "Dhana Yoga (Lagna with Wealth Lords)",
        "Lagna lord in sambandha (conjunction/mutual aspect/exchange) with "
        "any of the 2nd/5th/9th/11th lords.",
        "sambandha_lagna_wealth",
        "Traditional attribution: BPHS/Phaladeepika Dhana chapters (UNVERIFIED exact verse). "
        "Lagna involvement required by this rule.",
        "parashari_dhana_lagna_formation", ["dhana_yoga", "lagna"])


def _pair_ev(h1, h2, l1, l2, kind, detail) -> Evidence:
    return Evidence(
        evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
        subject=f"Lords of {h1} ({l1}) and {h2} ({l2})",
        value=kind, expected="conjunction/mutual_aspect/exchange",
        actual=f"{kind}: {detail}", source="ChartFacts",
        significance=f"Dhana sambandha {h1}-{h2}: {kind}",
        details={"relationship_type": kind})


def _pair_formed(ctx, h1: int, h2: int):
    kind, l1, l2, detail = lords_sambandha(ctx, h1, h2)
    if kind in ("conjunction", "mutual_aspect", "exchange"):
        return True, [_pair_ev(h1, h2, l1, l2, kind, detail)], (l1, l2)
    if kind == "same_lord":
        h = house_of(ctx, l1)
        if h is not None and (is_kendra_house(h) or is_trikona_house(h)):
            return True, [Evidence(
                evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
                subject=f"Single lord {l1} of {h1} and {h2}",
                value="same_lord_placed", expected="Kendra/Trikona",
                actual=f"house {h}", source="ChartFacts",
                significance=f"{l1} rules both, in {h}",
                details={"relationship_type": "same_lord_placed"})], (l1, l2)
    return False, [_pair_ev(h1, h2, l1, l2, "none", detail)], (l1, l2)


def dhana_2_11_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ok, ev, _ = _pair_formed(ctx, 2, 11)
    return ok, ev


def dhana_5_9_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ok, ev, _ = _pair_formed(ctx, 5, 9)
    return ok, ev


def dhana_lagna_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    evidence: List[Evidence] = []
    for h in (2, 5, 9, 11):
        ok, ev, _ = _pair_formed(ctx, 1, h)
        evidence.extend(ev)
        if ok:
            return True, evidence
    return False, evidence


FORMATION_EVALUATORS = {
    "parashari_dhana_2_11_formation": dhana_2_11_formation,
    "parashari_dhana_5_9_formation": dhana_5_9_formation,
    "parashari_dhana_lagna_formation": dhana_lagna_formation,
}
