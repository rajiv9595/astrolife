"""
Phase 6B — canonical fact namespace.

Machine-readable path patterns. A declared input_fact must match one pattern;
anything else fails dependency validation. Follows existing project naming
(RuleContext accessors, VargaPosition keys, JaiminiFacts fields).
"""
from __future__ import annotations

import re
from typing import Dict, List

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
           "Rahu", "Ketu"]
VARGAS = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20",
          "D24", "D27", "D30", "D40", "D45", "D60"]
KARAKAS = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK", "PiK"]
DASHA_SYSTEMS = ["vimshottari", "jaimini"]
STRENGTH_METRICS = ["shadbala", "bhava", "vimsopaka", "avastha", "dignity",
                    "functional", "composite"]

# pattern -> (source_layer, description)
NAMESPACE: Dict[str, tuple] = {
    r"natal\.ascendant\.(sign|degree)": ("ChartFacts", "Ascendant sign/degree"),
    r"natal\.(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\.(sign|longitude|house|degree|nakshatra|pada|retrograde)": ("ChartFacts", "Natal planet fact"),
    r"houses\.\d+\.(sign|lord)": ("ChartFacts", "House sign/lord"),
    r"varga\.(D1|D2|D3|D4|D7|D9|D10|D12|D16|D20|D24|D27|D30|D40|D45|D60)\.(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)": ("VargaFacts", "Varga sign"),
    r"strength\.(shadbala|bhava|vimsopaka|avastha|dignity|functional|composite)\.[A-Za-z]+": ("StrengthReport", "Strength fact"),
    r"dasha\.(vimshottari|jaimini)\.(mahadasha|antardasha|active_sign|profile|period_id)": ("DashaTimeline", "Dasha fact"),
    r"transit\.(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\.(sign|longitude|house)": ("TransitSnapshot", "Transit fact"),
    r"jaimini\.karaka\.(AK|AmK|BK|MK|PK|GK|DK|PiK)": ("JaiminiFacts", "Chara karaka planet"),
    r"jaimini\.drishti": ("JaiminiFacts", "Rashi drishti map"),
    r"jaimini\.pada\.\d+": ("JaiminiFacts", "Arudha pada final"),
    r"jaimini\.karakamsha": ("JaiminiFacts", "Karakamsha sign"),
    r"jaimini\.swamsa": ("JaiminiFacts", "Swamsa sign"),
    r"aspects\.(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)": ("RuleContext", "Parashari aspect list"),
}

_COMPILED = [(re.compile(p), meta) for p, meta in NAMESPACE.items()]


def match_namespace(path: str):
    """Return (source_layer, description) or None for a fact path."""
    for rx, meta in _COMPILED:
        if rx.fullmatch(path):
            return meta
    return None


def namespace_of(path: str) -> str:
    m = match_namespace(path)
    return m[0] if m else "UNKNOWN"


def list_namespaces() -> List[str]:
    return sorted(NAMESPACE.keys())
