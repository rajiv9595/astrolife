"""
Activation Evaluators — Astrolife V2 Phase 5A

Separate evaluators for rule activation based on Dasha, Transit, and other timing factors.
Activation is evaluated INDEPENDENTLY from formation.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .models import RuleResult, Evidence, ActivationStatus, ActivationRule
from .context import RuleContext
from .enums import EvidenceType


@dataclass
class ActivationEvaluator:
    """Base activation evaluator"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        activation_rule: ActivationRule,
        params: Dict[str, Any] = None
    ) -> tuple[bool, List[Evidence]]:
        raise NotImplementedError


class DefaultActivationEvaluator:
    """Default activation evaluator using Dasha hierarchy"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        activation_rule: ActivationRule,
        params: Dict[str, Any] = None
    ) -> tuple[bool, List[Evidence]]:
        """Check if relevant planets are active in current Dasha"""
        
        mahadasha = context.get_current_mahadasha()
        antardasha = context.get_current_antardasha()
        pratyantar = None
        
        # Get deeper hierarchy if available
        hierarchy = context.get_dasha_hierarchy()
        if len(hierarchy) >= 3:
            pratyantar = hierarchy[2]
        
        dasha_planets = [p for p in [mahadasha, antardasha, pratyantar] if p]
        relevant_planets = result.relevant_planets
        
        # Check intersection
        matching = set(dasha_planets) & set(relevant_planets)
        is_active = len(matching) > 0
        
        evidence = [Evidence(
            evidence_type=EvidenceType.DASHA_PERIOD,
            subject="Dasha Activation",
            value={"mahadasha": mahadasha, "antardasha": antardasha, "pratyantar": pratyantar},
            expected="At least one relevant planet in Dasha",
            actual={"relevant_planets": relevant_planets, "dasha_planets": dasha_planets, "matching": list(matching)},
            source="DynamicState",
            significance=f"Dasha: {'-'.join(dasha_planets)} | Relevant: {relevant_planets} | Match: {list(matching)} -> {'ACTIVE' if is_active else 'INACTIVE'}"
        )]
        
        return is_active, evidence


class DashaActivationEvaluator:
    """Evaluates activation based on specific Dasha requirements"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        activation_rule: ActivationRule,
        params: Dict[str, Any] = None
    ) -> tuple[bool, List[Evidence]]:
        """
        Params:
        - required_level: "mahadasha" | "antardasha" | "pratyantar" | "sookshma" | "prana"
        - required_planets: list of planet names that must be in Dasha
        - any_of: true if any required planet, false if all required
        """
        params = params or {}
        required_level = params.get("required_level", "antardasha")
        required_planets = params.get("required_planets", [])
        any_of = params.get("any_of", True)
        
        if not required_planets:
            required_planets = result.relevant_planets
        
        hierarchy = context.get_dasha_hierarchy()
        level_map = {"mahadasha": 0, "antardasha": 1, "pratyantar": 2, "sookshma": 3, "prana": 4}
        level_idx = level_map.get(required_level, 1)
        
        dasha_planet = hierarchy[level_idx] if len(hierarchy) > level_idx else None
        
        if any_of:
            is_active = dasha_planet in required_planets
        else:
            is_active = all(p in hierarchy[:level_idx+1] for p in required_planets)
        
        evidence = [Evidence(
            evidence_type=EvidenceType.DASHA_PERIOD,
            subject=f"Dasha Activation ({required_level})",
            value=dasha_planet,
            expected=f"One of {required_planets}" if any_of else f"All of {required_planets}",
            actual={"current": dasha_planet, "hierarchy": hierarchy[:level_idx+1]},
            source="DynamicState",
            significance=f"{required_level.title()}: {dasha_planet} | Required: {required_planets} ({'any' if any_of else 'all'}) -> {'ACTIVE' if is_active else 'INACTIVE'}"
        )]
        
        return is_active, evidence


class TransitActivationEvaluator:
    """Evaluates activation based on transit conditions"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        activation_rule: ActivationRule,
        params: Dict[str, Any] = None
    ) -> tuple[bool, List[Evidence]]:
        """
        Params:
        - transit_planet: planet to check
        - natal_planet: natal planet to aspect
        - aspect_type: "conjunction" | "opposition" | "trine" | "square" | "sextile"
        - orb: degree orb
        """
        params = params or {}
        transit_planet = params.get("transit_planet")
        natal_planet = params.get("natal_planet")
        aspect_type = params.get("aspect_type", "conjunction")
        orb = params.get("orb", 1.0)
        
        if not transit_planet or not natal_planet:
            return False, [Evidence(
                evidence_type=EvidenceType.TRANSIT,
                subject="Transit Activation",
                value=None,
                expected="transit_planet and natal_planet params",
                actual="Missing parameters",
                source="RuleDefinition"
            )]
        
        # Get transit position
        transit_sign = context.get_transit_planet_sign(transit_planet)
        transit_house = context.get_transit_planet_house(transit_planet)
        
        if not transit_sign or not transit_house:
            return False, [Evidence(
                evidence_type=EvidenceType.TRANSIT,
                subject=f"Transit {transit_planet}",
                value=None,
                expected="Valid transit position",
                actual="Transit data unavailable",
                source="DynamicState"
            )]
        
        # Get natal position
        natal_sign = context.get_planet_sign(natal_planet)
        natal_house = context.get_planet_house(natal_planet)
        
        if not natal_sign or not natal_house:
            return False, [Evidence(
                evidence_type=EvidenceType.TRANSIT,
                subject=f"Natal {natal_planet}",
                value=None,
                expected="Valid natal position",
                actual="Natal data unavailable",
                source="ChartFacts"
            )]
        
        # Simple house-based aspect check
        house_diff = (transit_house - natal_house) % 12
        aspect_map = {
            "conjunction": [0],
            "opposition": [6],
            "trine": [4, 8],
            "square": [3, 9],
            "sextile": [2, 10]
        }
        
        required_diffs = aspect_map.get(aspect_type, [0])
        is_active = house_diff in required_diffs
        
        evidence = [Evidence(
            evidence_type=EvidenceType.TRANSIT,
            subject=f"Transit {transit_planet} {aspect_type} Natal {natal_planet}",
            value={"transit_house": transit_house, "natal_house": natal_house, "diff": house_diff},
            expected=f"House difference in {required_diffs}",
            actual={"diff": house_diff, "match": is_active},
            source="DynamicState",
            significance=f"Transit {transit_planet} in house {transit_house}, Natal {natal_planet} in house {natal_house}, diff={house_diff} ({aspect_type}) -> {'ACTIVE' if is_active else 'INACTIVE'}"
        )]
        
        return is_active, evidence


class PanchangaActivationEvaluator:
    """Evaluates activation based on Panchanga factors"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        activation_rule: ActivationRule,
        params: Dict[str, Any] = None
    ) -> tuple[bool, List[Evidence]]:
        """
        Params:
        - required_tithi: list of tithi names
        - required_nakshatra: list of nakshatra names
        - required_yoga: list of yoga names
        - required_paksha: "shukla" | "krishna"
        - required_day: boolean (True=day, False=night)
        """
        params = params or {}
        
        checks = []
        details = {}
        
        # Tithi check
        if "required_tithi" in params:
            required = params["required_tithi"]
            if isinstance(required, str):
                required = [required]
            current = context.get_tithi()
            match = current in required if current else False
            checks.append(match)
            details["tithi"] = {"current": current, "required": required, "match": match}
        
        # Nakshatra check
        if "required_nakshatra" in params:
            required = params["required_nakshatra"]
            if isinstance(required, str):
                required = [required]
            current = context.get_nakshatra()
            match = current in required if current else False
            checks.append(match)
            details["nakshatra"] = {"current": current, "required": required, "match": match}
        
        # Yoga check
        if "required_yoga" in params:
            required = params["required_yoga"]
            if isinstance(required, str):
                required = [required]
            current = context.get_yoga()
            match = current in required if current else False
            checks.append(match)
            details["yoga"] = {"current": current, "required": required, "match": match}
        
        # Paksha check
        if "required_paksha" in params:
            required = params["required_paksha"]
            current = context.get_paksha()
            match = current == required if current else False
            checks.append(match)
            details["paksha"] = {"current": current, "required": required, "match": match}
        
        # Day/Night check
        if "required_day" in params:
            required = params["required_day"]
            current = context.is_day()
            match = current == required if current is not None else False
            checks.append(match)
            details["day"] = {"current": current, "required": required, "match": match}
        
        is_active = all(checks) if checks else False
        
        evidence = [Evidence(
            evidence_type=EvidenceType.PANCHANGA,
            subject="Panchanga Activation",
            value=details,
            expected="All required Panchanga factors match",
            actual={k: v["match"] for k, v in details.items()},
            source="DynamicState",
            significance=f"Panchanga: {details} -> {'ACTIVE' if is_active else 'INACTIVE'}"
        )]
        
        return is_active, evidence


class CombinedActivationEvaluator:
    """Combines multiple activation evaluators with AND/OR logic"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        activation_rule: ActivationRule,
        params: Dict[str, Any] = None
    ) -> tuple[bool, List[Evidence]]:
        """
        Params:
        - evaluators: list of {type: "...", params: {...}}
        - logic: "AND" | "OR"
        """
        params = params or {}
        evaluators = params.get("evaluators", [])
        logic = params.get("logic", "AND")
        
        if not evaluators:
            return False, [Evidence(
                evidence_type=EvidenceType.CUSTOM,
                subject="Combined Activation",
                value=None,
                expected="List of evaluators",
                actual="Empty evaluators list",
                source="RuleDefinition"
            )]
        
        evaluator_map = {
            "dasha": DashaActivationEvaluator,
            "transit": TransitActivationEvaluator,
            "panchanga": PanchangaActivationEvaluator,
            "default": DefaultActivationEvaluator,
        }
        
        results = []
        all_evidence = []
        
        for ev in evaluators:
            ev_type = ev.get("type", "default")
            ev_params = ev.get("params", {})
            evaluator_class = evaluator_map.get(ev_type, DefaultActivationEvaluator)
            
            passed, evidence = evaluator_class.evaluate(context, result, activation_rule, ev_params)
            results.append(passed)
            all_evidence.extend(evidence)
        
        if logic == "AND":
            is_active = all(results)
        else:
            is_active = any(results)
        
        summary_evidence = Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Combined Activation",
            value={"logic": logic, "results": results},
            expected=f"All true ({logic})" if logic == "AND" else f"At least one true ({logic})",
            actual={"individual_results": results, "final": is_active},
            source="CombinedActivationEvaluator",
            significance=f"Combined activation ({logic}): {results} -> {'ACTIVE' if is_active else 'INACTIVE'}"
        )
        all_evidence.append(summary_evidence)
        
        return is_active, all_evidence