# ASTROLIFE V2 — PHASE 5C: TEST REPORT

## Test Summary

| Metric | Count |
|--------|-------|
| **Phase 5C Tests** | **157 passed, 0 failed** |
| Phase 1 Regression | 39 / 39 |
| Phase 2 Regression | 19,692 / 19,692 |
| Phase 3 Regression (Transit) | 788 / 788 |
| Phase 3 Regression (Panchanga) | 423 / 423 |
| Phase 4B Regression | 87 / 87 |
| Phase 5A Regression | 185 / 185 |
| Phase 5B Regression | 355 / 355 |
| **Total Regression** | **21,569 / 21,569** |

## Phase 5C Test Breakdown

### Catalogue Integrity (24 tests)
- 6 expected rule IDs present and unique
- Category = DOSHA for all rules
- Tradition declared for all rules
- Formation conditions present
- Provenance source present
- No prediction/fear language

### Manglik Lagna Method (18 tests)
- Mars in houses 1, 2, 4, 7, 8, 12 from Lagna → FORMED (6 tests)
- Mars in houses 3, 5, 6, 9, 10, 11 from Lagna → NOT_FORMED (6 tests)
- Method metadata verification
- Evidence presence

### Manglik Moon Method (2 tests)
- Mars in 7th from Moon → FORMED
- Mars NOT in dosha houses from Moon → NOT_FORMED

### Manglik Venus Method (2 tests)
- Mars in 8th from Venus → FORMED
- Mars NOT in dosha houses from Venus → NOT_FORMED

### Manglik Exhaustive Sweep (12 tests)
- Mars in all 12 houses from Aries Lagna
- Each house correctly classified as FORMED or NOT_FORMED

### Manglik Cancellation (2 tests)
- Jupiter conjunct Mars → CANCELLED
- Jupiter aspects Mars (5th aspect) → CANCELLED

### Manglik Mitigation (1 test)
- Mars exalted → MITIGATED

### Manglik Severity (3 tests)
- Debilitated Mars → HIGH or MODERATE
- Exalted Mars → LOW
- Not formed → NONE

### Kemadruma Dosha (5 tests)
- Isolated Moon → FORMED
- Planet in 2nd from Moon → NOT_FORMED
- Planet in 12th from Moon → NOT_FORMED
- Planet in kendra from Moon → NOT_FORMED
- Jupiter aspects Moon → CANCELLED

### Kala Sarpa Dosha (4 tests)
- All 7 planets inside arc → FORMED
- Planets outside arc → NOT_FORMED
- Boundary case (planet on Rahu sign)
- Wrap-around configuration

### Kala Sarpa Cancellation (1 test)
- Jupiter in Ascendant → CANCELLED

### Pitru Dosha (3 tests)
- Sun conjunct Rahu → FORMED
- Rahu in 9th house → FORMED
- No conditions met → NOT_FORMED

### No Prediction / No Fear Language (12 tests)
- All dosha rules checked for forbidden words

### Evidence Quality (12 tests)
- All doshas have evidence when evaluated
- All evidence items have subject and significance

### Golden Chart Integration (1 test)
- All 6 doshas evaluated against canonical birth data
- Snapshot written to golden_dosha_snapshot.json

### Determinism (1 test)
- Identical inputs produce identical outputs

### Manifest (2 tests)
- Manifest has entries
- All entries have required fields

### 12-Ascendant Sweep (1 test)
- Manglik Lagna method: 12/12 ascendants correct

### No-AI Guard (5 tests)
- No AI library imports in any dosha module

## Known Limitations

1. **dasha_phase3.py and dynamic_phase3.py** — Pre-existing path resolution errors (not caused by Phase 5C)
2. **Kala Sarpa severity** — No validated classical severity scale; returns UNKNOWN
3. **Pitru Dosha confidence** — Marked TRADITION_DEPENDENT; formation rules are modern synthesis
4. **Manglik cancellation** — Own-sign cancellation is disputed; implemented as partial only
5. **Kemadruma Sun special case** — Sun conjunction with Moon (Amavasya) treated as partial mitigation only
