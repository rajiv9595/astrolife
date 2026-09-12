"""
Canonical Dosha Adapter — Production adapter: canonical Dosha engine
-> legacy-compatible dosha response shapes.

NO ASTROLOGY IS COMPUTED HERE. Every value originates from:
- backend.core.rules.doshas.catalog.evaluate_all_doshas (canonical dosha
  evaluation: formation, severity, cancellation, mitigation, evidence,
  provenance over RuleContext facts).

This module ONLY projects canonical DoshaResult entries into the response
shapes consumed by the frontend (MangalDoshaCard, AdvancedDoshasCard) and AI
context:
- `mangal_dosha`: {has_dosha, verdict, details:{Lagna,Moon,Venus}, ...}
- `advanced_doshas`: {kala_sarpa_dosha:{...}, pitru_dosha:{...}}
- `doshas`: full canonical list (additive).
"""

from typing import Any, Dict, List, Optional

from backend.core.rules.doshas.catalog import (
    evaluate_all_doshas, create_dosha_evaluator, DOSHA_RULE_IDS,
)
from backend.core.rules.context import RuleContext
from backend.core.calculation.pipeline import ChartFacts


MANGLIK_REF_IDS = {
    "Lagna": "DOSHA.MANGLIK.LAGNA_CLASSICAL",
    "Moon": "DOSHA.MANGLIK.MOON_REFERENCE",
    "Venus": "DOSHA.MANGLIK.VENUS_REFERENCE",
}

_SEV_RANK = {"NONE": 0, "LOW": 1, "MODERATE": 2, "HIGH": 3, "UNKNOWN": 0}


def _ev_list(result: Any) -> List[Any]:
    return list(getattr(result, "evidence", []) or [])


def _ev_significance(ev: Any) -> str:
    sig = getattr(ev, "significance", None)
    if sig:
        return str(sig)
    if isinstance(ev, dict):
        return str(ev.get("significance", ""))
    return ""


def _ev_details(ev: Any) -> Dict[str, Any]:
    det = getattr(ev, "details", None)
    if isinstance(det, dict):
        return det
    if isinstance(ev, dict) and isinstance(ev.get("details"), dict):
        return ev["details"]
    return {}


def _ev_value(ev: Any) -> Any:
    val = getattr(ev, "value", None)
    if val is None and isinstance(ev, dict):
        val = ev.get("value")
    return val


def _is_full_cancel(ev: Any) -> bool:
    return bool(_ev_details(ev).get("is_full"))


def _has_cancel_type(ev: Any) -> bool:
    return bool(_ev_details(ev).get("cancellation_type"))


def evaluate_canonical_doshas(
    chart_facts: ChartFacts,
    strength_report: Optional[Any] = None,
    varga_facts: Optional[Dict[str, Any]] = None,
    dynamic_state: Optional[Any] = None,
    evaluation_datetime: Optional[Any] = None,
):
    """Evaluate all canonical doshas. Raises on engine failure (caller falls back)."""
    context = RuleContext(
        chart_facts=chart_facts,
        strength_report=strength_report,
        varga_facts=varga_facts or {},
        dynamic_state=dynamic_state,
        evaluation_datetime=evaluation_datetime,
    )
    return evaluate_all_doshas(context, create_dosha_evaluator())


def _mars_house_from_ref(result: Any) -> Optional[int]:
    """Extract Mars' house counted from the reference point (formation evidence)."""
    for ev in _ev_list(result):
        det = _ev_details(ev)
        if "mars_from_ref" in det:
            try:
                return int(det["mars_from_ref"])
            except (TypeError, ValueError):
                return None
        val = _ev_value(ev)
        if isinstance(val, dict) and "mars_from_ref" in val:
            try:
                return int(val["mars_from_ref"])
            except (TypeError, ValueError):
                return None
    return None


def _cancellation_reasons(result: Any, full_only: bool = True) -> List[str]:
    reasons = []
    for ev in _ev_list(result):
        if not _has_cancel_type(ev):
            continue
        if full_only and not _is_full_cancel(ev):
            continue
        sig = _ev_significance(ev)
        if sig and sig not in reasons:
            reasons.append(sig)
    return reasons


def build_mangal_dosha_block(dosha_set: Any) -> Dict[str, Any]:
    """Project the three canonical Manglik results to the MangalDoshaCard shape."""
    by_id = {r.dosha_id: r for r in (getattr(dosha_set, "dosha_results", []) or [])}
    details: Dict[str, Any] = {}
    active_severities: List[str] = []
    formed_any = False
    all_formed_cancelled = True
    cancellations_found: List[str] = []

    for tab, rule_id in MANGLIK_REF_IDS.items():
        r = by_id.get(rule_id)
        if r is None:
            details[tab] = {"is_present": False, "is_cancelled": False,
                            "house": None, "cancellation_reasons": [],
                            "severity": "UNKNOWN", "rule_id": rule_id,
                            "note": "rule not evaluated"}
            continue
        formed = bool(r.is_formed())
        cancelled = bool(r.is_cancelled())
        severity = str(getattr(r.severity_status, "value", r.severity_status))
        reasons = _cancellation_reasons(r, full_only=True)
        if formed:
            formed_any = True
        if formed and not cancelled:
            all_formed_cancelled = False
            active_severities.append(severity)
        if cancelled:
            cancellations_found.extend(x for x in reasons if x not in cancellations_found)
        details[tab] = {
            "is_present": formed,
            "is_cancelled": cancelled,
            "house": _mars_house_from_ref(r),
            "cancellation_reasons": reasons,
            "severity": severity,
            "mitigation": str(getattr(r.mitigation_status, "value", r.mitigation_status)),
            "rule_id": rule_id,
        }

    if not formed_any:
        verdict, has_dosha = "No Dosha", False
    elif all_formed_cancelled:
        verdict, has_dosha = "Cancelled", False
    else:
        verdict = max(active_severities,
                      key=lambda s: _SEV_RANK.get(s, 0)) if active_severities else "UNKNOWN"
        has_dosha = True

    return {
        "has_dosha": has_dosha,
        "verdict": verdict,
        "details": details,
        "cancellations_found": cancellations_found,
        "severities": {tab: details[tab].get("severity") for tab in MANGLIK_REF_IDS},
        "evidence_summary": "; ".join(
            f"{tab}: " + (_ev_significance(_ev_list(by_id[rid])[0])
                           if by_id.get(rid) is not None and _ev_list(by_id[rid]) else "unevaluated")
            for tab, rid in MANGLIK_REF_IDS.items()),
        "provenance": {
            rid: {"rule_id": rid,
                  "method": getattr(by_id[rid], "method", "") if rid in by_id else "",
                  "tradition": str(getattr(getattr(by_id.get(rid), "tradition", ""), "value",
                                           getattr(by_id.get(rid), "tradition", "")))}
            for rid in MANGLIK_REF_IDS.values()
        },
        "_source": "canonical",
        "_engine": "canonical",
    }


def _active_legacy_entry(result: Any, active_verdict: str) -> Dict[str, Any]:
    formed = bool(result.is_formed()) if result is not None else False
    cancelled = bool(result.is_cancelled()) if result is not None else False
    active = formed and not cancelled
    reasons = []
    detail_parts = []
    if result is not None:
        for ev in _ev_list(result):
            sig = _ev_significance(ev)
            if sig:
                detail_parts.append(sig)
                if active:
                    reasons.append(sig)
    return {
        "has_dosha": active,
        "verdict": active_verdict if active else "No Dosha",
        "details": "; ".join(detail_parts) if detail_parts else (
            "No Dosha" if result is None or not formed else
            "Dosha formed but cancelled"),
        "reasons": reasons,
        "formation": str(getattr(getattr(result, "formation_status", ""), "value",
                                 getattr(result, "formation_status", "UNKNOWN"))) if result else "UNKNOWN",
        "severity": str(getattr(getattr(result, "severity_status", ""), "value",
                                getattr(result, "severity_status", "UNKNOWN"))) if result else "UNKNOWN",
        "cancellation": str(getattr(getattr(result, "cancellation_status", ""), "value",
                                    getattr(result, "cancellation_status", "UNKNOWN"))) if result else "UNKNOWN",
        "_source": "canonical",
    }


def build_advanced_doshas_block(dosha_set: Any) -> Dict[str, Any]:
    """Project canonical Kala Sarpa + Pitru to the AdvancedDoshasCard shape."""
    by_id = {r.dosha_id: r for r in (getattr(dosha_set, "dosha_results", []) or [])}
    return {
        "kala_sarpa_dosha": _active_legacy_entry(by_id.get("DOSHA.KALA_SARPA.SIGN_BASED"),
                                                 "Active Kala Sarpa"),
        "pitru_dosha": _active_legacy_entry(by_id.get("DOSHA.PITRU.MODERN_COMMON"),
                                            "Active Pitru Dosha"),
    }


def _evidence_to_json(ev: Any) -> Dict[str, Any]:
    if isinstance(ev, dict):
        return {"evidence_type": str(ev.get("evidence_type", "")),
                "subject": ev.get("subject", ""),
                "value": ev.get("value"),
                "expected": ev.get("expected"),
                "actual": ev.get("actual"),
                "source": ev.get("source", ""),
                "significance": ev.get("significance", ""),
                "details": ev.get("details", {}) or {}}
    return {"evidence_type": str(getattr(getattr(ev, "evidence_type", ""), "value",
                                        getattr(ev, "evidence_type", ""))),
            "subject": getattr(ev, "subject", ""),
            "value": getattr(ev, "value", None),
            "expected": getattr(ev, "expected", None),
            "actual": getattr(ev, "actual", None),
            "source": getattr(ev, "source", ""),
            "significance": getattr(ev, "significance", ""),
            "details": getattr(ev, "details", {}) or {}}


def build_doshas_block(dosha_set: Any) -> List[Dict[str, Any]]:
    """Full canonical dosha list (additive; powers AI + future UI)."""
    out = []
    for r in (getattr(dosha_set, "dosha_results", []) or []):
        prov = getattr(r, "provenance", None)
        out.append({
            "id": r.dosha_id,
            "name": getattr(r, "dosha_name", r.dosha_id),
            "formation": str(getattr(getattr(r, "formation_status", ""), "value",
                                     getattr(r, "formation_status", "UNKNOWN"))),
            "severity": str(getattr(getattr(r, "severity_status", ""), "value",
                                    getattr(r, "severity_status", "UNKNOWN"))),
            "cancellation": str(getattr(getattr(r, "cancellation_status", ""), "value",
                                        getattr(r, "cancellation_status", "UNKNOWN"))),
            "mitigation": str(getattr(getattr(r, "mitigation_status", ""), "value",
                                      getattr(r, "mitigation_status", "UNKNOWN"))),
            "activation": str(getattr(getattr(r, "activation_status", ""), "value",
                                      getattr(r, "activation_status", "UNKNOWN"))),
            "confidence": str(getattr(getattr(r, "confidence", ""), "value",
                                      getattr(r, "confidence", "UNKNOWN"))),
            "method": getattr(r, "method", ""),
            "tradition": str(getattr(getattr(r, "tradition", ""), "value",
                                     getattr(r, "tradition", ""))),
            "evidence": [_evidence_to_json(e) for e in _ev_list(r)],
            "evidence_summary": "; ".join(_ev_significance(e) for e in _ev_list(r)),
            "relevant_planets": list(getattr(r, "relevant_planets", []) or []),
            "relevant_houses": list(getattr(r, "relevant_houses", []) or []),
            "provenance": {
                "source_type": str(getattr(getattr(prov, "source_type", ""), "value",
                                           getattr(prov, "source_type", ""))) if prov else "",
                "source_name": getattr(prov, "source_name", "") if prov else "",
                "source_reference": getattr(prov, "source_reference", "") if prov else "",
                "tradition": str(getattr(getattr(prov, "tradition", ""), "value",
                                         getattr(prov, "tradition", ""))) if prov else "",
                "method": getattr(prov, "method", "") if prov else "",
                "notes": getattr(prov, "notes", "") if prov else "",
            },
            "_source": "canonical",
        })
    return out


def get_canonical_dosha_coverage() -> Dict[str, Any]:
    """Canonical dosha catalogue coverage (rule IDs + legacy overlap map)."""
    return {
        "canonical_rule_ids": list(DOSHA_RULE_IDS),
        "mangal_reference_ids": dict(MANGLIK_REF_IDS),
        "legacy_overlap": {
            "DOSHA.KALA_SARPA.SIGN_BASED": ["kala_sarpa_dosha"],
            "DOSHA.PITRU.MODERN_COMMON": ["pitru_dosha"],
        },
        "legacy_only": [],
    }
