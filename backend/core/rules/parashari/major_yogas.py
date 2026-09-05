"""
Phase 5B — major named yogas: Gaja Kesari, Budha-Aditya, Chandra-Mangala,
Adhi, Lakshmi, Saraswati, Amala, Vasumati, Sunapha, Anapha, Durudhara,
Kemadruma. Each formation documented; strength/cancellation central.
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
    house_of, sign_of, lord_of_house, moon_house, house_from_moon,
    is_kendra_from_moon, planets_in_house_from_moon, NATURAL_BENEFICS,
    UPACHAYA_HOUSES,
)


def _prov(source: str, method: str, notes: str,
          tradition=RuleTradition.PARASHARI_CLASSICAL) -> Provenance:
    return Provenance(
        source_type=SourceType.CLASSICAL_TEXT, source_name=source,
        source_reference="UNVERIFIED", tradition=tradition, method=method,
        implementation_version="1.0.0", notes=notes,
    )


def _base(rule_id, name, desc, prov, conf, ftype, tags, req) -> RuleDefinition:
    return RuleDefinition(
        metadata=RuleMetadata(
            rule_id=rule_id, rule_version="1.0.0", name=name,
            category=RuleCategory.YOGA, tradition=prov.tradition,
            school_method="Parashari Classical", status=RuleStatus.ENABLED,
            description=desc, provenance=prov, confidence=conf,
            tags=tags, enabled=True),
        formation_conditions=[Condition(type=ftype, params={})],
        strength_conditions=[], activation_rules=[],
        cancellation_rules=[CancellationRule(
            rule_id=f"{rule_id}.CANCEL", description="Generic cancellation scan",
            evaluator="parashari_cancellation_generic", is_partial=True)],
        mitigation_rules=[MitigationRule(
            rule_id=f"{rule_id}.MITIG", description="Generic mitigation scan",
            evaluator="parashari_mitigation_generic", strength_impact="partial")],
        required_evidence=req,
    )


# ---------------- builders ----------------

def build_gaja_kesari() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.GAJA_KESARI", "Gaja Kesari Yoga",
        "Jupiter in a Kendra (1,4,7,10 houses) from Moon by whole-sign houses.",
        _prov("Brihat Parashara Hora Shastra", "kendra_from_moon_house",
              "Traditional attribution (UNVERIFIED exact verse). House-based Kendra; "
              "waxing-Moon and dignity-gated variants documented, not merged."),
        ConfidenceLevel.HIGH, "parashari_gaja_kesari_formation",
        ["gaja_kesari", "jupiter", "moon"],
        [EvidenceType.KENDRA_TRIKONA, EvidenceType.PLANET_DIGNITY])


def build_budha_aditya() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.BUDHA_ADITYA", "Budha-Aditya Yoga",
        "Sun and Mercury in the same whole-sign house.",
        _prov("Brihat Parashara Hora Shastra", "same_house_conjunction",
              "Traditional attribution (UNVERIFIED exact verse). Conjunction alone forms; "
              "combustion/affliction affect strength via exceptions."),
        ConfidenceLevel.HIGH, "parashari_budha_aditya_formation",
        ["budha_aditya", "sun", "mercury"],
        [EvidenceType.CONJUNCTION])


def build_chandra_mangala() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.CHANDRA_MANGALA", "Chandra-Mangala Yoga",
        "Moon and Mars in the same whole-sign house.",
        _prov("Brihat Parashara Hora Shastra", "same_house_conjunction",
              "Traditional attribution (UNVERIFIED exact verse). Mutual-aspect variant "
              "documented as omitted."),
        ConfidenceLevel.HIGH, "parashari_chandra_mangala_formation",
        ["chandra_mangala", "moon", "mars"],
        [EvidenceType.CONJUNCTION])


def build_adhi() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.ADHI", "Adhi Yoga",
        "Any of Jupiter/Venus/Mercury in the 6th, 7th or 8th house from Moon.",
        _prov("Brihat Parashara Hora Shastra", "benefic_678_from_moon_any",
              "Traditional attribution (UNVERIFIED exact verse). Lenient 'any' reading; "
              "strict all-three-houses and malefic-exclusion variants documented.",
              tradition=RuleTradition.TRADITION_DEPENDENT),
        ConfidenceLevel.TRADITION_DEPENDENT, "parashari_adhi_formation",
        ["adhi", "moon"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_lakshmi() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.LAKSHMI", "Lakshmi Yoga",
        "9th lord in Kendra/Trikona in own/exalted dignity AND Lagna lord strong.",
        _prov("Brihat Parashara Hora Shastra", "ninth_lord_strong_plus_lagna",
              "Traditional attribution (UNVERIFIED exact verse). One high-consensus form; "
              "Venus-based competing definitions documented, not implemented.",
              tradition=RuleTradition.TRADITION_DEPENDENT),
        ConfidenceLevel.TRADITION_DEPENDENT, "parashari_lakshmi_formation",
        ["lakshmi", "wealth"],
        [EvidenceType.HOUSE_LORD_POSITION, EvidenceType.PLANET_DIGNITY])


def build_saraswati() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.SARASWATI", "Saraswati Yoga",
        "Jupiter, Venus and Mercury all in Kendra/Trikona houses from Lagna.",
        _prov("Jataka Parijata", "benefic_trio_kendra_trikona",
              "Traditional attribution (UNVERIFIED exact verse). Dignity-gated variants "
              "documented, not imposed on formation."),
        ConfidenceLevel.MEDIUM, "parashari_saraswati_formation",
        ["saraswati", "learning"],
        [EvidenceType.KENDRA_TRIKONA])


def build_amala() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.AMALA", "Amala Yoga",
        "A natural benefic in the 10th house from Lagna.",
        _prov("Brihat Parashara Hora Shastra", "benefic_tenth_from_lagna",
              "Traditional attribution (UNVERIFIED exact verse). 10th-from-Moon variant "
              "documented as omitted."),
        ConfidenceLevel.MEDIUM, "parashari_amala_formation",
        ["amala"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_vasumati() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.VASUMATI", "Vasumati Yoga",
        "At least three of Jupiter/Venus/Mercury/Moon in Upachaya houses (3,6,10,11).",
        _prov("Brihat Parashara Hora Shastra", "benefics_in_upachaya_count",
              "Traditional attribution (UNVERIFIED exact verse). Strict all-benefics "
              "reading documented.",
              tradition=RuleTradition.TRADITION_DEPENDENT),
        ConfidenceLevel.TRADITION_DEPENDENT, "parashari_vasumati_formation",
        ["vasumati", "wealth"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_sunapha() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.SUNAPHA", "Sunapha Yoga",
        "A planet (excl. Sun/Rahu/Ketu) in the 2nd house from Moon.",
        _prov("Brihat Parashara Hora Shastra", "planet_2nd_from_moon",
              "Traditional attribution (UNVERIFIED exact verse)."),
        ConfidenceLevel.HIGH, "parashari_sunapha_formation",
        ["sunapha", "moon"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_anapha() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.ANAPHA", "Anapha Yoga",
        "A planet (excl. Sun/Rahu/Ketu) in the 12th house from Moon.",
        _prov("Brihat Parashara Hora Shastra", "planet_12th_from_moon",
              "Traditional attribution (UNVERIFIED exact verse)."),
        ConfidenceLevel.HIGH, "parashari_anapha_formation",
        ["anapha", "moon"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_durudhara() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.DURUDHARA", "Durudhara Yoga",
        "Planets (excl. Sun/Rahu/Ketu) in BOTH the 2nd and 12th houses from Moon.",
        _prov("Brihat Parashara Hora Shastra", "planets_2nd_and_12th_from_moon",
              "Traditional attribution (UNVERIFIED exact verse)."),
        ConfidenceLevel.HIGH, "parashari_durudhara_formation",
        ["durudhara", "moon"],
        [EvidenceType.PLANET_IN_HOUSE])


def build_kemadruma() -> RuleDefinition:
    return _base(
        "PARASHARI.YOGA.KEMADRUMA", "Kemadruma Yoga",
        "No planet (excl. Sun/Rahu/Ketu) in the 2nd or 12th from Moon AND none "
        "in Kendra from Moon. Cancellations evaluated separately.",
        _prov("Brihat Parashara Hora Shastra", "classical_isolation",
              "Traditional attribution (UNVERIFIED exact verse). Categorised under YOGA "
              "per classical catalogues; cancellations in exceptions module."),
        ConfidenceLevel.HIGH, "parashari_kemadruma_formation",
        ["kemadruma", "moon"],
        [EvidenceType.PLANET_IN_HOUSE, EvidenceType.KENDRA_TRIKONA])


# ---------------- formation evaluators ----------------

def gaja_kesari_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    hm, hj = moon_house(ctx), house_of(ctx, "Jupiter")
    ok = is_kendra_from_moon(ctx, "Jupiter")
    ev = [Evidence(
        evidence_type=EvidenceType.KENDRA_TRIKONA,
        subject="Jupiter Kendra from Moon",
        value={"moon_house": hm, "jupiter_house": hj},
        expected="Jupiter in 1/4/7/10 from Moon",
        actual=f"Jupiter house {hj}, Moon house {hm}",
        source="ChartFacts",
        significance="Gaja Kesari formed" if ok else "Jupiter not in Kendra from Moon",
        details={"method": "kendra_from_moon_house"})]
    return ok, ev


def _same_house(ctx, a: str, b: str, label: str):
    ha, hb = house_of(ctx, a), house_of(ctx, b)
    ok = ha is not None and ha == hb
    orb = None
    try:
        la, lb = ctx.get_planet_longitude(a), ctx.get_planet_longitude(b)
        if la is not None and lb is not None:
            d = abs(la - lb)
            orb = min(d, 360.0 - d)
    except Exception:
        orb = None
    ev = [Evidence(
        evidence_type=EvidenceType.CONJUNCTION, subject=f"{a}-{b} {label}",
        value={"house_a": ha, "house_b": hb, "orb_deg": orb},
        expected="same whole-sign house", actual=f"houses {ha}/{hb}",
        source="ChartFacts",
        significance=f"{label} formed" if ok else f"{a} and {b} not conjunct",
        details={"method": "same_house_conjunction"})]
    return ok, ev


def budha_aditya_formation(ctx, params):
    return _same_house(ctx, "Sun", "Mercury", "Budha-Aditya")


def chandra_mangala_formation(ctx, params):
    return _same_house(ctx, "Moon", "Mars", "Chandra-Mangala")


def adhi_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    hm = moon_house(ctx)
    found = []
    ev: List[Evidence] = []
    for b in ("Jupiter", "Venus", "Mercury"):
        off = house_from_moon(ctx, b)
        hit = off in (6, 7, 8)
        if hit:
            found.append(b)
        ev.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE,
            subject=f"{b} from Moon",
            value={"house": house_of(ctx, b), "from_moon": off},
            expected="6th/7th/8th from Moon", actual=f"{off} from Moon",
            source="ChartFacts",
            significance=f"{b} in {off} from Moon" if hit else f"{b} not in 6/7/8 from Moon",
            details={"method": "benefic_678_from_moon_any"}))
    if not found:
        ev.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="Adhi scan",
            value="none", expected="a benefic in 6/7/8 from Moon",
            actual="none", source="ChartFacts",
            significance="Adhi not formed"))
        return False, ev
    return True, ev


def lakshmi_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    lord9 = lord_of_house(ctx, 9)
    lord1 = lord_of_house(ctx, 1)
    ev: List[Evidence] = []
    if not lord9 or not lord1:
        return False, ev
    h9 = house_of(ctx, lord9)
    pos_ok = h9 is not None and h9 in (1, 4, 7, 10, 5, 9)
    dign_ok = bool(ctx.is_exalted(lord9) or ctx.is_own_sign(lord9))
    lagna_strong = bool(ctx.is_exalted(lord1) or ctx.is_own_sign(lord1)
                        or ctx.is_moolatrikona(lord1)
                        or (house_of(ctx, lord1) in (1, 4, 7, 10, 5, 9))
                        or (ctx.get_shadbala_ratio(lord1) or 0) >= 1.0)
    ev.append(Evidence(
        evidence_type=EvidenceType.HOUSE_LORD_POSITION,
        subject=f"9th lord {lord9}",
        value={"house": h9, "dignity": ctx.get_dignity_category(lord9)},
        expected="Kendra/Trikona in own/exalted",
        actual=f"house {h9}, {ctx.get_dignity_category(lord9)}",
        source="ChartFacts",
        significance="9th lord qualifies" if (pos_ok and dign_ok) else "9th lord fails"))
    ev.append(Evidence(
        evidence_type=EvidenceType.PLANET_DIGNITY,
        subject=f"Lagna lord {lord1}",
        value={"house": house_of(ctx, lord1), "dignity": ctx.get_dignity_category(lord1)},
        expected="strong", actual="strong" if lagna_strong else "weak",
        source="StrengthReport",
        significance="Lagna lord strong" if lagna_strong else "Lagna lord weak"))
    return bool(pos_ok and dign_ok and lagna_strong), ev


def saraswati_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ev: List[Evidence] = []
    ok_all = True
    for b in ("Jupiter", "Venus", "Mercury"):
        h = house_of(ctx, b)
        ok = h is not None and h in (1, 4, 7, 10, 5, 9)
        ok_all = ok_all and ok
        ev.append(Evidence(
            evidence_type=EvidenceType.KENDRA_TRIKONA, subject=f"{b} Kendra/Trikona",
            value=h, expected="Kendra/Trikona", actual=f"house {h}",
            source="ChartFacts",
            significance=f"{b} qualifies" if ok else f"{b} fails"))
    return ok_all, ev


def amala_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    tenth = ctx.get_planets_in_house(10)
    benefics = [p for p in tenth if p in NATURAL_BENEFICS]
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE,
        subject="10th house from Lagna",
        value={"occupants": tenth, "benefics": benefics},
        expected="a natural benefic in 10th", actual=str(benefics or "none"),
        source="ChartFacts",
        significance="Amala formed" if benefics else "no benefic in 10th",
        details={"method": "benefic_tenth_from_lagna"})]
    return bool(benefics), ev


def vasumati_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    ev: List[Evidence] = []
    count = 0
    for b in ("Jupiter", "Venus", "Mercury", "Moon"):
        h = house_of(ctx, b)
        ok = h is not None and h in UPACHAYA_HOUSES
        count += 1 if ok else 0
        ev.append(Evidence(
            evidence_type=EvidenceType.PLANET_IN_HOUSE, subject=f"{b} Upachaya",
            value=h, expected="Upachaya (3,6,10,11)", actual=f"house {h}",
            source="ChartFacts", significance=f"{b} in Upachaya" if ok else f"{b} not in Upachaya"))
    formed = count >= 3
    ev.append(Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="Vasumati count",
        value=count, expected=">=3 benefics in Upachaya", actual=count,
        source="ChartFacts", significance="Vasumati formed" if formed else "Vasumati not formed"))
    return formed, ev


def sunapha_formation(ctx, params):
    found = planets_in_house_from_moon(ctx, 2)
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="2nd from Moon",
        value=found, expected="a planet in 2nd from Moon (excl Sun/Rahu/Ketu)",
        actual=str(found or "none"), source="ChartFacts",
        significance="Sunapha formed" if found else "Sunapha not formed")]
    return bool(found), ev


def anapha_formation(ctx, params):
    found = planets_in_house_from_moon(ctx, 12)
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="12th from Moon",
        value=found, expected="a planet in 12th from Moon (excl Sun/Rahu/Ketu)",
        actual=str(found or "none"), source="ChartFacts",
        significance="Anapha formed" if found else "Anapha not formed")]
    return bool(found), ev


def durudhara_formation(ctx, params):
    f2 = planets_in_house_from_moon(ctx, 2)
    f12 = planets_in_house_from_moon(ctx, 12)
    ok = bool(f2 and f12)
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="2nd and 12th from Moon",
        value={"second": f2, "twelfth": f12},
        expected="planets on both sides", actual=str({"second": f2, "twelfth": f12}),
        source="ChartFacts",
        significance="Durudhara formed" if ok else "Durudhara not formed")]
    return ok, ev


def kemadruma_formation(ctx, params) -> Tuple[bool, List[Evidence]]:
    f2 = planets_in_house_from_moon(ctx, 2)
    f12 = planets_in_house_from_moon(ctx, 12)
    hm = moon_house(ctx)
    kendra_moon = []
    if hm is not None:
        for d in (0, 3, 6, 9):
            target = ((hm + d - 1) % 12) + 1
            for p in ("Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
                if house_of(ctx, p) == target and not (d == 0 and p == "Moon"):
                    kendra_moon.append(p)
        kendra_moon = sorted(set(kendra_moon))
    ok = (not f2) and (not f12) and (not kendra_moon)
    ev = [Evidence(
        evidence_type=EvidenceType.PLANET_IN_HOUSE, subject="Kemadruma isolation",
        value={"second": f2, "twelfth": f12, "kendra_from_moon": kendra_moon},
        expected="2nd & 12th empty and no planet in Kendra from Moon",
        actual=str({"second": f2, "twelfth": f12, "kendra_from_moon": kendra_moon}),
        source="ChartFacts",
        significance="Kemadruma formed" if ok else "Kemadruma not formed (companions present)")]
    return ok, ev


FORMATION_EVALUATORS = {
    "parashari_gaja_kesari_formation": gaja_kesari_formation,
    "parashari_budha_aditya_formation": budha_aditya_formation,
    "parashari_chandra_mangala_formation": chandra_mangala_formation,
    "parashari_adhi_formation": adhi_formation,
    "parashari_lakshmi_formation": lakshmi_formation,
    "parashari_saraswati_formation": saraswati_formation,
    "parashari_amala_formation": amala_formation,
    "parashari_vasumati_formation": vasumati_formation,
    "parashari_sunapha_formation": sunapha_formation,
    "parashari_anapha_formation": anapha_formation,
    "parashari_durudhara_formation": durudhara_formation,
    "parashari_kemadruma_formation": kemadruma_formation,
}
