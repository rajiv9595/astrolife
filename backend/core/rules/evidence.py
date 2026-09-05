"""
Evidence System — Astrolife V2 Phase 5A

Structured evidence generation and formatting for rule results.
Every rule detection must explain exactly why it fired with specific facts.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .models import Evidence
from .enums import EvidenceType
from .context import RuleContext


@dataclass
class EvidenceBuilder:
    """Helper to build structured evidence from context facts"""
    context: RuleContext
    evidence_list: List[Evidence] = field(default_factory=list)
    
    def add(self, evidence: Evidence) -> EvidenceBuilder:
        self.evidence_list.append(evidence)
        return self
    
    def planet_in_sign(self, planet: str, expected_sign: str = None) -> EvidenceBuilder:
        actual_sign = self.context.get_planet_sign(planet)
        if actual_sign:
            passed = expected_sign is None or actual_sign == expected_sign
            self.evidence_list.append(Evidence(
                evidence_type=EvidenceType.PLANET_IN_SIGN,
                subject=planet,
                value=actual_sign,
                expected=expected_sign,
                actual=actual_sign,
                source="ChartFacts",
                significance=f"{planet} in {actual_sign}" + (f" (expected {expected_sign})" if expected_sign else "")
            ))
        return self
    
    def planet_in_house(self, planet: str, expected_house: int = None) -> EvidenceBuilder:
        actual_house = self.context.get_planet_house(planet)
        if actual_house:
            passed = expected_house is None or actual_house == expected_house
            self.evidence_list.append(Evidence(
                evidence_type=EvidenceType.PLANET_IN_HOUSE,
                subject=planet,
                value=actual_house,
                expected=expected_house,
                actual=actual_house,
                source="ChartFacts",
                significance=f"{planet} in house {actual_house}" + (f" (expected {expected_house})" if expected_house else "")
            ))
        return self
    
    def planet_dignity(self, planet: str) -> EvidenceBuilder:
        dignity = self.context.get_dignity_category(planet)
        if dignity:
            self.evidence_list.append(Evidence(
                evidence_type=EvidenceType.PLANET_DIGNITY,
                subject=planet,
                value=dignity,
                expected=None,
                actual=dignity,
                source="StrengthReport",
                significance=f"{planet} dignity: {dignity}"
            ))
        return self
    
    def planet_strength(self, planet: str) -> EvidenceBuilder:
        ratio = self.context.get_shadbala_ratio(planet)
        status = self.context.get_shadbala_status(planet)
        if ratio is not None:
            self.evidence_list.append(Evidence(
                evidence_type=EvidenceType.PLANET_STRENGTH,
                subject=planet,
                value=ratio,
                expected=">= 1.0",
                actual=ratio,
                source="StrengthReport",
                significance=f"{planet} Shadbala ratio: {ratio:.3f} ({status})"
            ))
        return self
    
    def house_lord_position(self, house: int) -> EvidenceBuilder:
        lord = self.context.get_house_lord(house)
        if lord:
            lord_house = self.context.get_planet_house(lord)
            if lord_house:
                self.evidence_list.append(Evidence(
                    evidence_type=EvidenceType.HOUSE_LORD_POSITION,
                    subject=f"Lord of house {house}",
                    value=f"{lord} in house {lord_house}",
                    expected=None,
                    actual=f"{lord} in house {lord_house}",
                    source="ChartFacts",
                    significance=f"Lord of {house} ({lord}) placed in house {lord_house}"
                ))
        return self
    
    def lordship_relationship(self, house1: int, house2: int) -> EvidenceBuilder:
        lord1 = self.context.get_house_lord(house1)
        lord2 = self.context.get_house_lord(house2)
        if lord1 and lord2:
            connected = self.context.are_lords_mutually_connected(house1, house2)
            self.evidence_list.append(Evidence(
                evidence_type=EvidenceType.LORDSHIP_RELATIONSHIP,
                subject=f"Lords of {house1} and {house2}",
                value="Connected" if connected else "Not connected",
                expected="Mutual connection",
                actual="Connected" if connected else "No connection",
                source="ChartFacts",
                significance=f"Lords of {house1} ({lord1}) and {house2} ({lord2}) {'are' if connected else 'are not'} mutually connected"
            ))
        return self
    
    def conjunction(self, planet1: str, planet2: str) -> EvidenceBuilder:
        conjunct = self.context.are_conjunct(planet1, planet2)
        self.evidence_list.append(Evidence(
            evidence_type=EvidenceType.CONJUNCTION,
            subject=f"{planet1}-{planet2}",
            value="Conjunct" if conjunct else "Not conjunct",
            expected="Conjunction",
            actual="Conjunct" if conjunct else "Separate",
            source="ChartFacts",
            significance=f"{planet1} {'conjunct' if conjunct else 'not conjunct'} {planet2}"
        ))
        return self
    
    def aspect(self, from_planet: str, to_planet: str) -> EvidenceBuilder:
        aspects = self.context.get_planet_aspecting_planet(from_planet, to_planet)
        self.evidence_list.append(Evidence(
            evidence_type=EvidenceType.ASPECT,
            subject=f"{from_planet} aspects {to_planet}",
            value="Aspecting" if aspects else "Not aspecting",
            expected="Parashari aspect",
            actual="Aspecting" if aspects else "No aspect",
            source="ChartFacts",
            significance=f"{from_planet} {'aspects' if aspects else 'does not aspect'} {to_planet}"
        ))
        return self
    
    def exchange(self, planet1: str, planet2: str) -> EvidenceBuilder:
        exchanged = self.context.is_exchange(planet1, planet2)
        p1_sign = self.context.get_planet_sign(planet1)
        p2_sign = self.context.get_planet_sign(planet2)
        self.evidence_list.append(Evidence(
            evidence_type=EvidenceType.EXCHANGE,
            subject=f"{planet1}-{planet2}",
            value="Exchange" if exchanged else "No exchange",
            expected="Parivartana",
            actual=f"{planet1} in {p1_sign}, {planet2} in {p2_sign}",
            source="ChartFacts",
            significance=f"{planet1} and {planet2} {'are in Parivartana' if exchanged else 'are not in Parivartana'}"
        ))
        return self
    
    def yogakaraka(self, planet: str) -> EvidenceBuilder:
        is_yk = self.context.is_yogakaraka(planet)
        self.evidence_list.append(Evidence(
            evidence_type=EvidenceType.YOGAKARAKA,
            subject=planet,
            value="Yogakaraka" if is_yk else "Not Yogakaraka",
            expected="Rules Kendra and Trikona",
            actual="Yes" if is_yk else "No",
            source="StrengthReport",
            significance=f"{planet} {'is' if is_yk else 'is not'} Yogakaraka"
        ))
        return self
    
    def functional_nature(self, planet: str) -> EvidenceBuilder:
        nature = self.context.get_functional_nature(planet)
        if nature:
            self.evidence_list.append(Evidence(
                evidence_type=EvidenceType.FUNCTIONAL_NATURE,
                subject=planet,
                value=nature,
                expected=None,
                actual=nature,
                source="StrengthReport",
                significance=f"{planet} functional nature: {nature}"
            ))
        return self
    
    def kendra_trikona(self, planet: str) -> EvidenceBuilder:
        in_kendra = self.context.get_planet_house(planet) in (1, 4, 7, 10) if self.context.get_planet_house(planet) else False
        in_trikona = self.context.get_planet_house(planet) in (1, 5, 9) if self.context.get_planet_house(planet) else False
        self.evidence_list.append(Evidence(
            evidence_type=EvidenceType.KENDRA_TRIKONA,
            subject=planet,
            value={"kendra": in_kendra, "trikona": in_trikona, "house": self.context.get_planet_house(planet)},
            expected="Kendra or Trikona",
            actual=f"Kendra: {in_kendra}, Trikona: {in_trikona}",
            source="ChartFacts",
            significance=f"{planet} in house {self.context.get_planet_house(planet)}: Kendra={in_kendra}, Trikona={in_trikona}"
        ))
        return self
    
    def varga_position(self, planet: str, varga_num: int) -> EvidenceBuilder:
        sign = self.context.get_varga_sign(planet, varga_num)
        if sign:
            self.evidence_list.append(Evidence(
                evidence_type=EvidenceType.VARGA_POSITION,
                subject=f"{planet} in D{varga_num}",
                value=sign,
                expected=None,
                actual=sign,
                source="VargaFacts",
                significance=f"{planet} in {sign} in D{varga_num}"
            ))
        return self
    
    def dasha_period(self) -> EvidenceBuilder:
        mahadasha = self.context.get_current_mahadasha()
        antardasha = self.context.get_current_antardasha()
        hierarchy = self.context.get_dasha_hierarchy()
        self.evidence_list.append(Evidence(
            evidence_type=EvidenceType.DASHA_PERIOD,
            subject="Current Dasha",
            value={"mahadasha": mahadasha, "antardasha": antardasha, "hierarchy": hierarchy},
            expected=None,
            actual=f"{mahadasha}-{antardasha}",
            source="DynamicState",
            significance=f"Current Dasha: {mahadasha}-{antardasha} (hierarchy: {'-'.join(hierarchy)})"
        ))
        return self
    
    def build(self) -> List[Evidence]:
        return self.evidence_list


def format_evidence_for_display(evidence: List[Evidence]) -> str:
    """Format evidence list for human-readable display"""
    if not evidence:
        return "No evidence"
    
    lines = []
    for i, e in enumerate(evidence, 1):
        lines.append(f"  {i}. [{e.evidence_type.value}] {e.subject}")
        lines.append(f"     Value: {e.value}")
        if e.expected is not None:
            lines.append(f"     Expected: {e.expected}")
        if e.actual is not None:
            lines.append(f"     Actual: {e.actual}")
        lines.append(f"     Source: {e.source}")
        if e.significance:
            lines.append(f"     Significance: {e.significance}")
        lines.append("")
    
    return "\n".join(lines).strip()


def format_evidence_for_json(evidence: List[Evidence]) -> List[Dict[str, Any]]:
    """Convert evidence to JSON-serializable format"""
    return [
        {
            "evidence_type": e.evidence_type.value,
            "subject": e.subject,
            "value": e.value,
            "expected": e.expected,
            "actual": e.actual,
            "source": e.source,
            "significance": e.significance,
            "details": e.details
        }
        for e in evidence
    ]


def group_evidence_by_type(evidence: List[Evidence]) -> Dict[EvidenceType, List[Evidence]]:
    """Group evidence by type for analysis"""
    grouped: Dict[EvidenceType, List[Evidence]] = {}
    for e in evidence:
        if e.evidence_type not in grouped:
            grouped[e.evidence_type] = []
        grouped[e.evidence_type].append(e)
    return grouped


def count_evidence_by_source(evidence: List[Evidence]) -> Dict[str, int]:
    """Count evidence by source"""
    counts: Dict[str, int] = {}
    for e in evidence:
        counts[e.source] = counts.get(e.source, 0) + 1
    return counts


class EvidenceValidator:
    """Validate evidence quality and completeness"""
    
    @staticmethod
    def validate(evidence: List[Evidence], required_types: List[EvidenceType] = None) -> List[str]:
        """Validate evidence list"""
        warnings = []
        
        if not evidence:
            warnings.append("No evidence provided")
            return warnings
        
        # Check for required types
        if required_types:
            present_types = {e.evidence_type for e in evidence}
            missing = [t for t in required_types if t not in present_types]
            if missing:
                warnings.append(f"Missing required evidence types: {[t.value for t in missing]}")
        
        # Check for evidence with missing significance
        for e in evidence:
            if not e.significance or not e.significance.strip():
                warnings.append(f"Evidence for {e.subject} ({e.evidence_type.value}) has no significance description")
        
        # Check for evidence with no source
        for e in evidence:
            if not e.source or not e.source.strip():
                warnings.append(f"Evidence for {e.subject} ({e.evidence_type.value}) has no source")
        
        return warnings
    
    @staticmethod
    def get_evidence_summary(evidence: List[Evidence]) -> Dict[str, Any]:
        """Get summary statistics for evidence"""
        if not evidence:
            return {"total": 0}
        
        by_type = group_evidence_by_type(evidence)
        by_source = count_evidence_by_source(evidence)
        
        with_significance = sum(1 for e in evidence if e.significance)
        with_expected = sum(1 for e in evidence if e.expected is not None)
        
        return {
            "total": len(evidence),
            "by_type": {k.value: len(v) for k, v in by_type.items()},
            "by_source": by_source,
            "with_significance": with_significance,
            "with_expected": with_expected,
            "completeness": {
                "significance_pct": round(with_significance / len(evidence) * 100, 1),
                "expected_pct": round(with_expected / len(evidence) * 100, 1)
            }
        }