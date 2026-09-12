# ASTROLIFE MIGRATION #4 — CANONICAL JAIMINI PRODUCTION WIRING
## FINAL REPORT

**Date:** 2026-09-11
**Scope:** Jaimini production wiring only. No Phase 13. No Migration #5.
No frontend redesign. No unrelated engine changes.
**Verdict:** PASS
**No Commit / No Push — awaiting review.**

---

## 1. Executive summary

The existing canonical Jaimini engine (`backend/core/jaimini/`) was audited,
found production-ready, and wired as the authoritative production source via a
new thin adapter (`backend/canonical_jaimini.py`). `/compute` now returns
canonical Jaimini facts; the legacy module (`backend/jaimini.py`) is retained
but has no primary production caller (rollback-only). Field-level crosscheck:
**36/36 MATCH** (golden + 12-ascendant sweep) — zero discrepancies. All golden
anchors preserved exactly; no canonical formula modified. All regression
suites pass.

## 2. Initial canonical Jaimini capability inventory

| Feature | Canonical exists? | Source |
|---------|-------------------|--------|
| Chara Karakas | YES | `core/jaimini/karakas.py` (7- and 8-schemes; default SEVEN_KARAKA) |
| AK | YES | Jupiter 21.84° Virgo (golden) |
| AmK | YES | Moon 17.86° Sagittarius |
| BK | YES | Mars 16.59° Aries |
| MK | YES | Mercury 14.84° Cancer |
| PK | YES | Saturn 10.06° Cancer |
| GK | YES | Venus 5.64° Virgo |
| DK | YES | Sun 0.04° Leo |
| Karakamsha | YES | `core/jaimini/karakamsha.py` (Cancer golden) |
| Arudha Lagna (AL) | YES | `core/jaimini/arudha.py` + `padas.py` (Capricorn golden) |
| Upapada (UL) | YES | `core/jaimini/upapada.py` (Capricorn golden) |
| Jaimini Drishti | YES | `core/jaimini/rashi_drishti.py` (sign-based, 12×3 structure) |
| Jaimini Yogas | YES | `core/jaimini/rules/` (12 rules, deterministic pipeline) |
| Chara Dasha | YES | `core/jaimini/dasha/` (default profile = golden Profile A) |
| Chara Dasha timing | YES | Full period timelines with UTC bounds + antardashas |
| Current-period API | NO dedicated API | Gap reported (§13): adapter performs a labeled deterministic interval lookup over canonical UTC bounds (projection, not astrology) |
| Jaimini evidence | YES | Per-module evidence + evidence graph (`evidence.py`) |
| Jaimini provenance | YES | `JaiminiProvenance` (JAIMINI / CLASSICAL_ARUDHA_STANDARD / UNVERIFIED) |

Nothing was invented: every wired field comes from the pre-existing engine.
Tie-breaking (canonical Graha precedence within float tolerance) and Rahu
conventions already existed and were tested, not created.

## 3. Files changed

| File | Change |
|------|--------|
| `backend/canonical_jaimini.py` | NEW: thin adapter (facts→response projection, JSON serialization, labeled current-period lookup, coverage map). No astrology, no legacy imports |
| `backend/canonical_response.py` | Jaimini block → canonical-primary with legacy rollback; docstring/comments updated (3 small edits) |
| `backend/test_jaimini_production_4.py` | NEW: 91-check wiring suite |
| (3B/3C artifacts) | Untouched by this migration |

Pre-existing working-tree modifications (frontend files, `app.py`,
`structural.py` sun-helpers, `ai_routes.py`, etc.) predate this migration and
were left untouched. A test-side-effect reorder of
`golden_dosha_snapshot.json` (planet-list ordering only, from running the 5C
suite during verification) was reverted; dosha code is untouched.

## 4. Canonical pipeline architecture

`generate_chart_facts → generate_jaimini_facts (karakas + rashi_drishti +
arudha padas + upapada + karakamsha + evidence + provenance) →
evaluate_jaimini_yogas (12 rules) → calculate_jaimini_dasha (default profile)
→ thin adapter → /compute → frontend / AI`. Routes never calculate; frontend
never calculates; AI never calculates.

## 5. Response adapter architecture

`evaluate_canonical_jaimini(chart_facts, varga_facts, evaluation_datetime)`
returns: legacy-compatible `chara_karakas` (`{"Atmakaraka (AK)": planet…}` in
rank order) and `arudha_padas` (`{"1": sign…}`), plus additive canonical
richness (`karakamsha`, `arudha_lagna`, `upapada`, `rashi_drishti`, `yogas`
with per-rule evidence, `chara_dasha` with full periods + labeled `current`,
`evidence`, `provenance`), `_source/_engine = "canonical"`. Engine objects
serialized to JSON-native values (fixes a latent non-serializable evidence
type that would have broken API serialization). On engine failure the caller
falls back to legacy tagged `legacy_fallback`.

## 6. Chara Karaka verification

Golden ordering exact: Jupiter→AK, Moon→AmK, Mars→BK, Mercury→MK,
Saturn→PK, Venus→GK, Sun→DK; degrees match anchors within 0.01°; descending
order; sidereal intra-sign degrees; Rahu/Ketu excluded under the 7-method;
evidence ≥7 lines. Tie policy tested (equal-degree pair resolves by canonical
precedence, deterministically). No legacy override anywhere.

## 7. Karakamsha verification

Cancer, derived by the canonical engine (AK Jupiter, D1 Virgo → D9 Cancer);
adapter projects, never computes. Golden snapshot value preserved.

## 8. Arudha Lagna verification

Capricorn (A1; Venus-ruled Taurus → Virgo lord → Capricorn projection, no
exception), canonical source, deterministic, Whole Sign. Legacy agrees
(12/12 padas MATCH on golden and sweep).

## 9. Upapada verification

Capricorn (12th-house Aries, Mars in Aries), canonical `UpapadaDetails` with
evidence, projected compatibly.

## 10. Jaimini Drishti verification

Canonical Rashi Drishti wired as structured `sign_aspects` (12 signs × 3, no
self-aspect) plus `planet_aspects`. It is sign-based and distinct from
Parashari Graha Drishti and Western aspects (asserted in tests). Preserved in
response and AI context.

## 11. Jaimini Yoga verification

All 12 canonical rules wired (`JAI.KARAKA.*`, `JAI.DRISHTI.*`,
`JAI.ARUDHA.*`, `JAI.KARAKAMSHA.*`, `JAI.SWAMSA.*`); golden formed set pinned:
`AL_LORD_KENDRA_TRINE`, `AK_AMK_MUTUAL`, `KARAKAMSHA_BENEFIC_OCCUPANCY`
(3 formed). Parashari/Jaimini families kept separate (distinct IDs,
traditions, pipelines). No gaps filled with invented formulas.

## 12. Chara Dasha verification

Default profile wired: Taurus / REVERSE / 92.0y (golden Profile A), 12
mahadashas × 12 antardashas with UTC bounds, durations summing to 92y,
starting-sign evidence, clean validation. Profiles B (Taurus/FORWARD/96) and C
(Taurus/REVERSE/92) verified golden-anchored and available via profile
selection (production uses the canonical default). Formulas untouched.

## 13. Evaluation datetime behavior

Natal facts are birth-derived (no wall-clock). `chara_dasha.current` is a
labeled interval lookup at the supplied evaluation datetime (production passes
birth time, consistent with the birth-chart response: Taurus/Taurus at birth).
The canonical engine has no current-period API — reported gap, bridged only by
the labeled deterministic projection. Birth facts vs evaluation timing are
never conflated.

## 14. Evidence

Preserved everywhere supported: karaka derivation lines, pada step
derivations, karakamsha derivation, drishti derivation, per-yoga formation
evidence, dasha starting-sign/duration evidence + validation evidence nodes.
No generic success-message evidence.

## 15. Provenance

`JaiminiProvenance` (JAIMINI, CLASSICAL_ARUDHA_STANDARD, UNVERIFIED reference,
engine version) preserved in response and AI context. Legacy rollback fields
receive no canonical provenance (tagged `legacy_fallback`).

## 16. Legacy-vs-canonical field comparison

| Legacy field | Canonical | Result |
|--------------|-----------|--------|
| `chara_karakas` (7) | Same 7, same rank order | MATCH |
| `arudha_padas` (12) | Same 12 signs | MATCH |
| (nothing else in legacy) | karakamsha/AL/UL/drishti/yogas/dasha/evidence/provenance | Canonical-only richness (no legacy counterpart) |

Sweep: 36/36 MATCH (12 ascendants × 3 configurations). Legacy-only fields:
none. Canonical is primary for every overlapping field.

## 17. Every discrepancy

**None.** Zero MATCH failures across golden + sweep. (Independent note: legacy
`degree_in_sign_manual` sourcing differs by input plumbing, not by karaka
rule — both rank sidereal intra-sign degrees with identical precedence.)

## 18. /compute runtime trace

`generate_chart_facts → build_canonical_compute_response →
enrich_response_with_legacy_modules → evaluate_canonical_jaimini (facts +
12 yogas + dasha) → response["jaimini"] (_source canonical)`. Legacy not
invoked (proven by failure-injection test: legacy outage leaves production
intact; canonical outage yields tagged legacy rollback). Yoga block unaffected
(82 entries).

## 19. Authenticated behavior

`jaimini._source = "canonical"`, golden karakas/padas/dasha, 12 yogas (3
formed), full evidence/provenance. Verified live.

## 20. Unauthenticated behavior

Identical canonical block (Jaimini was never auth-gated). Verified live.

## 21. AI runtime verification

Expert-report context carries the full canonical block (`_source`,
provenance, AK/AL values verified live); system instruction unchanged (no
recalculation). Base `/analyze` summary omits jaimini (pre-existing behavior,
unchanged). AI-bound payload is JSON-serializable.

## 22. Frontend verification

**Frontend unchanged — Jaimini response contract preserved.**
`JaiminiCard` consumes `chara_karakas`/`arudha_padas` maps exactly as before
(same keys, same value types); extra canonical keys are ignored by the UI.
No frontend change needed. Phase 11 passes.

## 23. Regression tests

New suite 91/91. Existing: 5D (143), 5E (62), 5F (57), 5G (38), 5GH (63),
timing (57 pytest), 5A, 5B (695), 3B (589), 3C (290), golden (39), 4B, 5C,
6A–6E, 7 (176), 8 (211), 9 (281), 10 (1085), 11 (242), 12 (310). No test
weakened or deleted.

## 24. Determinism

Byte-identical reruns at engine, adapter, and enrich levels (JSON-compared).
No randomness, wall-clock (natal), API, or mutable-global dependence; legacy
fallback ordering cannot affect canonical results (fallback only on exception).

## 25. Performance

Adapter mean well under the 5 s gate (sub-second in practice); Phase 12
`perf.jaimini` gate still passes. Facts/StrengthReport/vargas reused; no
repeated astronomy.

## 26. Legacy caller audit

| Caller | Purpose | Status |
|--------|---------|--------|
| `canonical_response.py:740` (`compute_jaimini_system`) | Rollback fallback only (exception path) | Retained deliberately |
| `backend/verify_jaimini_ashtakavarga.py` | Dev verification script | Not production |
| `test_frontend_phase11.py:244` | Test-only direct call | Not production |

**Legacy Jaimini has no primary production caller; retained for compatibility
and future cleanup.** `backend/jaimini.py` NOT deleted, NOT modified.

## 27. Remaining limitations/gaps

1. No canonical current-period API (bridged by labeled lookup, §13).
2. Production wires the default dasha profile (A); B/C available but not
   profile-switchable via API.
3. Base `/analyze` AI summary omits jaimini (expert report includes it) —
   pre-existing, unchanged.
4. 8-karaka scheme supported by engine but production uses the golden
   7-scheme default (documented, not a gap in the wired contract).

## 28. Final PASS/BLOCKED verdict

**PASS.** All 33 pass criteria met: canonical Jaimini is production primary
with formulas unchanged; all golden karakas/karakamsha/AL/UL/dasha profiles
exact; drishti/yogas/dasha wired where canonically available; adapter thin
with zero astrology; legacy cannot override (failure-injected proof);
field comparison 36/36 with every (zero) discrepancy accounted for; evidence
and provenance preserved; AI receives canonical data without recalculating;
frontend contract preserved with zero frontend changes; runtime verified
(auth + unauth + AI-bound); determinism and performance verified; full
regression battery green; Category E and unrelated systems untouched; no
commit; no push. No BLOCKED condition triggered.

**NO COMMIT / NO PUSH — awaiting review.**
