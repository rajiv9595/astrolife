"""
Phase 5B — Pancha Mahapurusha Yogas. Formation: planet in Kendra from Lagna
AND (own sign OR exalted). Moolatrikona alone never qualifies.
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
from .structural import house_of, sign_of, is_kendra_house

SPECS = {
    "RUCHAKA": ("Mars", ("Aries", "Scorpio"), "Capricorn"),
    "BHADRA": ("Mercury", ("Gemini", "Virgo"), "Virgo"),
    "HAMSA": ("Jupiter", ("Sagittarius", "Pisces"), "Cancer"),
    "MALAVYA": ("Venus", ("Taurus", "Libra"), "Pisces"),
    "SASA": ("Saturn", ("Capricorn", "Aquarius"), "Libra"),
}


def _prov(notes: str) -> Provenance:
    return Provenance(
        source_type=SourceType.CLASSICAL_TEXT,
        source_name="Brihat Parashara Hora Shastra",
        source_reference="UNVERIFIED",
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        method="mahapurusha_kendra_own_exalted",
        implementation_version="1.0.0", notes=notes,
    )


def _build(yoga: str, planet: str) -> RuleDefinition:
    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id=f"PARASHARI.YOGA.{yoga}", rule_version="1.0.0",
            name=f"{yoga.capitalize()} Mahapurusha Yoga",
            category=RuleCategory.YOGA, tradition=RuleTradition.PARASHARI_CLASSICAL,
            school_method="Parashari Classical", status=RuleStatus.ENABLED,
            description=f"{planet} in own sign or exaltation in a Kendra from Lagna.",
            provenance=_prov(
                "Traditional attribution: BPHS Mahapurusha adhyaya; Brihat Jataka; "
                "Phaladeepika; Saravali (UNVERIFIED exact verse). Lagna-Kendra reading; "
                "Moon-Kendra variant omitted; Moolatrikona alone excluded."),
            confidence=ConfidenceLevel.HIGH,
            tags=["mahapurusha", planet.lower(), "kendra"], enabled=True),
        formation_conditions=[Condition(type=f"parashari_{yoga.lower()}_formation", params={})],
        strength_conditions=[], activation_rules=[],
        cancellation_rules=[CancellationRule(
            rule_id=f"PARASHARI.YOGA.{yoga}.CANCEL",
            description="Combustion/affliction weakens; debilitation impossible by formation",
            evaluator="parashari_cancellation_generic", is_partial=True)],
        mitigation_rules=[MitigationRule(
            rule_id=f"PARASHARI.YOGA.{yoga}.MITIG",
            description="Benefic/dignity/house support",
            evaluator="parashari_mitigation_generic", strength_impact="partial")],
        required_evidence=[EvidenceType.KENDRA_TRIKONA, EvidenceType.PLANET_DIGNITY],
    )


def build_ruchaka() -> RuleDefinition:
    return _build("RUCHAKA", "Mars")


def build_bhadra() -> RuleDefinition:
    return _build("BHADRA", "Mercury")


def build_hamsa() -> RuleDefinition:
    return _build("HAMSA", "Jupiter")


def build_malavya() -> RuleDefinition:
    return _build("MALAVYA", "Venus")


def build_sasa() -> RuleDefinition:
    return _build("SASA", "Saturn")


def _formation(ctx, yoga: str, planet: str) -> Tuple[bool, List[Evidence]]:
    h, sign = house_of(ctx, planet), sign_of(ctx, planet)
    kendra = h is not None and is_kendra_house(h)
    own = bool(ctx.is_own_sign(planet))
    exalted = bool(ctx.is_exalted(planet))
    dign_ok = own or exalted
    evidence = [
        Evidence(
            evidence_type=EvidenceType.KENDRA_TRIKONA, subject=f"{planet} Kendra check",
            value=h, expected="Kendra (1,4,7,10)", actual=f"house {h}",
            source="ChartFacts",
            significance=f"{planet} in Kendra {h}" if kendra else f"{planet} not in Kendra (house {h})"),
        Evidence(
            evidence_type=EvidenceType.PLANET_DIGNITY, subject=f"{planet} dignity",
            value=ctx.get_dignity_category(planet), expected="own sign or exalted",
            actual=f"{ctx.get_dignity_category(planet)} in {sign}",
            source="StrengthReport",
            significance=f"{planet} dignity {ctx.get_dignity_category(planet)}",
            details={"own_sign": own, "exalted": exalted,
                     "moolatrikona_insufficient": bool(ctx.is_moolatrikona(planet))}),
    ]
    return bool(kendra and dign_ok), evidence


def _mk(yoga, planet):
    def _fn(ctx, params, _y=yoga, _p=planet):
        return _formation(ctx, _y, _p)
    return _fn


FORMATION_EVALUATORS = {
    "parashari_ruchaka_formation": _mk("RUCHAKA", "Mars"),
    "parashari_bhadra_formation": _mk("BHADRA", "Mercury"),
    "parashari_hamsa_formation": _mk("HAMSA", "Jupiter"),
    "parashari_malavya_formation": _mk("MALAVYA", "Venus"),
    "parashari_sasa_formation": _mk("SASA", "Saturn"),
}
