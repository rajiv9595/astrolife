/**
 * Backend status semantics — Phase 11.
 * UNKNOWN / INVALID / CONFLICTED / NOT_FORMED / UNSUPPORTED / INSUFFICIENT /
 * PARTIAL / FORMED must never collapse into true/false or good/bad.
 * Pure module (no React, no network) — covered by node:test suite.
 */

export const STATUSES = Object.freeze([
  'FORMED',
  'NOT_FORMED',
  'UNKNOWN',
  'INVALID',
  'CONFLICTED',
  'UNSUPPORTED',
  'INSUFFICIENT',
  'PARTIAL',
  'ACTIVE',
  'STRONG',
]);

const DESCRIPTIONS = Object.freeze({
  FORMED: 'Formed per canonical backend evaluation.',
  NOT_FORMED: 'Not formed per canonical backend evaluation.',
  UNKNOWN: 'Unknown — insufficient data. Not a negative result.',
  INVALID: 'Invalid — input or rule not applicable. Not a negative result.',
  CONFLICTED: 'Conflicted — sources or rules disagree. See provenance.',
  UNSUPPORTED: 'Unsupported — subsystem cannot evaluate this. Not negative.',
  INSUFFICIENT: 'Insufficient data for evaluation.',
  PARTIAL: 'Partially applicable.',
  ACTIVE: 'Active.',
  STRONG: 'Strong.',
});

// Badge tones reuse the existing Tailwind palette only.
const TONES = Object.freeze({
  FORMED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  NOT_FORMED: 'bg-stone-100 text-stone-600 border-stone-200',
  UNKNOWN: 'bg-amber-50 text-amber-700 border-amber-200',
  INVALID: 'bg-red-50 text-red-600 border-red-200',
  CONFLICTED: 'bg-purple-50 text-purple-700 border-purple-200',
  UNSUPPORTED: 'bg-stone-100 text-stone-500 border-stone-200',
  INSUFFICIENT: 'bg-amber-50 text-amber-700 border-amber-200',
  PARTIAL: 'bg-sky-50 text-sky-700 border-sky-200',
  ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  STRONG: 'bg-emerald-50 text-emerald-700 border-emerald-200',
});

export function normalizeStatus(value) {
  if (typeof value !== 'string') return 'UNKNOWN';
  const v = value.trim().toUpperCase();
  return STATUSES.includes(v) ? v : 'UNKNOWN';
}

export function describeStatus(value) {
  return DESCRIPTIONS[normalizeStatus(value)];
}

/** True when the status must NOT be presented as a negative result. */
export function isUncertain(value) {
  return ['UNKNOWN', 'INVALID', 'CONFLICTED', 'UNSUPPORTED', 'INSUFFICIENT'].includes(
    normalizeStatus(value)
  );
}

export function badgeTone(value) {
  return TONES[normalizeStatus(value)];
}

/** Error taxonomy preserved from backend failures (never mapped to "no yoga"). */
export const ERROR_KINDS = Object.freeze([
  'VALIDATION_ERROR',
  'NOT_FOUND',
  'UNAVAILABLE',
  'INVALID_INPUT',
  'CONFLICT',
  'UNKNOWN',
  'INTERNAL_ERROR',
]);

export function normalizeErrorKind(value) {
  if (typeof value !== 'string') return 'UNKNOWN';
  const v = value.trim().toUpperCase();
  return ERROR_KINDS.includes(v) ? v : 'UNKNOWN';
}
