"""
Operations routes — Phase 12 (additive only).

GET /ready — cheap readiness probe (imports, ephemeris path, rule counts).
Never runs full astrology per request. No sensitive data in responses.
"""
from fastapi import APIRouter

router = APIRouter(tags=["Operations"])


@router.get("/ready")
def readiness():
    try:
        from backend.core.ops import health as _health
    except ImportError:
        from core.ops import health as _health
    return _health.readiness()
