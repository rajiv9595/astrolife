"""
Phase 5F — deterministic Jaimini conflict-analysis layer (report-only).

Classes:
  DIRECT_CONTRADICTION — two results assert incompatible claims about the
      same proposition (e.g. disjoint AK–AmK rules both FORMED: integrity alarm).
  APPARENT_CONTRADICTION — surface tension resolved by reading evidence
      (reserved; none in the 5E catalogue).
  DIFFERENT_DIMENSIONS — rules describe different subject matter: NO_CONFLICT.
  TRADITION_VARIANT — same dimension viewed under different origin labels or
      tradition-profile subsets.
  INSUFFICIENT_INFORMATION — an UNKNOWN rule participates; conflict
      undecidable for that pair.
  NO_CONFLICT — default for independent/different-dimension pairs.

The engine never resolves conflicts and never ranks rules. It reports.
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field

from ..rules.enums import FormationStatus

DIRECT_CONTRADICTION = "DIRECT_CONTRADICTION"
APPARENT_CONTRADICTION = "APPARENT_CONTRADICTION"
DIFFERENT_DIMENSIONS = "DIFFERENT_DIMENSIONS"
TRADITION_VARIANT = "TRADITION_VARIANT"
INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
NO_CONFLICT = "NO_CONFLICT"


class RuleConflict(BaseModel):
    rule_a: str
    rule_b: str
    conflict_class: str
    same_proposition: bool = False
    detail: str = ""
    resolution: str = "REPORTED_ONLY"


# Pairs asserting about the SAME proposition (same karaka pair / same padas).
SAME_PROPOSITION_PAIRS: List[Tuple[str, str, str]] = [
    ("JAI.KARAKA.AK_AMK_CONJUNCTION", "JAI.DRISHTI.AK_AMK_MUTUAL",
     "AK–AmK relationship: conjunction and mutual-drishti are disjoint by construction"),
    ("JAI.KARAKA.DK_UL_SAMBANDHA", "JAI.ARUDHA.A7_UL_ALIGNMENT",
     "UL family dimension via DK vs via A7"),
    ("JAI.KARAKAMSHA.BENEFIC_OCCUPANCY", "JAI.SWAMSA.BENEFIC_OCCUPANCY",
     "D9 benefic dimension via Karakamsha vs via Swamsa"),
]

# Dimension tags for different-dimension analysis.
DIMENSIONS: Dict[str, str] = {
    "JAI.KARAKA.AK_AMK_CONJUNCTION": "karaka-relationship",
    "JAI.KARAKA.AK_KENDRA_FROM_AL": "karaka-arudha",
    "JAI.KARAKA.DK_UL_SAMBANDHA": "family-ul",
    "JAI.DRISHTI.AK_AMK_MUTUAL": "karaka-relationship",
    "JAI.DRISHTI.AMK_ON_AL": "karaka-arudha",
    "JAI.DRISHTI.AK_ON_AL": "karaka-arudha",
    "JAI.ARUDHA.AL_BENEFIC_OCCUPANCY": "arudha-strength-context",
    "JAI.ARUDHA.AL_LORD_KENDRA_TRINE": "arudha-lordship",
    "JAI.ARUDHA.DHANA_A2_A11": "wealth-padas",
    "JAI.ARUDHA.A7_UL_ALIGNMENT": "family-ul",
    "JAI.KARAKAMSHA.BENEFIC_OCCUPANCY": "d9-karakamsha",
    "JAI.SWAMSA.BENEFIC_OCCUPANCY": "d9-swamsa",
}


def analyze_conflicts(rule_results: List[Any]) -> List[RuleConflict]:
    """Pairwise deterministic conflict analysis over rule results."""
    by_id = {r.rule_id: r for r in rule_results}
    conflicts: List[RuleConflict] = []
    for (a, b, proposition) in sorted(SAME_PROPOSITION_PAIRS):
        ra, rb = by_id.get(a), by_id.get(b)
        if ra is None or rb is None:
            continue
        # 5F UNKNOWN semantics: formation_status == UNCERTAIN (formed=False).
        if ra.formation_status == FormationStatus.UNCERTAIN or \
                rb.formation_status == FormationStatus.UNCERTAIN:
            conflicts.append(RuleConflict(
                rule_a=a, rule_b=b, conflict_class=INSUFFICIENT_INFORMATION,
                same_proposition=True,
                detail=f"{proposition}; undecidable while a participant is UNKNOWN."))
            continue
        if ra.formed and rb.formed and {a, b} == {
                "JAI.KARAKA.AK_AMK_CONJUNCTION", "JAI.DRISHTI.AK_AMK_MUTUAL"}:
            conflicts.append(RuleConflict(
                rule_a=a, rule_b=b, conflict_class=DIRECT_CONTRADICTION,
                same_proposition=True,
                detail=f"{proposition}; both FORMED is definitionally impossible — integrity alarm."))
        elif getattr(ra, "origin_label", None) != getattr(rb, "origin_label", None):
            conflicts.append(RuleConflict(
                rule_a=a, rule_b=b, conflict_class=TRADITION_VARIANT,
                same_proposition=True,
                detail=f"{proposition}; viewed under different origin labels "
                       f"({getattr(ra, 'origin_label', '?')} vs {getattr(rb, 'origin_label', '?')})."))
        else:
            conflicts.append(RuleConflict(
                rule_a=a, rule_b=b, conflict_class=DIFFERENT_DIMENSIONS,
                same_proposition=True,
                detail=f"{proposition}; distinct conditions, no contradiction "
                       f"(formed={ra.formed}/{rb.formed})."))
    return sorted(conflicts, key=lambda c: (c.rule_a, c.rule_b))
