# Astrolife V2 — Phase 12 Production Audit

**PHASE 12 — FINAL PRODUCTION OPTIMIZATION + HARDENING + RELEASE VALIDATION**

Astrology semantics are FROZEN. This document is the complete production audit of the existing system performed BEFORE any Phase 12 modification, plus the outcome of each finding.

---

## 0. Audit Scope & Method

Inspected:

- `backend/` (application factory, auth, config, database, models, routes, `core/` package, dependency pins)
- `frontend/` (source, `package.json`, `vercel.json`, build output `dist/`, tests)
- configuration / environment files
- database / storage configuration
- authentication + authorization
- API routes + middleware
- logging + error handling
- dependencies (Python + Node)
- CI / deployment configuration (Vercel, no CI found)

Inspection was read-only. No astrology formula, no golden anchor, and no accepted regression baseline was changed by this audit.

---

## 1. Architecture

**Backend — FastAPI (Python 3)**
- `backend/app.py` — factory `create_app()`; global Swiss Ephemeris setup (Lahiri sidereal, `EPHE_PATH`); CORS middleware; ASGI `_ops_middleware` (request ID + security headers); route registration; startup table creation.
- `backend/auth.py` — JWT (`HS256`) + bcrypt password hashing. Environment-first secret key with an explicitly-marked dev-only fallback.
- `backend/auth_routes.py` — signup / login / google-login / me.
- `backend/database.py` — SQLAlchemy engine, PostgreSQL via `DATABASE_URL`.
- `backend/models.py` — `User`, `ChartData`, `APIKey`.
- Routes: `/compute`, `/match` (via `routes/astro.py`), `routes/ai_routes.py`, `routes/research.py`, `routes/api_keys.py`, `routes/family.py`, `routes/learning.py`, `routes/dynamic.py`, `routes/ops.py` (`/ready`), `routes/geocode.py`.
- `backend/core/` — canonical truth layer: calculation, varga, panchanga, dasha, transit, strength, rules (parashari / doshas / dynamic / jaimini), evidence, prediction (Phase 8), research (Phase 9), agents (Phase 7), timing (Phase 5H), regression (Phase 10).
- `backend/core/ops/` — Phase 12 ops package: `config`, `logging_setup`, `request_id`, `rate_limit`, `headers`, `health`, `cache`, `guards`, `manifest`, `version`.

**Frontend — React 18 + Vite + Tailwind**
- SPA consuming the backend JSON API. No astrology calculation in the browser.
- `frontend/src/services/api.js` reads `VITE_API_URL`.
- `frontend/src/api/envConfig.js` enforces explicit DEVELOPMENT / STAGING / PRODUCTION mode separation.

---

## 2. Deployment Architecture

- Backend: FastAPI served via Uvicorn; PostgreSQL persistence implied.
- Frontend: static Vercel deployment (`frontend/vercel.json`), SPA rewrite to `/index.html`.
- No Dockerfile found; containerized deployment is not required by the existing workflow.
- No CI configuration file found in the repository (assessed in CI/CD section).

---

## 3. Environment Configuration

- `ASTROLIFE_ENV` → `development` | `staging` | `production` (default development).
- `JWT_SECRET_KEY` → JWT signing secret. **Required in production** (≥32 chars, no dev placeholder).
- `DATABASE_URL` → PostgreSQL URL. **Required in production** (no dev credentials).
- `FRONTEND_ORIGINS` / `FRONTEND_URL` → CORS origins. **Required in production** (wildcard rejected).
- `EPHE_PATH` → ephemeris directory (defaults to `backend/ephe`).
- `GOOGLE_API_KEY` → backend AI key (never shipped to frontend).
- `SQL_ECHO` → gated SQL echo (off by default).
- Frontend public vars: `VITE_API_URL`, `VITE_APP_ENV`. Only `VITE_` variables reach the browser.

Phase 12 adds `core.ops.config.validate_production_config()`: production fails fast (startup/validation) if `JWT_SECRET_KEY`, `DATABASE_URL`, or CORS origins are missing/insecure. **No insecure silent fallback.**

---

## 4. Security Posture

**Secure / addressed:**
- JWT signing secret is environment-first; the dev fallback is explicitly rejected in production.
- Password hashing uses bcrypt (rounds 12) with SHA-256 pre-hash for >72-byte passwords.
- API keys stored hashed (`sha256`) in the DB; inactive keys never authenticate.
- SQL echo gated behind `SQL_ECHO` env, off by default.
- No committed secrets found in `backend/` source scan (Phase 12 secret audit).
- No backend secrets (`GOOGLE_API_KEY`, `JWT_SECRET`) in `frontend/src`.
- Security headers applied at middleware: `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `X-Frame-Options: SAMEORIGIN`.

**Documented exception:** No restrictive `Content-Security-Policy` by default because the Vite SPA uses inline module scripts; a tailored CSP is recommended after verifying the built bundle (documented in `headers.py`).

**Noted (non-blocking, documented):** Python/Node dependencies are unpinned (`requirements.txt` has no `==`); full pinning is recommended for reproducible production builds.

---

## 5. Authentication

- Email/password signup + login (JWT bearer).
- Google OAuth login (backend handles exchange; no key in frontend source).
- JWT `HS256`, `exp` claim, 24h expiry, `sub` = email, `is_active` enforced at login and on each optional guard.
- Long-password pre-hash handled explicitly.
- API key auth via `X-API-Key` header (hashed, active-checked, `last_used` updated).
- `dependencies.get_current_user_optional` — fail-closed (returns `None` on invalid token/expiry, never fabricates identity).

Authentication is functional and not being replaced. The auth boundary is: JWT/API-key verified on the backend; frontend just stores and forwards the credential.

---

## 6. Authorization

Access tiers defined:

- **PUBLIC**: signup, login, google-login, `/health`, `/ready`, geocode, `/compute`, `/match` (base chart fields).
- **AUTHENTICATED_USER**: your own charts, saved data, `/compute` yogas (only computed for authenticated users), `/api-keys`.
- **MEMBER/DEVELOPER**: dynamic DSL / research lab endpoints (gated, read-only where applicable).
- **ADMIN**: not separately modeled in this single-owner deployment; administrative DB actions are outside the API surface.

Backend enforcement: `/compute` yogas are computed only for authenticated users (`routes/astro.py`); `/api-keys` are user-scoped; family charts are user-scoped (`routes/family.py` uses `user_id`). Frontend route hiding is NOT the security boundary — the backend enforces.

---

## 7. User Data Isolation

- `ChartData` and `APIKey` models carry a `user_id` foreign key.
- `core.ops.cache.chart_key(..., user=...)` embeds the user in the cache key, preventing cross-user cache leakage.
- `core.ops.cache.IsolatedCache` never shares private entries across users when the key builders are used.
- Multi-user isolation exercised in Phase 12 tests (users A/B/C with distinct charts and distinct cache keys; concurrent path same/different users).

---

## 8. PII Minimization

- `core.ops.logging_setup.PII_KEYS` redacts `date_of_birth`, `time_of_birth`, `latitude`, `longitude`, `mobile_number`, `password`, `token`, `secret`.
- `LOG.scrub()` redacts `password=`, `token=`, `secret=`, `Bearer`, and DB-url credentials in free text.
- `LOG.sanitize_mapping()` redacts PII keys in structured records.
- Health/log endpoints do not emit chart payloads, birth coords, or secrets.

---

## 9. Logging

- Structured records via `LOG.build_log_record()`: `request_id / endpoint / status / latency_ms / subsystem / error_category`.
- PII scrubbing built into `LOG.scrub()/sanitize_mapping()`.
- `get_logger()` returns per-name singletons with INFO default, no propagation.
- SQL echo is gated (off by default) so verbose SQL debug is not emitted in production.

---

## 10. Error Handling

- Phase 12 `core.ops.guards` provides safe size/JSON/enum/path validation raising typed exceptions (`OversizedPayload`, `UnsafePath`) rather than leaking raw tracebacks.
- Health/ops routes (`ops.py`, `health.py`) intentionally contain no `traceback`, no secret, no password reference — safe error surfaces.
- Existing API error taxonomy is preserved; Phase 12 adds safe guards without altering it.

---

## 11. Request Correlation

- `core.ops.request_id.new_request_id()` (uuid4 hex, 32 chars).
- `app.py` ASGI middleware sets `request.state.request_id` and echoes `X-Request-ID` header + sets security headers.
- **Explicitly documented:** request IDs are observability metadata; excluded from canonical fingerprints, golden outputs, regression outputs, and canonical-result cache keys.

---

## 12. Rate Limiting

- `core.ops.rate_limit.InMemoryRateLimiter` — token-bucket with per-class limits:
  - `auth` 20/60s, `chart` 60/60s, `expensive` 30/60s, `prediction` 30/60s, `research` 30/60s, `developer` 60/60s, `default` 120/60s.
- Per-key isolation; `reset()` API; window rollover.
- Purpose: protection, not a substitute for architectural performance (documented in module).

---

## 13. CORS

- Production origins come from `FRONTEND_ORIGINS` (comma list) or `FRONTEND_URL` (single), both via `config.effective_cors_origins()`.
- Wildcard `*` is only the **unconfigured** legacy default (dev parity) and is **rejected** by production validation.
- `app.py` wires CORS to `effective_cors_origins()`.

---

## 14. Security Headers

Applied in `app.py` `_ops_middleware`:
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Frame-Options: SAMEORIGIN`
- CSP intentionally omitted by default (documented exception; SPA uses inline module scripts). HSTS left to deployment HTTPS layer.

---

## 15. CSRF / XSS

- Token-based (JWT bearer / API key) auth; no cookie-based session CSRF surface.
- Frontend renders backend data; Phase 12 static audit checks for `eval(`/`Function(` absence in `frontend/src`.
- Research/evidence/developer text is DATA — validated, never executed (Phase 6A/9 DSL checks).

---

## 16. Injection Security

- `core.ops.guards` + `core.rules.dynamic.dsl.find_suspicious_text` + `core.research.security.is_text_attack_blocked` cover: DSL injection, research auto-promotion, source-verification spoofs, SQL, XSS, path traversal, oversize, malformed JSON.
- Hostile-input corpus exercised in Phase 12 test section 12/57.

---

## 17. Dependency Audit

**Python (`requirements.txt`)** — present: `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `pyswisseph`, `python-jose`, `bcrypt`, `httpx`, `google-generativeai`, `psycopg2` (implied). No `==` pins (documented risk; recommend pinning).

**Node (`frontend/package.json`)** — `react` ^18, `axios`, `react-router-dom`, `react-markdown`, `framer-motion`, `tailwindcss`, `vite` ^5, `eslint` ^8. No `swisseph`/ephemeris in dependencies.

No known-critical upgrading was performed; `==` pinning is a **documented recommendation** (dependency audit outcome), not an applied change, to avoid perturbing validated behavior.

---

## 18. Frontend Bundle Audit

- Built output present at `frontend/dist/`.
- JS bundles: `index-BB-1lhZV.js` (~199 KB), `vendor-1_e3Ttku.js` (~494 KB).
- Bundle scan confirms no `swisseph`, no `set_sid_mode` in shipped JS (no ephemeris in browser).
- No backend secrets in `frontend/src` or bundle.

**Pre-existing flagged ~1 MB asset:** `frontend/dist/assets/ganesha_circle-BZz3BMEW.png` (~1,028,496 bytes / 1.0 MB).
- **Determination: PRE-EXISTING, ACCEPTABLE (image asset, not code).** It is a static illustration resource loaded by the app, not part of the JS bundle, and not a backend leak or ephemeris. It is documented as an accepted pre-existing finding; optional future optimization could compress/replace it without touching UI logic.

---

## 19. Backend Performance

- `core/ops/health.readiness()` is deliberately cheap (imports, ephemeris path existence, rule-count lookup) and **never** runs full astrology — required so health checks stay cheap.
- Phase 12 performance test baselines (see `ASTROLIFE_V2_PHASE12_PERFORMANCE.md`): chart generation, vargas, strength, yogas, doshas, jaimini, research. All within measured bounds on the reference machine.
- No formula changes; optimization limited to non-canonical infrastructure.

---

## 20. Storage

- PostgreSQL via `DATABASE_URL`.
- `models.py`: `User`, `ChartData` (with `user_id`, index), `APIKey`; `nullable=False` constraints, `server_default` timestamps.
- `migrate_db.py` is **non-destructive** (only `DROP NOT NULL`), manual-invocation guarded, no `DROP TABLE`/`DELETE`.
- Connection via SQLAlchemy engine with `echo` gated by `SQL_ECHO`.

**Backup/recovery:** no automated backup/restore pipeline is present. Documented in `RELIABILITY.md` / `RUNBOOK.md` with recommended strategy (PostgreSQL `pg_dump`/`pg_restore`, retention, DR steps). Recovery capability is *recommended configuration*, not claimed-as-tested.

---

## 21. Health / Readiness

- `/health` — liveness (`status`).
- `/ready` (`routes/ops.py`) — readiness via `core.ops.health.readiness()`: config module, ephemeris path, swisseph import, parashari rule catalogue count.
- Distinct ALIVE vs READY; cheap; no sensitive data; no full calculation per request.

---

## 22. Observability

- Structured access log shape: request ID, endpoint, status, latency, subsystem, error category.
- Angular/metrics collection is not externalized; recommended external metrics/alerting documented (not fabricated).

---

## 23. Alerting

- No external alert infrastructure present. Recommended alerts (documented in `RUNBOOK.md`): high error rate, repeated calculation failures, DB failure, auth failure bursts, excessive latency, deployment failure, health failure.

---

## 24. Canonical Astrology Integrity

- Phase 12 integrity checks re-verify frozen anchors: JD, ayanamsha, ascendant, Moon longitude/nakshatra, Ketu exact opposition, Jaimini karakas, karakamsha/AL/UL, strength totals, yoga/dosha formations, dasha hierarchy.
- Canonical fingerprint = calculation profile + engine/catalogue versions (deterministic; excludes request IDs).

---

## 25. Version Compatibility

- `core/ops/version.py`: app 12.0.0, API `v1`, engine `core/calculation (Lahiri, Mean Node, Whole Sign)`, schema `6A/1.0.0`, rule catalogue `parashari-31/dosha-6/jaimini-12`, evidence `6D/1.0.0`, prediction `phase8/1.0.0`, research `phase9/1.0.0`.

---

## 26. API Backward Compatibility

- No frontend endpoint broken by Phase 12; ops are additive (`routes/ops.py` new `/ready`).
- Existing contracts (`/compute`, `/match`, auth, api-keys, family, dynamic, research) preserved.

---

## 27. Concurrency

- `core.calculation.varga.calculate_varga_position` identical across concurrent threads (Phase 12 test 17).
- Concurrent distinct-chart computation yields distinct JD / distinct ascendants with no shared-state races (test 37).
- Rate limiter is per-key isolated and thread-safe for its in-process use.

---

## 28. Thread / Process Safety

- No shared mutable canonical state introduced. Global caches in `core/ops/cache.IsolatedCache` are per-instance; canonical chart results are recomputed idempotently.
- Ephemeris usage remains deterministic and correctly configured (Lahiri, Mean Node, Whole Sign), isolated from user-controllable paths.

---

## 29. Ephemeris Safety

- Fixed `EPHE_PATH` from env (default `backend/ephe`), set once at app creation.
- Lahiri sidereal mode forced globally.
- No user-controllable filesystem path reaches ephemeris.

---

## 30. Filesystem Security

- `core.ops.guards.safe_join()` rejects path traversal (`../`, nested escapes); typed `UnsafePath`.
- Oversized payload/text/list limits (`MAX_JSON_BYTES`, `MAX_TEXT_FIELD`, `MAX_LIST_ITEMS`) bound file growth and uploads.
- No executable upload / unsafe extraction surface in normal flow.

---

## 31. Import / Export Security

- Research/evidence/rule packages are validated as DATA through Phase 6A/9 guards (suspicious-text detection, research namespace isolation `research://`, promotion gating).
- `guards.safe_json_loads()` rejects malformed JSON; `check_json_size()` bounds hostile payloads.
- No executable deserialization (no `pickle` of untrusted data).

---

## 32. Prediction Safety (Phase 8)

- `core/prediction/validation.py` carries `CERTAINTY_PATTERNS`, `SCORE_PATTERNS`.
- `TimingWindow` semantics preserved (uncertainty, `EVENT_WINDOW`); no fabricated event dates.
- Phase 12 static audit confirms no `probability`/`accuracy`/`p_value`/`confidence %` and no `guaranteed` language in pipeline/event_types.

---

## 33. Research Safety (Phase 9)

- `core/research/promotion.py` requires explicit `APPROVE` gate.
- Experimental namespace isolated via `research://`.
- No silent auto-promotion (Phase 12 test 23).
- Human review + promotion audit model preserved.

---

## 34. AI Safety (Phase 7)

- Agents operate read-only on provided facts through adapters; agent modules do not import `swisseph`/`generate_chart_facts` (Phase 12 test 24).
- `core/agents/golden.py` is explicitly documented as a fixture builder ("Fixture setup, not agent reasoning"), not a calculation authority.
- `agent_security.py` present.

---

## 35. Frontend Security

- No `eval(`/`Function(` in `frontend/src`.
- No secrets (`sk-`, `AKIA`, `GOOGLE_API_KEY`, `JWT_SECRET`) in source or bundle.
- Tokens stored/forked per the existing auth architecture; no backend secret reaches the browser.

---

## 36. Protected Routes

- Frontend route hiding is UI-only; backend enforces authorization at the API boundary (yogas gated on auth, api-keys/family user-scoped).
- Research/developer endpoints are not reachable by URL guessing alone without backend auth.

---

## 37. Deployment Hardening — see `ASTROLIFE_V2_PHASE12_DEPLOYMENT.md`

---

## 38. CI/CD — see `ASTROLIFE_V2_PHASE12_DEPLOYMENT.md` (no CI present; recommended release pipeline documented)

---

## 39–40. Release Gate / Golden Regression — see `ASTROLIFE_V2_PHASE12_TEST_REPORT.md` and `FINAL_REPORT.md`

---

## 41–51. Golden Anchors / E2E / Unknown / Multi-user / Concurrent / Determinism / Security Corpus / Static / Frontend / Backend Audits — see `ASTROLIFE_V2_PHASE12_TEST_REPORT.md` and `FINAL_REPORT.md`

---

## 52. Known Pre-Existing Findings (re-evaluated)

| # | Phase 11 finding | Phase 12 determination |
|---|---|---|
| 1 | 4 pre-existing security findings | Re-audited. Addressed/documented as non-blocking where applicable (see `SECURITY.md`). |
| 2 | ~1 MB asset (`ganesha_circle-*.png`, 1,028,496 B) | **PRE-EXISTING ACCEPTABLE** — static image, not code/ephemeris/secret; optional future optimization, does not block release. |
| 3 | Broken pre-existing lint script | Frontend `lint` script references ESLint with no lint config/plugin resolution verified for `jsx`; the Phase 11 finding is re-confirmed — the lint script is **documented as pre-existing and not part of release gate**; `build` is the validated production path. |

Also re-confirmed: pre-existing `chara dasha` vocabulary (token "chara dasha") guard failure in `dasha/profile.py`/`dasha/reference.py` dates from Phase 5F and is NOT caused by Phase 12 code; it is a documented pre-existing failure, not a Phase 12 regression.

---

## 53. Production Blockers

- **None identified** for Phase 12. All 16 HARD STOP conditions evaluated; none violated.
- Production configuration required variables are documented and enforced by fail-fast validation.

---

## 54. Recommendations (non-blocking)

1. Pin Python dependency versions (`requirements.txt` with `==`).
2. Add a tailored `Content-Security-Policy` after verifying the built SPA bundle.
3. Configure external metrics + alerting on a real deployment.
4. Configure + test PostgreSQL backup/restore (documented in RUNBOOK).
5. Optional: compress/replace the ~1 MB ganesha image.
6. Establish CI with the release gate documented in `DEPLOYMENT.md`.

---

**Audit conclusion:** The system is production-auditable; the aggregate architecture, security posture, auth/z model, PII handling, observability surface, and canonical-integrity checks satisfy the Phase 12 production requirements. Astrology semantics unchanged.
