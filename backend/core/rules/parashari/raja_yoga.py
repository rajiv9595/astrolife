"""
Phase 5B — Raja Yoga structures (Kendra/Trikona sambandha, Dharma-Karmadhipati,
Yogakaraka Raja). Formation only; strength/cancellation handled centrally.
"""
from __future__ import annotations
from typing import List, Tuple

from ..models import (
    RuleDefinition, RuleMetadata, Provenance, Evidence,
    ActivationRule, CancellationRule, MitigationRule, Condition,
)
from ..enums import (
    RuleCategory, RuleTradition, RuleStatus, ConfidenceLevel,
    SourceType, EvidenceType,
)
from .structural import (
    KENDRA_HOUSES, TRIKONA_HOUSES, house_of, lords_sambandha, is_kendra_house,
    is_trikona_house,
)


def _prov(method: str, notes: str) -> Provenance:
    return Provenance(
        source_type=SourceType.CLASSICAL_TEXT,
        source_name="Brihat Parashara Hora Shastra",
        source_reference="UNVERIFIED",
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        method=method,
        implementation_version="1.0.0",
        notes=notes,
    )


def _base(rule_id: str, name: str, desc: str, method: str, notes: str,
          confidence: ConfidenceLevel, formation_type: str, tags: List[str]) -> RuleDefinition:
    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id=rule_id, rule_version="1.0.0", name=name,
            category=RuleCategory.YOGA, tradition=RuleTradition.PARASHARI_CLASSICAL,
            school_method="Parashari Classical", status=RuleStatus.ENABLED,
            description=desc, provenance=_prov(method, notes),
            confidence=confidence, tags=tags, enabled=True,
        ),
        formation_conditions=[Condition(type=formation_type, params={})],
        strength_conditions=[],
        activation_rules=[],
        cancellation_rules=[CancellationRule(
            rule_id=f"{rule_id}.CANCEL", description="Debilitation/Dusthana/malefic check",
            evaluator="parashari_cancellation_generic", is_partial=True)],
        mitigation_rules=[MitigationRule(
            rule_id=f"{rule_id}.MITIG", description="Benefic/dignity/house support",
            evaluator="parashari_mitigation_generic", strength_impact="partial")],
        required_evidence=[EvidenceType.LORDSHIP_RELATIONSHIP, EvidenceType.PLANET_DIGNITY],
    )


def build_raja_kendra_trikona() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.RAJA_KENDRA_TRIKONA", "Raja Yoga (Kendra-Trikona Sambandha)",
        "Any Kendra lord and Trikona lord (different planets) in conjunction, "
        "mutual Parashari aspect, or sign exchange; same-lord case needs Kendra/Trikona occupancy.",
        "kendra_trikona_sambandha",
        "Traditional attribution: BPHS Raja Yoga adhyaya (edition-dependent; UNVERIFIED exact verse). "
        "Narrow 3-sambandha reading; mutual-kendra-occupancy variant omitted.",
        ConfidenceLevel.HIGH, "parashari_raja_kendra_trikona_formation",
        ["raja_yoga", "kendra", "trikona"],
    )


def build_dharma_karmadhipati() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.DHARMA_KARMADHIPATI", "Dharma-Karmadhipati Yoga",
        "9th and 10th lords in conjunction, mutual aspect, or exchange. "
        "Evidence records the exact relationship_type.",
        "sambandha_9_10",
        "Traditional attribution: BPHS Raja Yoga adhyaya (UNVERIFIED exact verse). "
        "Conjunction/mutual-aspect/exchange only; mutual-kendra occupancy omitted.",
        ConfidenceLevel.HIGH, "parashari_dharma_karmadhipati_formation",
        ["raja_yoga", "dharma", "karma", "9th_lord", "10th_lord"],
    )


def build_yogakaraka_raja() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.YOGAKARAKA_RAJA", "Yogakaraka Raja Yoga",
        "Yogakaraka planet (rules both Kendra and Trikona per Phase 4) placed in Kendra or Trikona.",
        "yogakaraka_in_kendra_trikona",
        "Functional lordship from Phase 4 engine; classical Yogakaraka doctrine (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_yogakaraka_raja_formation",
        ["raja_yoga", "yogakaraka"],
    )


# ---------------- formation evaluators ----------------

def _ev_lordship(house1: int, house2: int, lord1, lord2, kind: str, detail: str) -> Evidence:
    return Evidence(
        evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
        subject=f"Lords of {house1} ({lord1}) and {house2} ({lord2})",
        value=kind, expected="conjunction/mutual_aspect/exchange",
        actual=f"{kind}: {detail}", source="ChartFacts",
        significance=f"9/10-type sambandha: {kind}" if {house1, house2} == {9, 10} else f"sambandha: {kind}",
        details={"house1": house1, "house2": house2, "lord1": lord1, "lord2": lord2,
                 "relationship_type": kind},
    )


def raja_kendra_trikona_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    evidence: List[Evidence] = []
    hits = []
    for kh in KENDRA_HOUSES:
        for th in TRIKONA_HOUSES:
            if kh == th:
                continue  # same house is not a Kendra-Trikona pair
            kind, lord1, lord2, detail = lords_sambandha(ctx, kh, th)
            if kind in ("conjunction", "mutual_aspect", "exchange"):
                hits.append((kh, th, lord1, lord2, kind, detail))
                evidence.append(_ev_lordship(kh, th, lord1, lord2, kind, detail))
            elif kind == "same_lord":
                h = house_of(ctx, lord1)
                if h is not None and (is_kendra_house(h) or is_trikona_house(h)):
                    hits.append((kh, th, lord1, lord2, "same_lord_placed", f"{lord1} in {h}"))
                    evidence.append(Evidence(
                        evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
                        subject=f"Single lord {lord1} of {kh} and {th}",
                        value="same_lord_placed", expected="Kendra/Trikona occupancy",
                        actual=f"house {h}", source="ChartFacts",
                        significance=f"{lord1} rules both, placed in {h}",
                        details={"relationship_type": "same_lord_placed"}))
    if not hits:
        evidence.append(Evidence(
            evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
            subject="Kendra-Trikona sambandha scan",
            value="none", expected="a Kendra-Trikona sambandha",
            actual="none found", source="ChartFacts",
            significance="no Kendra-Trikona lord sambandha",
            details={"relationship_type": "none"}))
        return False, evidence
    return True, evidence


def dharma_karmadhipati_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    kind, lord1, lord2, detail = lords_sambandha(ctx, 9, 10)
    if kind in ("conjunction", "mutual_aspect", "exchange"):
        return True, [_ev_lordship(9, 10, lord1, lord2, kind, detail)]
    if kind == "same_lord":
        h = house_of(ctx, lord1)
        if h is not None and (is_kendra_house(h) or is_trikona_house(h)):
            return True, [Evidence(
                evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
                subject=f"Single lord {lord1} of 9 and 10",
                value="same_lord_placed", expected="Kendra/Trikona occupancy",
                actual=f"house {h}", source="ChartFacts",
                significance=f"Yogakaraka-like {lord1} in {h}",
                details={"relationship_type": "same_lord_placed"})]
        return False, [Evidence(
            evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
            subject=f"Single lord {lord1} of 9 and 10",
            value="same_lord_misplaced", expected="Kendra/Trikona occupancy",
            actual=f"house {h}", source="ChartFacts",
            significance=f"{lord1} rules 9+10 but placed in {h}",
            details={"relationship_type": "same_lord_misplaced"})]
    return False, [_ev_lordship(9, 10, lord1, lord2, "none", detail)]


def yogakaraka_raja_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    # Classical Yogakaraka for this yoga: must rule a non-Lagna Kendra
    # (4/7/10) AND a non-Lagna Trikona (5/9). This excludes Lagna-lord-only
    # cases (e.g. Taurus Venus ruling 1+6 via house 1 counting as both).
    evidence: List[Evidence] = []
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        if ctx.is_yogakaraka(planet):
            ruled = set(ctx.get_houses_ruled_by(planet))
            classical_yk = bool(ruled & {4, 7, 10}) and bool(ruled & {5, 9})
            h = house_of(ctx, planet)
            if not classical_yk:
                evidence.append(Evidence(
                    evidence_type=EvidenceType.YOGAKARAKA,
                    subject=f"Yogakaraka {planet} (non-classical scope)",
                    value=f"rules {sorted(ruled)}", expected="non-Lagna Kendra + Trikona",
                    actual=f"rules {sorted(ruled)}", source="StrengthReport",
                    significance=f"{planet} is functional Yogakaraka but rules no "
                                 f"non-Lagna Kendra+Trikona pair; excluded from this yoga",
                    details={"houses_ruled": sorted(ruled)}))
                continue
            ok = h is not None and (is_kendra_house(h) or is_trikona_house(h))
            evidence.append(Evidence(
                evidence_type=EvidenceType.YOGAKARAKA,
                subject=f"Yogakaraka {planet}",
                value=f"house {h}", expected="Kendra/Trikona",
                actual=f"house {h}", source="StrengthReport",
                significance=f"Yogakaraka {planet} in {h}" if ok else f"Yogakaraka {planet} misplaced in {h}",
                details={"houses_ruled": ctx.get_houses_ruled_by(planet)}))
            if ok:
                return True, evidence
    if not evidence:
        evidence.append(Evidence(
            evidence_type=EvidenceType.YOGAKARAKA, subject="Yogakaraka scan",
            value="none", expected="a Yogakaraka planet", actual="none",
            source="StrengthReport", significance="no Yogakaraka for this ascendant"))
    return False, evidence


FORMATION_EVALUATORS = {
    "parashari_raja_kendra_trikona_formation": raja_kendra_trikona_formation,
    "parashari_dharma_karmadhipati_formation": dharma_karmadhipati_formation,
    "parashari_yogakaraka_raja_formation": yogakaraka_raja_formation,
}
