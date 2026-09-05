# Astrolife V2 — Phase 12 Production Configuration

This document lists required/optional configuration for a production deployment. It deliberately does **not** include secret values.

---

## 1. Backend Environment Variables

| Variable | Required (prod) | Description |
|---|---|---|
| `ASTROLIFE_ENV` | ✅ | `production` (also `staging`/`development`). Fail-fast production gates apply when `production`. |
| `JWT_SECRET_KEY` | ✅ | JWT signing secret, **≥32 chars**, must NOT be a dev placeholder. Missing/insecure ⇒ startup/validation failure. |
| `DATABASE_URL` | ✅ | Production PostgreSQL URL. Must not use dev credentials. Missing ⇒ validation failure. |
| `FRONTEND_ORIGINS` | ✅ (or `FRONTEND_URL`) | Comma-separated allowed CORS origins. Wildcard rejected in production. |
| `FRONTEND_URL` | ✅ (or `FRONTEND_ORIGINS`) | Single frontend origin fallback for CORS. |
| `EPHE_PATH` | optional | Ephemeris directory (default `backend/ephe`). |
| `GOOGLE_API_KEY` | optional (AI) | Backend-only AI key; never shipped to frontend. |
| `SQL_ECHO` | optional | `true` enables SQL echo (off by default; keep off in prod). |

## 2. Frontend Configuration (public `VITE_` only)

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend base URL. **Required in production** — missing throws visibly rather than calling a wrong backend. |
| `VITE_APP_ENV` | Optional explicit mode override. |

**No backend secrets are ever set as `VITE_` vars.**

## 3. Secrets Management Rules

- Secrets live in the deployment environment / secret store only.
- Never commit secret values to source.
- Frontend must never receive backend secrets.
- `JWT_SECRET_KEY` rotation: sign/verify with the same value within a release; different secrets across envs means tokens do not cross-verify (documented).

## 4. CORS Configuration

- `development`: default wildcard accepted (legacy parity).
- `staging` / `production`: set `FRONTEND_ORIGINS` or `FRONTEND_URL`; wildcard rejected in production by `validate_production_config()`.

## 5. Rate Limits (baseline)

Per-key in-memory limits (`core/ops/rate_limit.LIMITS`, window 60 s):
- auth 20/60s, chart 60/60s, expensive 30/60s, prediction 30/60s, research 30/60s, developer 60/60s, default 120/60s.

## 6. Request Size Limits (`core/ops/guards`)

- JSON body ≤ 1,000,000 bytes
- text field ≤ 50,000 chars
- list ≤ 5,000 items

## 7. Logging Configuration

- Structured records: `request_id / endpoint / status / latency_ms / subsystem / error_category`.
- PII redaction enabled (`PII_KEYS`); SQL echo off by default. Production default level: INFO (not verbose debug).

## 8. Monitoring / Alerting

- Health: `/health` (liveness), `/ready` (readiness).
- External metrics + alerts are recommended configuration (see `RELIABILITY.md` / `RUNBOOK.md`); not fabricated as present.

## 9. Database / Storage

- PostgreSQL production instance via `DATABASE_URL`.
- Recommended backup/restore (see `RELIABILITY.md`), not present by default.

## 10. Versioning

Reference `core/ops/version.py`:
- app `12.0.0`, API `v1`, engine `core/calculation (Lahiri, Mean Node, Whole Sign)`, schema `6A/1.0.0`, rules `parashari-31/dosha-6/jaimini-12`, evidence `6D/1.0.0`, prediction `phase8/1.0.0`, research `phase9/1.0.0`.

---

## Validation

`core.ops.config.validate_production_config()` enforces the fail-fast production gates above. Missing `JWT_SECRET_KEY` / `DATABASE_URL` / CORS, short/placeholder JWT, dev DB creds, or wildcard origin all fail validation (see Phase 12 tests 2/30).
