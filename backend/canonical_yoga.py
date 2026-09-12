"""
Canonical Yoga Adapter — Production adapter: canonical Rule Engine -> legacy yoga response shape.

NO ASTROLOGY IS COMPUTED HERE. Every value originates from:
- backend.core.rules.parashari.evaluate_all_parashari (canonical yoga evaluation)
- backend.core.rules.evidence (evidence formatting)
- backend.core.rules.provenance (provenance records)

This module ONLY projects canonical RuleResult into the legacy yoga response format
consumed by frontend (chart_data.yogas).
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.core.rules.parashari import evaluate_all_parashari, create_parashari_evaluator
from backend.core.rules.context import RuleContext
from backend.core.rules.evidence import format_evidence_for_json
from backend.core.rules.provenance import ProvenanceRegistry, create_provenance_from_rule
from backend.core.calculation.pipeline import ChartFacts
from backend.core.strength.models import StrengthReport
from backend.core.calculation.dynamic import DynamicAstrologyState


def _rule_result_to_legacy_yoga(rule_result, include_evidence: bool = True, include_provenance: bool = True) -> Dict[str, Any]:
    """Convert canonical RuleResult to legacy yoga response format."""
    
    # Map canonical formation status to legacy status.
    # NOTE: check NOT_FORMED first — "FORMED" is a substring of "NOT_FORMED".
    formation_status = str(rule_result.formation_status)
    if "NOT_FORMED" in formation_status:
        legacy_status = "INACTIVE"
    elif "FORMED" in formation_status:
        legacy_status = "ACTIVE"
    else:
        legacy_status = formation_status
    
    # Legacy yoga structure
    yoga = {
        "id": rule_result.rule_id,
        "name": rule_result.rule_name,
        "description": "",  # Could be populated from rule metadata
        "status": legacy_status,
        "is_strong": "STRONG" in str(rule_result.strength_status),
        "is_active": rule_result.is_active(),
    }
    
    # Add score if available (canonical uses strength status, legacy used score)
    if hasattr(rule_result, 'strength_status') and rule_result.strength_status:
        strength_str = str(rule_result.strength_status)
        if "STRONG" in strength_str:
            yoga["score"] = 100
        elif "WEAK" in strength_str:
            yoga["score"] = 30
        else:
            yoga["score"] = 50
    else:
        yoga["score"] = 100 if "FORMED" in formation_status else 0
    
    # Add evidence
    if include_evidence and rule_result.evidence:
        yoga["evidence"] = format_evidence_for_json(rule_result.evidence)
        yoga["evidence_summary"] = _build_evidence_summary(rule_result.evidence)
    else:
        yoga["evidence"] = []
        yoga["evidence_summary"] = "No evidence"
    
    # Add provenance
    if include_provenance:
        provenance_record = ProvenanceRegistry.get(rule_result.rule_id)
        if provenance_record:
            yoga["provenance"] = {
                "rule_id": provenance_record.rule_id,
                "source": provenance_record.source_name,
                "reference": provenance_record.source_reference,
                "tradition": provenance_record.tradition.value if hasattr(provenance_record.tradition, 'value') else str(provenance_record.tradition),
                "method": provenance_record.method,
                "verification_status": provenance_record.verification_status,
                "chapter": provenance_record.chapter,
                "verse": provenance_record.verse,
            }
        else:
            yoga["provenance"] = {
                "rule_id": rule_result.rule_id,
                "source": "Canonical Rule Engine",
                "reference": "UNVERIFIED",
                "tradition": "PARASHARI_CLASSICAL",
                "method": rule_result.method,
                "verification_status": "UNVERIFIED",
            }
    else:
        yoga["provenance"] = {}
    
    # Add signal details for debugging (legacy compatibility)
    if hasattr(rule_result, 'relevant_planets'):
        yoga["relevant_planets"] = rule_result.relevant_planets
    if hasattr(rule_result, 'relevant_houses'):
        yoga["relevant_houses"] = rule_result.relevant_houses
    
    return yoga


def _build_evidence_summary(evidence: List[Any]) -> str:
    """Build a human-readable evidence summary."""
    if not evidence:
        return "No evidence"
    
    by_type = {}
    for e in evidence:
        etype = e.evidence_type.value if hasattr(e.evidence_type, 'value') else str(e.evidence_type)
        by_type[etype] = by_type.get(etype, 0) + 1
    
    parts = []
    for etype, count in sorted(by_type.items()):
        parts.append(f"{count} {etype}")
    
    return "; ".join(parts)


def evaluate_canonical_yogas(
    chart_facts: ChartFacts,
    strength_report: Optional[StrengthReport] = None,
    varga_facts: Optional[Dict[str, Any]] = None,
    dynamic_state: Optional[DynamicAstrologyState] = None,
    evaluation_datetime: Optional[datetime] = None,
    include_evidence: bool = True,
    include_provenance: bool = True,
) -> List[Dict[str, Any]]:
    """
    Evaluate all canonical Parashari yogas and return in legacy yoga format.
    
    This is the authoritative production yoga evaluation.
    """
    # Build RuleContext from canonical data
    context = RuleContext(
        chart_facts=chart_facts,
        strength_report=strength_report,
        varga_facts=varga_facts,
        dynamic_state=dynamic_state,
        evaluation_datetime=evaluation_datetime,
    )
    
    # Create evaluator with canonical config
    evaluator = create_parashari_evaluator()
    
    # Evaluate all canonical Parashari yogas
    results = evaluate_all_parashari(context, evaluator)
    
    # Convert to legacy format
    legacy_yogas = []
    for result in results:
        legacy_yoga = _rule_result_to_legacy_yoga(
            result,
            include_evidence=include_evidence,
            include_provenance=include_provenance,
        )
        legacy_yogas.append(legacy_yoga)
    
    return legacy_yogas


def get_canonical_yoga_by_id(
    rule_id: str,
    chart_facts: ChartFacts,
    strength_report: Optional[StrengthReport] = None,
    varga_facts: Optional[Dict[str, Any]] = None,
    dynamic_state: Optional[DynamicAstrologyState] = None,
    evaluation_datetime: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    """Evaluate a single canonical yoga by rule_id."""
    context = RuleContext(
        chart_facts=chart_facts,
        strength_report=strength_report,
        varga_facts=varga_facts,
        dynamic_state=dynamic_state,
        evaluation_datetime=evaluation_datetime,
    )
    evaluator = create_parashari_evaluator()
    
    from backend.core.rules.parashari import evaluate_parashari_by_id
    result = evaluate_parashari_by_id(rule_id, context, evaluator)
    
    if result is None:
        return None
    
    return _rule_result_to_legacy_yoga(result, include_evidence=True, include_provenance=True)


def get_canonical_yoga_coverage() -> Dict[str, Any]:
    """Get information about canonical yoga coverage vs legacy."""
    from backend.core.rules.parashari import PARASHARI_RULE_IDS, build_parashari_catalog
    
    catalog = build_parashari_catalog()
    rule_ids = PARASHARI_RULE_IDS
    
    # Categorize by type
    categories = {}
    for rule in catalog:
        cat = rule.metadata.category.value if hasattr(rule.metadata.category, 'value') else str(rule.metadata.category)
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(rule.metadata.rule_id)
    
    return {
        "total_canonical_rules": len(rule_ids),
        "rule_ids": rule_ids,
        "by_category": categories,
    }


# Canonical rule ID -> legacy ruleset ID(s) it covers.
# Category A (exact/alias), Category B (represented), Category C (Migration #3B).
# Legacy entries covered here are suppressed in the /compute merge so the
# canonical result is the single authoritative entry (no duplicate Yoga IDs).
CANONICAL_COVERS_LEGACY: Dict[str, List[str]] = {
    # --- Category A: exact matches / alias ---
    "PARASHARI.YOGA.ADHI": ["adhi_yoga"],
    "PARASHARI.YOGA.AMALA": ["amala_yoga"],
    "PARASHARI.YOGA.ANAPHA": ["anapha_yoga"],
    "PARASHARI.YOGA.BHADRA": ["bhadra_yoga"],
    "PARASHARI.YOGA.BUDHA_ADITYA": ["budhaditya_yoga", "nipuna_yoga"],
    "PARASHARI.YOGA.CHANDRA_MANGALA": ["chandra_mangala_yoga"],
    "PARASHARI.YOGA.DHARMA_KARMADHIPATI": ["dharma_karmadhipati_yoga"],
    "PARASHARI.YOGA.DURUDHARA": ["durdhara_yoga"],
    "PARASHARI.YOGA.GAJA_KESARI": ["gaja_kesari"],
    "PARASHARI.YOGA.HAMSA": ["hamsa_yoga"],
    "PARASHARI.YOGA.KEMADRUMA": ["kemadruma_yoga"],
    "PARASHARI.YOGA.LAKSHMI": ["lakshmi_yoga"],
    "PARASHARI.YOGA.MALAVYA": ["malavya_yoga"],
    "PARASHARI.YOGA.PARIVARTANA_MAHA": ["maha_parivartana_yoga"],
    "PARASHARI.YOGA.PARIVARTANA_KHALA": ["khala_parivartana_yoga"],
    "PARASHARI.YOGA.PARIVARTANA_DAINYA": ["dainya_parivartana_yoga"],
    "PARASHARI.YOGA.RUCHAKA": ["ruchaka_yoga"],
    "PARASHARI.YOGA.SARASWATI": ["saraswati_yoga"],
    "PARASHARI.YOGA.SASA": ["sasa_yoga"],
    "PARASHARI.YOGA.SUNAPHA": ["sunapha_yoga"],
    "PARASHARI.YOGA.VASUMATI": ["vasumati_yoga"],
    # --- Category B: already represented by canonical splits ---
    "PARASHARI.YOGA.DHANA_2_11": ["dhana_yoga"],
    "PARASHARI.YOGA.DHANA_5_9": ["dhana_yoga"],
    "PARASHARI.YOGA.DHANA_LAGNA_WEALTH": ["dhana_yoga"],
    "PARASHARI.YOGA.NEECHA_BHANGA": ["neechabhanga"],
    "PARASHARI.YOGA.NEECHA_BHANGA_RAJA": ["neechabhanga"],
    "PARASHARI.YOGA.VIPARITA_HARSHA": ["viparita_rajayoga"],
    "PARASHARI.YOGA.VIPARITA_SARALA": ["viparita_rajayoga"],
    "PARASHARI.YOGA.VIPARITA_VIMALA": ["viparita_rajayoga"],
    # --- Category C: Migration #3B canonical re-implementation ---
    "PARASHARI.YOGA.AKHANDA_SAMRAJYA": ["akhanda_samrajya_yoga"],
    "PARASHARI.YOGA.BHAGYA": ["bhagya_yoga"],
    "PARASHARI.YOGA.CHAMARA": ["chamara_yoga"],
    "PARASHARI.YOGA.CHHATRA": ["chhatra_yoga"],
    "PARASHARI.YOGA.DHENU": ["dhenu_yoga"],
    "PARASHARI.YOGA.GANDHARVA": ["gandharva_yoga"],
    "PARASHARI.YOGA.GO": ["go_yoga"],
    "PARASHARI.YOGA.HARA": ["hara_yoga"],
    "PARASHARI.YOGA.HARI": ["hari_yoga"],
    "PARASHARI.YOGA.JALADHI": ["jaladhi_yoga"],
    "PARASHARI.YOGA.KAHALA": ["kahala_yoga"],
    "PARASHARI.YOGA.KALANIDHI": ["kalanidhi_yoga"],
    "PARASHARI.YOGA.KAMA": ["kama_yoga"],
    "PARASHARI.YOGA.KHYATHI": ["khyathi_yoga"],
    "PARASHARI.YOGA.KUSUMA": ["kusuma_yoga"],
    "PARASHARI.YOGA.MALA": ["mala_yoga"],
    "PARASHARI.YOGA.MUSALA": ["musala_yoga"],
    "PARASHARI.YOGA.PARIJATA": ["parijata_yoga"],
    "PARASHARI.YOGA.PARVATA": ["parvata_yoga"],
    "PARASHARI.YOGA.PUSHKALA": ["pushkala_yoga"],
    "PARASHARI.YOGA.RAJA_LAKSHANA": ["raja_lakshana_yoga"],
    "PARASHARI.YOGA.RAVI": ["ravi_yoga"],
    "PARASHARI.YOGA.SHAKATA": ["shakata_yoga"],
    "PARASHARI.YOGA.SHAURYA": ["shaurya_yoga"],
    "PARASHARI.YOGA.SHIVA": ["shiva_yoga"],
    "PARASHARI.YOGA.SRINATHA": ["srinatha_yoga"],
    "PARASHARI.YOGA.SUPARIJATA": ["suparijata_yoga"],
    "PARASHARI.YOGA.UBHAYACHARI": ["ubhayachari_yoga"],
    "PARASHARI.YOGA.VASI": ["vasi_yoga"],
    "PARASHARI.YOGA.VESI": ["vesi_yoga"],
    "PARASHARI.YOGA.VISHNU": ["vishnu_yoga"],
    # --- Category D: Migration #3C canonical extension ---
    "PARASHARI.YOGA.ASTRA": ["astra_yoga"],
    "PARASHARI.YOGA.ASURA": ["asura_yoga"],
    "PARASHARI.YOGA.BHERI": ["bheri_yoga"],
    "PARASHARI.YOGA.BHRIGU_MANGALA": ["bhrigu_mangala_yoga"],
    "PARASHARI.YOGA.BRAHMA": ["brahma_yoga"],
    "PARASHARI.YOGA.DAMA": ["dama_yoga"],
    "PARASHARI.YOGA.GOLA": ["gola_yoga"],
    "PARASHARI.YOGA.INDRA": ["indra_yoga"],
    "PARASHARI.YOGA.KEDARA": ["kedara_yoga"],
    "PARASHARI.YOGA.KURMA": ["kurma_yoga"],
    "PARASHARI.YOGA.PASHA": ["pasha_yoga"],
    "PARASHARI.YOGA.SARPA": ["sarpa_yoga"],
    "PARASHARI.YOGA.SHULA": ["shula_yoga"],
    "PARASHARI.YOGA.VEENA": ["veena_yoga"],
    "PARASHARI.YOGA.YUGA": ["yuga_yoga"],
}


def get_covered_legacy_ids() -> set:
    """Legacy ruleset IDs covered by canonical rules (gap-fill must skip these)."""
    covered = set()
    for legacy_ids in CANONICAL_COVERS_LEGACY.values():
        covered.update(legacy_ids)
    return covered


# Legacy yoga ruleset IDs for comparison
LEGACY_YOGA_RULESET_IDS = [
    "adhi_yoga", "akhanda_samrajya_yoga", "amala_yoga", "anapha_yoga", "astra_yoga",
    "asura_yoga", "bhadra_yoga", "bhagya_yoga", "bheri_yoga", "bhrigu_mangala_yoga",
    "brahma_yoga", "budhaditya_yoga", "chamara_yoga", "chandra_mangala_yoga",
    "chhatra_yoga", "dainya_parivartana_yoga", "dama_yoga", "dhana_yoga",
    "dharma_karmadhipati_yoga", "dhenu_yoga", "durdhara_yoga", "gaja_kesari",
    "gandharva_yoga", "garuda_yoga", "go_yoga", "gola_yoga", "hamsa_yoga",
    "hara_yoga", "hari_yoga", "indra_yoga", "jaladhi_yoga", "kahala_yoga",
    "kalanidhi_yoga", "kalpadruma_yoga", "kama_yoga", "kedara_yoga", "kemadruma_yoga",
    "khala_parivartana_yoga", "khyathi_yoga", "kurma_yoga", "kusuma_yoga",
    "lakshmi_yoga", "maha_parivartana_yoga", "mahabhagya_yoga", "mala_yoga",
    "malavya_yoga", "matsya_yoga", "mridanga_yoga", "musala_yoga", "neechabhanga",
    "nipuna_yoga", "parijata_yoga", "parvata_yoga", "pasha_yoga", "pushkala_yoga",
    "raja_lakshana_yoga", "ravi_yoga", "ruchaka_yoga", "saraswati_yoga",
    "sarpa_yoga", "sasa_yoga", "shakata_yoga", "shaurya_yoga", "shiva_yoga",
    "shula_yoga", "srinatha_yoga", "sunapha_yoga", "suparijata_yoga", "ubhayachari_yoga",
    "vasi_yoga", "vasumati_yoga", "veena_yoga", "vesi_yoga", "viparita_rajayoga",
    "vishnu_yoga", "yuga_yoga",
]


def compare_coverage() -> Dict[str, Any]:
    """Compare canonical vs legacy yoga coverage."""
    canonical = get_canonical_yoga_coverage()
    canonical_ids = set(canonical["rule_ids"])
    legacy_ids = set(LEGACY_YOGA_RULESET_IDS)
    
    # Normalize IDs for comparison (remove prefixes)
    canonical_normalized = set()
    for rid in canonical_ids:
        # PARASHARI.YOGA.GAJA_KESARI -> gaja_kesari
        parts = rid.split(".")
        if len(parts) >= 3:
            canonical_normalized.add(parts[-1].lower())
        else:
            canonical_normalized.add(rid.lower())
    
    legacy_normalized = set([rid.replace("_yoga", "").replace("_", "") for rid in legacy_ids])
    # Also try with yoga suffix
    legacy_normalized2 = set([rid.replace("_yoga", "").lower() for rid in legacy_ids])
    
    # Find overlaps
    overlap = canonical_normalized & legacy_normalized
    overlap2 = canonical_normalized & legacy_normalized2
    all_overlap = overlap | overlap2
    
    return {
        "canonical_count": len(canonical_ids),
        "legacy_count": len(legacy_ids),
        "canonical_normalized": sorted(canonical_normalized),
        "legacy_normalized": sorted(legacy_normalized),
        "overlap": sorted(all_overlap),
        "canonical_only": sorted(canonical_normalized - all_overlap),
        "legacy_only": sorted(legacy_normalized - all_overlap),
        "coverage_percentage": round(len(all_overlap) / max(len(canonical_normalized), 1) * 100, 1),
    }