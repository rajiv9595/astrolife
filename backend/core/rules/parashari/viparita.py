"""
Phase 5B — Viparita Raja Yogas: Harsha (6L), Sarala (8L), Vimala (12L)
each placed in a Dusthana house (6, 8, 12). Conjunction/exchange variants
NOT counted (documented omission).
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
from .structural import house_of, lord_of_house, DUSTHANA_HOUSES

SPECS = {
    "HARSHA": 6,
    "SARALA": 8,
    "VIMALA": 12,
}


def _build(yoga: str, house: int) -> RuleDefinition:
    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id=f"PARASHARI.YOGA.VIPARITA_{yoga}", rule_version="1.0.0",
            name=f"Viparita Raja Yoga ({yoga.capitalize()})",
            category=RuleCategory.YOGA, tradition=RuleTradition.PARASHARI_CLASSICAL,
            school_method="Parashari Classical", status=RuleStatus.ENABLED,
            description=f"Lord of the {house}th house placed in a Dusthana house (6, 8 or 12).",
            provenance=Provenance(
                source_type=SourceType.CLASSICAL_TEXT,
                source_name="Brihat Parashara Hora Shastra",
                source_reference="UNVERIFIED",
                tradition=RuleTradition.PARASHARI_CLASSICAL,
                method=f"viparita_{yoga.lower()}_{house}L_in_dusthana",
                implementation_version="1.0.0",
                notes="Traditional attribution (UNVERIFIED exact verse). Explicit "
                      "lord-house pairing; bare dusthana occupancy rejected; "
                      "conjunction/exchange variants omitted."),
            confidence=ConfidenceLevel.HIGH,
            tags=["viparita_raja", yoga.lower()], enabled=True),
        formation_conditions=[Condition(
            type=f"parashari_viparita_{yoga.lower()}_formation", params={})],
        strength_conditions=[], activation_rules=[],
        cancellation_rules=[CancellationRule(
            rule_id=f"PARASHARI.YOGA.VIPARITA_{yoga}.CANCEL",
            description="Generic cancellation scan",
            evaluator="parashari_cancellation_generic", is_partial=True)],
        mitigation_rules=[MitigationRule(
            rule_id=f"PARASHARI.YOGA.VIPARITA_{yoga}.MITIG",
            description="Generic mitigation scan",
            evaluator="parashari_mitigation_generic", strength_impact="partial")],
        required_evidence=[EvidenceType.DUSTHANA, EvidenceType.HOUSE_LORD_POSITION],
    )


def build_harsha() -> RuleDefinition:
    return _build("HARSHA", 6)


def build_sarala() -> RuleDefinition:
    return _build("SARALA", 8)


def build_vimala() -> RuleDefinition:
    return _build("VIMALA", 12)


def _formation(ctx, yoga: str, house: int) -> Tuple[bool, List[Evidence]]:
    lord = lord_of_house(ctx, house)
    h = house_of(ctx, lord) if lord else None
    ok = h is not None and h in DUSTHANA_HOUSES
    ev = [Evidence(
        evidence_type=EvidenceType.DUSTHANA,
        subject=f"{house}th lord {lord}",
        value=h, expected="Dusthana (6,8,12)", actual=f"house {h}",
        source="ChartFacts",
        significance=f"Viparita {yoga} formed" if ok else f"{house}th lord not in Dusthana",
        details={"lord": lord, "method": f"viparita_{yoga.lower()}"})]
    return ok, ev


def _mk(yoga, house):
    def _fn(ctx, params, _y=yoga, _h=house):
        return _formation(ctx, _y, _h)
    return _fn


FORMATION_EVALUATORS = {
    "parashari_viparita_harsha_formation": _mk("HARSHA", 6),
    "parashari_viparita_sarala_formation": _mk("SARALA", 8),
    "parashari_viparita_vimala_formation": _mk("VIMALA", 12),
}
