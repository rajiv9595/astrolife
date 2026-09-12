# ASTROLIFE MIGRATION #3C — CATEGORY D ENGINE EXTENSION
## FINAL REPORT

**Date:** 2026-09-11
**Scope:** Category D only (15 Yogas). No Category E. No Migration #4. No Phase 13.
**Verdict:** PASS
**No Commit / No Push — awaiting review.**

---

## 1. Executive summary

All 15 Category D Yogas are implemented as canonical Rule Engine rules with
one new reusable primitive (seven-planet Nabha sign distribution) plus reuse
of existing lordship/house/aspect/strength primitives. Canonical coverage moves
**62/82 (75.6%) → 77/82 (93.9%)**; legacy fallback is exactly the 5 Category E
Yogas (6.1%). Live `/compute` verified: 82 entries authenticated
(77 canonical + 5 legacy_fallback), 77 canonical unauthenticated, deterministic,
no duplicates. All regression suites pass. No canonical astronomy or astrology
formula was modified; Category E is untouched.

## 2. Exact 15 rules implemented

`PARASHARI.YOGA.ASTRA`, `PARASHARI.YOGA.ASURA`, `PARASHARI.YOGA.BHERI`,
`PARASHARI.YOGA.BHRIGU_MANGALA`, `PARASHARI.YOGA.BRAHMA`, `PARASHARI.YOGA.DAMA`,
`PARASHARI.YOGA.GOLA`, `PARASHARI.YOGA.INDRA`, `PARASHARI.YOGA.KEDARA`,
`PARASHARI.YOGA.KURMA`, `PARASHARI.YOGA.PASHA`, `PARASHARI.YOGA.SARPA`,
`PARASHARI.YOGA.SHULA`, `PARASHARI.YOGA.VEENA`, `PARASHARI.YOGA.YUGA`
— exact §19 IDs, all unique, no collisions with the existing 62.

## 3. New primitive architecture

New module `backend/core/rules/parashari/category_d_yogas.py` (isolated
addition; no second engine; no edits to existing primitive files):

- `nabhasa_sign_distribution(ctx)` — reusable canonical representation:
  ordered map of the seven classical planets (Sun..Saturn) to sidereal D1
  signs from ChartFacts. Nodes never counted.
- `nabhasa_occupied_sign_count(ctx)` — distinct-sign count consumed by the
  seven Nabha rules.
- Canonical lord-strength (`_lord_strength_evidence`) imported from
  `classical_yogas` — single definition reused, not duplicated.
- Everything else reuses existing `RuleContext`/structural primitives
  (`house_from_moon/planet`, `is_kendra_from_planet`, natural benefic/malefic
  sets, Shadbala-backed strength). No longitude math in any rule.

## 4. Rule-by-rule semantics

| Yoga | Canonical condition |
|------|---------------------|
| Astra | Malefic in 6th AND L6 strong (conjunctive reading of ruleset description; legacy code dropped the malefic clause — documented defect) |
| Asura | Malefic in 8th AND L8 strong (same note as Astra) |
| Bheri | Houses 1, 2, 7, 12 each occupied by ≥1 classical planet (nodes excluded); legacy key unhandled (dead rule) |
| Bhrigu Mangala | Venus–Mars same whole-sign house (aspect does not qualify; tested) |
| Brahma | Jupiter, Venus, Mercury each in Kendra from the Lagna lord's house (three explicit predicates) |
| Dama / Gola / Kedara / Pasha / Shula / Veena / Yuga | Seven-planet signs occupy exactly 6/1/4/5/3/7/2 signs (legacy `nabha` keys unhandled — dead rules) |
| Indra | Mars 3rd from Moon AND Saturn 7th from Mars AND Venus 7th from Saturn (three explicit links) |
| Kurma | Benefic in EACH of 5, 6, 7 AND malefic in EACH of 1, 3, 11 (strict; nodes count as malefics per canonical set) |
| Sarpa | Malefics in ≥3 Kendras (canonical natural-malefic set incl. Rahu/Ketu — recorded convention) |

Variant notes and omitted readings are recorded in each rule's metadata notes.

## 5. Nabha counting implementation

Sign-based over `ctx.get_planet_sign` (sidereal D1); degrees ignored; houses
ignored; tropical never used; Rahu/Ketu excluded by construction
(`NABHASA_PLANETS = SEVEN_PLANETS`). One representation, seven consumers.
Tested for counts 1–7, node-in-extra-signs exclusion, and sign-vs-house
distinction.

## 6. Malefic/strength implementation

Malefic = canonical `NATURAL_MALEFICS` (Sun, Mars, Saturn, Rahu, Ketu) — no
"malefic = bad" shortcut; occupancy is positional, strength is the established
canonical lord-strength (dignity + Kendra/Trikona + Shadbala ≥ 1.0). No second
strength engine; Shadbala never recomputed. Astra/Asura tested with both
clauses isolated (malefic-absent and lord-weak negatives).

## 7. Multi-step relationship implementation

- Brahma: three per-planet Kendra-from-Lagna-lord predicates, each evidenced.
- Indra: three per-link offset predicates (3 from Moon; 7 from Mars; 7 from
  Saturn), each evidenced; link-break negatives tested individually.
No chain collapsed into generic conjunction.

## 8. Complex-pattern implementation

- Bheri: four per-house occupancy predicates over the seven planets.
- Kurma: six per-house predicates (3 benefic + 3 malefic), each evidenced;
  strict ALL-houses reading, no loose approximation.
- Sarpa: per-Kendra occupancy + threshold count evidence.

## 9. Evidence

All 15 emit fact-derived Evidence (planet/sign/house/lord/conjunction/dignity/
strength). Nabha evidence carries the full seven-planet sign map + occupied
count. Brahma/Indra evidence exposes every link. Kurma/Bheri/Sarpa evidence
exposes every house predicate. Verified: ≥1 item for all 77 rules on golden;
no generic content-free evidence.

## 10. Provenance

All 15 carry classical attribution (BPHS, UNVERIFIED reference per convention),
per-rule method, and variant notes, registered idempotently in the existing
`ProvenanceRegistry`. Verified: all 15 resolve; all 15 legacy D slugs plus all
5 legacy E slugs resolve to `None` (no canonical provenance on fallback).

## 11. Coverage before/after

- Before: 62/82 = 75.6% (20 legacy: 15 D + 5 E).
- After: **77/82 = 93.9%** (5 legacy: E only).
- Denominator 82 untouched.

## 12. Golden chart results

Golden chart (17/08/2005 00:02 IST, Anaparthy; astronomy untouched): exactly
one new formation — **PASHA** (seven planets in 5 signs: Leo, Sagittarius,
Aries, Cancer, Virgo; evidence recorded). The other 14 do not form, each for
an exact recorded reason (e.g. Sarpa: only 1 malefic Kendra; Indra: Mars 5th
not 3rd from Moon; Kurma: 6th empty; Bheri: houses 1/2/7 empty). Total golden
FORMED: **17** (16 + Pasha); NOT_FORMED: 60. No condition tuned to inflate
formations.

## 13. Legacy crosscheck

64 mapped rules: **54 MATCH**, 10 documented non-matches (9 carried over from
#3B: 3 pre-existing conventions + Chhatra/Jaladhi/Suparijata/Ubhayachari/Vasi/
Vesi; plus 1 new below). No canonical rule altered for parity.

## 14. Every canonical-vs-legacy discrepancy

New in #3C (1): **Pasha** — canonical FORMED vs legacy INACTIVE.
Classification: **legacy implementation defect (dead rule)** — the legacy
`{"type": "nabha", "count": N}` condition key has no handler in
`yoga_evaluator.evaluate_yoga`, so all seven legacy Nabha rules (and Bheri's
`houses` key, Kahala/Go clauses noted in #3B) can never fire. Same root cause
class as the #3B Ubhayachari/Vasi/Vesi deltas. All other 14 Category D rules
MATCH on golden. Full per-rule table in crosscheck.json (64 rows).

## 15. /compute runtime trace

`generate_chart_facts → build_canonical_compute_response →
enrich_response_with_legacy_modules → evaluate_canonical_yogas (77 rules) →
legacy gap-fill → coverage-map suppression → source tagging → response.`
Verified live on the golden chart (timings §22).

## 16. Authenticated response

**82 entries = 77 `canonical` + 5 `legacy_fallback`**; IDs unique; no `None`;
zero covered-legacy leakage; canonical 17 ACTIVE / 60 INACTIVE; all 15 D IDs
present (only Pasha ACTIVE); legacy remainder exactly
`garuda/kalpadruma/mahabhagya/matsya/mridanga`.

## 17. Unauthenticated response

**77 canonical only** (legacy auth-gating unchanged); all `_source =
"canonical"`.

## 18. AI verification

No AI code changed. `summarize_context`/`build_expert_context` pass yoga
dicts through (verified live: `_source`, `provenance`, `evidence_summary`,
`status` preserved for both canonical and legacy entries); system instruction
unchanged ("Do not perform new calculations; interpret the provided ones").
AI recalculates nothing.

## 19. Frontend compatibility

**Frontend unchanged — response contract preserved.** Canonical entries carry
all 12 contract keys (asserted); legacy fallback keeps pre-existing shape +
`_source`. No frontend code touched. Phase 11 passes (242/242); Phase 12
release checks pass.

## 20. Regression tests

| Suite | Result |
|-------|--------|
| New `test_category_d_yogas_3c.py` | **290/290** (registration, metadata, Nabha 1–7 + node exclusion, 15×pos/neg, boundaries, chains, evidence, provenance, golden pins, determinism, merge, hygiene incl. no-legacy-import and no-Category-E guards) |
| Migration #3B Category C suite | 589/589 |
| Phase 4B / 5A / 5B (695) / 5C / Golden (39) | PASS |
| Phase 6A–6E (48/51/115/86/105) | PASS |
| Phase 7 (176) / 8 (211) / 9 | PASS |
| Phase 10 (1085) / 11 (242) / 12 (310) | PASS |

Count-assertion updates (62→77, catalogues 87→102, applicable 86→101) are
migration-necessitated anchor updates only; no test deleted or weakened.

## 21. Determinism

Byte-identical reruns at engine, adapter, Nabha-primitive, and full `/compute`
levels. No randomness, wall-clock, API, or mutable-global dependence.

## 22. Performance

77-rule evaluation mean **0.011 s** (62-rule: 0.012 s — no material change).
Full enrich ≈ 6.1 s, dominated by pre-existing legacy modules (unchanged).
Facts/StrengthReport reused; no repeated astronomy.

## 23. Remaining Category E fallback

Garuda, Kalpadruma, Mahabhagya, Matsya, Mridanga — exactly these five, verified
by ID live. No other Yoga remains legacy fallback.

## 24. Legacy caller audit

`evaluate_canonical_yogas()` primary (77); `evaluate_all_yogas()` auth-gated
gap-fill (5 uncovered only; 71 covered slugs suppressed); full-legacy branch
rollback-only (not triggered); `yoga_evaluator.py` and all rulesets retained
(only prior `neechabhanga.json` id repair stands). No canonical result ever
overridden by legacy. No production caller removed.

## 25. Known limitations

1. Astra/Asura conjunctive reading follows the ruleset description over the
   clause-dropping legacy code (documented defect, §4).
2. Sarpa/Kurma node-as-malefic follows the existing canonical natural-malefic
   set (pinned by test, recorded in metadata).
3. Bheri node exclusion follows Nabhasa seven-graha convention (recorded).
4. Legacy Nabha/Bheri rules can never fire (dead keys) — crosscheck deltas
   are reference defects, not canonical issues.
5. AI summary receives first 12 yogas only (pre-existing).

## 26. Final PASS/BLOCKED verdict

**PASS.** All 26 pass criteria met: 15/15 implemented with exact §19 IDs on
RuleContext facts; new primitive reusable and narrow; no legacy calls from
canonical rules; Evidence + Provenance for all 15; 77/82 coverage with exactly
the 5 Category E fallback; no duplicates; precedence verified; golden
deterministic (17 FORMED); crosscheck complete with every discrepancy
documented; auth/unauth paths verified live; AI metadata preserved; frontend
contract preserved; all suites pass; no astronomy/astrology formula changed;
Category E and all unrelated systems untouched; no commit; no push.

**NO COMMIT / NO PUSH — awaiting review.**
