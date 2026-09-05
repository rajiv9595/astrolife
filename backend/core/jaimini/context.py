"""
Jaimini Context — Astrolife V2 Phase 5D

Provides convenient, deterministic, read-only access to computed Jaimini facts.
Consumes pre-computed JaiminiFacts without performing any independent calculations.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any

from .models import JaiminiFacts, KarakaItem, ArudhaPadaItem, UpapadaDetails, KarakamshaDetails


class JaiminiContext:
    """
    Read-only convenience wrapper around JaiminiFacts.
    Useful for future Jaimini rule engines and report formatters.
    """
    
    def __init__(self, facts: JaiminiFacts):
        self._facts = facts
        
    @property
    def facts(self) -> JaiminiFacts:
        return self._facts
        
    @property
    def atmakaraka(self) -> str:
        """Name of the Atmakaraka planet (e.g. 'Moon')."""
        return self._facts.karakamsha.atmakaraka_planet
        
    @property
    def amatyakaraka(self) -> str:
        """Name of the Amatyakaraka planet."""
        item = self._facts.chara_karakas.karakas.get("AmK")
        return item.planet if item else ""
        
    @property
    def darakaraka(self) -> str:
        """Name of the Darakaraka planet."""
        item = self._facts.chara_karakas.karakas.get("DK")
        return item.planet if item else ""
        
    @property
    def arudha_lagna(self) -> str:
        """Sign name of Arudha Lagna (AL / A1)."""
        return self._facts.arudha_lagna.final_sign
        
    @property
    def upapada(self) -> str:
        """Sign name of Upapada Lagna (UL / A12)."""
        return self._facts.upapada.final_sign
        
    @property
    def karakamsha_sign(self) -> str:
        """Sign name of Karakamsha (D9 sign of Atmakaraka)."""
        return self._facts.karakamsha.karakamsha_sign
        
    @property
    def swamsa_navamsha_lagna(self) -> str:
        """Sign name of D9 Navamsha Lagna."""
        return self._facts.karakamsha.swamsa_navamsha_lagna_sign
        
    def get_karaka(self, code: str) -> Optional[KarakaItem]:
        """Lookup KarakaItem by code ('AK', 'AmK', 'BK', etc.)."""
        return self._facts.chara_karakas.karakas.get(code)
        
    def get_planet_karaka(self, planet_name: str) -> Optional[str]:
        """Lookup Karaka code for a given planet name."""
        return self._facts.chara_karakas.planet_to_karaka.get(planet_name)
        
    def get_arudha_pada(self, house_num: int) -> Optional[ArudhaPadaItem]:
        """Lookup ArudhaPadaItem for a house 1-12."""
        return self._facts.arudha_padas.get(house_num)
        
    def does_sign_aspect(self, source_sign: str, target_sign: str) -> bool:
        """Check if source_sign casts Rashi Drishti on target_sign."""
        aspects = self._facts.rashi_drishti.sign_aspects.get(source_sign, [])
        return target_sign in aspects
        
    def does_planet_aspect_sign(self, planet_name: str, target_sign: str) -> bool:
        """Check if planet casts Rashi Drishti on target_sign via occupied sign."""
        aspects = self._facts.rashi_drishti.planet_aspects.get(planet_name, [])
        return target_sign in aspects
        
    def does_planet_aspect_planet(self, planet_from: str, planet_to: str) -> bool:
        """Check if planet_from casts Rashi Drishti on planet_to via occupied signs."""
        aspects = self._facts.rashi_drishti.planets_aspected_by_planet.get(planet_from, [])
        return planet_to in aspects
