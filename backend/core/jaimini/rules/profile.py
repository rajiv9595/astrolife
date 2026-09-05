"""
Phase 5E — Jaimini yoga evaluation profile.

Pure configuration. No astronomy, no prediction, no timestamps.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class JaiminiYogaProfile(BaseModel):
    """
    Configuration for Jaimini yoga evaluation.

    The karaka_method MUST match the method bound into the consumed
    JaiminiFacts; the pipeline refuses to mix 7-karaka and 8-karaka results.
    """

    karaka_method: str = Field(
        default="SEVEN_KARAKA",
        description="Must equal JaiminiFacts.chara_karakas.method (SEVEN_KARAKA/EIGHT_KARAKA)"
    )
    enabled_rule_ids: Optional[List[str]] = Field(
        default=None,
        description="Subset of catalogue rule IDs to evaluate; None evaluates all"
    )
    float_tolerance: float = Field(
        default=1e-7,
        description="Epsilon for karaka-identity tie detection in cancellation"
    )
    source_reference: str = Field(
        default="UNVERIFIED",
        description="Exact textual reference verification status"
    )
    version: str = Field(default="1.0.0", description="Yoga engine version")
