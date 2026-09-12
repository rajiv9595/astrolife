"""
Canonical AI Agents Bridge — Migration #10.

Thin production bridge wiring the EXISTING Phase 7 deterministic specialist
agents into the production AI architecture.

NO ASTROLOGY IS COMPUTED HERE. Every value originates from:
- backend.core.agents.agent_registry.build_default_registry (existing registry)
- backend.core.agents.agent_router.route (existing deterministic router)
- backend.core.agents.agents.BUILDERS (existing deterministic drafts)
- backend.core.agents.agent_result.finalize_result / validate_model_output
- production /compute response projections (canonical Yoga/Dosha/Jaimini/
  Strength/Dasha facts with evidence + provenance)
- canonical transit sections (backend/ai_transit_context.py)
- deterministic prediction summaries (Migration #9, verbatim)

Responsibilities (projection/orchestration only):
- singleton production agent registry (existing class, no duplicate)
- AgentContext construction from canonical production data (summaries only;
  missing sections stay missing -> agents yield honest UNKNOWN)
- deterministic routing (FULL domain set, sorted; unknown IDs rejected;
  allow-list BUILDERS only — no dynamic imports, no user module loading)
- direct deterministic draft execution + strict validation + JSON
  serialization with `_source: production_agents` for AI synthesis input

Security boundaries preserved:
- agents are analysis specialists: READ/CONTRACT-scoped, CALCULATE/PREDICT
  forbidden by contract; user question text is DATA (injection-scanned)
- research:// / EXPERIMENTAL rules never enter (only supplied ACTIVE
  canonical summaries; no lab/service imports)
- one agent failure -> invalid_result for that agent only; canonical facts
  untouched; nothing fabricated as replacement
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.agents.agent_contract import ALL_AGENTS
from backend.core.agents.agent_registry import build_default_registry
from backend.core.agents.agent_router import DOMAIN_ROUTES, route

_PRODUCTION_AGENT_REGISTRY = None

FULL_DOMAINS = ["FULL"]

ALLOWED_TRADITIONS = [
    "PARASHARI_CLASSICAL",
    "JAIMINI_CLASSICAL",
    "TRADITION_DEPENDENT",
    "MODERN_COMMON",
    "CUSTOM_DEVELOPER",
]

_DIGNITY_BACKMAP = {
    "Exalted": "EXALTED",
    "Moolatrikona": "MOOLATRIKONA",
    "Own Sign": "OWN_SIGN",
    "Friend Sign": "FRIEND",
    "Neutral": "NEUTRAL",
    "Enemy Sign": "ENEMY",
    "Debilitated": "DEBILITATED",
}

_KARAKA_LEGACY_TO_CODE = {
    "Atmakaraka (AK)": "AK",
    "Amatyakaraka (AmK)": "AmK",
    "Bhratrukaraka (BK)": "BK",
    "Matrukaraka (MK)": "MK",
    "Putrakaraka (PK)": "PK",
    "Gnatikaraka (GK)": "GK",
    "Darakaraka (DK)": "DK",
    "Pitrukaraka (PiK)": "PiK",
}


def get_production_agent_registry():
    """Singleton over the existing canonical agent registry (no duplicate)."""
    global _PRODUCTION_AGENT_REGISTRY
    if _PRODUCTION_AGENT_REGISTRY is None:
        _PRODUCTION_AGENT_REGISTRY = build_default_registry()
    return _PRODUCTION_AGENT_REGISTRY


def get_production_agent_ids() -> List[str]:
    """Stable production agent IDs in deterministic order."""
    return sorted(ALL_AGENTS)


def route_production_agents(
    domains: Optional[List[str]] = None,
    traditions: Optional[List[str]] = None,
    profile: str = "",
    question: str = "",
    request_id: str = "production",
) -> Dict[str, Any]:
    """Deterministic routing over stable IDs. Unknown domains are rejected
    (never dynamically imported)."""
    from backend.core.agents.agent_context import AgentRequest
    request = AgentRequest(
        request_id=request_id,
        question=question or "",
        requested_domains=list(domains or FULL_DOMAINS),
        traditions=list(traditions or []),
        profile=profile or "",
    )
    from backend.core.agents.agent_context import AgentContext
    context = AgentContext(
        allowed_traditions=list(ALLOWED_TRADITIONS),
        profile=profile or "",
        question=question or "",
    )
    routed = route(request, context)
    return {
        "agents": list(routed.get("agents", [])),
        "notes": list(routed.get("notes", [])),
        "rejected": list(routed.get("rejected", [])),
        "_source": "production_agents",
    }


def _str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return str(value)
    return str(value)


def build_agent_context_from_compute(
    compute_response: Dict[str, Any],
    *,
    question: str = "",
    traditions: Optional[List[str]] = None,
    profile: str = "",
    transit_section: Optional[Dict[str, Any]] = None,
    prediction_summary: Optional[Dict[str, Any]] = None,
) -> Any:
    """Summarize canonical production data into an AgentContext.

    Only supplied sections are populated; anything absent stays absent so
    agents yield honest UNKNOWN (never inferred, never fabricated).
    """
    from backend.core.agents.agent_context import AgentContext
    from backend.core.agents.agent_models import (
        ConflictSummary,
        RuleResultSummary,
        TimingCandidateSummary,
    )

    data = compute_response or {}
    planets = data.get("planets") or {}
    asc = data.get("ascendant") or {}

    facts: Dict[str, str] = {}
    if asc.get("sign"):
        facts["ascendant_sign"] = _str(asc.get("sign"))
    for name, info in sorted(planets.items()):
        if not isinstance(info, dict):
            continue
        sign = info.get("sign") or info.get("sign_manual")
        if sign:
            facts[f"{name}_sign"] = _str(sign)
        house = info.get("house_num")
        if house is not None:
            facts[f"{name}_house"] = _str(house)

    vargas: Dict[str, Dict[str, str]] = {}
    vargas_block = data.get("vargas") or {}
    for varga in ("d1", "d9", "d10"):
        table = vargas_block.get(varga) or {}
        if isinstance(table, dict):
            entries = {p: _str(v.get("sign")) for p, v in sorted(table.items())
                       if isinstance(v, dict) and v.get("sign")
                       and not str(p).startswith("_")}
            if entries:
                vargas[varga.upper()] = entries

    strength: Dict[str, str] = {}
    shadbala = data.get("shadbala") or {}
    for planet in sorted(shadbala):
        entry = shadbala[planet] or {}
        strength[f"classical.shadbala.{planet}"] = (
            f"{entry.get('total_rupas', '?')} rupas, minimum "
            f"{entry.get('minimum_rupas', '?')}, status "
            f"{entry.get('status', 'UNKNOWN')} per canonical Shadbala report")
    for row in data.get("strengths") or []:
        planet = row.get("planet")
        nature = row.get("nature")
        if planet and nature and planet not in ("Rahu", "Ketu"):
            mapped = _DIGNITY_BACKMAP.get(nature)
            if mapped:
                dignity_key = planet
                strength.setdefault(f"dignity.{dignity_key}", mapped)
    dignity: Dict[str, str] = {}
    for key in sorted(strength):
        if key.startswith("dignity."):
            dignity[key[len("dignity."):]] = strength[key]
    for house, entry in sorted((data.get("bhava_bala") or {}).items()):
        strength[f"classical.bhava_bala.{house}"] = _str(
            (entry or {}).get("classification", entry))[:80]
    for planet, systems in sorted((data.get("avastha") or {}).items()):
        if isinstance(systems, dict):
            names = sorted({str(v.get("avastha_name", v)) for k, v in
                            systems.items() if isinstance(v, dict)
                            and k != "_source"})
            if names:
                strength[f"classical.avastha.{planet}"] = ", ".join(names)
    for planet, entry in sorted((data.get("composite_strength") or {}).items()):
        if isinstance(entry, dict):
            strength[f"custom.composite.{planet}"] = (
                f"score {entry.get('score', '?')} label "
                f"{entry.get('label', '?')} per custom composite")

    evidence_ids: List[str] = []
    sources: Dict[str, str] = {}

    def _register_source(source_id: str, title: str) -> str:
        sid = source_id or "UNRECORDED"
        sources.setdefault(sid, title or sid)
        return sid

    rules: List[RuleResultSummary] = []
    for yoga in data.get("yogas") or []:
        if not isinstance(yoga, dict) or not yoga.get("id"):
            continue
        prov = yoga.get("provenance") or {}
        sid = _register_source(prov.get("source", ""),
                               prov.get("source", ""))
        ev = yoga.get("evidence") or []
        ev_ids = [f"compute-ev:{yoga['id']}:{i:02d}" for i in range(len(ev))]
        evidence_ids.extend(ev_ids)
        rules.append(RuleResultSummary(
            rule_id=yoga["id"],
            tradition=prov.get("tradition", "") or "PARASHARI_CLASSICAL",
            formation="FORMED" if yoga.get("status") == "ACTIVE" else "NOT_FORMED",
            cancellation="",
            mitigation="",
            activation="",
            evidence_ids=ev_ids,
            source_ids=[sid]))

    doshas: List[RuleResultSummary] = []
    for dosha in data.get("doshas") or []:
        if not isinstance(dosha, dict) or not dosha.get("id"):
            continue
        prov = dosha.get("provenance") or {}
        sid = _register_source(prov.get("source_name", ""),
                               prov.get("source_name", ""))
        ev = dosha.get("evidence") or []
        ev_ids = [f"compute-ev:{dosha['id']}:{i:02d}" for i in range(len(ev))]
        evidence_ids.extend(ev_ids)
        doshas.append(RuleResultSummary(
            rule_id=dosha["id"],
            tradition=dosha.get("tradition", "") or "PARASHARI_CLASSICAL",
            formation=_str(dosha.get("formation", "")),
            cancellation=_str(dosha.get("cancellation", "")),
            mitigation=_str(dosha.get("mitigation", "")),
            activation=_str(dosha.get("activation", "")),
            evidence_ids=ev_ids,
            source_ids=[sid]))

    jaimini_block = data.get("jaimini") or {}
    jaimini: Dict[str, str] = {}
    for legacy_name, planet in sorted((jaimini_block.get("chara_karakas") or {}).items()):
        code = _KARAKA_LEGACY_TO_CODE.get(legacy_name, legacy_name)
        jaimini[f"karaka_{code}"] = _str(planet)
    for key in ("karakamsha", "arudha_lagna", "upapada"):
        entry = jaimini_block.get(key) or {}
        if isinstance(entry, dict):
            if key == "karakamsha" and entry.get("karakamsha_sign"):
                jaimini["karakamsha"] = _str(entry.get("karakamsha_sign"))
            if key == "arudha_lagna" and entry.get("final_sign"):
                jaimini["AL"] = _str(entry.get("final_sign"))
            if key == "upapada" and entry.get("final_sign"):
                jaimini["UL"] = _str(entry.get("final_sign"))
    if jaimini_block.get("rashi_drishti"):
        jaimini["rashi_drishti"] = "per canonical report"
    if jaimini:
        jaimini.setdefault("profile", "SEVEN_KARAKA")
    jaimini_rules: List[RuleResultSummary] = []
    for item in jaimini_block.get("yogas") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        ev = item.get("evidence") or []
        ev_ids = [f"compute-ev:{item['id']}:{i:02d}" for i in range(len(ev))]
        evidence_ids.extend(ev_ids)
        jaimini_rules.append(RuleResultSummary(
            rule_id=item["id"], tradition="JAIMINI_CLASSICAL",
            formation="FORMED" if item.get("formed") else "NOT_FORMED",
            cancellation="", mitigation="", activation="",
            evidence_ids=ev_ids, source_ids=["JAIMINI_TRADITION"]))
    if jaimini_rules:
        sources.setdefault("JAIMINI_TRADITION", "Jaimini tradition corpus")

    dasha: Dict[str, str] = {}
    vim = data.get("vimshottari") or {}
    current = vim.get("current_dasha") or {}
    md = current.get("mahadasha") or {}
    ad = current.get("antardasha") or {}
    if md.get("lord"):
        dasha["vimshottari_mahadasha"] = (
            f"{md.get('lord')} {md.get('start_date', '')} to {md.get('end_date', '')}")
    if ad.get("lord"):
        dasha["vimshottari_antardasha"] = (
            f"{ad.get('lord')} {ad.get('start_date', '')} to {ad.get('end_date', '')}")
    transit_section = transit_section or {}
    section_dasha = transit_section.get("DASHA") or {}
    if isinstance(section_dasha, dict):
        for key in ("mahadasha", "antardasha"):
            if section_dasha.get(key) and key not in dasha:
                dasha[key] = _str(section_dasha.get(key))

    transit: Dict[str, str] = {}
    current_transits = transit_section.get("CURRENT_TRANSITS") or {}
    for name, info in sorted((current_transits.get("planets") or {}).items()):
        if isinstance(info, dict) and info.get("sign"):
            transit[name] = _str(info.get("sign"))

    timing: List[TimingCandidateSummary] = []
    for cand in (prediction_summary or {}).get("candidates") or []:
        if not isinstance(cand, dict):
            continue
        windows = cand.get("windows") or []
        window = "unavailable"
        if windows and isinstance(windows[0], dict):
            window = f"{windows[0].get('start', '')} to {windows[0].get('end', '')}"
        timing.append(TimingCandidateSummary(
            candidate_id=_str(cand.get("hypothesis_id", "UNKNOWN")),
            kind=_str(cand.get("event_type", "")),
            window=window,
            basis_rule_ids=[],
            detail="Restated deterministic prediction candidate; no outcome stated."))

    applicability = {r.rule_id: "APPLICABLE" for r in rules}
    applicability.update({d.rule_id: "APPLICABLE" for d in doshas})

    conflicts: List[ConflictSummary] = []
    context = AgentContext(
        chart_fingerprint="",
        calculation_profile=_str(data.get("calculation_profile", "")) or "DEFAULT",
        facts=facts, vargas=vargas, strength=strength, dignity=dignity,
        rules=rules, doshas=doshas, jaimini=jaimini,
        jaimini_rules=jaimini_rules, dasha=dasha, transit=transit,
        timing=timing, applicability=applicability,
        evidence_ids=sorted(set(evidence_ids)), conflicts=conflicts,
        sources=sources, requested_domain="FULL",
        allowed_traditions=list(traditions or ALLOWED_TRADITIONS),
        profile=profile or "", question=question or "",
        output_mode="STRUCTURED")
    fingerprint = context.fingerprint()
    return context.model_copy(update={"chart_fingerprint": fingerprint})


def run_production_agents(
    context: Any,
    agent_ids: Optional[List[str]] = None,
    registry: Any = None,
) -> Dict[str, Any]:
    """Execute deterministic specialists over a shared context.

    Facts are built once by the caller and shared (never regenerated per
    agent). Unknown IDs are rejected (allow-list only). Builder exceptions
    become per-agent INVALID results; canonical facts are never touched and
    no replacement output is fabricated.
    """
    from backend.core.agents.agent_result import (
        finalize_result,
        invalid_result,
        validate_model_output,
    )
    from backend.core.agents.agents import BUILDERS

    reg = registry if registry is not None else get_production_agent_registry()
    selected = sorted(agent_ids) if agent_ids is not None else get_production_agent_ids()
    known = set(get_production_agent_ids())
    results: List[Dict[str, Any]] = []
    records: List[Dict[str, Any]] = []
    rejected: List[str] = []
    for agent_id in selected:
        if agent_id not in known or agent_id not in BUILDERS:
            rejected.append(f"unknown agent {agent_id!r}")
            continue
        try:
            reg.get_agent(agent_id)
        except KeyError:
            rejected.append(f"unregistered agent {agent_id!r}")
            continue
        try:
            draft = BUILDERS[agent_id](context)
        except Exception as exc:
            failed = invalid_result(
                agent_id, context, [f"builder exception: {type(exc).__name__}"],
                ["agent execution failed; no replacement output fabricated"])
            results.append(_serialize(failed, context))
            records.append(_record(agent_id, context, failed,
                                   ["builder exception isolated"]))
            continue
        ok, notes, parsed = validate_model_output(draft, context, agent_id)
        if not ok or parsed is None:
            failed = invalid_result(
                agent_id, context, notes,
                [f"adapter output rejected: {n}" for n in notes])
            results.append(_serialize(failed, context))
            records.append(_record(agent_id, context, failed, notes))
            continue
        final = finalize_result(parsed, context)
        results.append(_serialize(final, context))
        records.append(_record(agent_id, context, final, notes))
    return {
        "agents": [r["agent_id"] for r in results],
        "results": results,
        "records": records,
        "rejected": sorted(rejected),
        "context_fingerprint": context.fingerprint(),
        "registry_fingerprint": reg.fingerprint(),
        "_source": "production_agents",
    }


def run_full_production_with_synthesis(context: Any) -> Dict[str, Any]:
    """Run all six specialists (deterministic order) plus synthesis."""
    from backend.core.agents.agents import BUILDERS
    from backend.core.agents.agent_result import (
        AgentResult,
        finalize_result,
        invalid_result,
        validate_model_output,
    )
    sub_ids = [a for a in get_production_agent_ids() if a != "CHART_SYNTHESIS_AGENT"]
    run = run_production_agents(context, sub_ids)
    sub_results = []
    for item in run["results"]:
        try:
            sub_results.append(AgentResult.model_validate(item["result"]))
        except Exception:
            continue
    try:
        draft = BUILDERS["CHART_SYNTHESIS_AGENT"](context, sub_results)
    except Exception as exc:
        failed = invalid_result(
            "CHART_SYNTHESIS_AGENT", context,
            [f"builder exception: {type(exc).__name__}"],
            ["synthesis failed; sub-results preserved"])
        run["synthesis"] = _serialize(failed, context)
        return run
    ok, notes, parsed = validate_model_output(draft, context, "CHART_SYNTHESIS_AGENT")
    if not ok or parsed is None:
        failed = invalid_result("CHART_SYNTHESIS_AGENT", context, notes,
                                ["synthesis rejected; sub-results preserved"])
        run["synthesis"] = _serialize(failed, context)
        return run
    run["synthesis"] = _serialize(finalize_result(parsed, context), context)
    return run


def _serialize(result: Any, context: Any) -> Dict[str, Any]:
    payload = result.model_dump(mode="json")
    payload["_source"] = "production_agents"
    return {"agent_id": result.agent_id, "status": result.status,
            "result": payload}


def _record(agent_id: str, context: Any, result: Any,
            notes: List[str]) -> Dict[str, Any]:
    return {
        "agent_id": agent_id,
        "context_fingerprint": context.fingerprint(),
        "input_fingerprint": result.input_fingerprint,
        "output_fingerprint": result.output_fingerprint,
        "status": result.status,
        "validation_notes": sorted(notes),
    }


def get_production_agent_coverage() -> Dict[str, Any]:
    """Registry/coverage metadata for responses and tests."""
    reg = get_production_agent_registry()
    return {
        "agent_ids": get_production_agent_ids(),
        "domains": sorted(DOMAIN_ROUTES),
        "registry_fingerprint": reg.fingerprint(),
        "_source": "production_agents",
    }
