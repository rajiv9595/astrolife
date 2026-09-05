# ASTROLIFE V2 — PHASE 6D ARCHITECTURE

## Overview
Phase 6D builds the **Rule Knowledge + Evidence + Provenance Integration** layer on top of the accepted 6A/6B/6C infrastructure. It provides the deterministic plumbing that connects:

```
SOURCE → EVIDENCE → CLAIM → RULE_VERSION → DEPENDENCIES → EVALUATION → RESULT → GRAPH → EXPLANATION
```

## Core Principles
1. **Determinism First** — no timestamps, no random IDs, canonical serialization
2. **Tradition Isolation** — Jaimini ≠ Parashari ≠ Western; explicit labels everywhere
3. **Honest Provenance** — VERIFIED requires locator+quotation; UNVERIFIED default
4. **Conflict Transparency** — REPORTED_ONLY; never auto-resolve
5. **Security by Default** — scan all text fields; data never executed

## Component Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        PHASE 6D LAYER                            │
├──────────────┬───────────────┬────────────┬─────────────────────┤
│  Source      │  Evidence     │  Claim     │  Verification       │
│  (source.py) │ (evidence_    │ (claim.py) │ (verification.py)   │
│              │  record.py)   │            │                     │
├──────────────┼───────────────┼────────────┼─────────────────────┤
│  Graph       │  Bundle       │  Package   │  Import/Export      │
│ (evidence_   │ (evidence_    │ (rule_     │ (import_            │
│  graph.py)   │  record.py)   │  package.py)│  export.py)        │
└──────────────┴───────────────┴────────────┴─────────────────────┘
```

## Data Flow

### 1. Source Ingestion
```
User/Developer → SourceRecord (VERIFIED/UNVERIFIED/CONTESTED/...)
              → SourceManagement (primary/secondary/supporting/conflicting)
              → record_conflict() preserves both as CONTESTED
```

### 2. Claim Creation
```
SourceRecord → ClaimRecord (SOURCE_CLAIM with locator+quotation)
            → ClaimRecord (IMPLEMENTATION_CLAIM - code-level)
            → ClaimRecord (INTERPRETATION_CLAIM - traditional reading)
            → ClaimRecord (DEVELOPER_NOTE - internal docs)
            → ClaimRegistry (deterministic sorted storage)
```

### 3. Rule Definition with Provenance
```
DynamicRuleDefinition → RuleProvenance (SourceReference + confidence)
                    → RuleDependencies (input_facts, varga_dependencies, etc.)
                    → RulePackage (lifecycle + test_cases + reports)
```

### 4. Evaluation & Evidence Bundle
```
RulePackage + CanonicalFacts → evaluate_dynamic_rule()
                          → EvidenceBundle (immutable, fingerprinted)
                          → Contains: all evidence, resolved facts, diagnostics, conflicts
```

### 5. Evidence Graph Construction
```
EvidenceBundle → build_evidence_graph_from_bundle()
             → EvidenceGraph (nodes + edges, deterministic fingerprint)
             → Nodes: DIRECT_FACT | DERIVED_FACT | RULE_DERIVED | SOURCE_CLAIM
             → Edges: DERIVES | FEEDS | EVALUATES_TO | SUPPORTS | CONTRADICTS
```

### 6. Traceability Export
```
EvidenceBundle.to_traceability_dict() → complete chain
trace_evaluation() → linear path: RESULT → CONDITION → EVIDENCE → FACT → SOURCE → CLAIM
```

## Key Models

### SourceRecord (source.py)
```python
source_id: str
category: PRIMARY | SECONDARY | SUPPORTING | CONFLICTING
verification_status: VERIFIED | UNVERIFIED | CONTESTED | SECONDARY | TRADITIONAL | USER_SUPPLIED | CUSTOM
title, author, publication, locator, quotation: str
# VERIFIED requires locator + quotation
```

### EvidenceRecord (evidence_record.py)
```python
evidence_id, rule_id, rule_version
condition_path, condition_type
claim_id, source_id, fact_path
expected_value, actual_value, passed
tier: DIRECT_FACT | DERIVED_FACT | RULE_DERIVED | SOURCE_CLAIM
```

### EvidenceBundle (evidence_record.py)
```python
rule_id, rule_version, rule_name, tradition, category
formation_status: FORMED | NOT_FORMED | UNKNOWN | INVALID
cancellation_status, mitigation_status
source_references, evidence_records
resolved_facts, unresolved_facts
declared_dependencies, used_dependencies
diagnostics, conflicts, fingerprint (auto-computed)
```

### ClaimRecord (claim.py)
```python
claim_id
claim_type: SOURCE_CLAIM | IMPLEMENTATION_CLAIM | INTERPRETATION_CLAIM | DEVELOPER_NOTE
rule_id, rule_version, text
source_id, locator, quotation
verification_status, tradition, dependencies
```

### EvidenceGraph (evidence_graph.py)
```python
nodes: List[GraphNode]  # sorted by node_id
edges: List[GraphEdge]  # sorted by (from_id, to_id, relation)

GraphNode: node_id, tier, label, value, source, rule_id, rule_version
GraphEdge: from_id, to_id, relation, description
```

## Tradition Isolation Enforcement
- Every EvidenceBundle carries `tradition` field
- EvidenceGraph construction preserves tradition in node metadata
- Different traditions → different fingerprints
- Jaimini rules cannot access Parashari evidence
- TRADITION_DEPENDENT sources explicitly labelled

## Security Boundary
All text fields scanned via `find_suspicious_text()`:
- title, author, publication, locator, quotation, notes
- claim text, evidence description
- Blocks: eval, exec, import, subprocess, shell, SQL, lambda, __class__
- Benign prose: "Mars in Aries gives strong executive energy" → passes

## Import/Export Pipeline
```
Export: RulePackage → canonical JSON (sorted keys, no timestamps) → ExportResult
Import: JSON → security scan → schema validation → duplicate check → RulePackage
```
**Rejection criteria:** invalid JSON, security violations, VERIFIED without locator/quotation, broken deps, tradition violations, duplicate version with different content

## Determinism Guarantees
- All models `frozen=True`
- Canonical serialization: `json.dumps(..., sort_keys=True, separators=(",", ":"))`
- No timestamps in fingerprints
- Sorted lists/dicts in all canonical forms
- 50-run determinism verified for: EvidenceBundle, EvidenceGraph, EvidenceRecord

## Integration Points
| Consumes From | Produces For |
|---------------|--------------|
| 6A: DynamicRuleDefinition, RuleProvenance | RulePackage with evidence |
| 6B: CanonicalFactResolver, evaluate_dynamic_rule | EvidenceBundle, EvidenceGraph |
| 6C: RulePackage, RuleLabService, lifecycle | EvidenceBundle attached to package |
| 5F: JaiminiEvidenceGraph concepts | Generalized EvidenceGraph |

## Version Lineage
```
Rule v1.0.0 → EvidenceBundle(v1.0.0) → fingerprint A
Rule v1.1.0 → EvidenceBundle(v1.1.0) → fingerprint B
```
- EvidenceBundle locked to `rule_version`
- Historical bundles reproducible (identical → identical fingerprint)
- No silent migration across versions

## Conflict Handling
```python
# Source conflict
sm.record_conflict(s1, s2) → both CONTESTED in conflicting list

# Rule conflict (5F)
RuleConflict(rule_a, rule_b, DIRECT_CONTRADICTION, resolution="REPORTED_ONLY")
# Never auto-resolved
```

## Files
```
backend/core/rules/dynamic/
├── source.py              # SourceRecord, SourceManagement
├── claim.py               # ClaimRecord, ClaimRegistry  
├── evidence_record.py     # EvidenceRecord, EvidenceBundle
├── verification.py        # SourceVerificationPolicy
├── evidence_graph.py      # EvidenceGraph, GraphNode, GraphEdge, trace
├── import_export.py       # export_package, import_package
├── rule_package.py        # RulePackage (existing, unchanged)
├── audit.py               # AuditRecord, AuditLog (existing)
├── fingerprint.py         # compute_fingerprint (existing)
├── lifecycle.py           # (existing)
├── schema.py              # (existing)
└── __init__.py            # exports all 6D additions
```