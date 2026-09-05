"""
Phase 8 — declarative event definitions (§4).

Each definition wires an event category to ACCEPTED rule IDs (never invented
rules). Formation policy ANY: any listed rule FORMED -> formation FORMED; all
NOT_FORMED -> NOT_FORMED; otherwise UNKNOWN (missing is never negative
evidence). Definitions without accepted-rule coverage honestly yield
INSUFFICIENT_RULE_COVERAGE via the formation engine.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from . import event_types as ET


class EventDefinition(BaseModel):
    event_id: str
    category: str
    name: str = ""
    description: str = ""
    tradition_constraints: List[str] = Field(default_factory=list)
    required_rule_families: List[str] = Field(default_factory=list)
    required_activation_signals: List[str] = Field(default_factory=list)
    optional_activation_signals: List[str] = Field(default_factory=list)
    exclusion_signals: List[str] = Field(default_factory=list)
    timing_requirements: List[str] = Field(default_factory=list)
    evidence_requirements: List[str] = Field(default_factory=list)
    formation_policy: str = "ANY"
    version: str = "1.0.0"
    lifecycle: str = "ACTIVE"

    model_config = {"frozen": True, "extra": "forbid"}


def _define(event_id: str, category: str, name: str, traditions: List[str],
            required: List[str], exclusion: List[str],
            version: str = "1.0.0", lifecycle: str = "ACTIVE") -> EventDefinition:
    return EventDefinition(
        event_id=event_id, category=category, name=name,
        description=f"Declarative wiring of {category} to accepted rule IDs; "
                    f"no astrology defined here.",
        tradition_constraints=traditions, required_rule_families=required,
        required_activation_signals=["DASHA_SIGNAL"],
        optional_activation_signals=["TRANSIT_SIGNAL", "JAIMINI_DASHA_SIGNAL"],
        exclusion_signals=exclusion,
        timing_requirements=["DASHA_RANGE"], evidence_requirements=[],
        version=version, lifecycle=lifecycle)


DEFINITIONS: Dict[str, EventDefinition] = {}


def _register(defn: EventDefinition) -> None:
    DEFINITIONS[f"{defn.event_id}@{defn.version}"] = defn


_register(_define("EV.MARRIAGE.V1", ET.MARRIAGE, "Marriage timing candidate",
                  ["JAIMINI_CLASSICAL"],
                  ["JAI.ARUDHA.A7_UL_ALIGNMENT", "JAI.KARAKA.DK_UL_SAMBANDHA"],
                  ["DOSHA.MANGLIK.LAGNA_CLASSICAL", "DOSHA.MANGLIK.MOON_REFERENCE",
                   "DOSHA.MANGLIK.VENUS_REFERENCE"]))
_register(_define("EV.RELATIONSHIP.V1", ET.RELATIONSHIP, "Relationship timing candidate",
                  ["JAIMINI_CLASSICAL"],
                  ["JAI.KARAKA.DK_UL_SAMBANDHA", "JAI.ARUDHA.A7_UL_ALIGNMENT",
                   "JAI.DRISHTI.AMK_ON_AL", "JAI.DRISHTI.AK_ON_AL"],
                  []))
_register(_define("EV.WEALTH.V1", ET.FINANCE, "Wealth timing candidate",
                  ["PARASHARI_CLASSICAL", "JAIMINI_CLASSICAL"],
                  ["PARASHARI.YOGA.DHANA_2_11", "PARASHARI.YOGA.DHANA_5_9",
                   "PARASHARI.YOGA.DHANA_LAGNA_WEALTH",
                   "JAI.ARUDHA.DHANA_A2_A11"],
                  []))
_register(_define("EV.CAREER.V1", ET.CAREER, "Career timing candidate",
                  ["PARASHARI_CLASSICAL"],
                  ["PARASHARI.YOGA.RAJA_KENDRA_TRIKONA",
                   "PARASHARI.YOGA.DHARMA_KARMADHIPATI",
                   "PARASHARI.YOGA.YOGAKARAKA_RAJA"],
                  []))
_register(_define("EV.CAREER.V1", ET.CAREER, "Career timing candidate (extended rule set)",
                  ["PARASHARI_CLASSICAL"],
                  ["PARASHARI.YOGA.RAJA_KENDRA_TRIKONA",
                   "PARASHARI.YOGA.DHARMA_KARMADHIPATI",
                   "PARASHARI.YOGA.YOGAKARAKA_RAJA",
                   "PARASHARI.YOGA.AMALA"],
                  [], version="1.1.0"))
_register(_define("EV.EDUCATION.V1", ET.EDUCATION, "Education timing candidate",
                  ["PARASHARI_CLASSICAL"],
                  ["PARASHARI.YOGA.SARASWATI", "PARASHARI.YOGA.BUDHA_ADITYA"],
                  []))
_register(_define("EV.HEALTH.V1", ET.HEALTH, "Health timing candidate",
                  ["PARASHARI_CLASSICAL"], [], []))
_register(_define("EV.CUSTOM.V1", ET.OTHER, "Developer-rule demonstration candidate",
                  ["CUSTOM_DEVELOPER"], ["CUSTOM.NATAL.TEST"], []))


def get_event_definition(event_id: str, version: Optional[str] = None) -> EventDefinition:
    """Exact version when given; latest ACTIVE otherwise (explicit, never silent)."""
    if version is not None:
        definition = DEFINITIONS.get(f"{event_id}@{version}")
        if definition is None:
            raise KeyError(f"Unknown event {event_id}@{version}")
        return definition
    candidates = [d for d in DEFINITIONS.values()
                  if d.event_id == event_id and d.lifecycle == "ACTIVE"]
    if not candidates:
        raise KeyError(f"Unknown event {event_id!r}")
    return sorted(candidates, key=lambda d: _version_tuple(d.version))[-1]


def list_event_definitions(lifecycle: Optional[str] = None) -> List[EventDefinition]:
    definitions = list(DEFINITIONS.values())
    if lifecycle is not None:
        definitions = [d for d in definitions if d.lifecycle == lifecycle]
    return sorted(definitions, key=lambda d: (d.event_id, _version_tuple(d.version)))


def list_event_versions(event_id: str) -> List[str]:
    return sorted({d.version for d in DEFINITIONS.values() if d.event_id == event_id},
                  key=_version_tuple)


def _version_tuple(version: str) -> tuple:
    try:
        return tuple(int(x) for x in version.split("-")[0].split("."))
    except ValueError:
        return (0, 0, 0)
