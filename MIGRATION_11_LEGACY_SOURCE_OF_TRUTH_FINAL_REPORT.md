# MIGRATION #11 — FINAL LEGACY / DEAD-PATH + SOURCE-OF-TRUTH AUDIT
## FINAL REPORT

**Verdict: PASS**
**NO COMMIT / NO PUSH — awaiting review.**

Golden chart: MEDAPATI BHASKARA VENKATA RAJEEV REDDY, 17/08/2005, 12:02 AM IST,
Anaparthy AP India (16.93407, 81.95522), Sidereal / Swiss Ephemeris / Lahiri /
Mean Rahu / Whole Sign / PARASHARI_CLASSICAL.

---

## 1. Executive Summary

Repository-wide audit of every astrology production path is complete. Canonical
specification governs throughout: no legacy result overwrites any canonical
result (proven by import/call-graph trace + live `_source` tags), no duplicate
production engine exists, frontend and AI/agents calculate nothing.

Two defects found and fixed (both wiring/documentation, zero astrology):
1. `/match` was broken at runtime — the pre-existing canonical `/compute`
   rewrite dropped the `compute_match_for_birth_data` import while the route
   still calls it. Single import line restored (legacy-only endpoint; no
   canonical match engine exists). Verified live 200.
2. Legacy `shadbala.py` / `strength_evaluator.py` proven unreachable
   (no production/functional importer) → DEPRECATE via header markers
   (kept on disk; nothing deleted).

One own-test-run side effect reverted (`golden_dosha_snapshot.json`
ordering-only rewrite). New test file 55/55. Full regression green. Vite
build green. Nothing mass-deleted; default KEEP honored everywhere else.

## 2. Repository Inventory

- `backend/*.py` (~85 files): canonical adapters (`canonical_*`), legacy
  calculators (`calculations`, `yoga_evaluator`, `doshas_advanced`, `jaimini`,
  `ashtakavarga`, `maitri`, `panchanga_advanced`, `tables`, `shadbala`,
  `strength_evaluator`), shared helpers, ~40 test files, dev `verify_*` /
  `compare_vargas` / `diagnose_*` / `golden_*` scripts, `main.py` launcher.
- `backend/core/`: calculation (ephemeris/dasha/panchanga/varga/dynamic),
  transit, strength, rules (5A + parashari/doshas/dynamic), jaimini,
  prediction, agents, research, regression, ops.
- `backend/routes/`: astro, dynamic, prediction, ai_routes, research
  (read-only), ops, auth/family/learning/api_keys/geocode (non-astrology).
- `frontend/src/`: no astrology formulas (scanned); services pass params;
  sessionStorage holds auth tokens only; chartData localStorage has
  generation guards + quota handling.
- Swiss Ephemeris imports confined to canonical calculation layers +
  legacy `calculations.py` + `app.py` (presence check) + tests/dev scripts.

## 3. Source-of-Truth Matrix

| Domain | Canonical engine | Production caller | Legacy caller | Status | Action |
|--------|------------------|-------------------|---------------|--------|--------|
| D1 | `core/calculation/pipeline.generate_chart_facts` | astro route, canonical_response | none | Canonical | KEEP |
| Varga | `core/calculation/varga.calculate_all_vargas` | same | none | Canonical | KEEP |
| Panchanga | `core/calculation/panchanga` | canonical_response, dynamic | panchanga_advanced (Avakahada/Ghata only) | Canonical-primary | KEEP both, documented |
| Vimshottari Dasha | `core/calculation/dasha` | dynamic state, prediction | none | Canonical | KEEP |
| Current Dasha | `get_current_dasha` (containment) | same | none | Canonical | KEEP |
| Transit | `core/transit/*` via `get_dynamic_state` | dynamic, prediction, AI context | none | Canonical | KEEP |
| Transit/Natal Relations | `compute_transit_natal_relations` | same chain | none | Canonical | KEEP |
| Event Candidates | `core/prediction/candidates` | prediction route | none | Canonical | KEEP |
| Prediction | `evaluate_prediction` | prediction route | none | Canonical | KEEP |
| Shadbala | `core/strength/shadbala` | canonical_strength | legacy `shadbala.py` (dead) | Canonical | KEEP; legacy DEPRECATE |
| Bhava Bala | `core/strength` | canonical_strength | none | Canonical | KEEP |
| Vimsopaka | `core/strength` | canonical_strength | none | Canonical | KEEP |
| Avastha | `core/strength` | canonical_strength | none | Canonical | KEEP |
| Dignity | `core/strength/dignity` | canonical_strength | legacy scorer (dead) | Canonical | KEEP; legacy DEPRECATE |
| Functional Nature | `core/strength` | canonical_strength | none | Canonical | KEEP |
| Custom Composite | `core/strength/composite` | canonical_strength | none | Canonical | KEEP |
| Parashari Yoga | `core/rules/parashari` (77) | canonical_yoga | yoga_evaluator (gap-fill) | Canonical-primary | KEEP both |
| Category C Yoga | classical_yogas (in 77) | same | suppressed IDs | Canonical | KEEP |
| Category D Yoga | category_d_yogas (in 77) | same | suppressed IDs | Canonical | KEEP |
| Category E Yoga | — (gap documented) | — | legacy rulesets only | GAP | DOCUMENT GAP, untouched |
| Dosha (6) | `core/rules/doshas` | canonical_dosha | doshas_advanced (exception rollback) | Canonical | KEEP both |
| Jaimini | `core/jaimini/*` | canonical_jaimini | jaimini.py (exception rollback) | Canonical | KEEP both |
| Chara Dasha | `core/jaimini/dasha` | jaimini adapter | none on prod path | Canonical | KEEP |
| Ashtakavarga | — (no canonical capability) | legacy `ashtakavarga.py` | same | LEGACY REQUIRED | KEEP, §14 |
| Dynamic Rules | dynamic engine + RuleRegistry view | canonical_rules | none | Canonical | KEEP |
| Evidence | EvidenceBuilder/formatters | adapters | none | Canonical | KEEP |
| Provenance | ProvenanceRegistry | adapters | none | Canonical | KEEP |
| AI Agents (6) | deterministic builders | canonical_agents | mock adapter (tests) | Canonical | KEEP |
| AI Synthesis | Gemini interpret-only + grounding | ai_routes | none | Canonical posture | KEEP |

## 4. Production Call Graphs

- `/compute`: route → `generate_chart_facts` + `calculate_all_vargas` →
  `build_canonical_compute_response` → `enrich_response_with_legacy_modules`
  (canonical yoga/dosha/jaimini/strength first; legacy gap-fill/rollback only).
- `/ai/analyze` → summarize → transit section → agent findings → Gemini.
- `/ai/expert_report` → expert context (+rules) → transit → agents → Gemini.
- `/prediction/evaluate` → facts → dynamic state → entry → engine → response.
- `/match` → legacy `compute_match_for_birth_data` (legacy-only, restored).
- `/dynamic/*` → canonical state builders (`compute-dynamic` sub-path is
  DEV ONLY legacy wrapper, not on any canonical path).

## 5. D1 / Varga Audit

`generate_chart_facts` + `calculate_all_vargas` authoritative; no legacy
overwrite (no legacy importer besides rollback/dev). Golden anchors unchanged
(Moon 257.862789°, asc Taurus — verified live in §29).

## 6. Panchanga Audit

Canonical Tithi/Nakshatra/Yoga/Karana/weekday/sunrise/sunset primary.
`panchanga_advanced` retained ONLY for Avakahada/Ghata Chakra (no canonical
equivalent) — documented reason, separate response key, no overwrite.

## 7. Dasha Audit

Canonical Vimshottari primary; current hierarchy from canonical containment.
Goldens unchanged: Venus ≈13.2058y; 2026-09-02 Moon/Rahu/Jupiter/Rahu/Moon
(re-verified via `/dynamic/state` in tests). No legacy dasha anywhere.

## 8. Transit Audit

Canonical Swiss Ephemeris engine primary (Lahiri, Mean Node). No duplicate
calculation in prediction/AI/agents/frontend (source scans clean across
Migrations #9–#11). Legacy transit helpers: none outside canonical tree.

## 9. Prediction Audit

Migration #9 chain intact: facts → dasha → transit → relations → candidates
→ evaluator. Live `canonical_transit_engine` provenance re-verified. No
legacy prediction path exists, let alone overrides.

## 10. Full Strength Audit

All seven components canonical-primary with goldens intact (Sun 6.18,
Moon 5.73, Mars 5.50, Mercury 7.33, Jupiter 6.81, Venus 7.34, Saturn 4.52 —
asserted live). Formulas untouched. Legacy scorer files deprecated (§31).

## 11. Yoga Audit

77/82 canonical via `canonical_yoga.py`; covered legacy IDs suppressed;
uncovered legacy gap-fill tagged `legacy_fallback`. Category-E
(Garuda/Kalpadruma/Mahabhagya/Matsya/Mridanga): no canonical entries,
NOT implemented, legacy ruleset files untouched.

## 12. Dosha Audit

Six canonical rules authoritative with live evidence/provenance (Gaja Kesari
analogue: Mangal 3-reference block verified). Formulas untouched; legacy
rollback exception-only.

## 13. Jaimini Audit

Chara Karakas, Karakamsha, AL/UL, Rashi Drishti, yogas, Chara Dasha all
canonical-primary with evidence/provenance. No duplicated calculations.

## 14. Ashtakavarga Audit

No canonical engine exists (no `core/ashtakavarga`, no
`canonical_ashtakavarga.py` — asserted). Legacy `backend/ashtakavarga.py`
retained: AV_TABLES intact, no canonical claims in-file, no transit/kaksha
additions. Classification: **LEGACY REQUIRED — NO CANONICAL EQUIVALENT**.
Untouched.

## 15. Dynamic Rule Audit

`canonical_rules.py` registry view (83 rules) + ACTIVE-only dynamic
evaluation intact (`evaluated_count` 0 on empty production registry —
correct). Research imports absent from bridge; EXPERIMENTAL promotion
blocked (re-tested). No eval/exec/dynamic execution.

## 16. Evidence Audit

Canonical evidence primary end-to-end (Gaja Kesari + all doshas non-empty
live). No legacy evidence generator exists on the path; nothing overwrites.

## 17. Provenance Audit

Canonical provenance primary (BPHS Ch. 36 Vs. 1-2 VERIFIED live). No
fabricated citations; UNVERIFIED stays UNVERIFIED; Ashtakavarga carries no
fake provenance.

## 18. AI Agent Audit

Six agents reachable via `canonical_agents.py`; agent sources contain no
ephemeris/chart/dasha/transit/yoga/dosha/jaimini/prediction engine imports
(re-scanned). Restatement specialists only.

## 19. AI Synthesis Audit

Gemini downstream of deterministic facts on both routes; grounding forbids
calculation/override/invention/research-promotion/UNKNOWN-override.
Mocked-LLM tests prove findings delivery. No live-LLM run (no key).

## 20. Frontend Boundary Audit

No planetary/dasha/yoga/dosha/transit/strength formulas in `frontend/src`
(regex scan incl. tests-excluded); backend remains authoritative
(`chartParams.js` states this explicitly). No redesign; `vite build` green.

## 21. Legacy Module Matrix

| Module | Caller | Classification | Canonical replacement | Safe to remove? | Reason |
|--------|--------|----------------|-----------------------|-----------------|--------|
| calculations.py | /match, dynamic.compute-dynamic, dev scripts | LEGACY ROLLBACK (+ legacy-only /match) | None for match | No | Unique capability |
| yoga_evaluator.py | canonical_response gap-fill | LEGACY FALLBACK | Partial (77 covered) | No | Uncovered rules |
| doshas_advanced.py | exception rollback | LEGACY ROLLBACK | Yes | No | Rollback requirement |
| jaimini.py | exception rollback | LEGACY ROLLBACK | Yes | No | Rollback requirement |
| ashtakavarga.py | canonical_response | LEGACY REQUIRED | None | No | No canonical equivalent |
| maitri.py | canonical_response | LEGACY REQUIRED | None | No | Unique capability |
| panchanga_advanced.py | canonical_response | LEGACY REQUIRED | None (Avakahada/Ghata) | No | Unique capability |
| tables.py | canonical_response, core strength | CANONICAL PRODUCTION (shared helper) | N/A | No | In active use |
| shadbala.py | none (dev/import checks) | DEAD → DEPRECATE | Yes | Not yet (test imports) | Marker added, kept |
| strength_evaluator.py | none (import checks) | DEAD → DEPRECATE | Yes | Not yet (test imports) | Marker added, kept |
| compare_vargas/verify_*/quick_test/diagnose/golden_* | none (dev invocation) | DEV ONLY | N/A | No | Tooling |
| main.py | launcher | launcher (non-astro) | N/A | No | Entry point |
| knowledge_base.py | ai_routes (static text) | CANONICAL support (no calc) | N/A | No | Interpretive text |

## 22. Import / Call Graph

Absolute-import trace (test + dev + relative-sibling excluded): every legacy
production edge lands in `canonical_response.py` (fallback/rollback/required)
except `calculations.py` → `/match` + dev `compute-dynamic`. No hidden
dynamic imports (`importlib` absent from routes/bridge/router). `app.py`
`swe` import is a dependency presence check only.

## 23. Response Overwrite Audit

Searched canonical→legacy same-key writes: none. Yoga merge is additive with
covered-ID suppression (order asserted); dosha keys written once canonically
(fallback in `except` only — asserted by position); jaimini canonical with
exception fallback; strength/shadbala/rules canonical-only keys. **Clean.**

## 24. Source Tag Audit

Live vocabulary: `canonical` (77 yogas, mangal, jaimini, rules, doshas),
`legacy_fallback[_full]` (gap-fill only), `production_agents`. 82 yogas use
only established vocabulary; Ashtakavarga carries no canonical label.
Truthful throughout.

## 25. Cache Audit

Prediction route stateless (no cache); response builder holds no browser
storage; frontend chartData guards + quota handling intact (Phase 11);
no fingerprint changes that would orphan caches; no large payloads added
(#11 delta is one import line + comments).

## 26. Security

- [x] no eval/exec/arbitrary/dynamic imports in production path (scanned)
- [x] no research→production / experimental→production bypass (re-tested)
- [x] no frontend astrology calculation
- [x] no legacy override; no profile override (no such params)
- [x] no hidden calculation path (full swe/import trace)

## 27. Determinism

`/compute` repeat byte-identical; golden values stable; agent/prediction
determinism covered by Migrations #9–#10 suites (74 + 103 green).

## 28. Concurrency

3-way concurrent `/compute` byte-identical; no cross-request contamination
(stateless construction per request; frozen shared models).

## 29. Golden Chart Verification

Moon 257.862789° (±0.001), Shadbala Jupiter 6.81 / Saturn 4.52 (±0.05),
77 canonical yogas, Category-E absent from canonical — allunchanged.

## 30. Endpoint Matrix

| Endpoint | Domain | Canonical primary? | Legacy edge? | Result |
|----------|--------|--------------------|--------------|--------|
| /compute | natal+all domains | Yes | gap-fill/rollback/required (tagged) | PASS |
| /prediction/evaluate | prediction | Yes | none | PASS |
| /ai/analyze | synthesis | Yes | none | PASS (mocked LLM) |
| /ai/expert_report | synthesis | Yes | none | PASS (mocked LLM) |
| /match | compatibility | No — legacy-only | legacy engine (restored) | PASS (200) |
| /dynamic/state, /dynamic/* | dasha/transit | Yes | none (compute-dynamic dev-only) | PASS |
| /research/golden, /research/gates | research | Read-only | none | PASS |

## 31. Deprecation Decisions

- `shadbala.py`, `strength_evaluator.py`: **DEPRECATE** (header markers;
  kept — test files import them, failing removal proof #2).
- Everything else: **KEEP** (rollback/test/dev/unique-capability reasons).
- **REMOVE**: nothing. Zero deletions.

## 32. Tests

New `backend/test_legacy_source_of_truth_11.py`: **55/55 pass** (call graphs,
precedence, classification incl. absolute-import trace, overwrite prevention,
source tags, Ashtakavarga, frontend boundary, cache, prediction, AI/agents,
dynamic boundary, evidence, provenance, firewall, security, determinism,
concurrency, goldens, endpoint matrix incl. restored `/match`).

## 33. Full Regression Results

Migrations #11/#10/#9/#8: 55/103/74/105; Phase 7/8/10/12/9/11: all pass;
#4/#5/#6/#7: 91/149/87/39; 5A/5B/5C, 6A–6E, #3B/#3C, 5D–5GH, 4B, Phase-3
family, goldens, hotfixes: all pass; `test_timing_engine.py` NOT RUN
(pre-existing: needs `pytest`); `vite build` PASS (20 s). No weakening.

## 34. Files Changed

- `backend/routes/astro.py` (pre-existing mods retained): + one import line
  restoring `compute_match_for_birth_data` for legacy-only `/match`.
  Purpose: fix runtime NameError. Production impact: `/match` works again
  (200, legacy output). Wiring only. Astrology formulas changed: none.
  Source-of-truth changed: none (endpoint classified legacy-only).
- `backend/shadbala.py`, `backend/strength_evaluator.py`: + deprecation
  header comments only. Production impact: none. Formulas: none (untouched).
- NEW `backend/test_legacy_source_of_truth_11.py`: tests only.
- NEW `MIGRATION_11_LEGACY_SOURCE_OF_TRUTH_FINAL_REPORT.md`: docs only.
- Reverted own side effect: `golden_dosha_snapshot.json` (ordering-only).
- Deleted: nothing. All other pre-existing tree changes untouched.

## 35. Remaining Limitations

1. `/match` remains legacy-only (no canonical match engine — documented gap).
2. Category-E Yogas + Ashtakavarga canonical gaps documented, untouched.
3. Deprecated files kept (test import-presence coupling).
4. Live-LLM wording unasserted (no key); `test_timing_engine.py` needs pytest.

## 36. Final PASS/BLOCKED Verdict

**PASS** — all §37 criteria met: inventory + matrix complete; call graphs
traced; D1/Varga/Panchanga/Dasha/Transit/Prediction/Strength/Yoga/Dosha/
Jaimini/Dynamic-Rules/Evidence/Provenance/Agents/Synthesis verified canonical
(or documented legacy-required); callers classified with no vague entries;
overwrite/source-tag/cache audits clean; security clean; determinism +
concurrency verified; goldens unchanged; Ashtakavarga preserved as legacy;
Category-E untouched; no new astrology; no unsafe deletion (none);
regression + frontend build green.

**NO COMMIT / NO PUSH — awaiting review.**
