"""
Dosha Engine — Astrolife V2 Phase 5C

Deterministic, evidence-backed, tradition-aware, explainable dosha evaluation.

Doshas implemented:
  - Manglik/Kuja Dosha (3 methods: Lagna, Moon, Venus)
  - Kemadruma Dosha (classical Parashari)
  - Kala Sarpa Dosha (tradition-dependent, sign-based)
  - Pitru Dosha (modern common definition, tradition-dependent)

Key principles:
  - Formation ≠ Severity (independent statuses)
  - Cancellation ≠ Mitigation (independent concepts)
  - No AI in formation evaluation
  - No deterministic predictions
  - No fear-based language
  - No arbitrary numerical scoring
  - Every result carries evidence and provenance
"""
from .enums import (
    DoshaCategory, DoshaSeverity, DoshaFormationStatus,
    DoshaCancellationStatus, DoshaMitigationStatus, DoshaActivationStatus,
    DoshaTradition, DoshaConfidence, DoshaSourceType,
    ManglikReferencePoint, KalaSarpaMethod,
)
from .models import (
    DoshaResult, DoshaEvaluationSet, DoshaProvenance, DoshaMetadata,
    DoshaEvidence,
)
from .catalog import (
    build_dosha_catalog, evaluate_all_doshas, evaluate_dosha_by_id,
    create_dosha_evaluator, build_manifest, register_dosha_rules,
    DOSHA_RULE_IDS,
)

__all__ = [
    # Enums
    "DoshaCategory", "DoshaSeverity", "DoshaFormationStatus",
    "DoshaCancellationStatus", "DoshaMitigationStatus", "DoshaActivationStatus",
    "DoshaTradition", "DoshaConfidence", "DoshaSourceType",
    "ManglikReferencePoint", "KalaSarpaMethod",
    # Models
    "DoshaResult", "DoshaEvaluationSet", "DoshaProvenance", "DoshaMetadata",
    "DoshaEvidence",
    # Catalog
    "build_dosha_catalog", "evaluate_all_doshas", "evaluate_dosha_by_id",
    "create_dosha_evaluator", "build_manifest", "register_dosha_rules",
    "DOSHA_RULE_IDS",
]
