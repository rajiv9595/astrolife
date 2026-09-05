# ASTROLIFE V2 — PHASE 6A: PROVENANCE

**Models:** `SourceReference`, `RuleProvenance` (`schema.py`); firewall +
checks (`validators.py`).

## 1. SourceReference

source_id, title, author, publication, locator, quotation, verification_status
∈ VERIFIED | UNVERIFIED | CONTESTED | SECONDARY | TRADITIONAL |
USER_SUPPLIED | CUSTOM. VERIFIED requires locator or quotation (enforced).
Developer/user-supplied sources stay USER_SUPPLIED/CUSTOM until independently
verified. No auto-verification exists in 6A.

## 2. Tradition Isolation & Firewall

Traditions: PARASHARI_CLASSICAL, JAIMINI_CLASSICAL, TRADITION_DEPENDENT,
MODERN_COMMON, WESTERN, CUSTOM_DEVELOPER. Explicit per-tradition read
namespaces (`FIREWALL`): e.g. JAIMINI_CLASSICAL ⇒ natal/houses/jaimini/varga/
dasha/transit/rule (no aspects/strength/Western); WESTERN ⇒ no jaimini.*;
PARASHARI ⇒ no jaimini.drishti. Violations fail validation; conflicting
results coexist with provenance (evaluator never picks winners).

## 3. Golden Fixture Honesty

`DEMO.CUSTOM.SYNTHETIC_GOLDEN` is CUSTOM_DEVELOPER / USER_SUPPLIED /
UNVERIFIED provenance with CUSTOM confidence, explicitly "not a classical
rule". It exercises formation + cancellation + mitigation, a D9 dependency, a
rule dependency, evidence, and UNKNOWN behavior.
