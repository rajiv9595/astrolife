# ASTROLIFE V2 — PHASE 11 — ARCHITECTURE

## Layers
Components/pages → hooks (`useCanonicalChart`) → `api/canonicalClient`
(+ existing services) → axios instance (`services/api.js`: env-first
`VITE_API_URL`, Bearer interceptor) → FastAPI backend → canonical truth
layers. Adapters (`getChartDataByType`, `getActiveDasha`, formatters) reshape
for display only; status words pass through verbatim.

## State
Static (birth params + ChartFacts, cache-keyed) vs dynamic (evaluation ISO
+ dasha/transit, keyed on chart+evaluation+profile). Chart identity change
clears dynamic state first (stale-guard); AbortController cancels
superseded dynamic fetches; `useMemo` avoids recompute-per-render. No
global store was introduced; multi-chart isolation via cache keys.

## Types
Plain-JS project: JSDoc contracts in `api/types.js` (contract v11.0.0)
covering ChartFacts → Research, plus the normalized error shape. No TS
migration, no calculation inside types.

## Timezone safety
`chartParams.buildComputeParams` validates ranges + IANA tz and passes the
local wall time through untouched. Backend owns UTC/JD/ayanamsha.
UTC≡IST equivalence proven in backend contracts (same `jd_ut`).

## Errors
`normalizeApiError` → VALIDATION_ERROR / NOT_FOUND / UNAVAILABLE /
INVALID_INPUT / CONFLICT / UNKNOWN / INTERNAL_ERROR. Backend errors never
render as "no yoga/dosha/event". UNKNOWN/INVALID/CONFLICTED keep dedicated
tones and explanations.

## Research
Read-only `/research/*` → ResearchLab with EXPERIMENTAL badging, 12-gate
visibility, evidence states. No promotion action exists in the UI by design.
