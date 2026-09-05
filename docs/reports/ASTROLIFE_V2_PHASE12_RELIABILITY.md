# Astrolife V2 — Phase 12 Reliability

Astrology semantics FROZEN; this document covers production reliability, determinism, concurrency, storage, backup, health, and observability.

---

## 1. Health & Readiness

- `/health` — liveness (`{"status": "alive"}` + app `{"status":"active"}` root check).
- `/ready` — readiness via `core.ops.health.readiness()`:
  - config module import
  - ephemeris path existence
  - `swisseph` import
  - parashari rule catalogue count

Readiness is **cheap** — it never runs full astrology per request. ALIVE ≠ READY distinction is explicit.

## 2. Canonical Truth-Layer Health

Phase 12 verifies canonical integrity at startup/CI/release (not per request):
- Ketu exact opposition invariant
- longitude range (0–360)
- sign/longitude consistency
- D1 determinism (fingerprint identical across runs)
- varga availability
- dasha availability
- schema compatibility (versions in `core/ops/version.py`)

## 3. Canonical Fingerprint

Deterministic fingerprint composed of: calculation profile + calculation engine version + rule catalogue version + evidence catalogue version + prediction catalogue version + research catalogue version. Request IDs are **excluded** (observability only).

## 4. Determinism (50-run)

- Critical golden pipeline run 50× yields **one unique canonical fingerprint** and byte-identical structured output (Phase 12 test 27).

## 5. Concurrency & Thread Safety

- `calculate_varga_position` identical across 8 concurrent threads (test 17).
- Concurrent distinct charts → distinct JD + distinct ascendants, no races (test 37).
- No shared mutable canonical state. `IsolatedCache` is per-instance; canonical results recomputed idempotently.
- Ephemeris: fixed `EPHE_PATH`, Lahiri Mean-Node Whole-Sign, deterministic, isolated from user-controllable paths.

## 6. Caching & Invalidation

- Cross-user isolation enforced by cache-key embedding user.
- Dynamic data binds evaluation datetime + profile ⇒ changed eval date updates (test 14/33).
- Per-key + prefix invalidation; research keys bind package id/version/fingerprint.

## 7. Storage

- PostgreSQL via `DATABASE_URL`; SQLAlchemy engine; `echo` gated by `SQL_ECHO` (off by default).
- Schema: `User`, `ChartData` (`user_id` FK + index), `APIKey`; `nullable=False`, `server_default`.
- `migrate_db.py` non-destructive (only `DROP NOT NULL`), manual invocation, no destructive statements.
- Connection pooling via SQLAlchemy; transaction boundaries per request.

## 8. Backup / Recovery

**Current state:** No automated backup/restore pipeline exists in the repo.

**Recommended strategy (documented, to be configured at deployment):**
1. PostgreSQL `pg_dump` on a schedule (daily full + hourly WAL).
2. Off-site/object-storage retention (e.g., 30 days daily + 6 monthly).
3. Documented restore procedure (`pg_restore`, verification query).
4. Periodic restore drill to confirm recoverability.
5. DR: re-deploy application from release manifest with same env; restore DB.

Recovery is **recommended configuration**, not claimed-as-tested (per Phase 12 §27).

## 9. Observability

- Structured access-log shape: `request_id / endpoint / status / latency_ms / subsystem / error_category`.
- PII scrubbed; a birth-data keys never logged.
- External metrics (latency percentiles, error rate, endpoint usage, calculation/auth failures, rate-limit events) are **recommended configuration** — no external collector is present.

## 10. Alerting (recommended configuration)

Recommended alerts at deployment:
- High error rate (e.g., >5% over 5 min)
- Repeated calculation failures
- Database failure / connection pool exhaustion
- Auth failure bursts (possible credential stuffing)
- Excessive latency (p95 > threshold)
- Deployment failure (CI gate)
- Health/readiness failure

These are documented recommendations for the real deployment, not fabricated as present.

## 11. Failure Handling

- Errors are structured, safe, non-sensitive (no stack traces/passwords/SQL to users).
- Typed guards (`OversizedPayload`, `UnsafePath`) reject hostile input cleanly.

## 12. Version Compatibility & Migration Safety

- API `v1`; schema `6A/1.0.0`; catalogue versions pinned in `version.py`.
- Frontend/backend contracts preserved; no endpoint broken by Phase 12 (additive ops only).
- Any future migration: reversible-where-practical, tested, non-destructive, documented.

---

## Reliability Conclusion

Deterministic canonical output, isolation-safe caching, thread-safe ephemeris/calculation, cheap health/readiness, structured and PII-safe logging, and a documented (to-be-configured) backup/DR plan. No hard-stop reliability condition violated.
