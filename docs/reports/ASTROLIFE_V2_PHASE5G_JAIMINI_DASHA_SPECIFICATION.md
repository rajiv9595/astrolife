# ASTROLIFE V2 — PHASE 5G: JAIMINI DASHA SPECIFICATION

**Method:** `CHARA_DASHA_LAGNA_START_V1` (`dasha_system = JAIMINI_CHARA`)
**Version:** 1.0.0
**Status:** IMPLEMENTED & VALIDATED (period FACTS only; no timing claims)

---

## 1. Profile (`core/jaimini/dasha/profile.py`)

`JaiminiDashaProfile`: system/tradition/method, `start_sign_rule=LAGNA_START`,
`sign_progression_rule=NATURE_DIRECTION_FROM_START`,
`year_duration_rule=INCLUSIVE_LORD_DISTANCE_WITH_OWN_SIGN_TWELVE`,
`exception_rule=OWN_SIGN_TWELVE`,
`subperiod_rule=TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT`,
`direction_rule=MOVABLE_FORWARD_FIXED_REVERSE_DUAL_PARITY`,
`birth_balance_rule=NO_BIRTH_BALANCE`, `year_model=MEAN_JULIAN_YEAR`
(`days_per_year=365.25`), half-open `[start,end)` boundaries,
levels MAHA_DASHA+ANTARDASHA, UNVERIFIED / TRADITION_DEPENDENT.
`require_supported()` raises `UnsupportedDashaMethodError` for any other
method (8 known-but-unsupported traditions listed; never merged).

## 2. Algorithms

* **Start** (`calculator.calculate_starting_sign`): Lagna sign from
  ChartFacts, with input/derivation/profile/reason evidence. All 12 tested.
* **Direction** (`sequence.direction_for_start_sign`): movable FORWARD, fixed
  REVERSE, dual odd-numbered (Gemini 3, Sagittarius 9) FORWARD, even-numbered
  (Virgo 6, Pisces 12) REVERSE — fixed once for the whole cycle.
* **Sequence** (`sequence.full_cycle`): 12 signs exactly once from start in
  sequence direction; wrap-around both ways tested.
* **Duration** (`duration.duration_for_sign`): inclusive house-count from
  period sign to its SINGLE-classical lord in sequence direction; lord in own
  sign → 12 years (`OWN_SIGN_TWELVE`, else `NONE`). Range 1..12. No dignity
  adjustments. Per-period evidence: reference_sign/lord/lord_sign/
  distance_houses/direction/exception/duration_years.
* **Antardashas:** 12 equal subdivisions from the parent sign in sequence
  direction; child sums == parent (1e-9 years); clamped to parent end.
* **Dates:** birth UTC anchor (full first period), `timedelta(days =
  years × 365.25)`, tz-aware UTC ISO, contiguous boundaries.
* **UNKNOWN:** missing lord-sign planet → status UNKNOWN with missing-input
  explanation; co-lord profiles rejected.

## 3. Models & Pipeline

`JaiminiDashaPeriod` (deterministic IDs `<method>:M<i>:<sign>`,
`<method>:A<j>:<sign>:of:<parent>`), `JaiminiDashaResult` (periods, evidence,
validation, provenance). `calculate_jaimini_dasha(chart_facts, jaimini_facts,
profile)` validates and attaches `DASHA_DERIVED` evidence nodes/edges
(complementing 5F yoga `RULE_DERIVED`).

## 4. Golden Result

Taurus start, REVERSE; head Taurus 9 → Aries 12 → Pisces 7 → Aquarius 8 →
Capricorn 7 → Sagittarius 4 → Scorpio 8 → Libra 2 → Virgo 3 → Leo 12 →
Cancer 8 → Gemini 12; cycle 92.0 years (2005-08-16 → 2097-08-16).
Snapshot `backend/golden_jaimini_dasha_snapshot.json`, engine-generated.
