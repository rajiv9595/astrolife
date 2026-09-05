"""
Phase 5E — Karakamsha / Swamsa yogas.

Strict separation: Karakamsha = D9 sign of AK; Swamsa = D9 Lagna sign.
D9 occupancy is consumed from canonical varga facts (VargaPosition or dict).
D1 Rashi-Drishti mitigation is NOT applicable inside D9 scope; mitigation is
therefore NONE with explicit evidence (honest scope boundary).
"""
from __future__ import annotations
from typing import Any, List

from .models import FormationEvidenceItem, YogaOutcome
from .predicates import (
    d9_lagna_sign,
    karaka_planet,
    planets_in_d9_sign,
    NATURAL_BENEFICS,
)
from core.rules.enums import CancellationStatus, MitigationStatus


def _d9_none_mitigation(focal: str) -> tuple:
    return (
        MitigationStatus.NONE,
        [f"No mitigation: {focal} is a D9-scope rule; D1 Rashi-Drishti mitigation not applicable."],
    )


def _benefic_occupancy_rule(
    chart_facts: Any,
    varga_facts: Any,
    focal_sign: str | None,
    focal_label: str,
    dependencies: List[str],
    notes: str,
) -> YogaOutcome:
    occupants = planets_in_d9_sign(chart_facts, varga_facts, focal_sign) if focal_sign else []
    benefics = [p for p in occupants if p in NATURAL_BENEFICS]
    formed = len(benefics) > 0
    ev = [
        FormationEvidenceItem(
            condition=f"benefic occupies {focal_label} (D9)",
            actual_value=f"{focal_label}={focal_sign}; D9 occupants={occupants}; benefics={benefics}",
            expected_value=">=1 of Jupiter/Venus/Mercury/Moon in D9 sign",
            source_fact="varga_facts D9 (canonical, not recomputed)",
            passed=formed,
        )
    ]
    mstat, mev = _d9_none_mitigation(focal_label)
    return YogaOutcome(
        formed=formed, formation_evidence=ev,
        cancellation_status=CancellationStatus.NONE,
        cancellation_evidence=["No cancellation: D9 occupancy is factual; no defensible structural cancellation."],
        mitigation_status=mstat, mitigation_evidence=mev,
        relevant_planets=benefics,
        relevant_signs=[focal_sign] if focal_sign else [],
        dependencies=dependencies,
        notes=notes,
    )


def evaluate_karakamsha_benefic(
    chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float
) -> YogaOutcome:
    """A natural benefic occupies the Karakamsha (AK's D9 sign) in D9."""
    ak = karaka_planet(jaimini_facts, "AK")
    kak = jaimini_facts.karakamsha.karakamsha_sign
    return _benefic_occupancy_rule(
        chart_facts, varga_facts, kak, "Karakamsha",
        dependencies=["JaiminiFacts.karakamsha", "JaiminiFacts.chara_karakas", "varga_facts.D9"],
        notes=f"Karakamsha benefic-occupancy combination (AK={ak}); condition formed, no outcome claimed.",
    )


def evaluate_swamsa_benefic(
    chart_facts: Any, jaimini_facts: Any, varga_facts: Any, tolerance: float
) -> YogaOutcome:
    """A natural benefic occupies the Swamsa (D9 Lagna sign) in D9."""
    kak = jaimini_facts.karakamsha.karakamsha_sign
    swa = jaimini_facts.karakamsha.swamsa_navamsha_lagna_sign
    out = _benefic_occupancy_rule(
        chart_facts, varga_facts, swa, "Swamsa",
        dependencies=["JaiminiFacts.karakamsha", "varga_facts.D9"],
        notes="Swamsa benefic-occupancy combination; condition formed, no outcome claimed.",
    )
    out.relevant_signs = sorted({s for s in ([swa, kak] if kak != swa else [swa]) if s})
    out.notes += f" Karakamsha={kak} tracked separately (interchange guard)."
    return out
