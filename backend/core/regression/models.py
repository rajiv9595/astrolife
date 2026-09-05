"""
Phase 10 — regression models. Declarative golden records + comparison
results. No calculation logic here; this package CALLS canonical systems.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

SOURCE_TYPES = (
    "INDEPENDENT_CALCULATION",
    "EXTERNAL_REFERENCE",
    "MATHEMATICAL_INVARIANT",
    "HISTORICAL_ACCEPTED",
    "SYNTHETIC_EXPECTED",
    "UNVERIFIED_GOLDEN",
)

FAILURE_CLASSES = (
    "CALCULATION_REGRESSION",
    "VARGA_REGRESSION",
    "DASHA_REGRESSION",
    "TRANSIT_REGRESSION",
    "STRENGTH_REGRESSION",
    "YOGA_REGRESSION",
    "DOSHA_REGRESSION",
    "JAIMINI_REGRESSION",
    "RULE_REGRESSION",
    "EVIDENCE_REGRESSION",
    "AGENT_REGRESSION",
    "PREDICTION_REGRESSION",
    "RESEARCH_REGRESSION",
    "API_CONTRACT_REGRESSION",
    "DETERMINISM_REGRESSION",
    "SECURITY_REGRESSION",
    "TEST_INFRASTRUCTURE_FAILURE",
    "UNKNOWN",
)

TOLERANCE_KINDS = ("exact", "absolute", "angular")


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, default=str)


def sha256_of(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


class Tolerance(BaseModel):
    kind: str = "exact"
    value: float = 0.0

    model_config = {"frozen": True}


class GoldenValue(BaseModel):
    golden_id: str
    field: str = ""
    expected: Any = None
    tolerance: Tolerance = Field(default_factory=Tolerance)
    source_type: str = "HISTORICAL_ACCEPTED"
    source_reference: str = ""
    verification_state: str = "ACCEPTED"
    methodology: str = ""
    notes: str = ""

    model_config = {"frozen": True}


class CompareResult(BaseModel):
    golden_id: str
    passed: bool
    expected: Any = None
    actual: Any = None
    difference: Any = None
    tolerance: Tolerance = Field(default_factory=Tolerance)
    failure_class: str = "UNKNOWN"

    model_config = {"frozen": True}


class Discrepancy(BaseModel):
    golden_id: str
    expected: Any = None
    actual: Any = None
    difference: Any = None
    first_divergent_layer: str = ""
    affected_downstream: List[str] = Field(default_factory=list)
    suspected_cause: str = ""
    implementation_or_golden_wrong: str = "UNDETERMINED"
    recommendation: str = ""
    failure_class: str = "UNKNOWN"

    model_config = {"frozen": True}
