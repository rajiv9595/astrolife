# ASTROLIFE V2 — PHASE 5G: JAIMINI DASHA AUDIT

**Date:** 2026-09-04
**Scope:** Pre-implementation audit for Phase 5G (Dasha calculation foundation only)
**Status:** Audit Complete — Ready for Implementation
**Prior phases:** 5D/5D-H/5E/5F COMPLETE and accepted (no redesign).

---

## 1. Existing Dasha Infrastructure

* Phase 3 Vimshottari (`core/calculation/dasha.py`, accepted): JD-based
  `DashaPeriod`/`DashaTimeline`, nakshatra balance, 5 sublevels, explicit
  `DashaCalculationProfile.days_per_year` (default 365.2425). Untouched by 5G;
  no sequence/balance reuse (different system).
* No Jaimini Dasha code exists anywhere (only Chara-Karaka naming and Chara
  karanas — unrelated). Clean slate, no legacy behavior to match.
* Routes consume Vimshottari timelines (`routes/ai_routes.py`); 5G adds no
  routes, no frontend.

## 2. Reusable Generic Infrastructure

Pydantic timestamp-free modeling discipline (5E/5F), 5F evidence tiers
(extended with `DASHA_DERIVED`), UNVERIFIED provenance pattern, 5D sign/lord
tables (`SIGNS`, `CLASSICAL_SIGN_LORDS`), sign-type table (movable/fixed/dual).
Date handling: plain tz-aware `datetime + timedelta` (no swe dependency in the
Jaimini package; calendar conversion is explicit profile arithmetic).

## 3. Jaimini-Specific Requirements

Explicit `JaiminiDashaProfile` (system/tradition/method/start/sequence/
duration/exception/subperiod/direction/year-model/source/confidence);
starting-sign strategy; per-period duration evidence; full-cycle + antardasha
hierarchy; birth anchor (no Vimshottari-style balance); UNKNOWN on missing
inputs; UNSUPPORTED for unimplemented traditions.

## 4. Selected Profile (5G implements exactly one)

`dasha_system = JAIMINI_CHARA`, `method = CHARA_DASHA_LAGNA_START_V1`,
tradition JAIMINI, source_reference UNVERIFIED, confidence
TRADITION_DEPENDENT. Rules (profile conventions, see spec): start = Lagna
sign; sequence direction fixed from start-sign nature (movable→FORWARD,
fixed→REVERSE, dual odd-numbered→FORWARD, dual even→REVERSE); duration =
inclusive house-count from period sign to its single-classical lord in sequence
direction, with OWN_SIGN_TWELVE exception (lord in own sign → 12 years);
12 mahadashas covering all signs once; 12 equal antardashas per parent from
the parent sign in sequence direction; year = 365.25 days; birth anchor = full
first period (NO_BIRTH_BALANCE); boundary `[start, end)` half-open, UTC ISO.

## 5. Competing Traditions (isolated as UNSUPPORTED, never merged)

Paka-Lagna/AK-based starts, Sthira/Narayana/Brahma/Mandooka/Karaka dashas,
exaltation/debilitation duration adjustments, Savana (360-day) year,
alternative dual-direction rules. Requesting any method ID other than the
implemented one raises an explicit UNSUPPORTED error.

## 6. Unresolved Tradition Questions (documented, not hidden)

Exact verses unverified (hence UNVERIFIED); dual-direction and own-sign-12
rules are profile conventions with variant traditions acknowledged in the
provenance doc; antardasha equality is the profile's stated convention;
pratyantardasha deferred (only MAHA+ANTAR levels defined).

## 7. Implementation Scope / Files

New: `core/jaimini/dasha/` (`__init__`, `profile`, `models`, `sequence`,
`duration`, `calculator`, `evidence`, `validators`, `pipeline`),
`backend/test_jaimini_dasha_phase5g.py`,
`backend/golden_jaimini_dasha_snapshot.json`. Docs: audit, specification,
provenance, test report. Expected changes: none to accepted code.

## 8. Protected Files

Everything accepted: 5D/5E/5F Jaimini code, Phase 3 Vimshottari, calculation,
varga, rules, strength, legacy `backend/jaimini.py`, routes, frontend.
Upstream defect → STOP and report.
