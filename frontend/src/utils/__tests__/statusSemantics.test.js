/**
 * Phase 11 — status semantics unit tests (node:test, zero dependencies).
 * Backend truth words must survive the frontend untouched.
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  STATUSES, normalizeStatus, describeStatus, isUncertain, badgeTone,
  ERROR_KINDS, normalizeErrorKind,
} from '../statusSemantics.js';

describe('status vocabulary', () => {
  it('contains all eight required states', () => {
    for (const s of ['FORMED', 'NOT_FORMED', 'UNKNOWN', 'INVALID', 'CONFLICTED', 'UNSUPPORTED', 'INSUFFICIENT', 'PARTIAL']) {
      assert.ok(STATUSES.includes(s), s);
    }
  });
  it('normalizes case-insensitively', () => {
    assert.equal(normalizeStatus('formed'), 'FORMED');
    assert.equal(normalizeStatus('  Unknown '), 'UNKNOWN');
  });
  it('maps garbage to UNKNOWN, never to NOT_FORMED', () => {
    assert.equal(normalizeStatus('garbage!!'), 'UNKNOWN');
    assert.equal(normalizeStatus(null), 'UNKNOWN');
    assert.equal(normalizeStatus(undefined), 'UNKNOWN');
    assert.equal(normalizeStatus(42), 'UNKNOWN');
    assert.notEqual(normalizeStatus('???'), 'NOT_FORMED');
  });
  it('UNKNOWN !== NOT_FORMED !== INVALID !== CONFLICTED !== UNSUPPORTED', () => {
    const set = new Set(['UNKNOWN', 'NOT_FORMED', 'INVALID', 'CONFLICTED', 'UNSUPPORTED'].map(normalizeStatus));
    assert.equal(set.size, 5);
  });
  it('every status has a description', () => {
    for (const s of STATUSES) assert.ok(describeStatus(s).length > 0, s);
  });
  it('UNKNOWN description is not a negative', () => {
    assert.ok(!/not present|absent|no yoga|no dosha/i.test(describeStatus('UNKNOWN')));
  });
});

describe('uncertainty guard', () => {
  it('flags UNKNOWN/INVALID/CONFLICTED/UNSUPPORTED/INSUFFICIENT', () => {
    for (const s of ['UNKNOWN', 'INVALID', 'CONFLICTED', 'UNSUPPORTED', 'INSUFFICIENT']) {
      assert.equal(isUncertain(s), true, s);
    }
  });
  it('does not flag FORMED/NOT_FORMED/PARTIAL/ACTIVE/STRONG', () => {
    for (const s of ['FORMED', 'NOT_FORMED', 'PARTIAL', 'ACTIVE', 'STRONG']) {
      assert.equal(isUncertain(s), false, s);
    }
  });
});

describe('badge tones reuse existing palette', () => {
  it('every status maps to a Tailwind tone string', () => {
    for (const s of STATUSES) {
      const t = badgeTone(s);
      assert.ok(typeof t === 'string' && t.includes('bg-') && t.includes('border-'), s);
    }
  });
  it('UNKNOWN and NOT_FORMED use different tones', () => {
    assert.notEqual(badgeTone('UNKNOWN'), badgeTone('NOT_FORMED'));
  });
});

describe('extra states', () => {
  it('normalizes partial/active/strong', () => {
    assert.equal(normalizeStatus('partial'), 'PARTIAL');
    assert.equal(normalizeStatus('Active'), 'ACTIVE');
    assert.equal(normalizeStatus('STRONG'), 'STRONG');
  });
  it('conflicted tone differs from formed tone', () => {
    assert.notEqual(badgeTone('CONFLICTED'), badgeTone('FORMED'));
    assert.ok(badgeTone('CONFLICTED').includes('purple'));
  });
  it('invalid tone signals error, unsupported stays neutral', () => {
    assert.ok(badgeTone('INVALID').includes('red'));
    assert.ok(badgeTone('UNSUPPORTED').includes('stone'));
  });
  it('vocabulary and error kinds are frozen', () => {
    assert.ok(Object.isFrozen(STATUSES));
    assert.ok(Object.isFrozen(ERROR_KINDS));
  });
  it('insufficient is uncertain and amber', () => {
    assert.equal(isUncertain('INSUFFICIENT'), true);
    assert.ok(badgeTone('INSUFFICIENT').includes('amber'));
  });
  it('empty string normalizes to UNKNOWN', () => {
    assert.equal(normalizeStatus(''), 'UNKNOWN');
    assert.equal(normalizeStatus('   '), 'UNKNOWN');
  });
});

describe('error taxonomy', () => {
  it('contains all seven kinds', () => {
    for (const k of ['VALIDATION_ERROR', 'NOT_FOUND', 'UNAVAILABLE', 'INVALID_INPUT', 'CONFLICT', 'UNKNOWN', 'INTERNAL_ERROR']) {
      assert.ok(ERROR_KINDS.includes(k), k);
    }
  });
  it('no error kind mentions yoga/dosha/event negatives', () => {
    for (const k of ERROR_KINDS) assert.ok(!/no yoga|no dosha|no event/i.test(k));
  });
  it('normalizes unknown to UNKNOWN', () => {
    assert.equal(normalizeErrorKind('weird'), 'UNKNOWN');
    assert.equal(normalizeErrorKind('validation_error'), 'VALIDATION_ERROR');
  });
});
