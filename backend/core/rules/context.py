"""
Rule Context — Astrolife V2 Phase 5A

Provides deterministic, read-only access to canonical chart facts, vargas,
strength calculations, and dynamic state for rule evaluation.

NEVER calculates astronomy independently - only consumes pre-computed facts.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from functools import lru_cache

from core.calculation.models import ChartFacts, PlanetData, HouseData, SignPosition
from core.strength.models import StrengthReport, DignityResult, FunctionalStrengthResult, ShadbalaResult
from core.calculation.varga import VargaPosition, calculate_all_vargas
from core.calculation.dynamic import DynamicAstrologyState

from .enums import EvidenceType


@dataclass(frozen=True)
class PlanetPosition:
    """Immutable planet position snapshot"""
    name: str
    longitude: float
    latitude: float
    sign: str
    sign_num: int
    degree: float
    house: int
    nakshatra: str
    nakshatra_pada: int
    retrograde: bool
    speed: float


@dataclass(frozen=True)
class HouseInfo:
    """Immutable house information"""
    number: int
    sign: str
    sign_num: int
    lord: str


class RuleContext:
    """
    Deterministic rule evaluation context.
    
    Consumes canonical ChartFacts, StrengthReport, VargaFacts, DynamicAstrologyState.
    Provides convenient accessors for rule conditions.
    NO astronomy calculations - only data access.
    """
    
    def __init__(
        self,
        chart_facts: ChartFacts,
        strength_report: Optional[StrengthReport] = None,
        varga_facts: Optional[Dict[str, Any]] = None,
        dynamic_state: Optional[DynamicAstrologyState] = None,
        evaluation_datetime: Optional[Any] = None
    ):
        self._chart_facts = chart_facts
        self._strength_report = strength_report
        self._varga_facts = varga_facts or {}
        self._dynamic_state = dynamic_state
        self._evaluation_datetime = evaluation_datetime
        
        # Pre-compute cached lookups
        self._planet_cache: Dict[str, PlanetPosition] = {}
        self._house_cache: Dict[int, HouseInfo] = {}
        self._sign_lords = self._build_sign_lords()
        self._planet_houses: Dict[str, int] = {}
        self._house_lords: Dict[int, str] = {}
        self._planet_dignities: Dict[str, DignityResult] = {}
        self._planet_functional: Dict[str, FunctionalStrengthResult] = {}
        self._planet_shadbala: Dict[str, ShadbalaResult] = {}
        self._varga_positions: Dict[str, Dict[str, VargaPosition]] = {}
        
        self._initialize_caches()
    
    def _build_sign_lords(self) -> Dict[str, str]:
        return {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
            "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
            "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
    
    def _initialize_caches(self):
        """Build all cached lookups from canonical data"""
        # Planets
        for name, pdata in self._chart_facts.planets.items():
            self._planet_cache[name] = PlanetPosition(
                name=name,
                longitude=float(pdata.longitude.sidereal),
                latitude=float(pdata.latitude),
                sign=pdata.sign.name,
                sign_num=pdata.sign.id,
                degree=float(pdata.sign.degree),
                house=pdata.house,
                nakshatra=pdata.nakshatra.name,
                nakshatra_pada=pdata.nakshatra.pada,
                retrograde=pdata.retrograde,
                speed=float(pdata.speed)
            )
            self._planet_houses[name] = pdata.house
        
        # Houses
        for num, hdata in self._chart_facts.houses.items():
            self._house_cache[num] = HouseInfo(
                number=num,
                sign=hdata.sign.name,
                sign_num=hdata.sign.id,
                lord=self._sign_lords.get(hdata.sign.name, "")
            )
            self._house_lords[num] = self._sign_lords.get(hdata.sign.name, "")
        
        # Strength data
        if self._strength_report:
            for planet, dignity in self._strength_report.dignity.items():
                self._planet_dignities[planet] = dignity
            for planet, functional in self._strength_report.functional_strength.items():
                self._planet_functional[planet] = functional
            for planet, shadbala in self._strength_report.planets.items():
                self._planet_shadbala[planet] = shadbala
        
        # Vargas
        if self._varga_facts:
            self._varga_positions = self._varga_facts.get("planets", {})
    
    # ==================== Core Accessors ====================
    
    @property
    def chart_facts(self) -> ChartFacts:
        return self._chart_facts
    
    @property
    def strength_report(self) -> Optional[StrengthReport]:
        return self._strength_report
    
    @property
    def varga_facts(self) -> Dict[str, Any]:
        return self._varga_facts
    
    @property
    def dynamic_state(self) -> Optional[DynamicAstrologyState]:
        return self._dynamic_state
    
    @property
    def evaluation_datetime(self) -> Optional[Any]:
        return self._evaluation_datetime
    
    @property
    def ascendant_sign(self) -> str:
        return self._chart_facts.ascendant.sign.name
    
    @property
    def ascendant_longitude(self) -> float:
        return float(self._chart_facts.ascendant.longitude.sidereal)
    
    @property
    def moon_sign(self) -> str:
        moon = self._planet_cache.get("Moon")
        return moon.sign if moon else ""
    
    @property
    def sun_sign(self) -> str:
        sun = self._planet_cache.get("Sun")
        return sun.sign if sun else ""
    
    # ==================== Planet Access ====================
    
    def get_planet(self, name: str) -> Optional[PlanetPosition]:
        return self._planet_cache.get(name)
    
    def get_planet_longitude(self, name: str) -> Optional[float]:
        p = self._planet_cache.get(name)
        return p.longitude if p else None
    
    def get_planet_sign(self, name: str) -> Optional[str]:
        p = self._planet_cache.get(name)
        return p.sign if p else None
    
    def get_planet_sign_num(self, name: str) -> Optional[int]:
        p = self._planet_cache.get(name)
        return p.sign_num if p else None
    
    def get_planet_degree(self, name: str) -> Optional[float]:
        p = self._planet_cache.get(name)
        return p.degree if p else None
    
    def get_planet_house(self, name: str) -> Optional[int]:
        return self._planet_houses.get(name)
    
    def get_planet_nakshatra(self, name: str) -> Optional[str]:
        p = self._planet_cache.get(name)
        return p.nakshatra if p else None
    
    def get_planet_retrograde(self, name: str) -> Optional[bool]:
        p = self._planet_cache.get(name)
        return p.retrograde if p else None
    
    def get_planet_speed(self, name: str) -> Optional[float]:
        p = self._planet_cache.get(name)
        return p.speed if p else None
    
    def get_all_planets(self) -> List[PlanetPosition]:
        return list(self._planet_cache.values())
    
    def get_planets_in_sign(self, sign: str) -> List[str]:
        return [name for name, p in self._planet_cache.items() if p.sign == sign]
    
    def get_planets_in_house(self, house: int) -> List[str]:
        return [name for name, h in self._planet_houses.items() if h == house]
    
    def get_planets_in_kendra(self) -> List[str]:
        return [name for name, h in self._planet_houses.items() if h in (1, 4, 7, 10)]
    
    def get_planets_in_trikona(self) -> List[str]:
        return [name for name, h in self._planet_houses.items() if h in (1, 5, 9)]
    
    def get_planets_in_dusthana(self) -> List[str]:
        return [name for name, h in self._planet_houses.items() if h in (6, 8, 12)]
    
    # ==================== House Access ====================
    
    def get_house(self, number: int) -> Optional[HouseInfo]:
        return self._house_cache.get(number)
    
    def get_house_sign(self, number: int) -> Optional[str]:
        h = self._house_cache.get(number)
        return h.sign if h else None
    
    def get_house_lord(self, number: int) -> Optional[str]:
        return self._house_lords.get(number)
    
    def get_houses_ruled_by(self, planet: str) -> List[int]:
        return [num for num, lord in self._house_lords.items() if lord == planet]
    
    def get_lord_of_sign(self, sign: str) -> Optional[str]:
        return self._sign_lords.get(sign)
    
    # ==================== Dignity & Strength ====================
    
    def get_dignity(self, planet: str) -> Optional[DignityResult]:
        return self._planet_dignities.get(planet)
    
    def is_exalted(self, planet: str) -> bool:
        d = self._planet_dignities.get(planet)
        return d.is_exalted if d else False
    
    def is_debilitated(self, planet: str) -> bool:
        d = self._planet_dignities.get(planet)
        return d.is_debilitated if d else False
    
    def is_own_sign(self, planet: str) -> bool:
        d = self._planet_dignities.get(planet)
        return d.is_own_sign if d else False
    
    def is_moolatrikona(self, planet: str) -> bool:
        d = self._planet_dignities.get(planet)
        return d.is_moolatrikona if d else False
    
    def get_dignity_category(self, planet: str) -> Optional[str]:
        d = self._planet_dignities.get(planet)
        return d.dignity if d else None
    
    def get_functional_strength(self, planet: str) -> Optional[FunctionalStrengthResult]:
        return self._planet_functional.get(planet)
    
    def is_yogakaraka(self, planet: str) -> bool:
        f = self._planet_functional.get(planet)
        return f.yogakaraka if f else False
    
    def get_functional_nature(self, planet: str) -> Optional[str]:
        f = self._planet_functional.get(planet)
        return f.functional_nature if f else None
    
    def is_functional_benefic(self, planet: str) -> bool:
        nature = self.get_functional_nature(planet)
        return nature in ("YOGAKARAKA", "FUNCTIONAL_BENEFIC") if nature else False
    
    def is_functional_malefic(self, planet: str) -> bool:
        nature = self.get_functional_nature(planet)
        return nature in ("FUNCTIONAL_MALEFIC", "MARAKA") if nature else False
    
    def get_shadbala(self, planet: str) -> Optional[ShadbalaResult]:
        return self._planet_shadbala.get(planet)
    
    def get_shadbala_total_rupas(self, planet: str) -> Optional[float]:
        s = self._planet_shadbala.get(planet)
        return s.total_rupas if s else None
    
    def get_shadbala_ratio(self, planet: str) -> Optional[float]:
        s = self._planet_shadbala.get(planet)
        return s.ratio if s else None
    
    def get_shadbala_status(self, planet: str) -> Optional[str]:
        s = self._planet_shadbala.get(planet)
        return s.strength_status if s else None
    
    def is_strong_by_shadbala(self, planet: str, threshold: float = 1.0) -> bool:
        ratio = self.get_shadbala_ratio(planet)
        return ratio is not None and ratio >= threshold
    
    # ==================== Varga Access ====================
    
    def get_varga_position(self, planet: str, varga_num: int) -> Optional[VargaPosition]:
        planet_vargas = self._varga_positions.get(planet, {})
        return planet_vargas.get(f"D{varga_num}")
    
    def get_varga_sign(self, planet: str, varga_num: int) -> Optional[str]:
        pos = self.get_varga_position(planet, varga_num)
        return pos.sign if pos else None
    
    def get_varga_sign_num(self, planet: str, varga_num: int) -> Optional[int]:
        pos = self.get_varga_position(planet, varga_num)
        return pos.sign_num if pos else None
    
    def get_varga_degree(self, planet: str, varga_num: int) -> Optional[float]:
        pos = self.get_varga_position(planet, varga_num)
        return pos.degree if pos else None
    
    def is_planet_in_varga_sign(self, planet: str, varga_num: int, sign: str) -> bool:
        pos = self.get_varga_position(planet, varga_num)
        return pos.sign == sign if pos else False
    
    def get_planets_in_varga_sign(self, varga_num: int, sign: str) -> List[str]:
        return [
            name for name in self._planet_cache.keys()
            if self.is_planet_in_varga_sign(name, varga_num, sign)
        ]
    
    # ==================== Relationship Utilities ====================
    
    def are_conjunct(self, planet1: str, planet2: str, orb_degrees: float = 8.0) -> bool:
        p1 = self._planet_cache.get(planet1)
        p2 = self._planet_cache.get(planet2)
        if not p1 or not p2:
            return False
        diff = abs(p1.longitude - p2.longitude)
        diff = min(diff, 360.0 - diff)
        return diff <= orb_degrees
    
    def are_in_same_house(self, planet1: str, planet2: str) -> bool:
        h1 = self._planet_houses.get(planet1)
        h2 = self._planet_houses.get(planet2)
        return h1 is not None and h1 == h2
    
    def are_in_same_sign(self, planet1: str, planet2: str) -> bool:
        p1 = self._planet_cache.get(planet1)
        p2 = self._planet_cache.get(planet2)
        return p1 and p2 and p1.sign == p2.sign
    
    def get_house_from_planet(self, from_planet: str, target_house: int) -> Optional[int]:
        """Get house number that is target_house from from_planet's position"""
        from_house = self._planet_houses.get(from_planet)
        if not from_house:
            return None
        return ((from_house + target_house - 2) % 12) + 1
    
    def is_kendra_from(self, planet1: str, planet2: str) -> bool:
        h1 = self._planet_houses.get(planet1)
        h2 = self._planet_houses.get(planet2)
        if not h1 or not h2:
            return False
        diff = (h1 - h2) % 12
        return diff in (0, 3, 6, 9)
    
    def is_trikona_from(self, planet1: str, planet2: str) -> bool:
        h1 = self._planet_houses.get(planet1)
        h2 = self._planet_houses.get(planet2)
        if not h1 or not h2:
            return False
        diff = (h1 - h2) % 12
        return diff in (0, 4, 8)
    
    def is_dusthana_from(self, planet1: str, planet2: str) -> bool:
        h1 = self._planet_houses.get(planet1)
        h2 = self._planet_houses.get(planet2)
        if not h1 or not h2:
            return False
        diff = (h1 - h2) % 12
        return diff in (5, 7, 11)  # 6th, 8th, 12th
    
    def is_planet_aspecting_house(self, planet: str, target_house: int) -> bool:
        """Check Parashari aspect from planet to house"""
        planet_house = self._planet_houses.get(planet)
        if not planet_house:
            return False
        
        # Standard 7th aspect for all planets
        if ((planet_house + 6 - 1) % 12) + 1 == target_house:
            return True
        
        # Special aspects
        special_aspects = {
            "Mars": [4, 7, 8],
            "Jupiter": [5, 7, 9],
            "Saturn": [3, 7, 10],
        }
        
        if planet in special_aspects:
            for aspect_house in special_aspects[planet]:
                if ((planet_house + aspect_house - 2) % 12) + 1 == target_house:
                    return True
        
        return False
    
    def get_planet_aspecting_planet(self, from_planet: str, to_planet: str) -> bool:
        to_house = self._planet_houses.get(to_planet)
        if not to_house:
            return False
        return self.is_planet_aspecting_house(from_planet, to_house)
    
    def is_exchange(self, planet1: str, planet2: str) -> bool:
        """Check if two planets are in sign exchange (Parivartana)"""
        p1_sign = self.get_planet_sign(planet1)
        p2_sign = self.get_planet_sign(planet2)
        if not p1_sign or not p2_sign:
            return False
        return (self._sign_lords.get(p1_sign) == planet2 and 
                self._sign_lords.get(p2_sign) == planet1)
    
    def are_lords_mutually_connected(self, house1: int, house2: int) -> bool:
        """Check if lords of two houses are conjunct, aspect, or exchange"""
        lord1 = self.get_house_lord(house1)
        lord2 = self.get_house_lord(house2)
        if not lord1 or not lord2 or lord1 == lord2:
            return False
        
        # Conjunction
        if self.are_in_same_house(lord1, lord2):
            return True
        
        # Mutual aspect
        if (self.get_planet_aspecting_planet(lord1, lord2) and 
            self.get_planet_aspecting_planet(lord2, lord1)):
            return True
        
        # Exchange
        if self.is_exchange(lord1, lord2):
            return True
        
        return False
    
    # ==================== Dynamic State Access ====================
    
    def get_current_mahadasha(self) -> Optional[str]:
        if not self._dynamic_state or not self._dynamic_state.dasha:
            return None
        current = self._dynamic_state.dasha.get("current", {})
        md = current.get("mahadasha")
        return md.get("planet") if md else None
    
    def get_current_antardasha(self) -> Optional[str]:
        if not self._dynamic_state or not self._dynamic_state.dasha:
            return None
        current = self._dynamic_state.dasha.get("current", {})
        ad = current.get("antardasha")
        return ad.get("planet") if ad else None
    
    def get_dasha_hierarchy(self) -> List[str]:
        if not self._dynamic_state or not self._dynamic_state.dasha:
            return []
        current = self._dynamic_state.dasha.get("current", {})
        return current.get("hierarchy", [])
    
    def get_transit_planet_sign(self, planet: str) -> Optional[str]:
        if not self._dynamic_state or not self._dynamic_state.transits:
            return None
        snapshot = self._dynamic_state.transits.get("snapshot", {})
        planets = snapshot.get("planets", {})
        pdata = planets.get(planet, {})
        return pdata.get("sign")
    
    def get_transit_planet_house(self, planet: str) -> Optional[int]:
        if not self._dynamic_state or not self._dynamic_state.transits:
            return None
        relations = self._dynamic_state.transits.get("relations", [])
        for r in relations:
            if r.get("transit_planet") == planet:
                return r.get("natal_house")
        return None
    
    # ==================== Panchanga Access ====================
    
    def get_tithi(self) -> Optional[str]:
        if not self._dynamic_state:
            return None
        return self._dynamic_state.panchanga.tithi.name if self._dynamic_state.panchanga.tithi else None
    
    def get_nakshatra(self) -> Optional[str]:
        if not self._dynamic_state:
            return None
        return self._dynamic_state.panchanga.nakshatra.name if self._dynamic_state.panchanga.nakshatra else None
    
    def get_yoga(self) -> Optional[str]:
        if not self._dynamic_state:
            return None
        return self._dynamic_state.panchanga.yoga.name if self._dynamic_state.panchanga.yoga else None
    
    def get_karana(self) -> Optional[str]:
        if not self._dynamic_state:
            return None
        return self._dynamic_state.panchanga.karana.name if self._dynamic_state.panchanga.karana else None
    
    def get_paksha(self) -> Optional[str]:
        if not self._dynamic_state:
            return None
        return self._dynamic_state.panchanga.paksha
    
    def is_day(self) -> Optional[bool]:
        if not self._dynamic_state:
            return None
        return self._dynamic_state.panchanga.is_day
    
    # ==================== Evidence Builder ====================
    
    def build_evidence(
        self,
        evidence_type: EvidenceType,
        subject: str,
        value: Any,
        expected: Any = None,
        actual: Any = None,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build structured evidence from context facts"""
        return {
            "evidence_type": evidence_type.value,
            "subject": subject,
            "value": value,
            "expected": expected,
            "actual": actual,
            "source": "ChartFacts" if evidence_type != EvidenceType.DASHA_PERIOD else "DynamicState",
            "significance": "",
            "details": details or {}
        }