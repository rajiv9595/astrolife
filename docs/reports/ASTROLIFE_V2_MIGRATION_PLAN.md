# Astrolife V2 - Phase 0: Migration Plan

This plan details the phased migration strategy for upgrading Astrolife to V2.

## PHASE 1: Canonical Calculation / Truth Layer
- **Files Affected**: `backend/calculations.py`, `backend/ashtakavarga.py`, `backend/doshas_advanced.py`, `backend/shadbala.py`, `backend/yoga_evaluator.py`, `backend/maitri.py`
- **Goal**: Consolidate core utilities (sign indexing, exaltation/debilitation arrays) to establish a single source of truth for the entire engine.
- **Dependencies**: `pyswisseph`
- **Risks**: High risk. Refactoring the core engine affects every single feature downstream.
- **Tests Required**: Strict adherence to Golden Chart baseline and all existing verification scripts (`verify_final_modules.py`, etc.).

## PHASE 2: Verified D1 + Vargas
- **Files Affected**: `backend/calculations.py`, `backend/compare_vargas.py`
- **Goal**: Harden the Divisional Charts (D2-D60) algorithms, formalizing the tradition dependencies and locking in the math.
- **Dependencies**: Phase 1
- **Risks**: Moderate. Some Varga calculations are historically contested.
- **Tests Required**: `verify_upgrades.py` with expanded dataset for extreme edge cases.

## PHASE 3: Panchanga + Dasha + Transit
- **Files Affected**: `backend/panchanga_advanced.py`, `backend/calculations.py` (Vimshottari logic)
- **Goal**: Ensure accurate timelines, isolate system time dependencies from core logic, and strictly separate static birth state from dynamic state.
- **Dependencies**: Phase 1, Phase 2
- **Risks**: Moderate. Timezone and daylight saving offsets historically cause drift in Dasha transition dates.
- **Tests Required**: Timezone boundary testing and manual Dasha regression testing.

## PHASE 4: Strength Engine
- **Files Affected**: `backend/shadbala.py`, `backend/strength_evaluator.py`
- **Goal**: Solidify and modularize the 6-fold Shadbala planetary strength calculator.
- **Dependencies**: Phase 1
- **Risks**: Low to Moderate. Complex math, but well-defined structurally.
- **Tests Required**: `verify_shadbala.py`

## PHASE 5: Yoga / Dosha / Jaimini
- **Files Affected**: `backend/yoga_evaluator.py`, `backend/doshas_advanced.py`, `backend/jaimini.py`, `backend/verify_jaimini_ashtakavarga.py`
- **Goal**: Consolidate heuristic interpretation rules into clean logic patterns using the Canonical Truth Layer.
- **Dependencies**: Phase 1, Phase 4
- **Risks**: Moderate. Potential disruption to AI rule logic if schema changes.
- **Tests Required**: Specific Yoga activation tests based on test profiles.

## PHASE 6: Evidence + Dynamic Rule Engine
- **Files Affected**: `backend/rulesets/`, `backend/ai_engine.py`
- **Goal**: Build a dynamic rule processor allowing JSON-based configuration of astrological heuristics and AI evidence ingestion.
- **Dependencies**: Phase 5
- **Risks**: High. Requires precise syntax matching and error handling for dynamic rules.
- **Tests Required**: Rule engine unit tests validating correct parsing and application.

## PHASE 7: Specialized AI Agents
- **Files Affected**: `backend/ai_engine.py`
- **Goal**: Upgrade Gemini AI usage to specialized agents (e.g., Transit Analyzer, Career Oracle).
- **Dependencies**: Phase 6
- **Risks**: High. AI token limits, hallucination of aspects, prompt drifting.
- **Tests Required**: LLM evaluation testing.

## PHASE 8: Timing / Event Prediction
- **Files Affected**: New prediction engine modules.
- **Goal**: Combine Dasha, Transit, and Ashtakavarga data to trigger highly specific event probability windows.
- **Dependencies**: Phase 3, Phase 7
- **Risks**: High. Compounding complexity in timeline intersection algorithms.
- **Tests Required**: Historical event backtracking and verification.

## PHASE 9: Developer Rule Lab
- **Files Affected**: `frontend/src/components/DeveloperAPI.jsx`, Backend routes
- **Goal**: Provide API interfaces for developers to create and test their own rules.
- **Dependencies**: Phase 6, Phase 8
- **Risks**: Low. Mostly infrastructure and security controls.
- **Tests Required**: API auth and rate limiting.

## PHASE 10: Golden Tests / Regression
- **Files Affected**: Global Test Suite
- **Goal**: Cement the V2 architecture with a full end-to-end testing harness that guarantees 100% mathematical regression matching.
- **Dependencies**: Phases 1-9
- **Risks**: Low. Only bolsters stability.
- **Tests Required**: Integration test suite.

## PHASE 11: Frontend Integration
- **Files Affected**: `frontend/src/`
- **Goal**: Wire up new V2 endpoints to the React UI without altering the aesthetic or current user flow.
- **Dependencies**: Phases 1-10
- **Risks**: Moderate. API contract alignment issues.
- **Tests Required**: E2E browser testing.

## PHASE 12: Production Optimization
- **Files Affected**: Deployment configs, DB models, caching layer
- **Goal**: Add caching, DB indexing, and scale the application for production launch.
- **Dependencies**: Phase 11
- **Risks**: Moderate. Cache invalidation on time-based calculations.
- **Tests Required**: Load testing.
