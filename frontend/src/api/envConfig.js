/**
 * Environment configuration — Phase 12.
 * Explicit DEVELOPMENT / STAGING / PRODUCTION separation. Reads only
 * public (VITE_) variables; backend secrets must never appear here.
 * Missing production API URL fails visibly instead of silently calling
 * a wrong backend.
 */

function readEnv() {
  try {
    return import.meta.env || {};
  } catch {
    return {};
  }
}

export function appMode(env = readEnv()) {
  const mode = env.MODE || env.VITE_APP_ENV || 'development';
  if (['production', 'staging', 'development', 'test'].includes(mode)) return mode;
  return 'development';
}

export function apiBaseUrl(env = readEnv()) {
  const url = env.VITE_API_URL || '';
  if (!url && appMode(env) === 'production') {
    // Visible failure instead of a silent wrong-backend call.
    throw new Error('VITE_API_URL is required in production');
  }
  return url || 'http://localhost:8001';
}

export function isDebugAllowed(env = readEnv()) {
  return appMode(env) !== 'production';
}
