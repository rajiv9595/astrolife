/**
 * Phase 11 — birth-input validation + timezone-safety tests (node:test).
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { validateBirthInput, buildComputeParams, chartCacheKey, dynamicCacheKey } from '../chartParams.js';

const GOLDEN_INPUT = {
  year: 2005, month: 8, day: 17, hour: 0, minute: 2,
  lat: 16.93407, lon: 81.95522, tz: 'Asia/Kolkata',
};

describe('validateBirthInput', () => {
  it('accepts the canonical golden input', () => {
    assert.deepEqual(validateBirthInput(GOLDEN_INPUT), []);
  });
  it('rejects out-of-range fields', () => {
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT, month: 13 }).length > 0);
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT, day: 0 }).length > 0);
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT, hour: 24 }).length > 0);
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT, minute: 60 }).length > 0);
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT, lat: 91 }).length > 0);
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT, lon: -181 }).length > 0);
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT, year: 1700 }).length > 0);
  });
  it('requires an IANA timezone (no silent browser-local fallback)', () => {
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT, tz: '' }).length > 0);
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT, tz: 'IST' }).length > 0);
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT }).length === 0);
  });
  it('handles missing input object', () => {
    assert.ok(validateBirthInput(null).length > 0);
    assert.ok(validateBirthInput({}).length > 0);
  });
});

describe('buildComputeParams timezone safety', () => {
  it('preserves the tz string verbatim', () => {
    const { params, errors } = buildComputeParams(GOLDEN_INPUT);
    assert.ok(!errors);
    assert.equal(params.tz, 'Asia/Kolkata');
  });
  it('passes local wall time through (never pre-converted to UTC)', () => {
    const { params } = buildComputeParams(GOLDEN_INPUT);
    assert.equal(params.hour, 0);
    assert.equal(params.minute, 2);
    assert.equal(params.second, 0);
  });
  it('returns errors, not params, for invalid input', () => {
    const r = buildComputeParams({ ...GOLDEN_INPUT, lat: 500 });
    assert.ok(r.errors && r.errors.length > 0);
    assert.ok(!r.params);
  });
});

describe('param details', () => {
  it('second is always zero (backend owns sub-minute precision)', () => {
    const { params } = buildComputeParams(GOLDEN_INPUT);
    assert.equal(params.second, 0);
  });
  it('errors are human-readable strings', () => {
    const { errors } = buildComputeParams({ ...GOLDEN_INPUT, month: 99 });
    assert.ok(errors.every((e) => typeof e === 'string' && e.length > 0));
  });
  it('boundary values pass (day 31, hour 23, minute 59)', () => {
    assert.deepEqual(validateBirthInput({ ...GOLDEN_INPUT, day: 31, hour: 23, minute: 59 }), []);
  });
  it('poles and antimeridian pass', () => {
    assert.deepEqual(validateBirthInput({ ...GOLDEN_INPUT, lat: -90, lon: 180 }), []);
  });
  it('non-integer numerics fail', () => {
    assert.ok(validateBirthInput({ ...GOLDEN_INPUT, year: 2005.5 }).length > 0);
  });
  it('cache key embeds the timezone', () => {
    const a = buildComputeParams(GOLDEN_INPUT).params;
    const b = buildComputeParams({ ...GOLDEN_INPUT, tz: 'America/New_York' }).params;
    assert.ok(chartCacheKey(a).includes('Asia/Kolkata'));
    assert.notEqual(chartCacheKey(a), chartCacheKey(b));
  });
});

describe('year and boundary rules', () => {
  it('year 1800 and 2100 pass', () => {
    assert.deepEqual(validateBirthInput({ ...GOLDEN_INPUT, year: 1800 }), []);
    assert.deepEqual(validateBirthInput({ ...GOLDEN_INPUT, year: 2100 }), []);
  });
  it('month 1 and 12 pass', () => {
    assert.deepEqual(validateBirthInput({ ...GOLDEN_INPUT, month: 1 }), []);
    assert.deepEqual(validateBirthInput({ ...GOLDEN_INPUT, month: 12 }), []);
  });
  it('dynamic key defaults profile when omitted', () => {
    const a = buildComputeParams(GOLDEN_INPUT).params;
    assert.ok(dynamicCacheKey(a, 'X', undefined).includes('default'));
  });
});

describe('cache keys prevent cross-chart leaks', () => {
  it('identical inputs share a chart key', () => {
    const a = buildComputeParams(GOLDEN_INPUT).params;
    const b = buildComputeParams({ ...GOLDEN_INPUT }).params;
    assert.equal(chartCacheKey(a), chartCacheKey(b));
  });
  it('different birth time changes the key', () => {
    const a = buildComputeParams(GOLDEN_INPUT).params;
    const b = buildComputeParams({ ...GOLDEN_INPUT, minute: 3 }).params;
    assert.notEqual(chartCacheKey(a), chartCacheKey(b));
  });
  it('different coordinates change the key', () => {
    const a = buildComputeParams(GOLDEN_INPUT).params;
    const b = buildComputeParams({ ...GOLDEN_INPUT, lat: 17 }).params;
    assert.notEqual(chartCacheKey(a), chartCacheKey(b));
  });
  it('dynamic key binds chart + evaluation + profile', () => {
    const a = buildComputeParams(GOLDEN_INPUT).params;
    const k1 = dynamicCacheKey(a, '2026-09-02T12:00:00Z', 'default');
    const k2 = dynamicCacheKey(a, '2026-09-03T12:00:00Z', 'default');
    const k3 = dynamicCacheKey(a, '2026-09-02T12:00:00Z', 'other');
    assert.notEqual(k1, k2);
    assert.notEqual(k1, k3);
  });
});
