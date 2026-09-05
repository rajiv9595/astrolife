"""
Phase 5B — Neecha Bhanga (cancellation) + Neecha Bhanga Raja Yoga.

Separated: DEBILITATED (dignity fact) != NEECHA_BHANGA (>=1 classical
cancellation) != NEECHA_BHANGA_RAJA_YOGA (bhanga + planet in
Kendra/Trikona from Lagna). D9 strength alone is NEVER a bhanga.

Cancellation conditions (each evidence-backed):
  C1 debilitation-sign lord in Kendra from Lagna
  C2 debilitation-sign lord in Kendra from Moon
  C3 exaltation-sign lord in Kendra from Lagna
  C4 exaltation-sign lord in Kendra from Moon
  C5 exalting planet (the planet exalted in that sign) in Kendra from Lagna/Moon
  C6 debilitation/exaltation lord aspects the debilitated planet
  C7 sign exchange with the debilitation-sign lord
"""
from __future__ import annotations
from typing import Dict, List, Tuple

from ..models import (
    RuleDefinition, RuleMetadata, Provenance, Evidence,
    CancellationRule, MitigationRule, Condition,
)
from ..enums import (
    RuleCategory, RuleTradition, RuleStatus, ConfidenceLevel,
    SourceType, EvidenceType,
)
from .structural import (
    house_of, sign_of, SIGN_LORDS, is_kendra_house, is_trikona_house,
    kendras_from_moon_houses,
)

EXALTATION_SIGN = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
    "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
    "Saturn": "Libra",
}
DEBILITATION_SIGN = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
    "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
    "Saturn": "Aries",
}
# planet that is exalted in a given sign
EXALTED_IN = {v: k for k, v in EXALTATION_SIGN.items()}

SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def neecha_bhanga_conditions(ctx, planet: str) -> List[Dict]:
    """Evaluate C1..C7 for one planet. Returns list of {id, met, detail}."""
    conds: List[Dict] = []
    deb_sign = DEBILITATION_SIGN.get(planet)
    ex_sign = EXALTATION_SIGN.get(planet)
    if not ctx.is_debilitated(planet):
        return [{"id": "NOT_DEBILITATED", "met": False, "detail": f"{planet} not debilitated"}]
    dep_lord = SIGN_LORDS.get(deb_sign or "")
    ex_lord = SIGN_LORDS.get(ex_sign or "")
    exalting = EXALTED_IN.get(deb_sign or "")
    dep_house = house_of(ctx, dep_lord) if dep_lord else None
    ex_house = house_of(ctx, ex_lord) if ex_lord else None
    exalting_house = house_of(ctx, exalting) if exalting else None
    moon_kendras = kendras_from_moon_houses(ctx)

    def _mk(cid, met, detail):
        return {"id": cid, "met": bool(met), "detail": detail}

    conds.append(_mk("C1", dep_house is not None and is_kendra_house(dep_house),
                     f"debilitation lord {dep_lord} in house {dep_house}"))
    conds.append(_mk("C2", dep_house is not None and dep_house in moon_kendras,
                     f"debilitation lord {dep_lord} in Moon-kendra {dep_house}"))
    conds.append(_mk("C3", ex_house is not None and is_kendra_house(ex_house),
                     f"exaltation lord {ex_lord} in house {ex_house}"))
    conds.append(_mk("C4", ex_house is not None and ex_house in moon_kendras,
                     f"exaltation lord {ex_lord} in Moon-kendra {ex_house}"))
    conds.append(_mk("C5", exalting_house is not None and
                     (is_kendra_house(exalting_house) or exalting_house in moon_kendras),
                     f"exalting planet {exalting} in house {exalting_house}"))
    asp = False
    if dep_lord:
        asp = asp or bool(ctx.get_planet_aspecting_planet(dep_lord, planet))
    if ex_lord:
        asp = asp or bool(ctx.get_planet_aspecting_planet(ex_lord, planet))
    conds.append(_mk("C6", asp, "aspect by debilitation/exaltation lord"))
    exch = bool(dep_lord and ctx.is_exchange(planet, dep_lord))
    conds.append(_mk("C7", exch, f"exchange {planet}-{dep_lord}"))
    return conds


def has_neecha_bhanga(ctx, planet: str) -> bool:
    return any(c["met"] for c in neecha_bhanga_conditions(ctx, planet))


def _debilitated_planets(ctx) -> List[str]:
    return [p for p in SEVEN if ctx.is_debilitated(p)]


def _prov(method: str, notes: str) -> Provenance:
    return Provenance(
        source_type=SourceType.CLASSICAL_TEXT,
        source_name="Brihat Parashara Hora Shastra",
        source_reference="UNVERIFIED",
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        method=method, implementation_version="1.0.0", notes=notes,
    )


def build_neecha_bhanga() -> RuleDefinition:
    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id="PARASHARI.YOGA.NEECHA_BHANGA", rule_version="1.0.0",
            name="Neecha Bhanga (Debilitation Cancellation)",
            category=RuleCategory.YOGA, tradition=RuleTradition.PARASHARI_CLASSICAL,
            school_method="Parashari Classical", status=RuleStatus.ENABLED,
            description="A debilitated planet with at least one classical "
                        "cancellation (C1-C7). D9 strength alone never qualifies.",
            provenance=_prov(
                "neecha_bhanga_C1_C7",
                "Traditional attribution (UNVERIFIED exact verse). C1-C4 core; "
                "C5-C7 commentarial variance documented. D9-only shortcut excluded."),
            confidence=ConfidenceLevel.HIGH,
            tags=["neecha_bhanga", "debilitated"], enabled=True),
        formation_conditions=[Condition(type="parashari_neecha_bhanga_formation", params={})],
        strength_conditions=[], activation_rules=[],
        cancellation_rules=[], mitigation_rules=[MitigationRule(
            rule_id="PARASHARI.YOGA.NEECHA_BHANGA.MITIG",
            description="Bhanga itself mitigates debilitation",
            evaluator="parashari_mitigation_generic", strength_impact="significant")],
        required_evidence=[EvidenceType.PLANET_DIGNITY],
    )


def build_neecha_bhanga_raja() -> RuleDefinition:
    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id="PARASHARI.YOGA.NEECHA_BHANGA_RAJA", rule_version="1.0.0",
            name="Neecha Bhanga Raja Yoga",
            category=RuleCategory.YOGA, tradition=RuleTradition.PARASHARI_CLASSICAL,
            school_method="Parashari Classical", status=RuleStatus.ENABLED,
            description="Neecha Bhanga planet additionally placed in Kendra/Trikona from Lagna.",
            provenance=_prov(
                "neecha_bhanga_raja_kendra_trikona",
                "Traditional attribution (UNVERIFIED exact verse). Raja qualification "
                "requires Kendra/Trikona occupancy; D9-only promotion excluded."),
            confidence=ConfidenceLevel.HIGH,
            tags=["neecha_bhanga", "raja_yoga"], enabled=True),
        formation_conditions=[Condition(type="parashari_neecha_bhanga_raja_formation", params={})],
        strength_conditions=[], activation_rules=[],
        cancellation_rules=[CancellationRule(
            rule_id="PARASHARI.YOGA.NEECHA_BHANGA_RAJA.CANCEL",
            description="Generic cancellation scan",
            evaluator="parashari_cancellation_generic", is_partial=True)],
        mitigation_rules=[MitigationRule(
            rule_id="PARASHARI.YOGA.NEECHA_BHANGA_RAJA.MITIG",
            description="Generic mitigation scan",
            evaluator="parashari_mitigation_generic", strength_impact="partial")],
        required_evidence=[EvidenceType.PLANET_DIGNITY, EvidenceType.KENDRA_TRIKONA],
    )


def _ev_for(ctx, planet: str) -> List[Evidence]:
    ev: List[Evidence] = []
    for c in neecha_bhanga_conditions(ctx, planet):
        ev.append(Evidence(
            evidence_type=EvidenceType.PLANET_DIGNITY,
            subject=f"{planet} bhanga {c['id']}",
            value="met" if c["met"] else "not_met",
            expected="cancellation condition", actual=c["detail"],
            source="ChartFacts" if c["id"] != "NOT_DEBILITATED" else "StrengthReport",
            significance=f"{planet} {c['id']}: {c['detail']}",
            details={"condition": c["id"], "d9_ignored_by_design": True}))
    return ev


def neecha_bhanga_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    debilitated = _debilitated_planets(ctx)
    if not debilitated:
        return False, [Evidence(
            evidence_type=EvidenceType.PLANET_DIGNITY, subject="Neecha Bhanga scan",
            value="no debilitated planet", expected="a debilitated planet",
            actual="none", source="StrengthReport",
            significance="no debilitation, no bhanga")]
    ev: List[Evidence] = []
    formed = False
    for planet in debilitated:
        ev.append(Evidence(
            evidence_type=EvidenceType.PLANET_DIGNITY, subject=f"{planet} debilitated",
            value=sign_of(ctx, planet), expected=DEBILITATION_SIGN.get(planet),
            actual=sign_of(ctx, planet), source="StrengthReport",
            significance=f"{planet} debilitated in {sign_of(ctx, planet)}"))
        planet_ev = _ev_for(ctx, planet)
        ev.extend(planet_ev)
        if has_neecha_bhanga(ctx, planet):
            formed = True
    return formed, ev


def neecha_bhanga_raja_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    debilitated = _debilitated_planets(ctx)
    if not debilitated:
        return False, [Evidence(
            evidence_type=EvidenceType.PLANET_DIGNITY, subject="NBRY scan",
            value="no debilitated planet", expected="debilitated planet in Kendra/Trikona",
            actual="none", source="StrengthReport", significance="no candidate")]
    ev: List[Evidence] = []
    formed = False
    for planet in debilitated:
        bhanga = has_neecha_bhanga(ctx, planet)
        h = house_of(ctx, planet)
        placed = h is not None and (is_kendra_house(h) or is_trikona_house(h))
        ev.extend(_ev_for(ctx, planet))
        ev.append(Evidence(
            evidence_type=EvidenceType.KENDRA_TRIKONA,
            subject=f"{planet} Raja placement",
            value=h, expected="Kendra/Trikona from Lagna", actual=f"house {h}",
            source="ChartFacts",
            significance=f"{planet} qualifies for Raja" if (bhanga and placed)
                         else f"{planet} bhanga={bhanga} placed={placed}"))
        if bhanga and placed:
            formed = True
    return formed, ev


FORMATION_EVALUATORS = {
    "parashari_neecha_bhanga_formation": neecha_bhanga_formation,
    "parashari_neecha_bhanga_raja_formation": neecha_bhanga_raja_formation,
}
