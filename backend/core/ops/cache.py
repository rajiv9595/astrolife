"""
Phase 12 — isolated cache. Keys always bind chart identity (+ evaluation
datetime + profile for dynamic data). No global caching of private data;
per-key invalidation; cross-user contamination structurally impossible
when callers use the key builders.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def chart_key(year: int, month: int, day: int, hour: int, minute: int,
              lat: float, lon: float, tz: str, user: str = "") -> str:
    return "|".join(["chart", str(year), str(month), str(day), str(hour),
                     str(minute), str(lat), str(lon), tz, user])


def dynamic_key(base: str, evaluation_iso: str, profile: str = "default") -> str:
    return "|".join(["dynamic", base, evaluation_iso or "now", profile])


def research_key(package_id: str, package_version: str, fingerprint: str) -> str:
    return "|".join(["research", package_id, package_version, fingerprint])


class IsolatedCache:
    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def put(self, key: str, value: Any) -> None:
        self._store[key] = value

    def invalidate(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def invalidate_prefix(self, prefix: str) -> int:
        doomed = [k for k in self._store if k.startswith(prefix)]
        for k in doomed:
            del self._store[k]
        return len(doomed)

    def __len__(self) -> int:
        return len(self._store)
