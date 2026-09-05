"""
Jaimini Pipeline — Astrolife V2 Phase 5D

Pure, deterministic pipeline assembling all Jaimini mathematical and structural facts
from validated canonical ChartFacts and VargaFacts.
"""
from __future__ import annotations
from typing import Dict, Any, Optional

from ..calculation.models import ChartFacts
from .profile import JaiminiCalculationProfile
from .models import JaiminiFacts, JaiminiProvenance
from .karakas import calculate_chara_karakas
from .rashi_drishti import calculate_rashi_drishti
from .padas import calculate_all_arudha_padas
from .upapada import calculate_upapada
from .karakamsha import calculate_karakamsha
from .validators import validate_jaimini_facts


def generate_jaimini_facts(
    chart_facts: ChartFacts,
    varga_facts: Dict[str, Any],
    profile: Optional[JaiminiCalculationProfile] = None
) -> JaiminiFacts:
    """
    Deterministically generates JaiminiFacts from canonical inputs.
    
    Requirements:
    - Pure function
    - Zero datetime.now calls
    - Zero Swiss Ephemeris calls
    - Zero recalculation of D1 or D9
    - Strictly reproducible
    """
    if profile is None:
        profile = JaiminiCalculationProfile()
        
    # 1. Chara Karakas
    chara_karakas = calculate_chara_karakas(chart_facts, profile)
    
    # 2. Rashi Drishti (Sign Aspects)
    rashi_drishti = calculate_rashi_drishti(chart_facts, profile)
    
    # 3. Arudha Padas (A1 through A12)
    arudha_padas = calculate_all_arudha_padas(chart_facts, profile)
    arudha_lagna = arudha_padas[1]
    
    # 4. Upapada Lagna (UL / A12)
    upapada = calculate_upapada(chart_facts, profile, precomputed_a12=arudha_padas[12])
    
    # 5. Karakamsha & Swamsa
    karakamsha = calculate_karakamsha(chart_facts, varga_facts, chara_karakas, profile)
    
    # 6. Assemble Unified Evidence
    evidence: Dict[str, Any] = {
        "chara_karakas": chara_karakas.evidence,
        "rashi_drishti": rashi_drishti.evidence,
        "arudha_lagna": arudha_lagna.evidence,
        "upapada": upapada.evidence,
        "karakamsha": karakamsha.evidence,
        "all_padas": {f"A{h}": arudha_padas[h].evidence for h in range(1, 13)}
    }
    
    provenance = JaiminiProvenance(
        tradition="JAIMINI",
        method="CLASSICAL_ARUDHA_STANDARD",
        source_texts=[
            "Jaimini Upadesha Sutras",
            "Brihat Parashara Hora Shastra"
        ],
        source_reference="UNVERIFIED",
        version=profile.version,
        confidence="UNVERIFIED",
        notes="Deterministic fact engine. Zero prediction logic. Exact verse references unverified."
    )

    metadata: Dict[str, Any] = {
        "tradition": "JAIMINI",
        "method": "CLASSICAL_ARUDHA_STANDARD",
        "source_reference": "UNVERIFIED",
        "karaka_method": profile.karaka_method.value,
        "rahu_karaka_method": profile.rahu_karaka_method.value,
        "rashi_drishti_method": profile.rashi_drishti_method.value,
        "arudha_method": profile.arudha_method.value,
        "upapada_method": profile.upapada_method.value,
        "source_tradition": profile.source_tradition
    }
    
    facts = JaiminiFacts(
        profile=profile,
        chara_karakas=chara_karakas,
        rashi_drishti=rashi_drishti,
        arudha_padas=arudha_padas,
        arudha_lagna=arudha_lagna,
        upapada=upapada,
        karakamsha=karakamsha,
        evidence=evidence,
        provenance=provenance,
        metadata=metadata
    )
    
    # 7. Validate Fact Integrity
    validate_jaimini_facts(facts)
    
    return facts


def get_jaimini_facts(
    chart_facts: ChartFacts,
    varga_facts: Dict[str, Any],
    profile: Optional[JaiminiCalculationProfile] = None
) -> JaiminiFacts:
    """Convenience alias for generate_jaimini_facts."""
    return generate_jaimini_facts(chart_facts, varga_facts, profile)
