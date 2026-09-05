# ASTROLIFE V2 — PHASE 6A: RULE DSL

**Module:** `backend/core/rules/dynamic/dsl.py` + `evaluator.py`

## 1. ConditionNode

`{op, params, children[], n?}`. Data-only; the evaluator reads known ops and
compares resolved fact values. Payload strings are inert data (equality only).

## 2. Primitives (22)

planet_in_sign, planet_in_house, planet_in_varga_sign, planet_owns_house,
planets_conjunct, planets_aspect, rashi_drishti, karaka_equals, pada_equals,
planet_exalted, planet_debilitated, planet_in_own_sign, planet_in_moolatrikona,
house_is_kendra, house_is_trikona, lord_in_house, lord_of_house, dasha_active,
transit_in_sign, transit_conjunct_natal, strength_threshold, rule_formed.
Each declares required params; vocabularies validated (planets, signs 1–12
houses, 16 vargas, 8 karakas).

## 3. Composition

ALL (false-dominant), ANY (true-dominant), NOT (exactly 1 child),
EXACTLY_N / AT_LEAST_N / AT_MOST_N with `0 <= n <= children`. Missing inputs
propagate UNKNOWN (never coerce to FALSE), except exact-count decidability
rules documented in `evaluator.py`.

## 4. Fact Paths & Resolver

Dotted paths (`natal.Mars.sign`, `varga.D9.Mars`, `jaimini.karaka.AK`,
`dasha.JAIMINI_CHARA.active_sign`, `transit.Jupiter.sign`,
`strength.shadbala.Jupiter`, `rule:ID`). Caller-supplied resolver;
undeclared paths rejected with `UNDECLARED_ACCESS` diagnostics; missing facts
⇒ UNKNOWN. Formation/cancellation/mitigation evaluate to
FORMED|NOT_FORMED|UNKNOWN, CANCELLED|NOT_CANCELLED|UNKNOWN,
MITIGATED|NOT_MITIGATED|UNKNOWN independently, with per-node evidence.

## 5. UNKNOWN Semantics

Missing D9/transit/dasha/strength/karaka ⇒ UNKNOWN for dependent trees only.
UNKNOWN ≠ NOT_FORMED ≠ NOT_ACTIVE. Source confidence never alters formation.
