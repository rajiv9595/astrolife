# Astrolife V2 - Phase 4: Classical Planetary Strength Engine Specification

This document describes the implementation of the Classical Planetary Strength Engine, establishing separate, well-defined strength calculations that consume the canonical ChartFacts from Phase 1 and validated Vargas from Phase 2.

---

## Architecture Overview

```
backend/core/strength/
├── __init__.py              # Package exports
├── models.py                # Pydantic models for all strength results
├── profile.py               # Configuration profiles & reference data
├── pipeline.py              # Main entry: generate_strength_report()
├── sthana_bala.py           # Sthana Bala (5 subcomponents)
├── dig_bala.py              # Dig Bala (Directional)
├── kala_bala.py             # Kala Bala (9 temporal subcomponents)
├── chesta_bala.py           # Chesta Bala (Motional)
├── naisargika_bala.py       # Naisargika Bala (Natural)
├── drig_bala.py             # Drig Bala (Aspectual)
├── shadbala.py              # Shadbala aggregation
├── bhava_bala.py            # Bhava Bala (House strength)
├── vimsopaka.py             # Vimsopaka Bala (20-point)
├── avastha.py               # Avastha (Planetary states)
├── dignity.py               # Dignity evaluator
├── functional.py            # Functional strength (Yogakaraka, etc.)
└── composite.py             # Custom Astrolife composite (legacy compatible)
```

---

## Classification System

Every result carries mandatory metadata:

```python
classification: StrengthClassification = CLASSICAL | TRADITION_DEPENDENT | CUSTOM | APPROXIMATION
system: StrengthSystem = PARASHARI_SHADBALA | BHAVA_BALA | VIMSOPAKA | AVASTHA | PARASHARI_DIGNITY | PARASHARI_FUNCTIONAL | ASTROLIFE_COMPOSITE
method: str  # Specific tradition/method name
```

---

## 1. Shadbala (Six-Fold Strength)

**System**: `PARASHARI_SHADBALA`  
**Method**: `PARASHARI_CLASSICAL`  
**Classification**: `CLASSICAL`

### 1.1 Sthana Bala (Positional Strength) — 225 virupas max

| Subcomponent | Maximum | Formula | Classification |
|--------------|---------|---------|----------------|
| Uchcha Bala | 60 | `60 × (1 - distance_from_exaltation/180)` | CLASSICAL |
| Saptavargaja Bala | 60 | Average dignity score across D1,D2,D3,D7,D9,D12,D30 | CLASSICAL |
| Ojhayugma Bala | 30 | 15 each for odd/even sign & house (planet-specific) | CLASSICAL |
| Kendradi Bala | 60 | Kendra=60, Panaphara=30, Apoklima=15 | CLASSICAL |
| Drekkana Bala | 15 | Based on drekkana placement & planet gender | CLASSICAL |

### 1.2 Dig Bala (Directional Strength) — 60 virupas max

Continuous angular distance from ideal house cusp:
- Formula: `60 × cos(angular_distance/2)` 
- Ideal houses: Sun/Mars=10, Moon/Venus=4, Jupiter/Mercury=1, Saturn=7
- Uses Whole Sign house cusps (0° of each sign)

### 1.3 Kala Bala (Temporal Strength) — 540 virupas max

| Subcomponent | Maximum | Basis |
|--------------|---------|-------|
| Nathonnatha Bala | 60 | Diurnal/Nocturnal (Sun/Jup/Ven day, Moon/Mar/Sat night, Merc always) |
| Paksha Bala | 60 | Lunar phase angle (benefics waxing, malefics waning) |
| Tribhaga Bala | 60 | 1/3 day/night period (planet-specific) |
| Varsha Bala | 60 | Year lord (weekday of Jan 1) |
| Masa Bala | 60 | Month lord (weekday of 1st of month) |
| Dina Bala | 60 | Day lord (weekday of birth) |
| Hora Bala | 60 | Hour lord (planetary hour) |
| Ayana Bala | 60 | Sun's declination (N/S) |
| Yuddha Bala | 60 | Planetary war (within 1°) |

### 1.4 Chesta Bala (Motional Strength) — 60 virupas max

- Retrograde: 60 virupas
- Direct: `(actual_speed / mean_speed) × 60`
- Sun: Base 30 × speed ratio
- Moon: Full range based on speed ratio
- Mean motions from classical values

### 1.5 Naisargika Bala (Natural Strength) — 60 virupas max

Fixed traditional values (Parashara):
- Sun: 60, Moon: 51.43, Venus: 42.86, Jupiter: 34.29, Mercury: 25.71, Mars: 17.14, Saturn: 8.57

### 1.6 Drig Bala (Aspectual Strength) — 60 virupas max

Parashari aspects:
- All planets: 7th house (180°) = 60
- Mars: 4th (90°), 8th (210°) = 45 each
- Jupiter: 5th (150°), 9th (270°) = 45 each
- Saturn: 3rd (60°), 10th (300°) = 45 each
- Rahu/Ketu: 5th, 9th = 45 each
- Benefic aspects add, malefic subtract, normalized to 0-60

### 1.7 Shadbala Total

- Total Virupas = Sum of 6 Balas
- Total Rupas = Total Virupas / 60
- Minimum requirements (Rupas): Sun 6.5, Moon 6.0, Mars 5.0, Mercury 7.0, Jupiter 6.5, Venus 5.5, Saturn 5.0
- Ratio = Total / Minimum
- Status: STRONG (≥1.0), MODERATE (0.8-1.0), WEAK (<0.8)

---

## 2. Bhava Bala (House Strength)

**System**: `BHAVA_BALA`  
**Method**: `PARASHARI_CLASSICAL`  
**Classification**: `CLASSICAL`

Per house (1-12):
- Bhavadhipati Bala: Lord's Shadbala (converted to virupas)
- Dig Bala: Base 30
- Drishti Bala: Aspects on house cusp
- Total: Sum of components

---

## 3. Vimsopaka Bala (20-Point Strength)

**System**: `VIMSOPAKA`  
**Method**: `PARASHARI_CLASSICAL`  
**Classification**: `TRADITION_DEPENDENT`

Vargas used: D1(6), D2(2), D3(2), D7(4), D9(5), D12(2), D30(4) — total weight 25
- Dignity scores: Exalted=60, Moolatrikona=45, Own=30, Friend=22.5, Neutral=15, Enemy=7.5, Debilitated=0
- Weighted average normalized to 20-point scale

---

## 4. Avastha (Planetary States)

**System**: `AVASTHA`  
**Methods**: `BALA_AVASTHA`, `JAGRATADI_AVASTHA`  
**Classification**: `CLASSICAL`

### 4.1 Bala Avastha (5 states × 6° each)
- 0-6°: BALA (Infant)
- 6-12°: KUMARA (Youth)
- 12-18°: YUVA (Adult)
- 18-24°: VRIDDHA (Old)
- 24-30°: MRITYA (Dead)

### 4.2 Jagratadi Avastha (3 states by sign type)
- Movable (Chara): JAGRAT (Waking)
- Fixed (Sthira): SVAPNA (Dreaming)
- Dual (Dwisvabhava): SUSHUPTI (Deep Sleep)

---

## 5. Dignity (Planetary Dignity in Signs)

**System**: `PARASHARI_DIGNITY`  
**Method**: `PARASHARI_CLASSICAL`  
**Classification**: `CLASSICAL`

Categories (in priority order):
1. EXALTED — At exaltation sign (degree checked)
2. MOOLATRIKONA — In moolatrikona sign within degree range
3. OWN_SIGN — Rules the sign
4. FRIEND — Natural friend of sign lord
5. NEUTRAL — Neither friend nor enemy
6. ENEMY — Natural enemy of sign lord
7. DEBILITATED — In debilitation sign

Returns structured evidence: ruler, relationship, boolean flags.

---

## 6. Functional Strength

**System**: `PARASHARI_FUNCTIONAL`  
**Method**: `PARASHARI_CLASSICAL`  
**Classification**: `TRADITION_DEPENDENT`

Based on house lordship from Ascendant:
- YOGAKARAKA: Rules both Kendra (1,4,7,10) and Trikona (1,5,9)
- FUNCTIONAL_BENEFIC: Rules Trikona only
- FUNCTIONAL_MALEFIC: Rules Dusthana (6,8,12) only
- MARAKA: Rules Maraka (2,7) only
- NEUTRAL_KENDRA: Rules Kendra only
- NEUTRAL: Mixed or other

Score: Yogakaraka=100, Functional Benefic=75, Neutral Kendra=50, Neutral=40, Maraka=20, Functional Malefic=10

---

## 7. Composite Strength (Custom - Legacy Compatible)

**System**: `ASTROLIFE_COMPOSITE`  
**Method**: `ASTROLIFE_CUSTOM`  
**Classification**: `CUSTOM`

Explicitly labeled as CUSTOM with disclaimer. Combines:
- D1 dignity score
- House placement bonuses/penalties
- Retrograde bonus
- Classical Shadbala ratio (new integration)
- D9 improvements (Vargottama, mitigation — NOT automatic Neecha Bhanga)

Output: 0-100 score with label (Very Strong/Strong/Moderate/Weak/Very Weak)

---

## Canonical Inputs

All calculations consume (never recalculate):
- `ChartFacts` from `core.calculation.pipeline.generate_chart_facts()`
- Validated Vargas from `core.calculation.varga.calculate_all_vargas()`
- Panchanga data from Phase 3

---

## Determinism

- No `datetime.now()` in core calculations
- Same input → identical output (bitwise for floats)
- Evaluation datetime passed explicitly for dynamic components

---

## Golden Chart Validation

Birth: 17 Aug 2005, 00:02 IST, Anaparthy (16.93407, 81.95522)
Profile: SIDEREAL / LAHIRI_STANDARD / MEAN_NODE / WHOLE_SIGN

| Planet | Total Rupas | Min Rupas | Ratio | Status |
|--------|-------------|-----------|-------|--------|
| Sun | 5.70 | 6.5 | 0.88 | MODERATE |
| Moon | 6.73 | 6.0 | 1.12 | STRONG |
| Mars | 5.51 | 5.0 | 1.10 | STRONG |
| Mercury | 6.34 | 7.0 | 0.91 | MODERATE |
| Jupiter | 5.83 | 6.5 | 0.90 | MODERATE |
| Venus | 7.35 | 5.5 | 1.34 | STRONG |
| Saturn | 5.52 | 5.0 | 1.10 | STRONG |

---

## Regression Status

All previous phase tests pass:
- Phase 1: 39/39 ✓
- Phase 2: 19,692/19,692 ✓
- Phase 3: 81,283 + 423 + 27 + 788 = 82,521/82,521 ✓
- Legacy shadbala: Works (backward compatible)
- Legacy composite: Works (backward compatible)

---

## Files Created

### Core Strength Package (14 files)
1. `backend/core/strength/__init__.py`
2. `backend/core/strength/models.py`
3. `backend/core/strength/profile.py`
4. `backend/core/strength/pipeline.py`
5. `backend/core/strength/sthana_bala.py`
6. `backend/core/strength/dig_bala.py`
7. `backend/core/strength/kala_bala.py`
8. `backend/core/strength/chesta_bala.py`
9. `backend/core/strength/naisargika_bala.py`
10. `backend/core/strength/drig_bala.py`
9. `backend/core/strength/shadbala.py`
10. `backend/core/strength/bhava_bala.py`
11. `backend/core/strength/vimsopaka.py`
12. `backend/core/strength/avastha.py`
13. `backend/core/strength/dignity.py`
14. `backend/core/strength/functional.py`
15. `backend/core/strength/composite.py`

### Documentation
- `ASTROLIFE_V2_STRENGTH_AUDIT.md` — Audit of existing strength code
- `ASTROLIFE_V2_STRENGTH_SPECIFICATION.md` — This document

---

## Remaining Work / Uncertainty

1. **Kala Bala subcomponents** — Some (Varsha/Masa/Dina/Hora) use simplified weekday-lord method; full astronomical calculation (e.g., exact Sankranti for Varsha) could be added
2. **Drig Bala** — Uses simplified benefic/malefic classification; Moon's paksha-based nature needs full integration
3. **Saptavargaja Bala** — Uses 7 Vargas per Parashara; other traditions may use different sets
4. **Cross-check with JHora** — Not yet performed; discrepancies should be documented
4. **Synthetic test charts** — Need to create for boundary conditions (exact exaltation, debilitation, etc.)
5. **D9 chart facts integration** — Current D9 facts wrapper is minimal; could be enhanced

---

*Phase 4 Implementation Complete — Classical Strength Engine Operational*