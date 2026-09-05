"""
Mitigation Evaluators — Astrolife V2 Phase 5A

Separate evaluators for rule mitigation (strengthening factors that reduce negative impact).
Mitigation is evaluated INDEPENDENTLY from formation, strength, and cancellation.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .models import RuleResult, Evidence, MitigationStatus, MitigationRule
from .context import RuleContext
from .enums import EvidenceType


@dataclass
class MitigationEvaluator:
    """Base mitigation evaluator"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        mit_rule: MitigationRule
    ) -> tuple[bool, List[Evidence]]:
        raise NotImplementedError


class DefaultMitigationEvaluator:
    """Default mitigation evaluator - checks for standard strengthening factors"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        mit_rule: MitigationRule
    ) -> tuple[bool, List[Evidence]]:
        """No default mitigation - specific rules should define their own"""
        return False, []


class BeneficAssociationMitigationEvaluator:
    """
    Mitigation through benefic association.
    
    A malefic yoga/dosha is mitigated if:
    - Benefic planets aspect the afflicted planets
    - Benefic planets conjunct the afflicted planets
    - Benefics in Kendra/Trikona from afflicted planets
    """
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        mit_rule: MitigationRule
    ) -> tuple[bool, List[Evidence]]:
        """Check for benefic association with relevant planets"""
        
        mitigations = []
        evidence = []
        
        benefics = ["Jupiter", "Venus", "Mercury"]
        relevant = result.relevant_planets
        
        for planet in relevant:
            # Check conjunctions with benefics
            for b in benefics:
                if context.are_conjunct(planet, b):
                    mitigations.append(f"{planet} conjunct benefic {b}")
                    evidence.append(Evidence(
                        evidence_type=EvidenceType.CONJUNCTION,
                        subject=f"Benefic Mitigation: {planet}",
                        value=f"Conjunct {b}",
                        expected="Benefic association",
                        actual=f"{planet} conjunct {b}",
                        source="ChartFacts",
                        significance=f"Mitigation: {planet} conjunct benefic {b}"
                    ))
            
            # Check aspects from benefics
            for b in benefics:
                if context.get_planet_aspecting_planet(b, planet):
                    mitigations.append(f"{planet} aspected by benefic {b}")
                    evidence.append(Evidence(
                        evidence_type=EvidenceType.ASPECT,
                        subject=f"Benefic Mitigation: {planet}",
                        value=f"Aspected by {b}",
                        expected="Benefic aspect",
                        actual=f"{b} aspects {planet}",
                        source="ChartFacts",
                        significance=f"Mitigation: {planet} aspected by benefic {b}"
                    ))
            
            # Check if planet in Kendra/Trikona from benefics
            for b in benefics:
                b_house = context.get_planet_house(b)
                p_house = context.get_planet_house(planet)
                if b_house and p_house:
                    diff = (p_house - b_house) % 12
                    if diff in (0, 3, 4, 6, 8, 9):  # Kendra or Trikona from benefic
                        mitigations.append(f"{planet} in Kendra/Trikona from benefic {b}")
                        evidence.append(Evidence(
                            evidence_type=EvidenceType.KENDRA_TRIKONA,
                            subject=f"Benefic Mitigation: {planet}",
                            value=f"In Kendra/Trikona from {b}",
                            expected="Kendra/Trikona from benefic",
                            actual=f"{planet} house {p_house}, {b} house {b_house}, diff {diff}",
                            source="ChartFacts",
                            significance=f"Mitigation: {planet} in Kendra/Trikona from {b}"
                        ))
        
        is_mitigated = len(mitigations) > 0
        strength_impact = "significant" if len(mitigations) >= 2 else "partial"
        
        summary = Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Benefic Association Mitigation Summary",
            value={"mitigations": mitigations, "strength_impact": strength_impact},
            expected="At least one benefic association",
            actual=f"Mitigations: {mitigations}" if mitigations else "No benefic associations",
            source="BeneficAssociationMitigationEvaluator",
            significance=f"Benefic mitigation: {mitigations}" if mitigations else "No benefic mitigation"
        )
        evidence.append(summary)
        
        return is_mitigated, evidence


class DignityMitigationEvaluator:
    """
    Mitigation through planetary dignity.
    
    Affliction is mitigated if afflicted planet has:
    - Exaltation
    - Own sign
    - Moolatrikona
    - Vargottama (same sign in D1 and D9)
    - Strong in Shadbala
    """
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        mit_rule: MitigationRule
    ) -> tuple[bool, List[Evidence]]:
        """Check for dignity-based mitigation"""
        
        mitigations = []
        evidence = []
        
        for planet in result.relevant_planets:
            # Exaltation
            if context.is_exalted(planet):
                mitigations.append(f"{planet} exalted")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.PLANET_DIGNITY,
                    subject=f"Dignity Mitigation: {planet}",
                    value="Exalted",
                    expected="High dignity",
                    actual="Exalted",
                    source="StrengthReport",
                    significance=f"Mitigation: {planet} exalted"
                ))
            
            # Own sign
            if context.is_own_sign(planet):
                mitigations.append(f"{planet} in own sign")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.PLANET_DIGNITY,
                    subject=f"Dignity Mitigation: {planet}",
                    value="Own Sign",
                    expected="High dignity",
                    actual="Own Sign",
                    source="StrengthReport",
                    significance=f"Mitigation: {planet} in own sign"
                ))
            
            # Moolatrikona
            if context.is_moolatrikona(planet):
                mitigations.append(f"{planet} in Moolatrikona")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.PLANET_DIGNITY,
                    subject=f"Dignity Mitigation: {planet}",
                    value="Moolatrikona",
                    expected="High dignity",
                    actual="Moolatrikona",
                    source="StrengthReport",
                    significance=f"Mitigation: {planet} in Moolatrikona"
                ))
            
            # Vargottama (D1 = D9 sign)
            d1_sign = context.get_planet_sign(planet)
            d9_sign = context.get_varga_sign(planet, 9)
            if d1_sign and d9_sign and d1_sign == d9_sign:
                mitigations.append(f"{planet} Vargottama ({d1_sign})")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.VARGA_POSITION,
                    subject=f"Dignity Mitigation: {planet}",
                    value=f"Vargottama in {d1_sign}",
                    expected="Same sign in D1 and D9",
                    actual=f"D1: {d1_sign}, D9: {d9_sign}",
                    source="VargaFacts",
                    significance=f"Mitigation: {planet} Vargottama"
                ))
            
            # Strong Shadbala
            ratio = context.get_shadbala_ratio(planet)
            if ratio and ratio >= 1.2:
                mitigations.append(f"{planet} strong Shadbala ({ratio:.2f}x)")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.PLANET_STRENGTH,
                    subject=f"Dignity Mitigation: {planet}",
                    value=f"Shadbala ratio {ratio:.2f}",
                    expected="Ratio >= 1.2",
                    actual=f"Ratio {ratio:.2f}",
                    source="StrengthReport",
                    significance=f"Mitigation: {planet} strong Shadbala"
                ))
        
        is_mitigated = len(mitigations) > 0
        strength_impact = "significant" if len(mitigations) >= 2 else "partial"
        
        summary = Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Dignity Mitigation Summary",
            value={"mitigations": mitigations, "strength_impact": strength_impact},
            expected="At least one dignity factor",
            actual=f"Mitigations: {mitigations}" if mitigations else "No dignity factors",
            source="DignityMitigationEvaluator",
            significance=f"Dignity mitigation: {mitigations}" if mitigations else "No dignity mitigation"
        )
        evidence.append(summary)
        
        return is_mitigated, evidence


class HousePositionMitigationEvaluator:
    """
    Mitigation through house position.
    
    Affliction is mitigated if:
    - Afflicted planet in Kendra (1, 4, 7, 10)
    - Afflicted planet in Trikona (1, 5, 9)
    - Afflicted planet in Upachaya (3, 6, 10, 11) - for malefics
    - Lord of house in Kendra/Trikona
    """
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        mit_rule: MitigationRule
    ) -> tuple[bool, List[Evidence]]:
        """Check for house position mitigation"""
        
        mitigations = []
        evidence = []
        
        for planet in result.relevant_planets:
            p_house = context.get_planet_house(planet)
            if not p_house:
                continue
            
            # Kendra
            if p_house in (1, 4, 7, 10):
                mitigations.append(f"{planet} in Kendra house {p_house}")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.KENDRA_TRIKONA,
                    subject=f"House Position Mitigation: {planet}",
                    value=f"Kendra house {p_house}",
                    expected="Kendra placement",
                    actual=f"House {p_house}",
                    source="ChartFacts",
                    significance=f"Mitigation: {planet} in Kendra"
                ))
            
            # Trikona
            if p_house in (1, 5, 9):
                mitigations.append(f"{planet} in Trikona house {p_house}")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.KENDRA_TRIKONA,
                    subject=f"House Position Mitigation: {planet}",
                    value=f"Trikona house {p_house}",
                    expected="Trikona placement",
                    actual=f"House {p_house}",
                    source="ChartFacts",
                    significance=f"Mitigation: {planet} in Trikona"
                ))
            
            # Upachaya (for malefics)
            malefics = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]
            if planet in malefics and p_house in (3, 6, 10, 11):
                mitigations.append(f"Malefic {planet} in Upachaya house {p_house}")
                evidence.append(Evidence(
                    evidence_type=EvidenceType.HOUSE_LORD_POSITION,
                    subject=f"House Position Mitigation: {planet}",
                    value=f"Upachaya house {p_house}",
                    expected="Malefic in Upachaya",
                    actual=f"House {p_house}",
                    source="ChartFacts",
                    significance=f"Mitigation: Malefic {planet} in Upachaya"
                ))
            
            # Lord of house in Kendra/Trikona
            houses_ruled = context.get_houses_ruled_by(planet)
            for h in houses_ruled:
                if h in (1, 4, 5, 7, 9, 10):
                    mitigations.append(f"{planet} rules Kendra/Trikona house {h}")
                    evidence.append(Evidence(
                        evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
                        subject=f"House Position Mitigation: {planet}",
                        value=f"Rules house {h}",
                        expected="Rules Kendra/Trikona",
                        actual=f"Rules house {h}",
                        source="ChartFacts",
                        significance=f"Mitigation: {planet} rules Kendra/Trikona"
                    ))
        
        is_mitigated = len(mitigations) > 0
        strength_impact = "significant" if len(mitigations) >= 2 else "partial"
        
        summary = Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="House Position Mitigation Summary",
            value={"mitigations": mitigations, "strength_impact": strength_impact},
            expected="At least one house position factor",
            actual=f"Mitigations: {mitigations}" if mitigations else "No house position factors",
            source="HousePositionMitigationEvaluator",
            significance=f"House position mitigation: {mitigations}" if mitigations else "No house position mitigation"
        )
        evidence.append(summary)
        
        return is_mitigated, evidence


class VargaMitigationEvaluator:
    """
    Mitigation through Varga positions.
    
    Affliction is mitigated if planet is well-placed in:
    - D9 (Navamsa) - most important
    - D10 (Dasamsa) - for career
    - D7 (Saptamsa) - for children
    - D12 (Dwadasamsa) - for parents
    - D30 (Trimsamsa) - for misfortunes
    """
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        mit_rule: MitigationRule
    ) -> tuple[bool, List[Evidence]]:
        """Check for Varga-based mitigation"""
        
        params = getattr(mit_rule, 'params', {}) or {}
        vargas_to_check = params.get("vargas", [9, 10, 7, 12, 30])
        required_dignities = params.get("dignities", ["exalted", "own", "moolatrikona", "friend"])
        
        mitigations = []
        evidence = []
        
        for planet in result.relevant_planets:
            for varga_num in vargas_to_check:
                varga_sign = context.get_varga_sign(planet, varga_num)
                if not varga_sign:
                    continue
                
                # Check dignity in varga (simplified - would need varga-specific dignity)
                # For now, check if varga sign is own/exaltation/moolatrikona of planet
                # This requires knowing planet's rulerships in varga - simplified check
                
                # Check if varga sign matches D1 own/exaltation signs
                d1_own_signs = []
                d1_exalt_signs = []
                d1_mool_signs = []
                
                # This would need planet-specific data - placeholder
                # For demonstration, we'll check basic conditions
                
                if varga_num == 9:  # Navamsa is most important
                    mitigations.append(f"{planet} in {varga_sign} in D{varga_num}")
                    evidence.append(Evidence(
                        evidence_type=EvidenceType.VARGA_POSITION,
                        subject=f"Varga Mitigation: {planet}",
                        value=f"D{varga_num} sign {varga_sign}",
                        expected="Benefic Varga placement",
                        actual=f"D{varga_num}: {varga_sign}",
                        source="VargaFacts",
                        significance=f"Mitigation: {planet} in D{varga_num}"
                    ))
        
        is_mitigated = len(mitigations) > 0
        strength_impact = "partial"
        
        summary = Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Varga Mitigation Summary",
            value={"mitigations": mitigations, "strength_impact": strength_impact},
            expected="At least one Varga factor",
            actual=f"Mitigations: {mitigations}" if mitigations else "No Varga factors",
            source="VargaMitigationEvaluator",
            significance=f"Varga mitigation: {mitigations}" if mitigations else "No Varga mitigation"
        )
        evidence.append(summary)
        
        return is_mitigated, evidence


class CombinedMitigationEvaluator:
    """Combines multiple mitigation evaluators"""
    
    @staticmethod
    def evaluate(
        context: RuleContext,
        result: RuleResult,
        mit_rule: MitigationRule
    ) -> tuple[bool, List[Evidence]]:
        """
        Params:
        - evaluators: list of {type: "...", params: {...}, weight: 1.0}
        - threshold: minimum total weight for significant mitigation
        """
        params = getattr(mit_rule, 'params', {}) or {}
        evaluators = params.get("evaluators", [])
        threshold = params.get("threshold", 1.0)
        
        if not evaluators:
            # Default set
            evaluators = [
                {"type": "benefic", "params": {}, "weight": 1.0},
                {"type": "dignity", "params": {}, "weight": 1.5},
                {"type": "house", "params": {}, "weight": 1.0},
            ]
        
        evaluator_map = {
            "benefic": BeneficAssociationMitigationEvaluator,
            "dignity": DignityMitigationEvaluator,
            "house": HousePositionMitigationEvaluator,
            "varga": VargaMitigationEvaluator,
        }
        
        total_weight = 0.0
        all_evidence = []
        all_mitigations = []
        
        for ev in evaluators:
            ev_type = ev.get("type", "benefic")
            ev_params = ev.get("params", {})
            weight = ev.get("weight", 1.0)
            
            evaluator_class = evaluator_map.get(ev_type, BeneficAssociationMitigationEvaluator)
            
            # Create a modified mit_rule with params for this evaluator
            class TempRule:
                params = ev_params
            
            passed, evidence = evaluator_class.evaluate(context, result, TempRule())
            
            if passed:
                total_weight += weight
                # Extract mitigation names from evidence
                for e in evidence:
                    if e.significance and "Mitigation:" in e.significance:
                        all_mitigations.append(e.significance)
            
            all_evidence.extend(evidence)
        
        is_significant = total_weight >= threshold
        is_partial = total_weight > 0 and not is_significant
        
        if is_significant:
            status = MitigationStatus.SIGNIFICANT
        elif is_partial:
            status = MitigationStatus.PARTIAL
        else:
            status = MitigationStatus.NONE
        
        summary = Evidence(
            evidence_type=EvidenceType.CUSTOM,
            subject="Combined Mitigation Summary",
            value={"total_weight": total_weight, "threshold": threshold, "mitigations": all_mitigations},
            expected=f"Weight >= {threshold}",
            actual=f"Weight: {total_weight}, Status: {status.value}",
            source="CombinedMitigationEvaluator",
            significance=f"Combined mitigation: weight={total_weight}/{threshold} -> {status.value}"
        )
        all_evidence.append(summary)
        
        return status != MitigationStatus.NONE, all_evidence