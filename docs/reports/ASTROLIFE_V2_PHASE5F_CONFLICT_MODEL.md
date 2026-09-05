# ASTROLIFE V2 — PHASE 5F: CONFLICT MODEL

**Module:** `backend/core/jaimini/conflicts.py` — deterministic, report-only
(`resolution` is always `REPORTED_ONLY`; no precedence, no auto-resolution).

## 1. Classes

| Class | Trigger |
| :--- | :--- |
| `DIRECT_CONTRADICTION` | Same-proposition pair with definitionally incompatible outcomes both FORMED (integrity alarm; e.g. disjoint conjunction vs mutual-drishti) |
| `APPARENT_CONTRADICTION` | Reserved; no 5E pair qualifies |
| `DIFFERENT_DIMENSIONS` | Same subject matter, distinct conditions, no contradiction (golden: all 3 pairs) |
| `TRADITION_VARIANT` | Same proposition viewed under different origin labels |
| `INSUFFICIENT_INFORMATION` | A participant is UNKNOWN (UNCERTAIN) — undecidable |
| `NO_CONFLICT` | Default for independent pairs (not emitted as records) |

## 2. Same-Proposition Pairs (explicit, metadata-level)

1. `AK_AMK_CONJUNCTION` × `AK_AMK_MUTUAL` — AK–AmK relationship (disjoint).
2. `DK_UL_SAMBANDHA` × `A7_UL_ALIGNMENT` — UL family dimension via DK vs A7.
3. `KARAKAMSHA_BENEFIC` × `SWAMSA_BENEFIC` — D9 benefic dimension, separate signs.

`same_proposition=True` marks shared subject matter; the class records whether
the conditions actually collide. Dimension tags (`DIMENSIONS`) document each
rule's subject for future pairs.

## 3. Tradition Handling

Cross-origin same-proposition evaluation yields `TRADITION_VARIANT`, keeping
`CLASSICAL_JAIMINI` / `TRADITION_DEPENDENT` results distinguishable under
profile-subset evaluation (5/7/12 rule subsets, formed subsets consistent).
