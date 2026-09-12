# MIGRATION #8 — DYNAMIC RULES + EVIDENCE / PROVENANCE PRODUCTION WIRING
## FINAL REPORT

**Verdict: PASS**
**NO COMMIT / NO PUSH — awaiting review.**

Golden chart: MEDAPATI BHASKARA VENKATA RAJEEV REDDY, 17/08/2005, 12:02 AM IST,
Anaparthy AP India (16.93407, 81.95522), Sidereal / Swiss Ephemeris / Lahiri /
Mean Rahu / Whole Sign / PARASHARI_CLASSICAL.

---

## 1. Executive summary

The canonical Dynamic Rule Engine (Phase 5A `RuleContext`/`RuleEvaluator`/`RuleResult`,
Phase 6A–6E dynamic DSL/engine/registry/RuleLab), `EvidenceBuilder`, and
`ProvenanceRegistry` architectures were fully audited. Production (`/compute`)
already evaluated canonical Yoga/Dosha/Jaimini/Strength through per-domain
adapters, but had **no production entrypoint at all** for the canonical rule
registry or the dynamic rule engine — both were reachable only from tests.

Migration #8 adds the thinnest possible production bridge
(`backend/canonical_rules.py`, new, ~230 lines, **zero astrology formulas**):

- ONE production `RuleRegistry` view populated via the existing
  `register_parashari_rules` / `register_dosha_rules` catalogue functions
  (77 Parashari + 6 Dosha = 83 registered rules; no duplicate registry class).
- `build_production_rule_context` / `build_production_dynamic_context`: single
  canonical-facts → context constructors (never response JSON, never frontend).
- `evaluate_production_dynamic_rules`: **ACTIVE-lifecycle-only** evaluation with
  conflict **REPORT-ONLY** semantics; empty production registry → 0 evaluations.
- Additive `rules` block in `/compute` (`registry` coverage + `dynamic`
  outcome, `_source: canonical`); additive `rules` passthrough in AI expert
  context. No existing response key changed.

No new astrology rules. No Ashtakavarga change. No Yoga/Dosha/Jaimini/Strength
formula change. `backend/test_rules_evidence_production_8.py`: **105/105 pass**.
All prior suites green (see §33). Two pre-existing environment notes (§33).

## 2. Architecture inventory

| Path | Role | Production use (after #8) |
|------|------|---------------------------|
| `backend/core/rules/context.py` | `RuleContext` (facts consumer, no astronomy) | Primary, via bridge + 3 adapters |
| `backend/core/rules/evaluator.py` | `RuleEvaluator` (deterministic) | Primary (Yoga/Dosha catalogues) |
| `backend/core/rules/models.py` | `RuleResult`, `Evidence`, `Provenance`, `RuleDefinition` | Primary |
| `backend/core/rules/registry.py` | `RuleRegistry` + global singleton | Primary via `get_production_rule_registry()` |
| `backend/core/rules/evidence.py` | `EvidenceBuilder`, formatters, validator | Primary (adapters serialize from it) |
| `backend/core/rules/provenance.py` | `ProvenanceRegistry`, `ClassicalSource` | Primary |
| `backend/core/rules/conditions.py` | Condition primitives | Primary |
| `backend/core/rules/activation.py`, `cancellation.py`, `mitigation.py` | Eval plug-ins | Primary (catalogue-wired) |
| `backend/core/rules/validators.py` | Rule/catalogue validation | Primary (registry integrity) |
| `backend/core/rules/enums.py` | Status vocabularies | Primary (unchanged) |
| `backend/core/rules/dynamic/*` (6A–6E) | DSL, resolver, engine, registry, lifecycle, RuleLab service, evidence records | Production-reachable via bridge, ACTIVE-only |
| `backend/core/rules/parashari/*` | 77-rule Yoga catalogue + evaluators | Primary (unchanged) |
| `backend/core/rules/doshas/*` | 6-rule Dosha catalogue + evaluators | Primary (unchanged) |
| `backend/core/research/*` | Research pipeline + 12-gate promotion firewall | Untouched, gates intact |
| `backend/canonical_yoga.py` | Yoga adapter (RuleResult→legacy shape) | Primary (unchanged) |
| `backend/canonical_dosha.py` | Dosha adapter | Primary (unchanged) |
| `backend/canonical_jaimini.py` | Jaimini adapter (own facts pipeline) | Primary (unchanged) |
| `backend/canonical_strength.py` | Strength projector | Primary (unchanged) |
| `backend/canonical_rules.py` | **NEW: production rules bridge** | **NEW primary entrypoint** |
| `backend/canonical_response.py` | `/compute` builder + enrichment | + additive `rules` block |
| `backend/routes/astro.py` | `/compute`, `/match` | + `"rules"` contract field |
| `backend/routes/ai_routes.py` | `/ai/analyze`, `/ai/expert_report` | + `"rules"` expert passthrough |
| `backend/routes/dynamic.py` | `/dynamic/*` (state/panchanga/transit) | Untouched |
| `backend/routes/research.py` | Read-only research/gates API | Untouched |
| `backend/ai_engine.py` | Gemini wrapper (interpret-only) | Untouched |

## 3. Capability matrix

| Capability | Exists | Tested | Production primary | Current consumers |
|------------|--------|--------|---------------------|-------------------|
| RuleContext | Yes | Yes (5A, #8) | Yes | bridge, 3 adapters |
| RuleEvaluator | Yes | Yes (5A, #8) | Yes | parashari/dosha catalogues |
| RuleResult | Yes | Yes (#8) | Yes | yoga/dosha adapters, bridge serializer |
| Rule catalogue | Yes (77+6) | Yes | Yes (via bridge registry view) | `/compute` |
| Rule applicability | Yes (enabled/status/declared deps) | Yes (#8 §5/§13) | Yes | bridge ACTIVE-only + engine declared-dep enforcement |
| Dependency resolution | Yes (dynamic resolver + registry cycle check) | Yes (6A–6E, #8 §6) | Yes | bridge |
| EvidenceBuilder | Yes | Yes | Yes | adapters project its evidence |
| ProvenanceRegistry | Yes | Yes | Yes | adapters project its records |
| Conflict handling | Yes (report-only) | Yes | Yes | `evaluate_many`, bridge `conflicts` |
| Cancellation | Yes | Yes | Yes | yoga/dosha evaluators |
| Mitigation | Yes | Yes | Yes | yoga/dosha evaluators |
| Rule versioning | Yes (semver, multi-version store) | Yes | Yes (preserved, never invented) | adapters + bridge coverage |
| Tradition metadata | Yes | Yes | Yes | registry filters, bridge |
| Profile filtering | Partial (tradition/category/status/provenance filters; no separate "profile" object) | Yes | Yes where supported | catalogue filters |
| Research firewall | Yes | Yes (Ph9, #8 §14) | Yes (intact) | promotion module |
| Developer Rule Lab | Yes (`RuleLabService`) | Yes (6C–6E) | Boundary intact (no direct prod writes) | lab service only |
| Production rule registry | **Gap → bridged** | Yes (#8) | **Yes (new view, existing class)** | `rules` block |

No test-only component was assumed production-ready: the dynamic engine's
ACTIVE-only gate was verified (§13) before wiring.

## 4. Canonicality criteria

Checklist applied to the 83 production-canonical rules (77 Yoga + 6 Dosha):

- [x] Belong to canonical architecture (5A engine + catalogues)
- [x] Stable rule IDs (`PARASHARI.YOGA.*`, `DOSHA.*`)
- [x] Defined applicability (formation conditions + enabled status)
- [x] Consume canonical facts via `RuleContext`
- [x] Deterministic evaluation (no clock/randomness; verified §31)
- [x] Return canonical `RuleResult` / `DoshaResult`
- [x] Defined status semantics (existing vocabularies, unchanged)
- [x] Evidence generated from actual facts (source allow-list verified §9)
- [x] Provenance defined where available (never fabricated, §10)
- [x] Tradition/profile explicit (PARASHARI_CLASSICAL / JAIMINI / CUSTOM)
- [x] No legacy calculation imports in engine path
- [x] Not research-only / not experimental (ACTIVE-gated)
- [x] Not dependent on frontend state

Dynamic-lab fixtures are CUSTOM/USER_SUPPLIED by design and stay OUT of the
production registry (ACTIVE-only gate returns 0 evaluations). Reported as the
standing gap, not silently promoted (§34 in report terms → see §34 Tests).

## 5. Rule registry

- Production previously had **no registry**: `astro.py`/`canonical_response.py`
  called `evaluate_all_parashari` / `evaluate_all_doshas` directly; the 5A
  global registry (`get_registry`) and `DynamicRuleRegistry` were test-only.
- `get_production_rule_registry()` populates ONE `RuleRegistry` via the
  existing `register_parashari_rules` / `register_dosha_rules` functions
  (83 rules). No duplicate registry class created.
- Verified: rule-ID resolution, latest-version semantics, unknown-ID → None,
  enabled/status flags, tradition filter, catalogue lookup. Dynamic side uses
  the existing `DynamicRuleRegistry` + `catalogue.list_rules` (ACTIVE-only).

## 6. RuleContext

`build_production_rule_context` passes `ChartFacts` / `StrengthReport` /
varga facts / dynamic state straight into `RuleContext`. Verified identity
(`ctx.chart_facts is CF`), Moon-sign accessor correctness, no frontend-shaped
inputs, no legacy-output consumption. Dynamic side uses existing
`dynamic.context.build_context` with the same canonical sources.

## 7. Applicability

- Engine enforces declared dependencies: stripped declaration → INVALID with
  diagnostics (not FALSE).
- Withheld fact layers (e.g. varga absent) → UNKNOWN with unresolved-facts
  explanation (never coerced to FALSE).
- Production bridge evaluates only `lifecycle.status == ACTIVE` rules with
  optional tradition filter. No blind evaluation.
- Existing status vocabulary untouched (FORMED/NOT_FORMED/UNKNOWN/INVALID,
  FORMED_CANCELLED/FORMED_MITIGATED).

## 8. Dependency resolution

- Existing `DynamicRuleRegistry.validate_graph()` cycle detection verified:
  acyclic fixture set clean; intentional A↔B pair reported as CYCLE.
- `rule_formed` cross-rule deps resolve through caller outcome maps.
- No repeated astronomy: resolver performs field reads + containment over
  canonical timelines only. No legacy dependency leaks (engine imports are
  canonical `core.*` only).

## 9. RuleResult

Verified on golden chart: 77 `RuleResult`s, Gaja Kesari FORMED,
`effective_status()` semantics, evidence serialization
(`format_evidence_for_json`), `EvidenceValidator` clean, dedup intact.

## 10. EvidenceBuilder

- Evidence objects carry type/subject/value/expected/actual/source/
  significance/details; sources restricted to
  ChartFacts/StrengthReport/VargaFacts/DynamicState (golden Yoga evidence
  allow-list verified — no fabrication).
- Immutable/deterministic (frozen models; repeated runs byte-identical at the
  response level, §31). Survive serialization (JSON-native projection).
- Contain human-readable `significance` per item → AI-trustable without
  recalculation (AI receives, never evaluates).

## 11. ProvenanceRegistry

Records: rule_id, source_type, source_name, source_reference,
tradition, method, chapter/verse, verification_status, verified_by/at,
implementation_version, notes. Classical entries (e.g. Gaja Kesari →
BPHS Ch. 36 Vs. 1-2, VERIFIED) preserved verbatim. UNVERIFIED stays
UNVERIFIED (upgrade requires locator+quotation; conflict sources preserved as
CONTESTED). No citations invented.

## 12. Production rule path

```
production facts → build_production_rule_context → catalogue evaluator
  → RuleResult → adapter projection (evidence/provenance retained)
  → thin response projection (_source: canonical) → /compute / AI / expert
dynamic: canonical facts → build_production_dynamic_context
  → evaluate_production_dynamic_rules (ACTIVE-only, REPORT-ONLY)
  → rules.dynamic block → /compute / expert context
```

## 13. Yoga integration

Engine untouched. Production path verified canonical-primary:
`RuleContext` → `create_parashari_evaluator` → `evaluate_all_parashari` →
`_rule_result_to_legacy_yoga` (evidence + provenance + `_source: canonical`).
77/77 canonical on golden chart; Category-E (Garuda, Kalpadruma, Mahabhagya,
Matsya, Mridanga) have no canonical entries — NOT implemented.

## 14. Dosha integration

Formulas untouched. Verified: 6/6 evaluated, Mangal 3-reference block
(Lagna/Moon/Venus with house/severity/mitigation/rule_id),
advanced-doshas + full-list projections all `_source: canonical` with
evidence + provenance. No calculated-but-dropped results.

## 15. Jaimini integration

Calculations untouched. Canonical engine already emitted evidence +
provenance; adapter projection verified reaching production
(`evidence`, `provenance`, per-yoga `evidence`, explicit tradition).
Jaimini intentionally uses its own facts pipeline (not generic RuleContext)
— accepted per-domain architecture, not flattened (§17).

## 16. Strength integration

Formulas untouched. Shadbala/Dignity/Bhava/Vimsopaka/Avastha/Functional/
CUSTOM Composite preserved exactly. Strength components NOT converted to
RuleResults (architecture does not do so). Verified projector outputs intact.

## 17. Legacy caller audit

| Caller | Classification |
|--------|----------------|
| `canonical_response.evaluate_canonical_yogas` | CANONICAL PRIMARY |
| `canonical_response.evaluate_canonical_doshas` | CANONICAL PRIMARY |
| `canonical_response.evaluate_canonical_jaimini` | CANONICAL PRIMARY |
| `canonical_strength` projectors | CANONICAL PRIMARY |
| `yoga_evaluator.evaluate_all_yogas` (gap-fill, `_source: legacy_fallback`, covered IDs suppressed) | LEGACY FALLBACK |
| `doshas_advanced` / `jaimini.compute_jaimini_system` (exception rollback only) | LEGACY FALLBACK |
| `ashtakavarga` / `maitri` / `panchanga_advanced` (no canonical equivalent) | LEGACY PRIMARY (by Migration #7 acceptance) |
| `routes/dynamic.compute_dynamic` → legacy `compute_chart` | LEGACY DEV TOOL (untouched, out of `/compute` path) |
| Legacy modules on disk | Retained, none deleted |

Canonical-first ordering asserted in test (`evaluate_canonical_yogas` precedes
`legacy_unique` merge). Legacy never overwrites canonical.

## 18. Response adapter

`backend/canonical_rules.py` + existing per-domain adapters: field mapping,
serialization, source tagging only — zero astrology formulas (source scan
asserts no `eval(`/`exec(`/`__import__`/`subprocess`/`os.system`).

## 19. /compute verification

Live `POST /compute` (TestClient, golden payload): 200; 77 canonical yogas;
mangal/jaimini/rules blocks `_source: canonical`; `rules.registry`
parashari=77/dosha=6/registered=83; `rules.dynamic` ACTIVE_ONLY with 0
evaluations (no ACTIVE dynamic rules — correct); Category-E absent from
canonical; all golden keys intact; two consecutive responses byte-identical.

## 20. AI verification

`summarize_context` preserves planets/yogas incl. per-yoga evidence;
`build_expert_context` now additionally passes `doshas`, strength blocks,
`jaimini`, and `rules`. AI architecture unchanged (interpret-only; no rule
evaluation in AI layer). Live LLM call not exercised (no API key in
environment) — verification covers context preservation/serialization, which
is this migration's scope.

## 21. Frontend verification

No redesign, no frontend astrology logic. Contract fields asserted
(yoga id/name/status; mangal has_dosha/verdict/details). `rules` is additive
(unknown keys ignored by UI). Phase 11 suite: 242/242 pass.

## 22. Evidence regression

Golden Yoga evidence counts > 0 for all 77 canonical entries post-migration;
Gaja Kesari evidence non-empty with fact sources; Dosha/Jaimini evidence
blocks present. Nothing disappeared through the adapter change (only additive
`rules` key added).

## 23. Provenance regression

Gaja Kesari provenance `BPHS Ch. 36, Vs. 1-2` VERIFIED retained end-to-end
(registry → adapter → `/compute`). Dosha/Jaimini provenance blocks present.
No missing provenance fabricated (fallback records stay UNVERIFIED-labelled).

## 24. Research firewall

`research://` → experiment → 12-gate promotion → `production://` intact.
EXPERIMENTAL promotion attempt → `promoted: False`. Research routes remain
read-only. Dynamic bridge performs no promotion and exposes no promotion API.

## 25. Developer Rule Lab

`RuleLabService` lifecycle verified: DRAFT cannot jump to ACTIVE
(`is_valid_transition("DRAFT","ACTIVE") is False`); activation requires
REVIEW_PENDING + APPROVED review + tests + provenance + security scan.
Non-ACTIVE registry content evaluates to 0 under the production function.
No `eval`/`exec`/imports/shell in DSL (pattern scan; evaluator reads
data-only trees).

## 26. Promotion gate

Existing gates used, none bypassed, no parallel approval system created.
Gap documented (not built): no automated pipeline moves a RuleLab ACTIVE rule
into the production dynamic registry — that step remains an explicit operator
action, which is the correct conservative posture.

## 27. Rule version/tradition/profile handling

Rule versions preserved and addressable (`registry.get(id, version)`,
`list_versions`); production results traceable to rule_id + version +
tradition + method. No versions invented (coverage lists carry IDs only).
Tradition filters verified; profile filtering exists as
tradition/category/status/provenance filters (no separate profile object —
documented as-is, not extended).

## 28. Conflict handling

`evaluate_many` reports same-derived-fact FORMED/NOT_FORMED splits as
`REPORTED_ONLY` conflicts; UNKNOWN pairs excluded. No silent merges, no
precedence invention, no winner selection. Cancellation/mitigation semantics
preserved from canonical evaluators.

## 29. Security

- [x] no eval / exec / arbitrary imports in bridge + adapter
- [x] no user-controlled rule code (DSL data-only + suspicious-pattern gate)
- [x] no frontend-controlled source (facts-only contexts)
- [x] research firewall intact; promotion gate intact
- [x] canonical cannot be overridden by legacy (ordering asserted)
- [x] rule IDs cannot execute code (ID strings scan clean)

## 30. Determinism

Repeated `/compute` identical (wall-clock `evaluated_at` is model-internal
and not serialized into responses). Yoga/Dosha/dynamic evaluations
deterministic; dynamic `EvidenceBundle` fingerprints stable (sha256 over
sorted canonical dict).

## 31. Performance

Golden-chart timings: registry build cached ~0.000 s; full Yoga eval ~0.017 s;
`/compute` ~11.2 s (ephemeris-dominated, unchanged profile). Bridge adds one
registry build (cached) + zero dynamic evaluations (empty ACTIVE set) —
no N× execution. Phase 12 perf suite: 310/310 pass.

## 32. Tests

New: `backend/test_rules_evidence_production_8.py` — **105/105 pass**,
covering capability matrix, RuleContext, registry, applicability,
dependencies, RuleResult, EvidenceBuilder, ProvenanceRegistry, source tagging,
IDs/versions, tradition, Yoga/Dosha/Jaimini integration, legacy audit,
canonical precedence, firewall, Lab boundary, promotion gate, `/compute`,
AI serialization, frontend compat, golden regression, determinism,
performance, security, Ashtakavarga intactness.

## 33. Full regression results

| Suite | Result |
|-------|--------|
| Migration #8 (new) | 105/105 |
| Phase 5A rule engine | 185/185 |
| Phase 5B parashari | 695/695 |
| Phase 5C doshas | pass |
| Phase 6A / 6B / 6C / 6D / 6E dynamic | 48+51+115+86+105 pass |
| Migration #3B (Cat C) | 589/589 |
| Migration #3C (Cat D) | 290/290 |
| Migration #4 jaimini prod | 91/91 |
| Migration #5 strength prod | 149/149 |
| Migration #6 dosha prod | 87/87 |
| Migration #7 ashtakavarga prod | 39/39 |
| Golden chart canonical | 39/39 |
| Phase 10 regression | 1085/1085 |
| Phase 9 research | 281/281 |
| Phase 12 production | 310/310 |
| Phase 8 prediction | 211/211 |
| Phase 7 agents | 176/176 |
| Phase 11 frontend | 242/242 |
| Phase 4B strength | 87/87 |
| Phase 5D/5E/5F/5G/5GH jaimini | 143/62/57/38/63 pass |
| Phase 3 dasha/panchanga/transit/dynamic/varga | 81283/423/788/27/19692 pass |
| AI transit + prediction transit hotfix | 31/31, 15/15 |
| Phase 13 shadbala file (pre-existing; run only) | 40/40 |
| `test_timing_engine.py` | NOT RUN — pre-existing env gap (`pytest` not installed; fails at `import pytest`, unrelated to #8) |

No test files weakened. Simulated-failure tracebacks in jaimini/dosha prod
suites are their own expected fallback-path logs; verdicts pass.

## 34. Remaining limitations

1. Production dynamic registry starts EMPTY (no ACTIVE dynamic rule has passed
   gates) — `rules.dynamic.evaluated_count` is 0 by correct design, not by
   defect. First ACTIVE rule will flow automatically.
2. No automated RuleLab→production-registry promotion pipeline (explicit
   operator step; intentional).
3. Jaimini does not use generic `RuleContext` (own facts pipeline, by design).
4. No separate "profile" object beyond tradition/category/status/provenance
   filters (documented, not extended).
5. Live LLM output not exercised (no API key); AI scope limited to context
   preservation.
6. `test_timing_engine.py` unrunnable here (missing `pytest`).

## 35. Files changed

**Migration #8 changes (vs pre-existing working tree):**

- NEW `backend/canonical_rules.py` — thin production bridge (no astrology).
- NEW `backend/test_rules_evidence_production_8.py` — 105 checks.
- NEW `MIGRATION_8_RULES_EVIDENCE_PROVENANCE_FINAL_REPORT.md` (this file).
- `backend/canonical_response.py` (untracked pre-existing file): + `rules: {}`
  seed key; + additive bridge call in `enrich_response_with_legacy_modules`
  (try/except, never breaks `/compute`).
- `backend/routes/astro.py` (pre-existing mods retained): + `"rules"` in
  `COMPUTE_RESPONSE_FIELDS` only.
- `backend/routes/ai_routes.py` (pre-existing mods retained): + `"rules"` in
  `build_expert_context` passthrough only.

All other working-tree modifications (astro canonical migration, transit
wiring, frontend files, parashari catalogues/snapshots, etc.) are
**pre-existing and untouched**. Ashtakavarga files unmodified. No deletions.
No commits. No pushes.

## 36. Final PASS/BLOCKED verdict

**PASS** — all §40 criteria met:

- [x] Canonical Rule architecture fully audited
- [x] RuleContext production path verified
- [x] Rule registry verified (bridged, not duplicated)
- [x] Applicability verified (UNKNOWN/INVALID, never coerced)
- [x] Dependency resolution verified (cycle detection)
- [x] RuleResult verified
- [x] Evidence production path verified
- [x] Provenance production path verified
- [x] Canonical Yoga/Dosha/Jaimini/Strength paths preserved
- [x] Legacy callers audited; canonical precedence verified
- [x] Research firewall intact; Lab boundary intact; promotion gate intact
- [x] No dynamic execution
- [x] `/compute` verified; AI verified (context scope); frontend compatible
- [x] Evidence/provenance regression verified
- [x] Determinism, performance, security verified
- [x] Ashtakavarga untouched; Category-E untouched; no new astrology rules
- [x] Full regression green (one pre-existing env gap noted)
- [x] No unrelated changes; no commit; no push

**NO COMMIT / NO PUSH — awaiting review.**
