# ASTROLIFE V2 — PHASE 6D REPOSITORY AUDIT

**Generated:** 2026-09-05  
**Scope:** Phase 6D — Rule Knowledge, Evidence & Provenance Integration  
**Status:** Pre-implementation audit of existing infrastructure

---

## 1. EXISTING SOURCE MODELS

### 1.1 `core/rules/dynamic/source.py` — Phase 6C SourceRecord

**SourceRecord** (frozen pydantic model):
```python
source_id: str
category: str = PRIMARY           # PRIMARY | SECONDARY | SUPPORTING | CONFLICTING
verification_status: str = UNVERIFIED  # VERIFIED | UNVERIFIED | CONTESTED | SECONDARY | TRADITIONAL | USER_SUPPLIED | CUSTOM
title: str = ""
author: str = ""
publication: str = ""
locator: str = ""
quotation: str = ""
```

**SourceManagement** (frozen container):
- `primary: Optional[SourceRecord]`
- `secondary: Optional[SourceRecord]`
- `supporting: List[SourceRecord]`
- `conflicting: List[SourceRecord]`

**Verification states defined:**
- `VERIFIED` — requires locator + quotation
- `UNVERIFIED` — default
- `CONTESTED` — when conflicts recorded
- `SECONDARY` — secondary source
- `TRADITIONAL` — classical text
- `USER_SUPPLIED` — developer fixture
- `CUSTOM` — custom/developer

**Key enforcement:** `set_verification()` rejects `UNVERIFIED → VERIFIED` without locator + quotation.

---

### 1.2 `core/rules/provenance.py` — Phase 5A ProvenanceRecord

**ProvenanceRecord** (dataclass, NOT frozen):
```python
rule_id: str
source_type: SourceType       # CLASSICAL_TEXT | COMMENTARY | MODERN_AUTHOR | ORAL_TRADITION | UNVERIFIED | CUSTOM
source_name: str              # e.g. "Brihat Parashara Hora Shastra"
source_reference: str         # e.g. "BPHS Ch. 36, Vs. 1-2"
tradition: RuleTradition      # PARASHARI_CLASSICAL | JAIMINI | TRADITION_DEPENDENT | WESTERN | CUSTOM
method: str
chapter: str = ""
verse: str = ""
commentator: str = ""
translation: str = ""
verification_status: str = "UNVERIFIED"  # VERIFIED | UNVERIFIED
verified_by: str = ""
verified_at: str = ""         # TIMESTAMP — NOT DETERMINISTIC
notes: str = ""
implementation_version: str = "1.0.0"
created_at: str = datetime.utcnow().isoformat()  # TIMESTAMP — NOT DETERMINISTIC
updated_at: str = datetime.utcnow().isoformat()  # TIMESTAMP — NOT DETERMINISTIC
```

**ProvenanceRegistry** — class-level mutable registry with `register()`, `get()`, `get_all()`, `verify()`.

**Pre-populated:** 4 classical sources (Gaja Kesari, Dharma-Karmadhipati, Kemadruma, Neecha Bhanga) from BPHS with `VERIFIED` status.

**Gap:** Contains non-deterministic timestamps (`created_at`, `updated_at`, `verified_at`). Not frozen. Mutates in-place via `verify()`.

---

### 1.3 `core/rules/dynamic/schema.py` — Phase 6A SourceReference + RuleProvenance

**SourceReference** (frozen):
```python
source_id: str = ""
title: str = ""
author: str = ""
publication: str = ""
locator: str = ""
quotation: str = ""
verification_status: str  # VERIFIED | UNVERIFIED | CONTESTED | SECONDARY | TRADITIONAL | USER_SUPPLIED | CUSTOM
```

**RuleProvenance** (frozen):
```python
source_reference: SourceReference
source_type: str = ""
source_author: str = ""
source_title: str = ""
source_locator: str = ""
provenance_status: str = ""
confidence: str = ""
```

**Note:** Phase 6A schema has more granular bibliographic fields (source_id, title, author, publication) than Phase 5A ProvenanceRecord.

---

## 2. EXISTING EVIDENCE MODELS

### 2.1 `core/rules/evidence.py` — Phase 5A Evidence (dataclass, NOT frozen)

```python
evidence_type: EvidenceType       # 22 enum values (PLANET_IN_SIGN, CONJUNCTION, etc.)
subject: str                      # e.g. "Jupiter"
value: Any                        # actual value
expected: Any = None              # expected value
actual: Any = None                # actual value
source: str                       # "ChartFacts", "StrengthReport", "VargaFacts", "JaiminiFacts", "DynamicState"
significance: str = ""            # human-readable explanation
details: Dict[str, Any] = field(default_factory=dict)
passed: bool = True               # NOT in original - added by EvidenceBuilder?
```

**EvidenceBuilder** — fluent builder for RuleContext-based evidence construction. Produces mutable lists.

**EvidenceValidator** — validates evidence quality (required types, significance, source).

---

### 2.2 `core/jaimini/evidence.py` — Phase 5F JaiminiEvidenceGraph

**EvidenceNode** (frozen):
```python
node_id: str          # deterministic: "d1:planet:Mars:sign", "karaka:AK", "rule:JAI...:result"
tier: str             # DIRECT_FACT | DERIVED_FACT | RULE_DERIVED
label: str
value: Any = None
source: str = ""
```

**EvidenceEdge** (frozen):
```python
from_id: str
to_id: str
relation: str = "supports"  # "derives", "feeds", "evaluates-to", "co-chart-fact"
```

**JaiminiEvidenceGraph** (frozen):
```python
nodes: List[EvidenceNode]      # sorted by node_id for determinism
edges: List[EvidenceEdge]      # sorted by (from_id, to_id, relation)
```

**Tier hierarchy:**
- Tier 1 (DIRECT_FACT): `d1:planet:X:sign`, `d1:lagna`
- Tier 2 (DERIVED_FACT): `karaka:AK`, `pada:A1:final`, `karakamsha:sign`, `swamsa:lagna`, `d9:planet:X:sign`
- Tier 3 (RULE_DERIVED): `rule:JAI...:formation`, `rule:JAI...:result`

**Edge relations:** "derives", "feeds", "evaluates-to", "co-chart-fact", "tracked-separately"

---

### 2.3 `core/rules/dynamic/rule_package.py` — Phase 6C RuleTestCase + Test Reports

**RuleTestCase** (frozen):
```python
test_id: str
description: str
input_fixture: Dict[str, Any]
expected_formation: str           # FORMED | NOT_FORMED | UNKNOWN
expected_cancellation: str = NOT_CANCELLED
expected_mitigation: str = NOT_MITIGATED
expected_final_state: str = FORMED
expected_unknown_invalid: Optional[str] = None
expected_evidence: Optional[List[str]] = None
expected_dependencies: Optional[List[str]] = None
is_golden: bool = False
```

**RuleTestReport** (frozen):
```python
total: int
passed: int
failed: int
skipped: int
diagnostics: List[str]
execution_fingerprint: str
```

**ValidationReport** (frozen):
```python
errors: List[Diagnostic]
warnings: List[Diagnostic]
info: List[Diagnostic]
```

---

## 3. EXISTING PROVENANCE STRUCTURES

| Model | Location | Frozen | Deterministic | Purpose |
|-------|----------|--------|---------------|---------|
| SourceRecord | 6C source.py | ✅ | ✅ | Minimal bibliographic + verification |
| SourceReference | 6A schema.py | ✅ | ✅ | Embedded in RuleProvenance |
| RuleProvenance | 6A schema.py | ✅ | ✅ | Full provenance on DynamicRuleDefinition |
| ProvenanceRecord | 5A provenance.py | ❌ | ❌ (timestamps) | Registry + display formatting |
| SourceManagement | 6C source.py | ✅ | ✅ | Multi-source container per rule |

**Verification state taxonomy (multiple overlapping):**
- 6C source.py: VERIFIED, UNVERIFIED, CONTESTED, SECONDARY, TRADITIONAL, USER_SUPPLIED, CUSTOM
- 5A provenance.py: VERIFIED, UNVERIFIED (string only)
- 6A schema.py: VERIFIED, UNVERIFIED, CONTESTED, SECONDARY, TRADITIONAL, USER_SUPPLIED, CUSTOM
- 5A enums.py ConfidenceLevel: VERIFIED, HIGH, MEDIUM, TRADITION_DEPENDENT, EXPERIMENTAL, CUSTOM

---

## 4. DEPENDENCY IDENTIFIERS

### 4.1 Phase 5F `core/jaimini/dependencies.py`

**Dependency types:**
- `FACT` — canonical upstream (ChartFacts, etc.)
- `DERIVED_FACT` — 5D engine output (JaiminiFacts)
- `RULE_RESULT` — another rule's outcome (future use)

**RuleDependency** (frozen dataclass):
```python
rule_id: str
dependency_type: str          # FACT | DERIVED_FACT | RULE_RESULT
fact_path: str                # e.g. "ChartFacts.planets[D1]", "JaiminiFacts.chara_karakas"
required: bool
description: str
```

**RuleDependencySpec** (frozen dataclass):
```python
rule_id: str
dependencies: List[RuleDependency]
varga_dependencies: List[str]       # e.g. ["D9"]
strength_dependencies: List[str]    # always [] for 5E
origin_label: str                   # CLASSICAL_JAIMINI | TRADITION_DEPENDENT
```

**DEPENDENCY_SPECS** — 12 rules registered with explicit fact paths.

**Key fact path constants:**
- `_CHART = "ChartFacts.planets[D1]"`
- `_KAR = "JaiminiFacts.chara_karakas"`
- `_DRI = "JaiminiFacts.rashi_drishti"`
- `_AL = "JaiminiFacts.arudha_padas[1]"`
- `_D9 = "varga_facts.D9"`

**Coverage check:** `dependency_covered(declared_paths, used_path)` — exact or parent-collection match.

**Cycle detection:** `detect_dependency_cycles()` over `RULE_RESULT` edges.

---

### 4.2 Phase 6A/6B — Dynamic Rule Dependencies

**RuleDependencies** (frozen, schema.py):
```python
input_facts: List[str]              # e.g. ["natal.Mars.sign", "varga.D9.Mars"]
rule_dependencies: List[str]        # e.g. ["DEMO.CUSTOM.SUPPORT"]
varga_dependencies: List[str]       # e.g. ["D9"]
dasha_dependencies: List[str]       # e.g. ["vimshottari.mahadasha"]
transit_dependencies: List[str]     # e.g. ["Jupiter"]
strength_dependencies: List[str]    # e.g. ["shadbala.Mars"]
```

**Preview/Diagnostics:** `DependencyPreview` (direct_facts, undeclared_dependency_diagnostics, etc.)

---

## 5. RULE IDs & VERSION IDs

### 5.1 Phase 5E/5F Jaimini Rule IDs (12 total)
```
JAI.KARAKA.AK_AMK_CONJUNCTION
JAI.KARAKA.AK_KENDRA_FROM_AL
JAI.KARAKA.DK_UL_SAMBANDHA
JAI.DRISHTI.AK_AMK_MUTUAL
JAI.DRISHTI.AMK_ON_AL
JAI.DRISHTI.AK_ON_AL
JAI.ARUDHA.AL_BENEFIC_OCCUPANCY
JAI.ARUDHA.AL_LORD_KENDRA_TRINE
JAI.ARUDHA.DHANA_A2_A11
JAI.ARUDHA.A7_UL_ALIGNMENT
JAI.KARAKAMSHA.BENEFIC_OCCUPANCY
JAI.SWAMSA.BENEFIC_OCCUPANCY
```

**Format:** `JAI.<SUBSYSTEM>.<RULE_NAME>`

### 5.2 Phase 5B Parashari Rule IDs (31 total)
```
PARASHARI.YOGA.GAJA_KESARI
PARASHARI.YOGA.DHARMA_KARMADHIPATI
PARASHARI.YOGA.YOGAKARAKA_RAJA
PARASHARI.YOGA.DHANA_2_11
PARASHARI.YOGA.DHANA_5_9
PARASHARI.YOGA.DHANA_LAGNA_WEALTH
PARASHARI.YOGA.RUCHAKA
PARASHARI.YOGA.BHADRA
PARASHARI.YOGA.HAMSA
PARASHARI.YOGA.MALAVYA
PARASHARI.YOGA.SASA
PARASHARI.YOGA.GAJA_KESARI
PARASHARI.YOGA.BUDHA_ADITYA
PARASHARI.YOGA.CHANDRA_MANGALA
PARASHARI.YOGA.ADHI
PARASHARI.YOGA.LAKSHMI
PARASHARI.YOGA.SARASWATI
PARASHARI.YOGA.AMALA
PARASHARI.YOGA.VASUMATI
PARASHARI.YOGA.SUNAPHA
PARASHARI.YOGA.ANAPHA
PARASHARI.YOGA.DURUDHARA
PARASHARI.YOGA.KEMADRUMA
PARASHARI.YOGA.PARIVARTANA_MAHA
PARASHARI.YOGA.PARIVARTANA_KHALA
PARASHARI.YOGA.PARIVARTANA_DAINYA
PARASHARI.YOGA.VIPARITA_HARSHA
PARASHARI.YOGA.VIPARITA_SARALA
PARASHARI.YOGA.VIPARITA_VIMALA
PARASHARI.YOGA.NEECHA_BHANGA
PARASHARI.YOGA.NEECHA_BHANGA_RAJA
```

**Format:** `PARASHARI.YOGA.<RULE_NAME>`

### 5.3 Phase 5C Dosha Rule IDs (6 total)
```
DOSHA.MANGLIK.LAGNA_CLASSICAL
DOSHA.MANGLIK.MOON_REFERENCE
DOSHA.MANGLIK.VENUS_REFERENCE
DOSHA.KEMADRUMA.CLASSICAL
DOSHA.KALA_SARPA.SIGN_BASED
DOSHA.PITRU.MODERN_COMMON
```

**Format:** `DOSHA.<TYPE>.<METHOD>`

### 5.4 Phase 6A/6C Dynamic Rule IDs (Developer Lab)
```
DEMO.CUSTOM.SYNTHETIC_GOLDEN@1.0.0
DEMO.CUSTOM.SYNTHETIC_GOLDEN@1.1.0
DEMO.VERSION.TEST@1.0.0
DEMO.VERSION.TEST@1.1.0
```

**Format:** `<NAMESPACE>.<CUSTOM>.<NAME>@<SEMVER>`

### 5.5 Version IDs
- Semantic versioning enforced: `major.minor.patch` or `major.minor.patch-prerelease`
- Immutable per rule_id: same version cannot be recreated with different content
- `DynamicRuleRegistry.list_versions(rule_id)` returns ordered list

---

## 6. FINGERPRINT IDs

### 6.1 Phase 6C `fingerprint.py`
```python
compute_fingerprint(package: RulePackage) -> str   # SHA256 of canonical JSON
fingerprints_match(pkg1, pkg2) -> bool
fingerprint_from_dict(data: Dict) -> str
```

**Canonicalization:** `to_canonical_dict()` produces sorted keys, compact JSON, no timestamps, no random IDs.

### 6.2 Phase 6A `serialization.py`
```python
to_canonical_json(rule: DynamicRuleDefinition) -> str
from_canonical_json(json_str) -> DynamicRuleDefinition
round_trip(json_str) -> str  # byte-identical
```

---

## 7. CONFLICT IDs

### 7.1 Phase 5F `conflicts.py`
**RuleConflict** (frozen):
```python
rule_a: str
rule_b: str
conflict_class: str           # DIRECT_CONTRADICTION | APPARENT_CONTRADICTION | DIFFERENT_DIMENSIONS | TRADITION_VARIANT | INSUFFICIENT_INFORMATION | NO_CONFLICT
same_proposition: bool = False
detail: str = ""
resolution: str = "REPORTED_ONLY"
```

**SAME_PROPOSITION_PAIRS** (3 pairs):
1. `JAI.KARAKA.AK_AMK_CONJUNCTION` vs `JAI.DRISHTI.AK_AMK_MUTUAL`
2. `JAI.KARAKA.DK_UL_SAMBANDHA` vs `JAI.ARUDHA.A7_UL_ALIGNMENT`
3. `JAI.KARAKAMSHA.BENEFIC_OCCUPANCY` vs `JAI.SWAMSA.BENEFIC_OCCUPANCY`

**DIMENSIONS** — 12 dimension tags for cross-dimension analysis.

---

### 7.2 Phase 6C `source.py` SourceConflict
```python
record_conflict(s1, s2) -> SourceManagement
```
Moves both to `CONFLICTING` category, `CONTESTED` verification status.

---

## 8. AUDIT IDs

### 8.1 Phase 6C `audit.py`
**AuditRecord** (frozen):
```python
audit_id: str     # "aud_<sha256(seq:event:rule:version:actor:reason:ts)[:12]>"
event_type: str   # RULE_CREATED | RULE_VALIDATED | RULE_TESTED | RULE_REVIEWED | RULE_ACTIVATED | RULE_DISABLED | RULE_DEPRECATED | RULE_ARCHIVED | RULE_VERSION_CREATED
rule_id: str
version: str
timestamp: str    # deterministic: "audit_step_{seq:06d}" or provided
actor: str
reason: str
payload: Dict[str, Any]
```

**AuditLog** — append-only list with `record()`, `get_records()`, `get_records_by_type()`, `get_records_for_rule()`, `export()`, `import_records()`.

**Deterministic timestamp:** `"audit_step_000001"` (not wall-clock).

---

## 9. REUSABLE INFRASTRUCTURE SUMMARY

### 9.1 Canonical Models (FROZEN, DETERMINISTIC) — REUSE AS-IS
| Model | File | Purpose |
|-------|------|---------|
| SourceRecord | 6C source.py | Minimal source + verification |
| SourceReference | 6A schema.py | Bibliographic reference in RuleProvenance |
| RuleProvenance | 6A schema.py | Full provenance on rule definition |
| SourceManagement | 6C source.py | Multi-source container |
| EvidenceNode | 5F evidence.py | Graph node with deterministic ID |
| EvidenceEdge | 5F evidence.py | Graph edge with relation type |
| JaiminiEvidenceGraph | 5F evidence.py | Complete evidence graph |
| RuleDependency | 5F dependencies.py | Declared dependency metadata |
| RuleDependencySpec | 5F dependencies.py | Full spec per rule |
| AuditRecord | 6C audit.py | Immutable lifecycle event |
| AuditLog | 6C audit.py | Append-only log |
| RulePackage | 6C rule_package.py | Full rule lifecycle container |
| RuleTestCase | 6C rule_package.py | Declarative test fixture |
| RuleTestReport | 6C rule_package.py | Test execution summary |
| ValidationReport | 6C rule_package.py | Validation diagnostics |
| RuleDiff | 6C rule_package.py | Semantic version diff |
| RuleHealth | 6C rule_package.py | Structured health status |

### 9.2 Models Needing Migration/Extension (NON-DETERMINISTIC OR MUTABLE)
| Model | Issue | Fix Required |
|-------|-------|--------------|
| ProvenanceRecord | timestamps, mutable registry | Remove timestamps, freeze, make registry append-only |
| Evidence (5A) | mutable, not frozen | Replace with frozen model or deprecate |
| EvidenceBuilder | mutable builder pattern | Keep as builder; output frozen EvidenceRecord |
| ProvenanceRegistry | class-level mutable dict | Replace with immutable registry or AuditLog integration |

### 9.3 Non-Existent Models — MUST CREATE
| Model | Spec Section | Purpose |
|-------|--------------|---------|
| ClaimRecord | §6 | Separate source statement from implementation interpretation |
| EvidenceRecord | §3 | Immutable evidence with source linkage (distinct from graph node) |
| EvidenceBundle | §8 | Immutable evaluation explanation package |
| SourceVerificationPolicy | §4 | Explicit VERIFIED requirements (locator+quotation) |

---

## 10. DUPLICATION RISKS IDENTIFIED

1. **SourceRecord vs SourceReference vs ProvenanceRecord** — three overlapping bibliographic models with different field granularity and determinism properties.

2. **Evidence (5A) vs EvidenceNode/Edge (5F) vs RuleTestCase.evidence (6C)** — three evidence representations serving different layers but conceptually overlapping.

3. **Verification states** — 6C source.py has 7 states; 5A enums.py ConfidenceLevel has 6; 5A provenance.py uses raw strings.

4. **Dependency declarations** — 5F RuleDependency (Jaimini-specific) vs 6A RuleDependencies (generic dynamic rules). Different fact path namespaces.

5. **Audit vs Registry** — 6C AuditLog is append-only immutable; 5A ProvenanceRegistry is mutable class-level dict.

---

## 11. FILES TO MODIFY / EXTEND (PRELIMINARY)

### Core Schema Files (additive only):
- `core/rules/dynamic/schema.py` — add ClaimRecord, extend EvidenceRecord
- `core/rules/dynamic/source.py` — extend SourceRecord if needed (edition, publisher, language)
- `core/rules/dynamic/audit.py` — add source/evidence event types
- `core/rules/dynamic/rule_package.py` — add EvidenceBundle to RulePackage
- `core/rules/dynamic/preview.py` — extend for EvidenceBundle preview

### New Files:
- `core/rules/dynamic/claim.py` — ClaimRecord model
- `core/rules/dynamic/evidence_record.py` — EvidenceRecord model (frozen, source-linked)
- `core/rules/dynamic/evidence_bundle.py` — EvidenceBundle model
- `core/rules/dynamic/verification.py` — SourceVerificationPolicy + VERIFIED gate
- `core/rules/dynamic/graph.py` — Generalized EvidenceGraph (not Jaimini-specific)

### Test File:
- `backend/test_dynamic_rules_phase6d.py` — dedicated test suite

---

## 12. INTEGRATION POINTS

| Phase 6D Component | Consumes From | Produces For |
|-------------------|---------------|--------------|
| SourceRecord | — | RuleProvenance, RulePackage |
| EvidenceRecord | SourceRecord, RulePackage | EvidenceBundle, EvidenceGraph |
| ClaimRecord | SourceRecord | RuleProvenance (source statement) |
| EvidenceBundle | RulePackage, EvaluationResult, EvidenceGraph | Export, Audit, Historical Reproducibility |
| EvidenceGraph (generalized) | EvidenceRecord, RuleDependencySpec | Traceability, Debugging |
| SourceVerificationPolicy | SourceRecord | VERIFIED gate enforcement |
| AuditLog extensions | All above | Complete lifecycle trail |

---

## 13. CONCLUSION

**Existing infrastructure provides ~80% of required models.** The key gaps are:

1. **ClaimRecord** — to separate source text from implementation interpretation
2. **EvidenceRecord** — immutable, source-linked evidence (distinct from graph nodes)
3. **EvidenceBundle** — complete evaluation explanation package
4. **SourceVerificationPolicy** — explicit VERIFIED requirements
5. **Generalized EvidenceGraph** — not Jaimini-specific

**All existing frozen/deterministic models should be reused.** The non-deterministic ProvenanceRecord should be deprecated in favor of RuleProvenance + AuditLog.

**No canonical calculation engines need modification.** This is purely an integration layer on top of 6A/6B/6C.