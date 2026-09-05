# ASTROLIFE V2 — PHASE 6D EVIDENCE MODEL

## EvidenceRecord
**Location:** `core/rules/dynamic/evidence_record.py`

### Purpose
Immutable record linking a rule evaluation step to its source. Unlike JaiminiEvidenceGraph nodes, EvidenceRecord is:
- Tradition-agnostic
- Directly source-linked via `source_id`
- Carries pass/fail state for the specific condition
- No timestamps in deterministic fingerprints

### Schema
```python
evidence_id: str                    # stable identifier
rule_id: str
rule_version: str
condition_path: str                 # e.g. "semantics.formation.children[0].params.planet"
condition_type: str                 # e.g. "planet_in_sign", "ALL", "ANY"
claim_id: Optional[str]             # links to ClaimRecord
source_id: Optional[str]            # links to SourceRecord
fact_path: Optional[str]            # e.g. "natal.Mars.sign", "varga.D9.Mars"
expected_value: Optional[Any]
actual_value: Optional[Any]
passed: bool
tier: Literal["DIRECT_FACT", "DERIVED_FACT", "RULE_DERIVED", "SOURCE_CLAIM"]
description: str = ""
metadata: Dict[str, Any] = {}
```

### Tier Semantics
| Tier | Meaning | Example |
|------|---------|---------|
| DIRECT_FACT | Canonical upstream fact | `natal.Mars.sign = "Aries"` |
| DERIVED_FACT | Engine-computed fact | `karaka:AK = "Mars"` |
| RULE_DERIVED | Rule condition/result | `planet_in_sign(Mars, Aries)` |
| SOURCE_CLAIM | Source text supporting rule | "Mars in Aries gives strength" |

### Deterministic Fingerprint
```python
def to_fingerprint_dict(self) -> Dict[str, Any]:
    return {
        "evidence_id": self.evidence_id,
        "rule_id": self.rule_id,
        "rule_version": self.rule_version,
        "condition_path": self.condition_path,
        "condition_type": self.condition_type,
        "claim_id": self.claim_id,
        "source_id": self.source_id,
        "fact_path": self.fact_path,
        "expected_value": self.expected_value,
        "actual_value": self.actual_value,
        "passed": self.passed,
        "tier": self.tier,
        "description": self.description,
        "metadata": {k: v for k, v in sorted(self.metadata.items())},
    }
```

---

## EvidenceBundle
**Location:** `core/rules/dynamic/evidence_record.py`

### Purpose
Complete immutable evidence bundle for a rule evaluation. Contains everything needed to answer "Why did this rule produce this result?" without recalculating.

### Schema
```python
rule_id: str
rule_version: str
rule_name: str
tradition: str
category: str
formation_status: str                  # FORMED | NOT_FORMED | UNKNOWN | INVALID
cancellation_status: str               # CANCELLED | NOT_CANCELLED | PARTIAL | UNKNOWN
mitigation_status: str                 # MITIGATED | NOT_MITIGATED | PARTIAL | UNKNOWN
source_references: List[str]           # source_ids
evidence_records: List[EvidenceRecord]
resolved_facts: Dict[str, Any]         # fact_path → value
unresolved_facts: List[str]            # missing fact_paths
declared_dependencies: List[str]       # from RuleDependencies
used_dependencies: List[str]           # actually accessed
diagnostics: List[str]                 # validation/runtime warnings
conflicts: List[str]                   # conflicting rule_ids
fingerprint: str = ""                  # auto-computed on init
```

### Auto-computed Fingerprint
On `model_post_init`, computes SHA256 of canonical dict:
```python
{
    "rule_id": ..., "rule_version": ..., "rule_name": ...,
    "tradition": ..., "category": ...,
    "formation_status": ..., "cancellation_status": ..., "mitigation_status": ...,
    "source_references": sorted(...),
    "evidence_records": [e.to_fingerprint_dict() for e in sorted(evidence_records, key=lambda x: x.evidence_id)],
    "resolved_facts": sorted(...),
    "unresolved_facts": sorted(...),
    "declared_dependencies": sorted(...),
    "used_dependencies": sorted(...),
    "diagnostics": sorted(...),
    "conflicts": sorted(...),
}
```

### Methods
```python
evidence_by_tier(tier: str) → List[EvidenceRecord]
evidence_by_condition(condition_path: str) → List[EvidenceRecord]
source_evidence_map() → Dict[str, List[EvidenceRecord]]
is_complete() → bool  # FORMED needs evidence; UNKNOWN/INVALID needs no unresolved facts
to_traceability_dict() → Dict  # full traceability export
```

---

## EvidenceBundle.to_traceability_dict()
Exports the complete explanation chain:
```python
{
    "rule": { "rule_id", "rule_version", "rule_name", "tradition", "category" },
    "outcome": { "formation", "cancellation", "mitigation" },
    "dependencies": { "declared": [...], "used": [...], "unresolved": [...] },
    "facts": { "resolved": {...} },
    "evidence": [
        {
            "evidence_id", "condition_path", "condition_type",
            "fact_path", "expected", "actual", "passed", "tier",
            "source_id", "claim_id"
        }
    ],
    "sources": [...],
    "diagnostics": [...],
    "conflicts": [...],
    "fingerprint": "..."
}
```

---

## Source → Evidence Linkage
```
SourceRecord (source_id, locator, quotation)
    ↓
ClaimRecord (claim_id, SOURCE_CLAIM, quotation, locator)
    ↓
EvidenceRecord (evidence_id, source_id, claim_id, fact_path, passed)
    ↓
EvidenceBundle (collects all evidence_records, source_references)
```

### Traceability Path
```
RESULT (EvidenceBundle.outcome)
    ↓
EVALUATION (RulePackage lifecycle + test_report)
    ↓
RULE_VERSION (rule_id + rule_version)
    ↓
DEPENDENCIES (declared_dependencies, used_dependencies, unresolved_facts)
    ↓
FACTS (resolved_facts: fact_path → value)
    ↓
EVIDENCE (evidence_records: condition → fact → passed)
    ↓
SOURCE (source_references → SourceRecord with locator/quotation)
    ↓
CLAIM (claim_id → ClaimRecord with SOURCE_CLAIM text)
```

---

## EvidenceGraph Construction
**Location:** `core/rules/dynamic/evidence_graph.py`

### Node Tiers
| Tier | Constant | Description |
|------|----------|-------------|
| DIRECT_FACT | `DIRECT_FACT` | Canonical upstream facts |
| DERIVED_FACT | `DERIVED_FACT` | Engine-computed facts |
| RULE_DERIVED | `RULE_DERIVED` | Rule conditions & results |
| SOURCE_CLAIM | `SOURCE_CLAIM` | Source text claims |

### Edge Relations
| Relation | Constant | Meaning |
|----------|----------|---------|
| DERIVES | `DERIVES` | Fact → Evidence |
| FEEDS | `FEEDS` | Dependency/Fact → Condition |
| EVALUATES_TO | `EVALUATES_TO` | Condition → Result |
| CO_CHART_FACT | `CO_CHART_FACT` | Co-occurring chart facts |
| SUPPORTS | `SUPPORTS` | Source/Claim → Evidence |
| CONTRADICTS | `CONTRADICTS` | Conflicting evidence |
| TRACKED_SEPARATELY | `TRACKED_SEPARATELY` | Separate dimension tracking |

### `build_evidence_graph_from_bundle(bundle)`
Primary constructor. Builds:
1. **Tier 1 nodes:** `fact:{fact_path}` for each resolved/unresolved fact
2. **Tier 2 nodes:** `derived:{fact_path}` from RuleDependencySpec (if provided)
3. **Tier 3 nodes:** `rule:{rule_id}:{condition_path}`, `rule:{rule_id}:result`
4. **Evidence nodes:** `evidence:{evidence_id}` linked to conditions
5. **Source/Claim nodes:** `source:{source_id}`, `claim:{claim_id}`

**Canonical serialization:** nodes sorted by `node_id`, edges sorted by `(from_id, to_id, relation)`

---

## Traceability: `trace_evaluation(bundle)`
Returns linear path from result back to sources:
```python
[
    {"step": "RESULT", "node_id": "...", "label": "...", "value": {...}},
    {"step": "CONDITION", "node_id": "...", "label": "...", "value": {...}},
    {"step": "EVIDENCE", "node_id": "...", "label": "...", "value": {...}, "passed": True},
    {"step": "FACT", "node_id": "...", "label": "...", "value": "..."},
    {"step": "SOURCE", "node_id": "...", "label": "Source: SRC-001"},
    {"step": "CLAIM", "node_id": "...", "label": "Source Claim: CLAIM-001"},
]
```

---

## UNKNOWN / INVALID Semantics
| Status | Meaning | Evidence Behavior |
|--------|---------|-------------------|
| UNKNOWN | Missing required input | `unresolved_facts` populated, `is_complete() = False` |
| INVALID | Undeclared dependency / bad vocab | `diagnostics` populated, `is_complete() = False` |
| NOT_FORMED | Evaluated false | Evidence present with `passed=False` |

**Never:** Convert UNKNOWN to FALSE. Infer missing source evidence.

---

## Tradition Isolation
- EvidenceBundle carries explicit `tradition` field
- EvidenceGraph construction preserves tradition
- Different traditions → different fingerprints
- Jaimini evidence cannot satisfy Parashari rule dependencies
- TRADITION_DEPENDENT sources explicitly labelled

---

## Version Lineage
```python
bundle_v1 = EvidenceBundle(rule_version="1.0.0", ...)
bundle_v2 = EvidenceBundle(rule_version="1.1.0", ...)

bundle_v1.fingerprint != bundle_v2.fingerprint  # True
bundle_v1.rule_version == "1.0.0"  # Locked to version
```
- Historical bundles reproducible: identical inputs → identical fingerprint
- No silent evidence migration across versions

---

## Integration with RulePackage
```python
pkg = create_rule_draft(...)
test_report = run_rule_tests(pkg)
pkg_tested = pkg.transition_lifecycle("TESTED").model_copy(update={"test_report": test_report})
pkg_review = pkg_tested.transition_lifecycle("REVIEW_PENDING")
act_ok, pkg_active, act_rep = activate_rule(pkg_review, review_record=rev)

# pkg_active now has test_report + activation_metadata
# Export includes all evidence
exp = export_package(pkg_active)
```