"""Phase 7 — agents package. Six specialized deterministic agents."""
from .parashari_agent import CONTRACT as PARASHARI_CONTRACT, build_draft as parashari_draft
from .jaimini_agent import CONTRACT as JAIMINI_CONTRACT, build_draft as jaimini_draft
from .strength_agent import CONTRACT as STRENGTH_CONTRACT, build_draft as strength_draft
from .yoga_dosha_agent import CONTRACT as YOGA_DOSHA_CONTRACT, build_draft as yoga_dosha_draft
from .timing_agent import CONTRACT as TIMING_CONTRACT, build_draft as timing_draft
from .chart_synthesis_agent import CONTRACT as SYNTHESIS_CONTRACT, build_draft as synthesis_draft

BUILDERS = {
    "PARASHARI_AGENT": parashari_draft,
    "JAIMINI_AGENT": jaimini_draft,
    "STRENGTH_AGENT": strength_draft,
    "YOGA_DOSHA_AGENT": yoga_dosha_draft,
    "TIMING_AGENT": timing_draft,
    "CHART_SYNTHESIS_AGENT": synthesis_draft,
}

__all__ = ["BUILDERS", "PARASHARI_CONTRACT", "JAIMINI_CONTRACT",
           "STRENGTH_CONTRACT", "YOGA_DOSHA_CONTRACT", "TIMING_CONTRACT",
           "SYNTHESIS_CONTRACT"]
