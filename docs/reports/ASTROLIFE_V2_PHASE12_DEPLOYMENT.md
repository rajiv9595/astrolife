# Astrolife V2 — Phase 12 Deployment

Astrology semantics FROZEN. Deployment hardening is additive and does not replace the existing Vercel workflow.

---

## 1. Architecture

- **Frontend (static):** React 18 + Vite, pre-built into `frontend/dist`, deployed to Vercel (`frontend/vercel.json`).
- **Backend:** FastAPI + Uvicorn (Python), PostgreSQL persistence, auth, AI integration. Served from the backend/app host.
- SPA rewrites to `/index.html` so client-side routes resolve.

## 2. Environment Separation

Three explicit modes via `ASTROLIFE_ENV`: `development`, `staging`, `production`. Frontend also separates via `VITE_APP_ENV` / build mode. In production, `VITE_API_URL` is **required** — missing it fails visibly instead of silently calling a wrong backend (`envConfig.js`).

## 3. Required Environment Variables

**Backend (production):**
- `ASTROLIFE_ENV=production`
- `JWT_SECRET_KEY` (≥32 chars, not a dev placeholder) — **fail-fast required**
- `DATABASE_URL` (production PostgreSQL, no dev credentials) — **fail-fast required**
- `FRONTEND_ORIGINS` (comma list) **or** `FRONTEND_URL` (single) — **fail-fast required** (wildcard rejected)
- `EPHE_PATH` (default `backend/ephe`)
- `GOOGLE_API_KEY` (AI, backend-only)
- `SQL_ECHO` (default off)

**Frontend (public `VITE_` only):**
- `VITE_API_URL`
- `VITE_APP_ENV` (optional) / build mode

Full list (without secret values) in `ASTROLIFE_V2_PHASE12_PRODUCTION_CONFIG.md`.

## 4. Vercel Configuration

`frontend/vercel.json` (existing):
- SPA rewrite rule to `/index.html`
- `rewrites` key present
- Build output `frontend/dist`

Phase 12 does not replace deployment infrastructure. HTTPS, headers, and caching defaults are left to the hosting platform; security headers are additionally emitted by the backend middleware (`nosniff`, referrer policy, `X-Frame-Options`).

## 5. Backend Deployment

- Launch with `uvicorn backend.app:app` (or equivalent) on the backend host.
- Application factory `create_app()` sets ephemeris path + Lahiri mode, wires CORS (from env), adds request-ID/security-header middleware, registers routes, and creates tables on startup.
- CORS origins resolved from `FRONTEND_ORIGINS` / `FRONTEND_URL`; production wildcard is rejected.

## 6. HTTPS / Headers / HSTS

- HTTPS terminated by hosting platform.
- HSTS: left to platform; recommend `Strict-Transport-Security` on the edge for `production`.
- Backend adds: `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `X-Frame-Options: SAMEORIGIN`.

## 7. CI/CD (recommended release pipeline)

**No CI file exists in the repo.** Recommended release gate (single deterministic gate):

```
AUDIT
→ DEPENDENCY CHECK
→ SECURITY
→ TYPECHECK / BUILD
→ FRONTEND TEST
→ BACKEND TEST
→ INTEGRATION TEST
→ GOLDEN REGRESSION
→ DETERMINISM (50-run)
→ BUILD
→ DEPLOYMENT CONFIGURATION
→ RELEASE CANDIDATE
```

No release if any critical gate fails. (Concrete implementation to be added at the hosting provider.)

## 8. Deployment Dry Run

Phase 12 validates the production-like path locally: env validation, routing, health endpoint, frontend→backend API, auth, CORS, static assets, chart calculation, error handling. A real production deploy is **not** performed automatically (per §73: only if authorized by existing workflow).

## 9. Rollback (summary)

- Frontend rollback: redeploy last known-good `dist` / pin prior build.
- Backend rollback: redeploy last known-good image/build; env must match release manifest.
- See `ASTROLIFE_V2_PHASE12_RUNBOOK.md`.

## 10. Release Manifest

Deterministic manifest (see `ASTROLIFE_V2_PHASE12_RELEASE_MANIFEST.md`): app/API/engine/schema/rule/evidence/prediction/research versions + golden-data SHA-256 + rule count + regression fingerprint.

---

## Deployment Conclusion

Existing Vercel SPA workflow preserved; backend hardened with fail-fast production config, explicit CORS, security headers, request correlation, health/readiness, and a documented (not-yet-implemented) CI release gate. No deployment blocker.
