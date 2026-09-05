# ASTROLIFE V2 — PHASE 5C: DOSHA ENGINE SPECIFICATION

## Overview

Phase 5C implements a deterministic, evidence-backed, tradition-aware dosha engine
that distinguishes formation, severity, cancellation, mitigation, and activation as
independent concepts.

## Architecture

### Package Location
`backend/core/rules/doshas/`

### Files Created

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports |
| `enums.py` | Dosha-specific enums (DoshaCategory, DoshaSeverity, etc.) |
| `models.py` | DoshaResult, DoshaEvaluationSet, DoshaProvenance, DoshaEvidence |
| `manglik.py` | Manglik/Kuja Dosha (3 methods: Lagna, Moon, Venus) |
| `kemadruma.py` | Kemadruma Dosha (classical Parashari) |
| `kala_sarpa.py` | Kala Sarpa Dosha (tradition-dependent, sign-based) |
| `pitru.py` | Pitru Dosha (modern common definition) |
| `afflictions.py` | Generic affliction engine (malefic conjunction/aspect, combustion, etc.) |
| `catalog.py` | Aggregation, evaluator creation, manifest generation |
| `golden_dosha_snapshot.json` | Golden chart dosha evaluation snapshot |

### Files Created (Tests)

| File | Tests |
|------|-------|
| `test_doshas_phase5c.py` | 157 tests across all doshas |

### Files Created (Documentation)

| File | Purpose |
|------|---------|
| `ASTROLIFE_V2_PHASE5C_SOURCE_AUDIT.md` | Source audit for all candidate doshas |
| `ASTROLIFE_V2_PHASE5C_DOSHA_SPECIFICATION.md` | This document |
| `ASTROLIFE_V2_PHASE5C_DOSHA_CATALOGUE.md` | Human-readable dosha catalogue |
| `ASTROLIFE_V2_PHASE5C_TEST_REPORT.md` | Test results report |

### Files Modified
None. All new files.

## Dosha Result Model

### DoshaResult Fields
- `dosha_id` — unique identifier
- `dosha_name` — human-readable name
- `category` — DoshaCategory enum
- `tradition` — DoshaTradition enum
- `method` — specific method identifier
- `formation_status` — DoshaFormationStatus (NOT_FORMED / FORMED / PARTIAL / UNCERTAIN)
- `severity_status` — DoshaSeverity (NONE / LOW / MODERATE / HIGH / UNKNOWN)
- `cancellation_status` — DoshaCancellationStatus (NONE / PARTIAL / FULL)
- `mitigation_status` — DoshaMitigationStatus (NONE / PARTIAL / SIGNIFICANT)
- `activation_status` — DoshaActivationStatus (NOT_EVALUATED / INACTIVE / ACTIVE)
- `confidence` — DoshaConfidence enum
- `evidence` — List[DoshaEvidence]
- `relevant_planets` — List[str]
- `relevant_houses` — List[int]
- `provenance` — DoshaProvenance
- `notes` — str

### Independence Principle
All five statuses are INDEPENDENT:
- Formation = FORMED does NOT imply Severity = HIGH
- Cancellation = FULL does NOT erase formation evidence
- Mitigation = PARTIAL is separate from cancellation
- Activation = NOT_EVALUATED is by design (no prediction engine)

## Implemented Doshas

### 1. Manglik / Kuja Dosha

**Rule IDs:**
- `DOSHA.MANGLIK.LAGNA_CLASSICAL`
- `DOSHA.MANGLIK.MOON_REFERENCE`
- `DOSHA.MANGLIK.VENUS_REFERENCE`

**Tradition:** PARASHARI_CLASSICAL (attributed to BPHS, exact verse unverified)
**Confidence:** HIGH

**Formation:** Mars in houses {1, 2, 4, 7, 8, 12} from reference point (whole-sign).

**Methods:**
- Lagna: reference = 1st house (Ascendant)
- Moon: reference = Moon's house
- Venus: reference = Venus's house

**Cancellation:**
- Jupiter conjunct Mars (full cancellation)
- Jupiter aspects Mars via Parashari (full cancellation)
- Mars in own sign (partial — disputed)

**Mitigation:**
- Mars exalted
- Strong Lagna lord
- Benefic in 7th house

**Severity:**
- Based on Mars dignity (exalted=LOW, own=LOW, debilitated=HIGH)
- House position modifier (8th house = higher severity)

### 2. Kemadruma Dosha

**Rule ID:** `DOSHA.KEMADRUMA.CLASSICAL`
**Tradition:** PARASHARI_CLASSICAL (attributed to BPHS, exact verse unverified)
**Confidence:** HIGH

**Formation (strict classical — ALL conditions must be true):**
1. No planet in 2nd house from Moon
2. No planet in 12th house from Moon
3. No planet in any kendra (1, 4, 7, 10) from Moon (excluding Moon)

**Cancellation:**
- Jupiter aspects Moon (full cancellation)

**Mitigation:**
- Moon exalted or in own sign
- Venus conjunct Moon

**Severity:**
- Moon dignity: exalted/own = LOW, debilitated = HIGH, else MODERATE

### 3. Kala Sarpa Dosha

**Rule ID:** `DOSHA.KALA_SARPA.SIGN_BASED`
**Tradition:** TRADITION_DEPENDENT
**Confidence:** TRADITION_DEPENDENT

**Formation:** All 7 classical planets (Sun-Saturn) hemmed between Rahu and Ketu
on one side of the nodal axis (sign-based containment).

**Boundary handling:** Planets on Rahu/Ketu sign = boundary (UNCERTAIN in strict methods).

**Cancellation:**
- Jupiter in Ascendant (full)
- Jupiter aspects Rahu (full)

**Mitigation:**
- Strong Lagna lord

**Severity:** UNKNOWN (no validated classical scale)

### 4. Pitru Dosha

**Rule ID:** `DOSHA.PITRU.MODERN_COMMON`
**Tradition:** TRADITION_DEPENDENT
**Confidence:** TRADITION_DEPENDENT

**Formation (ANY condition triggers):**
1. Sun conjunct Rahu
2. Sun conjunct Ketu
3. Moon conjunct Rahu
4. Moon conjunct Ketu
5. Rahu in 9th house from Lagna
6. Ketu in 9th house from Lagna

**Cancellation:** None (partial Jupiter protection recorded as mitigation only)

**Mitigation:**
- Jupiter in Ascendant

**Severity:** Based on count of conditions met (1=LOW, 2=MODERATE, 3+=HIGH)

### 5. Generic Affliction Engine

Not a named dosha. Reusable functions for:
- Malefic conjunction
- Malefic aspect (Parashari)
- Combustion
- Debilitation
- Dusthana affliction
- Node conjunction

Key principle: "Saturn aspects Moon" does NOT automatically mean "Dosha X exists."

## Evaluator Configuration

```
evaluate_formation = True (custom evaluators)
evaluate_strength = False (severity evaluated separately)
evaluate_activation = False (NOT_EVALUATED by design)
evaluate_cancellation = True (custom evaluators)
evaluate_mitigation = True (custom evaluators)
collect_evidence = True
collect_trace = False
```

## Golden Chart Results

For MEDAPATI BHASKARA VENKATA RAJEEV REDDY (17/08/2005, 00:02 IST):

| Dosha | Formation | Severity | Cancellation | Mitigation |
|-------|-----------|----------|--------------|------------|
| Manglik (Lagna) | FORMED | LOW | NONE | PARTIAL |
| Manglik (Moon) | NOT_FORMED | NONE | NONE | NONE |
| Manglik (Venus) | FORMED | LOW | NONE | PARTIAL |
| Kemadruma | NOT_FORMED | NONE | NONE | NONE |
| Kala Sarpa | NOT_FORMED | NONE | NONE | NONE |
| Pitru | NOT_FORMED | NONE | NONE | NONE |

## Design Constraints

1. No AI in formation evaluation
2. No deterministic predictions
3. No fear-based language
4. No arbitrary numerical scoring
5. Every result carries evidence and provenance
6. Formation evidence is never overwritten
7. Parashari aspects used (not Western degree aspects)
8. Phase 4 functional lordship consumed (not recreated)
9. Swiss Ephemeris NOT called (uses pre-computed ChartFacts)
