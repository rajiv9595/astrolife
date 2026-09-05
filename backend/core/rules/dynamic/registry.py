"""
Phase 6A — DynamicRuleRegistry. New registry; accepted 5A RuleRegistry is
untouched. Versions immutable: duplicate (id, version) rejected; newer
versions allowed with supersedes linkage. Deterministic ordering everywhere.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .schema import DynamicRuleDefinition
from .validators import Diagnostic, compare_versions, validate_rule


class DuplicateVersionError(ValueError):
    pass


class DynamicRuleRegistry:
    def __init__(self) -> None:
        self._rules: Dict[str, Dict[str, DynamicRuleDefinition]] = {}

    def register(self, rule: DynamicRuleDefinition,
                 known_ids: Optional[set] = None) -> List[Diagnostic]:
        diags = validate_rule(rule, known_ids if known_ids is not None else set(self._rules))
        if any(d.severity == "ERROR" for d in diags):
            return diags
        versions = self._rules.setdefault(rule.identity.rule_id, {})
        if rule.identity.rule_version in versions:
            raise DuplicateVersionError(
                f"{rule.identity.rule_id}@{rule.identity.rule_version} already registered; "
                f"modifications require a new version.")
        versions[rule.identity.rule_version] = rule
        return diags

    def get(self, rule_id: str, version: Optional[str] = None) -> Optional[DynamicRuleDefinition]:
        versions = self._rules.get(rule_id)
        if not versions:
            return None
        if version is not None:
            return versions.get(version)
        latest = sorted(versions.keys(), key=lambda v: tuple(int(x) for x in v.split("-")[0].split(".")))[-1]
        return versions[latest]

    def list_versions(self, rule_id: str) -> List[str]:
        versions = self._rules.get(rule_id, {})
        return sorted(versions.keys(),
                      key=lambda v: tuple(int(x) for x in v.split("-")[0].split(".")))

    def list_all(self) -> List[DynamicRuleDefinition]:
        out = []
        for rid in sorted(self._rules):
            out.append(self.get(rid))
        return [r for r in out if r is not None]

    def filter_by(self, tradition: Optional[str] = None, category: Optional[str] = None,
                  verification: Optional[str] = None,
                  validation_status: Optional[str] = None) -> List[DynamicRuleDefinition]:
        out = []
        for rule in self.list_all():
            if tradition and rule.classification.tradition != tradition:
                continue
            if category and rule.classification.category != category:
                continue
            if verification and rule.provenance.source_reference.verification_status != verification:
                continue
            if validation_status and rule.validation.validation_status != validation_status:
                continue
            out.append(rule)
        return out

    def deprecate(self, rule_id: str, version: str, deprecated_by: str) -> bool:
        rule = self.get(rule_id, version)
        if rule is None:
            return False
        new_lifecycle = rule.lifecycle.model_copy(update={"status": "DEPRECATED",
                                                           "deprecated_by": deprecated_by})
        self._rules[rule_id][version] = rule.model_copy(update={"lifecycle": new_lifecycle})
        return True

    def validate_graph(self) -> List[Diagnostic]:
        """Multi-level cycle detection across registered rule_dependencies."""
        diags: List[Diagnostic] = []
        adj = {rid: sorted({d for v in vers.values() for d in v.dependencies.rule_dependencies})
               for rid, vers in self._rules.items()}
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {rid: WHITE for rid in adj}

        def visit(node: str, stack: List[str]) -> None:
            color[node] = GRAY
            stack.append(node)
            for nxt in adj.get(node, []):
                if nxt not in adj:
                    continue
                if color[nxt] == GRAY:
                    diags.append(Diagnostic(
                        code="CYCLE", path=f"registry.{node}",
                        message=f"Dependency cycle: {' -> '.join(stack + [nxt])}"))
                elif color[nxt] == WHITE:
                    visit(nxt, stack)
            stack.pop()
            color[node] = BLACK

        for rid in sorted(adj):
            if color[rid] == WHITE:
                visit(rid, [])
        return sorted(diags, key=lambda d: (d.code, d.path, d.message))

    def count(self) -> int:
        return sum(len(v) for v in self._rules.values())
