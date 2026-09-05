"""
Phase 8 — provenance (§37). Every candidate traces:

prediction -> hypothesis -> signals -> canonical rule/dasha/transit/Jaimini
result -> canonical facts -> evidence/dependencies.

No unsupported prediction may enter the canonical result: hypotheses with
empty supporting ancestry and no supplied evidence degrade to
EVIDENCE_INSUFFICIENT/UNKNOWN, never to a bare claim.
"""
from __future__ import annotations

from typing import Any, Dict, List


def build_hypothesis_provenance(hypothesis: Any, definition: Any,
                                request: Any) -> Dict[str, Any]:
    signals = hypothesis.signals if hasattr(hypothesis, "signals") else []
    return {
        "event_id": definition.event_id,
        "event_version": definition.version,
        "request_id": request.request_id,
        "profile": request.prediction_profile,
        "traditions": sorted(definition.tradition_constraints),
        "signals": sorted(s.signal_id for s in signals),
        "signal_origins": sorted({s.provenance.get("origin", "") for s in signals}),
        "rule_versions": sorted({s.provenance.get("rule_version", "")
                                 for s in signals
                                 if s.provenance.get("rule_version")}),
        "facts": sorted({a for s in signals for a in (s.ancestry or [])}),
        "evidence": sorted({e for s in signals for e in (s.evidence or [])}),
        "conflicts": list(hypothesis.conflicts) if hasattr(hypothesis, "conflicts") else [],
        "unknowns": list(hypothesis.unknowns) if hasattr(hypothesis, "unknowns") else [],
    }


def get_prediction_provenance(result: Any) -> Dict[str, Any]:
    return {
        "request_id": result.request.request_id,
        "profile": result.profile,
        "input_fingerprint": result.input_fingerprint,
        "output_fingerprint": result.output_fingerprint,
        "candidates": [
            {"hypothesis_id": c.hypothesis_id,
             "provenance": dict(c.provenance) if isinstance(c.provenance, dict)
             else c.provenance}
            for c in result.candidates],
    }


def get_prediction_snapshot(result: Any) -> Dict[str, Any]:
    import hashlib
    import json
    payload = json.dumps(result.model_dump(mode="json"), sort_keys=True,
                         separators=(",", ":"))
    return {"snapshot": json.loads(payload),
            "snapshot_fingerprint": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "result_fingerprint": result.output_fingerprint}
