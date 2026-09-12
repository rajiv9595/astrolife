"""
Phase 5B-3C — Category D yogas (Migration #3C implementation).

15 valid traditional Yogas requiring engine extension beyond the
Migration #3B primitive set:

- Nabha distribution primitive (new, reusable): seven-planet sign
  distribution consumed by Dama/Gola/Kedara/Pasha/Shula/Veena/Yuga.
- Malefic-occupancy + canonical lord-strength: Astra/Asura.
- Four-house occupancy pattern: Bheri.
- Named Venus-Mars conjunction: Bhrigu Mangala.
- Multi-planet relational chains: Brahma, Indra.
- Six-house benefic/malefic distribution: Kurma.
- Three-kendra malefic pattern: Sarpa.

No astronomy, no legacy calls, no Category E logic. Every formation
consumes RuleContext facts only. Canonical lord-strength semantics are
reused from classical_yogas (single definition, no duplication).
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from ..models import (
    RuleDefinition, RuleMetadata, Provenance, Evidence,
    CancellationRule, MitigationRule, Condition,
)
from ..enums import (
    RuleCategory, RuleTradition, RuleStatus, ConfidenceLevel,
    SourceType, EvidenceType,
)
from .structural import (
    KENDRA_HOUSES,
    house_of, sign_of, lord_of_house,
    moon_house,
    house_from_moon, house_from_planet, is_kendra_from_planet,
    NATURAL_BENEFICS, NATURAL_MALEFICS, SEVEN_PLANETS,
)
from .classical_yogas import _lord_strength_evidence


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
          confidence: ConfidenceLevel, formation_type: str, tags: List[str],
          required: List[EvidenceType]) -> RuleDefinition:
    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id=rule_id, rule_version="1.0.0", name=name,
            category=RuleCategory.YOGA, tradition=RuleTradition.PARASHARI_CLASSICAL,
            school_method="Parashari Classical", status=RuleStatus.ENABLED,
            description=desc, provenance=_prov(method, notes),
            confidence=confidence, tags=tags, enabled=True),
        formation_conditions=[Condition(type=formation_type, params={})],
        strength_conditions=[], activation_rules=[],
        cancellation_rules=[CancellationRule(
            rule_id=f"{rule_id}.CANCEL", description="Debilitation/Dusthana/malefic check",
            evaluator="parashari_cancellation_generic", is_partial=True)],
        mitigation_rules=[MitigationRule(
            rule_id=f"{rule_id}.MITIG", description="Benefic/dignity/house support",
            evaluator="parashari_mitigation_generic", strength_impact="partial")],
        required_evidence=required,
    )


# ---------------- new reusable primitive: Nabha distribution ----------------

#: Classical seven planets counted for Nabha distribution (nodes excluded).
NABHASA_PLANETS: Tuple[str, ...] = SEVEN_PLANETS


def nabhasa_sign_distribution(ctx) -> Dict[str, str]:
    """Reusable canonical Nabha representation: seven-planet sidereal signs.

    Sign-based only (whole-sign D1 placements from ChartFacts). Rahu/Ketu
    are never counted. Deterministic: fixed planet order.
    """
    dist: Dict[str, str] = {}
    for p in NABHASA_PLANETS:
        sign = sign_of(ctx, p)
        if sign:
            dist[p] = sign
    return dist


def nabhasa_occupied_sign_count(ctx) -> int:
    """Number of distinct signs occupied by the seven classical planets."""
    return len(set(nabhasa_sign_distribution(ctx).values()))


def _nabhasa_evidence(ctx, method: str, label: str) -> Tuple[Dict[str, str], int, List[Evidence]]:
    dist = nabhasa_sign_distribution(ctx)
    count = len(set(dist.values()))
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_SIGN,
        subject=f"Seven-planet signs ({label})",
        value={p: dist.get(p) for p in NABHASA_PLANETS},
        expected="sign distribution of Sun..Saturn (nodes excluded)",
        actual=f"{count} occupied signs: {sorted(set(dist.values()))}",
        source="ChartFacts",
        significance=f"{count} signs occupied by the seven planets",
        details={"method": method, "occupied_count": count})]
    return dist, count, ev


# ---------------- small local occupancy helpers ----------------

def _malefics_in_house(ctx, house: int) -> List[str]:
    return [p for p in ctx.get_planets_in_house(house) if p in NATURAL_MALEFICS]


def _benefics_in_house(ctx, house: int) -> List[str]:
    return [p for p in ctx.get_planets_in_house(house) if p in NATURAL_BENEFICS]


def _occupancy_evidence(ctx, house: int, occupants: List[str], kind: str,
                        method: str, label: str) -> Evidence:
    return Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject=label,
        value=house, expected=kind, actual=f"house {house}: {occupants or 'none'}",
        source="ChartFacts",
        significance=f"{label}: {', '.join(occupants) if occupants else 'none'}",
        details={"method": method, "house": house, "occupants": occupants})


# ---------------- builders (15) ----------------

def build_astra() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.ASTRA", "Astra Yoga",
        "A natural malefic occupies the 6th house and the 6th lord is strong "
        "(canonical lord-strength).",
        "malefic_6th_sixth_lord_strong",
        "Traditional attribution (UNVERIFIED exact verse). Conjunctive reading of "
        "the ruleset description; the legacy code checked the lord alone and "
        "dropped the malefic clause (documented legacy implementation defect).",
        ConfidenceLevel.MEDIUM, "parashari_astra_formation",
        ["astra"],
        [EvidenceType.PLANET_IN_HOUSE, EvidenceType.HOUSE_LORD_POSITION])


def build_asura() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.ASURA", "Asura Yoga",
        "A natural malefic occupies the 8th house and the 8th lord is strong "
        "(canonical lord-strength).",
        "malefic_8th_eighth_lord_strong",
        "Traditional attribution (UNVERIFIED exact verse). Conjunctive reading of "
        "the ruleset description; the legacy code checked the lord alone and "
        "dropped the malefic clause (documented legacy implementation defect).",
        ConfidenceLevel.MEDIUM, "parashari_asura_formation",
        ["asura"],
        [EvidenceType.PLANET_IN_HOUSE, EvidenceType.HOUSE_LORD_POSITION])


def build_bheri() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.BHERI", "Bheri Yoga",
        "Each of the houses 1, 2, 7 and 12 is occupied by at least one of the "
        "seven classical planets (nodes excluded per Nabhasa convention).",
        "houses_1_2_7_12_occupied",
        "Traditional attribution (UNVERIFIED exact verse). Four-house pattern per "
        "Migration #3B analysis; the legacy condition key was unhandled so the "
        "legacy rule never fired (documented legacy implementation defect).",
        ConfidenceLevel.MEDIUM, "parashari_bheri_formation",
        ["bheri"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_bhrigu_mangala() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.BHRIGU_MANGALA", "Bhrigu Mangala Yoga",
        "Venus and Mars in the same whole-sign house (named conjunction).",
        "venus_mars_same_house",
        "Traditional attribution (UNVERIFIED exact verse). Same-house = "
        "conjunction per canonical Budha-Aditya precedent; Parashari aspect "
        "does not qualify.",
        ConfidenceLevel.HIGH, "parashari_bhrigu_mangala_formation",
        ["bhrigu_mangala", "venus", "mars"],
        [EvidenceType.CONJUNCTION])


def build_brahma() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.BRAHMA", "Brahma Yoga",
        "Jupiter, Venus and Mercury each in a Kendra counted from the Lagna "
        "lord's house.",
        "jupiter_venus_mercury_kendra_from_lagna_lord",
        "Traditional attribution (UNVERIFIED exact verse). Each of the three "
        "planet-to-Lagna-lord relationships is evaluated and evidenced "
        "individually; no clause collapsed.",
        ConfidenceLevel.HIGH, "parashari_brahma_formation",
        ["brahma"],
        [EvidenceType.KENDRA_TRIKONA, EvidenceType.LORDSHIP_RELATIONSHIP])


def build_dama() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.DAMA", "Dama Yoga",
        "The seven classical planets occupy exactly 6 different signs (Nabha).",
        "nabha_exactly_6_signs",
        "Traditional attribution (UNVERIFIED exact verse). Sign-based count of "
        "Sun..Saturn; nodes excluded. Legacy nabha key was unhandled "
        "(legacy rule never fired).",
        ConfidenceLevel.HIGH, "parashari_dama_formation",
        ["dama", "nabha", "nabhasa"],
        [EvidenceType.PLANET_IN_SIGN])


def build_gola() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.GOLA", "Gola Yoga",
        "The seven classical planets occupy exactly 1 sign (Nabha).",
        "nabha_exactly_1_sign",
        "Traditional attribution (UNVERIFIED exact verse). Sign-based count of "
        "Sun..Saturn; nodes excluded. Legacy nabha key was unhandled.",
        ConfidenceLevel.HIGH, "parashari_gola_formation",
        ["gola", "nabha", "nabhasa"],
        [EvidenceType.PLANET_IN_SIGN])


def build_indra() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.INDRA", "Indra Yoga",
        "Mars in the 3rd from the Moon, Saturn in the 7th from Mars, Venus in "
        "the 7th from Saturn (Moon → Mars → Saturn → Venus chain).",
        "moon_mars_saturn_venus_chain",
        "Traditional attribution (UNVERIFIED exact verse). All three chain links "
        "encoded and evidenced individually; not approximated by conjunction.",
        ConfidenceLevel.HIGH, "parashari_indra_formation",
        ["indra"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_kedara() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.KEDARA", "Kedara Yoga",
        "The seven classical planets occupy exactly 4 different signs (Nabha).",
        "nabha_exactly_4_signs",
        "Traditional attribution (UNVERIFIED exact verse). Sign-based count of "
        "Sun..Saturn; nodes excluded. Legacy nabha key was unhandled.",
        ConfidenceLevel.HIGH, "parashari_kedara_formation",
        ["kedara", "nabha", "nabhasa"],
        [EvidenceType.PLANET_IN_SIGN])


def build_kurma() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.KURMA", "Kurma Yoga",
        "A natural benefic in each of the houses 5, 6 and 7, and a natural "
        "malefic in each of the houses 1, 3 and 11.",
        "benefics_567_malefics_1_3_11",
        "Traditional attribution (UNVERIFIED exact verse). Strict all-houses "
        "reading per ruleset description and legacy pattern; no loose "
        "approximation. Malefic set is the canonical natural set (nodes count "
        "as malefics per existing definition).",
        ConfidenceLevel.HIGH, "parashari_kurma_formation",
        ["kurma"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_pasha() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.PASHA", "Pasha Yoga",
        "The seven classical planets occupy exactly 5 different signs (Nabha).",
        "nabha_exactly_5_signs",
        "Traditional attribution (UNVERIFIED exact verse). Sign-based count of "
        "Sun..Saturn; nodes excluded. Legacy nabha key was unhandled.",
        ConfidenceLevel.HIGH, "parashari_pasha_formation",
        ["pasha", "nabha", "nabhasa"],
        [EvidenceType.PLANET_IN_SIGN])


def build_sarpa() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.SARPA", "Sarpa Yoga",
        "Natural malefics occupying at least 3 Kendra houses (Nabhasa).",
        "malefics_in_three_kendras",
        "Traditional attribution (UNVERIFIED exact verse). Threshold >=3 per "
        "ruleset description and legacy predicate. Malefic set is the canonical "
        "natural set, which explicitly includes Rahu/Ketu; nodes therefore "
        "count when present in a Kendra.",
        ConfidenceLevel.MEDIUM, "parashari_sarpa_formation",
        ["sarpa", "nabhasa"],
        [EvidenceType.KENDRA_TRIKONA, EvidenceType.PLANET_IN_HOUSE])


def build_shula() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.SHULA", "Shula Yoga",
        "The seven classical planets occupy exactly 3 different signs (Nabha).",
        "nabha_exactly_3_signs",
        "Traditional attribution (UNVERIFIED exact verse). Sign-based count of "
        "Sun..Saturn; nodes excluded. Legacy nabha key was unhandled.",
        ConfidenceLevel.HIGH, "parashari_shula_formation",
        ["shula", "nabha", "nabhasa"],
        [EvidenceType.PLANET_IN_SIGN])


def build_veena() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.VEENA", "Veena Yoga",
        "The seven classical planets occupy exactly 7 different signs (Nabha).",
        "nabha_exactly_7_signs",
        "Traditional attribution (UNVERIFIED exact verse). Sign-based count of "
        "Sun..Saturn; nodes excluded. Legacy nabha key was unhandled.",
        ConfidenceLevel.HIGH, "parashari_veena_formation",
        ["veena", "nabha", "nabhasa"],
        [EvidenceType.PLANET_IN_SIGN])


def build_yuga() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.YUGA", "Yuga Yoga",
        "The seven classical planets occupy exactly 2 different signs (Nabha).",
        "nabha_exactly_2_signs",
        "Traditional attribution (UNVERIFIED exact verse). Sign-based count of "
        "Sun..Saturn; nodes excluded. Legacy nabha key was unhandled.",
        ConfidenceLevel.HIGH, "parashari_yuga_formation",
        ["yuga", "nabha", "nabhasa"],
        [EvidenceType.PLANET_IN_SIGN])


# ---------------- formation evaluators ----------------

def _malefic_lord_formation(ctx, house_num: int, method: str,
                             label: str) -> Tuple[bool, List[Evidence]]:
    """'<malefic> in <N>th + <N>th lord strong' pattern (Astra/Asura)."""
    occ = _malefics_in_house(ctx, house_num)
    lord, strong, ev = _lord_strength_evidence(ctx, house_num, method)
    ev.append(_occupancy_evidence(
        ctx, house_num, occ, "a natural malefic", method,
        f"Malefic in {house_num}th house ({label})"))
    return bool(occ and strong), ev


def astra_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _malefic_lord_formation(ctx, 6, "malefic_6th_sixth_lord_strong", "Astra")


def asura_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _malefic_lord_formation(ctx, 8, "malefic_8th_eighth_lord_strong", "Asura")


def bheri_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ev: List[Evidence] = []
    ok_all = True
    for h in (1, 2, 7, 12):
        occ = [p for p in SEVEN_PLANETS if house_of(ctx, p) == h]
        hit = bool(occ)
        ok_all = ok_all and hit
        ev.append(_occupancy_evidence(
            ctx, h, occ, "a classical planet", "houses_1_2_7_12_occupied",
            f"Planet in house {h} (Bheri)"))
    ev.append(Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="Bheri scan",
        value="all occupied" if ok_all else "missing",
        expected="planets in 1st, 2nd, 7th and 12th",
        actual="all occupied" if ok_all else "missing",
        source="ChartFacts",
        significance="Bheri formed" if ok_all else "Bheri not formed",
        details={"method": "houses_1_2_7_12_occupied"}))
    return ok_all, ev


def bhrigu_mangala_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    hv, hm = house_of(ctx, "Venus"), house_of(ctx, "Mars")
    ok = hv is not None and hv == hm
    ev = [Evidence(
        evidence_type=EvidenceType.CONJUNCTION,
        subject="Venus-Mars Bhrigu Mangala",
        value={"venus_house": hv, "mars_house": hm},
        expected="same whole-sign house",
        actual=f"houses {hv}/{hm}",
        source="ChartFacts",
        significance="Bhrigu Mangala formed" if ok else "Venus and Mars not conjunct",
        details={"method": "venus_mars_same_house"})]
    return ok, ev


def brahma_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    l1 = lord_of_house(ctx, 1)
    if not l1:
        return False, []
    h_l1 = house_of(ctx, l1)
    ev: List[Evidence] = []
    ok_all = True
    for p in ("Jupiter", "Venus", "Mercury"):
        off = house_from_planet(ctx, l1, p)
        hit = off is not None and off in (1, 4, 7, 10)
        ok_all = ok_all and hit
        ev.append(Evidence(
            evidence_type=EvidenceType.KENDRA_TRIKONA,
            subject=f"{p} from Lagna lord {l1}",
            value=off, expected="Kendra (1,4,7,10) from Lagna lord",
            actual=f"{off} from {l1} (house {h_l1})",
            source="ChartFacts",
            significance=f"{p} in Kendra from Lagna lord" if hit
            else f"{p} not in Kendra from Lagna lord",
            details={"method": "jupiter_venus_mercury_kendra_from_lagna_lord",
                     "lord": l1}))
    return ok_all, ev


def _nabha_count_formation(ctx, count: int, method: str,
                            label: str) -> Tuple[bool, List[Evidence]]:
    dist, n, ev = _nabhasa_evidence(ctx, method, label)
    ok = n == count
    ev.append(Evidence(
        evidence_type=EvidenceType.PLANET_IN_SIGN, subject=f"{label} count",
        value=n, expected=f"exactly {count} signs", actual=n,
        source="ChartFacts",
        significance=f"{label} formed" if ok else f"{label} not formed ({n} signs)",
        details={"method": method}))
    return ok, ev


def dama_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _nabha_count_formation(ctx, 6, "nabha_exactly_6_signs", "Dama")


def gola_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _nabha_count_formation(ctx, 1, "nabha_exactly_1_sign", "Gola")


def kedara_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _nabha_count_formation(ctx, 4, "nabha_exactly_4_signs", "Kedara")


def pasha_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _nabha_count_formation(ctx, 5, "nabha_exactly_5_signs", "Pasha")


def shula_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _nabha_count_formation(ctx, 3, "nabha_exactly_3_signs", "Shula")


def veena_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _nabha_count_formation(ctx, 7, "nabha_exactly_7_signs", "Veena")


def yuga_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _nabha_count_formation(ctx, 2, "nabha_exactly_2_signs", "Yuga")


def indra_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    link1 = house_from_moon(ctx, "Mars")
    link2 = house_from_planet(ctx, "Mars", "Saturn")
    link3 = house_from_planet(ctx, "Saturn", "Venus")
    hit1 = link1 == 3
    hit2 = link2 == 7
    hit3 = link3 == 7
    ok = bool(hit1 and hit2 and hit3)
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject="Mars 3rd from Moon (Indra link 1)",
        value=link1, expected=3,
        actual=f"Mars house {house_of(ctx, 'Mars')}, Moon house {moon_house(ctx)}",
        source="ChartFacts",
        significance="Link 1 holds" if hit1 else "Link 1 fails",
        details={"method": "moon_mars_saturn_venus_chain"}),
        Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject="Saturn 7th from Mars (Indra link 2)",
        value=link2, expected=7,
        actual=f"Saturn house {house_of(ctx, 'Saturn')}, Mars house {house_of(ctx, 'Mars')}",
        source="ChartFacts",
        significance="Link 2 holds" if hit2 else "Link 2 fails",
        details={"method": "moon_mars_saturn_venus_chain"}),
        Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject="Venus 7th from Saturn (Indra link 3)",
        value=link3, expected=7,
        actual=f"Venus house {house_of(ctx, 'Venus')}, Saturn house {house_of(ctx, 'Saturn')}",
        source="ChartFacts",
        significance="Link 3 holds" if hit3 else "Link 3 fails",
        details={"method": "moon_mars_saturn_venus_chain"})]
    return ok, ev


def kurma_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ev: List[Evidence] = []
    ok_all = True
    for h in (5, 6, 7):
        found = _benefics_in_house(ctx, h)
        hit = bool(found)
        ok_all = ok_all and hit
        ev.append(_occupancy_evidence(
            ctx, h, found, "a natural benefic",
            "benefics_567_malefics_1_3_11", f"Benefic in {h}th (Kurma)"))
    for h in (1, 3, 11):
        found = _malefics_in_house(ctx, h)
        hit = bool(found)
        ok_all = ok_all and hit
        ev.append(_occupancy_evidence(
            ctx, h, found, "a natural malefic",
            "benefics_567_malefics_1_3_11", f"Malefic in {h} (Kurma)"))
    return ok_all, ev


def sarpa_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ev: List[Evidence] = []
    count = 0
    for k in KENDRA_HOUSES:
        found = _malefics_in_house(ctx, k)
        if found:
            count += 1
        ev.append(_occupancy_evidence(
            ctx, k, found, "a natural malefic",
            "malefics_in_three_kendras", f"Malefic in Kendra {k}"))
    ok = count >= 3
    ev.append(Evidence(
        evidence_type=EvidenceType.KENDRA_TRIKONA, subject="Sarpa kendra count",
        value=count, expected=">=3 Kendras with malefics", actual=count,
        source="ChartFacts",
        significance="Sarpa formed" if ok else "Sarpa not formed",
        details={"method": "malefics_in_three_kendras"}))
    return ok, ev


FORMATION_EVALUATORS = {
    "parashari_astra_formation": astra_formation,
    "parashari_asura_formation": asura_formation,
    "parashari_bheri_formation": bheri_formation,
    "parashari_bhrigu_mangala_formation": bhrigu_mangala_formation,
    "parashari_brahma_formation": brahma_formation,
    "parashari_dama_formation": dama_formation,
    "parashari_gola_formation": gola_formation,
    "parashari_indra_formation": indra_formation,
    "parashari_kedara_formation": kedara_formation,
    "parashari_kurma_formation": kurma_formation,
    "parashari_pasha_formation": pasha_formation,
    "parashari_sarpa_formation": sarpa_formation,
    "parashari_shula_formation": shula_formation,
    "parashari_veena_formation": veena_formation,
    "parashari_yuga_formation": yuga_formation,
}


def build_category_d_catalog() -> List[RuleDefinition]:
    return [
        build_astra(), build_asura(), build_bheri(),
        build_bhrigu_mangala(), build_brahma(), build_dama(),
        build_gola(), build_indra(), build_kedara(),
        build_kurma(), build_pasha(), build_sarpa(),
        build_shula(), build_veena(), build_yuga(),
    ]


CATEGORY_D_YOGA_RULE_IDS: List[str] = [
    r.metadata.rule_id for r in build_category_d_catalog()
]


def register_category_d_yoga_provenance() -> int:
    """Register Category D provenance records (idempotent)."""
    from ..provenance import ProvenanceRegistry, create_provenance_from_rule
    n = 0
    for rule in build_category_d_catalog():
        ProvenanceRegistry.register(create_provenance_from_rule(rule))
        n += 1
    return n


register_category_d_yoga_provenance()
