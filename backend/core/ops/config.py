"""
Phase 12 — environment configuration + fail-fast production validation.
No insecure silent fallbacks: missing production secrets = startup failure,
never a "development-secret".
"""
from __future__ import annotations

import os
from typing import Dict, List

ENV_MODES = ("development", "staging", "production")


def app_env() -> str:
    mode = os.getenv("ASTROLIFE_ENV", "development").strip().lower()
    return mode if mode in ENV_MODES else "development"


def is_production() -> bool:
    return app_env() == "production"


REQUIRED_PROD_VARS = ("JWT_SECRET_KEY", "DATABASE_URL")
# CORS origin requirement is enforced separately (FRONTEND_ORIGINS or FRONTEND_URL).

# Dev-only fallbacks. The literal below is intentionally NOT a usable
# production secret and is rejected by validate_production_config().
DEV_JWT_FALLBACK = "dev-only-insecure-fallback-not-for-production"


def jwt_secret() -> str:
    return os.getenv("JWT_SECRET_KEY", DEV_JWT_FALLBACK)


def effective_cors_origins() -> List[str]:
    """Explicit origins in production; legacy wildcard only when unconfigured
    (dev parity). Unconfigured production is flagged by the validator."""
    raw = os.getenv("FRONTEND_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    single = os.getenv("FRONTEND_URL", "").strip()
    if single:
        return [single]
    return ["*"]


def sql_echo_enabled() -> bool:
    return os.getenv("SQL_ECHO", "false").strip().lower() in ("1", "true", "yes")


def validate_production_config(env: Dict[str, str] | None = None) -> Dict[str, object]:
    """Fail fast on missing/insecure production configuration."""
    src = dict(env) if env is not None else dict(os.environ)
    errors: List[str] = []
    mode = (src.get("ASTROLIFE_ENV", "development") or "").strip().lower()
    if mode != "production":
        return {"mode": mode or "development", "valid": True, "errors": [],
                "note": "production gates apply only when ASTROLIFE_ENV=production"}
    for var in REQUIRED_PROD_VARS:
        if not (src.get(var) or "").strip():
            errors.append(f"missing required production variable: {var}")
    jwt = (src.get("JWT_SECRET_KEY") or "")
    if jwt and len(jwt) < 32:
        errors.append("JWT_SECRET_KEY must be at least 32 characters")
    if "development-secret" in jwt or "change-in-production" in jwt or jwt == DEV_JWT_FALLBACK:
        errors.append("JWT_SECRET_KEY uses a development placeholder")
    db = src.get("DATABASE_URL", "")
    if db and ("postgres:postgres@" in db or "password" in db.lower() and "localhost" in db):
        errors.append("DATABASE_URL uses development credentials")
    origins = [o.strip() for o in (src.get("FRONTEND_ORIGINS", "") or "").split(",") if o.strip()]
    if not origins:
        single = (src.get("FRONTEND_URL") or "").strip()
        if not single:
            errors.append("CORS origins unconfigured (FRONTEND_ORIGINS or FRONTEND_URL required)")
        elif single == "*":
            errors.append("CORS wildcard origin not allowed in production")
    return {"mode": "production", "valid": len(errors) == 0, "errors": errors}
