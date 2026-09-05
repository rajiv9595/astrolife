/**
 * Phase 11 — canonical formatting unit tests (node:test, zero dependencies).
 * Formatting is presentation-only; raw values are always retained.
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { formatDegree, formatPrecise, formatIsoDisplay, wholeSignHouseDisplay, SIGN_ORDER } from '../canonicalFormat.js';

describe('formatDegree', () => {
  it('formats 120.04186 with raw retained', () => {
    const r = formatDegree(120.04186);
    assert.equal(r.text, '120\u00B02\'');
    assert.equal(r.raw, 120.04186);
    assert.equal(r.precise, '120.041860');
  });
  it('handles invalid input without inventing values', () => {
    assert.equal(formatDegree(NaN).text, '--');
    assert.equal(formatDegree('x').text, '--');
  });
});

describe('formatPrecise truncates display only', () => {
  it('23.93565836563647 -> 23.935658, raw kept', () => {
    const r = formatPrecise(23.93565836563647);
    assert.equal(r.text, '23.935658');
    assert.equal(r.raw, 23.93565836563647);
  });
  it('never rounds the stored raw value', () => {
    const r = formatPrecise(0.33970886264484434, 6);
    assert.equal(r.raw, 0.33970886264484434);
  });
});

describe('formatIsoDisplay keeps raw ISO', () => {
  it('passes ISO through verbatim', () => {
    const r = formatIsoDisplay('2026-09-02T12:00:00+00:00');
    assert.equal(r.raw, '2026-09-02T12:00:00+00:00');
    assert.ok(r.text.includes('2026-09-02'));
  });
  it('empty/invalid yields placeholder', () => {
    assert.equal(formatIsoDisplay('').text, '--');
    assert.equal(formatIsoDisplay('not-a-date').text, '--');
  });
});

describe('format edge cases', () => {
  it('zero degrees formats cleanly', () => {
    const r = formatDegree(0);
    assert.equal(r.text, '0\u00B00\'');
    assert.equal(r.raw, 0);
  });
  it('precise keeps six decimals by default', () => {
    assert.equal(formatPrecise(6.18).text, '6.180000');
  });
  it('ISO display preserves offsets', () => {
    const r = formatIsoDisplay('2005-08-16T18:32:00.000006+00:00');
    assert.equal(r.raw, '2005-08-16T18:32:00.000006+00:00');
  });
  it('sign order starts Aries ends Pisces', () => {
    assert.equal(SIGN_ORDER[0], 'Aries');
    assert.equal(SIGN_ORDER[11], 'Pisces');
  });
});

describe('more formatting', () => {
  it('359.99 formats without rollover invention', () => {
    const r = formatDegree(359.99);
    assert.equal(r.text, '359\u00B059\'');
    assert.equal(r.raw, 359.99);
  });
  it('integer input formats with decimals retained', () => {
    assert.equal(formatPrecise(100).text, '100.000000');
  });
  it('whole-sign houses cover 1..12 for Aries ascendant', () => {
    const houses = new Set(SIGN_ORDER.map((s) => wholeSignHouseDisplay('Aries', s)));
    assert.equal(houses.size, 12);
  });
});

describe('wholeSignHouseDisplay', () => {
  it('Taurus ascendant, Virgo planet -> house 5', () => {
    assert.equal(wholeSignHouseDisplay('Taurus', 'Virgo'), 5);
  });
  it('wraps around the zodiac', () => {
    assert.equal(wholeSignHouseDisplay('Sagittarius', 'Aries'), 5);
    assert.equal(wholeSignHouseDisplay('Taurus', 'Taurus'), 1);
    assert.equal(wholeSignHouseDisplay('Taurus', 'Aries'), 12);
  });
  it('unknown signs yield null, not a fabricated house', () => {
    assert.equal(wholeSignHouseDisplay('Taurus', 'Pluto-sign'), null);
    assert.equal(wholeSignHouseDisplay(null, 'Aries'), null);
  });
  it('sign order covers all twelve', () => {
    assert.equal(SIGN_ORDER.length, 12);
    assert.ok(SIGN_ORDER.includes('Taurus') && SIGN_ORDER.includes('Pisces'));
  });
});
