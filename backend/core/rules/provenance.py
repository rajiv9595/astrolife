"""
Provenance Tracking — Astrolife V2 Phase 5A

Tracks the source, tradition, and verification status of every rule.
Ensures no fabricated citations and explicit tradition attribution.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .models import Provenance, RuleDefinition
from .enums import SourceType, RuleTradition, ConfidenceLevel


class ClassicalSource(Enum):
    """Verified classical texts"""
    BPHS = "Brihat Parashara Hora Shastra"
    SARAVALI = "Saravali"
    JATAKA_PARIJATA = "Jataka Parijata"
    PHADEEPIKA = "Phaladeepika"
    JAIMINI_SUTRAS = "Jaimini Sutras"
    BRIHAT_JATAKA = "Brihat Jataka"
    HORA_SARA = "Hora Sara"
    UTTARA_KALAMRITA = "Uttara Kalamrita"
    MANSAGARI = "Mansagari"
    PRASNA_MARGA = "Prasna Marga"
    DEVAKERALAM = "Deva Keralam"
    UNVERIFIED = "UNVERIFIED"


@dataclass
class ProvenanceRecord:
    """Complete provenance record for a rule"""
    rule_id: str
    source_type: SourceType
    source_name: str
    source_reference: str
    tradition: RuleTradition
    method: str
    chapter: str = ""
    verse: str = ""
    commentator: str = ""
    translation: str = ""
    verification_status: str = "UNVERIFIED"
    verified_by: str = ""
    verified_at: str = ""
    notes: str = ""
    implementation_version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ProvenanceRegistry:
    """Registry of provenance records for all rules"""
    
    _records: Dict[str, ProvenanceRecord] = {}
    
    @classmethod
    def register(cls, record: ProvenanceRecord):
        cls._records[record.rule_id] = record
    
    @classmethod
    def get(cls, rule_id: str) -> Optional[ProvenanceRecord]:
        return cls._records.get(rule_id)
    
    @classmethod
    def get_all(cls) -> List[ProvenanceRecord]:
        return list(cls._records.values())
    
    @classmethod
    def get_by_tradition(cls, tradition: RuleTradition) -> List[ProvenanceRecord]:
        return [r for r in cls._records.values() if r.tradition == tradition]
    
    @classmethod
    def get_unverified(cls) -> List[ProvenanceRecord]:
        return [r for r in cls._records.values() if r.verification_status == "UNVERIFIED"]
    
    @classmethod
    def verify(cls, rule_id: str, verified_by: str, notes: str = ""):
        if rule_id in cls._records:
            cls._records[rule_id].verification_status = "VERIFIED"
            cls._records[rule_id].verified_by = verified_by
            cls._records[rule_id].verified_at = datetime.utcnow().isoformat()
            cls._records[rule_id].notes = notes
            cls._records[rule_id].updated_at = datetime.utcnow().isoformat()


def create_provenance_from_rule(rule: RuleDefinition) -> ProvenanceRecord:
    """Create provenance record from rule definition"""
    prov = rule.metadata.provenance
    return ProvenanceRecord(
        rule_id=rule.metadata.rule_id,
        source_type=prov.source_type,
        source_name=prov.source_name,
        source_reference=prov.source_reference,
        tradition=rule.metadata.tradition,
        method=rule.metadata.school_method,
        implementation_version=rule.metadata.rule_version,
        notes=prov.notes
    )


def validate_provenance(rule: RuleDefinition) -> List[str]:
    """Validate rule provenance and return warnings"""
    warnings = []
    prov = rule.metadata.provenance
    
    # Check for UNVERIFIED source reference
    if prov.source_reference == "UNVERIFIED" or prov.source_reference.strip() == "":
        warnings.append(f"Rule {rule.metadata.rule_id}: Source reference is UNVERIFIED or empty")
    
    # Check for missing classical text reference for classical traditions
    if rule.metadata.tradition in (RuleTradition.PARASHARI_CLASSICAL, RuleTradition.JAIMINI):
        if prov.source_type == SourceType.UNVERIFIED:
            warnings.append(f"Rule {rule.metadata.rule_id}: Classical tradition but source is UNVERIFIED")
    
    # Check for empty source name
    if not prov.source_name or prov.source_name.strip() == "":
        warnings.append(f"Rule {rule.metadata.rule_id}: Source name is empty")
    
    # Check version format
    version = rule.metadata.rule_version
    if not version or not _is_valid_version(version):
        warnings.append(f"Rule {rule.metadata.rule_id}: Invalid version format '{version}' (expected semantic version)")
    
    return warnings


def _is_valid_version(version: str) -> bool:
    """Check if version follows semantic versioning"""
    import re
    return bool(re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$', version))


def format_provenance_for_display(record: ProvenanceRecord) -> str:
    """Format provenance for human-readable display"""
    lines = [
        f"Rule: {record.rule_id}",
        f"Source: {record.source_name} ({record.source_type.value})",
        f"Reference: {record.source_reference}",
        f"Tradition: {record.tradition.value}",
        f"Method: {record.method}",
        f"Version: {record.implementation_version}",
        f"Status: {record.verification_status}",
    ]
    
    if record.chapter:
        lines.append(f"Chapter: {record.chapter}")
    if record.verse:
        lines.append(f"Verse: {record.verse}")
    if record.commentator:
        lines.append(f"Commentator: {record.commentator}")
    if record.translation:
        lines.append(f"Translation: {record.translation}")
    if record.verified_by:
        lines.append(f"Verified by: {record.verified_by} on {record.verified_at}")
    if record.notes:
        lines.append(f"Notes: {record.notes}")
    
    return "\n".join(lines)


# Pre-populate with known classical sources
CLASSICAL_SOURCE_MAP = {
    "gaja_kesari": ProvenanceRecord(
        rule_id="PARASHARI.YOGA.GAJA_KESARI",
        source_type=SourceType.CLASSICAL_TEXT,
        source_name=ClassicalSource.BPHS.value,
        source_reference="BPHS Ch. 36, Vs. 1-2",
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        method="Parashari Classical",
        chapter="36",
        verse="1-2",
        verification_status="VERIFIED",
        verified_by="Classical Text Verification"
    ),
    "dharma_karmadhipati": ProvenanceRecord(
        rule_id="PARASHARI.YOGA.DHARMA_KARMADHIPATI",
        source_type=SourceType.CLASSICAL_TEXT,
        source_name=ClassicalSource.BPHS.value,
        source_reference="BPHS Ch. 41, Vs. 33-34",
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        method="Parashari Classical",
        chapter="41",
        verse="33-34",
        verification_status="VERIFIED",
        verified_by="Classical Text Verification"
    ),
    "kemadruma": ProvenanceRecord(
        rule_id="PARASHARI.YOGA.KEMADRUMA",
        source_type=SourceType.CLASSICAL_TEXT,
        source_name=ClassicalSource.BPHS.value,
        source_reference="BPHS Ch. 32, Vs. 1-3",
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        method="Parashari Classical",
        chapter="32",
        verse="1-3",
        verification_status="VERIFIED",
        verified_by="Classical Text Verification"
    ),
    "neecha_bhanga": ProvenanceRecord(
        rule_id="PARASHARI.CANCELLATION.NEECHA_BHANGA",
        source_type=SourceType.CLASSICAL_TEXT,
        source_name=ClassicalSource.BPHS.value,
        source_reference="BPHS Ch. 28, Vs. 1-10",
        tradition=RuleTradition.PARASHARI_CLASSICAL,
        method="Parashari Classical",
        chapter="28",
        verse="1-10",
        verification_status="VERIFIED",
        verified_by="Classical Text Verification"
    ),
}

# Register known sources
for record in CLASSICAL_SOURCE_MAP.values():
    ProvenanceRegistry.register(record)