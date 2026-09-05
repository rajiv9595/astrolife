"""
Phase 6A — validators for dynamic rules. Structured, machine-readable
diagnostics (no generic unstructured throws). Covers schema, identity,
conditions, vocabularies, provenance, dependencies, cycles, firewall,
code-payload, and version rules.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from .dsl import LOGICAL_OPS, PRIMITIVES, find_suspicious_text, known_ops
from .schema import DynamicRuleDefinition

PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
           "Rahu", "Ketu"}
SIGNS = {"Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"}
VARGAS = {"D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20",
          "D24", "D27", "D30", "D40", "D45", "D60"}
TRADITIONS = {"PARASHARI_CLASSICAL", "JAIMINI_CLASSICAL", "TRADITION_DEPENDENT",
              "MODERN_COMMON", "WESTERN", "CUSTOM_DEVELOPER"}
VERIFICATION = {"VERIFIED", "UNVERIFIED", "CONTESTED", "SECONDARY",
                "TRADITIONAL", "USER_SUPPLIED", "CUSTOM"}
KARAKAS = {"AK", "AmK", "BK", "MK", "PK", "GK", "DK", "PiK"}
STATUSES = {"ACTIVE", "DEPRECATED", "SUPERSEDED", "DRAFT", "VALIDATED", "TESTED", "REVIEW_PENDING", "DISABLED", "ARCHIVED", "REJECTED"}
VALIDATION_STATUSES = {"UNVALIDATED", "VALID", "INVALID", "NEEDS_REVIEW"}

# Tradition firewall: namespaces a rule of a given tradition may read.
# Everything else fails validation. Cross-tradition reads must be declared
# under an explicit hybrid tradition (not creatable silently here).
FIREWALL: Dict[str, Set[str]] = {
    "PARASHARI_CLASSICAL": {"natal", "houses", "varga", "dignity", "aspects",
                            "dasha", "transit", "strength", "rule"},
    "JAIMINI_CLASSICAL": {"natal", "houses", "jaimini", "varga", "dasha",
                          "transit", "rule"},
    "TRADITION_DEPENDENT": {"natal", "houses", "jaimini", "varga", "dignity",
                            "aspects", "dasha", "transit", "strength", "rule"},
    "MODERN_COMMON": {"natal", "houses", "varga", "transit", "rule"},
    "WESTERN": {"natal", "houses", "transit", "rule"},
    "CUSTOM_DEVELOPER": {"natal", "houses", "jaimini", "varga", "dignity",
                         "aspects", "dasha", "transit", "strength", "rule"},
}

_SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$")
_RULE_ID = re.compile(r"^[A-Z0-9_]+(\.[A-Z0-9_]+)+$")


class Diagnostic(BaseModel):
    code: str
    path: str
    message: str
    severity: str = "ERROR"
    model_config = {"frozen": True}


def _walk_tree(node: Any, path: str, out: List):
    out.append((node, path))
    for i, c in enumerate(getattr(node, "children", []) or []):
        _walk_tree(c, f"{path}.children[{i}]", out)


def _scan_strings(value: Any, path: str, diags: List[Diagnostic]) -> None:
    if isinstance(value, str):
        for pat in find_suspicious_text(value):
            diags.append(Diagnostic(code="ARBITRARY_CODE", path=path,
                                    message=f"Suspicious payload pattern {pat!r}"))
    elif isinstance(value, dict):
        for k, v in sorted(value.items()):
            _scan_strings(v, f"{path}.{k}", diags)
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            _scan_strings(v, f"{path}[{i}]", diags)


def validate_rule(rule: DynamicRuleDefinition,
                  known_rule_ids: Optional[Set[str]] = None) -> List[Diagnostic]:
    """Full validation. Returns sorted diagnostics (empty = valid)."""
    diags: List[Diagnostic] = []
    known_rule_ids = known_rule_ids or set()
    rid = rule.identity.rule_id

    # identity / versioning
    if not rid or not _RULE_ID.match(rid):
        diags.append(Diagnostic(code="SCHEMA", path="identity.rule_id",
                                message="rule_id must be DOT.SEPARATED.UPPERCASE"))
    if not _SEMVER.match(rule.identity.rule_version or ""):
        diags.append(Diagnostic(code="VERSION", path="identity.rule_version",
                                message="rule_version must be semver X.Y.Z"))
    if not rule.identity.rule_name:
        diags.append(Diagnostic(code="SCHEMA", path="identity.rule_name",
                                message="rule_name is required"))
    if rule.schema_version != "6A/1.0.0":
        diags.append(Diagnostic(code="SCHEMA", path="schema_version",
                                message="schema_version must be 6A/1.0.0"))

    # classification
    if rule.classification.tradition not in TRADITIONS:
        diags.append(Diagnostic(code="TRADITION", path="classification.tradition",
                                message=f"Unknown tradition; allowed {sorted(TRADITIONS)}"))
    for f, p in (("system", "classification.system"), ("category", "classification.category")):
        if not getattr(rule.classification, f):
            diags.append(Diagnostic(code="SCHEMA", path=p, message=f"{f} is required"))

    # provenance / source
    src = rule.provenance.source_reference
    if src.verification_status not in VERIFICATION:
        diags.append(Diagnostic(code="PROVENANCE", path="provenance.source_reference.verification_status",
                                message=f"Unknown verification state; allowed {sorted(VERIFICATION)}"))
    if src.verification_status == "VERIFIED" and not (src.locator or src.quotation):
        diags.append(Diagnostic(code="PROVENANCE", path="provenance.source_reference",
                                message="VERIFIED requires locator or quotation evidence"))
    if not rule.provenance.confidence:
        diags.append(Diagnostic(code="PROVENANCE", path="provenance.confidence",
                                message="confidence is required"))
    if rule.provenance.provenance_status not in VERIFICATION and rule.provenance.provenance_status != "":
        diags.append(Diagnostic(code="PROVENANCE", path="provenance.provenance_status",
                                message=f"Unknown provenance status; allowed {sorted(VERIFICATION)}"))

    # condition trees
    for label in ("formation", "cancellation", "mitigation"):
        tree = getattr(rule.semantics, label)
        if tree is None:
            continue
        nodes: List = []
        _walk_tree(tree, f"semantics.{label}", nodes)
        for node, path in nodes:
            if node.op not in known_ops():
                diags.append(Diagnostic(code="CONDITION", path=f"{path}.op",
                                        message=f"Unknown op {node.op!r}"))
                continue
            if node.op in LOGICAL_OPS:
                if node.op == "NOT" and len(node.children) != 1:
                    diags.append(Diagnostic(code="CONDITION", path=path,
                                            message="NOT requires exactly 1 child"))
                if node.op in ("EXACTLY_N", "AT_LEAST_N", "AT_MOST_N"):
                    if node.n is None or node.n < 0 or node.n > len(node.children):
                        diags.append(Diagnostic(code="CONDITION", path=path,
                                                message=f"{node.op} needs 0 <= n <= children"))
                if node.op in ("ALL", "ANY") and not node.children:
                    diags.append(Diagnostic(code="CONDITION", path=path,
                                            message=f"{node.op} needs >= 1 child"))
            else:
                want = PRIMITIVES[node.op]
                for p in want:
                    if p not in node.params:
                        diags.append(Diagnostic(code="CONDITION", path=f"{path}.params",
                                                message=f"{node.op} missing param {p!r}"))
                for p in node.params:
                    if p not in want:
                        diags.append(Diagnostic(code="CONDITION", path=f"{path}.params",
                                                message=f"{node.op} unknown param {p!r}",
                                                severity="WARNING"))
                _check_vocab(node.op, node.params, path, diags)

    # lifecycle
    if rule.lifecycle.status not in STATUSES:
        diags.append(Diagnostic(code="LIFECYCLE", path="lifecycle.status",
                                message=f"Unknown status; allowed {sorted(STATUSES)}"))
    if rule.validation.validation_status not in VALIDATION_STATUSES:
        diags.append(Diagnostic(code="LIFECYCLE", path="validation.validation_status",
                                message=f"Unknown validation status; allowed {sorted(VALIDATION_STATUSES)}"))

    # dependencies: declared rule deps must exist; firewall on fact namespaces
    for dep in rule.dependencies.rule_dependencies:
        if dep not in known_rule_ids:
            diags.append(Diagnostic(code="DEPENDENCY", path="dependencies.rule_dependencies",
                                    message=f"Unknown rule dependency {dep!r}"))
    allowed_ns = FIREWALL.get(rule.classification.tradition, set())
    for lst_name in ("input_facts", "varga_dependencies", "dasha_dependencies",
                     "transit_dependencies", "strength_dependencies"):
        for dep in getattr(rule.dependencies, lst_name):
            ns = dep.split(".")[0].split(":")[0]
            # varga/dasha/transit/strength lists map to their namespaces
            ns_map = {"input_facts": ns, "varga_dependencies": "varga",
                      "dasha_dependencies": "dasha", "transit_dependencies": "transit",
                      "strength_dependencies": "strength"}
            if ns_map[lst_name] not in allowed_ns:
                diags.append(Diagnostic(code="FIREWALL", path=f"dependencies.{lst_name}",
                                        message=f"{rule.classification.tradition} may not read {ns_map[lst_name]}.*"))
    # cycle detection over rule_dependencies
    if _has_cycle(rid, rule.dependencies.rule_dependencies, known_rule_ids):
        diags.append(Diagnostic(code="CYCLE", path="dependencies.rule_dependencies",
                                message="Dependency cycle detected"))

    # arbitrary-code scan over the whole definition
    _scan_strings(rule.model_dump(mode="json"), "rule", diags)

    return sorted(diags, key=lambda d: (d.code, d.path, d.message))


def _check_vocab(op: str, params: Dict[str, Any], path: str, diags: List[Diagnostic]) -> None:
    def planet(p: str) -> None:
        if params.get(p) not in PLANETS:
            diags.append(Diagnostic(code="VOCABULARY", path=f"{path}.params.{p}",
                                    message=f"Unknown planet {params.get(p)!r}"))
    def sign(p: str) -> None:
        if params.get(p) not in SIGNS:
            diags.append(Diagnostic(code="VOCABULARY", path=f"{path}.params.{p}",
                                    message=f"Unknown sign {params.get(p)!r}"))
    def house(p: str) -> None:
        h = params.get(p)
        if not isinstance(h, int) or not (1 <= h <= 12):
            diags.append(Diagnostic(code="VOCABULARY", path=f"{path}.params.{p}",
                                    message=f"House must be int 1..12, got {h!r}"))
    if op in ("planet_in_sign",):
        planet("planet")
        sign("sign")
    elif op == "planet_in_house":
        planet("planet")
        house("house")
    elif op == "planet_in_varga_sign":
        planet("planet")
        sign("sign")
        if params.get("varga") not in VARGAS:
            diags.append(Diagnostic(code="VOCABULARY", path=f"{path}.params.varga",
                                    message=f"Unknown varga {params.get('varga')!r}"))
    elif op in ("planet_owns_house", "lord_of_house"):
        planet("planet") if "planet" in params else None
        house("house")
    elif op == "planets_conjunct":
        planet("a")
        planet("b")
    elif op == "planets_aspect":
        planet("a")
        planet("b")
    elif op == "rashi_drishti":
        sign("from_sign")
        sign("to_sign")
    elif op == "karaka_equals":
        if params.get("karaka") not in KARAKAS:
            diags.append(Diagnostic(code="VOCABULARY", path=f"{path}.params.karaka",
                                    message=f"Unknown karaka {params.get('karaka')!r}"))
        planet("planet")
    elif op == "pada_equals":
        house("house")
        sign("sign")
    elif op in ("planet_exalted", "planet_debilitated", "planet_in_own_sign",
                "planet_in_moolatrikona", "strength_threshold"):
        planet("planet")
    elif op in ("house_is_kendra", "house_is_trikona"):
        house("house")
    elif op == "lord_in_house":
        house("house")
        house("target_house")
    elif op == "dasha_active":
        # Active key is a lord for Vimshottari, a sign for Jaimini Chara:
        # accept either vocabulary explicitly.
        if params.get("sign") not in SIGNS and params.get("sign") not in PLANETS:
            diags.append(Diagnostic(code="VOCABULARY", path=f"{path}.params.sign",
                                    message=f"dasha_active key must be a planet (Vimshottari lord) or sign (Jaimini), got {params.get('sign')!r}"))
    elif op == "transit_in_sign":
        planet("planet")
        sign("sign")
    elif op == "transit_conjunct_natal":
        planet("transit_planet")
        planet("natal_planet")


def _has_cycle(rule_id: str, deps: List[str], known: Set[str]) -> bool:
    # Single-level check available here (multi-level needs a rule map; the
    # registry-level check lives in registry.validate_graph).
    return rule_id in (deps or [])


def compare_versions(a: str, b: str) -> int:
    """Deterministic semver compare: -1 | 0 | 1 (ignores pre-release tag)."""
    def parts(v: str):
        core = v.split("-")[0]
        return tuple(int(x) for x in core.split("."))
    pa, pb = parts(a), parts(b)
    return (pa > pb) - (pa < pb)
