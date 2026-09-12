"""
Phase 5B-3B — Category C classical yogas (Migration #3B implementation).

31 Yogas derivable from existing canonical primitives. No new primitives,
no astronomy, no legacy calls. Every formation consumes RuleContext only
(lordship, house_position, sign_type/dignity, conjunction/same-house,
aspect, kendra/trikona, planet_relationship, benefic/malefic
classification, strength/shadbala, dispositor, house_from_sun/moon,
empty_house_check).

Conventions reused from the existing canonical engine:
- "lord strong" mirrors Lakshmi's lagna_strong: exalted / own /
  moolatrikona / Kendra-or-Trikona occupancy / Shadbala ratio >= 1.0.
  (Legacy yoga_evaluator used exalted/own/kendra only; the delta is
  documented per rule and in MIGRATION_3B_IMPLEMENTATION_FINAL_REPORT.md.)
- Same whole-sign house = conjunction (cf. Budha-Aditya _same_house).
- Parashari aspects via RuleContext (special aspects included).
- house_from_sun / house_from_moon exclude Moon/Rahu/Ketu and Sun/Rahu/Ketu
  respectively, per structural helpers and classical definition.
- Strength graded centrally (strength.py); activation NOT_EVALUATED;
  generic cancellation/mitigation evaluators like all other Parashari rules.
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
    KENDRA_HOUSES, TRIKONA_HOUSES,
    house_of, sign_of, lord_of_house,
    moon_house, sun_house,
    is_kendra_from_moon, is_kendra_from_planet, is_6_8_12_from,
    planets_in_house_from_moon, planets_in_house_from_sun,
    planets_in_house_from_planet,
    NATURAL_BENEFICS, NATURAL_MALEFICS, SEVEN_PLANETS,
    SIGN_LORDS,
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


# ---------------- shared canonical helpers ----------------

def _lord_strong(ctx, lord: str) -> Tuple[bool, Dict]:
    """Canonical 'lord strong' (Lakshmi-consistent): dignity, house, Shadbala."""
    h = house_of(ctx, lord)
    dignity = ctx.get_dignity_category(lord)
    ratio = ctx.get_shadbala_ratio(lord)
    dign_ok = bool(ctx.is_exalted(lord) or ctx.is_own_sign(lord)
                   or ctx.is_moolatrikona(lord))
    house_ok = bool(h is not None and h in (1, 4, 7, 10, 5, 9))
    shadbala_ok = bool(ratio is not None and ratio >= 1.0)
    return (dign_ok or house_ok or shadbala_ok), {
        "house": h, "dignity": dignity, "shadbala_ratio": ratio,
        "dignity_strong": dign_ok, "house_strong": house_ok,
        "shadbala_strong": shadbala_ok,
    }


def _lord_strength_evidence(ctx, house_num: int, method: str) -> Tuple[Optional[str], bool, List[Evidence]]:
    """Evidence pair for '<N>th lord strong'. Returns (lord, strong, evidence)."""
    lord = lord_of_house(ctx, house_num)
    if not lord:
        return None, False, [Evidence(
            evidence_type=EvidenceType.HOUSE_LORD_POSITION,
            subject=f"Lord of house {house_num}",
            value=None, expected="strong lord", actual="missing lord",
            source="ChartFacts",
            significance=f"Lord of {house_num} missing; yoga not formed",
            details={"method": method})]
    strong, info = _lord_strong(ctx, lord)
    ev = [Evidence(
        evidence_type=EvidenceType.HOUSE_LORD_POSITION,
        subject=f"{lord} (lord of {house_num})",
        value=info["house"], expected="strong placement",
        actual=f"house {info['house']}, {info['dignity']}, shadbala {info['shadbala_ratio']}",
        source="ChartFacts",
        significance=f"Lord of {house_num} ({lord}) strong" if strong
        else f"Lord of {house_num} ({lord}) not strong",
        details={"method": method, "lord": lord, **info}),
        Evidence(
        evidence_type=EvidenceType.PLANET_DIGNITY,
        subject=f"{lord} dignity",
        value=info["dignity"], expected="exalted/own/moolatrikona or supported",
        actual=str(info["dignity"]), source="StrengthReport",
        significance=f"{lord} dignity {info['dignity']}",
        details={"method": method, "lord": lord})]
    return lord, strong, ev


def _benefics_in_house(ctx, house: int) -> List[str]:
    return [p for p in ctx.get_planets_in_house(house) if p in NATURAL_BENEFICS]


def _malefics_in_house(ctx, house: int) -> List[str]:
    return [p for p in ctx.get_planets_in_house(house) if p in NATURAL_MALEFICS]


def _occupancy_evidence(ctx, house: int, occupants: List[str], kind: str,
                        method: str, label: str) -> Evidence:
    return Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject=label,
        value=house, expected=kind, actual=f"house {house}: {occupants or 'none'}",
        source="ChartFacts",
        significance=f"{label}: {', '.join(occupants) if occupants else 'none'}",
        details={"method": method, "house": house, "occupants": occupants})


def _same_house(ctx, a: str, b: str) -> Tuple[bool, Optional[int]]:
    ha, hb = house_of(ctx, a), house_of(ctx, b)
    if ha is None or hb is None:
        return False, None
    return ha == hb, ha


# ---------------- builders (31) ----------------

def build_akhanda_samrajya() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.AKHANDA_SAMRAJYA", "Akhanda Samrajya Yoga",
        "Jupiter rules the 2nd, 5th or 11th and a wealth-lord (2nd/9th/11th lord "
        "or Jupiter itself) is in a Kendra from the Moon.",
        "jupiter_rules_wealth_plus_kendra_from_moon",
        "Traditional attribution (UNVERIFIED exact verse). Implemented as the union "
        "of the two documented readings (Jupiter-as-kendra-planet vs lord-of-2/9/11 "
        "in kendra from Moon); both recorded in evidence.",
        ConfidenceLevel.MEDIUM, "parashari_akhanda_samrajya_formation",
        ["akhanda_samrajya", "raja_yoga"],
        [EvidenceType.LORDSHIP_RELATIONSHIP, EvidenceType.KENDRA_TRIKONA])


def build_bhagya() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.BHAGYA", "Bhagya Yoga",
        "9th lord strong and a natural benefic occupies the 9th house.",
        "ninth_lord_strong_plus_benefic",
        "Traditional attribution (UNVERIFIED exact verse). Conjunctive reading per "
        "Migration #3B derivation; legacy checked the lord alone (documented delta).",
        ConfidenceLevel.MEDIUM, "parashari_bhagya_formation",
        ["bhagya", "fortune"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_IN_HOUSE])


def build_chamara() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.CHAMARA", "Chamara Yoga",
        "Lagna lord exalted in a Kendra and aspecting the Lagna (Parashari aspect).",
        "lagna_lord_exalted_kendra_aspecting_lagna",
        "Traditional attribution (UNVERIFIED exact verse). Aspect clause per Migration "
        "#3B derivation; legacy checked exaltation+kendra only (documented delta).",
        ConfidenceLevel.MEDIUM, "parashari_chamara_formation",
        ["chamara"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_DIGNITY, EvidenceType.ASPECT])


def build_chhatra() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.CHHATRA", "Chhatra Yoga",
        "5th lord strong (canonical lord-strength).",
        "fifth_lord_strong",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_chhatra_formation",
        ["chhatra"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_DIGNITY])


def build_dhenu() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.DHENU", "Dhenu Yoga",
        "2nd lord exalted.",
        "second_lord_exalted",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_dhenu_formation",
        ["dhenu", "wealth"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_DIGNITY])


def build_gandharva() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.GANDHARVA", "Gandharva Yoga",
        "10th lord in a Kama trikona (3, 7, 11), Sun dignified (exalted/own/ "
        "moolatrikona), Moon in the 9th house.",
        "tenth_lord_kama_trkona_sun_moon",
        "Traditional attribution (UNVERIFIED exact verse). Sun 'strong' read as "
        "dignity-strong (legacy used own/exalted only; documented delta).",
        ConfidenceLevel.MEDIUM, "parashari_gandharva_formation",
        ["gandharva", "arts"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_DIGNITY,
         EvidenceType.PLANET_IN_HOUSE])


def build_go() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.GO", "Go Yoga",
        "Jupiter in moolatrikona in the same whole-sign house as the Lagna lord.",
        "jupiter_moolatrikona_with_lagna_lord",
        "Traditional attribution (UNVERIFIED exact verse). Same-house = conjunction "
        "per canonical Budha-Aditya precedent.",
        ConfidenceLevel.HIGH, "parashari_go_formation",
        ["go_yoga"],
        [EvidenceType.PLANET_DIGNITY, EvidenceType.CONJUNCTION])


def build_hara() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.HARA", "Hara Yoga",
        "A natural benefic in each of the 4th, 8th and 9th houses from the 7th lord.",
        "benefics_489_from_seventh_lord",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_hara_formation",
        ["hara"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_hari() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.HARI", "Hari Yoga",
        "A natural benefic in each of the 2nd, 8th and 12th houses from the 2nd lord.",
        "benefics_2812_from_second_lord",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_hari_formation",
        ["hari"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_jaladhi() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.JALADHI", "Jaladhi Yoga",
        "4th lord strong and a natural benefic occupies the 4th house.",
        "fourth_lord_strong_plus_benefic",
        "Traditional attribution (UNVERIFIED exact verse). Conjunctive reading per "
        "Migration #3B derivation; legacy checked the lord alone (documented delta).",
        ConfidenceLevel.MEDIUM, "parashari_jaladhi_formation",
        ["jaladhi"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_IN_HOUSE])


def build_kahala() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.KAHALA", "Kahala Yoga",
        "4th and 9th lords in mutual Kendras, or both in Kendras from the Lagna "
        "(same-lord case: the single lord in a Kendra).",
        "fourth_ninth_lords_kendra",
        "Traditional attribution (UNVERIFIED exact verse). Disjunctive reading of "
        "'kendra from each other/lagna' per Migration #3B derivation.",
        ConfidenceLevel.MEDIUM, "parashari_kahala_formation",
        ["kahala"],
        [EvidenceType.LORDSHIP_RELATIONSHIP, EvidenceType.KENDRA_TRIKONA])


def build_kalanidhi() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.KALANIDHI", "Kalanidhi Yoga",
        "Jupiter in the 2nd or 5th house in the same whole-sign house as Mercury or Venus.",
        "jupiter_2_5_with_mercury_venus",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_kalanidhi_formation",
        ["kalanidhi", "arts"],
        [EvidenceType.PLANET_IN_HOUSE, EvidenceType.CONJUNCTION])


def build_kama() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.KAMA", "Kama Yoga",
        "7th lord strong (canonical lord-strength).",
        "seventh_lord_strong",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_kama_formation",
        ["kama"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_DIGNITY])


def build_khyathi() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.KHYATHI", "Khyathi Yoga",
        "10th lord strong (canonical lord-strength).",
        "tenth_lord_strong",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_khyathi_formation",
        ["khyathi", "fame"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_DIGNITY])


def build_kusuma() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.KUSUMA", "Kusuma Yoga",
        "Venus in a Kendra, Moon in a Trikona, Saturn in the 10th house.",
        "venus_kendra_moon_trikona_saturn_10",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_kusuma_formation",
        ["kusuma"],
        [EvidenceType.KENDRA_TRIKONA, EvidenceType.PLANET_IN_HOUSE])


def build_mala() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.MALA", "Mala Yoga",
        "Natural benefics occupying at least 3 Kendra houses (Nabhasa garland).",
        "benefics_in_three_kendras",
        "Traditional attribution (UNVERIFIED exact verse). Threshold 3 per classical "
        "spec and Migration #3B derivation; legacy used >=2 (documented delta). "
        "Simple kendra-occupancy count only; no Category D Nabha counting primitive.",
        ConfidenceLevel.MEDIUM, "parashari_mala_formation",
        ["mala", "nabhasa"],
        [EvidenceType.KENDRA_TRIKONA, EvidenceType.PLANET_IN_HOUSE])


def build_musala() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.MUSALA", "Musala Yoga",
        "Lagna lord in the 12th house and a natural malefic in the 12th house.",
        "lagna_lord_12th_plus_malefic",
        "Traditional attribution (UNVERIFIED exact verse). Conjunctive reading per "
        "Migration #3B derivation; legacy checked the lord alone (documented delta).",
        ConfidenceLevel.MEDIUM, "parashari_musala_formation",
        ["musala"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_IN_HOUSE])


def build_parijata() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.PARIJATA", "Parijata Yoga",
        "Dispositor of the Lagna lord exalted.",
        "lagna_lord_dispositor_exalted",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_parijata_formation",
        ["parijata"],
        [EvidenceType.LORDSHIP_RELATIONSHIP, EvidenceType.PLANET_DIGNITY])


def build_parvata() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.PARVATA", "Parvata Yoga",
        "A natural benefic in a Kendra and no planet in the 6th or 8th house.",
        "benefic_kendra_empty_6_8",
        "Traditional attribution (UNVERIFIED exact verse). Empty-house check over all "
        "chart planets including nodes, per legacy semantics.",
        ConfidenceLevel.HIGH, "parashari_parvata_formation",
        ["parvata"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_pushkala() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.PUSHKALA", "Pushkala Yoga",
        "Lord of the Moon's sign with the Lagna lord in the same whole-sign house, "
        "in a Kendra.",
        "moon_lord_with_lagna_lord_kendra",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_pushkala_formation",
        ["pushkala"],
        [EvidenceType.LORDSHIP_RELATIONSHIP, EvidenceType.KENDRA_TRIKONA])


def build_raja_lakshana() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.RAJA_LAKSHANA", "Raja Lakshana Yoga",
        "Jupiter, Venus, Mercury and Moon each in a Kendra house.",
        "four_benefics_in_kendras",
        "Traditional attribution (UNVERIFIED exact verse). Strict all-four reading per "
        "Migration #3B derivation; legacy used >=2 kendras with any benefic "
        "(documented delta).",
        ConfidenceLevel.MEDIUM, "parashari_raja_lakshana_formation",
        ["raja_lakshana"],
        [EvidenceType.KENDRA_TRIKONA])


def build_ravi() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.RAVI", "Ravi Yoga",
        "Sun in the 10th house and the 10th lord in the 3rd house.",
        "sun_10th_tenth_lord_3rd",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_ravi_formation",
        ["ravi"],
        [EvidenceType.PLANET_IN_HOUSE, EvidenceType.HOUSE_LORD_POSITION])


def build_shakata() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.SHAKATA", "Shakata Yoga",
        "Moon in the 6th, 8th or 12th house from Jupiter (whole-sign).",
        "moon_6_8_12_from_jupiter",
        "Traditional attribution (UNVERIFIED exact verse). Canonical is_6_8_12_from "
        "primitive; no Western aspect.",
        ConfidenceLevel.HIGH, "parashari_shakata_formation",
        ["shakata"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_shaurya() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.SHAURYA", "Shaurya Yoga",
        "3rd lord strong (canonical lord-strength).",
        "third_lord_strong",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_shaurya_formation",
        ["shaurya", "courage"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_DIGNITY])


def build_shiva() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.SHIVA", "Shiva Yoga",
        "5th lord in the 9th, 9th lord in the 10th, 10th lord in the 5th.",
        "lord_5_9_9_10_10_5",
        "Traditional attribution (UNVERIFIED exact verse). All three placements required.",
        ConfidenceLevel.HIGH, "parashari_shiva_formation",
        ["shiva"],
        [EvidenceType.HOUSE_LORD_POSITION])


def build_srinatha() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.SRINATHA", "Srinatha Yoga",
        "7th lord exalted in the 10th house and the 10th lord in the same "
        "whole-sign house as the 9th lord.",
        "seventh_lord_exalted_10th_plus_10_9",
        "Traditional attribution (UNVERIFIED exact verse). Conjunctive reading of both "
        "clauses per Migration #3B derivation; legacy encoded the first clause only "
        "(documented delta). 'With' = same whole-sign house per canonical precedent.",
        ConfidenceLevel.MEDIUM, "parashari_srinatha_formation",
        ["srinatha"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_DIGNITY,
         EvidenceType.LORDSHIP_RELATIONSHIP])


def build_suparijata() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.SUPARIJATA", "Suparijata Yoga",
        "11th lord strong (canonical lord-strength).",
        "eleventh_lord_strong",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_suparijata_formation",
        ["suparijata", "gains"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_DIGNITY])


def build_ubhayachari() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.UBHAYACHARI", "Ubhayachari Yoga",
        "Planets (excl. Moon/Rahu/Ketu) in both the 2nd and the 12th from the Sun.",
        "planets_2nd_and_12th_from_sun",
        "Traditional attribution (UNVERIFIED exact verse). Canonical "
        "planets_in_house_from_sun primitive (exclusions built in).",
        ConfidenceLevel.HIGH, "parashari_ubhayachari_formation",
        ["ubhayachari", "sun_yoga"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_vasi() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.VASI", "Vasi Yoga",
        "A planet (excl. Moon/Rahu/Ketu) in the 12th from the Sun.",
        "planet_12th_from_sun",
        "Traditional attribution (UNVERIFIED exact verse). Canonical "
        "planets_in_house_from_sun primitive (exclusions built in).",
        ConfidenceLevel.HIGH, "parashari_vasi_formation",
        ["vasi", "sun_yoga"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_vesi() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.VESI", "Vesi Yoga",
        "A planet (excl. Moon/Rahu/Ketu) in the 2nd from the Sun.",
        "planet_2nd_from_sun",
        "Traditional attribution (UNVERIFIED exact verse). Canonical "
        "planets_in_house_from_sun primitive (exclusions built in).",
        ConfidenceLevel.HIGH, "parashari_vesi_formation",
        ["vesi", "sun_yoga"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_vishnu() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.VISHNU", "Vishnu Yoga",
        "9th and 10th lords both in the 2nd house.",
        "ninth_tenth_lords_in_second",
        "Traditional attribution (UNVERIFIED exact verse).",
        ConfidenceLevel.HIGH, "parashari_vishnu_formation",
        ["vishnu"],
        [EvidenceType.HOUSE_LORD_POSITION])


# ---------------- formation evaluators ----------------

def akhanda_samrajya_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    houses_jup = set(ctx.get_houses_ruled_by("Jupiter"))
    rules_wealth = bool(houses_jup & {2, 5, 11})
    candidates: Dict[str, str] = {"Jupiter": "Jupiter"}
    for h in (2, 9, 11):
        lord = lord_of_house(ctx, h)
        if lord:
            candidates[lord] = f"lord of {h}"
    kendra_hits = sorted(p for p in candidates if is_kendra_from_moon(ctx, p))
    ok = bool(rules_wealth and kendra_hits)
    ev = [Evidence(
        evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
        subject="Jupiter rulership of 2/5/11",
        value=sorted(houses_jup), expected="rules 2, 5 or 11",
        actual=str(sorted(houses_jup)),
        source="ChartFacts",
        significance="Jupiter rules a wealth house" if rules_wealth
        else "Jupiter rules none of 2/5/11",
        details={"method": "jupiter_rules_wealth_plus_kendra_from_moon"})]
    for p, role in sorted(candidates.items()):
        hit = p in kendra_hits
        ev.append(Evidence(
            evidence_type=EvidenceType.KENDRA_TRIKONA,
            subject=f"{p} Kendra from Moon ({role})",
            value=house_of(ctx, p), expected="Kendra (1,4,7,10) from Moon",
            actual=f"house {house_of(ctx, p)}, Moon house {moon_house(ctx)}",
            source="ChartFacts",
            significance=f"{p} in Kendra from Moon" if hit else f"{p} not in Kendra from Moon",
            details={"method": "jupiter_rules_wealth_plus_kendra_from_moon"}))
    ev.append(Evidence(
        evidence_type=EvidenceType.KENDRA_TRIKONA, subject="Akhanda Samrajya scan",
        value=kendra_hits, expected="Jupiter rules 2/5/11 + a candidate in Kendra from Moon",
        actual=str(kendra_hits or "none"), source="ChartFacts",
        significance="Akhanda Samrajya formed" if ok else "Akhanda Samrajya not formed"))
    return ok, ev


def _lord_strong_plus_occupancy(ctx, house_num: int, method: str,
                                need: str) -> Tuple[bool, List[Evidence]]:
    """'<N>th lord strong + <benefic|malefic> in <N>th' pattern."""
    lord, strong, ev = _lord_strength_evidence(ctx, house_num, method)
    occ = _benefics_in_house(ctx, house_num) if need == "benefic" \
        else _malefics_in_house(ctx, house_num)
    ev.append(_occupancy_evidence(
        ctx, house_num, occ,
        f"a natural {need} in {house_num}th", method,
        f"{'Benefic' if need == 'benefic' else 'Malefic'} in {house_num}th house"))
    return bool(strong and occ), ev


def bhagya_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _lord_strong_plus_occupancy(ctx, 9, "ninth_lord_strong_plus_benefic", "benefic")


def chamara_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord = lord_of_house(ctx, 1)
    if not lord:
        return False, []
    h = house_of(ctx, lord)
    exalted = ctx.is_exalted(lord)
    kendra = h is not None and h in KENDRA_HOUSES
    aspects = ctx.is_planet_aspecting_house(lord, 1)
    ok = bool(exalted and kendra and aspects)
    ev = [Evidence(
        evidence_type=EvidenceType.HOUSE_LORD_POSITION,
        subject=f"{lord} (lord of 1)",
        value=h, expected="exalted in Kendra",
        actual=f"house {h}, {ctx.get_dignity_category(lord)}",
        source="ChartFacts",
        significance=f"Lagna lord {lord} exalted in Kendra {h}" if (exalted and kendra)
        else f"Lagna lord {lord} fails exalted-in-Kendra",
        details={"method": "lagna_lord_exalted_kendra_aspecting_lagna", "lord": lord}),
        Evidence(
        evidence_type=EvidenceType.ASPECT,
        subject=f"{lord} aspects Lagna",
        value="Aspecting" if aspects else "Not Aspecting",
        expected="Parashari aspect to house 1", actual="Yes" if aspects else "No",
        source="ChartFacts",
        significance=f"{lord} aspects Lagna" if aspects else f"{lord} does not aspect Lagna",
        details={"method": "lagna_lord_exalted_kendra_aspecting_lagna", "lord": lord})]
    return ok, ev


def chhatra_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord, strong, ev = _lord_strength_evidence(ctx, 5, "fifth_lord_strong")
    return strong, ev


def dhenu_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord = lord_of_house(ctx, 2)
    if not lord:
        return False, []
    ok = bool(ctx.is_exalted(lord))
    ev = [Evidence(
        evidence_type=EvidenceType.HOUSE_LORD_POSITION,
        subject=f"{lord} (lord of 2)",
        value=house_of(ctx, lord), expected="exalted",
        actual=f"house {house_of(ctx, lord)}, {ctx.get_dignity_category(lord)}",
        source="ChartFacts",
        significance=f"2nd lord {lord} exalted" if ok else f"2nd lord {lord} not exalted",
        details={"method": "second_lord_exalted", "lord": lord})]
    return ok, ev


def gandharva_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord10 = lord_of_house(ctx, 10)
    h10 = house_of(ctx, lord10) if lord10 else None
    kama_ok = h10 is not None and h10 in (3, 7, 11)
    sun_ok = bool(ctx.is_exalted("Sun") or ctx.is_own_sign("Sun")
                  or ctx.is_moolatrikona("Sun"))
    moon_ok = house_of(ctx, "Moon") == 9
    ok = bool(kama_ok and sun_ok and moon_ok)
    ev = [Evidence(
        evidence_type=EvidenceType.HOUSE_LORD_POSITION,
        subject=f"{lord10} (lord of 10)",
        value=h10, expected="Kama trikona (3,7,11)",
        actual=f"house {h10}", source="ChartFacts",
        significance=f"10th lord {lord10} in Kama trikona" if kama_ok
        else f"10th lord {lord10} not in Kama trikona",
        details={"method": "tenth_lord_kama_trkona_sun_moon", "lord": lord10}),
        Evidence(
        evidence_type=EvidenceType.PLANET_DIGNITY,
        subject="Sun dignity",
        value=ctx.get_dignity_category("Sun"), expected="exalted/own/moolatrikona",
        actual=str(ctx.get_dignity_category("Sun")), source="StrengthReport",
        significance="Sun dignified" if sun_ok else "Sun not dignified",
        details={"method": "tenth_lord_kama_trkona_sun_moon"}),
        Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject="Moon in 9th house",
        value=house_of(ctx, "Moon"), expected=9,
        actual=f"house {house_of(ctx, 'Moon')}", source="ChartFacts",
        significance="Moon in 9th" if moon_ok else "Moon not in 9th",
        details={"method": "tenth_lord_kama_trkona_sun_moon"})]
    return ok, ev


def go_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord1 = lord_of_house(ctx, 1)
    mt = bool(ctx.is_moolatrikona("Jupiter"))
    same, hj = _same_house(ctx, "Jupiter", lord1) if lord1 else (False, None)
    ok = bool(mt and same)
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_DIGNITY,
        subject="Jupiter dignity",
        value=ctx.get_dignity_category("Jupiter"), expected="moolatrikona",
        actual=str(ctx.get_dignity_category("Jupiter")), source="StrengthReport",
        significance="Jupiter in moolatrikona" if mt else "Jupiter not in moolatrikona",
        details={"method": "jupiter_moolatrikona_with_lagna_lord"}),
        Evidence(
        evidence_type=EvidenceType.CONJUNCTION,
        subject=f"Jupiter-{lord1} Go",
        value={"jupiter_house": house_of(ctx, "Jupiter"),
               "lagna_lord_house": house_of(ctx, lord1) if lord1 else None},
        expected="same whole-sign house", actual=f"houses {house_of(ctx, 'Jupiter')}/"
        f"{house_of(ctx, lord1) if lord1 else '?'}",
        source="ChartFacts",
        significance="Jupiter with Lagna lord" if same else "Jupiter not with Lagna lord",
        details={"method": "jupiter_moolatrikona_with_lagna_lord", "lord": lord1})]
    return ok, ev


def _benefics_from_lord(ctx, lord_house: int, offsets: Tuple[int, ...],
                         method: str, label: str) -> Tuple[bool, List[Evidence]]:
    lord = lord_of_house(ctx, lord_house)
    if not lord:
        return False, []
    h_lord = house_of(ctx, lord)
    if h_lord is None:
        return False, []
    ev: List[Evidence] = []
    ok_all = True
    for off in offsets:
        target = ((h_lord + off - 2) % 12) + 1
        found = [p for p in ctx.get_planets_in_house(target) if p in NATURAL_BENEFICS]
        hit = bool(found)
        ok_all = ok_all and hit
        ev.append(_occupancy_evidence(
            ctx, target, found, "a natural benefic", method,
            f"{off} from {lord} (lord of {lord_house})"))
    ev.append(Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject=f"{label} scan",
        value="all present" if ok_all else "missing",
        expected=f"benefics in {label}", actual="all present" if ok_all else "missing",
        source="ChartFacts",
        significance=f"{label} formed" if ok_all else f"{label} not formed",
        details={"method": method, "lord": lord}))
    return ok_all, ev


def hara_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _benefics_from_lord(ctx, 7, (4, 8, 9), "benefics_489_from_seventh_lord",
                               "4th/8th/9th from 7th lord")


def hari_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _benefics_from_lord(ctx, 2, (2, 8, 12), "benefics_2812_from_second_lord",
                               "2nd/8th/12th from 2nd lord")


def jaladhi_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _lord_strong_plus_occupancy(ctx, 4, "fourth_lord_strong_plus_benefic", "benefic")


def kahala_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    l4, l9 = lord_of_house(ctx, 4), lord_of_house(ctx, 9)
    if not l4 or not l9:
        return False, []
    h4, h9 = house_of(ctx, l4), house_of(ctx, l9)
    if l4 == l9:
        ok = h4 is not None and h4 in KENDRA_HOUSES
        detail, actual = "single lord in Kendra", f"house {h4}"
    else:
        mutual = is_kendra_from_planet(ctx, l4, l9)
        both_kendra = (h4 in KENDRA_HOUSES if h4 else False) and \
                      (h9 in KENDRA_HOUSES if h9 else False)
        ok = bool(mutual or both_kendra)
        detail = f"mutual_kendra={mutual}, both_kendra_from_lagna={both_kendra}"
        actual = f"{l4} house {h4}, {l9} house {h9}"
    ev = [Evidence(
        evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
        subject=f"Lords of 4 ({l4}) and 9 ({l9})",
        value=detail, expected="mutual Kendra or both in Kendra from Lagna",
        actual=actual, source="ChartFacts",
        significance="Kahala formed" if ok else "Kahala not formed",
        details={"method": "fourth_ninth_lords_kendra", "lord1": l4, "lord2": l9,
                 "house1": h4, "house2": h9})]
    return ok, ev


def kalanidhi_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    hj = house_of(ctx, "Jupiter")
    pos_ok = hj is not None and hj in (2, 5)
    partners = [p for p in ("Mercury", "Venus")
                if _same_house(ctx, "Jupiter", p)[0]]
    ok = bool(pos_ok and partners)
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject="Jupiter in 2nd/5th",
        value=hj, expected="house 2 or 5", actual=f"house {hj}",
        source="ChartFacts",
        significance="Jupiter in 2nd/5th" if pos_ok else "Jupiter not in 2nd/5th",
        details={"method": "jupiter_2_5_with_mercury_venus"}),
        Evidence(
        evidence_type=EvidenceType.CONJUNCTION,
        subject="Jupiter-Mercury/Venus Kalanidhi",
        value=partners, expected="same house as Mercury or Venus",
        actual=str(partners or "none"), source="ChartFacts",
        significance=f"Jupiter with {', '.join(partners)}" if partners
        else "Jupiter with neither Mercury nor Venus",
        details={"method": "jupiter_2_5_with_mercury_venus"})]
    return ok, ev


def kama_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord, strong, ev = _lord_strength_evidence(ctx, 7, "seventh_lord_strong")
    return strong, ev


def khyathi_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord, strong, ev = _lord_strength_evidence(ctx, 10, "tenth_lord_strong")
    return strong, ev


def kusuma_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    hv, hm, hs = house_of(ctx, "Venus"), house_of(ctx, "Moon"), house_of(ctx, "Saturn")
    v_ok = hv is not None and hv in KENDRA_HOUSES
    m_ok = hm is not None and hm in TRIKONA_HOUSES
    s_ok = hs == 10
    ok = bool(v_ok and m_ok and s_ok)
    ev = [Evidence(
        evidence_type=EvidenceType.KENDRA_TRIKONA, subject="Venus in Kendra",
        value=hv, expected="Kendra (1,4,7,10)", actual=f"house {hv}",
        source="ChartFacts",
        significance="Venus in Kendra" if v_ok else "Venus not in Kendra",
        details={"method": "venus_kendra_moon_trikona_saturn_10"}),
        Evidence(
        evidence_type=EvidenceType.KENDRA_TRIKONA, subject="Moon in Trikona",
        value=hm, expected="Trikona (1,5,9)", actual=f"house {hm}",
        source="ChartFacts",
        significance="Moon in Trikona" if m_ok else "Moon not in Trikona",
        details={"method": "venus_kendra_moon_trikona_saturn_10"}),
        Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="Saturn in 10th",
        value=hs, expected=10, actual=f"house {hs}",
        source="ChartFacts",
        significance="Saturn in 10th" if s_ok else "Saturn not in 10th",
        details={"method": "venus_kendra_moon_trikona_saturn_10"})]
    return ok, ev


def mala_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ev: List[Evidence] = []
    count = 0
    for k in KENDRA_HOUSES:
        found = _benefics_in_house(ctx, k)
        if found:
            count += 1
        ev.append(_occupancy_evidence(
            ctx, k, found, "a natural benefic",
            "benefics_in_three_kendras", f"Benefic in Kendra {k}"))
    ok = count >= 3
    ev.append(Evidence(
        evidence_type=EvidenceType.KENDRA_TRIKONA, subject="Mala kendra count",
        value=count, expected=">=3 Kendras with benefics", actual=count,
        source="ChartFacts",
        significance="Mala formed" if ok else "Mala not formed",
        details={"method": "benefics_in_three_kendras"}))
    return ok, ev


def musala_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord = lord_of_house(ctx, 1)
    h = house_of(ctx, lord) if lord else None
    in12 = h == 12
    occ = _malefics_in_house(ctx, 12)
    ok = bool(in12 and occ)
    ev = [Evidence(
        evidence_type=EvidenceType.HOUSE_LORD_POSITION,
        subject=f"{lord} (lord of 1)",
        value=h, expected=12, actual=f"house {h}",
        source="ChartFacts",
        significance=f"Lagna lord {lord} in 12th" if in12
        else f"Lagna lord {lord} not in 12th",
        details={"method": "lagna_lord_12th_plus_malefic", "lord": lord}),
        _occupancy_evidence(ctx, 12, occ, "a natural malefic",
                            "lagna_lord_12th_plus_malefic", "Malefic in 12th house")]
    return ok, ev


def parijata_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    l1 = lord_of_house(ctx, 1)
    if not l1:
        return False, []
    sign_l1 = sign_of(ctx, l1)
    disp = SIGN_LORDS.get(sign_l1) if sign_l1 else None
    if not disp:
        return False, []
    ok = bool(ctx.is_exalted(disp))
    ev = [Evidence(
        evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
        subject=f"Dispositor of Lagna lord ({l1} in {sign_l1} -> {disp})",
        value=sign_of(ctx, disp), expected="exalted",
        actual=f"{disp} in {sign_of(ctx, disp)}, {ctx.get_dignity_category(disp)}",
        source="ChartFacts",
        significance=f"Dispositor {disp} exalted" if ok else f"Dispositor {disp} not exalted",
        details={"method": "lagna_lord_dispositor_exalted", "lord": disp})]
    return ok, ev


def parvata_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    kendra_ben: List[str] = []
    for k in KENDRA_HOUSES:
        kendra_ben.extend(f"{p} in {k}" for p in _benefics_in_house(ctx, k))
    h6 = ctx.get_planets_in_house(6)
    h8 = ctx.get_planets_in_house(8)
    empty_ok = (not h6) and (not h8)
    ok = bool(kendra_ben and empty_ok)
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="Benefic in Kendra",
        value=kendra_ben or "none", expected="a natural benefic in a Kendra",
        actual=str(kendra_ben or "none"), source="ChartFacts",
        significance="Benefic in Kendra" if kendra_ben else "No benefic in Kendra",
        details={"method": "benefic_kendra_empty_6_8"}),
        Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="6th and 8th empty",
        value={"sixth": h6, "eighth": h8}, expected="both empty",
        actual=str({"sixth": h6, "eighth": h8}), source="ChartFacts",
        significance="6th and 8th empty" if empty_ok else "6th/8th occupied",
        details={"method": "benefic_kendra_empty_6_8"})]
    return ok, ev


def pushkala_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    moon_sign = sign_of(ctx, "Moon")
    l_moon = SIGN_LORDS.get(moon_sign) if moon_sign else None
    l1 = lord_of_house(ctx, 1)
    if not l_moon or not l1:
        return False, []
    same, h = _same_house(ctx, l_moon, l1)
    kendra = h is not None and h in KENDRA_HOUSES
    ok = bool(same and kendra)
    ev = [Evidence(
        evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
        subject=f"Moon lord {l_moon} with Lagna lord {l1}",
        value=h, expected="same Kendra house",
        actual=f"houses {house_of(ctx, l_moon)}/{house_of(ctx, l1)}",
        source="ChartFacts",
        significance="Pushkala formed" if ok else "Pushkala not formed",
        details={"method": "moon_lord_with_lagna_lord_kendra",
                 "lord1": l_moon, "lord2": l1})]
    return ok, ev


def raja_lakshana_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ev: List[Evidence] = []
    ok_all = True
    for p in ("Jupiter", "Venus", "Mercury", "Moon"):
        h = house_of(ctx, p)
        hit = h is not None and h in KENDRA_HOUSES
        ok_all = ok_all and hit
        ev.append(Evidence(
            evidence_type=EvidenceType.KENDRA_TRIKONA, subject=f"{p} in Kendra",
            value=h, expected="Kendra (1,4,7,10)", actual=f"house {h}",
            source="ChartFacts",
            significance=f"{p} in Kendra" if hit else f"{p} not in Kendra",
            details={"method": "four_benefics_in_kendras"}))
    return ok_all, ev


def ravi_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    sun_ok = house_of(ctx, "Sun") == 10
    l10 = lord_of_house(ctx, 10)
    h10 = house_of(ctx, l10) if l10 else None
    lord_ok = h10 == 3
    ok = bool(sun_ok and lord_ok)
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="Sun in 10th",
        value=house_of(ctx, "Sun"), expected=10,
        actual=f"house {house_of(ctx, 'Sun')}", source="ChartFacts",
        significance="Sun in 10th" if sun_ok else "Sun not in 10th",
        details={"method": "sun_10th_tenth_lord_3rd"}),
        Evidence(
        evidence_type=EvidenceType.HOUSE_LORD_POSITION,
        subject=f"{l10} (lord of 10)",
        value=h10, expected=3, actual=f"house {h10}",
        source="ChartFacts",
        significance=f"10th lord {l10} in 3rd" if lord_ok
        else f"10th lord {l10} not in 3rd",
        details={"method": "sun_10th_tenth_lord_3rd", "lord": l10})]
    return ok, ev


def shakata_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ok = bool(is_6_8_12_from(ctx, "Moon", "Jupiter"))
    hm, hj = house_of(ctx, "Moon"), house_of(ctx, "Jupiter")
    off = ((hm - hj) % 12) + 1 if (hm is not None and hj is not None) else None
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="Moon from Jupiter",
        value=off, expected="6th/8th/12th from Jupiter",
        actual=f"Moon house {hm}, Jupiter house {hj} ({off} from Jupiter)",
        source="ChartFacts",
        significance="Shakata formed" if ok else "Shakata not formed",
        details={"method": "moon_6_8_12_from_jupiter"})]
    return ok, ev


def shaurya_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord, strong, ev = _lord_strength_evidence(ctx, 3, "third_lord_strong")
    return strong, ev


def shiva_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    req = ((5, 9), (9, 10), (10, 5))
    ev: List[Evidence] = []
    ok_all = True
    for lord_house, target in req:
        lord = lord_of_house(ctx, lord_house)
        h = house_of(ctx, lord) if lord else None
        hit = h == target
        ok_all = ok_all and hit
        ev.append(Evidence(
            evidence_type=EvidenceType.HOUSE_LORD_POSITION,
            subject=f"{lord} (lord of {lord_house})",
            value=h, expected=target, actual=f"house {h}",
            source="ChartFacts",
            significance=f"Lord of {lord_house} in {target}" if hit
            else f"Lord of {lord_house} not in {target}",
            details={"method": "lord_5_9_9_10_10_5", "lord": lord}))
    return ok_all, ev


def srinatha_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    l7 = lord_of_house(ctx, 7)
    h7 = house_of(ctx, l7) if l7 else None
    first = bool(l7 and ctx.is_exalted(l7) and h7 == 10)
    l9, l10 = lord_of_house(ctx, 9), lord_of_house(ctx, 10)
    same = bool(l9 and l10 and _same_house(ctx, l10, l9)[0])
    ok = bool(first and same)
    ev = [Evidence(
        evidence_type=EvidenceType.HOUSE_LORD_POSITION,
        subject=f"{l7} (lord of 7)",
        value=h7, expected="exalted in 10th",
        actual=f"house {h7}, {ctx.get_dignity_category(l7) if l7 else '?'}",
        source="ChartFacts",
        significance=f"7th lord {l7} exalted in 10th" if first
        else f"7th lord {l7} fails exalted-in-10th",
        details={"method": "seventh_lord_exalted_10th_plus_10_9", "lord": l7}),
        Evidence(
        evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
        subject=f"10th lord {l10} with 9th lord {l9}",
        value="same house" if same else "apart",
        expected="same whole-sign house",
        actual=f"houses {house_of(ctx, l10) if l10 else '?'}/"
        f"{house_of(ctx, l9) if l9 else '?'}",
        source="ChartFacts",
        significance="10th lord with 9th lord" if same else "10th lord not with 9th lord",
        details={"method": "seventh_lord_exalted_10th_plus_10_9",
                 "lord1": l10, "lord2": l9})]
    return ok, ev


def suparijata_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord, strong, ev = _lord_strength_evidence(ctx, 11, "eleventh_lord_strong")
    return strong, ev


def _sun_side_formation(ctx, offsets: Tuple[int, ...], method: str,
                         label: str) -> Tuple[bool, List[Evidence]]:
    hs = sun_house(ctx)
    if hs is None:
        return False, []
    ev: List[Evidence] = []
    ok_all = True
    for off in offsets:
        found = planets_in_house_from_sun(ctx, off)
        hit = bool(found)
        ok_all = ok_all and hit
        target = ((hs + off - 2) % 12) + 1
        ev.append(_occupancy_evidence(
            ctx, target, found, "a planet (excl Moon/Rahu/Ketu)", method,
            f"{off} from Sun ({label})"))
    ev.append(Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject=f"{label} scan",
        value="present" if ok_all else "absent",
        expected=f"planets {label} from Sun", actual="present" if ok_all else "absent",
        source="ChartFacts",
        significance=f"{label} formed" if ok_all else f"{label} not formed",
        details={"method": method}))
    return ok_all, ev


def ubhayachari_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _sun_side_formation(ctx, (2, 12), "planets_2nd_and_12th_from_sun",
                               "2nd and 12th")


def vasi_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _sun_side_formation(ctx, (12,), "planet_12th_from_sun", "12th")


def vesi_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    return _sun_side_formation(ctx, (2,), "planet_2nd_from_sun", "2nd")


def vishnu_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ev: List[Evidence] = []
    ok_all = True
    for h in (9, 10):
        lord = lord_of_house(ctx, h)
        lh = house_of(ctx, lord) if lord else None
        hit = lh == 2
        ok_all = ok_all and hit
        ev.append(Evidence(
            evidence_type=EvidenceType.HOUSE_LORD_POSITION,
            subject=f"{lord} (lord of {h})",
            value=lh, expected=2, actual=f"house {lh}",
            source="ChartFacts",
            significance=f"Lord of {h} in 2nd" if hit else f"Lord of {h} not in 2nd",
            details={"method": "ninth_tenth_lords_in_second", "lord": lord}))
    return ok_all, ev


FORMATION_EVALUATORS = {
    "parashari_akhanda_samrajya_formation": akhanda_samrajya_formation,
    "parashari_bhagya_formation": bhagya_formation,
    "parashari_chamara_formation": chamara_formation,
    "parashari_chhatra_formation": chhatra_formation,
    "parashari_dhenu_formation": dhenu_formation,
    "parashari_gandharva_formation": gandharva_formation,
    "parashari_go_formation": go_formation,
    "parashari_hara_formation": hara_formation,
    "parashari_hari_formation": hari_formation,
    "parashari_jaladhi_formation": jaladhi_formation,
    "parashari_kahala_formation": kahala_formation,
    "parashari_kalanidhi_formation": kalanidhi_formation,
    "parashari_kama_formation": kama_formation,
    "parashari_khyathi_formation": khyathi_formation,
    "parashari_kusuma_formation": kusuma_formation,
    "parashari_mala_formation": mala_formation,
    "parashari_musala_formation": musala_formation,
    "parashari_parijata_formation": parijata_formation,
    "parashari_parvata_formation": parvata_formation,
    "parashari_pushkala_formation": pushkala_formation,
    "parashari_raja_lakshana_formation": raja_lakshana_formation,
    "parashari_ravi_formation": ravi_formation,
    "parashari_shakata_formation": shakata_formation,
    "parashari_shaurya_formation": shaurya_formation,
    "parashari_shiva_formation": shiva_formation,
    "parashari_srinatha_formation": srinatha_formation,
    "parashari_suparijata_formation": suparijata_formation,
    "parashari_ubhayachari_formation": ubhayachari_formation,
    "parashari_vasi_formation": vasi_formation,
    "parashari_vesi_formation": vesi_formation,
    "parashari_vishnu_formation": vishnu_formation,
}


def build_classical_catalog() -> List[RuleDefinition]:
    return [
        build_akhanda_samrajya(), build_bhagya(), build_chamara(),
        build_chhatra(), build_dhenu(), build_gandharva(),
        build_go(), build_hara(), build_hari(),
        build_jaladhi(), build_kahala(), build_kalanidhi(),
        build_kama(), build_khyathi(), build_kusuma(),
        build_mala(), build_musala(), build_parijata(),
        build_parvata(), build_pushkala(), build_raja_lakshana(),
        build_ravi(), build_shakata(), build_shaurya(),
        build_shiva(), build_srinatha(), build_suparijata(),
        build_ubhayachari(), build_vasi(), build_vesi(),
        build_vishnu(),
    ]


CLASSICAL_YOGA_RULE_IDS: List[str] = [
    r.metadata.rule_id for r in build_classical_catalog()
]


def register_classical_yoga_provenance() -> int:
    """Register Category C provenance records in the existing ProvenanceRegistry.

    Called once at import so every new canonical rule has a registry record
    (canonical_yoga adapter resolves ProvenanceRegistry.get(rule_id)).
    Idempotent: re-registration overwrites the same record.
    """
    from ..provenance import ProvenanceRegistry, create_provenance_from_rule
    n = 0
    for rule in build_classical_catalog():
        ProvenanceRegistry.register(create_provenance_from_rule(rule))
        n += 1
    return n


register_classical_yoga_provenance()
