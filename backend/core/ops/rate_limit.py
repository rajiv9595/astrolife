"""
Phase 12 — in-memory token-bucket rate limiting (pure logic; framework
wiring lives in middleware factory with graceful degradation).
Protects auth, chart creation, expensive calculations, prediction,
research, and developer endpoints. Not a substitute for real performance.
"""
from __future__ import annotations

import time
from typing import Dict, Tuple

# endpoint class -> (max_requests, window_seconds)
LIMITS: Dict[str, Tuple[int, int]] = {
    "auth": (20, 60),
    "chart": (60, 60),
    "expensive": (30, 60),
    "prediction": (30, 60),
    "research": (30, 60),
    "developer": (60, 60),
    "default": (120, 60),
}


class InMemoryRateLimiter:
    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._buckets: Dict[str, list] = {}

    def check(self, key: str, klass: str = "default") -> Dict[str, object]:
        limit, window = LIMITS.get(klass, LIMITS["default"])
        now = self._clock()
        stamps = [t for t in self._buckets.get(key, []) if now - t < window]
        if len(stamps) >= limit:
            retry = max(0.0, window - (now - stamps[0]))
            self._buckets[key] = stamps
            return {"allowed": False, "retry_after": round(retry, 2), "limit": limit}
        stamps.append(now)
        self._buckets[key] = stamps
        return {"allowed": True, "retry_after": 0.0, "limit": limit}

    def reset(self, key: str | None = None) -> None:
        if key is None:
            self._buckets.clear()
        else:
            self._buckets.pop(key, None)
