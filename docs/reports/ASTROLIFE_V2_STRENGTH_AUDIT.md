# Astrolife V2 - Phase 4: Strength Audit

This document records the baseline inventory of all planetary strength calculations present in the repository prior to Phase 4 migration.

---

## 1. Existing Strength Implementations

### 1.1 `backend/shadbala.py` — `compute_shadbala()`

**Purpose**: Computes a "simplified Shadbala" for 7 primary planets

**Input**: 
- `planets`: Dict of planet data (from legacy `compute_chart`)
- `asc_sign`: Ascendant sign string
- `is_day_birth`: Boolean

**Output**: Dict per planet with 6 components + total in Virupas and Rupas

| Component | Formula | Classical? | Units | Notes |
|-----------|---------|------------|-------|-------|
| **Sthana Bala** | Distance from exaltation point: `max(0, 60 - distance/3)` where distance = angular distance from exact exaltation degree | APPROXIMATION | Virupas (0-60) | Uses only Uchcha Bala concept; ignores Saptavargaja, Ojhayugma, Kendradi, Drekkana |
| **Dig Bala** | House distance from Dig Bala house: `max(0, 60 - house_dist * 10)` | APPROXIMATION | Virupas (0-60) | Whole Sign house distance only; no continuous angular calculation |
| **Kaala Bala** | Diurnal: 60 day / 30 night; Nocturnal: 30 day / 60 night; Mercury: 60 always | APPROXIMATION | Virupas (30/60) | Only day/night binary; ignores Nathonnatha, Paksha, Tribhaga, Varsha/Masa/Dina/Hora, Ayana, Yuddha |
| **Chesta Bala** | Retrograde = 60, Direct = 30, Sun/Moon = 30 | APPROXIMATION | Virupas (30/60) | Binary retrograde/direct; no speed-based calculation |
| **Naisargika Bala** | Fixed table: Sun=60, Moon=51.43, Venus=42.85, Jupiter=34.28, Mercury=25.7, Mars=17.14, Saturn=8.57 | CLASSICAL (values) | Virupas | Traditional values preserved |
| **Drig Bala** | Constant 30 for all planets | PLACEHOLDER | Virupas | Explicitly noted as "baseline unless full aspecting engine wired" |

**Total**: Sum of 6 components → converted to Rupas (÷60)

**Strength Level**: High ≥3.8 Rupas, Medium ≥3.2, Low <3.2

**Consumers**: 
- `backend/routes/astro.py` line 89 (`shadbala_data` in API response)
- `backend/verify_shadbala.py` (test script)

**Classification**: **SIMPLIFIED / APPROXIMATION** — The function docstring explicitly says "Computes a simplified Shadbala"

---

### 1.2 `backend/strength_evaluator.py` — `evaluate_planet_strength()` / `calculate_chart_strengths()`

**Purpose**: Custom composite strength score (0-100 normalized) with textual labels

**Input**:
- `planet_name`, `p_data` (planet dict from chart)
- `asc_sign`: Ascendant sign
- `d9_planets`: D9 planet list

**Output**: Per planet: `score` (0-100), `label` (Very Strong/Strong/Moderate/Weak/Very Weak), `nature` (dignity), `reasons` (list of strings)

**Scoring Components**:

| Component | Formula | Classical? | Notes |
|-----------|---------|------------|-------|
| **Sign Nature** | Exalted=100, Moolatrikona=80, Own=75, Friend=60, Neutral=50, Enemy=30, Debilitated=0 | CUSTOM | Moolatrikona not actually calculated; uses simplified friend/enemy logic |
| **House Type** | Kendra +20, Trikona +15, Dusthana -15 | CUSTOM | Arbitrary bonuses/penalties |
| **Dig Bala** | +30 if in Dig Bala house | CUSTOM | Binary |
| **Retrograde** | +20 | CUSTOM | Binary |
| **D9 (Navamsa)** | Vargottama +40; Debilitated→Exalted/Own in D9 +50 (Neecha Bhanga shortcut); Exalted→Debilitated -40; Exalted in D9 +20; Debilitated in D9 -20 | CUSTOM / TRADITION_DEPENDENT | **CRITICAL**: Implements "Neecha Bhanga" as automatic +50 bonus — violates Phase 4 Step 23 |
| **Normalization** | `min(score, 120) / 1.2` clamped to 0-100 | CUSTOM | Arbitrary scaling |

**Consumers**:
- `backend/routes/astro.py` line 45, 125 (`planet_strengths` in API response)

**Classification**: **CUSTOM** — This is explicitly a custom composite score, not classical Shadbala

---

### 1.3 `backend/tables.py` — Supporting Tables

**Used by**: `strength_evaluator.py`

| Table | Content | Classical? |
|-------|---------|------------|
| `SIGN_LORDS` | Sign → Planet ruler mapping | CLASSICAL |
| `FRIENDLY_SIGNS` | Planet → list of friendly signs | TRADITION_DEPENDENT (varies by tradition) |
| `EXALTED` / `DEBILITATED` (in strength_evaluator.py) | Hardcoded exaltation/debilitation signs | CLASSICAL (signs) / APPROXIMATION (no degrees) |

---

## 2. Duplicate Implementations

| Concept | Locations |
|---------|-----------|
| Sign index lookup | `shadbala.py:get_sign_index()`, `strength_evaluator.py` (inline), `tables.py` (not directly), `calculations.py` (multiple), `doshas_advanced.py`, `maitri.py`, `ashtakavarga.py`, `shadbala.py` |
| Exaltation check | `shadbala.py` (EXALTATION_DEGREES), `strength_evaluator.py` (hardcoded EXALTED dict), `calculations.py` (`is_exalted`), `yoga_evaluator.py` (`is_planet_exalted`) |
| Debilitation check | `shadbala.py` (implied via distance), `strength_evaluator.py` (hardcoded DEBILITATED dict), `calculations.py` (`is_debilitated`), `yoga_evaluator.py` (`is_planet_debilitated`) |
| Dig Bala houses | `shadbala.py` (DIG_BALA_HOUSES), `strength_evaluator.py` (DIGBALA_HOUSES) |
| Naisargika Bala | `shadbala.py` (NAISARGIKA_BALA), not in strength_evaluator |

---

## 3. Missing Classical Components (Per Phase 4 Requirements)

| Component | Status | Required by Phase 4 |
|-----------|--------|---------------------|
| **Sthana Bala subcomponents** | | |
| - Uchcha Bala | Approximate (distance-based only) | ✅ STEP 5 |
| - Saptavargaja Bala | **MISSING** | ✅ STEP 6 |
| - Ojhayugma Bala | **MISSING** | ✅ STEP 7 |
| - Kendradi Bala | **MISSING** | ✅ STEP 8 |
| - Drekkana Bala | **MISSING** | ✅ STEP 9 |
| **Dig Bala** | Binary house-based | ✅ STEP 10 (continuous angular) |
| **Kala Bala subcomponents** | | |
| - Nathonnatha Bala | **MISSING** | ✅ STEP 11 |
| - Paksha Bala | **MISSING** | ✅ STEP 11 |
| - Tribhaga Bala | **MISSING** | ✅ STEP 11 |
| - Varsha/Masa/Dina/Hora Bala | **MISSING** | ✅ STEP 11 |
| - Ayana Bala | **MISSING** | ✅ STEP 11 |
| - Yuddha Bala | **MISSING** | ✅ STEP 11 |
| **Chesta Bala** | Binary retrograde/direct | ✅ STEP 12 (speed-based) |
| **Naisargika Bala** | Present (classical values) | ✅ STEP 13 |
| **Drig Bala** | Constant 30 (placeholder) | ✅ STEP 14 (aspect-based) |
| **Bhava Bala** | **MISSING** | ✅ STEP 17 |
| **Vimsopaka Bala** | **MISSING** | ✅ STEP 18 |
| **Avastha** | **MISSING** | ✅ STEP 19 |
| **Dignity Evaluator** | Simplified in strength_evaluator | ✅ STEP 20 |
| **Functional Strength** | Partial in strength_evaluator (house-based) | ✅ STEP 21 |
| **Neecha Bhanga shortcut** | **PRESENT** in strength_evaluator (+50 bonus) | ❌ STEP 23 (must remove) |

---

## 4. AI / Frontend Consumers

### AI Engine (`backend/ai_engine.py`)
- Line 76: `"strengths": ["Trait 1", "Trait 2", "Trait 3"]` — placeholder
- Line 92: References "Ascendant lord strength" in summary

### Frontend (via API `/astro/compute`)
- `strengths` array (from `strength_evaluator.calculate_chart_strengths`)
- `shadbala` object (from `shadbala.compute_shadbala`)

### Yoga Rulesets
- Multiple rulesets reference `"strength": "strong"` as condition
- `neechabhanga.json` exists but logic is in strength_evaluator

---

## 5. Test Files

| File | Tests | Status |
|------|-------|--------|
| `backend/verify_shadbala.py` | Manual verification script | Runs, outputs current simplified values |

**No automated regression tests for strength calculations exist.**

---

## 6. Summary: What Must Change

| Current | Phase 4 Requirement |
|---------|---------------------|
| Single `compute_shadbala()` with 6 simplified components | Separate modules for each Bala component with classical formulas |
| Constant Drig Bala = 30 | Actual aspect-based Drig Bala calculation |
| Binary Kaala Bala (day/night) | Full Kala Bala with all subcomponents |
| Binary Chesta Bala (retro/direct) | Speed-based Chesta Bala |
| No Saptavargaja, Ojhayugma, Kendradi, Drekkana | Implement all Sthana Bala subcomponents |
| Neecha Bhanga automatic +50 bonus | Remove; record D9 dignity separately |
| Custom 0-100 score labeled as "strength" | Rename to `ASTROLIFE_COMPOSITE_STRENGTH` with `CLASSIFICATION: CUSTOM` |
| No Bhava Bala | Implement separate Bhava Bala |
| No Vimsopaka Bala | Implement separate Vimsopaka Bala |
| No Avastha | Implement Avastha |
| No canonical dignity object | Implement structured dignity evaluator |
| Duplicate sign/exaltation logic | Consolidate to canonical layer |

---

## 7. Canonical Inputs Available (Phase 1/2/3)

The new strength engine MUST consume (not recalculate):

- `ChartFacts` from `core.calculation.pipeline.generate_chart_facts()`
  - Planets: tropical/sidereal longitude, latitude, distance, speed, retrograde, sign, house, nakshatra
  - Ascendant: longitude, sign, nakshatra
  - Houses: Whole Sign mapping
  - Time: JD, UTC, timezone
  - Ayanamsha: value, system
  - Location: lat, lon
- Validated Vargas from Phase 2 (`core.calculation.varga`)
- Panchanga data from Phase 3 (`core.calculation.panchanga`)
- Transit data from Phase 3 if needed for dynamic strength

---

*End of Audit — Proceed to Phase 4 Implementation*