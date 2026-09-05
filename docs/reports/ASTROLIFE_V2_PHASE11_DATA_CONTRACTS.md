# ASTROLIFE V2 — PHASE 11 — DATA CONTRACTS

## Golden frontend contract (canonical chart, via route-handler functions)
Taurus ascendant; 9+ planets; Moon Purvashada Pada 2; d9 + vimshottari +
vargas present; strengths/jaimini/ashtakavarga/shadbala/maitri/
panchanga/doshas enrichment all non-null; UTC≡IST same `jd_ut` and sign;
distinct charts distinct results; dynamic state has dasha/panchanga/
transits; research golden package id + EXPERIMENTAL visibility + 12 gates.

## Error contracts
Invalid month → backend 422 (route-level; frontend surfaces
VALIDATION_ERROR, never a negative reading). Unavailable backend →
UNAVAILABLE alert. Error taxonomy asserted in both suites.

## Type contracts (`api/types.js` v11.0.0)
ComputeResponse, DynamicStateResponse, YogaResult (formation vocabulary),
DoshaResult (formation/severity/mitigation/tradition), AgentResult,
PredictionEvent (EVENT_WINDOW, uncertainty, no probability), ResearchRuleView
(lifecycle visible), NormalizedApiError. Raw canonical values retained
alongside every formatted display string.

## Cache contracts
`chartCacheKey` (birth+place+tz) and `dynamicCacheKey` (+evaluation+profile)
asserted: identical inputs share keys; any change splits keys — no
cross-chart or cross-date leaks. Natal facts never refetched on
evaluation-date change.
