"""
Phase 12 — liveness vs readiness. Readiness checks are CHEAP (imports,
ephemeris path, registry counts). Never runs full astrology per request;
canonical truth health belongs to startup/CI/release validation.
"""
from __future__ import annotations

import os
from typing import Any, Dict


def liveness() -> Dict[str, str]:
    return {"status": "alive"}


def readiness() -> Dict[str, Any]:
    checks: Dict[str, Any] = {}
    try:
        import backend.config as _cfg  # noqa: F401
        checks["config_module"] = "ok"
    except Exception:
        try:
            import config as _cfg2  # noqa: F401
            checks["config_module"] = "ok"
        except Exception as e:
            checks["config_module"] = f"missing: {e}"
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ephe = os.path.join(os.path.dirname(base), "ephe")
    checks["ephemeris_path"] = "ok" if os.path.isdir(ephe) else "missing"
    try:
        import swisseph  # noqa: F401
        checks["swisseph"] = "ok"
    except Exception as e:
        checks["swisseph"] = f"missing: {e}"
    try:
        from backend.core.rules.parashari import catalog as _pc
        checks["parashari_rules"] = str(len(_pc.get_parashari_rules()))
    except Exception:
        try:
            from core.rules.parashari import catalog as _pc2
            checks["parashari_rules"] = str(len(_pc2.get_parashari_rules()))
        except Exception as e:
            checks["parashari_rules"] = f"missing: {e}"
    ready = all(v == "ok" or (isinstance(v, str) and v.isdigit()) for v in checks.values())
    return {"ready": ready, "checks": checks}
