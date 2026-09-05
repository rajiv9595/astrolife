/**
 * Phase 12 — environment configuration tests (node:test, zero dependencies).
 * import.meta is undefined under plain node, so env objects are injected.
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { appMode, apiBaseUrl, isDebugAllowed } from '../envConfig.js';

describe('appMode', () => {
  it('resolves production/staging/development/test', () => {
    assert.equal(appMode({ MODE: 'production' }), 'production');
    assert.equal(appMode({ MODE: 'staging' }), 'staging');
    assert.equal(appMode({ MODE: 'development' }), 'development');
    assert.equal(appMode({ MODE: 'test' }), 'test');
  });
  it('falls back to development for unknown or missing mode', () => {
    assert.equal(appMode({ MODE: 'weird' }), 'development');
    assert.equal(appMode({}), 'development');
  });
  it('honours VITE_APP_ENV override', () => {
    assert.equal(appMode({ VITE_APP_ENV: 'staging' }), 'staging');
  });
});

describe('apiBaseUrl', () => {
  it('uses VITE_API_URL when set', () => {
    assert.equal(apiBaseUrl({ MODE: 'production', VITE_API_URL: 'https://api.example.com' }), 'https://api.example.com');
  });
  it('throws visibly in production when missing', () => {
    assert.throws(() => apiBaseUrl({ MODE: 'production' }), /VITE_API_URL is required/);
  });
  it('falls back to localhost only outside production', () => {
    assert.equal(apiBaseUrl({ MODE: 'development' }), 'http://localhost:8001');
  });
});

describe('isDebugAllowed', () => {
  it('forbids debug in production only', () => {
    assert.equal(isDebugAllowed({ MODE: 'production' }), false);
    assert.equal(isDebugAllowed({ MODE: 'development' }), true);
    assert.equal(isDebugAllowed({ MODE: 'staging' }), true);
  });
});
