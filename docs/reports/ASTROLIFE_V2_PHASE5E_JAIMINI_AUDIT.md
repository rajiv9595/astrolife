# ASTROLIFE V2 — PHASE 5E: JAIMINI YOGA / RULE ENGINE REPOSITORY AUDIT

**Date:** 2026-09-04
**Scope:** Pre-implementation audit for Phase 5E — Jaimini Classical Yoga / Rule Engine
**Status:** Audit Complete — Ready for Catalogue & Implementation
**Prior phase:** Phase 5D-H COMPLETE and formally accepted (do not redesign).

---

## 1. What Already Exists (reuse, do not duplicate)

### 1.1 Jaimini Foundation (`backend/core/jaimini/`, Phase 5D/5D-H, accepted)
| Module | Provides | 5E reuse |
| :--- | :--- | :--- |
| `profile.py` | `JaiminiCalculationProfile` (+ `source_reference="UNVERIFIED"`), Karaka/Rahu/Drishti/Arudha/Upapada/CoLord enums | Consume as-is; evaluation profile must match facts' `karaka_method` |
| `models.py` | `KarakaItem`, `CharaKarakasReport`, `RashiDrishtiReport`, `ArudhaPadaItem`, `UpapadaDetails`, `KarakamshaDetails`, `JaiminiProvenance` (UNVERIFIED), `JaiminiFacts` | Direct consumption; no new fact calculation |
| `karakas.py` | 7/8-karaka ranking, Rahu DIRECT/INVERSE, tie-breaking + evidence | Consume output only |
| `rashi_drishti.py` | `CANONICAL_SIGN_ASPECTS`, `get_sign_rashi_drishti`, sign + planet propagation; imports NO Parashari aspect code | Only sanctioned aspect source |
| `arudha.py` | `CLASSICAL_SIGN_LORDS`, `calculate_single_arudha` (single source of truth) | Consume padas; reuse lord map; never recalculate |
| `padas.py` / `upapada.py` | A1–A12, UL==A12 invariant | Consume only |
| `karakamsha.py` | Karakamsha (AK D9) vs Swamsa (D9 Lagna) separated | Consume only |
| `context.py` | `JaiminiContext` read-only accessors (karakas, AL/UL, drishti checks) | Primary rule-input façade |
| `pipeline.py` | `generate_jaimini_facts` (deterministic, validated) | Upstream only |
| `validators.py` | Fact integrity checks | Upstream only |

Accepted golden facts (engine truth, never hardcode in rules): AK=Jupiter,
AmK=Moon, BK=Mars, MK=Mercury, PK=Saturn, GK=Venus, DK=Sun; Karakamsha=Cancer;
AL=Capricorn; UL=Capricorn. Snapshot: `backend/golden_jaimini_snapshot.json`.

### 1.2 Generic Rule Engine (`backend/core/rules/`, Phase 5A, accepted)
Reusable without modification: `enums.py` (`RuleCategory.JAIMINI`,
`RuleTradition.JAIMINI`, `FormationStatus`, `StrengthStatus`,
`CancellationStatus`, `MitigationStatus`, `ConfidenceLevel`,
`SourceType`, `Provenance` with `source_reference: str`), `registry.py`
(`RuleRegistry`), `evaluator.py`, `context.py` (`RuleContext` over ChartFacts),
`cancellation.py` / `mitigation.py` patterns, `provenance.py`.

NOT reused: `RuleResult` / `EvaluationResult` (both stamp
`datetime.utcnow()`, breaking snapshot determinism) and the
`Condition`-tree evaluator (overkill for Jaimini fact predicates; Jaimini
rules evaluate pure predicates over `JaiminiFacts`). 5E defines its own
timestamp-free result model reusing the accepted enums.

### 1.3 Parashari Yoga Engine (`backend/core/rules/parashari/`, Phase 5B, accepted)
Pattern to mirror (not import logic from): per-group builder modules +
`FORMATION_EVALUATORS` dict + `catalog.py` + golden snapshot
(`golden_snapshot.json`) + fixture tests. Reusable constants by import:
`KENDRA_HOUSES`, `TRIKONA_HOUSES`, `NATURAL_BENEFICS`, `NATURAL_MALEFICS`,
`SEVEN_PLANETS` from `structural.py` (single source; attributed at import).
Sign lords reused from Jaimini-owned `arudha.CLASSICAL_SIGN_LORDS`
(identical values, avoids cross-tradition coupling). Parashari *aspect*
functions are NEVER imported.

### 1.4 Dosha Engine (`backend/core/rules/doshas/`, Phase 5C, accepted)
Pattern reference only (catalog + afflictions + golden snapshot). No imports.

### 1.5 Upstream facts (accepted, read-only)
`core.calculation.models.ChartFacts` (D1 signs/houses), `core.calculation.varga`
(D9 via `varga_facts["planets"][P]["D9"]` / `varga_facts["ascendant"]["D9"]`,
`VargaPosition` or dict form). No astronomy recalculation in 5E.

### 1.6 Legacy + consumers (must remain compatible, untouched)
* `backend/jaimini.py` — dict prototype used by `backend/routes/astro.py:84`
  (`compute_jaimini_system(chart_data["planets"], chart_data["asc_sign"])`).
* `frontend/.../JaiminiCard.jsx` consumes `jaimini.chara_karakas` (dict) and
  `jaimini.arudha_padas` (dict). 5E adds a new service; no route/frontend change.

---

## 2. What Must Be Added (Phase 5E scope)

New subpackage `backend/core/jaimini/rules/` (pure, deterministic, timestamp-free):
`profile.py` (`JaiminiYogaProfile`: enabled rules, karaka-method guard, benefic
sets), `models.py` (timestamp-free `JaiminiRuleResult` with structured
formation/cancellation/mitigation evidence; `JaiminiYogaEvaluation` container),
`predicates.py` (reusable karaka/drishti/arudha/D9 predicates over
`JaiminiFacts`+`ChartFacts`+varga facts), `catalogue.py` (12 stable rule IDs,
all `TRADITION_DEPENDENT`/`CLASSICAL_JAIMINI` labelled, `UNVERIFIED` refs),
`karaka_yogas.py` / `drishti_yogas.py` / `arudha_yogas.py` /
`karakamsha_yogas.py`, `pipeline.py`
(`evaluate_jaimini_yogas(chart_facts, jaimini_facts, varga_facts, profile)`),
`__init__.py` exports. Tests: `backend/test_jaimini_yogas_phase5e.py`.
Snapshots: `backend/golden_jaimini_yoga_snapshot.json` (engine-generated).
Docs: audit (this file), specification, test report, rule catalogue.

## 3. What Must NOT Be Changed
5D foundation, calculation/varga/panchanga/dasha/transit/strength engines,
generic rule engine, 5B, 5C, `backend/jaimini.py`, routes, frontend.
If an upstream defect surfaces: STOP and report; do not silently refactor.

## 4. Unresolved Textual / Source Questions
Exact sutra/verse provenance for every Jaimini yoga is UNVERIFIED. Therefore
ALL 5E rules carry `source_reference="UNVERIFIED"` and confidence
`TRADITION_DEPENDENT` (no `UNVERIFIED` member exists in accepted
`ConfidenceLevel`; `TRADITION_DEPENDENT` + explicit UNVERIFIED reference is the
honest mapping). No Adhyaya/Pada/sutra/verse numbers or Sanskrit quotations
anywhere. Origin labels (`CLASSICAL_JAIMINI` vs `TRADITION_DEPENDENT`) record
consensus level only, never verification.

## 5. Tradition-Dependent Decisions
* 7/8-karaka isolation enforced: evaluation aborts rules whose facts-method
  mismatches the yoga profile (never mix).
* Benefics `(Jupiter, Venus, Mercury, Moon)` / malefics `(Sun, Mars, Saturn,
  Rahu, Ketu)` imported from `parashari.structural` (documented convention).
* Quality (strength) left `UNASSESSED` for all rules — no defensible classical
  quality formula in scope; formation ≠ strength.
* Cancellation: only structural karaka-identity tie → `PARTIAL`; else `NONE`
  with evidence (never inferred from benefic/malefic presence).
* Mitigation: benefic Rashi Drishti / co-occupancy on focal sign → `PARTIAL`
  supporting influence, labelled `TRADITION_DEPENDENT`; else `NONE`.
* Wording is conditional only ("condition … is formed"); zero timing/outcome
  claims; no scores, no AI, no Western aspects, no orbs.

## 6. Test Strategy
Per rule: positive / negative / boundary / unrelated fixtures (+ cancellation
tie fixture, + mitigation fixture where applicable). Exhaustive: 12 ascendants,
lord-placement sweeps, drishti permutations, karakamsha≠swamsa interchange
trap, 7k/8k isolation, UL variations, independent reference predicates (not
calling production code). Determinism: repeated evaluation + snapshot bytes.
Guards: no-prediction vocabulary scan, no-astronomy scan (no Swiss Ephemeris /
`datetime.now` in rules package). Regression: all prior suites re-executed
with exact accounting (EXECUTED vs CARRIED-FORWARD), repo-root invocation noted
for Dasha/Dynamic suites.
