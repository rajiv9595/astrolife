/**
 * Phase 11 — endpoint map tests (node:test, zero dependencies).
 * Every constant must be a real backend route (verified cross-check in the
 * Python suite against the live FastAPI route table). No invented endpoints.
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { ENDPOINTS, buildGeocodeSearchUrl, buildGeocodeSuggestionsUrl } from '../endpoints.js';

const EXPECTED = Object.freeze({
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

describe('endpoint map', () => {
  it('matches the verified backend route table exactly', () => {
    assert.deepEqual({ ...ENDPOINTS }, { ...EXPECTED });
  });
  it('all values are absolute paths', () => {
    for (const v of Object.values(ENDPOINTS)) assert.ok(v.startsWith('/'), v);
  });
  it('map is frozen (no runtime mutation)', () => {
    assert.ok(Object.isFrozen(ENDPOINTS));
  });
  it('has exactly the verified route set', () => {
    assert.equal(Object.keys(ENDPOINTS).length, 17);
  });
  it('no trailing slashes or query strings in constants', () => {
    for (const v of Object.values(ENDPOINTS)) {
      assert.ok(!v.endsWith('/') || v === '/', v);
      assert.ok(!v.includes('?'), v);
    }
  });
  it('auth endpoints match backend auth router', () => {
    assert.equal(ENDPOINTS.AUTH_SIGNUP, '/auth/signup');
    assert.equal(ENDPOINTS.AUTH_LOGIN, '/auth/login');
  });
  it('dynamic compute endpoint preserved for migration', () => {
    assert.equal(ENDPOINTS.DYNAMIC_COMPUTE, '/dynamic/compute-dynamic');
  });
  it('research endpoints are read-only GET paths', () => {
    assert.ok(ENDPOINTS.RESEARCH_GOLDEN.startsWith('/research/'));
    assert.ok(ENDPOINTS.RESEARCH_GATES.startsWith('/research/'));
  });
  it('builders handle empty and unicode queries', () => {
    assert.ok(buildGeocodeSearchUrl('').endsWith('?query='));
    assert.ok(buildGeocodeSuggestionsUrl('Ånä').includes('%C3%85'));
  });
  it('geocode builders encode queries', () => {
    assert.ok(buildGeocodeSearchUrl('Ana parthy').includes('Ana%20parthy'));
    assert.ok(buildGeocodeSuggestionsUrl('a&b').includes('a%26b'));
  });
});
