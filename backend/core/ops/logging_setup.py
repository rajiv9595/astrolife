"""
Phase 12 — structured production logging with PII minimization.
Logs request id / endpoint / status / latency / subsystem / error category.
Never logs passwords, tokens, secrets, or full private chart payloads.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict

_SCRUB_PATTERNS = [
    (re.compile(r"(?i)(password\s*[:=]\s*)(['\"]?)[^'\",\s}]+"), r"\1\2[REDACTED]"),
    (re.compile(r"(?i)(token\s*[:=]\s*)(['\"]?)[^'\",\s}]+"), r"\1\2[REDACTED]"),
    (re.compile(r"(?i)(secret\s*[:=]\s*)(['\"]?)[^'\",\s}]+"), r"\1\2[REDACTED]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-]+"), "Bearer [REDACTED]"),
    (re.compile(r"postgresql://[^:]+:[^@]+@"), "postgresql://[REDACTED]@"),
]

# Birth-data keys that must never enter logs/telemetry.
PII_KEYS = ("password", "password_hash", "token", "secret", "time_of_birth",
            "date_of_birth", "latitude", "longitude", "mobile_number")


def scrub(text: str) -> str:
    out = str(text)
    for rx, repl in _SCRUB_PATTERNS:
        out = rx.sub(repl, out)
    return out


def sanitize_mapping(mapping: Dict[str, Any]) -> Dict[str, Any]:
    return {k: ("[REDACTED]" if k in PII_KEYS else v) for k, v in mapping.items()}


def build_log_record(request_id: str, endpoint: str, status: int | str,
                     latency_ms: float, subsystem: str = "",
                     error_category: str = "") -> Dict[str, Any]:
    return {"request_id": request_id, "endpoint": endpoint, "status": status,
            "latency_ms": round(float(latency_ms), 2), "subsystem": subsystem,
            "error_category": error_category}


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"astrolife.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
