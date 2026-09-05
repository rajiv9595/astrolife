"""
Phase 5H — Golden Snapshot Capture + Regression.

Captures deterministic timing evaluation output as golden JSON snapshots.
Verifies byte-identical reproduction across runs.

50 full evaluations per profile must produce byte-identical serialized JSON.
No datetime.now() in deterministic core — only at API boundary.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import CandidateEvaluation


def _serialize_evaluation(eval_result: CandidateEvaluation) -> str:
    """Deterministic JSON serialization of a CandidateEvaluation.

    Sorted keys, no timestamps hidden in IDs, no floating-point drift.
    """
    data = eval_result.model_dump(mode="json")
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _hash_snapshot(serialized: str) -> str:
    """SHA-256 hash of serialized evaluation."""
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def capture_golden_snapshot(
    eval_result: CandidateEvaluation,
    snapshot_path: Path,
) -> Dict[str, Any]:
    """Capture a golden snapshot of a timing evaluation.

    Returns metadata: {hash, path, generated_at, total_candidates}.
    The snapshot file contains the deterministic JSON.
    """
    serialized = _serialize_evaluation(eval_result)
    snapshot_hash = _hash_snapshot(serialized)

    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(serialized, encoding="utf-8")

    return {
        "hash": snapshot_hash,
        "path": str(snapshot_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_candidates": eval_result.total_candidates,
        "profile_id": eval_result.profile_id,
    }


def verify_golden_snapshot(
    eval_result: CandidateEvaluation,
    snapshot_path: Path,
) -> Dict[str, Any]:
    """Verify a timing evaluation matches its golden snapshot.

    Returns {match: bool, expected_hash, actual_hash, detail}.
    """
    if not snapshot_path.exists():
        return {
            "match": False,
            "expected_hash": None,
            "actual_hash": None,
            "detail": f"Snapshot file not found: {snapshot_path}",
        }

    expected_text = snapshot_path.read_text(encoding="utf-8")
    expected_hash = _hash_snapshot(expected_text)

    actual_text = _serialize_evaluation(eval_result)
    actual_hash = _hash_snapshot(actual_text)

    match = expected_hash == actual_hash
    detail = "Byte-identical" if match else "Mismatch detected"

    return {
        "match": match,
        "expected_hash": expected_hash,
        "actual_hash": actual_hash,
        "detail": detail,
    }


def verify_determinism(
    evaluation_fn,
    profile_id: str,
    n_runs: int = 50,
) -> Dict[str, Any]:
    """Verify N consecutive evaluations produce byte-identical JSON.

    evaluation_fn must be a callable that takes no args and returns
    a CandidateEvaluation. All calls must use the same inputs.

    Returns {deterministic: bool, n_runs, unique_hashes: int, detail}.
    """
    hashes: List[str] = []
    for _ in range(n_runs):
        result = evaluation_fn()
        serialized = _serialize_evaluation(result)
        hashes.append(_hash_snapshot(serialized))

    unique = set(hashes)
    return {
        "deterministic": len(unique) == 1,
        "n_runs": n_runs,
        "unique_hashes": len(unique),
        "detail": (
            f"{'DETERMINISTIC' if len(unique) == 1 else 'NON-DETERMINISTIC'}: "
            f"{n_runs} runs, {len(unique)} unique hash(es)"
        ),
    }
