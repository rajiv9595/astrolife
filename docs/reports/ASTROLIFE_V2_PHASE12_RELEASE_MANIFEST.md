# Astrolife V2 — Phase 12 Release Manifest

Deterministic release manifest. Only explicitly external deployment metadata (frontend build hash, deploy timestamp) may vary; all version/fingerprint fields below are deterministic.

---

## 1. Application & API

| Field | Value |
|---|---|
| Application version | `12.0.0` |
| API version | `v1` |

## 2. Astrology Truth Layer (FROZEN)

| Field | Value |
|---|---|
| Calculation engine | `core/calculation (Lahiri, Mean Node, Whole Sign)` |
| Schema version | `6A/1.0.0` |
| Rule catalogue | `parashari-31/dosha-6/jaimini-12` |
| Evidence catalogue | `6D/1.0.0` |
| Prediction catalogue | `phase8/1.0.0` |
| Research catalogue | `phase9/1.0.0` |

## 3. Fingerprints

| Field | Value |
|---|---|
| Golden data SHA-256 (`backend/core/regression/golden_data.json`) | `df90a6579ff7e60dddbec107de6763b3b1f732b28e5e5ab5dca9bc4ae67812ba` |
| Parashari rule count | `31` |
| Regression fingerprint | `106073-executed/106035-unique/0-failures/phase12-accepted` |

## 4. Canonical Fingerprint Composition

The canonical fingerprint deterministically comprises:
- calculation profile
- calculation engine version
- rule catalogue version
- evidence catalogue version
- prediction catalogue version
- research catalogue version

**Request IDs are excluded** (observability metadata only). 50-run determinism yields one unique fingerprint.

## 5. External / Non-deterministic Fields

- Frontend `dist` build hash (asset filenames include content hashes).
- Deploy timestamp / commit hash.
- These do not affect astrology truth or canonical fingerprints.

## 6. Backward Compatibility

- `API_VERSION = v1` unchanged.
- No frontend endpoint broken by Phase 12 (additive ops only).
- Schema `6A/1.0.0` unchanged; migration `migrate_db.py` non-destructive (manual, `DROP NOT NULL` only).

---

Generated deterministically by `core.ops.manifest.build_release_manifest()`. Verified in Phase 12 tests 20/34 (golden SHA recomputed matches, rule count integer == 31). Regression fingerprint reflects the accepted Phase 12 full-suite run: **106,073 executed / 106,035 unique / 0 failures**. (Reconciliation note: historical suite re-run recorded `test_jaimini_dasha_phase5gh` at 63 vs 62 in the as-written Phase 11 report — an all-green +1 count reconciliation, not a regression.)
