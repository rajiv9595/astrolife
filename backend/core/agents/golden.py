"""
Phase 7 — golden fixture construction.

Builds CanonicalBundle (live canonical objects, orchestrator-side only) and
AgentContext (JSON-serializable summaries, the only thing agents ever see)
from the deterministic engines on the established golden chart.

NOTE: this module legitimately invokes canonical calculators to CONSTRUCT
fixtures. It is not an agent and is not on any agent execution path; the
static calculation-import audit (§27) therefore scopes to agent
implementation modules only, with this exclusion documented here and in the
security report. Agents themselves import nothing from calculation packages.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

GOLDEN_BIRTH = {"year": 2005, "month": 8, "day": 17, "hour": 0,
                "minute": 2, "second": 0, "lat": 16.93407, "lon": 81.95522,
                "tz_name": "Asia/Kolkata"}
GOLDEN_DT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def build_canonical_bundle() -> Any:
    """Run canonical engines once. Fixture setup, not agent reasoning."""
    from datetime import datetime as _dt  # local, explicit

    from core.calculation.config import DEFAULT_PROFILE
    from core.calculation.dynamic import get_dynamic_state
    from core.calculation.pipeline import generate_chart_facts
    from core.calculation.varga import calculate_all_vargas
    from core.jaimini.dasha import calculate_jaimini_dasha
    from core.jaimini.pipeline import generate_jaimini_facts
    from core.jaimini.profile import JaiminiCalculationProfile
    from core.rules.context import RuleContext
    from core.rules.doshas.catalog import evaluate_all_doshas
    from core.rules.parashari.catalog import evaluate_all_parashari
    from core.jaimini.rules.pipeline import evaluate_jaimini_yogas
    from core.strength.pipeline import DEFAULT_STRENGTH_PROFILE, generate_strength_report
    from core.transit.calculator import calculate_transit_positions

    from .agent_context import CanonicalBundle

    birth = GOLDEN_BIRTH
    chart = generate_chart_facts(
        year=birth["year"], month=birth["month"], day=birth["day"],
        hour=birth["hour"], minute=birth["minute"], second=birth["second"],
        lat=birth["lat"], lon=birth["lon"], tz_name=birth["tz_name"],
        location_name="Anaparthy", country_name="India", profile=DEFAULT_PROFILE)
    vargas = calculate_all_vargas(chart, DEFAULT_PROFILE)
    strength = generate_strength_report(chart, DEFAULT_STRENGTH_PROFILE)
    jaimini = generate_jaimini_facts(chart, vargas, JaiminiCalculationProfile())
    dynamic_state = get_dynamic_state(chart, GOLDEN_DT, profile=DEFAULT_PROFILE)
    transit = calculate_transit_positions(GOLDEN_DT)
    jaimini_dasha = calculate_jaimini_dasha(chart, jaimini)
    rule_context = RuleContext(
        chart_facts=chart, strength_report=strength, varga_facts=vargas,
        dynamic_state=dynamic_state, evaluation_datetime=GOLDEN_DT)
    parashari = evaluate_all_parashari(rule_context)
    doshas = evaluate_all_doshas(rule_context)
    jaimini_yogas = evaluate_jaimini_yogas(chart, jaimini, vargas)
    return CanonicalBundle(
        chart_facts=chart, varga_facts=vargas, strength_report=strength,
        jaimini_facts=jaimini,
        dasha_state={"dynamic_state": dynamic_state, "jaimini_dasha": jaimini_dasha},
        transit_state=transit,
        rule_results={"parashari": parashari, "doshas": doshas,
                      "jaimini_yogas": jaimini_yogas},
        evidence={"dynamic_state": dynamic_state})


def _enum_name(value: Any) -> str:
    return getattr(value, "value", str(value))


def golden_context(bundle: Any = None) -> Any:
    """Summarize canonical outputs into an AgentContext. Strings only."""
    from core.calculation.dasha import get_current_dasha

    from .agent_context import AgentContext
    from .agent_models import ConflictSummary, RuleResultSummary, TimingCandidateSummary

    bundle = bundle or build_canonical_bundle()
    chart = bundle.chart_facts
    vargas = bundle.varga_facts
    strength = bundle.strength_report
    jaimini = bundle.jaimini_facts
    dasha_state = bundle.dasha_state
    transit = bundle.transit_state
    rule_results = bundle.rule_results

    facts: Dict[str, str] = {"ascendant_sign": chart.ascendant.sign.name}
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        pdata = chart.planets.get(planet)
        if pdata is None:
            continue
        facts[f"{planet}_sign"] = pdata.sign.name
        facts[f"{planet}_house"] = str(pdata.house)
    varga_table: Dict[str, Dict[str, str]] = {}
    for varga in ("D1", "D9", "D10"):
        table: Dict[str, str] = {}
        for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            entry = (vargas.get("planets", {}).get(planet) or {}).get(varga)
            sign = getattr(entry, "sign", None)
            if sign:
                table[planet] = str(sign)
        varga_table[varga] = table
    strength_table: Dict[str, str] = {}
    for planet, entry in sorted((strength.planets or {}).items()):
        strength_table[f"classical.shadbala.{planet}"] = (
            f"{getattr(entry, 'total_rupas', '?')} rupas, minimum "
            f"{getattr(entry, 'minimum_rupas', '?')}, status "
            f"{_enum_name(getattr(entry, 'strength_status', 'UNKNOWN'))} "
            f"per canonical Shadbala report")
    for house, entry in sorted((strength.bhava_bala or {}).items()):
        strength_table[f"classical.bhava_bala.{house}"] = str(
            getattr(entry, "strength_status", entry))[:80]
    for planet, table in sorted((strength.avastha or {}).items()):
        names = sorted({getattr(v, "avastha_name", str(v)) for v in table.values()})
        strength_table[f"classical.avastha.{planet}"] = ", ".join(names)
    for planet, entry in sorted((strength.composite or {}).items()):
        strength_table[f"custom.composite.{planet}"] = (
            f"score {getattr(entry, 'score', '?')} label "
            f"{getattr(entry, 'label', '?')} per custom composite")
    dignity_table = {planet: _enum_name(getattr(entry, "dignity", "UNKNOWN"))
                     for planet, entry in sorted((strength.dignity or {}).items())}

    evidence_ids: List[str] = []
    sources: Dict[str, str] = {}

    def _register_source(source_id: str, title: str) -> str:
        sid = source_id or "UNRECORDED"
        sources.setdefault(sid, title or sid)
        return sid

    rules: List[RuleResultSummary] = []
    for index, result in enumerate(rule_results.get("parashari", [])):
        ev_ids = [f"classic-ev:{result.rule_id}:{i:02d}"
                  for i in range(len(result.evidence or []))]
        evidence_ids.extend(ev_ids)
        sid = _register_source(getattr(result.provenance, "source_name", ""),
                               getattr(result.provenance, "source_name", ""))
        rules.append(RuleResultSummary(
            rule_id=result.rule_id, tradition=_enum_name(result.tradition),
            formation=_enum_name(result.formation_status),
            cancellation=_enum_name(result.cancellation_status),
            mitigation=_enum_name(result.mitigation_status),
            activation=_enum_name(result.activation_status),
            evidence_ids=ev_ids, source_ids=[sid]))
    doshas: List[RuleResultSummary] = []
    dosha_set = rule_results.get("doshas")
    for item in getattr(dosha_set, "dosha_results", []) or []:
        doshas.append(RuleResultSummary(
            rule_id=getattr(item, "dosha_id", "UNKNOWN"),
            tradition=str(getattr(item, "tradition", "")),
            formation=str(getattr(item, "formation_status", "")),
            cancellation=str(getattr(item, "cancellation_status", "")),
            mitigation=str(getattr(item, "mitigation_status", "")),
            activation=str(getattr(item, "activation_status", "")),
            evidence_ids=[], source_ids=[]))
    jaimini_rules: List[RuleResultSummary] = []
    evaluation = rule_results.get("jaimini_yogas")
    for item in getattr(evaluation, "results", []) or []:
        origin = getattr(item, "origin_label", "TRADITION_DEPENDENT")
        tradition = ("JAIMINI_CLASSICAL" if origin == "CLASSICAL_JAIMINI"
                     else "TRADITION_DEPENDENT")
        ev_ids = [f"classic-ev:{item.rule_id}:{i:02d}"
                  for i in range(len(getattr(item, "evidence", []) or []))]
        evidence_ids.extend(ev_ids)
        jaimini_rules.append(RuleResultSummary(
            rule_id=item.rule_id, tradition=tradition,
            formation="FORMED" if getattr(item, "formed", False) else "NOT_FORMED",
            cancellation=_enum_name(getattr(item, "cancellation_status", "NONE")),
            mitigation=_enum_name(getattr(item, "mitigation_status", "NONE")),
            activation="", evidence_ids=ev_ids, source_ids=["JAIMINI_TRADITION"]))
    sources.setdefault("JAIMINI_TRADITION", "Jaimini tradition corpus")

    karakas = getattr(jaimini.chara_karakas, "karakas", {}) or {}
    jaimini_table = {f"karaka_{code}": getattr(item, "planet", "?")
                     for code, item in sorted(karakas.items())}
    jaimini_table["AL"] = getattr(jaimini.arudha_lagna, "final_sign", "?")
    jaimini_table["UL"] = getattr(jaimini.upapada, "final_sign", "?")
    jaimini_table["karakamsha"] = getattr(jaimini.karakamsha, "karakamsha_sign", "?")
    jaimini_table["swamsa"] = getattr(
        jaimini.karakamsha, "swamsa_navamsha_lagna_sign", "?")
    jaimini_table["rashi_drishti"] = (
        f"map with {len(getattr(jaimini.rashi_drishti, 'sign_aspects', {}) or {})} "
        f"signs per canonical report")
    jaimini_table["profile"] = "SEVEN_KARAKA"

    dasha_table: Dict[str, str] = {}
    dyn = dasha_state.get("dynamic_state")
    timeline = getattr(dyn, "dasha", None)
    current = None
    if isinstance(timeline, dict):
        current = timeline.get("current")
        if current is None and "timeline" in timeline:
            try:
                current = get_current_dasha(timeline["timeline"], GOLDEN_DT)
            except Exception:
                current = None
    if current:
        mahadasha = current.get("mahadasha") or {}
        antardasha = current.get("antardasha") or {}

        def _field(item: Any, name: str) -> str:
            if isinstance(item, dict):
                return str(item.get(name, "?"))
            return str(getattr(item, name, "?"))

        dasha_table["vimshottari_mahadasha"] = (
            f"{_field(mahadasha, 'lord')} "
            f"{_field(mahadasha, 'start_utc_iso')} to "
            f"{_field(mahadasha, 'end_utc_iso')}")
        dasha_table["vimshottari_antardasha"] = (
            f"{_field(antardasha, 'lord')} "
            f"{_field(antardasha, 'start_utc_iso')} to "
            f"{_field(antardasha, 'end_utc_iso')}")
    chara = dasha_state.get("jaimini_dasha")
    dasha_table["chara_profile"] = str(getattr(chara, "profile_method", "?"))
    dasha_table["chara_active"] = str(_chara_active(chara))

    transit_table = {}
    for planet, position in sorted((getattr(transit, "planets", {}) or {}).items()):
        transit_table[planet] = str(getattr(position, "sign", position))

    timing = [
        TimingCandidateSummary(
            candidate_id="GOLDEN-VIM-MD",
            kind="VIMSHOTTARI_MAHADASHA",
            window=dasha_table.get("vimshottari_mahadasha", "unavailable"),
            basis_rule_ids=[],
            detail="Restated current Mahadasha window; no outcome stated."),
        TimingCandidateSummary(
            candidate_id="GOLDEN-CHARA-ACTIVE",
            kind="CHARA_ACTIVE",
            window=dasha_table.get("chara_active", "unavailable"),
            basis_rule_ids=[],
            detail="Restated Chara active sign; no outcome stated."),
    ]
    applicability = {r.rule_id: "APPLICABLE" for r in rules[:5]}
    conflicts = _catalogue_conflicts()

    context = AgentContext(
        chart_fingerprint="", calculation_profile="DEFAULT",
        facts=facts, vargas=varga_table, strength=strength_table,
        dignity=dignity_table, rules=rules, doshas=doshas, jaimini=jaimini_table,
        jaimini_rules=jaimini_rules, dasha=dasha_table, transit=transit_table,
        timing=timing, applicability=applicability,
        evidence_ids=sorted(set(evidence_ids)), conflicts=conflicts,
        sources=sources, requested_domain="FULL",
        allowed_traditions=["PARASHARI_CLASSICAL", "JAIMINI_CLASSICAL",
                            "TRADITION_DEPENDENT", "MODERN_COMMON",
                            "CUSTOM_DEVELOPER"],
        profile="CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL",
        question="", output_mode="STRUCTURED")
    from .agent_security import stable_digest
    fingerprint = stable_digest({
        "facts": facts, "vargas": varga_table, "strength": strength_table,
        "dignity": dignity_table,
        "rules": [r.model_dump(mode="json") for r in rules],
        "jaimini": jaimini_table})
    return context.model_copy(update={"chart_fingerprint": fingerprint})


def _chara_active(chara: Any) -> str:
    periods = getattr(chara, "periods", None) or []
    for period in periods:
        start = getattr(period, "start_utc_iso", "") or ""
        end = getattr(period, "end_utc_iso", "") or ""
        if start <= GOLDEN_DT.isoformat().replace("+00:00", "Z") < end or (
                start <= "2026-01-01T00:00:00Z" < end):
            return f"{getattr(period, 'sign', '?')} {start} to {end}"
    first = periods[0] if periods else None
    return str(getattr(first, "sign", "unavailable"))


def _catalogue_conflicts() -> List[Any]:
    from core.rules.dynamic.knowledge import find_conflicts, get_rule_catalogue

    from .agent_models import ConflictSummary
    out = []
    for conflict in find_conflicts(get_rule_catalogue())[:4]:
        out.append(ConflictSummary(
            conflict_id=conflict.conflict_id, rule_a=conflict.rule_a,
            rule_b=conflict.rule_b, conflict_type=conflict.conflict_type,
            status=conflict.status, detail="Catalogue-level reported conflict."))
    return out
