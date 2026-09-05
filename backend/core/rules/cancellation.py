"""
Cancellation Evaluators — Astrolife V2 Phase 5A

Separate evaluators for rule cancellation (Neecha Bhanga, Kemadruma cancellation, etc.).
Cancellation is evaluated INDEPENDENTLY from formation and strength.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .models import RuleResult, Evidence, CancellationStatus, CancellationRule
from .context import RuleContext
from .enums import EvidenceType
from .conditions import PlanetExalted, PlanetInKendra, PlanetAspectsPlanet, LordsMutuallyConnected


@dataclass
class CancellationEvaluator:
    """Base cancellation evaluator"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        cancel_rule: CancellationRule
    ) -> tuple[bool, List[Evidence]]:
        raise NotImplementedError


class DefaultCancellationEvaluator:
    """Default cancellation evaluator - checks for standard cancellation patterns"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        cancel_rule: CancellationRule
    ) -> tuple[bool, List[Evidence]]:
        """
        Checks for common cancellation patterns based on rule category.
        This is a fallback - specific rules should define their own cancellation.
        """
        # No default cancellation
        return False, []


class NeechaBhangaCancellationEvaluator:
    """
    Evaluates Neecha Bhanga (cancellation of debilitation).
    
    Classical rules for cancellation:
    1. Lord of debilitation sign in Kendra from Lagna or Moon
    2. Lord of exaltation sign in Kendra from Lagna or Moon
    3. Debilitated planet conjunct exalted planet
    4. Debilitated planet aspected by lord of its sign
    5. Exchange (Parivartana) with lord of debilitation sign
    6. Debilitated planet in Kendra from Lagna or Moon
    """
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        cancel_rule: CancellationRule
    ) -> tuple[bool, List[Evidence]]:
        """
        Expects result.relevant_planets to contain debilitated planets.
        Checks all classical Neecha Bhanga conditions.
        """
        debilitated_planets = []
        
        # Find debilitated planets in relevant planets
        for planet in result.relevant_planets:
            if context.is_debilitated(planet):
                debilitated_planets.append(planet)
        
        if not debilitated_planets:
            return False, [Evidence(
                evidence_type=EvidenceType.CUSTOM,
                subject="Neecha Bhanga Check",
                value="No debilitated planets in rule",
                expected="Debilitated planets to check",
                actual="None found",
                source="ChartFacts"
            )]
        
        all_cancellations = []
        all_evidence = []
        
        for planet in debilitated_planets:
            cancellations, evidence = NeechaBhangaCancellationEvaluator._check_planet_cancellation(
                context, planet
            )
            all_cancellations.extend(cancellations)
            all_evidence.extend(evidence)
        
        is_cancelled = len(all_cancellations) > 0
        
        summary = Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Neecha Bhanga Summary",
            value={"cancelled_planets": all_cancellations},
            expected="At least one cancellation",
            actual=f"Cancelled: {all_cancellations}" if all_cancellations else "No cancellations",
            source="NeechaBhangaCancellationEvaluator",
            significance=f"Neecha Bhanga: {all_cancellations}" if all_cancellations else "No Neecha Bhanga found"
        )
        all_evidence.append(summary)
        
        return is_cancelled, all_evidence
    
    @staticmethod
    def _check_planet_cancellation(context: RuleContext, planet: str) -> tuple[List[str], List[Evidence]]:
        """Check all Neecha Bhanga conditions for a planet"""
        cancellations = []
        evidence = []
        
        planet_sign = context.get_planet_sign(planet)
        if not planet_sign:
            return cancellations, evidence
        
        # Get lords
        debilitation_lord = context.get_lord_of_sign(planet_sign)
        exaltation_signs = {
            "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
            "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra"
        }
        exaltation_sign = exaltation_signs.get(planet)
        exaltation_lord = context.get_lord_of_sign(exaltation_sign) if exaltation_sign else None
        planet_lord = context.get_lord_of_sign(planet_sign)  # Same as debilitation_lord
        
        # 1. Lord of debilitation sign in Kendra from Lagna
        if debilitation_lord:
            if context.is_kendra_from(debilitation_lord, "Lagna") if hasattr(context, 'is_kendra_from') else False:
                # Need to check from ascendant
                lagna_house = 1
                dl_house = context.get_planet_house(debilitation_lord)
                if dl_house and ((dl_house - lagna_house) % 12) in (0, 3, 6, 9):
                    cancellations.append(f"{planet}: Lord of debilitation ({debilitation_lord}) in Kendra from Lagna")
                    evidence.append(Evidence(
                        evidence_type=EvidenceType.CUSTOM,
                        subject=f"Neecha Bhanga: {planet}",
                        value=f"Lord of debilitation ({debilitation_lord}) in Kendra from Lagna",
                        expected="Cancellation condition met",
                        actual=f"{debilitation_lord} in house {dl_house}",
                        source="ChartFacts",
                        significance=f"Condition 1 met for {planet}"
                    ))
        
        # 2. Lord of exaltation sign in Kendra from Lagna
        if exaltation_lord:
            el_house = context.get_planet_house(exaltation_lord)
            if el_house and ((el_house - 1) % 12) in (0, 3, 6, 9):
                cancellations.append(f"{planet}: Lord of exaltation ({exaltation_lord}) in Kendra from Lagna")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.CUSTOM,
                    subject=f"Neecha Bhanga: {planet}",
                    value=f"Lord of exaltation ({exaltation_lord}) in Kendra from Lagna",
                    expected="Cancellation condition met",
                    actual=f"{exaltation_lord} in house {el_house}",
                    source="ChartFacts",
                    significance=f"Condition 2 met for {planet}"
                ))
        
        # 3. Lord of debilitation sign in Kendra from Moon
        moon_house = context.get_planet_house("Moon")
        if debilitation_lord and moon_house:
            dl_house = context.get_planet_house(debilitation_lord)
            if dl_house and ((dl_house - moon_house) % 12) in (0, 3, 6, 9):
                cancellations.append(f"{planet}: Lord of debilitation ({debilitation_lord}) in Kendra from Moon")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.CUSTOM,
                    subject=f"Neecha Bhanga: {planet}",
                    value=f"Lord of debilitation ({debilitation_lord}) in Kendra from Moon",
                    expected="Cancellation condition met",
                    actual=f"{debilitation_lord} in house {dl_house}, Moon in {moon_house}",
                    source="ChartFacts",
                    significance=f"Condition 3 met for {planet}"
                ))
        
        # 4. Lord of exaltation sign in Kendra from Moon
        if exaltation_lord and moon_house:
            el_house = context.get_planet_house(exaltation_lord)
            if el_house and ((el_house - moon_house) % 12) in (0, 3, 6, 9):
                cancellations.append(f"{planet}: Lord of exaltation ({exaltation_lord}) in Kendra from Moon")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.CUSTOM,
                    subject=f"Neecha Bhanga: {planet}",
                    value=f"Lord of exaltation ({exaltation_lord}) in Kendra from Moon",
                    expected="Cancellation condition met",
                    actual=f"{exaltation_lord} in house {el_house}, Moon in {moon_house}",
                    source="ChartFacts",
                    significance=f"Condition 4 met for {planet}"
                ))
        
        # 5. Debilitated planet conjunct exalted planet
        for other_planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            if other_planet == planet:
                continue
            if context.is_exalted(other_planet) and context.are_conjunct(planet, other_planet):
                cancellations.append(f"{planet}: Conjunct exalted {other_planet}")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.CONJUNCTION,
                    subject=f"Neecha Bhanga: {planet}",
                    value=f"Conjunct exalted {other_planet}",
                    expected="Conjunction with exalted planet",
                    actual=f"{planet} conjunct {other_planet}",
                    source="ChartFacts",
                    significance=f"Condition 5 met for {planet}"
                ))
        
        # 6. Debilitated planet aspected by its own lord
        if planet_lord and context.get_planet_aspecting_planet(planet_lord, planet):
            cancellations.append(f"{planet}: Aspected by own lord ({planet_lord})")
            evidence.append(Evidence(
                evidence_type=EvidenceType.ASPECT,
                subject=f"Neecha Bhanga: {planet}",
                value=f"Aspected by lord {planet_lord}",
                expected="Aspect from own lord",
                actual=f"{planet_lord} aspects {planet}",
                source="ChartFacts",
                significance=f"Condition 6 met for {planet}"
            ))
        
        # 7. Exchange with lord of debilitation sign
        if debilitation_lord and context.is_exchange(planet, debilitation_lord):
            cancellations.append(f"{planet}: Exchange with lord of debilitation ({debilitation_lord})")
            evidence.append(Evidence(
                evidence_type=EvidenceType.EXCHANGE,
                subject=f"Neecha Bhanga: {planet}",
                value=f"Exchange with {debilitation_lord}",
                expected="Parivartana with debilitation lord",
                actual=f"{planet} in {planet_sign}, {debilitation_lord} in {context.get_planet_sign(debilitation_lord)}",
                source="ChartFacts",
                significance=f"Condition 7 met for {planet}"
            ))
        
        # 8. Debilitated planet in Kendra from Lagna
        p_house = context.get_planet_house(planet)
        if p_house and p_house in (1, 4, 7, 10):
            cancellations.append(f"{planet}: Debilitated planet in Kendra from Lagna")
            evidence.append(Evidence(
                evidence_type=EvidenceType.KENDRA_TRIKONA,
                subject=f"Neecha Bhanga: {planet}",
                value=f"In Kendra house {p_house}",
                expected="Debilitated planet in Kendra",
                actual=f"House {p_house}",
                source="ChartFacts",
                significance=f"Condition 8 met for {planet}"
            ))
        
        # 9. Debilitated planet in Kendra from Moon
        if p_house and moon_house and ((p_house - moon_house) % 12) in (0, 3, 6, 9):
            cancellations.append(f"{planet}: Debilitated planet in Kendra from Moon")
            evidence.append(Evidence(
                evidence_type=EvidenceType.KENDRA_TRIKONA,
                subject=f"Neecha Bhanga: {planet}",
                value=f"In Kendra from Moon (house {p_house})",
                expected="Debilitated planet in Kendra from Moon",
                actual=f"Planet house {p_house}, Moon house {moon_house}",
                source="ChartFacts",
                significance=f"Condition 9 met for {planet}"
            ))
        
        return cancellations, evidence


class KemadrumaCancellationEvaluator:
    """
    Evaluates Kemadruma Yoga cancellation.
    
    Kemadruma forms when no planets in 2nd/12th from Moon (excl. Sun, Rahu, Ketu).
    Cancellations:
    1. Planets in Kendra from Lagna
    2. Planets in Kendra from Moon
    3. Moon in Kendra
    4. Moon aspected by benefics
    5. Moon conjunct benefics
    6. Moon in own/exaltation sign
    """
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        cancel_rule: CancellationRule
    ) -> tuple[bool, List[Evidence]]:
        """Check Kemadruma cancellation conditions"""
        
        # Only applies if Kemadruma formed (formation check done elsewhere)
        # Here we check if any cancellation condition exists
        
        cancellations = []
        evidence = []
        
        moon_house = context.get_planet_house("Moon")
        if not moon_house:
            return False, [Evidence(
                evidence_type=EvidenceType.CUSTOM,
                subject="Kemadruma Cancellation",
                value="Moon house unknown",
                expected="Valid Moon position",
                actual="Unknown",
                source="ChartFacts"
            )]
        
        # 1. Planets in Kendra from Lagna
        kendra_planets_lagna = context.get_planets_in_kendra()
        if kendra_planets_lagna:
            cancellations.append(f"Planets in Kendra from Lagna: {kendra_planets_lagna}")
            evidence.append(Evidence(
                evidence_type=EvidenceType.KENDRA_TRIKONA,
                subject="Kemadruma Cancellation",
                value=kendra_planets_lagna,
                expected="Planets in Kendra (1,4,7,10)",
                actual=f"Kendra planets: {kendra_planets_lagna}",
                source="ChartFacts",
                significance="Cancellation 1: Planets in Kendra from Lagna"
            ))
        
        # 2. Planets in Kendra from Moon
        moon_kendras = [(moon_house + i - 1) % 12 + 1 for i in [1, 4, 7, 10]]
        moon_kendra_planets = []
        for h in moon_kendras:
            moon_kendra_planets.extend(context.get_planets_in_house(h))
        if moon_kendra_planets:
            cancellations.append(f"Planets in Kendra from Moon: {moon_kendra_planets}")
            evidence.append(Evidence(
                evidence_type=EvidenceType.KENDRA_TRIKONA,
                subject="Kemadruma Cancellation",
                value=moon_kendra_planets,
                expected="Planets in Kendra from Moon",
                actual=f"Moon in {moon_house}, Kendra houses {moon_kendras}, planets: {moon_kendra_planets}",
                source="ChartFacts",
                significance="Cancellation 2: Planets in Kendra from Moon"
            ))
        
        # 3. Moon in Kendra
        if moon_house in (1, 4, 7, 10):
            cancellations.append("Moon in Kendra")
            evidence.append(Evidence(
                evidence_type=EvidenceType.KENDRA_TRIKONA,
                subject="Kemadruma Cancellation",
                value=f"Moon in house {moon_house}",
                expected="Moon in Kendra",
                actual=f"Moon in house {moon_house}",
                source="ChartFacts",
                significance="Cancellation 3: Moon in Kendra"
            ))
        
        # 4. Moon aspected by benefics
        benefics = ["Jupiter", "Venus", "Mercury"]
        for b in benefics:
            if context.get_planet_aspecting_planet(b, "Moon"):
                cancellations.append(f"Moon aspected by benefic {b}")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.ASPECT,
                    subject="Kemadruma Cancellation",
                    value=f"Moon aspected by {b}",
                    expected="Benefic aspect on Moon",
                    actual=f"{b} aspects Moon",
                    source="ChartFacts",
                    significance=f"Cancellation 4: Moon aspected by {b}"
                ))
        
        # 5. Moon conjunct benefics
        for b in benefics:
            if context.are_conjunct("Moon", b):
                cancellations.append(f"Moon conjunct benefic {b}")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.CONJUNCTION,
                    subject="Kemadruma Cancellation",
                    value=f"Moon conjunct {b}",
                    expected="Conjunction with benefic",
                    actual=f"Moon conjunct {b}",
                    source="ChartFacts",
                    significance=f"Cancellation 5: Moon conjunct {b}"
                ))
        
        # 6. Moon in own/exaltation sign
        moon_sign = context.get_planet_sign("Moon")
        if moon_sign:
            if context.is_exalted("Moon") or context.is_own_sign("Moon"):
                cancellations.append(f"Moon in own/exaltation sign ({moon_sign})")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.PLANET_DIGNITY,
                    subject="Kemadruma Cancellation",
                    value=f"Moon in {moon_sign}",
                    expected="Moon in own/exaltation sign",
                    actual=f"Moon in {moon_sign} ({'Exalted' if context.is_exalted('Moon') else 'Own Sign'})",
                    source="StrengthReport",
                    significance="Cancellation 6: Moon in own/exaltation sign"
                ))
        
        is_cancelled = len(cancellations) > 0
        
        summary = Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Kemadruma Cancellation Summary",
            value={"cancellations": cancellations},
            expected="At least one cancellation",
            actual=f"Cancelled: {cancellations}" if cancellations else "No cancellations",
            source="KemadrumaCancellationEvaluator",
            significance=f"Kemadruma cancelled by: {cancellations}" if cancellations else "Kemadruma not cancelled"
        )
        evidence.append(summary)
        
        return is_cancelled, evidence


class ManglikCancellationEvaluator:
    """
    Evaluates Manglik (Kuja) Dosha cancellation.
    
    Manglik forms when Mars in 1, 4, 7, 8, 12 from Lagna/Moon/Venus.
    Cancellations:
    1. Mars in own sign (Aries/Scorpio) or exaltation (Capricorn)
    2. Mars conjunct/aspected by Jupiter
    3. Mars in Kendra/Trikona from Lagna with benefic aspect
    4. Spouse also Manglik (external - not checkable here)
    5. Mars in 2nd house (some traditions)
    """
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        cancel_rule: CancellationRule
    ) -> tuple[bool, List[Evidence]]:
        """Check Manglik cancellation conditions"""
        
        cancellations = []
        evidence = []
        
        mars_sign = context.get_planet_sign("Mars")
        mars_house = context.get_planet_house("Mars")
        
        if not mars_sign or not mars_house:
            return False, []
        
        # 1. Mars in own sign or exaltation
        if context.is_exalted("Mars") or context.is_own_sign("Mars"):
            cancellations.append(f"Mars in {'exaltation' if context.is_exalted('Mars') else 'own sign'} ({mars_sign})")
            evidence.append(Evidence(
                evidence_type=EvidenceType.PLANET_DIGNITY,
                subject="Manglik Cancellation",
                value=f"Mars in {mars_sign}",
                expected="Mars in own/exaltation sign",
                actual=f"Mars in {mars_sign}",
                source="StrengthReport",
                significance="Cancellation 1: Mars in own/exaltation sign"
            ))
        
        # 2. Mars conjunct/aspected by Jupiter
        if context.are_conjunct("Mars", "Jupiter"):
            cancellations.append("Mars conjunct Jupiter")
            evidence.append(Evidence(
                evidence_type=EvidenceType.CONJUNCTION,
                subject="Manglik Cancellation",
                value="Mars conjunct Jupiter",
                expected="Mars conjunct Jupiter",
                actual="Mars conjunct Jupiter",
                source="ChartFacts",
                significance="Cancellation 2: Mars conjunct Jupiter"
            ))
        elif context.get_planet_aspecting_planet("Jupiter", "Mars"):
            cancellations.append("Mars aspected by Jupiter")
            evidence.append(Evidence(
                evidence_type=EvidenceType.ASPECT,
                subject="Manglik Cancellation",
                value="Jupiter aspects Mars",
                expected="Jupiter aspect on Mars",
                actual="Jupiter aspects Mars",
                source="ChartFacts",
                significance="Cancellation 2: Mars aspected by Jupiter"
            ))
        
        # 3. Mars in Kendra/Trikona with benefic aspect
        if mars_house in (1, 4, 5, 7, 9, 10):
            benefics = ["Jupiter", "Venus", "Mercury"]
            for b in benefics:
                if context.get_planet_aspecting_planet(b, "Mars"):
                    cancellations.append(f"Mars in Kendra/Trikona (house {mars_house}) aspected by {b}")
                    evidence.append(Evidence(
                        evidence_type=EvidenceType.ASPECT,
                        subject="Manglik Cancellation",
                        value=f"Mars in house {mars_house} aspected by {b}",
                        expected="Benefic aspect on Mars in Kendra/Trikona",
                        actual=f"Mars in {mars_house}, {b} aspects Mars",
                        source="ChartFacts",
                        significance=f"Cancellation 3: Mars in Kendra/Trikona with benefic aspect"
                    ))
        
        is_cancelled = len(cancellations) > 0
        
        summary = Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Manglik Cancellation Summary",
            value={"cancellations": cancellations},
            expected="At least one cancellation",
            actual=f"Cancelled: {cancellations}" if cancellations else "No cancellations",
            source="ManglikCancellationEvaluator",
            significance=f"Manglik cancelled by: {cancellations}" if cancellations else "Manglik not cancelled"
        )
        evidence.append(summary)
        
        return is_cancelled, evidence


class RajaYogaCancellationEvaluator:
    """
    Evaluates Raja Yoga cancellation (e.g., Dharma Karmadhipati exceptions).
    
    Common cancellations:
    1. Lords in Dusthana (6, 8, 12)
    2. Lords combust
    3. Lords debilitated without Neecha Bhanga
    4. Lords in enemy signs
    5. Malefic association without benefic support
    """
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        cancel_rule: CancellationRule
    ) -> tuple[bool, List[Evidence]]:
        """Check Raja Yoga cancellation conditions"""
        
        cancellations = []
        evidence = []
        
        # Check relevant planets for afflictions
        for planet in result.relevant_planets:
            p_house = context.get_planet_house(planet)
            p_sign = context.get_planet_sign(planet)
            
            if not p_house or not p_sign:
                continue
            
            # 1. Planet in Dusthana
            if p_house in (6, 8, 12):
                cancellations.append(f"{planet} in Dusthana house {p_house}")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.DUSTHANA,
                    subject=f"Raja Yoga Cancellation: {planet}",
                    value=f"House {p_house}",
                    expected="Not in Dusthana",
                    actual=f"House {p_house}",
                    source="ChartFacts",
                    significance=f"Cancellation: {planet} in Dusthana"
                ))
            
            # 2. Planet combust (check Sun proximity)
            if planet != "Sun":
                sun_lon = context.get_planet_longitude("Sun")
                p_lon = context.get_planet_longitude(planet)
                if sun_lon and p_lon:
                    diff = abs(sun_lon - p_lon)
                    diff = min(diff, 360 - diff)
                    # Combustion orbs (approximate)
                    combust_orbs = {"Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15}
                    orb = combust_orbs.get(planet, 8)
                    if diff <= orb:
                        cancellations.append(f"{planet} combust (within {orb}° of Sun)")
                        evidence.append(Evidence(
                            evidence_type=EvidenceType.CUSTOM,
                            subject=f"Raja Yoga Cancellation: {planet}",
                            value=f"Combust (Sun diff {diff:.2f}°)",
                            expected="Not combust",
                            actual=f"Combust within {orb}°",
                            source="ChartFacts",
                            significance=f"Cancellation: {planet} combust"
                        ))
            
            # 3. Planet debilitated without Neecha Bhanga
            if context.is_debilitated(planet):
                # Quick check for any Neecha Bhanga
                has_cancellation = False
                deb_lord = context.get_lord_of_sign(p_sign)
                if deb_lord and context.get_planet_house(deb_lord):
                    dl_house = context.get_planet_house(deb_lord)
                    if dl_house and ((dl_house - 1) % 12) in (0, 3, 6, 9):
                        has_cancellation = True
                
                if not has_cancellation:
                    cancellations.append(f"{planet} debilitated in {p_sign} without Neecha Bhanga")
                    evidence.append(Evidence(
                        evidence_type=EvidenceType.PLANET_DIGNITY,
                        subject=f"Raja Yoga Cancellation: {planet}",
                        value=f"Debilitated in {p_sign}",
                        expected="Not debilitated or Neecha Bhanga",
                        actual=f"Debilitated, no cancellation found",
                        source="StrengthReport",
                        significance=f"Cancellation: {planet} debilitated"
                    ))
        
        is_cancelled = len(cancellations) > 0
        
        summary = Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Raja Yoga Cancellation Summary",
            value={"cancellations": cancellations},
            expected="At least one cancellation",
            actual=f"Cancelled: {cancellations}" if cancellations else "No cancellations",
            source="RajaYogaCancellationEvaluator",
            significance=f"Raja Yoga cancelled by: {cancellations}" if cancellations else "Raja Yoga not cancelled"
        )
        evidence.append(summary)
        
        return is_cancelled, evidence