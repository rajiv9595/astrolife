# ASTROLIFE V2 — PHASE 6E CATALOGUE

**Builder:** `build_golden_catalogue()` in `backend/core/rules/dynamic/knowledge.py`
**Size:** 56 entries = 31 Parashari + 6 Dosha + 12 Jaimini + 6 required CUSTOM + 1 deprecated guard.
**No new classical claims.** Customs are synthetic fixtures (`DEV-6E-SYNTHETIC`,
`USER_SUPPLIED` / `CUSTOM`, `CUSTOM_DEVELOPER`).

## 1. Entry composition (§3)

Every entry: rule_id, rule_version, name, description, system, tradition,
category, subcategory, lifecycle_status, validation_status, provenance_status,
source_ids, evidence_ids, dependency_manifest, fingerprint (sha256 over the
canonical dict), supersedes, superseded_by, conflicts, applicability_spec.

## 2. System / tradition / category placement (§4, §5, §25)

| Family | System | Tradition | Category | Count |
|---|---|---|---|---|
| Parashari yogas (`PARASHARI.YOGA.*`) | PARASHARI | PARASHARI_CLASSICAL | YOGA | 31 |
| Doshas (`DOSHA.*`) | DOSHA | PARASHARI_CLASSICAL / MODERN_COMMON (PITRU) | DOSHA | 6 |
| Jaimini karaka (`JAI.KARAKA.*`, `JAI.KARAKAMSHA.*`) | JAIMINI | JAIMINI_CLASSICAL | KARAKA | 4 |
| Jaimini drishti (`JAI.DRISHTI.*`) | JAIMINI | JAIMINI_CLASSICAL | RASHI_DRISHTI | 3 |
| Jaimini arudha (`JAI.ARUDHA.*`, `JAI.SWAMSA.*`) | JAIMINI | JAIMINI_CLASSICAL | ARUDHA | 5 |
| Synthetic customs (`CUSTOM.*.TEST`) | DYNAMIC_CUSTOM | CUSTOM_DEVELOPER | CUSTOM | 6 + 1 guard |

Subcategory carries method / origin label (`CLASSICAL_JAIMINI` vs
`TRADITION_DEPENDENT` preserved verbatim from the 5E catalogue).
STRENGTH / PANCHANGA / DASHA / TRANSIT / VARGA systems are supported by the
taxonomy; no accepted standalone rules exist in them yet, so they are
documented as empty rather than invented.

## 3. Versions (§20)

Exact `(rule_id, version)` identity; `get_rule_version` reproduces bytes.
`latest_active_version` is explicit and never silently substituted into
evaluation paths. The scratch (non-golden) test demonstrates 1.0.0 vs 1.1.0
coexistence with distinct fingerprints.

## 4. Sources & evidence (§18, §21)

Entries expose `source_count`, `evidence_count`, `conflict_count` — counts
only. Verification states (`UNVERIFIED` classical, `USER_SUPPLIED` customs)
remain distinct; no score, no ranking, no authenticity inference.
`find_rules_by_source("DEV-6E-SYNTHETIC")` answers "supported by source X".

## 5. Conflicts (§19)

3+ Jaimini same-proposition pairs (incl. `AK_AMK_CONJUNCTION` vs
`AK_AMK_MUTUAL`) exposed as `CONFLICT:<hex>` records with rule_a/b,
tradition_a/b, version_a/b, `conflict_type=REPORTED_ONLY`,
`status=REPORTED_ONLY`. No automatic winner.

## 6. Snapshot (§24)

`CatalogueSnapshot`: entries, active_rules, versions, dependencies, sources,
evidence_references, conflicts, fingerprints. Canonical JSON
(`sort_keys`, compact separators); `snapshot_round_trip` asserts byte equality.

## 7. Dependency answers (§16, §17)

- D9 → `CUSTOM.D9.TEST` + Jaimini D9 rules; Shadbala → `CUSTOM.STRENGTH.TEST`;
  Vimshottari → `CUSTOM.DASHA.TEST`; Jupiter transit → `CUSTOM.TRANSIT.TEST`;
  Rashi Drishti → 5+ Jaimini rules; AL → 3+; UL → 2+.
- `reverse_index()`: fact → sorted `rule@version` list.
- `dependencies_of(id, version)`: rule → manifest (KeyError on unknown).
