/**
 * Display formatting over canonical backend values — Phase 11.
 * Formatting is presentation only: raw canonical values are always kept
 * alongside, never rounded before comparison. Pure module.
 */

export function formatDegree(value, decimals = 6) {
  const raw = Number(value);
  if (!Number.isFinite(raw)) return { text: '--', raw: value };
  const deg = Math.floor(raw);
  const mins = Math.floor((raw - deg) * 60);
  return { text: `${deg}\u00B0${mins}'`, precise: raw.toFixed(decimals), raw };
}

/** Truncate long precision for display, e.g. 23.93565836563647 -> 23.935658. */
export function formatPrecise(value, decimals = 6) {
  const raw = Number(value);
  if (!Number.isFinite(raw)) return { text: '--', raw: value };
  return { text: raw.toFixed(decimals), raw };
}

/** Display an ISO timestamp in a stable, explicit form (no silent tz shift). */
export function formatIsoDisplay(iso) {
  if (typeof iso !== 'string' || iso.length === 0) return { text: '--', raw: iso };
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return { text: '--', raw: iso };
  return { text: d.toISOString().replace('T', ' ').replace('Z', ' UTC'), raw: iso };
}

/** Whole-Sign house of a planet sign given the ascendant sign (display aid;
 *  house assignment itself remains backend-owned; this only mirrors the
 *  Whole Sign order already present in the UI for table display). */
const SIGN_ORDER = Object.freeze([
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]);

export function wholeSignHouseDisplay(ascSign, planetSign) {
  const a = SIGN_ORDER.indexOf(ascSign);
  const p = SIGN_ORDER.indexOf(planetSign);
  if (a === -1 || p === -1) return null;
  return ((p - a + 12) % 12) + 1;
}

export { SIGN_ORDER };
