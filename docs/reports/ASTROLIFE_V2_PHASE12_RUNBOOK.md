# Astrolife V2 — Phase 12 Production Runbook

Astrology semantics FROZEN. Operational procedures for the production deployment.

---

## 1. Deploy

**Frontend (Vercel):**
1. Build: `cd frontend && npm run build` (output `frontend/dist`).
2. Ensure `VITE_API_URL` (and `VITE_APP_ENV`) set for the target environment.
3. Deploy `frontend/dist` via existing Vercel SPA workflow (`vercel.json` rewrites to `/index.html`).
4. Verify `/` loads and `VITE_API_URL` is reachable.

**Backend:**
1. Set required vars (see `PRODUCTION_CONFIG.md`): `ASTROLIFE_ENV=production`, `JWT_SECRET_KEY`, `DATABASE_URL`, `FRONTEND_ORIGINS`/`FRONTEND_URL`.
2. Launch `uvicorn backend.app:app`.
3. Confirm startup (tables created), `/health` alive, `/ready` ready.

## 2. Rollback

- **Frontend:** redeploy last known-good build/pin prior `dist`. (SPA static.)
- **Backend:** redeploy last known-good image/build. Environment must match the release manifest being rolled back to.
- **DB:** restore from backup if a data-layer issue (see §6).

## 3. Health Check

- `GET /health` → `{"status": "alive"}` (liveness).
- `GET /ready` → `{"ready": true, "checks": {...}}` (readiness: config module, ephemeris path, swisseph, parashari rule count).

## 4. Logs

- Structured access records: `request_id / endpoint / status / latency_ms / subsystem / error_category`.
- PII scrubbed; no birth coords/secrets in logs.
- Correlate failures via `X-Request-ID` (echoed in headers).

## 5. Common Failures

| Symptom | Likely cause | Action |
|---|---|---|
| `/health` down | app crash / host down | restart; check logs |
| `/ready` `ready:false` | ephemeris path missing / swisseph import fail / rule catalogue missing | check `EPHE_PATH`, deps |
| Auth fails in production | `JWT_SECRET_KEY` mismatch / placeholder | set proper ≥32-char secret; tokens don't cross-verify between secrets (documented) |
| CORS errors | `FRONTEND_ORIGINS`/`FRONTEND_URL` missing or mismatch | set correct origin(s); wildcard rejected in production |
| DB connection errors | bad `DATABASE_URL` | fix URL; check reachability/creds |
| Oversized request rejected | payload > limits | reduce payload (limits: JSON 1 MB, field 50k, list 5k) |
| Slow strength computation | inherent (~1.2 s) | not a defect; acceptable server-side |

## 6. Database Recovery

1. Restore from fail-fast backup (`pg_restore` of latest `pg_dump`).
2. Verify row counts + a canonical chart recompute.
3. Re-deploy backend with matching env.
- Strategy (to be configured): daily `pg_dump` + hourly WAL, 30-day daily + 6 monthly retention, periodic restore drill. Recovery is recommended config, not claimed-as-tested.

## 7. Security Incident Response

1. Triage severity; if PII/credential exposure suspected → rotate `JWT_SECRET_KEY`, invalidate API keys, revoke sessions.
2. Capture `X-Request-ID` correlated logs.
3. Apply static/bundle scan (see `SECURITY.md` §11) to confirm no regression.
4. Roll back to last known-good release if a code defect.
5. Record incident; escalate per environment owner policy.

## 8. Dependency Outage

- If a runtime dependency fails (DB, AI provider, ephemeris), `/ready` reflects the failure; health/alerting triggers.
- AI provider (Gemini) outage → AI features degrade; canonical astrology still computes (independent of AI).
- Ephemeris/swisseph failure → astrology unavailable; block/rollback (astrology is core).

## 9. Astrology Calculation Regression Response

**Critical astrology regression triggers:**
```
STOP RELEASE
→ identify first divergence (compare against golden data + manifest)
→ restore last known-good version
```

1. Run accepted regression suite (baseline: 105,762 executed / 105,724 unique / 0 failures).
2. Re-verify frozen golden anchors (JD, ayanamsha, ascendant, Moon, Ketu opposition, Jaimini karakas, strength, yoga/dosha, dasha).
3. If divergence → revert to last-known-good and re-validate.
4. Do not introduce new astrology semantics to "fix" a regression.

## 10. Alerting (recommended)

Configure external alerts: high error rate, repeated backend/calculation failures, DB failure, auth failure bursts, excessive latency, deployment failure, health failure. (External alert infrastructure not present; to be configured at deployment.)
