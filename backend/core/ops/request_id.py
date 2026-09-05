"""
Phase 12 — request correlation IDs. Generated at request boundaries only.
Observability metadata: NEVER part of astrology calculations, canonical
fingerprints, golden outputs, regression outputs, or cache keys for
canonical results.
"""
from __future__ import annotations

import uuid

CANONICAL_EXCLUSION_NOTE = (
    "request_id is observability metadata and is excluded from all "
    "canonical fingerprints, golden outputs, and regression outputs."
)


def new_request_id() -> str:
    return uuid.uuid4().hex
