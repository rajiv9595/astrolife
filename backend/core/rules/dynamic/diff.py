"""
Phase 6C — Deterministic semantic diff between rule versions.

Output categories:
  ADDED_CONDITION, REMOVED_CONDITION, CHANGED_CONDITION
  ADDED_DEPENDENCY, REMOVED_DEPENDENCY
  CHANGED_PROVENANCE, CHANGED_TRADITION
  CHANGED_CANCELLATION, CHANGED_MITIGATION
  CHANGED_METADATA

Stable ordering required. Never simply returns "different".
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Set

from .rule_package import RuleDiff, RuleDiffCategory, RulePackage


def compare_rule_versions(
    base: RulePackage,
    target: RulePackage,
) -> RuleDiff:
    """Deterministic semantic diff between two RulePackages.

    Compares condition trees, dependencies, provenance, tradition,
    cancellation, mitigation, and metadata.
    """
    base_rule = base.rule
    target_rule = target.rule

    diff_map: Dict[str, List[str]] = {cat: [] for cat in RuleDiffCategory.ALL_CATEGORIES}

    # Compare formation condition
    base_f_hash = _tree_hash(base_rule.semantics.formation)
    target_f_hash = _tree_hash(target_rule.semantics.formation)
    if base_f_hash != target_f_hash:
        if base_rule.semantics.formation is None and target_rule.semantics.formation is not None:
            diff_map[RuleDiffCategory.ADDED_CONDITION].append("formation")
        elif base_rule.semantics.formation is not None and target_rule.semantics.formation is None:
            diff_map[RuleDiffCategory.REMOVED_CONDITION].append("formation")
        else:
            diff_map[RuleDiffCategory.CHANGED_CONDITION].append("formation")

    # Compare cancellation condition
    base_c_hash = _tree_hash(base_rule.semantics.cancellation)
    target_c_hash = _tree_hash(target_rule.semantics.cancellation)
    if base_c_hash != target_c_hash:
        diff_map[RuleDiffCategory.CHANGED_CANCELLATION].append(
            f"cancellation_hash:{base_c_hash[:8]}->{target_c_hash[:8]}"
        )

    # Compare mitigation condition
    base_m_hash = _tree_hash(base_rule.semantics.mitigation)
    target_m_hash = _tree_hash(target_rule.semantics.mitigation)
    if base_m_hash != target_m_hash:
        diff_map[RuleDiffCategory.CHANGED_MITIGATION].append(
            f"mitigation_hash:{base_m_hash[:8]}->{target_m_hash[:8]}"
        )

    # Compare dependencies
    base_inputs = set(base_rule.dependencies.input_facts or [])
    target_inputs = set(target_rule.dependencies.input_facts or [])
    for dep in sorted(target_inputs - base_inputs):
        diff_map[RuleDiffCategory.ADDED_DEPENDENCY].append(f"input_facts.{dep}")
    for dep in sorted(base_inputs - target_inputs):
        diff_map[RuleDiffCategory.REMOVED_DEPENDENCY].append(f"input_facts.{dep}")

    base_rule_deps = set(base_rule.dependencies.rule_dependencies or [])
    target_rule_deps = set(target_rule.dependencies.rule_dependencies or [])
    for dep in sorted(target_rule_deps - base_rule_deps):
        diff_map[RuleDiffCategory.ADDED_DEPENDENCY].append(f"rule_dependencies.{dep}")
    for dep in sorted(base_rule_deps - target_rule_deps):
        diff_map[RuleDiffCategory.REMOVED_DEPENDENCY].append(f"rule_dependencies.{dep}")

    for dep_type in ("varga_dependencies", "dasha_dependencies", "transit_dependencies", "strength_dependencies"):
        base_set = set(getattr(base_rule.dependencies, dep_type) or [])
        target_set = set(getattr(target_rule.dependencies, dep_type) or [])
        for dep in sorted(target_set - base_set):
            diff_map[RuleDiffCategory.ADDED_DEPENDENCY].append(f"{dep_type}.{dep}")
        for dep in sorted(base_set - target_set):
            diff_map[RuleDiffCategory.REMOVED_DEPENDENCY].append(f"{dep_type}.{dep}")

    # Compare provenance
    base_prov = base_rule.provenance
    target_prov = target_rule.provenance
    if base_prov.source_reference.verification_status != target_prov.source_reference.verification_status:
        diff_map[RuleDiffCategory.CHANGED_PROVENANCE].append(
            f"verification_status:{base_prov.source_reference.verification_status}->{target_prov.source_reference.verification_status}"
        )
    if base_prov.source_reference.source_id != target_prov.source_reference.source_id:
        diff_map[RuleDiffCategory.CHANGED_PROVENANCE].append(
            f"source_id:{base_prov.source_reference.source_id}->{target_prov.source_reference.source_id}"
        )
    if base_prov.confidence != target_prov.confidence:
        diff_map[RuleDiffCategory.CHANGED_PROVENANCE].append(
            f"confidence:{base_prov.confidence}->{target_prov.confidence}"
        )

    # Compare tradition
    if base.tradition != target.tradition:
        diff_map[RuleDiffCategory.CHANGED_TRADITION].append(
            f"tradition:{base.tradition}->{target.tradition}"
        )

    # Compare metadata
    if base.name != target.name:
        diff_map[RuleDiffCategory.CHANGED_METADATA].append(f"name:{base.name}->{target.name}")
    if base.description != target.description:
        diff_map[RuleDiffCategory.CHANGED_METADATA].append("description:modified")
    if base.category != target.category:
        diff_map[RuleDiffCategory.CHANGED_METADATA].append(f"category:{base.category}->{target.category}")

    # Ensure all lists are sorted for deterministic output
    for cat in RuleDiffCategory.ALL_CATEGORIES:
        diff_map[cat] = sorted(diff_map[cat])

    return RuleDiff(
        categories=diff_map,
        base_version=base.version,
        target_version=target.version,
        base_rule_id=base.rule_id,
        target_rule_id=target.rule_id,
    )


def _tree_hash(node: Any) -> str:
    """Hash a condition tree deterministically for structural comparison."""
    if node is None:
        return "NONE"
    kids = ""
    if getattr(node, "children", None):
        kid_hashes = sorted([_tree_hash(c) for c in node.children])
        kids = "|".join(kid_hashes)
    content = json.dumps({
        "op": getattr(node, "op", ""),
        "params": dict(sorted(getattr(node, "params", {}).items())),
        "children": kids,
        "n": getattr(node, "n", None),
    }, sort_keys=True)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()