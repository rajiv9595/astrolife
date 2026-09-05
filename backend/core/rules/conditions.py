"""
Conditions System — Astrolife V2 Phase 5A

Composable, deterministic condition classes for rule evaluation.
No eval(), no string parsing - pure Python objects with type safety.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from .enums import LogicalOperator, EvidenceType
from .models import Condition, Evidence, ConditionEvaluationResult
from .context import RuleContext


class ConditionOperator(Enum):
    """Comparison operators for value-based conditions"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "ge"
    LESS_THAN = "lt"
    LESS_EQUAL = "le"
    IN = "in"
    NOT_IN = "nin"
    CONTAINS = "contains"
    BETWEEN = "between"


@dataclass
class PrimitiveCondition:
    """A single atomic condition that evaluates to True/False with evidence"""
    condition_id: str
    condition_type: str
    evaluator: Callable[[RuleContext], tuple[bool, List[Evidence]]]
    
    def evaluate(self, context: RuleContext) -> ConditionEvaluationResult:
        passed, evidence = self.evaluator(context)
        return ConditionEvaluationResult(
            condition_id=self.condition_id,
            condition_type=self.condition_type,
            passed=passed,
            evidence=evidence
        )


class BaseCondition(ABC):
    """Base class for composable conditions"""
    
    def __init__(self, condition_id: str):
        self.condition_id = condition_id
        self.operator = LogicalOperator.AND
        self.children: List[BaseCondition] = []
        self.negated = False
    
    @abstractmethod
    def _evaluate_self(self, context: RuleContext) -> tuple[bool, List[Evidence]]:
        pass
    
    def evaluate(self, context: RuleContext) -> ConditionEvaluationResult:
        # Evaluate self
        self_passed, self_evidence = self._evaluate_self(context)
        
        # Evaluate children with logical operator
        if self.children:
            child_results = [child.evaluate(context) for child in self.children]
            child_passed = self._combine_children(child_results)
            passed = self_passed and child_passed
            all_evidence = self_evidence + [e for cr in child_results for e in cr.evidence]
        else:
            passed = self_passed
            all_evidence = self_evidence
        
        # Apply negation
        if self.negated:
            passed = not passed
        
        return ConditionEvaluationResult(
            condition_id=self.condition_id,
            condition_type=self.__class__.__name__,
            passed=passed,
            evidence=all_evidence,
            children=[cr for cr in child_results] if self.children else []
        )
    
    def _combine_children(self, results: List[ConditionEvaluationResult]) -> bool:
        if not results:
            return True
        
        if self.operator == LogicalOperator.AND:
            return all(r.passed for r in results)
        elif self.operator == LogicalOperator.OR:
            return any(r.passed for r in results)
        elif self.operator == LogicalOperator.NOT:
            return not all(r.passed for r in results)
        return False
    
    def add_child(self, child: BaseCondition, operator: LogicalOperator = LogicalOperator.AND) -> BaseCondition:
        self.children.append(child)
        self.operator = operator
        return self
    
    def and_(self, child: BaseCondition) -> BaseCondition:
        return self.add_child(child, LogicalOperator.AND)
    
    def or_(self, child: BaseCondition) -> BaseCondition:
        return self.add_child(child, LogicalOperator.OR)
    
    def not_(self) -> BaseCondition:
        self.negated = not self.negated
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "type": self.__class__.__name__,
            "operator": self.operator.value,
            "negated": self.negated,
            "children": [c.to_dict() for c in self.children]
        }


# ==================== Primitive Condition Factories ====================

def PlanetInSign(planet: str, sign: str, condition_id: str = None) -> BaseCondition:
    """Planet is in specific sign"""
    cid = condition_id or f"PlanetInSign_{planet}_{sign}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            actual_sign = ctx.get_planet_sign(planet)
            passed = actual_sign == sign
            evidence = [Evidence(
                evidence_type=EvidenceType.PLANET_IN_SIGN,
                subject=planet,
                value=actual_sign,
                expected=sign,
                actual=actual_sign,
                source="ChartFacts",
                significance=f"{planet} in {sign}" if passed else f"{planet} not in {sign} (in {actual_sign})"
            )] if actual_sign else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetInHouse(planet: str, house: int, condition_id: str = None) -> BaseCondition:
    """Planet is in specific house"""
    cid = condition_id or f"PlanetInHouse_{planet}_{house}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            actual_house = ctx.get_planet_house(planet)
            passed = actual_house == house
            evidence = [Evidence(
                evidence_type=EvidenceType.PLANET_IN_HOUSE,
                subject=planet,
                value=actual_house,
                expected=house,
                actual=actual_house,
                source="ChartFacts",
                significance=f"{planet} in house {house}" if passed else f"{planet} not in house {house} (in {actual_house})"
            )] if actual_house else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetInKendra(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is in Kendra house (1, 4, 7, 10)"""
    cid = condition_id or f"PlanetInKendra_{planet}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            house = ctx.get_planet_house(planet)
            passed = house in (1, 4, 7, 10) if house else False
            evidence = [Evidence(
                evidence_type=EvidenceType.KENDRA_TRIKONA,
                subject=planet,
                value=house,
                expected="Kendra (1,4,7,10)",
                actual=f"House {house}" if house else "Unknown",
                source="ChartFacts",
                significance=f"{planet} in Kendra house {house}" if passed else f"{planet} not in Kendra"
            )] if house else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetInTrikona(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is in Trikona house (1, 5, 9)"""
    cid = condition_id or f"PlanetInTrikona_{planet}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            house = ctx.get_planet_house(planet)
            passed = house in (1, 5, 9) if house else False
            evidence = [Evidence(
                evidence_type=EvidenceType.KENDRA_TRIKONA,
                subject=planet,
                value=house,
                expected="Trikona (1,5,9)",
                actual=f"House {house}" if house else "Unknown",
                source="ChartFacts",
                significance=f"{planet} in Trikona house {house}" if passed else f"{planet} not in Trikona"
            )] if house else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetInDusthana(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is in Dusthana house (6, 8, 12)"""
    cid = condition_id or f"PlanetInDusthana_{planet}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            house = ctx.get_planet_house(planet)
            passed = house in (6, 8, 12) if house else False
            evidence = [Evidence(
                evidence_type=EvidenceType.DUSTHANA,
                subject=planet,
                value=house,
                expected="Dusthana (6,8,12)",
                actual=f"House {house}" if house else "Unknown",
                source="ChartFacts",
                significance=f"{planet} in Dusthana house {house}" if passed else f"{planet} not in Dusthana"
            )] if house else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetOwnsHouse(planet: str, house: int, condition_id: str = None) -> BaseCondition:
    """Planet is lord of specific house"""
    cid = condition_id or f"PlanetOwnsHouse_{planet}_{house}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            lord = ctx.get_house_lord(house)
            passed = lord == planet
            evidence = [Evidence(
                evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
                subject=f"{planet} as lord of {house}",
                value=lord,
                expected=planet,
                actual=lord,
                source="ChartFacts",
                significance=f"{planet} rules house {house}" if passed else f"{planet} does not rule house {house} ({lord} does)"
            )]
            return passed, evidence
    
    return _Condition(cid)


def PlanetExalted(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is exalted"""
    cid = condition_id or f"PlanetExalted_{planet}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.is_exalted(planet)
            sign = ctx.get_planet_sign(planet)
            evidence = [Evidence(
                evidence_type=EvidenceType.PLANET_DIGNITY,
                subject=planet,
                value="Exalted" if passed else "Not Exalted",
                expected="Exalted",
                actual=ctx.get_dignity_category(planet),
                source="StrengthReport",
                significance=f"{planet} is exalted in {sign}" if passed else f"{planet} not exalted"
            )] if sign else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetDebilitated(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is debilitated"""
    cid = condition_id or f"PlanetDebilitated_{planet}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.is_debilitated(planet)
            sign = ctx.get_planet_sign(planet)
            evidence = [Evidence(
                evidence_type=EvidenceType.PLANET_DIGNITY,
                subject=planet,
                value="Debilitated" if passed else "Not Debilitated",
                expected="Debilitated",
                actual=ctx.get_dignity_category(planet),
                source="StrengthReport",
                significance=f"{planet} is debilitated in {sign}" if passed else f"{planet} not debilitated"
            )] if sign else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetInOwnSign(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is in own sign"""
    cid = condition_id or f"PlanetInOwnSign_{planet}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.is_own_sign(planet)
            sign = ctx.get_planet_sign(planet)
            evidence = [Evidence(
                evidence_type=EvidenceType.PLANET_DIGNITY,
                subject=planet,
                value="Own Sign" if passed else "Not Own Sign",
                expected="Own Sign",
                actual=ctx.get_dignity_category(planet),
                source="StrengthReport",
                significance=f"{planet} in own sign {sign}" if passed else f"{planet} not in own sign"
            )] if sign else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetInMoolatrikona(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is in Moolatrikona"""
    cid = condition_id or f"PlanetInMoolatrikona_{planet}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.is_moolatrikona(planet)
            sign = ctx.get_planet_sign(planet)
            evidence = [Evidence(
                evidence_type=EvidenceType.PLANET_DIGNITY,
                subject=planet,
                value="Moolatrikona" if passed else "Not Moolatrikona",
                expected="Moolatrikona",
                actual=ctx.get_dignity_category(planet),
                source="StrengthReport",
                significance=f"{planet} in Moolatrikona {sign}" if passed else f"{planet} not in Moolatrikona"
            )] if sign else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetsConjunct(planet1: str, planet2: str, orb_degrees: float = 8.0, condition_id: str = None) -> BaseCondition:
    """Two planets are conjunct within orb"""
    cid = condition_id or f"Conjunct_{planet1}_{planet2}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.are_conjunct(planet1, planet2, orb_degrees)
            evidence = [Evidence(
                evidence_type=EvidenceType.CONJUNCTION,
                subject=f"{planet1}-{planet2}",
                value="Conjunct" if passed else "Not Conjunct",
                expected=f"Within {orb_degrees}°",
                actual="Same house" if ctx.are_in_same_house(planet1, planet2) else "Different houses",
                source="ChartFacts",
                significance=f"{planet1} conjunct {planet2} (orb {orb_degrees}°)" if passed else f"{planet1} not conjunct {planet2}"
            )]
            return passed, evidence
    
    return _Condition(cid)


def PlanetAspectsPlanet(planet1: str, planet2: str, condition_id: str = None) -> BaseCondition:
    """Planet1 aspects Planet2 (Parashari)"""
    cid = condition_id or f"Aspects_{planet1}_{planet2}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.get_planet_aspecting_planet(planet1, planet2)
            evidence = [Evidence(
                evidence_type=EvidenceType.ASPECT,
                subject=f"{planet1} aspects {planet2}",
                value="Aspecting" if passed else "Not Aspecting",
                expected="Parashari aspect",
                actual="Yes" if passed else "No",
                source="ChartFacts",
                significance=f"{planet1} aspects {planet2}" if passed else f"{planet1} does not aspect {planet2}"
            )]
            return passed, evidence
    
    return _Condition(cid)


def PlanetAspectsHouse(planet: str, house: int, condition_id: str = None) -> BaseCondition:
    """Planet aspects a specific house"""
    cid = condition_id or f"AspectsHouse_{planet}_{house}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.is_planet_aspecting_house(planet, house)
            evidence = [Evidence(
                evidence_type=EvidenceType.ASPECT,
                subject=f"{planet} aspects house {house}",
                value="Aspecting" if passed else "Not Aspecting",
                expected=f"House {house}",
                actual="Yes" if passed else "No",
                source="ChartFacts",
                significance=f"{planet} aspects house {house}" if passed else f"{planet} does not aspect house {house}"
            )]
            return passed, evidence
    
    return _Condition(cid)


def LordOfHouseInHouse(lord_house: int, target_house: int, condition_id: str = None) -> BaseCondition:
    """Lord of house X is placed in house Y"""
    cid = condition_id or f"LordOf{_house_str(lord_house)}In{_house_str(target_house)}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            lord = ctx.get_house_lord(lord_house)
            if not lord:
                return False, [Evidence(
                    evidence_type=EvidenceType.HOUSE_LORD_POSITION,
                    subject=f"Lord of house {lord_house}",
                    value=None,
                    expected=f"In house {target_house}",
                    actual="No lord found",
                    source="ChartFacts"
                )]
            
            actual_house = ctx.get_planet_house(lord)
            passed = actual_house == target_house
            evidence = [Evidence(
                evidence_type=EvidenceType.HOUSE_LORD_POSITION,
                subject=f"{lord} (lord of {lord_house})",
                value=actual_house,
                expected=target_house,
                actual=actual_house,
                source="ChartFacts",
                significance=f"Lord of {lord_house} ({lord}) in house {target_house}" if passed else f"Lord of {lord_house} ({lord}) in house {actual_house}, not {target_house}"
            )] if actual_house else []
            return passed, evidence
    
    return _Condition(cid)


def LordsConjunct(house1: int, house2: int, orb_degrees: float = 8.0, condition_id: str = None) -> BaseCondition:
    """Lords of two houses are conjunct"""
    cid = condition_id or f"LordsConjunct_{house1}_{house2}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            lord1 = ctx.get_house_lord(house1)
            lord2 = ctx.get_house_lord(house2)
            if not lord1 or not lord2 or lord1 == lord2:
                return False, [Evidence(
                    evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
                    subject=f"Lords of {house1} and {house2}",
                    value="Same planet or missing",
                    expected="Different planets conjunct",
                    actual=f"{lord1}, {lord2}",
                    source="ChartFacts"
                )]
            
            passed = ctx.are_conjunct(lord1, lord2, orb_degrees)
            evidence = [Evidence(
                evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
                subject=f"{lord1} (L{lord1}) - {lord2} (L{lord2})",
                value="Conjunct" if passed else "Not Conjunct",
                expected=f"Within {orb_degrees}°",
                actual="Conjunct" if ctx.are_in_same_house(lord1, lord2) else "Not conjunct",
                source="ChartFacts",
                significance=f"Lords of {house1} and {house2} conjunct" if passed else f"Lords of {house1} and {house2} not conjunct"
            )]
            return passed, evidence
    
    return _Condition(cid)


def LordsMutuallyConnected(house1: int, house2: int, condition_id: str = None) -> BaseCondition:
    """Lords of two houses are mutually connected (conjunct, aspect, or exchange)"""
    cid = condition_id or f"LordsConnected_{house1}_{house2}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.are_lords_mutually_connected(house1, house2)
            lord1 = ctx.get_house_lord(house1)
            lord2 = ctx.get_house_lord(house2)
            evidence = [Evidence(
                evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
                subject=f"Lords of {house1} ({lord1}) and {house2} ({lord2})",
                value="Connected" if passed else "Not Connected",
                expected="Mutual connection",
                actual="Connected" if passed else "No connection",
                source="ChartFacts",
                significance=f"Lords of {house1} and {house2} mutually connected" if passed else f"Lords of {house1} and {house2} not connected"
            )] if lord1 and lord2 else []
            return passed, evidence
    
    return _Condition(cid)


def ExchangeOfSigns(planet1: str, planet2: str, condition_id: str = None) -> BaseCondition:
    """Two planets exchange signs (Parivartana)"""
    cid = condition_id or f"Exchange_{planet1}_{planet2}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.is_exchange(planet1, planet2)
            p1_sign = ctx.get_planet_sign(planet1)
            p2_sign = ctx.get_planet_sign(planet2)
            evidence = [Evidence(
                evidence_type=EvidenceType.EXCHANGE,
                subject=f"{planet1}-{planet2}",
                value="Exchange" if passed else "No Exchange",
                expected="Mutual sign exchange",
                actual=f"{planet1} in {p1_sign}, {planet2} in {p2_sign}",
                source="ChartFacts",
                significance=f"{planet1} and {planet2} in Parivartana" if passed else f"No Parivartana between {planet1} and {planet2}"
            )]
            return passed, evidence
    
    return _Condition(cid)


def BeneficPlanet(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is natural benefic"""
    cid = condition_id or f"BeneficPlanet_{planet}"
    NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = planet in NATURAL_BENEFICS
            evidence = [Evidence(
                evidence_type=EvidenceType.CUSTOM,
                subject=planet,
                value="Natural Benefic" if passed else "Not Natural Benefic",
                expected="Jupiter, Venus, Mercury, or Moon",
                actual=planet,
                source="Classical Definition",
                significance=f"{planet} is a natural benefic" if passed else f"{planet} is not a natural benefic"
            )]
            return passed, evidence
    
    return _Condition(cid)


def MaleficPlanet(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is natural malefic"""
    cid = condition_id or f"MaleficPlanet_{planet}"
    NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = planet in NATURAL_MALEFICS
            evidence = [Evidence(
                evidence_type=EvidenceType.CUSTOM,
                subject=planet,
                value="Natural Malefic" if passed else "Not Natural Malefic",
                expected="Sun, Mars, Saturn, Rahu, or Ketu",
                actual=planet,
                source="Classical Definition",
                significance=f"{planet} is a natural malefic" if passed else f"{planet} is not a natural malefic"
            )]
            return passed, evidence
    
    return _Condition(cid)


def FunctionalBenefic(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is functional benefic for the ascendant"""
    cid = condition_id or f"FunctionalBenefic_{planet}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.is_functional_benefic(planet)
            nature = ctx.get_functional_nature(planet)
            evidence = [Evidence(
                evidence_type=EvidenceType.FUNCTIONAL_NATURE,
                subject=planet,
                value="Functional Benefic" if passed else "Not Functional Benefic",
                expected="YOGAKARAKA or FUNCTIONAL_BENEFIC",
                actual=nature,
                source="StrengthReport",
                significance=f"{planet} is functional benefic ({nature})" if passed else f"{planet} is not functional benefic ({nature})"
            )] if nature else []
            return passed, evidence
    
    return _Condition(cid)


def FunctionalMalefic(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is functional malefic for the ascendant"""
    cid = condition_id or f"FunctionalMalefic_{planet}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.is_functional_malefic(planet)
            nature = ctx.get_functional_nature(planet)
            evidence = [Evidence(
                evidence_type=EvidenceType.FUNCTIONAL_NATURE,
                subject=planet,
                value="Functional Malefic" if passed else "Not Functional Malefic",
                expected="FUNCTIONAL_MALEFIC or MARAKA",
                actual=nature,
                source="StrengthReport",
                significance=f"{planet} is functional malefic ({nature})" if passed else f"{planet} is not functional malefic ({nature})"
            )] if nature else []
            return passed, evidence
    
    return _Condition(cid)


def Yogakaraka(planet: str, condition_id: str = None) -> BaseCondition:
    """Planet is Yogakaraka for the ascendant"""
    cid = condition_id or f"Yogakaraka_{planet}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.is_yogakaraka(planet)
            evidence = [Evidence(
                evidence_type=EvidenceType.YOGAKARAKA,
                subject=planet,
                value="Yogakaraka" if passed else "Not Yogakaraka",
                expected="Rules both Kendra and Trikona",
                actual="Yes" if passed else "No",
                source="StrengthReport",
                significance=f"{planet} is Yogakaraka" if passed else f"{planet} is not Yogakaraka"
            )]
            return passed, evidence
    
    return _Condition(cid)


def StrongPlanet(planet: str, threshold: float = 1.0, condition_id: str = None) -> BaseCondition:
    """Planet has Shadbala ratio >= threshold"""
    cid = condition_id or f"StrongPlanet_{planet}_{threshold}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            ratio = ctx.get_shadbala_ratio(planet)
            passed = ratio is not None and ratio >= threshold
            evidence = [Evidence(
                evidence_type=EvidenceType.PLANET_STRENGTH,
                subject=planet,
                value=ratio,
                expected=f">= {threshold}",
                actual=ratio,
                source="StrengthReport",
                significance=f"{planet} Shadbala ratio {ratio:.3f} (strong)" if passed else f"{planet} Shadbala ratio {ratio:.3f} (weak, threshold {threshold})"
            )] if ratio is not None else []
            return passed, evidence
    
    return _Condition(cid)


def WeakPlanet(planet: str, threshold: float = 1.0, condition_id: str = None) -> BaseCondition:
    """Planet has Shadbala ratio < threshold"""
    cid = condition_id or f"WeakPlanet_{planet}_{threshold}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            ratio = ctx.get_shadbala_ratio(planet)
            passed = ratio is not None and ratio < threshold
            evidence = [Evidence(
                evidence_type=EvidenceType.PLANET_STRENGTH,
                subject=planet,
                value=ratio,
                expected=f"< {threshold}",
                actual=ratio,
                source="StrengthReport",
                significance=f"{planet} Shadbala ratio {ratio:.3f} (weak)" if passed else f"{planet} Shadbala ratio {ratio:.3f} (strong, threshold {threshold})"
            )] if ratio is not None else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetInVargaSign(planet: str, varga_num: int, sign: str, condition_id: str = None) -> BaseCondition:
    """Planet is in specific sign in a varga"""
    cid = condition_id or f"Varga{planet}_D{varga_num}_{sign}"
    
    class _Condition(BaseCondition):
        def _evaluate_self(self, ctx: RuleContext) -> tuple[bool, List[Evidence]]:
            passed = ctx.is_planet_in_varga_sign(planet, varga_num, sign)
            actual_sign = ctx.get_varga_sign(planet, varga_num)
            evidence = [Evidence(
                evidence_type=EvidenceType.VARGA_POSITION,
                subject=f"{planet} in D{varga_num}",
                value=actual_sign,
                expected=sign,
                actual=actual_sign,
                source="VargaFacts",
                significance=f"{planet} in {sign} in D{varga_num}" if passed else f"{planet} in {actual_sign} in D{varga_num}, not {sign}"
            )] if actual_sign else []
            return passed, evidence
    
    return _Condition(cid)


def PlanetAboveStrengthThreshold(planet: str, threshold: float, condition_id: str = None) -> BaseCondition:
    """Planet Shadbala ratio above threshold"""
    return StrongPlanet(planet, threshold, condition_id)


def PlanetBelowStrengthThreshold(planet: str, threshold: float, condition_id: str = None) -> BaseCondition:
    """Planet Shadbala ratio below threshold"""
    return WeakPlanet(planet, threshold, condition_id)


# ==================== Composite Condition Builders ====================

class AllOf(BaseCondition):
    """All conditions must pass (AND)"""
    def __init__(self, condition_id: str, conditions: List[BaseCondition]):
        super().__init__(condition_id)
        self.operator = LogicalOperator.AND
        self.children = conditions
    
    def _evaluate_self(self, context: RuleContext) -> tuple[bool, List[Evidence]]:
        return True, []


class AnyOf(BaseCondition):
    """At least one condition must pass (OR)"""
    def __init__(self, condition_id: str, conditions: List[BaseCondition]):
        super().__init__(condition_id)
        self.operator = LogicalOperator.OR
        self.children = conditions
    
    def _evaluate_self(self, context: RuleContext) -> tuple[bool, List[Evidence]]:
        return True, []


class Not(BaseCondition):
    """Negate a condition"""
    def __init__(self, condition_id: str, condition: BaseCondition):
        super().__init__(condition_id)
        self.operator = LogicalOperator.NOT
        self.children = [condition]
    
    def _evaluate_self(self, context: RuleContext) -> tuple[bool, List[Evidence]]:
        return True, []


def _house_str(h: int) -> str:
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    suffix = suffixes.get(h % 10, "th") if h % 100 not in (11, 12, 13) else "th"
    return f"{h}{suffix}"


# ==================== Condition Registry ====================

class ConditionRegistry:
    """Registry of named conditions for reuse"""
    
    _conditions: Dict[str, Callable[..., BaseCondition]] = {
        "planet_in_sign": PlanetInSign,
        "planet_in_house": PlanetInHouse,
        "planet_in_kendra": PlanetInKendra,
        "planet_in_trikona": PlanetInTrikona,
        "planet_in_dusthana": PlanetInDusthana,
        "planet_owns_house": PlanetOwnsHouse,
        "planet_exalted": PlanetExalted,
        "planet_debilitated": PlanetDebilitated,
        "planet_in_own_sign": PlanetInOwnSign,
        "planet_in_moolatrikona": PlanetInMoolatrikona,
        "planets_conjunct": PlanetsConjunct,
        "planet_aspects_planet": PlanetAspectsPlanet,
        "planet_aspects_house": PlanetAspectsHouse,
        "lord_of_house_in_house": LordOfHouseInHouse,
        "lords_conjunct": LordsConjunct,
        "lords_mutually_connected": LordsMutuallyConnected,
        "exchange_of_signs": ExchangeOfSigns,
        "benefic_planet": BeneficPlanet,
        "malefic_planet": MaleficPlanet,
        "functional_benefic": FunctionalBenefic,
        "functional_malefic": FunctionalMalefic,
        "yogakaraka": Yogakaraka,
        "strong_planet": StrongPlanet,
        "weak_planet": WeakPlanet,
        "planet_in_varga_sign": PlanetInVargaSign,
        "planet_above_strength": PlanetAboveStrengthThreshold,
        "planet_below_strength": PlanetBelowStrengthThreshold,
    }
    
    @classmethod
    def get(cls, name: str) -> Optional[Callable]:
        return cls._conditions.get(name)
    
    @classmethod
    def register(cls, name: str, factory: Callable[..., BaseCondition]):
        cls._conditions[name] = factory
    
    @classmethod
    def list_conditions(cls) -> List[str]:
        return list(cls._conditions.keys())
    
    @classmethod
    def create(cls, name: str, **kwargs) -> Optional[BaseCondition]:
        factory = cls.get(name)
        if factory:
            return factory(**kwargs)
        return None


# ==================== Serialization Helpers ====================

def condition_to_dict(condition: BaseCondition) -> Dict[str, Any]:
    return condition.to_dict()


def condition_from_dict(data: Dict[str, Any]) -> Optional[BaseCondition]:
    """Deserialize condition from dict (for future rule loading)"""
    # This would be expanded for full serialization support
    pass