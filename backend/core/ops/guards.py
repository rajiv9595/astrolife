"""
Phase 12 — input/filesystem guards: request size limits, safe JSON parsing,
path-traversal prevention, enum validation. Research/evidence/developer
text stays DATA (validated, never executed) via existing Phase 6A/9 checks.
"""
from __future__ import annotations

import json
import os
from typing import Any, List

MAX_JSON_BYTES = 1_000_000
MAX_TEXT_FIELD = 50_000
MAX_LIST_ITEMS = 5_000


class OversizedPayload(ValueError):
    pass


class UnsafePath(ValueError):
    pass


def check_json_size(payload: bytes | str) -> None:
    n = len(payload) if isinstance(payload, (bytes, str)) else 0
    if n > MAX_JSON_BYTES:
        raise OversizedPayload(f"payload {n} bytes exceeds {MAX_JSON_BYTES}")


def check_text_field(value: str, name: str = "field") -> None:
    if isinstance(value, str) and len(value) > MAX_TEXT_FIELD:
        raise OversizedPayload(f"{name} exceeds {MAX_TEXT_FIELD} chars")


def check_list_size(values: list, name: str = "list") -> None:
    if isinstance(values, list) and len(values) > MAX_LIST_ITEMS:
        raise OversizedPayload(f"{name} exceeds {MAX_LIST_ITEMS} items")


def safe_json_loads(payload: str) -> Any:
    check_json_size(payload)
    try:
        return json.loads(payload)
    except json.JSONDecodeError as e:
        raise ValueError(f"malformed JSON: {e}")


def safe_join(base_dir: str, *parts: str) -> str:
    joined = os.path.normpath(os.path.join(base_dir, *parts))
    if os.path.commonpath([os.path.abspath(joined), os.path.abspath(base_dir)]) != os.path.abspath(base_dir):
        raise UnsafePath(f"path traversal rejected: {parts!r}")
    return joined


def validate_enum(value: str, allowed: List[str], name: str = "value") -> str:
    if value not in allowed:
        raise ValueError(f"invalid {name} {value!r}; allowed: {sorted(allowed)}")
    return value
