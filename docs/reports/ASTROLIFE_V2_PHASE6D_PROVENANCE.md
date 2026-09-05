# ASTROLIFE V2 — PHASE 6D PROVENANCE MODEL

## Overview
Provenance in Phase 6D is the **honest, explicit, deterministic** tracking of where every rule comes from, who verified it, and what evidence supports it. No fabricated citations. No silent upgrades.

## Core Models

### SourceRecord (source.py)
```python
class SourceRecord(BaseModel):
    source_id: str
    category: Literal["primary", "secondary", "supporting", "conflicting"] = "primary"
    verification_status: Literal[
        "VERIFIED", "UNVERIFIED", "CONTESTED", 
        "SECONDARY", "TRADITIONAL", "USER_SUPPLIED", "CUSTOM"
    ] = "UNVERIFIED"
    title: str = ""
    author: str = ""
    publication: str = ""
    locator: str = ""           # REQUIRED for VERIFIED
    quotation: str = ""         # REQUIRED for VERIFIED
    model_config = {"frozen": True}
```

### SourceManagement (source.py)
Container for multiple sources per rule:
```python
class SourceManagement(BaseModel):
    primary: Optional[SourceRecord] = None
    secondary: Optional[SourceRecord] = None
    supporting: List[SourceRecord] = []
    conflicting: List[SourceRecord] = []
    
    def add_source(self, source: SourceRecord) → "SourceManagement"
    def set_verification(self, source_id: str, new_status: str) → "SourceManagement"
    def record_conflict(self, s1: SourceRecord, s2: SourceRecord) → "SourceManagement"
    def list_all_sources(self) → List[SourceRecord]  # deterministic order
```

### RuleProvenance (schema.py — Phase 6A)
Embedded in DynamicRuleDefinition:
```python
class RuleProvenance(BaseModel):
    source_reference: SourceReference = Field(default_factory=SourceReference)
    source_type: str = ""
    source_author: str = ""
    source_title: str = ""
    source_locator: str = ""
    provenance_status: str = ""
    confidence: str = ""
    model_config = {"frozen": True}

class SourceReference(BaseModel):
    source_id: str = ""
    title: str = ""
    author: str = ""
    publication: str = ""
    locator: str = ""
    quotation: str = ""
    verification_status: str = "UNVERIFIED"
    model_config = {"frozen": True}
```

---

## Verification States

| State | Meaning | Requirements |
|-------|---------|--------------|
| **VERIFIED** | Source authenticated with evidence | `source_id` + `locator` + `quotation` all non-empty |
| **UNVERIFIED** | No verification performed | Default; no requirements |
| **CONTESTED** | Multiple sources conflict | Set by `record_conflict()` |
| **SECONDARY** | Commentary/derivative work | No special requirements |
| **TRADITIONAL** | Classical text authority | No special requirements |
| **USER_SUPPLIED** | Developer fixture/test | No special requirements |
| **CUSTOM** | Custom classification | No special requirements |

### VERIFIED Gate Enforcement
```python
# In SourceManagement.set_verification():
if new_status == VERIFIED and (not s.locator or not s.quotation):
    raise ValueError("Cannot upgrade to VERIFIED: locator and quotation required")

# In SourceVerificationPolicy (verification.py):
policy.validate_verified(source) → List[str]  # missing fields
policy.enforce_verified(source) → raises ValueError if invalid
```

**No silent upgrades.** UNVERIFIED → VERIFIED requires explicit locator + quotation.

---

## ClaimRecord (claim.py)
Separates **what the source says** from **what the implementation does**:

| Claim Type | Purpose | Example |
|------------|---------|---------|
| **SOURCE_CLAIM** | "Source text says X" | "Mars in Aries gives strength" (with locator) |
| **INTERPRETATION_CLAIM** | "Tradition reads X as Y" | "Mars in Aries = courage" |
| **IMPLEMENTATION_CLAIM** | "Astrolife implements X as condition Y" | `planet_in_sign(Mars, Aries)` |
| **DEVELOPER_NOTE** | Internal documentation | "Test fixture for Phase 6D" |

```python
class ClaimRecord(BaseModel):
    claim_id: str
    claim_type: Literal["SOURCE_CLAIM", "INTERPRETATION_CLAIM", "IMPLEMENTATION_CLAIM", "DEVELOPER_NOTE"]
    rule_id: str
    rule_version: str
    text: str
    source_id: Optional[str]
    locator: Optional[str]
    quotation: Optional[str]
    verification_status: Literal["VERIFIED", "UNVERIFIED", "CONTESTED", "USER_SUPPLIED", "TRADITIONAL"]
    tradition: Optional[str]
    notes: str
    dependencies: List[str]
    model_config = {"frozen": True}
```

---

## Evidence → Source Linkage
```
SourceRecord (source_id, locator, quotation)
    ↓
ClaimRecord (claim_type=SOURCE_CLAIM, locator, quotation, source_id)
    ↓
EvidenceRecord (source_id, claim_id, fact_path, passed)
    ↓
EvidenceBundle (source_references, evidence_records)
    ↓
Traceability: RESULT → EVALUATION → RULE → DEPS → FACTS → EVIDENCE → SOURCE → CLAIM
```

---

## Audit Trail (audit.py — Phase 6C)
Append-only immutable log:
```python
class AuditRecord(BaseModel):
    audit_id: str          # "aud_<sha256(seq:event:rule:version:actor:reason:ts)[:12]>"
    event_type: str        # RULE_CREATED, VALIDATED, TESTED, REVIEWED, ACTIVATED, DISABLED, DEPRECATED, ARCHIVED, VERSION_CREATED
    rule_id: str
    version: str
    timestamp: str         # deterministic: "audit_step_{seq:06d}"
    actor: str
    reason: str
    payload: Dict[str, Any]
    model_config = {"frozen": True}

class AuditLog:
    def record(event_type, rule_id, version, actor, reason, payload, timestamp=None) → AuditRecord
    def get_records() → List[AuditRecord]
    def get_records_by_type(event_type) → List[AuditRecord]
    def get_records_for_rule(rule_id) → List[AuditRecord]
```

**Events recorded for provenance:**
- Source attached (`payload`: source_id, category, verification_status)
- Source verification changed (`payload`: old_status, new_status, locator_provided)
- Conflict recorded (`payload`: source_ids, both_marked_CONTESTED)
- Claim created (`payload`: claim_id, claim_type, source_id)
- Evidence attached (`payload`: evidence_id, source_id, claim_id)

---

## SourceVerificationPolicy (verification.py)
```python
class SourceVerificationPolicy(BaseModel):
    MIN_FIELDS_FOR_VERIFIED: List[str] = ["source_id", "locator", "quotation"]
    ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
        "UNVERIFIED": ["VERIFIED", "CONTESTED", "SECONDARY", "TRADITIONAL", "USER_SUPPLIED", "CUSTOM"],
        "VERIFIED": ["CONTESTED"],
        "CONTESTED": ["VERIFIED", "UNVERIFIED"],
        "SECONDARY": ["VERIFIED", "UNVERIFIED", "CONTESTED"],
        "TRADITIONAL": ["VERIFIED", "UNVERIFIED", "CONTESTED"],
        "USER_SUPPLIED": ["VERIFIED", "UNVERIFIED", "CONTESTED"],
        "CUSTOM": ["VERIFIED", "UNVERIFIED", "CONTESTED"],
    }
    
    def validate_verified(source: SourceRecord) → List[str]  # missing fields
    def enforce_verified(source: SourceRecord) → None  # raises ValueError
    def can_transition(from_status, to_status) → bool
    def verify_source(source) → SourceVerificationResult
```

---

## Integration with RulePackage
```python
# Source attached during draft creation
prov = RuleProvenance(
    source_reference=SourceReference(
        source_id="SRC-001",
        title="Brihat Parashara Hora Shastra",
        author="Parashara",
        publication="BPHS",
        locator="Ch. 36, Vs. 1-2",
        quotation="Moon in kendra from Jupiter forms Gaja Kesari",
        verification_status="VERIFIED",
    ),
    confidence="HIGH",
    provenance_status="VERIFIED",
)
pkg = create_rule_draft(..., provenance=prov, ...)

# SourceManagement can hold multiple sources
sm = SourceManagement()
sm = sm.add_source(SourceRecord(source_id="SRC-001", category=PRIMARY, verification_status=VERIFIED, ...))
sm = sm.add_source(SourceRecord(source_id="SRC-002", category=SECONDARY, verification_status=UNVERIFIED, ...))

# Conflict handling
sm_conf = sm.record_conflict(src_a, src_b)  # both marked CONTESTED
```

---

## Import/Export Provenance
```python
# Export includes full provenance
exp = export_package(pkg)
# exp.json_payload contains:
# {
#   "provenance": {
#     "source_reference": {"source_id": "...", "locator": "...", "quotation": "...", "verification_status": "VERIFIED"},
#     "source_type": "...", "source_author": "...", "source_title": "...",
#     "source_locator": "...", "provenance_status": "...", "confidence": "..."
#   },
#   "fingerprint": "..."
# }

# Import validates provenance
imp = import_package(json_str)
# Rejects if:
# - VERIFIED without locator/quotation
# - Invalid source_id references
# - Tradition firewall violations
```

---

## Deprecated: ProvenanceRecord (5A)
**File:** `core/rules/provenance.py`  
**Status:** DEPRECATED — mutable, non-deterministic timestamps

```python
@dataclass
class ProvenanceRecord:
    created_at: str = datetime.utcnow().isoformat()  # NON-DETERMINISTIC
    updated_at: str = datetime.utcnow().isoformat()  # NON-DETERMINISTIC
    verified_at: str = ""                            # NON-DETERMINISTIC
    # ... mutable registry
```

**Migration:** Use `RuleProvenance` (schema.py) + `SourceRecord` (source.py) + `AuditLog` (audit.py) instead.

---

## Best Practices
1. **Never fabricate classical quotations** — use UNVERIFIED or USER_SUPPLIED
2. **Always provide locator for VERIFIED** — chapter, verse, page, section
3. **Separate claims** — SOURCE_CLAIM vs IMPLEMENTATION_CLAIM
4. **Preserve conflicts** — CONTESTED, never auto-resolve
5. **Tradition isolation** — Jaimini sources never satisfy Parashari rules
6. **Audit everything** — source attachments, verification changes, conflicts