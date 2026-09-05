# Astrolife V2 - Phase 0: Calculation Inventory

This document provides a baseline inventory of the astrology calculations present in the repository. It is a read-only snapshot prior to any V2 migration or refactoring.

## 1. Core Planetary Calculations
- **File**: `backend/calculations.py`
- **Function**: `compute_chart`, `calculate_planets`
- **Input**: `jd_ut` (Julian Day in UTC), `ay` (Ayanamsha), `topo_lon`
- **Output**: Dictionary of planets with `lon_tropical`, `lon_sidereal`, `speed_lon`, etc.
- **Formula**: Calls `swe.calc_ut`
- **Dependencies**: `pyswisseph`
- **Swiss Ephemeris**: Yes
- **Sidereal**: Yes
- **Ayanamsha**: Swiss Ephemeris Standard Lahiri (`swe.SIDM_LAHIRI`)
- **Node Type**: True / Mean Node (Mean Rahu is default)
- **House System**: Whole Sign
- **Deterministic**: Yes
- **Current Time Dependent**: No
- **Confidence**: VERIFIED

## 2. House Calculations
- **File**: `backend/calculations.py`
- **Function**: `calculate_houses`, `whole_sign_houses_from`
- **Input**: `jd_ut`, `lat`, `lon`, `ay`
- **Output**: Dictionary of houses (Ascendant, MC, ARMC, etc.)
- **Formula**: Calls `swe.houses_ex` and simple offset logic for Whole Sign
- **Dependencies**: `pyswisseph`
- **Swiss Ephemeris**: Yes
- **Sidereal**: Yes
- **Ayanamsha**: Lahiri
- **Deterministic**: Yes
- **Confidence**: VERIFIED

## 3. Nakshatra and Pada
- **File**: `backend/calculations.py`
- **Function**: `compute_nakshatra_pada`
- **Input**: `lon_sidereal`
- **Output**: Nakshatra index, name, pada, fraction, lord
- **Formula**: `lon_sidereal / (360 / 27)`
- **Dependencies**: None
- **Swiss Ephemeris**: No (Uses pre-calculated longitude)
- **Sidereal**: Yes
- **Deterministic**: Yes
- **Confidence**: VERIFIED

## 4. Divisional Charts (Vargas)
- **File**: `backend/calculations.py`
- **Function**: `build_chart_d9`, `build_chart_d10`, etc.
- **Input**: D1 planets, `asc_sidereal_deg`
- **Output**: D9/D10 chart dictionary
- **Formula**: Standard division formulas
- **Dependencies**: None
- **Swiss Ephemeris**: No
- **Sidereal**: Yes
- **Deterministic**: Yes
- **Confidence**: TRADITION DEPENDENT

## 5. Vimshottari Dasha
- **File**: `backend/calculations.py`
- **Function**: `compute_vimshottari_timeline`, `calculate_antar_dasha`, etc.
- **Input**: `jd_birth`, `moon_sidereal_lon`, `years_ahead`
- **Output**: Nested list of Mahadasha, Antardasha, Pratyantardasha, etc.
- **Formula**: Proportionate distribution of 120 years based on moon's nakshatra fraction
- **Dependencies**: None
- **Swiss Ephemeris**: No
- **Sidereal**: Yes
- **Deterministic**: Yes
- **Current Time Dependent**: Yes (`is_current` logic uses system time)
- **Confidence**: VERIFIED

## 6. Panchanga (Advanced)
- **File**: `backend/panchanga_advanced.py`, `backend/calculations.py`
- **Function**: `compute_advanced_panchanga`, `compute_tithi`, `compute_karana`, `compute_nithya_yoga`
- **Input**: Moon longitude, Sun longitude
- **Output**: Tithi, Karana, Yoga, Yoni, Gana, Nadi
- **Formula**: `moon_lon - sun_lon` and division
- **Dependencies**: None
- **Swiss Ephemeris**: No
- **Sidereal**: Yes
- **Deterministic**: Yes
- **Confidence**: NEEDS VALIDATION

## 7. Ashtakavarga
- **File**: `backend/ashtakavarga.py`
- **Function**: `compute_bav`, `compute_sav`, `compute_ashtakavarga`
- **Input**: Planets array, Ascendant sign
- **Output**: BAV (Bhinna Ashtakavarga) for each planet, SAV (Sarva Ashtakavarga)
- **Formula**: Traditional point distribution rules
- **Dependencies**: `get_sign_index`
- **Swiss Ephemeris**: No
- **Sidereal**: Yes
- **Deterministic**: Yes
- **Confidence**: VERIFIED

## 8. Shadbala
- **File**: `backend/shadbala.py`
- **Function**: `compute_shadbala`
- **Input**: Planets array, Ascendant sign, `is_day_birth`
- **Output**: Sthana Bala, Dig Bala, Kaala Bala, Chesta Bala, Naisargika Bala, Drig Bala
- **Formula**: Six sources of strength calculation
- **Dependencies**: None
- **Swiss Ephemeris**: No
- **Sidereal**: Yes
- **Deterministic**: Yes
- **Confidence**: NEEDS VALIDATION

## 9. Doshas (Advanced)
- **File**: `backend/doshas_advanced.py`, `backend/calculations.py`
- **Function**: `compute_advanced_doshas`, `calculate_mangal_dosha`
- **Input**: Planets array, Ascendant sign, Whole sign houses
- **Output**: Kala Sarpa, Pitru, Mangal doshas status and cancellation reasons
- **Formula**: Positional checks for Rahu-Ketu axis, Mars placement
- **Dependencies**: `get_sign_index`
- **Swiss Ephemeris**: No
- **Sidereal**: Yes
- **Deterministic**: Yes
- **Confidence**: CUSTOM HEURISTIC

## 10. Jaimini System
- **File**: `backend/jaimini.py`
- **Function**: `compute_jaimini_system`, `calculate_chara_karakas`, `calculate_arudha_padas`
- **Input**: Planets array, Ascendant sign
- **Output**: Chara Karakas, Arudha Padas
- **Formula**: Planet degree sorting, house counting
- **Dependencies**: None
- **Swiss Ephemeris**: No
- **Sidereal**: Yes
- **Deterministic**: Yes
- **Confidence**: VERIFIED

## 11. Yogas
- **File**: `backend/yoga_evaluator.py`
- **Function**: `evaluate_yogas`
- **Input**: Chart data, rule configs
- **Output**: List of active Yogas
- **Formula**: Dynamic JSON rule evaluation (Kendra, Trikona, conjunctions)
- **Dependencies**: `is_planet_exalted`, `is_planet_debilitated`
- **Swiss Ephemeris**: No
- **Sidereal**: Yes
- **Deterministic**: Yes
- **Confidence**: CUSTOM HEURISTIC

## 12. Maitri Chakra
- **File**: `backend/maitri.py`
- **Function**: `compute_maitri_chakra`
- **Input**: Planets array
- **Output**: Natural, Temporal, Compound relationships
- **Formula**: 3-sign distance for temporal, predefined tables for natural
- **Dependencies**: `get_sign_index`
- **Swiss Ephemeris**: No
- **Sidereal**: Yes
- **Deterministic**: Yes
- **Confidence**: VERIFIED
