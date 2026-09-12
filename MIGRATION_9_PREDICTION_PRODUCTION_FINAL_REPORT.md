# MIGRATION #9 — PREDICTION PRODUCTION WIRING + EVENT/TIMING VERIFICATION
## FINAL REPORT

**Verdict: PASS**
**NO COMMIT / NO PUSH — awaiting review.**

Golden chart: 17/08/2005, 12:02 AM IST, Anaparthy AP India (16.93407, 81.95522),
Sidereal / Swiss Ephemeris / Lahiri / Mean Rahu / Whole Sign / PARASHARI_CLASSICAL.
Golden evaluation moment: 2026-09-02T12:00:00+05:30.

---

## 1. Executive Summary

The canonical production prediction path was audited end-to-end and proven
canonical-primary with no silent legacy fallback:

```
birth params + explicit evaluation_datetime
  → generate_chart_facts (canonical natal)
  → get_dynamic_state (canonical dasha + transit + relations + exact events)
  → build_production_entry (pure mapping; windowless facts ≠ exact events)
  → evaluate_prediction (Phase 8 deterministic engine; consumes only)
  → response + provenance → frontend / AI (interpret-only)
```

`POST /prediction/evaluate` verified live on the golden chart (200, 7
candidates, `PARTIAL`, provenance `canonical_transit_engine`). Golden dasha
anchors reproduced exactly (Venus MD ≈ 13.2058y; Moon 257.862785° Purvashada
Pada 2, fraction ≈ 0.339709; 2026-09-02 hierarchy Moon/Rahu/Jupiter/Rahu/Moon).
Two minimal wiring fixes (honest availability flags; 422 on bad datetime —
both adapter/validation, zero astrology). New test file 74/74. Full regression
green. Frontend build green. No new astrology, no Ashtakavarga touch, no
Category-E change, no frontend redesign.

## 2. Production Call Graph

| Node | File : function | Canonical/Legacy | Input → Output |
|------|-----------------|------------------|----------------|
| API | `backend/app.py` → `routes/prediction.router` (`/prediction/evaluate`) | Canonical | birth JSON + eval datetime → response |
| Natal facts | `core/calculation/pipeline.py` : `generate_chart_facts` | Canonical | birth params → ChartFacts |
| Dasha | `core/calculation/dasha.py` : `calculate_vimshottari_timeline`, `get_current_dasha` (via `get_dynamic_state`) | Canonical | Moon longitude → timeline + current hierarchy |
| Transit | `core/calculation/dynamic.py` : `get_dynamic_state` → `core/transit/*` (Swiss Ephemeris) | Canonical | facts + eval datetime → snapshot/relations/aspects/events |
| Entry mapping | `routes/prediction.py` : `build_production_entry` | Canonical adapter | state dump → PredictionInput/entry contract |
| Prediction | `core/prediction/pipeline.py` : `evaluate_prediction` | Canonical | request + entry → PredictionResult |
| Response | `routes/prediction.py` : `evaluate` return block | Canonical adapter | result → candidates/windows/transits/provenance |
| AI interpret | `routes/ai_routes.py` + `ai_transit_context.py` + `ai_engine.py` | Canonical context, interpret-only | deterministic data → prose (no recalc) |
| Frontend | services/hook layer | Presentation-only | displays only; no prediction consumer exists (§13) |

Per-edge classification: every production edge is CANONICAL PRIMARY. No
LEGACY ONLY edge exists on the prediction path. `routes/dynamic.compute_dynamic`
(legacy `compute_chart` wrapper) is DEV ONLY and not on this path.

## 3. Canonical Dasha Audit

Production obtains dasha exclusively from the canonical Vimshottari engine
(Moon longitude → nakshatra → balance-of-MD → full timeline; containment for
current periods). Verified golden anchors, all exact:

- Venus Mahadasha (first, partial), remaining ≈ 13.2058 years ✓
- Moon 257.862785° (anchor 257.862789°, Δ < 0.001°) ✓
- Purvashada Pada 2, fraction ≈ 0.339709 ✓
- 2026-09-02 hierarchy Moon/Rahu/Jupiter/Rahu/Moon ✓
- Timezone/UTC/JD canonical (eval JD 2461285.7708; UTC iso `2026-09-02T06:30:00Z`) ✓
- MD/AD/PD levels projected into entry periods with canonical fingerprints ✓

Nothing reconstructed from response JSON; no legacy dasha import in route.

## 4. Canonical Transit Audit

- Explicit evaluation datetime (supplied, else now-at-boundary; never birth time).
- Timezone handled at boundary; UTC/JD canonical.
- Sidereal Lahiri preserved (`ayanamsha_system: LAHIRI_STANDARD`); Mean Node
  provenance (`node_mode: Mean Node`).
- 9-planet snapshot on golden eval (Jupiter in Cancer).
- Natal positions from canonical ChartFacts; prediction layer performs zero
  position calculation (source scan: no swisseph/ephemeris/Gemini/chart-facts
  computation in evaluator).

## 5. Transit/Natal Relations

`get_dynamic_state` returns 81 relations, 63 Parashari aspects and 81 Western
aspects as **separate keys** — Vedic Graha-Drishti logic stays distinct from
Western aspects; production does not merge them. AI grounding instructs
backend-supplied relations only. Prediction consumes sign facts + exact
timestamps; never recomputes positions.

## 6. Event Definition Audit

- 16/16 categories preserved (`RELATIONSHIP…OTHER`), zero additions.
- Definitions declarative: category → accepted rule IDs + tradition
  constraints + signal/timing requirements. No formulas in definitions or route.
- All ACTIVE definitions reference dotted canonical rule IDs; the one CUSTOM
  entry (`EV.CUSTOM.V1` → `CUSTOM.NATAL.TEST`) stays CUSTOM_DEVELOPER-labelled
  (no classical laundering). Lifecycle filter excludes non-ACTIVE.

## 7. Event Candidate Audit

FACT vs EVENT CANDIDATE vs TIMED EVENT preserved:
- Windowless transit sign facts → `transit_facts` (no timestamps anywhere).
- Exact-timestamp canonical events → `transit_events` (verbatim root stamps).
- Candidates carry windows with precision labels; EXACT precision exists only
  when `exact_events` non-empty (asserted over all golden + live candidates).

## 8. Exact Timing Audit

- Exact timestamps preserved verbatim from canonical root-finding into signals
  (`exact_time`) and windows (`start == end == exact`, precision EXACT).
- Windows without exact backing keep DASHA_RANGE/window semantics; no
  artificial precision invented.
- AI grounding: deterministic candidates interpreted verbatim, never re-timed;
  `prediction_summary` passes through untouched.

## 9. Prediction Evaluator Audit

`evaluate_prediction`: validates range → resolves profile → ACTIVE-only
definition selection → eligibility → candidates → dedup → fingerprints →
validator. Consumes supplied outcomes/periods/facts/events only. Does not
calculate natal/transit/dasha positions, does not invent Yoga/Dosha logic,
does not call Gemini. Phase 7 agents consume read-only summaries downstream.

## 10. Prediction API Audit

`POST /prediction/evaluate`: birth validation (pydantic) → 422 on invalid
datetime (fixed §4 wiring) → canonical facts → canonical state (events
included, 30-day default window) → entry → `PredictionRequest` (profile
`PREDICTION_DEFAULT_V1`, explicit window/selectors) → engine → serialized
response (status/evidence/profile/fingerprints/unknowns/conflicts/candidates/
windows/supporting_transits/eval metadata/transit payload/provenance).
No endpoint: no auth (consistent with public `/dynamic/*` posture; per-request
birth data, no account linkage — verified, not changed). No client parameter
for zodiac/ayanamsha/node/house system exists on the request model (asserted).

## 11. /compute Consistency

Same birth → natal Moon identical (< 1e-6°), ascendant identical (Taurus),
dasha timeline from the same canonical engine. (`/compute` evaluates dasha at
birth moment by design; prediction at the supplied moment — one engine, two
evaluation moments, not two paths.)

## 12. AI Integration

`/ai/analyze` + `/ai/expert_report` receive deterministic prediction data via
verbatim `DETERMINISTIC_PREDICTION` passthrough (newly asserted) alongside the
existing NATAL_FACTS / CURRENT_EVALUATION / CURRENT_TRANSITS /
TRANSIT_NATAL_RELATIONS / TRANSIT_ASPECTS (+EVENTS) / DASHA / PROVENANCE
sections. AI recalculates nothing; grounding text forbids turning UNKNOWN
into FORMED and windows into exact dates (prompt-grounded + verbatim
plumbing; no live-LLM run — no API key in environment).

## 13. Frontend Integration

**Remaining frontend gap (reported, not built):** no UI calls
`/prediction/evaluate` (no `prediction`/`/predict` route usage in services;
the Services page links to a dormant Life Predictor entry). Frontend is
presentation-only: no astrology formulas anywhere. Cache/abort posture exists
(`useCanonicalChart.js` AbortController + generation guards). No UI created —
correctly out of scope without a requiring production consumer.

## 14. Cache/Stale Data Audit

Stateless route: every request regenerates facts. Verified: changed evaluation
datetime changes `evaluation_utc_iso`, transit facts, and fingerprints — stale
output cannot survive changed birth/eval-moment inputs. No server cache layer
on this route; frontend AbortController patterns reused where applicable. No
large cache payloads introduced.

## 15. Evidence

Candidates trace hypothesis → signals → canonical rule/dasha/transit/Jaimini
ancestry with fingerprints; unsupported hypotheses degrade to
EVIDENCE_INSUFFICIENT/UNKNOWN (live golden-route candidates are honestly
UNKNOWN — outcomes not supplied on this route — never FORMED-from-nothing).
Validator rejects missing provenance, invented rule refs, certainty language,
numeric scores. No generic "astrology indicates" evidence exists.

## 16. Provenance

Per-candidate (`event_id/version/request/profile/traditions/signals/origins/
rule_versions/facts/evidence/conflicts/unknowns`) + result-level fingerprints
+ route block (`canonical_transit_engine` / Swiss Ephemeris / Lahiri /
Mean Node / engine `evaluate_prediction`). No classical references invented
for prediction events (no BPHS-style citations in provenance payloads).

## 17. Legacy Caller Audit

| Caller | Classification |
|--------|----------------|
| route → `generate_chart_facts`, `get_dynamic_state`, `evaluate_prediction` | CANONICAL PRIMARY |
| `ai_transit_context` → same canonical chain | CANONICAL PRIMARY |
| Phase 8 `golden.py` fixture builders | TEST ONLY (explicitly off execution path) |
| `routes/dynamic.compute_dynamic` → legacy `compute_chart` | DEV ONLY (not on prediction path) |
| `backend/calculations.py` legacy chart | LEGACY TEST ONLY / retained, not imported by route |

No legacy path overrides canonical prediction. No legacy files deleted.

## 18. Security

- [x] request validation (pydantic + supported-range + profile gates + 422)
- [x] no eval/exec/arbitrary imports (word-boundary source scan)
- [x] no user-controlled engine (no profile/ayanamsha override params)
- [x] no research/experimental rules (ACTIVE-only definitions; experimental excluded)
- [x] AI cannot create events or alter timestamps (verbatim passthrough + grounding)
- [x] frontend cannot override canonical profile (no such channel)
- [x] hostile notes scanned → warnings, never honored
- [x] no path traversal / dynamic imports (static imports only)
- Note: route is unauthenticated by design parity with `/dynamic/*` (§10).

## 19. Performance

Golden `POST /prediction/evaluate` ≈ 5.6 s (ephemeris + 103-event window);
engine-only `full_prediction` ≈ 0.17 s; per-stage breakdown recorded
(signal/formation/window/dedup). Facts generated once per request and reused
down the chain — no N× chart/dasha recomputation. No formula optimization
performed.

## 20. Determinism

Repeat responses semantically identical (candidates + status); 4-thread
concurrent burst identical. Only wall-clock-derived `request_id`
(`LIVE-<iso>`) varies when no explicit ID is supplied — non-semantic.

## 21. Golden Prediction Results

- Dasha anchors: §3, all exact. Transit: Jupiter in Cancer, 9 planets,
  103 exact events in 30-day window.
- Live result: status PARTIAL, 7 candidates, 15 unknowns, evidence
  EVIDENCE_INSUFFICIENT-or-better handling, zero FORMED inventions
  (formation UNKNOWN without supplied rule outcomes — honest).
- Golden engine fixture: evaluates cleanly with EXACT-only-from-exact invariant.

## 22. Tests

New `backend/test_prediction_production_9.py`: **74/74 pass** across call
graph, dasha, transit, relations, definitions, candidates, timing, evaluator,
statuses, missing data, live route, /compute consistency, AI context,
provenance, evidence, determinism, concurrency, security, performance,
stale-cache, legacy isolation.

## 23. Full Regression Results

| Suite | Result |
|-------|--------|
| Migration #9 (new) | 74/74 |
| Phase 8 prediction | 211/211 |
| Phase 10 regression | all pass |
| Phase 12 production | all pass |
| Migration #8 rules/evidence/provenance | 105/105 |
| Migrations #4/#5/#6/#7 | 91/149/87/39 pass |
| Phase 5A/5B/5C | 185/695/pass |
| Phase 6A–6E | 48/51/115/86/105 |
| #3B/#3C, Phase 9/7/11, 5D–5GH, 4B | all pass |
| Phase 3 dasha/transit/panchanga/dynamic/varga + golden canonical | all pass |
| AI/prediction transit hotfixes, Phase-13 shadbala file (run only) | all pass |
| `test_timing_engine.py` | NOT RUN — pre-existing env gap (needs `pytest`) |
| Frontend `vite build` | PASS (23 s, 2402 modules) |

No test weakened. Simulated-failure tracebacks in #4/#6 suites are their own
expected fallback-path logs.

## 24. Files Changed

- `backend/routes/prediction.py` (pre-existing untracked hotfix file):
  1. honest `has_dasha`/`has_jaimini` flags derived from supplied content
     (previously hardcoded True) — **wiring/validation, no astrology**;
  2. invalid evaluation datetime → HTTP 422 (previously raw ValueError/500) —
     **validation, no astrology**.
- NEW `backend/test_prediction_production_9.py` — **test only**.
- NEW `MIGRATION_9_PREDICTION_PRODUCTION_FINAL_REPORT.md` (this file) — **docs**.
- Canonical formulas changed: **NONE** (no edits under `core/prediction/`,
  `core/transit/`, `core/calculation/`, dasha, events, yogas, doshas, jaimini,
  strength, ashtakavarga, frontend).

## 25. Remaining Limitations

1. Production entry supplies `outcomes: []` → candidate formation honestly
   UNKNOWN; wiring canonical Yoga/Dosha/Jaimini outcomes into the entry is a
   future migration, not this one.
2. No CHARA periods on the production route → explicit missing-jaimini-layer
   UNKNOWN signals (honest, by design).
3. No prediction UI consumer exists (frontend gap, §13).
4. Route unauthenticated (parity with `/dynamic/*`; revisit if product requires).
5. Live-LLM behavior not exercised (no API key); AI guarantees are
   prompt + plumbing level.
6. `test_timing_engine.py` unrunnable here (missing `pytest`, pre-existing).

## 26. Final PASS/BLOCKED Verdict

**PASS** — all §32 criteria met: call graph audited; dasha/transit/relations
verified; definitions/candidates/timing verified; evaluator + route verified;
`/compute` consistent; AI receives deterministic data and cannot calculate;
evidence/provenance retained; legacy cannot overwrite canonical; firewall
intact; experimental excluded; missing-data safe; cache behavior verified;
determinism + concurrency verified; security + performance verified; golden
test passes; Phase 8 behavior preserved; full regression green; frontend build
green; no new astrology; no Ashtakavarga/Category-E changes; no redesign;
no commit; no push.

**NO COMMIT / NO PUSH — awaiting review.**
