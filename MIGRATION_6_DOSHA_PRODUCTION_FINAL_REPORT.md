# ASTROLIFE MIGRATION #6 — CANONICAL DOSHA PRODUCTION WIRING + CATEGORY-E AUDIT
## FINAL REPORT

**Date:** 2026-09-11
**Scope:** Dosha production wiring + Category-E audit only. No Phase 13, no new
roadmap phase. No frontend redesign. No unrelated engine changes.
**Verdict:** PASS
**No Commit / No Push — awaiting review.**

---

## 1. Executive summary

The canonical Dosha engine (6 rules: 3 Manglik references, Kemadruma,
sign-based Kala Sarpa, modern-common Pitru — with formation, severity,
cancellation, mitigation, evidence, provenance) existed but reached production
nowhere: `/compute` returned only legacy `advanced_doshas`, and the frontend's
`MangalDoshaCard` was starved (no `mangal_dosha` key ever produced). A thin
adapter (`backend/canonical_dosha.py`) now wires all 6 canonical doshas as
production primary with legacy-compatible projections plus `_source` tags;
legacy remains rollback-only. Canonical-vs-legacy crosscheck: all MATCH.
Golden dosha states preserved exactly. The five Category-E Yogas were
individually audited and **none implemented** (2 NEEDS RESEARCH, 3 UNSAFE/
AMBIGUOUS — §21/§22). Full regression battery green.

## 2. Capability inventory

| Dosha | Canonical exists? | Tested? | Production primary? | Legacy implementation? |
|-------|-------------------|---------|---------------------|------------------------|
| Manglik Lagna ref | YES | YES (5C) | YES (new: `mangal_dosha`) | none (card was starved) |
| Manglik Moon ref | YES | YES (5C) | YES (new) | none |
| Manglik Venus ref | YES | YES (5C) | YES (new) | none |
| Kemadruma (dosha) | YES | YES (5C) | YES (new: `doshas` list) | none |
| Kala Sarpa (sign-based) | YES | YES (5C) | YES (new projection) | `doshas_advanced` (rollback) |
| Pitru (modern common) | YES | YES (5C) | YES (new projection) | `doshas_advanced` (rollback) |

No dosha invented; catalogue of 6 preserved.

## 3. Dosha catalogue

`DOSHA.MANGLIK.LAGNA_CLASSICAL`, `DOSHA.MANGLIK.MOON_REFERENCE`,
`DOSHA.MANGLIK.VENUS_REFERENCE` (Mars in 1/2/4/7/8/12 whole-sign from
reference; most-common-house-set convention recorded),
`DOSHA.KEMADRUMA.CLASSICAL`, `DOSHA.KALA_SARPA.SIGN_BASED` (explicitly
TRADITION-DEPENDENT per its own provenance: not in BPHS/Phaladeepika/Saravali),
`DOSHA.PITRU.MODERN_COMMON`. Severities NONE/LOW/MODERATE/HIGH/UNKNOWN;
activation NOT_EVALUATED by design; Manglik cancellations partial-only by
design (disputed rules never granted FULL — see §6).

## 4. Canonical architecture

Unchanged engine: `RuleContext → RuleEvaluator → DoshaResult` (formation →
severity dispatch → cancellation → mitigation → evidence), plus
`DoshaEvaluationSet`. This migration adds only the projection layer.

## 5. Production wiring

`enrich_response_with_legacy_modules` now evaluates canonical doshas (reusing
its existing chart/strength/varga/dynamic facts) and sets `mangal_dosha`,
`advanced_doshas` (canonical projection), and additive `doshas` (full list of
6). The stale duplicate legacy `advanced_doshas` block was removed so legacy
can never overwrite canonical; legacy survives solely as the tagged
`legacy_fallback` rollback. Base keys initialized; `COMPUTE_RESPONSE_FIELDS`
extended.

## 6. Mangal Dosha trace

Canonical evaluation → adapter → `/compute.mangal_dosha` → `MangalDoshaCard`
(`chartData.mangal_dosha`) → AI expert context. Golden: Lagna FORMED house 12
(LOW, mitigated PARTIAL), Moon NOT_FORMED (house 5), Venus FORMED house 8
(LOW) → `has_dosha: true`, verdict `"LOW"` (severity verbatim, never
remapped). Per-ref `is_cancelled` is FULL-only per `DoshaResult.is_cancelled`;
canonical Manglik rules are partial-only, so production never emits a false
`"Cancelled"` (branch unit-tested with stubs). Cancellation reasons surface
only from full-cancellation evidence. Classical rule untouched, including its
profile semantics.

## 7. Response adapter

`backend/canonical_dosha.py`: pure projection (serialization, field mapping,
source tagging, compatibility mapping). Zero engine imports, zero formulas,
no legacy imports, no research imports (token-scanned in tests). Statuses
passed through verbatim (FORMED/NOT_FORMED/ severities / cancellation /
mitigation / NOT_EVALUATED); verdict vocabulary is exactly
No-Dosha/Cancelled/severity-verbatim.

## 8. Authenticated behavior

`mangal_dosha` present with golden verdict LOW and `_source: canonical`;
`advanced_doshas` canonical; `doshas` list of 6; yogas (82) / jaimini /
strengths unaffected. Verified live.

## 9. Anonymous behavior

Identical dosha blocks (doshas were never auth-gated; policy unchanged).
Verified live.

## 10. AI integration

Expert-report context now includes `mangal_dosha` + `doshas` (+ pre-existing
`advanced_doshas`); live-verified values, statuses, evidence summaries, and
`_source: canonical` survive serialization. Instruction unchanged (interpret,
don't recalculate).

## 11. Frontend verification

Zero frontend changes. `MangalDoshaCard` receives its exact expected shape
(`has_dosha/verdict/details.{Lagna,Moon,Venus}/cancellations_found`) —
previously `null`-guarded, now populated. `AdvancedDoshasCard` keys
(`has_dosha/verdict/details[/reasons]`) preserved verbatim. No React
astrology (nothing added). Phase 11 green.

## 12. Evidence

All 6 golden doshas carry engine evidence (formation positions, dignity
inputs, cancellation/mitigation factors with typed details); adapter forwards
it verbatim plus per-block summaries. No generic messages.

## 13. Provenance

Canonical `DoshaProvenance` (BPHS classical-text, UNVERIFIED reference,
method, notes) forwarded per dosha and per Manglik reference. Legacy rollback
receives no canonical provenance (`legacy_fallback` tag only).

## 14. Legacy caller audit

| Caller | Purpose | Status |
|--------|---------|--------|
| `canonical_response.py` (dosha try/except) | `compute_advanced_doshas` rollback only | Retained deliberately |
| `verify_jaimini_ashtakavarga.py` | Dev script (jaimini import) | Not production |
| Phase 11 test direct call | Test-only | Not production |

`verify_mangal_dosha.py` targets the retired `compute_chart` path (dev
script, not production). `doshas_advanced.py` NOT deleted. Failure injection
proved: legacy outage leaves production intact; canonical outage yields tagged
legacy fallback with `mangal_dosha: {}` + `doshas: []` (honest empty, never
fabricated).

## 15. Canonical-vs-legacy comparison

Overlapping fields (kala_sarpa/pitru `has_dosha`): golden + 4-chart sweep
(8 comparisons incl. positive Kala Sarpa and positive Pitru cases) — **all
MATCH**. Manglik/Kemadruma have no production legacy counterpart (previously
unserved). Lexical verdicts preserved (`Active Kala Sarpa`, `Active Pitru
Dosha`, `No Dosha`).

## 16. Every discrepancy

None. Zero non-matches. (Noted asymmetry, not a discrepancy: legacy Pitru
lacks severity/cancellation concepts the canonical engine provides; legacy
consumers only ever read `has_dosha/verdict/details/reasons`, all preserved.)

## 17. Golden regression

All 6 golden states byte-stable (2 FORMED/LOW/PARTIAL-mitigated Manglik refs;
4 NOT_FORMED/NONE). 5C snapshot counts (6/2/0/2) consistent. No numerical
invention (doshas are categorical by canonical design).

## 18. Determinism

Byte-identical reruns at engine, adapter, and `/compute` block levels
(JSON-compared). No randomness, mutable globals, or wall-clock dependence in
the dosha path.

## 19. Performance

Canonical dosha evaluation mean **0.001 s**; adapter negligible; Phase 12
gates pass. Existing facts reused; no duplicate astronomy.

## 20. Security

No `eval`/`exec`/dynamic dispatch from user input in touched files
(token-scanned); rule selection fixed at catalogue build; research modules
never imported by adapter or response path (firewall intact); `_source` tags
server-set, never frontend-derived; legacy cannot overwrite canonical
(structural ordering + injection-tested).

## 21. Category-E Yoga audit

| Yoga | Classical definition available? | Existing legacy rule | Canonical prerequisites expressible? | Safe? |
|------|----------------------------------|----------------------|----------------------------------------|-------|
| Garuda | CONTESTED (ruleset description vs code disagree: exalted lord-of-Moon-navamsa vs Moon-in-exalted-navamsa; plus paksha clause) | `moon_navamsa_exalt` (checks the code reading only) | Partial (D9 + dignity exist; paksha via dynamic state) | NO — C |
| Kalpadruma | VARIANT (4-level dispositor/navamsa chain depths differ by source) | `kalpadruma_chain` (2-level simplification) | Partial (dispositors + D9 exist) | NO — B |
| Mahabhagya | CLEAR but BLOCKED (requires gender + day/night birth) | `mahabhagya_check` (special-condition, unhandled) | NO (gender unknowable; must not be inferred) | NO — C |
| Matsya | GARBLED ("Mix in 5th"; description vs code conflict on 4th/8th clause) | `matsya_pattern` (partial) | Partial | NO — C |
| Mridanga | VARIANT (which exalted planet / whose navamsa lord unsettled; legacy code checks something else entirely) | `mridanga_complex` (wrong vs description) | Partial | NO — B |

## 22. Category-E decisions

- Garuda: **C — UNSAFE/AMBIGUOUS** (intended condition unestablishable).
- Kalpadruma: **B — NEEDS RESEARCH** (chain depth must be settled by research).
- Mahabhagya: **C — UNSAFE/AMBIGUOUS** (gender dependency must not be invented).
- Matsya: **C — UNSAFE/AMBIGUOUS** (definition garbled in-repo).
- Mridanga: **B — NEEDS RESEARCH** (verse pinned first, then trivially implementable).
- Zero implemented. Coverage stays **77/82 = 93.9%** by decision, not by omission — accuracy over percentage. Research firewall verified intact (no experimental import in production path).

## 23. Research firewall verification

`research:// → experiment → promotion gate → production://` untouched; no
research module imported by adapter/response/tests-asserted; no
EXPERIMENTAL→ACTIVE shortcut exists for doshas or Category E.

## 24. Tests

New `backend/test_dosha_production_6.py`: **87/87** — inventory, golden
states, Mangal variants (formed houses, partial-cancellation design,
never-FULL invariant), Kala Sarpa/Pitru positives, adapter contract incl.
stub-tested verdict branches, crosscheck sweep, production auth/anon,
outage/rollback injection, determinism, JSON, AI/frontend contract,
hygiene, Category-E non-coverage guards, research-firewall guard, perf smoke.

## 25. Regression results

5C, 5A, golden (39), 4B, strength-5 (149), 5B (695), 3B (589), 3C (290),
Jaimini-4 (91), 5D (143), 5E (62), 5F (57), 5G (38), 5GH (63), timing (57),
6A–6E, 7 (176), 8 (211), 9 (281), 10 (1085), 11 (242), 12 (310) — all green,
no weakening.

## 26. Remaining limitations

1. Mangal verdicts are severity-verbatim ("LOW") by canonical design; the
   `"Cancelled"` branch exists but is unreachable while cancellations stay
   partial-only (documented, stub-tested).
2. Kala Sarpa carries TRADITION_DEPENDENT provenance by its own engine notes.
3. Pitru rule is explicitly modern-common (method name says so).
4. Rollback path yields empty Mangal/doshas rather than fabricated data.
5. Dosha activation stays NOT_EVALUATED (no prediction layer — by design).

## 27. Files changed

| File | Change |
|------|--------|
| `backend/canonical_dosha.py` | NEW: thin projection adapter |
| `backend/canonical_response.py` | Canonical dosha block + stale legacy block removed; base keys |
| `backend/routes/astro.py` | Response-field doc list (+2 keys) |
| `backend/routes/ai_routes.py` | Expert passthrough (+2 keys) |
| `backend/test_dosha_production_6.py` | NEW: 87-check suite |

Pre-existing tree dirt untouched; dosha-snapshot reorder side effects from
verification runs reverted; no engine, frontend, auth, or lifecycle changes.

## 28. Final PASS/BLOCKED verdict

**PASS.** All 26 pass criteria met: architecture audited with full matrix;
canonical primary everywhere available (Mangal now reaches production —
nothing calculated-and-dropped); legacy reduced to justified rollback;
statuses/cancellation/mitigation/evidence/provenance preserved verbatim with
correct `_source` tagging; auth/anon verified; AI receives canonical doshas;
frontend contract preserved with zero frontend changes; Category E audited
with B/C decisions and zero speculative implementations; firewall intact;
deterministic, performant, secure; full battery green; no unrelated changes;
no commit; no push. No BLOCKED condition triggered.

**NO COMMIT / NO PUSH — awaiting review.**
