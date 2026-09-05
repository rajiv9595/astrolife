# ASTROLIFE V2 — PHASE 5E: JAIMINI YOGA / RULE ENGINE SPECIFICATION

**Version:** 1.0.0
**Status:** IMPLEMENTED & VALIDATED
**Foundation:** Phase 5D/5D-H (accepted, untouched)

---

## 1. Objective

Deterministic, provenance-aware evaluation of classical Jaimini yogas/rules on
top of accepted Phase 5D facts (Chara Karakas, Rashi Drishti, Arudha Padas,
AL, UL, Karakamsha, Swamsa) plus D1/D9 occupancy, sign lordship, and
tradition-explicit association. No dashas, no timing, no outcomes, no AI.

## 2. Architecture (`backend/core/jaimini/rules/`)

| File | Role |
| :--- | :--- |
| `profile.py` | `JaiminiYogaProfile` (karaka-method guard, enabled subset, tolerance) |
| `models.py` | Timestamp-free `JaiminiRuleResult`, `YogaOutcome`, `JaiminiYogaEvaluation` |
| `predicates.py` | Pure D1/D9/karaka/drishti helpers over canonical inputs |
| `catalogue.py` | 12 stable IDs, metadata, evaluator wiring |
| `karaka_yogas.py` | 3 karaka rules |
| `drishti_yogas.py` | 3 Rashi-Drishti rules |
| `arudha_yogas.py` | 4 Arudha/AL/UL rules |
| `karakamsha_yogas.py` | 2 Karakamsha/Swamsa rules |
| `pipeline.py` | `evaluate_jaimini_yogas(chart_facts, jaimini_facts, varga_facts, profile)` |

Decisions: 5A enums reused (`RuleCategory.JAIMINI`, `RuleTradition.JAIMINI`,
`FormationStatus`, `StrengthStatus`, `CancellationStatus`,
`MitigationStatus`, `ConfidenceLevel.TRADITION_DEPENDENT`,
`SourceType.UNVERIFIED`); `RuleResult` NOT reused (wall-clock timestamp breaks
determinism); `RuleEvaluator`/`Condition` tree not reused (overkill for fact
predicates). House tuples + benefic sets imported from
`core.rules.parashari.structural` (single source); sign lords from
Jaimini-owned `arudha.CLASSICAL_SIGN_LORDS`. Parashari aspect code never
imported. Karaka-method mismatch raises `ValueError` (7k/8k never mix).

## 3. Result Model

Per rule: `formed` + `formation_status` (FORMED/NOT_FORMED) distinct from
`quality` (always `UNKNOWN` = UNASSESSED — no defensible quality formula in
scope), `cancellation_status` (NONE, or PARTIAL on karaka-identity tie),
`mitigation_status` (PARTIAL on supporting benefic influence, NONE for D9-scope
rules with explicit scope evidence), structured `formation_evidence`
(condition/actual/expected/source_fact/passed), string
cancellation/mitigation evidence, provenance
(`tradition=JAIMINI`, `source_reference=UNVERIFIED`,
`confidence=TRADITION_DEPENDENT`), dependencies, notes. Results ordered by
`rule_id`; container carries profile/facts methods + provenance. No scores.

## 4. Rule Definitions (summary; full catalogue in RULE_CATALOGUE doc)

* `JAI.KARAKA.AK_AMK_CONJUNCTION` — AK & AmK same D1 sign (CLASSICAL_JAIMINI).
* `JAI.KARAKA.AK_KENDRA_FROM_AL` — AK in kendra from AL (TRADITION_DEPENDENT).
* `JAI.KARAKA.DK_UL_SAMBANDHA` — DK in UL / lords UL / mutual-drishti with UL
  lord; mode recorded (TRADITION_DEPENDENT).
* `JAI.DRISHTI.AK_AMK_MUTUAL` — mutual Rashi Drishti, same-sign excluded
  (CLASSICAL_JAIMINI). Disjoint from conjunction by construction.
* `JAI.DRISHTI.AMK_ON_AL`, `JAI.DRISHTI.AK_ON_AL` — karaka aspects AL
  (TRADITION_DEPENDENT).
* `JAI.ARUDHA.AL_BENEFIC_OCCUPANCY` — benefic in AL, D1 (CLASSICAL_JAIMINI).
* `JAI.ARUDHA.AL_LORD_KENDRA_TRINE` — AL lord in kendra/trikona from AL
  (CLASSICAL_JAIMINI).
* `JAI.ARUDHA.DHANA_A2_A11` — A2/A11 same sign, mutual drishti, or shared
  lord; mode recorded (CLASSICAL_JAIMINI).
* `JAI.ARUDHA.A7_UL_ALIGNMENT` — A7 == UL (TRADITION_DEPENDENT).
* `JAI.KARAKAMSHA.BENEFIC_OCCUPANCY` — benefic in Karakamsha D9 sign
  (TRADITION_DEPENDENT).
* `JAI.SWAMSA.BENEFIC_OCCUPANCY` — benefic in Swamsa D9 sign
  (TRADITION_DEPENDENT).

Arudha arithmetic is never recomputed; UL consumed from the A12 engine;
Karakamsha ≠ Swamsa enforced with interchange-trap tests. Wording is
conditional only ("condition … is formed").

## 5. Provenance & Verification Gate

All rules: `tradition=JAIMINI`, `source_reference=UNVERIFIED`,
`confidence=TRADITION_DEPENDENT`. No Adhyaya/Pada/sutra/verse numbers or
quotations. Origin labels record consensus level, never verification.

## 6. Determinism & Guards

50-iteration bit-for-bit identical evaluations; timestamp-free models;
sorted outputs. Guards: no prediction/timing/outcome vocabulary, no
independent astronomical computation, no Parashari/Western aspect paths,
legacy `compute_jaimini_system` schema intact, routes/frontend untouched.
