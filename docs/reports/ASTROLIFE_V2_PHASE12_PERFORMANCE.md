# Astrolife V2 — Phase 12 Performance

All astrology formulas FROZEN. Measurements are of the existing validated pipeline on the reference machine; no formula or golden change.

---

## 1. Backend Benchmark (reference machine)

Benchmark methodology: `time.perf_counter`, best representative single/3-run timings for the canonical golden chart (MEDAPATI BHASKARA VENKATA RAJEEV REDDY, 17/08/2005 00:02 IST, Anaparthy AP).

| Phase | Mean latency |
|---|---|
| Chart facts (cold) | **0.9 ms** |
| Chart facts (warm, n=3) | **0.9 ms** |
| All vargas (D1–D60) | **1.9 ms** |
| Strength report (shadbala/bhava/vimsopaka) | **1201.7 ms** |
| Parashari yogas (31 rules) | **7.3 ms** |
| Doshas (6) | **1.1 ms** |
| Jaimini facts | **0.7 ms** |
| Research experiment (read-only) | **0.8 ms** |

**Observation:** Strength report is the dominant cost (~1.2 s). This is inherent to the Avalon/shadbala calculation and was not optimized because correctness/validation precedence is frozen. It is well within a server-side request budget and unaffected by concurrency (no shared mutable state). Chart/varga/jaimini/yoga/dosha/research are all sub-10 ms.

Phase 12 test thresholds (all met comfortably):
- chart cold < 30 s, warm < 5 s
- varga < 2 s
- strength < 15 s
- yoga < 10 s, dosha < 10 s
- jaimini < 5 s
- research < 5 s

## 2. Frontend Bundle Audit

| Asset | Size |
|---|---|
| `index-*.js` (app) | 194.7 KB |
| `vendor-*.js` | 482.5 KB |
| `index-*.css` | 64.2 KB |
| `vendor-*.css` | 13.6 KB |
| `ganesha_circle-*.png` | 1004.4 KB |

**Bundle correctness:** Browser ships **zero ephemeris** (`swisseph` / `set_sid_mode` absent). App JS + vendor JS ≈ 677 KB combined; no duplicate unnecessary backend deps; no development-only libs in the production bundle.

## 3. Asset Finding (re-evaluated)

- Pre-existing ~1 MB `ganesha_circle-*.png` (1004.4 KB) **determination: PRE-EXISTING ACCEPTABLE** — a static illustration, not JS code, not ephemeris, not a secret. Optional future optimization (compression/WebP/CDN) without UI redesign; does not block release.

## 4. Caching

- `core.ops.cache.IsolatedCache` + `chart_key(..., user=)` / `dynamic_key(base, eval_iso, profile)` / `research_key(...)`:
  - Cross-user contamination impossible when key builders are used.
  - Dynamic data (dasha/transit/prediction) binds evaluation datetime + profile ⇒ changed evaluation date yields fresh data.
  - Per-key and prefix invalidation tested (test 14/33).
- No mutable astrology object is cached unsafely; no premature parallelization that could introduce nondeterminism.

## 5. Cold vs Warm

- Chart generation is already fast and stateless; cold≈warm (0.9 ms). Strength dominates at ~1.2 s regardless.

## 6. No Premature Optimization

- No correctness↔speed tradeoff.
- No unsafe caching of mutable astrology objects.
- No nondeterministic parallelization.
- No precision reduction.

## 7. Threshold Rationale

Thresholds are derived from the measured baseline (well below), chosen deliberately loose to avoid flaky CI on slower machines while still catching severe regressions (e.g., accidental O(n²) or added full per-request regression). Not arbitrary strict numbers.

---

## Performance Conclusion

- Backend: all endpoints within production-acceptable server-side budgets; dominant cost is the inherent strength computation.
- Frontend: compact code bundle, zero ephemeris, one accepted static image.
- No optimization changed any astrology formula or golden anchor.
