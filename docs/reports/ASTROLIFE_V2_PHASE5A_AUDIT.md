# ASTROLIFE V2 — PHASE 5A — REPOSITORY AUDIT

## Executive Summary

This audit documents the existing Astrolife repository state prior to Phase 5A (Deterministic Astrology Rule Engine Foundation). The repository has completed Phases 1-4B with 102,339 passing tests and zero failures.

---

## 1. Existing Rule/Yoga Architecture

### 1.1 Yoga Evaluator (`backend/yoga_evaluator.py`)

**Current Implementation:**
- JSON-based ruleset system in `backend/rulesets/yogas/`
- 70+ yoga JSON files with conditions evaluated against D1 chart
- Two evaluation paths:
  - **Signal-based** (legacy): Weighted predicates with `strong_if`/`active_if` boolean expressions
  - **Condition-based** (new): Structured conditions with named patterns
- Uses `eval()` for boolean condition strings (security risk)
- Evaluates against legacy `chart_data` dict format, NOT canonical `ChartFacts`

**Key Components:**
- `evaluate_predicate()` - 15+ predicate types (kendra_from, planet_in_signs, planet_debilitated, etc.)
- `evaluate_named_pattern()` - 30+ hardcoded named patterns (hari_pattern, shiva_pattern, etc.)
- `evaluate_condition()` - Uses `eval()` on string expressions
- `evaluate_yoga()` - Main entry point
- `evaluate_all_yogas()` - Directory scanner

**Tradition Handling:**
- No explicit tradition metadata in rules
- Mixes Parashari classical with custom patterns
- No versioning or provenance tracking

### 1.2 Dosha Engine (`backend/doshas_advanced.py`)

**Current Implementation:**
- Two hardcoded doshas: Kala Sarpa, Pitru Dosha
- Direct implementation in Python functions
- No rule engine abstraction
- No cancellation/mitigation architecture

### 1.3 Jaimini System (`backend/jaimini.py`)

**Current Implementation:**
- Chara Karaka calculation
- Rashi Drishti (sign aspects)
- Separate from yoga engine

### 1.4 AI Interpretation (`backend/ai_engine.py`, `backend/knowledge_base.py`)

**Current Implementation:**
- Google Gemini integration for narrative generation
- Knowledge base with ~5 concept definitions
- AI determines yoga significance (violates Phase 5A requirement)
- `generate_expert_report()` returns structured JSON with yoga references

---

## 2. Duplicate Implementations

| Functionality | Location 1 | Location 2 | Location 3 |
|---------------|------------|------------|------------|
| Sign Lords | `tables.py` | `yoga_evaluator.py` (local `SIGN_LORDS`) | `core/strength/functional.py` (imports from tables) |
| Exaltation/Debilitation | `yoga_evaluator.py` | `core/strength/profile.py` (`EXALTATION_DATA`) | `core/strength/dignity.py` |
| House from Sign | `yoga_evaluator.py` (`get_house_from_sign`) | `core/calculation/houses.py` | - |
| Planet Longitude Access | `yoga_evaluator.py` (`get_planet_longitude`) | `core/calculation/pipeline.py` (ChartFacts) | - |
| Kendra/Trikona/Dusthana | `yoga_evaluator.py` (constants) | `core/strength/functional.py` (constants) | - |
| Yogakaraka Logic | `yoga_evaluator.py` (`any_yogakaraka`) | `core/strength/functional.py` (`is_yogakaraka`) | `rulesets/strength_rules/yogakaraka_basic.json` |
| Conjunction Check | `yoga_evaluator.py` (`conjunction` predicate) | `core/strength/drig_bala.py` (aspect logic) | - |
| Aspect Definitions | `core/calculation/config.py` (`ParashariAspectConfig`) | `core/strength/drig_bala.py` (`ASPECT_DEFINITIONS`) | `yoga_evaluator.py` (7th house only in `any_connection`) |

---

## 3. Reusable Utilities (Canonical Layer)

### 3.1 Calculation Layer (Phase 1) - **DO NOT MODIFY**
- `core/calculation/pipeline.py` → `generate_chart_facts()` → `ChartFacts`
- `core/calculation/ephemeris.py` — Swiss Ephemeris wrapper
- `core/calculation/houses.py` — Whole Sign houses
- `core/calculation/varga.py` — D1-D60 Varga engine (Phase 2)
- `core/calculation/dynamic.py` — `DynamicAstrologyState` (Phase 3)

### 3.2 Strength Layer (Phase 4) - **DO NOT MODIFY**
- `core/strength/pipeline.py` → `generate_strength_report()` → `StrengthReport`
- `core/strength/shadbala.py` — 6 Balas
- `core/strength/dignity.py` — Planetary dignity
- `core/strength/functional.py` — Functional strength + Yogakaraka
- `core/strength/profile.py` — Configuration + reference data

### 3.3 Data Models - **DO NOT MODIFY**
- `core/calculation/models.py` — `ChartFacts`, `PlanetData`, `HouseData`, etc.
- `core/strength/models.py` — `StrengthReport`, `DignityResult`, `FunctionalStrengthResult`, etc.

---

## 4. Legacy Dependencies

### 4.1 Legacy Compute Module (`backend/calculations.py`)
- `compute_chart()` — Returns dict format used by:
  - `routes/astro.py` `/compute` endpoint
  - `yoga_evaluator.py` (expects dict format)
  - All existing tests

### 4.2 Legacy Strength Evaluator (`backend/strength_evaluator.py`)
- `calculate_chart_strengths()` — Used by `/compute` endpoint

### 4.3 Legacy Shadbala (`backend/shadbala.py`)
- `compute_shadbala()` — Used by `/compute` endpoint

### 4.4 Routes (`backend/routes/astro.py`)
- `/compute` endpoint aggregates everything
- Calls `evaluate_all_yogas()` with legacy dict format
- Must continue working unchanged

---

## 5. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| `eval()` in `evaluate_condition()` | HIGH | Replace with safe AST parser or condition objects |
| Dual data formats (dict vs ChartFacts) | HIGH | Create adapter `ChartFacts → LegacyDict` for yoga evaluator |
| No tradition separation in rules | HIGH | Add `tradition` field to rule metadata |
| No versioning/provenance | MEDIUM | Add to new rule metadata model |
| No cancellation/mitigation architecture | MEDIUM | Design separate evaluators in new engine |
| AI determines yoga existence | HIGH | Rule engine must be deterministic; AI only explains |
| 70+ JSON rulesets need migration | MEDIUM | Adapter pattern; don't rewrite all at once |

---

## 6. Migration Plan

### Phase 5A (This Phase) — Foundation Only
1. **Create** `backend/core/rules/` package with new architecture
2. **Implement** `RuleContext` consuming `ChartFacts` + `StrengthReport` + `DynamicAstrologyState`
3. **Implement** `RuleDefinition`, `RuleResult`, `Condition`, `Evidence` models
4. **Implement** `RuleRegistry` with versioning, tradition separation
5. **Implement** Composable condition system (no `eval()`)
6. **Implement** Evidence system with structured facts
6. **Create** 1-2 demonstration rules (simple structural rules)
7. **Create** Golden chart + synthetic tests
8. **Verify** zero regressions in Phases 1-4B

### Post-5A (Future Phases)
- **Phase 5B**: Migrate existing 70+ yoga JSON rules to new format
- **Phase 5C**: Implement Dosha catalogue in new engine
- **Phase 5D**: Jaimini rules in new engine
- **Phase 5E**: Activation/timing rules (Dasha/Transit integration)
- **Phase 5F**: Developer Rule Lab (declarative format)

---

## 7. Files That Should NOT Be Modified

### Core Calculation (Phase 1-2)
- `core/calculation/pipeline.py`
- `core/calculation/models.py`
- `core/calculation/ephemeris.py`
- `core/calculation/houses.py`
- `core/calculation/varga.py`
- `core/calculation/config.py`
- `core/calculation/dynamic.py`

### Core Strength (Phase 3-4)
- `core/strength/pipeline.py`
- `core/strength/models.py`
- `core/strength/profile.py`
- `core/strength/shadbala.py`
- `core/strength/bhava_bala.py`
- `core/strength/vimsopaka.py`
- `core/strength/avastha.py`
- `core/strength/dignity.py`
- `core/strength/functional.py`
- `core/strength/composite.py`
- All sub-modules in `core/strength/`

### Tests (Must Continue Passing)
- `test_golden_chart_canonical.py` (39 tests)
- `test_varga_phase2.py` (19,692 tests)
- `test_panchanga_phase3.py`, `test_dasha_phase3.py`, `test_dynamic_phase3.py`, `test_transit_phase3.py` (82,521 tests)
- `test_strength_phase4b.py` (87 tests)
- All golden chart verification scripts

### Legacy Compatibility (Must Continue Working)
- `backend/calculations.py` — `compute_chart()`
- `backend/strength_evaluator.py` — `calculate_chart_strengths()`
- `backend/shadbala.py` — `compute_shadbala()`
- `backend/routes/astro.py` — `/compute` endpoint
- `backend/yoga_evaluator.py` — Keep for legacy compatibility during transition
- `backend/doshas_advanced.py` — Keep for legacy compatibility

---

## 8. Files That Require Migration (Post-5A)

### High Priority
- `backend/yoga_evaluator.py` → Replace with adapter to new engine
- `backend/rulesets/yogas/*.json` (70+ files) → Convert to new rule format
- `backend/doshas_advanced.py` → Rewrite as rules in new engine

### Medium Priority
- `backend/routes/astro.py` — Update to use new engine (optional, can use adapter)
- `backend/ai_engine.py` — Remove yoga determination logic; use rule engine results

---

## 9. Compatibility Constraints

| Constraint | Requirement |
|------------|-------------|
| `/astro/compute` response format | Must remain identical |
| `ChartFacts` model | Immutable — rule engine consumes only |
| `StrengthReport` model | Immutable — rule engine consumes only |
| `DynamicAstrologyState` model | Immutable — rule engine consumes only |
| Existing test counts | 102,339 tests must continue passing |
| Golden chart values | Must not change |
| Legacy dict format | Must be supported via adapter during transition |

---

## 10. Architecture Decision Summary

### What the New Rule Engine Must Provide
1. **Deterministic evaluation** — Same inputs → same outputs, no `datetime.now()`, no randomness
2. **Tradition separation** — Every rule declares `tradition: PARASHARI_CLASSICAL | JAIMINI | TRADITION_DEPENDENT | CUSTOM`
3. **Formation ≠ Strength ≠ Activation** — Independent status enums
4. **Cancellation/Mitigation as separate evaluators** — Not embedded in rule logic
5. **Structured Evidence** — Every rule result includes exact facts that triggered it
6. **Provenance** — Source reference, implementation version, confidence level
7. **Versioning** — Rule ID + version; historical behavior preserved
8. **No arbitrary code execution** — Declarative conditions only
9. **Canonical layer consumption** — Never recalculates astronomy/strength

### What Phase 5A Does NOT Include
- Full yoga catalogue migration (70+ rules)
- Dosha catalogue
- Jaimini rule migration
- AI explanation layer
- Timing/activation engine
- Developer Rule Lab

---

## 11. Recommended Package Structure

```
backend/core/rules/
    __init__.py
    models.py          # RuleDefinition, RuleResult, Evidence, enums
    enums.py           # Category, Tradition, Status enums
    context.py         # RuleContext (consumes ChartFacts, StrengthReport, DynamicAstrologyState)
    registry.py        # RuleRegistry
    evaluator.py       # RuleEvaluator (deterministic evaluation)
    conditions.py      # Composable condition classes (AND, OR, NOT, primitives)
    evidence.py        # Evidence builder
    activation.py      # Activation evaluator (future: Dasha/Transit)
    cancellation.py    # Cancellation evaluator
    mitigation.py      # Mitigation evaluator
    provenance.py      # Provenance tracking
    validators.py      # Metadata validation
```

---

## 12. Golden Chart Test Data (Reference)

**Profile:** MEDAPATI BHASKARA VENKATA RAJEEV REDDY
- **DOB:** 17/08/2005
- **TOB:** 12:02 AM IST
- **Location:** Anaparthy, Andhra Pradesh, India (16.93407, 81.95522)
- **Profile:** SIDEREAL, LAHIRI_STANDARD, MEAN_NODE, WHOLE_SIGN
- **Ascendant:** Taurus (39.955°)
- **Moon:** Sagittarius (257.863°) — Purvashada Nakshatra, Pada 2

---

*End of Audit Document*