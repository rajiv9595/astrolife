"""
Phase 6C — Dependency and Evidence Previews.

Provides declarative inspection of a dynamic rule's dependencies and evidence paths:
  preview_rule_dependencies(rule_or_pkg) -> DependencyPreview
  preview_rule_evidence(rule_or_pkg) -> EvidencePreview

Inspection only — no calculation, no prediction, no interpretation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .bindings import required_paths
from .namespace import namespace_of
from .rule_package import RulePackage
from .schema import ConditionNode, DynamicRuleDefinition


class DependencyPreview(BaseModel):
    """Structured inspection of a rule's dependencies."""
    rule_id: str
    version: str
    direct_facts: List[str]
    varga_dependencies: List[str]
    dasha_dependencies: List[str]
    transit_dependencies: List[str]
    strength_dependencies: List[str]
    jaimini_dependencies: List[str]
    rule_dependencies: List[str]
    dependency_graph: Dict[str, List[str]]
    dependency_count: int
    undeclared_dependency_diagnostics: List[str]

    model_config = {"frozen": True}


class EvidenceChainItem(BaseModel):
    """Chain linking a rule node to canonical facts and sources."""
    tree: str
    node: str
    op: str
    facts: List[str]
    canonical_sources: List[str]

    model_config = {"frozen": True}


class DerivedFactChainItem(BaseModel):
    """Chain linking a derived fact to its source rule and underlying facts."""
    derived_fact: str
    source_rule: str
    underlying_facts: List[str]

    model_config = {"frozen": True}


class EvidencePreview(BaseModel):
    """Structured inspection of a rule's evidence flow."""
    rule_id: str
    version: str
    evidence_chains: List[EvidenceChainItem]
    derived_fact_chains: List[DerivedFactChainItem]

    model_config = {"frozen": True}


def _extract_tree_paths(node: Optional[ConditionNode]) -> List[str]:
    if node is None:
        return []
    paths = list(required_paths(node.op, node.params))
    for child in node.children or []:
        paths.extend(_extract_tree_paths(child))
    return paths


def _is_covered(needed: str, declared: List[str]) -> bool:
    if needed in declared:
        return True
    return any(needed == d or needed.startswith(d.rstrip("*")) for d in declared)


def preview_rule_dependencies(
    rule_or_pkg: Union[DynamicRuleDefinition, RulePackage],
) -> DependencyPreview:
    """Preview declared and required dependencies for a rule.

    Does not infer or silently add dependencies. Exposes undeclared dependencies.
    """
    rule = rule_or_pkg.rule if isinstance(rule_or_pkg, RulePackage) else rule_or_pkg
    rid = rule.identity.rule_id
    ver = rule.identity.rule_version

    # Collect needed paths from semantics trees
    needed: List[str] = []
    for tree in (rule.semantics.formation, rule.semantics.cancellation, rule.semantics.mitigation):
        needed.extend(_extract_tree_paths(tree))
    needed_sorted = sorted(set(needed))

    declared_inputs = sorted(rule.dependencies.input_facts or [])
    declared_rules = sorted(rule.dependencies.rule_dependencies or [])
    declared_vargas = sorted(rule.dependencies.varga_dependencies or [])
    declared_dashas = sorted(rule.dependencies.dasha_dependencies or [])
    declared_transits = sorted(rule.dependencies.transit_dependencies or [])
    declared_strengths = sorted(rule.dependencies.strength_dependencies or [])

    all_declared = sorted(
        set(declared_inputs)
        | {f"rule:{r}" for r in declared_rules}
        | set(declared_rules)
    )

    undeclared = [
        f"UNDECLARED_DEPENDENCY:{p}"
        for p in needed_sorted
        if not _is_covered(p, all_declared)
    ]

    # Partition needed facts by root namespace
    direct_facts = [p for p in needed_sorted if p.startswith("natal.")]
    vargas = [p for p in needed_sorted if p.startswith("varga.")]
    dashas = [p for p in needed_sorted if p.startswith("dasha.")]
    transits = [p for p in needed_sorted if p.startswith("transit.")]
    strengths = [p for p in needed_sorted if p.startswith("strength.")]
    jaiminis = [p for p in needed_sorted if p.startswith("jaimini.")]
    rule_deps = [p[len("rule:"):] if p.startswith("rule:") else p for p in needed_sorted if "rule" in p]

    dep_graph = {
        rid: sorted(set(declared_inputs + [f"rule:{r}" for r in declared_rules]))
    }

    all_distinct = set(declared_inputs) | set(declared_rules) | set(declared_vargas) | set(declared_dashas) | set(declared_transits) | set(declared_strengths)

    return DependencyPreview(
        rule_id=rid,
        version=ver,
        direct_facts=direct_facts,
        varga_dependencies=vargas or declared_vargas,
        dasha_dependencies=dashas or declared_dashas,
        transit_dependencies=transits or declared_transits,
        strength_dependencies=strengths or declared_strengths,
        jaimini_dependencies=jaiminis,
        rule_dependencies=declared_rules,
        dependency_graph=dep_graph,
        dependency_count=len(all_distinct),
        undeclared_dependency_diagnostics=undeclared,
    )


def preview_rule_evidence(
    rule_or_pkg: Union[DynamicRuleDefinition, RulePackage],
) -> EvidencePreview:
    """Preview the evidence mapping from conditions to facts to canonical sources."""
    rule = rule_or_pkg.rule if isinstance(rule_or_pkg, RulePackage) else rule_or_pkg
    rid = rule.identity.rule_id
    ver = rule.identity.rule_version

    evidence_chains: List[EvidenceChainItem] = []

    def _traverse_tree(node: Optional[ConditionNode], tree_label: str, prefix: str = "") -> None:
        if node is None:
            return
        node_id = f"{prefix}{node.op}"
        paths = sorted(required_paths(node.op, node.params))
        canonical_srcs = sorted({namespace_of(p) or "UNKNOWN" for p in paths})

        evidence_chains.append(
            EvidenceChainItem(
                tree=tree_label,
                node=node_id,
                op=node.op,
                facts=paths,
                canonical_sources=canonical_srcs,
            )
        )

        for i, child in enumerate(node.children or []):
            _traverse_tree(child, tree_label, f"{node_id}.c{i}_")

    _traverse_tree(rule.semantics.formation, "formation", "f_")
    _traverse_tree(rule.semantics.cancellation, "cancellation", "c_")
    _traverse_tree(rule.semantics.mitigation, "mitigation", "m_")

    derived_chains: List[DerivedFactChainItem] = []
    underlying = sorted(rule.dependencies.input_facts or [])
    for df in sorted(rule.semantics.derived_facts or []):
        derived_chains.append(
            DerivedFactChainItem(
                derived_fact=df,
                source_rule=rid,
                underlying_facts=underlying,
            )
        )

    return EvidencePreview(
        rule_id=rid,
        version=ver,
        evidence_chains=evidence_chains,
        derived_fact_chains=derived_chains,
    )
