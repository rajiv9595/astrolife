"""
Phase 6D — Generalized Evidence Graph.

Tradition-agnostic evidence graph for dynamic rules.
Nodes and edges have deterministic IDs and explicit relation types.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal, Tuple

from pydantic import BaseModel, Field


# Node tiers (matching Phase 5F conventions, generalized)
DIRECT_FACT = "DIRECT_FACT"       # Canonical fact from upstream (ChartFacts, VargaFacts, etc.)
DERIVED_FACT = "DERIVED_FACT"     # Engine-derived fact (JaiminiFacts, StrengthReport, etc.)
RULE_DERIVED = "RULE_DERIVED"     # Rule condition/result
SOURCE_CLAIM = "SOURCE_CLAIM"     # Source claim supporting rule

# Edge relation types
DERIVES = "derives"
FEEDS = "feeds"
EVALUATES_TO = "evaluates-to"
CO_CHART_FACT = "co-chart-fact"
SUPPORTS = "supports"
CONTRADICTS = "contradicts"
TRACKED_SEPARATELY = "tracked-separately"


class GraphNode(BaseModel):
    """A node in the evidence graph with deterministic ID."""

    node_id: str
    tier: Literal[DIRECT_FACT, DERIVED_FACT, RULE_DERIVED, SOURCE_CLAIM]
    label: str
    value: Any = None
    source: str = ""
    rule_id: Optional[str] = None
    rule_version: Optional[str] = None

    model_config = {"frozen": True}


class GraphEdge(BaseModel):
    """An edge in the evidence graph with explicit relation type."""

    from_id: str
    to_id: str
    relation: Literal[DERIVES, FEEDS, EVALUATES_TO, CO_CHART_FACT, SUPPORTS, CONTRADICTS, TRACKED_SEPARATELY] = FEEDS
    description: str = ""

    model_config = {"frozen": True}


class EvidenceGraph(BaseModel):
    """Complete deterministic evidence graph for a rule evaluation.

    Nodes and edges are always emitted in sorted order for canonical serialization.
    """

    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)

    model_config = {"frozen": True}

    def node_ids(self) -> List[str]:
        return [n.node_id for n in self.nodes]

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        return None

    def outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        return [e for e in self.edges if e.from_id == node_id]

    def incoming_edges(self, node_id: str) -> List[GraphEdge]:
        return [e for e in self.edges if e.to_id == node_id]

    def nodes_by_tier(self, tier: str) -> List[GraphNode]:
        return [n for n in self.nodes if n.tier == tier]

    def nodes_for_rule(self, rule_id: str) -> List[GraphNode]:
        return [n for n in self.nodes if n.rule_id == rule_id]

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Canonical serialization: sorted nodes + sorted edges."""
        return {
            "nodes": sorted(
                [n.model_dump() for n in self.nodes],
                key=lambda x: x["node_id"]
            ),
            "edges": sorted(
                [e.model_dump() for e in self.edges],
                key=lambda x: (x["from_id"], x["to_id"], x["relation"])
            ),
        }

    def fingerprint(self) -> str:
        """Deterministic fingerprint of the graph."""
        import hashlib
        import json
        canonical = self.to_canonical_dict()
        s = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(s.encode("utf-8")).hexdigest()


def build_evidence_graph_from_bundle(
    bundle: "EvidenceBundle",
    rule_definition: Optional["DynamicRuleDefinition"] = None,
    dependencies_spec: Optional["RuleDependencySpec"] = None,
) -> EvidenceGraph:
    """Build an EvidenceGraph from an EvidenceBundle.

    This is the primary graph construction function for Phase 6D.
    """
    from .evidence_record import EvidenceRecord
    from .schema import DynamicRuleDefinition
    try:
        from core.jaimini.dependencies import RuleDependencySpec
    except ImportError:
        RuleDependencySpec = None

    nodes: Dict[str, GraphNode] = {}
    edges: List[Tuple[str, str, str, str]] = []  # (from, to, relation, description)

    def add_node(node: GraphNode) -> None:
        nodes[node.node_id] = node

    def add_edge(from_id: str, to_id: str, relation: str, description: str = "") -> None:
        edges.append((from_id, to_id, relation, description))

    # Tier 1: DIRECT_FACTs from resolved_facts
    for fact_path, fact_value in sorted(bundle.resolved_facts.items()):
        node_id = f"fact:{fact_path}"
        add_node(GraphNode(
            node_id=node_id,
            tier=DIRECT_FACT,
            label=f"Fact: {fact_path}",
            value=fact_value,
            source="CanonicalFactResolver",
        ))

    # Tier 1: DIRECT_FACTs from unresolved (mark as missing)
    for fact_path in sorted(bundle.unresolved_facts):
        node_id = f"fact:{fact_path}"
        add_node(GraphNode(
            node_id=node_id,
            tier=DIRECT_FACT,
            label=f"Fact (UNAVAILABLE): {fact_path}",
            value=None,
            source="CanonicalFactResolver",
        ))

    # Tier 2: DERIVED_FACTs from declared dependencies (if spec provided)
    if dependencies_spec:
        for dep in sorted(dependencies_spec.dependencies, key=lambda d: d.fact_path):
            if dep.dependency_type == DERIVED_FACT:
                node_id = f"derived:{dep.fact_path}"
                add_node(GraphNode(
                    node_id=node_id,
                    tier=DERIVED_FACT,
                    label=f"Derived: {dep.description}",
                    value=None,
                    source=dep.fact_path,
                ))
                # Link to source facts if identifiable
                # (would need more context to link precisely)

    # Tier 3: RULE_DERIVED from evidence records
    for ev in sorted(bundle.evidence_records, key=lambda e: e.evidence_id):
        # Condition node
        cond_id = f"rule:{bundle.rule_id}:{ev.condition_path}"
        if cond_id not in nodes:
            add_node(GraphNode(
                node_id=cond_id,
                tier=RULE_DERIVED,
                label=f"Condition: {ev.condition_type} @ {ev.condition_path}",
                value={"expected": ev.expected_value, "actual": ev.actual_value},
                source="RuleEvaluator",
                rule_id=bundle.rule_id,
                rule_version=bundle.rule_version,
            ))

        # Result node
        result_id = f"rule:{bundle.rule_id}:result"
        if result_id not in nodes:
            add_node(GraphNode(
                node_id=result_id,
                tier=RULE_DERIVED,
                label=f"Result: {bundle.formation_status}",
                value={
                    "formation": bundle.formation_status,
                    "cancellation": bundle.cancellation_status,
                    "mitigation": bundle.mitigation_status,
                },
                source="RuleEvaluator",
                rule_id=bundle.rule_id,
                rule_version=bundle.rule_version,
            ))
            add_edge(cond_id, result_id, EVALUATES_TO, "condition evaluates to result")

        # Link evidence to condition
        ev_id = f"evidence:{ev.evidence_id}"
        if ev_id not in nodes:
            add_node(GraphNode(
                node_id=ev_id,
                tier=RULE_DERIVED if ev.tier == RULE_DERIVED else ev.tier,
                label=f"Evidence: {ev.condition_type}",
                value={"passed": ev.passed, "expected": ev.expected_value, "actual": ev.actual_value},
                source="RuleEvaluator",
                rule_id=bundle.rule_id,
                rule_version=bundle.rule_version,
            ))
            add_edge(ev_id, cond_id, FEEDS, "evidence feeds condition")

        # Link evidence to source fact
        if ev.fact_path:
            fact_id = f"fact:{ev.fact_path}"
            if fact_id in nodes:
                add_edge(fact_id, ev_id, DERIVES, "fact derives evidence")

        # Link evidence to source claim
        if ev.claim_id:
            claim_id = f"claim:{ev.claim_id}"
            if claim_id not in nodes:
                add_node(GraphNode(
                    node_id=claim_id,
                    tier=SOURCE_CLAIM,
                    label=f"Source Claim: {ev.claim_id}",
                    value=None,
                    source="SourceRecord",
                ))
            add_edge(claim_id, ev_id, SUPPORTS, "claim supports evidence")

        # Link evidence to source record
        if ev.source_id:
            source_id = f"source:{ev.source_id}"
            if source_id not in nodes:
                add_node(GraphNode(
                    node_id=source_id,
                    tier=SOURCE_CLAIM,
                    label=f"Source: {ev.source_id}",
                    value=None,
                    source="SourceRecord",
                ))
            add_edge(source_id, ev_id, SUPPORTS, "source supports evidence")

    # Link declared dependencies to rule condition
    for dep_path in sorted(bundle.declared_dependencies):
        dep_node_id = f"dep:{dep_path}"
        if dep_node_id not in nodes:
            add_node(GraphNode(
                node_id=dep_node_id,
                tier=DERIVED_FACT,
                label=f"Declared Dependency: {dep_path}",
                value=None,
                source="RuleDependencies",
            ))
        cond_id = f"rule:{bundle.rule_id}:formation"
        if cond_id in nodes:
            add_edge(dep_node_id, cond_id, FEEDS, "dependency feeds rule formation")

    # Build final graph
    ordered_nodes = [nodes[k] for k in sorted(nodes.keys())]
    ordered_edges = [
        GraphEdge(from_id=a, to_id=b, relation=r, description=d)
        for a, b, r, d in sorted(edges, key=lambda x: (x[0], x[1], x[2]))
    ]

    return EvidenceGraph(nodes=ordered_nodes, edges=ordered_edges)


# Convenience function for traceability export
def trace_evaluation(
    bundle: "EvidenceBundle",
    rule_definition: Optional["DynamicRuleDefinition"] = None,
) -> Dict[str, Any]:
    """Full traceability: RESULT → EVALUATION → RULE → DEPS → FACTS → EVIDENCE → SOURCE."""
    graph = build_evidence_graph_from_bundle(bundle, rule_definition)
    return {
        "evidence_bundle": bundle.to_traceability_dict(),
        "evidence_graph": graph.to_canonical_dict(),
        "trace_path": _build_trace_path(bundle, graph),
    }


def _build_trace_path(bundle: "EvidenceBundle", graph: EvidenceGraph) -> List[Dict[str, Any]]:
    """Build a linear trace path from result back to sources."""
    path: List[Dict[str, Any]] = []

    # Start from result
    result_node = graph.get_node(f"rule:{bundle.rule_id}:result")
    if result_node:
        path.append({
            "step": "RESULT",
            "node_id": result_node.node_id,
            "label": result_node.label,
            "value": result_node.value,
        })

    # Trace through conditions
    for ev in bundle.evidence_records:
        cond_id = f"rule:{bundle.rule_id}:{ev.condition_path}"
        cond_node = graph.get_node(cond_id)
        if cond_node:
            path.append({
                "step": "CONDITION",
                "node_id": cond_node.node_id,
                "label": cond_node.label,
                "value": cond_node.value,
            })

        # Evidence
        ev_id = f"evidence:{ev.evidence_id}"
        ev_node = graph.get_node(ev_id)
        if ev_node:
            path.append({
                "step": "EVIDENCE",
                "node_id": ev_node.node_id,
                "label": ev_node.label,
                "value": ev_node.value,
                "passed": ev.passed,
            })

        # Fact
        if ev.fact_path:
            fact_id = f"fact:{ev.fact_path}"
            fact_node = graph.get_node(fact_id)
            if fact_node:
                path.append({
                    "step": "FACT",
                    "node_id": fact_node.node_id,
                    "label": fact_node.label,
                    "value": fact_node.value,
                })

        # Source
        if ev.source_id:
            source_id = f"source:{ev.source_id}"
            source_node = graph.get_node(source_id)
            if source_node:
                path.append({
                    "step": "SOURCE",
                    "node_id": source_node.node_id,
                    "label": source_node.label,
                })

        # Claim
        if ev.claim_id:
            claim_id = f"claim:{ev.claim_id}"
            claim_node = graph.get_node(claim_id)
            if claim_node:
                path.append({
                    "step": "CLAIM",
                    "node_id": claim_node.node_id,
                    "label": claim_node.label,
                })

    return path