"""
Phase 5F — explicit Jaimini rule dependency declarations.

Dependencies are metadata, not hidden inside evaluator code. Every 5E rule
declares what it consumes; the integration layer enforces the declarations
(UNKNOWN on missing inputs, rejection of undeclared Varga/strength access).

Dependency types: FACT (canonical upstream) | DERIVED_FACT (5D engine output)
| RULE_RESULT (another rule's outcome — none in the 5E catalogue; supported
for future use with cycle detection).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


FACT = "FACT"
DERIVED_FACT = "DERIVED_FACT"
RULE_RESULT = "RULE_RESULT"


@dataclass(frozen=True)
class RuleDependency:
    rule_id: str
    dependency_type: str
    fact_path: str
    required: bool
    description: str


@dataclass(frozen=True)
class RuleDependencySpec:
    rule_id: str
    dependencies: List[RuleDependency] = field(default_factory=list)
    varga_dependencies: List[str] = field(default_factory=list)
    strength_dependencies: List[str] = field(default_factory=list)
    origin_label: str = "TRADITION_DEPENDENT"


def _dep(rule_id: str, dtype: str, path: str, required: bool, desc: str) -> RuleDependency:
    return RuleDependency(rule_id, dtype, path, required, desc)


_CHART = "ChartFacts.planets[D1]"
_KAR = "JaiminiFacts.chara_karakas"
_DRI = "JaiminiFacts.rashi_drishti"
_AL = "JaiminiFacts.arudha_padas[1]"
_A2 = "JaiminiFacts.arudha_padas[2]"
_A7 = "JaiminiFacts.arudha_padas[7]"
_A11 = "JaiminiFacts.arudha_padas[11]"
_UL = "JaiminiFacts.upapada"
_KAK = "JaiminiFacts.karakamsha"
_D9 = "varga_facts.D9"


DEPENDENCY_SPECS: Dict[str, RuleDependencySpec] = {}


def _register(rule_id: str, origin: str, deps: List[tuple],
              varga: Optional[List[str]] = None,
              strength: Optional[List[str]] = None) -> None:
    DEPENDENCY_SPECS[rule_id] = RuleDependencySpec(
        rule_id=rule_id,
        dependencies=[_dep(rule_id, t, p, r, d) for (t, p, r, d) in deps],
        varga_dependencies=list(varga or []),
        strength_dependencies=list(strength or []),
        origin_label=origin,
    )


_register("JAI.KARAKA.AK_AMK_CONJUNCTION", "CLASSICAL_JAIMINI", [
    (FACT, _CHART, True, "D1 signs of AK/AmK planets"),
    (DERIVED_FACT, _KAR, True, "AK and AmK assignments"),
    (DERIVED_FACT, _DRI, False, "supporting benefic-drishti mitigation context"),
])
_register("JAI.KARAKA.AK_KENDRA_FROM_AL", "TRADITION_DEPENDENT", [
    (FACT, _CHART, False, "benefic-support mitigation context"),
    (DERIVED_FACT, _KAR, True, "AK assignment"),
    (DERIVED_FACT, _AL, True, "AL final sign"),
    (DERIVED_FACT, _DRI, False, "supporting benefic-drishti mitigation context"),
])
_register("JAI.KARAKA.DK_UL_SAMBANDHA", "TRADITION_DEPENDENT", [
    (FACT, _CHART, True, "D1 signs of DK and UL lord"),
    (DERIVED_FACT, _KAR, True, "DK assignment"),
    (DERIVED_FACT, _UL, True, "UL final sign"),
    (DERIVED_FACT, _DRI, True, "mutual-drishti mode evaluation"),
])
_register("JAI.DRISHTI.AK_AMK_MUTUAL", "CLASSICAL_JAIMINI", [
    (DERIVED_FACT, _KAR, True, "AK and AmK assignments"),
    (DERIVED_FACT, _DRI, True, "mutual-drishti evaluation"),
])
_register("JAI.DRISHTI.AMK_ON_AL", "TRADITION_DEPENDENT", [
    (DERIVED_FACT, _KAR, True, "AmK assignment"),
    (DERIVED_FACT, _AL, True, "AL final sign"),
    (DERIVED_FACT, _DRI, True, "planet_aspects evaluation"),
])
_register("JAI.DRISHTI.AK_ON_AL", "TRADITION_DEPENDENT", [
    (DERIVED_FACT, _KAR, True, "AK assignment"),
    (DERIVED_FACT, _AL, True, "AL final sign"),
    (DERIVED_FACT, _DRI, True, "planet_aspects evaluation"),
])
_register("JAI.ARUDHA.AL_BENEFIC_OCCUPANCY", "CLASSICAL_JAIMINI", [
    (FACT, _CHART, True, "D1 occupants of AL"),
    (DERIVED_FACT, _AL, True, "AL final sign"),
    (DERIVED_FACT, _DRI, False, "supporting benefic-drishti mitigation context"),
])
_register("JAI.ARUDHA.AL_LORD_KENDRA_TRINE", "CLASSICAL_JAIMINI", [
    (FACT, _CHART, True, "D1 sign of AL lord"),
    (DERIVED_FACT, _AL, True, "AL final sign and house lord"),
    (DERIVED_FACT, _DRI, False, "supporting benefic-drishti mitigation context"),
])
_register("JAI.ARUDHA.DHANA_A2_A11", "CLASSICAL_JAIMINI", [
    (DERIVED_FACT, _A2, True, "A2 final sign"),
    (DERIVED_FACT, _A11, True, "A11 final sign"),
    (DERIVED_FACT, _DRI, True, "mutual-drishti mode evaluation"),
])
_register("JAI.ARUDHA.A7_UL_ALIGNMENT", "TRADITION_DEPENDENT", [
    (DERIVED_FACT, _A7, True, "A7 final sign"),
    (DERIVED_FACT, _UL, True, "UL final sign"),
])
_register("JAI.KARAKAMSHA.BENEFIC_OCCUPANCY", "TRADITION_DEPENDENT", [
    (DERIVED_FACT, _KAK, True, "Karakamsha sign"),
    (DERIVED_FACT, _KAR, True, "AK identity"),
    (FACT, _D9, True, "D9 occupants of Karakamsha sign"),
], varga=["D9"])
_register("JAI.SWAMSA.BENEFIC_OCCUPANCY", "TRADITION_DEPENDENT", [
    (DERIVED_FACT, _KAK, True, "Swamsa (D9 Lagna) sign"),
    (FACT, _D9, True, "D9 occupants of Swamsa sign"),
], varga=["D9"])


def get_dependency_spec(rule_id: str) -> RuleDependencySpec:
    spec = DEPENDENCY_SPECS.get(rule_id)
    if spec is None:
        raise KeyError(f"No dependency spec for rule {rule_id}")
    return spec


def dependency_covered(declared_paths: List[str], used_path: str) -> bool:
    """Coverage check: exact match, or the used path is a parent collection of
    a declared indexed path (e.g. declared 'JaiminiFacts.arudha_padas[1]'
    covers used 'JaiminiFacts.arudha_padas')."""
    if used_path in declared_paths:
        return True
    prefix = used_path + "["
    return any(p.startswith(prefix) for p in declared_paths)


def detect_dependency_cycles(specs: Optional[Dict[str, RuleDependencySpec]] = None) -> List[List[str]]:
    """Detect cycles among RULE_RESULT edges. Returns list of cycles (each a
    list of rule IDs). The 5E catalogue declares none, so production use must
    return []."""
    specs = specs if specs is not None else DEPENDENCY_SPECS
    edges: Dict[str, List[str]] = {}
    for rid, spec in specs.items():
        targets = []
        for dep in spec.dependencies:
            if dep.dependency_type == RULE_RESULT:
                targets.append(dep.fact_path)
        edges[rid] = sorted(targets)
    cycles: List[List[str]] = []
    visited: Dict[str, int] = {}

    def visit(node: str, stack: List[str]) -> None:
        visited[node] = 1
        stack.append(node)
        for nxt in edges.get(node, []):
            if nxt not in visited:
                visit(nxt, stack)
            elif visited.get(nxt) == 1:
                cycles.append(stack[stack.index(nxt):] + [nxt])
        stack.pop()
        visited[node] = 2

    for rid in sorted(edges):
        if rid not in visited:
            visit(rid, [])
    return sorted(cycles)
