# Astrolife V2 - Phase 0: Duplicate Calculations

This document details all duplicate sources of truth and redundant calculations found across the repository.

## 1. Sign Index Calculation
- **Concept**: Finding the integer index (1-12 or 0-11) of a Zodiac sign string.
- **Duplicate Locations**:
  - `backend/shadbala.py` (`def get_sign_index(sign: str) -> int:`)
  - `backend/maitri.py` (`def get_sign_index(sign: str) -> int:`)
  - `backend/doshas_advanced.py` (`def get_sign_index(sign: str) -> int:`)
  - `backend/ashtakavarga.py` (`def get_sign_index(sign: str) -> int:`)
- **Impact**: Code repetition, risk of out-of-sync logic if the underlying array of signs changes.

## 2. Exaltation Check
- **Concept**: Checking if a planet is exalted in a given sign.
- **Duplicate Locations**:
  - `backend/calculations.py` (`def is_exalted(planet_name: str, sign: str) -> bool:`)
  - `backend/yoga_evaluator.py` (`def is_planet_exalted(planet: str, sign: str) -> bool:`)
- **Impact**: Logic is split between core calculation engine and the rule engine.

## 3. Debilitation Check
- **Concept**: Checking if a planet is debilitated in a given sign.
- **Duplicate Locations**:
  - `backend/calculations.py` (`def is_debilitated(planet_name: str, sign: str) -> bool:`)
  - `backend/yoga_evaluator.py` (`def is_planet_debilitated(planet: str, sign: str) -> bool:`)
- **Impact**: Same as exaltation, split logic.

## 4. Sunrise / Sunset Calculation
- **Concept**: Calculating Sunrise and Sunset times.
- **Duplicate Locations**:
  - `backend/calculations.py` (`def compute_sunrise_sunset(jd_ut: float, lat: float, lon: float, tz_name: str) -> Dict:`)
  - `backend/calculations.py` (`def compute_sunrise_sunset_internal(jd_start: float, lat: float, lon: float) -> Dict:`)
- **Impact**: Internal vs external wrapper logic is redundant.

## 5. Date parsing (Frontend vs Backend)
- **Concept**: Parsing dates and times for current time.
- **Duplicate Locations**:
  - `frontend/src/pages/DashaPage.jsx` (`new Date(isoString)`)
  - `backend/auth.py` (`datetime.utcnow()`)
  - Various other frontend modules recalculating time differences natively.
- **Impact**: Timezone inconsistencies across the stack.

## Summary
The highest priority duplicates for Phase 1 are the fundamental structural references: `get_sign_index`, `is_exalted`, and `is_debilitated`. These need a single source of truth in the Canonical Calculation Layer.
