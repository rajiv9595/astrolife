# ASTROLIFE V2 — PHASE 6E AUDIT

**Date:** 2026-09-05
**Scope:** Knowledge / Rule Catalogue + Cross-System Applicability Engine
**Mode:** Machine-readable catalogue + applicability only. No AI, no prediction, no interpretation, no new astronomy.

## 1. Repository layout audited

| Path | Contents | Reuse decision |
|---|---|---|
| `backend/core/rules/` | `registry.py` (5A RuleRegistry), `evaluator.py`, `context.py`, `evidence.py`, `provenance.py`, `enums.py` (RuleCategory/RuleTradition/RuleStatus…), `validators.py`, parashari/doshas sub-pkgs | Reuse enums (aliased, not duplicated); reuse evaluator/context shape; do NOT modify |
| `backend/core/rules/dynamic/` | `schema.py` (DynamicRuleDefinition), `registry.py` (DynamicRuleRegistry), `rule_package.py` (RulePackage/TestCase/Health/Diff), `resolver.py` (CanonicalFactResolver), `results.py` (DynamicRuleResult), `engine.py`, `bindings.py` (required_paths), `namespace.py`, `dsl.py`, `validators.py` (FIREWALL), `lifecycle.py`, `fingerprint.py`, `diff.py`, `catalogue.py`, `evidence_record.py` (EvidenceBundle), `evidence_graph.py` (EvidenceGraph), `claim.py`, `source.py`, `verification.py`, `service.py` | Reuse all; do NOT duplicate. New module imports from these |
| `backend/core/rules/dynamic/__init__.py` | Re-exports 6A–6D surface | Additive export of 6E only |
| `backend/core/jaimini/` | `rules/catalogue.py` (12 Jaimini specs), `dependencies.py` (DEPENDENCY_SPECS), `conflicts.py` (SAME_PROPOSITION_PAIRS, REPORTED_ONLY), `profile.py`, `dasha/profile.py` (3 Chara profiles) | Reuse catalogue + dependency specs + conflict pairs |
| `backend/core/rules/parashari/catalog.py` | 31 rules, `build_parashari_catalog()`, `build_manifest()` | Ingest read-only |
| `backend/core/rules/doshas/catalog.py` | 6 rules, `build_dosha_catalog()`, `build_manifest()` | Ingest read-only |
| `backend/core/strength/` | pipeline/models (StrengthReport) | Read-only via resolver |
| `backend/core/calculation/` (dasha.py, varga.py, pipeline.py) | Vimshottari timeline, varga facts, ChartFacts | Read-only via resolver |
| `backend/core/transit/` | calculator (TransitSnapshot) | Read-only via resolver |
| Golden fixtures | `test_dynamic_rules_phase6b.py` golden context (2005-08-17 00:02 Asia/Kolkata, DT=2026-01-01Z); 6D golden fixtures | Reuse golden chart coordinates for 6E golden applicability |

## 2. Accepted rule inventory (existing, no new astrology)

- Parashari: **31** rules (`PARASHARI.YOGA.*`, tradition PARASHARI_CLASSICAL, versions 1.0.0, status ENABLED).
- Dosha: **6** rules (`DOSHA.*`, mixed PARASHARI_CLASSICAL/MODERN_COMMON via PITRU).
- Jaimini: **12** rules (`JAI.*`, tradition JAIMINI, origin CLASSICAL_JAIMINI/TRADITION_DEPENDENT, version 1.0.0).
- Dynamic custom: synthetic fixtures only (DEMO.*/CUSTOM.*), tradition CUSTOM_DEVELOPER, verification USER_SUPPLIED/UNVERIFIED.
- Total classical accepted base: **49** rules. 6E adds 6 CUSTOM synthetic fixtures → golden catalogue **55** entries.

## 3. Taxonomy gaps found (to bridge, not to change)

- Legacy `RuleTradition`: PARASHARI_CLASSICAL, JAIMINI, TRADITION_DEPENDENT, WESTERN, CUSTOM. 6E canonical adds JAIMINI_CLASSICAL (= JAIMINI alias), MODERN_COMMON, CUSTOM_DEVELOPER (= CUSTOM alias). Aliasing enforced in one normalizer.
- Legacy `RuleCategory`: YOGA, DOSHA, JAIMINI, STRENGTH, DIGNITY, HOUSE, LORDSHIP, ASPECT, TIMING, CUSTOM. 6E adds SIGN, VARGA, KARAKA, ARUDHA, RASHI_DRISHTI, DASHA, TRANSIT, PANCHANGA. Mapping table in `knowledge.py`; JAIMINI category split by rule-id prefix.
- Legacy lifecycle `RuleStatus` (ENABLED/DISABLED/DEPRECATED/EXPERIMENTAL) vs dynamic lifecycle states (DRAFT…ARCHIVED). 6E catalogue stores `lifecycle_status` verbatim from source and maps ENABLED→ACTIVE-equivalent for discovery.
- Chara Dasha profiles: 3 implemented methods (`…MOVABLE_FIXED_DUAL`, `…ODD_EVEN_FOOTED`, `…MOVABLE_FIXED_DUAL_ALWAYS`). Used as `profile_constraints` values.

## 4. Reused infrastructure (no duplication)

DynamicRuleRegistry, RulePackage, DynamicRuleDefinition, CanonicalFactResolver (+RESOLVED/MISSING/INVALID/UNAVAILABLE),
DynamicRuleResult, EvidenceBundle, EvidenceGraph, RuleDependencySpec/DEPENDENCY_SPECS, SAME_PROPOSITION_PAIRS/RuleConflict,
lifecycle transitions, provenance/SourceRecord/verification, fingerprint/diff, namespace match, required_paths, dsl suspicious scan.

## 5. Files to create / modify / protect

**CREATE:**
- `backend/core/rules/dynamic/knowledge.py` — unified catalogue + applicability + indexes + health + graph + snapshot + golden + API (single new module, no semantic changes elsewhere)
- `backend/test_dynamic_rules_phase6e.py` — 6E suite
- `ASTROLIFE_V2_PHASE6E_AUDIT.md` (this file)
- `ASTROLIFE_V2_PHASE6E_ARCHITECTURE.md`, `ASTROLIFE_V2_PHASE6E_CATALOGUE.md`, `ASTROLIFE_V2_PHASE6E_APPLICABILITY.md`, `ASTROLIFE_V2_PHASE6E_KNOWLEDGE_GRAPH.md`, `ASTROLIFE_V2_PHASE6E_TEST_REPORT.md`

**MODIFY:**
- `backend/core/rules/dynamic/__init__.py` — additive re-export of knowledge API only (no existing symbol changed)

**PROTECTED (read-only, stop-and-report before any change):**
- `backend/core/calculation/*`, `backend/core/rules/parashari/*`, `backend/core/rules/doshas/*`, `backend/core/jaimini/*`, `backend/core/strength/*`, `backend/core/transit/*`, all accepted test files, golden snapshots.

## 6. Risks / limitations

- Classical rules have no dynamic condition trees; their `applicability_spec` is derived from family-level dependency metadata (Jaimini DEPENDENCY_SPECS) or generic natal availability (Parashari/Dosha). This answers eligibility, never formation.
- `strength.bhava.*` namespace validates but resolver reports MISSING/UNAVAILABLE (accepted 6B behavior); specs avoid bhava probes.
- No prediction, no scoring, no ranking anywhere in 6E by construction.
