/**
 * Canonical backend endpoint map — Phase 11.
 * Names below MUST match backend routes exactly. Do not invent endpoints here;
 * see ASTROLIFE_V2_PHASE11_API_MAP.md. Frontend never calculates astrology.
 */
export const ENDPOINTS = Object.freeze({
  HEALTH: '/health',
  COMPUTE: '/compute',
  MATCH: '/match',
  DYNAMIC_STATE: '/dynamic/state',
  DYNAMIC_PANCHANGA: '/dynamic/panchanga',
  DYNAMIC_TRANSIT_SNAPSHOT: '/dynamic/transit-snapshot',
  DYNAMIC_TRANSIT_RANGE: '/dynamic/transit-range',
  DYNAMIC_COMPUTE: '/dynamic/compute-dynamic',
  AI_ANALYZE: '/ai/analyze',
  AI_EXPERT_REPORT: '/ai/expert_report',
  GEOCODE_SEARCH: '/geocode/search',
  GEOCODE_SUGGESTIONS: '/geocode/suggestions',
  GEOCODE_REVERSE: '/geocode/reverse',
  AUTH_SIGNUP: '/auth/signup',
  AUTH_LOGIN: '/auth/login',
  RESEARCH_GOLDEN: '/research/golden',
  RESEARCH_GATES: '/research/gates',
});

export function buildGeocodeSearchUrl(query) {
  return `${ENDPOINTS.GEOCODE_SEARCH}?query=${encodeURIComponent(query)}`;
}

export function buildGeocodeSuggestionsUrl(query) {
  return `${ENDPOINTS.GEOCODE_SUGGESTIONS}?query=${encodeURIComponent(query)}`;
}
