# ASTROLIFE V2 — PHASE 11 — TEST REPORT

## New Phase 11 tests: 307 / 307 PASS
- Python `backend/test_frontend_phase11.py`: **241/241** (structure 11,
  routes 19, calc-firewall 2, hardcoded scan 1, security 5, API map 17,
  contracts 40, wiring 12, types/utils 22, responsive/a11y/perf 7,
  stack/config 18, pages 12, protected layers 19, shell/cards 27, entry 15,
  surface 7).
- Node `node:test` (zero new deps): **66/66** across statusSemantics (20),
  canonicalFormat (14), chartParams (22), endpoints (10).

## Backend regression (§67): 0 failures
39 / 19,692 / 423 / 788 / 27 / 81,283 / 87 / 185 / 355 / 157 / 143 / 62 /
57 / 38 / 62 / 57 / 48 / 51 / 115 / 86 / 105 / 176 / 211 / 281 / 993 —
all re-executed in-session.
- Backend executed: 105,521 + 241 = **105,762**; unique: 105,483 + 241 = **105,724**.
- Frontend: 66/66. Combined new: **307**. System totals: executed **105,828**,
  unique **105,790** (reported separately per §69: backend / frontend /
  integration / build / audits — never merged misleadingly).

## Frontend regression (§68)
Pre-existing: no test framework, no tests (nothing deleted). New: 66 Node
tests + 241 Python integration/static tests. Build: `vite build` PASS
(23s; vendor 494KB/gzip 159KB; index 199KB/gzip 48KB). Lint: pre-existing
broken (no eslint config) — documented, untouched. Typecheck: n/a (JS
project; JSDoc contracts added instead).

## Integration (§49–51), visual (§47), static (§71–72, §75)
Golden chart renders Taurus/Moon-Purvashada-2 path end-to-end (backend
truth → adapters → existing components); no recalculation layer found;
cache-key isolation proven; visual preservation via minimal diff (4 files
touched, +~60 lines total); no-calculation static test with
DISPLAY/TYPE/API-vs-calculation distinction (two self-caught
false-positives fixed in the test itself).
