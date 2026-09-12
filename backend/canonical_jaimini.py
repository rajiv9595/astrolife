"""
Canonical Jaimini Adapter — Production adapter: canonical Jaimini engine
-> legacy-compatible jaimini response shape.

NO ASTROLOGY IS COMPUTED HERE. Every value originates from:
- backend.core.jaimini.pipeline.generate_jaimini_facts (canonical facts)
- backend.core.jaimini.rules.pipeline.evaluate_jaimini_yogas (canonical yogas)
- backend.core.jaimini.dasha.pipeline.calculate_jaimini_dasha (canonical dasha)

This module ONLY projects canonical facts into the response shape consumed
by the frontend (chart_data.jaimini) and AI context. The only computation is
a deterministic interval lookup for the current Chara period at the supplied
evaluation datetime (containment over canonical UTC bounds — no new astrology,
no current-period API invented: the engine exposes no such API, so the lookup
and its derivation are labeled explicitly).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.core.jaimini.pipeline import generate_jaimini_facts
from backend.core.jaimini.profile import JaiminiCalculationProfile
from backend.core.jaimini.rules.pipeline import evaluate_jaimini_yogas
from backend.core.jaimini.dasha.pipeline import calculate_jaimini_dasha
from backend.core.calculation.pipeline import ChartFacts


# Legacy frontend contract: {"Atmakaraka (AK)": planet, ...} in rank order.
KARAKA_CODE_TO_LEGACY_NAME = {
    "AK": "Atmakaraka (AK)",
    "AmK": "Amatyakaraka (AmK)",
    "BK": "Bhratrukaraka (BK)",
    "MK": "Matrukaraka (MK)",
    "PK": "Putrakaraka (PK)",
    "GK": "Gnatikaraka (GK)",
    "DK": "Darakaraka (DK)",
    "PiK": "Pitrukaraka (PiK)",
}


def _jsonable(value: Any) -> Any:
    """Project engine objects to plain JSON-native values (no astrology)."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            return _jsonable(model_dump(mode="json"))
        except TypeError:
            return _jsonable(model_dump())
    return str(value)


def _parse_iso(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        text = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (ValueError, TypeError):
        return None


def _normalize_eval_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    return _parse_iso(value)


def _find_current_period(periods: List[Any], eval_dt: Optional[datetime]) -> Dict[str, Any]:
    """Deterministic containment lookup over canonical UTC period bounds.

    Not a canonical engine API (none exists); derivation is labeled in output.
    """
    if eval_dt is None:
        return {"mahadasha": None, "antardasha": None,
                "derivation": "no_evaluation_datetime_supplied"}
    for period in periods:
        start = _parse_iso(getattr(period, "start_utc_iso", None))
        end = _parse_iso(getattr(period, "end_utc_iso", None))
        if start is None or end is None:
            continue
        if start <= eval_dt < end:
            current_antar = None
            for antar in getattr(period, "antardashas", []) or []:
                a_start = _parse_iso(getattr(antar, "start_utc_iso", None))
                a_end = _parse_iso(getattr(antar, "end_utc_iso", None))
                if a_start is not None and a_end is not None and a_start <= eval_dt < a_end:
                    current_antar = getattr(antar, "sign", None)
                    break
            return {"mahadasha": getattr(period, "sign", None),
                    "antardasha": current_antar,
                    "derivation": "interval_containment_over_canonical_utc_bounds"}
    return {"mahadasha": None, "antardasha": None,
            "derivation": "evaluation_datetime_outside_canonical_periods"}


def _period_to_dict(period: Any) -> Dict[str, Any]:
    return {
        "sign": getattr(period, "sign", None),
        "direction": getattr(period, "direction", None),
        "sequence_index": getattr(period, "sequence_index", None),
        "start_utc_iso": getattr(period, "start_utc_iso", None),
        "end_utc_iso": getattr(period, "end_utc_iso", None),
        "duration_years": getattr(period, "duration_years", None),
        "antardashas": [
            {"sign": getattr(a, "sign", None),
             "start_utc_iso": getattr(a, "start_utc_iso", None),
             "end_utc_iso": getattr(a, "end_utc_iso", None),
             "duration_years": getattr(a, "duration_years", None)}
            for a in (getattr(period, "antardashas", []) or [])
        ],
    }


def evaluate_canonical_jaimini(
    chart_facts: ChartFacts,
    varga_facts: Optional[Dict[str, Any]] = None,
    evaluation_datetime: Optional[Any] = None,
    include_yogas: bool = True,
    include_dasha: bool = True,
) -> Dict[str, Any]:
    """
    Evaluate canonical Jaimini facts and project to the response shape.

    Raises on engine failure (caller applies legacy rollback fallback).
    """
    profile = JaiminiCalculationProfile()
    facts = generate_jaimini_facts(chart_facts, varga_facts or {}, profile)

    # Legacy-compatible core (frontend JaiminiCard contract).
    chara_karakas: Dict[str, str] = {}
    for code in facts.chara_karakas.ordering:
        item = facts.chara_karakas.karakas.get(code)
        if item is not None:
            chara_karakas[KARAKA_CODE_TO_LEGACY_NAME.get(code, code)] = item.planet
    arudha_padas = {str(h): pada.final_sign
                    for h, pada in sorted(facts.arudha_padas.items())}

    result: Dict[str, Any] = {
        # --- legacy-compatible representation (contract preserved) ---
        "chara_karakas": chara_karakas,
        "arudha_padas": arudha_padas,
        # --- canonical richness (additive; frontend ignores unknown keys) ---
        "karakamsha": {
            "atmakaraka_planet": facts.karakamsha.atmakaraka_planet,
            "atmakaraka_d1_sign": facts.karakamsha.atmakaraka_d1_sign,
            "karakamsha_sign": facts.karakamsha.karakamsha_sign,
            "swamsa_navamsha_lagna_sign": facts.karakamsha.swamsa_navamsha_lagna_sign,
        },
        "arudha_lagna": {
            "final_sign": facts.arudha_lagna.final_sign,
            "source_sign": facts.arudha_lagna.source_sign,
            "lord": facts.arudha_lagna.house_lord,
            "lord_sign": facts.arudha_lagna.lord_sign,
            "exception_applied": facts.arudha_lagna.exception_applied,
        },
        "upapada": {
            "final_sign": facts.upapada.final_sign,
            "source_sign": facts.upapada.source_sign,
            "lord": facts.upapada.lord,
            "lord_sign": facts.upapada.lord_sign,
            "exception_applied": facts.upapada.exception_applied,
        },
        "rashi_drishti": {
            "sign_aspects": dict(facts.rashi_drishti.sign_aspects),
            "planet_aspects": dict(facts.rashi_drishti.planet_aspects),
        },
        "evidence": {k: list(v) for k, v in (facts.evidence or {}).items()},
        "provenance": {
            "tradition": facts.provenance.tradition,
            "method": facts.provenance.method,
            "source_texts": list(facts.provenance.source_texts),
            "source_reference": facts.provenance.source_reference,
            "version": facts.provenance.version,
            "confidence": facts.provenance.confidence,
        },
        "_source": "canonical",
        "_engine": "canonical",
    }

    if include_yogas:
        yoga_eval = evaluate_jaimini_yogas(chart_facts, facts, varga_facts or {})
        result["yogas"] = [
            {"id": r.rule_id,
             "name": r.name,
             "formed": bool(r.formed),
             "status": "ACTIVE" if r.formed else "INACTIVE",
             "relevant_planets": list(r.relevant_planets),
             "relevant_signs": list(r.relevant_signs),
             "relevant_houses": list(r.relevant_houses),
             "evidence": _jsonable(list(r.formation_evidence)),
             "_source": "canonical"}
            for r in yoga_eval.results
        ]

    if include_dasha:
        dasha = calculate_jaimini_dasha(chart_facts, facts)
        eval_dt = _normalize_eval_dt(evaluation_datetime)
        result["chara_dasha"] = {
            "starting_sign": dasha.starting_sign,
            "direction": dasha.direction,
            "total_years": dasha.total_years,
            "birth_utc_iso": dasha.birth_utc_iso,
            "status": dasha.status,
            "periods": [_period_to_dict(p) for p in dasha.periods],
            "current": _find_current_period(dasha.periods, eval_dt),
            "starting_sign_evidence": dict(dasha.starting_sign_evidence or {}),
            "_source": "canonical",
        }

    return result


def get_canonical_jaimini_coverage() -> Dict[str, Any]:
    """Field-level coverage of canonical Jaimini vs legacy output."""
    from backend.core.jaimini.rules.catalogue import get_rule_ids
    return {
        "canonical_fields": [
            "chara_karakas", "arudha_padas", "karakamsha", "arudha_lagna",
            "upapada", "rashi_drishti", "yogas", "chara_dasha",
            "evidence", "provenance",
        ],
        "legacy_fields": ["chara_karakas", "arudha_padas"],
        "legacy_only_fields": [],
        "canonical_yoga_rule_ids": get_rule_ids(),
    }
