# Astrolife V2 — Phase 12 Security

**Status: PASS** (with documented non-blocking findings)

Astrology semantics unchanged. Security hardening is additive.

---

## 1. Secrets Management

- **Scan performed** across the repository (Python + JSON source in `backend/`, `frontend/src`) for: `sk-*`, `AKIA*`, private-key blocks, `ghp_*`, `xox*` tokens, `postgresql://user:pass@` URLs, JWT secrets, service credentials.
- **Result:** no committed secrets in source.
- No backend secret (`GOOGLE_API_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`) is referenced from `frontend/src` or shipped in the bundle.
- Frontend receives only public `VITE_` variables.

## 2. JWT / Authentication

- `HS256`, 24h expiry `exp` claim, `sub` = email, `is_active` enforced.
- Secret from `JWT_SECRET_KEY` (env-first). Dev fallback is explicitly marked and **rejected** by `validate_production_config()` in production.
- Passwords: bcrypt rounds 12; >72-byte passwords pre-hashed with SHA-256.
- API keys stored hashed (`sha256`); inactive keys never authenticate; `last_used` tracked.
- Fail-closed optional guard: invalid/expired token ⇒ `None`, never a fabricated identity.

## 3. Authorization / Isolation

- `/compute` yogas computed only for authenticated users.
- `/api-keys`, `/family` user-scoped via backend (`user_id` FK, backend-enforced).
- Cache keys embed user ⇒ cross-user leakage structurally impossible when key builders are used.
- Route hiding is UI-only; backend is the authority.

## 4. PII / Logging

- `PII_KEYS` redact birth data, coordinates, mobile, password, token, secret in structured records.
- `scrub()` redacts secrets / bearer / DB-url credentials in free text.
- Health/ops endpoints: no chart payloads, no birth coords, no secrets, no `traceback`.

## 5. Injection

- DSL / research / evidence / source / AI / prediction text is DATA — validated, never executed.
- `find_suspicious_text` + `is_text_attack_blocked` + guards cover: prompt injection, auto-promotion spoofs, source-verification spoofs, SQL, XSS, path traversal, oversize, malformed JSON.
- `safe_join` rejects path traversal; `safe_json_loads` rejects malformed JSON; size limits bound hostile payloads.

## 6. CORS

- Production origins explicit (`FRONTEND_ORIGINS` / `FRONTEND_URL`); wildcard is legacy-unconfigured-only and **rejected** in production.

## 7. Security Headers

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Frame-Options: SAMEORIGIN`
- CSP omitted by default (documented exception: inline module scripts in the Vite SPA); tailored CSP recommended after bundle verification.
- HSTS delegated to deployment HTTPS layer in production.

## 8. CSRF / XSS

- Token (JWT/API-key) auth ⇒ no cookie CSRF surface.
- No `eval(`/`Function(` in `frontend/src`.
- Backend data rendered, not executed.

## 9. Prediction / Research / AI Safety

- No probability/accuracy/`p_value`/confidence% in prediction pipeline; no `guaranteed` event language; `TimingWindow`/uncertainty preserved.
- Research: no silent auto-promotion; explicit `APPROVE` gate; `research://` isolation.
- Agents: read-only on provided facts; no `swisseph`/`generate_chart_facts` import in agent reasoning; `agent_security.py` present.

## 10. Filesystem / Size

- `MAX_JSON_BYTES` 1 MB, `MAX_TEXT_FIELD` 50k chars, `MAX_LIST_ITEMS` 5k.
- `safe_join` blocks traversal / overwrite.
- No executable deserialization (`pickle`) of untrusted data.

## 11. Final Static Audit

Searched for: secrets, debug endpoints, `eval`/`exec`, arbitrary deserialization, shell execution, path traversal, hardcoded production `localhost`, insecure CORS, frontend astrology calculation, duplicated astrology engines, prediction probability, guaranteed language, research auto-promotion.

- Legitimate/test/documentation occurrences (e.g., `find_suspicious_text` corpus, `eval(x)` as a *test input to be blocked*, fixture builders) were classified separately and are not exposures.
- Frontend bundle contains zero ephemeris (`swisseph`/`set_sid_mode` absent).

---

## Findings Summary

| # | Finding | Classification |
|---|---|---|
| F1 | Python deps unpinned (`requirements.txt` no `==`) | NON-BLOCKING / DOCUMENTED recommendation |
| F2 | ~1 MB ganesha PNG asset in `dist` | NON-BLOCKING / PRE-EXISTING ACCEPTABLE (image, not code) |
| F3 | No restrictive CSP by default | NON-BLOCKING / DOCUMENTED exception (recommend post-build CSP) |
| F4 | Broken pre-existing lint script (jsx) | NON-BLOCKING / PRE-EXISTING (not in release gate; `build` is the validated path) |
| F5 | Backup/restore not automated | NON-BLOCKING / DOCUMENTED recommendation (see RELIABILITY/RUNBOOK) |

**No critical or unresolved critical findings.**

---

## Security Sign-Off

```
SECURITY: PASS
(no unresolved critical findings; non-blocking findings documented above)
```
