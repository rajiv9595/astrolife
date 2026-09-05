/**
 * Birth-input validation + canonical /compute param building — Phase 11.
 * Timezone safety: the local birth time + IANA timezone are passed through
 * verbatim. The frontend NEVER converts birth time to UTC and resubmits it
 * as local time; the backend remains authoritative for UTC/JD/ayanamsha.
 * Pure module (no React, no network).
 */

function isInt(n) {
  return typeof n === 'number' && Number.isInteger(n);
}

export function validateBirthInput(input) {
  const errors = [];
  const { year, month, day, hour, minute, lat, lon, tz } = input || {};
  if (!isInt(year) || year < 1800 || year > 2100) errors.push('year must be an integer 1800-2100');
  if (!isInt(month) || month < 1 || month > 12) errors.push('month must be 1-12');
  if (!isInt(day) || day < 1 || day > 31) errors.push('day must be 1-31');
  if (!isInt(hour) || hour < 0 || hour > 23) errors.push('hour must be 0-23');
  if (!isInt(minute) || minute < 0 || minute > 59) errors.push('minute must be 0-59');
  if (typeof lat !== 'number' || lat < -90 || lat > 90) errors.push('lat must be -90..90');
  if (typeof lon !== 'number' || lon < -180 || lon > 180) errors.push('lon must be -180..180');
  if (typeof tz !== 'string' || tz.length === 0 || !tz.includes('/')) errors.push('tz must be an IANA timezone like Asia/Kolkata');
  return errors;
}

/**
 * Build POST /compute params. Returns {params} or {errors}.
 * The tz string is preserved exactly as entered/selected.
 */
export function buildComputeParams(input) {
  const errors = validateBirthInput(input);
  if (errors.length > 0) return { errors };
  const { year, month, day, hour, minute, lat, lon, tz } = input;
  return {
    params: {
      year, month, day, hour, minute,
      second: 0,
      tz, // preserved verbatim — never converted client-side
      lat, lon,
    },
  };
}

/** Cache key covering canonical chart identity (birth + place + tz). */
export function chartCacheKey(params) {
  return ['chart', params.year, params.month, params.day, params.hour,
    params.minute, params.lat, params.lon, params.tz].join('|');
}

/** Dynamic-state key: chart identity + evaluation datetime + profile. */
export function dynamicCacheKey(params, evaluationIso, profile) {
  return ['dynamic', chartCacheKey(params), evaluationIso || 'now', profile || 'default'].join('|');
}
