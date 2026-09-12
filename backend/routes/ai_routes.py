from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json

from backend.dependencies import get_current_user_optional
from backend.models import User
from backend.ai_engine import ai_engine
from backend.knowledge_base import get_knowledge_context

router = APIRouter(prefix="/ai", tags=["AI Astrologer"])

class AIRequest(BaseModel):
    query: str
    context_data: Dict[str, Any]  # The astrological data from frontend
    # Optional canonical transit wiring (additive; omitted => legacy behavior + explicit unavailable state).
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    second: Optional[int] = None
    tz: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    evaluation_datetime: Optional[str] = None
    evaluation_iso: Optional[str] = None
    evaluation_tz: Optional[str] = None
    eval_lat: Optional[float] = None
    eval_lon: Optional[float] = None
    eval_tz: Optional[str] = None
    include_transit_events: bool = False
    event_window_days: int = 7
    # Optional deterministic prediction output for the AI to interpret (verbatim, never re-timed).
    prediction_summary: Optional[Dict[str, Any]] = None


SYSTEM_PROMPT_TEMPLATE = """
You are an expert AI Vedic Astrologer called "LifePath AI".
Your goal is to engage in a helpful, strictly astrological, and highly professional conversation with the user based on the provided chart data.

You have access to a rich set of astrological details including Graha Aspects (Drishti), Star Lords (Nakshatra Lords), all 16 divisional varga charts (D1 to D60), and special mathematical points (Maandi and Gulika).

CRITICAL RULES FOR INTERACTION:
1. **CONTEXTUAL & PINPOINT RESPONSES ONLY**: 
   - If the user greets you, simply greet them back warmly as an astrologer (e.g., "Hari Om! I have your chart ready. What would you like to know?").
   - **DO NOT** vomit the entire chart analysis or list yogas/planets upon a simple greeting.
   - **DO NOT** provide data that was not asked for.
2. **ANSWER SPECIFICALLY & PROFESSIONAL SYNTHESIS**: 
   - If the user asks about "Career", look at the 10th house, Saturn, relevant Yogas, and D10 (Dasamsa) chart.
   - If the user asks about "Yogas", list the ones in the data.
   - If the user asks about "Money", look at the 2nd/11th houses, Dhana Yogas, and D2 (Hora) chart.
   - If they ask about challenges or obstacles, check the 6th/8th/12th houses, D30 (Trimsamsa), and Maandi/Gulika placements.
   - Incorporate aspect relationships (e.g., which planet is aspecting what) and Star Lord influences to give a pinpoint, 100% data-driven analysis.
3. **EXPLAIN THE 'WHY'**: When you give an insight, briefly explain the astrological reasons by citing the charts, signs, aspects, or star lords (e.g., "Because Saturn in your D10 is aspecting the 10th house..." or "Because Mars is sitting under the star lord Ketu...").
4. **TONE**: Encouraging, wise, professional, and grounded. Avoid fatalistic predictions.
5. **DATA USAGE**: 
   - Use the provided JSON data as your source of truth.
   - Do not hallucinate planetary positions.
   - Do not perform new calculations; interpret the provided ones.
6. **LANGUAGE ADAPTABILITY**:
   - **DETECT** the language of the USER QUERY (English, Telugu, Hindi, Hinglish, Teluglish, etc.).
   - **ALWAYS RESPOND IN THE SAME LANGUAGE**.
   - If the user speaks Telugu, reply in Telugu (Script or Transliteration as per user).
   - If the user speaks Hindi, reply in Hindi.
   - Ensure the meaning remains astrologically accurate regardless of language.

KNOWLEDGE BASE:
{knowledge_base}

Use the above knowledge to enrich your explanation if relevant to the USER'S QUESTION.

CANONICAL TRANSIT GROUNDING (authoritative):
- Treat canonical transit facts in CURRENT_TRANSITS / TRANSIT_NATAL_RELATIONS / TRANSIT_ASPECTS as authoritative.
- Do NOT recalculate planetary longitudes. Do NOT invent transit positions.
- Distinguish natal placement (NATAL_FACTS/planets) from current transit (CURRENT_TRANSITS).
- Use only backend-supplied transit-to-natal relationships/events.
- Do NOT claim a transit is active unless the backend supplies the relevant relationship/event.
- If transit status is "unavailable", explicitly say timing/current-transit analysis is unavailable rather than inventing it.
- prediction_candidates (when present) are deterministic engine output; interpret them, do not re-time events independently.
- AGENT_FINDINGS (when present) are deterministic specialist-agent output over canonical facts; restate and explain them, do not recalculate astrology, do not override their UNKNOWN/CONFLICTED states, and do not invent findings.
- DETERMINISTIC_PREDICTION (when present) is authoritative engine output; interpret it verbatim, never re-time events independently.
- FUTURE_WINDOW (when present) is the canonical evaluation of the user's requested future period (transits, exact events, dasha, windowed candidates with evidence/provenance). Use it to answer future-range questions. Do NOT claim future transit data are unavailable when FUTURE_WINDOW is present, and do NOT ask the user to manually provide transit details the backend already supplied.
- Timing semantics are strict: EXACT only from canonical exact timestamps; EVENT_WINDOW stays a range; UNKNOWN stays unknown. Prefer "stronger career/opportunity window" over guaranteed-date language unless the canonical system supplies exact timing.
"""

def summarize_context(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarizes the massive chart data to fit within context window.
    Extracts all 11 planets (9 traditional + Maandi & Gulika) with their houses,
    nakshatras, star lords, aspect networks, and key divisional charts.
    """
    summary = {}
    
    # 1. Basic User Info
    summary["user"] = {
        "name": data.get("user_name"),
        "birth": data.get("birth_details")
    }
    
    # 2. Key Chart Points
    summary["ascendant"] = {
        "sign": data.get("ascendant", {}).get("sign", "Unknown"),
        "nakshatra": data.get("ascendant", {}).get("nakshatra", {}).get("nakshatra", "Unknown"),
        "star_lord": data.get("ascendant", {}).get("star_lord", "Unknown")
    }
    summary["moon_sign"] = data.get("moon_sign", "Unknown")
    
    # 3. Yogas (Only names and descriptions)
    if "yogas" in data:
        yogas = data["yogas"]
        summary["yogas"] = yogas[:12] if isinstance(yogas, list) else yogas
        
    # 4. Planets (including Maandi, Gulika, and Star Lords)
    if "planets" in data:
        planets_data = data["planets"]
        simple_planets = {}
        
        asc_sign = data.get("ascendant", {}).get("sign")
        SIGNS_LIST = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        
        def get_house(p_sign):
            if not asc_sign or not p_sign: return None
            try:
                asc_idx = SIGNS_LIST.index(asc_sign)
                p_idx = SIGNS_LIST.index(p_sign)
                return ((p_idx - asc_idx) % 12) + 1
            except ValueError:
                return None

        if isinstance(planets_data, dict):
            for name, p_info in planets_data.items():
                if name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Maandi", "Gulika"]:
                    p_sign = p_info.get("sign_manual") or p_info.get("sign") or p_info.get("sign_name")
                    simple_planets[name] = {
                        "sign": p_sign,
                        "house": get_house(p_sign),
                        "degree": p_info.get("degree_in_sign_manual") or p_info.get("degree_in_sign_flag") or 0.0,
                        "nakshatra": p_info.get("nakshatra", {}).get("nakshatra", "Unknown"),
                        "star_lord": p_info.get("star_lord", "Unknown"),
                        "retrograde": p_info.get("retrograde", False),
                        "combust": p_info.get("combust", False)
                    }
        summary["planets"] = simple_planets

    # 5. Graha Aspects (Drishti)
    if "aspects" in data:
        summary["aspects"] = data["aspects"]
        
    # 6. Key Divisional Charts (Vargas)
    # Extract key vargas for comprehensive analysis
    if "vargas" in data:
        vargas_data = data["vargas"]
        key_vargas = {}
        for v_name in ["d1", "d2", "d3", "d9", "d10", "d30", "d60"]:
            if v_name in vargas_data:
                v_chart = vargas_data[v_name]
                v_planets = {}
                for p_name, p_val in v_chart.items():
                    if p_name.startswith("_") or p_name == "planets":
                        continue
                    v_planets[p_name] = {
                        "sign": p_val.get(f"{v_name}_sign"),
                        "retrograde": p_val.get("retrograde", False),
                        "combust": p_val.get("combust", False),
                        "debilitated": p_val.get("debilitated", False),
                        "exalted": p_val.get("exalted", False)
                    }
                v_asc = v_chart.get("_ascendant", {}).get("sign", "Unknown")
                key_vargas[v_name] = {
                    "ascendant": v_asc,
                    "planets": v_planets
                }
        summary["key_vargas"] = key_vargas

    # 7. Dasha (Current Mahadasha and sub-periods)
    current_dasha = data.get("current_dasha")
    if not current_dasha and "vimshottari" in data:
        timeline = data["vimshottari"].get("timeline", [])
        current_dasha = next((d for d in timeline if d.get("is_current")), None)
        
    if current_dasha:
        sanitized_dasha = {
            "lord": current_dasha.get("lord"),
            "start": current_dasha.get("start_date"),
            "end": current_dasha.get("end_date")
        }
        
        if "antar_dashas" in current_dasha:
            for ad in current_dasha["antar_dashas"]:
                if ad.get("is_current"):
                    sanitized_dasha["current_sub_period"] = {
                        "lord": ad.get("lord"),
                        "start": ad.get("start_date"),
                        "end": ad.get("end_date")
                    }
                    if "pratyantar_dashas" in ad:
                        for pd in ad["pratyantar_dashas"]:
                            if pd.get("is_current"):
                                sanitized_dasha["current_sub_sub_period"] = {
                                    "lord": pd.get("lord"),
                                    "start": pd.get("start_date"),
                                    "end": pd.get("end_date")
                                }
                                break
                    break
        summary["current_period"] = sanitized_dasha

    # 8. Lucky Factors
    if "lucky_factors" in data:
        summary["lucky_factors"] = {
            "lucky_days": data["lucky_factors"].get("lucky_days"),
            "lucky_planets": data["lucky_factors"].get("lucky_planets"),
            "life_gemstone": data["lucky_factors"].get("life_gemstone"),
            "lucky_gemstone": data["lucky_factors"].get("lucky_gemstone")
        }

    return summary

def build_expert_context(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a highly detailed context specifically for the Expert Report.
    Retains all advanced mathematical modules (Jaimini, Shadbala, etc.).
    """
    summary = summarize_context(data)
    
    # Inject advanced modules for the expert AI
    for key in ["jaimini", "ashtakavarga", "shadbala", "maitri", "panchanga_advanced", "mangal_dosha", "advanced_doshas", "doshas",
                "bhava_bala", "vimsopaka", "avastha", "functional_nature", "composite_strength", "rules"]:
        if key in data:
            summary[key] = data[key]
            
    return summary

@router.post("/analyze")
def analyze_astrology(
    req: AIRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Analyzes the provided astrology JSON data and answers the user's query.
    """
    if not current_user:
         pass
         
    # Prepare system prompt with knowledge base
    kb_context = get_knowledge_context()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.replace("{knowledge_base}", kb_context)
    
    # SUMMARIZE DATA BEFORE SENDING (natal preserved; transit enriches, never replaces)
    optimized_data = summarize_context(req.context_data)
    optimized_data = _attach_transit_section(optimized_data, req)
    optimized_data = _attach_future_section(optimized_data, req, req.query)
    optimized_data = _attach_agent_section(optimized_data, req, req.query)
    
    # Context data to string
    data_str = json.dumps(optimized_data, indent=2)
    
    # Append user query
    final_prompt = f"{system_prompt}\n\nUSER QUERY: {req.query}"
    
    # Call AI
    response_text = ai_engine.generate_analysis(final_prompt, data_str)
    
    return {"response": response_text}

class ExpertReportRequest(BaseModel):
    context_data: Dict[str, Any]
    # Optional canonical transit wiring (additive; same semantics as AIRequest).
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    second: Optional[int] = None
    tz: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    evaluation_datetime: Optional[str] = None
    evaluation_iso: Optional[str] = None
    evaluation_tz: Optional[str] = None
    eval_lat: Optional[float] = None
    eval_lon: Optional[float] = None
    eval_tz: Optional[str] = None
    include_transit_events: bool = False
    event_window_days: int = 7
    # Optional deterministic prediction output for the AI to interpret (verbatim, never re-timed).
    prediction_summary: Optional[Dict[str, Any]] = None


def _request_birth(req: Any) -> Optional[Dict[str, Any]]:
    """Extract birth params when fully supplied; else None (legacy path)."""
    try:
        y, m, d = req.year, req.month, req.day
        if y is None or m is None or d is None:
            return None
        if req.tz is None or req.lat is None or req.lon is None:
            return None
        return {
            "year": int(y), "month": int(m), "day": int(d),
            "hour": int(req.hour or 0), "minute": int(req.minute or 0),
            "second": int(req.second or 0),
            "tz": str(req.tz), "lat": float(req.lat), "lon": float(req.lon),
        }
    except Exception:
        return None


def _request_eval_iso(req: Any) -> Optional[str]:
    return req.evaluation_datetime if getattr(req, "evaluation_datetime", None) else getattr(req, "evaluation_iso", None)


def _attach_transit_section(optimized_data: Dict[str, Any], req: Any) -> Dict[str, Any]:
    """
    Enrich (never replace) natal context with canonical transit facts.
    Backward compatible: missing birth => explicit unavailable state.
    """
    from backend.ai_transit_context import (
        build_canonical_transit_section,
        transit_unavailable_section,
    )

    birth = _request_birth(req)
    if birth is None:
        optimized_data["TRANSIT_STATUS"] = "unavailable-no-birth-params"
        optimized_data.update(transit_unavailable_section("no-birth-params"))
        return optimized_data
    try:
        section = build_canonical_transit_section(
            **birth,
            evaluation_iso=_request_eval_iso(req),
            evaluation_tz=getattr(req, "evaluation_tz", None),
            eval_lat=getattr(req, "eval_lat", None),
            eval_lon=getattr(req, "eval_lon", None),
            eval_tz=getattr(req, "eval_tz", None),
            include_events=bool(getattr(req, "include_transit_events", False)),
            event_window_days=int(getattr(req, "event_window_days", 7) or 7),
        )
    except Exception as exc:
        optimized_data["TRANSIT_STATUS"] = f"unavailable-error: {exc}"
        optimized_data.update(transit_unavailable_section(f"error: {exc}"))
        return optimized_data
    # Distinct keys per spec; natal summary keys untouched.
    for key in ("NATAL_FACTS", "CURRENT_EVALUATION", "CURRENT_TRANSITS",
                "TRANSIT_NATAL_RELATIONS", "TRANSIT_ASPECTS", "TRANSIT_EVENTS",
                "DASHA", "OTHER_CANONICAL_FACTS", "PROVENANCE"):
        if key in section:
            optimized_data[key] = section[key]
    optimized_data["TRANSIT_STATUS"] = "available" if section.get("_transit_available") else "unavailable"
    optimized_data["_dynamic_state_evaluation_utc_iso"] = (
        section.get("CURRENT_EVALUATION", {}) or {}
    ).get("evaluation_utc_iso")
    # Part D: deterministic prediction output passes through verbatim for interpretation.
    pred = getattr(req, "prediction_summary", None)
    if pred is not None:
        optimized_data["DETERMINISTIC_PREDICTION"] = pred
    return optimized_data

def _attach_agent_section(optimized_data: Dict[str, Any], req: Any,
                          query: str = "") -> Dict[str, Any]:
    """
    Attach deterministic specialist-agent findings (Migration #10, additive).

    Agents run as pure functions over canonical production data already in
    context; they calculate nothing. On any failure an explicit unavailable
    marker is set — never fabricated findings.
    """
    try:
        from backend.canonical_agents import (
            build_agent_context_from_compute,
            run_full_production_with_synthesis,
        )
    except ImportError:  # pragma: no cover - alternate import root
        from canonical_agents import (  # type: ignore
            build_agent_context_from_compute,
            run_full_production_with_synthesis,
        )
    try:
        transit_section = {
            key: optimized_data.get(key)
            for key in ("CURRENT_TRANSITS", "TRANSIT_NATAL_RELATIONS",
                        "TRANSIT_ASPECTS", "TRANSIT_EVENTS", "DASHA")
            if optimized_data.get(key) is not None
        }
        context = build_agent_context_from_compute(
            getattr(req, "context_data", {}) or {},
            question=query or "",
            transit_section=transit_section,
            prediction_summary=optimized_data.get("DETERMINISTIC_PREDICTION"),
        )
        full = run_full_production_with_synthesis(context)
        optimized_data["AGENT_FINDINGS"] = full
        optimized_data["AGENT_STATUS"] = "available"
    except Exception as exc:
        optimized_data["AGENT_FINDINGS"] = {
            "status": "unavailable", "reason": f"{type(exc).__name__}",
            "_source": "production_agents",
        }
        optimized_data["AGENT_STATUS"] = "unavailable"
    return optimized_data

def _attach_future_section(optimized_data: Dict[str, Any], req: Any,
                           query: str = "") -> Dict[str, Any]:
    """
    Attach canonical future-window evaluation (post-release bugfix, additive).

    When the user query names a future date range and birth params are
    present, the requested interval is evaluated with the existing canonical
    engines (no new astrology). A caller-supplied DETERMINISTIC_PREDICTION
    is never overridden. Any engine failure yields an explicit unavailable
    marker — never fabricated timing.
    """
    try:
        from backend.future_window import (
            build_future_window_section,
            parse_requested_range,
        )
    except ImportError:  # pragma: no cover - alternate import root
        from future_window import (  # type: ignore
            build_future_window_section,
            parse_requested_range,
        )
    birth = _request_birth(req)
    if birth is None or not query:
        return optimized_data
    if optimized_data.get("DETERMINISTIC_PREDICTION") is not None:
        return optimized_data
    try:
        from datetime import datetime as _dt
        from datetime import timezone as _tzmod
        tz_name = (getattr(req, "evaluation_tz", None)
                   or getattr(req, "eval_tz", None)
                   or birth.get("tz") or "UTC")
        now = _dt.now(_tzmod.utc)
        parsed = parse_requested_range(query, now, tz_name)
        if parsed is None:
            return optimized_data
        section = build_future_window_section(
            year=birth["year"], month=birth["month"], day=birth["day"],
            hour=birth.get("hour", 0), minute=birth.get("minute", 0),
            second=birth.get("second", 0), tz=birth.get("tz", "UTC"),
            lat=birth.get("lat", 0.0), lon=birth.get("lon", 0.0),
            range_start=parsed["future_start"], range_end=parsed["future_end"],
            eval_tz=getattr(req, "eval_tz", None),
            eval_lat=getattr(req, "eval_lat", None),
            eval_lon=getattr(req, "eval_lon", None),
            label=parsed["label"],
        )
        optimized_data["FUTURE_WINDOW"] = section
        optimized_data["FUTURE_WINDOW_STATUS"] = "available"
        optimized_data["DETERMINISTIC_PREDICTION"] = {
            "status": (section.get("PREDICTION") or {}).get("status"),
            "candidates": (section.get("PREDICTION") or {}).get("candidates", []),
            "source": "canonical-future-window",
        }
    except Exception as exc:
        optimized_data["FUTURE_WINDOW"] = {
            "status": "unavailable", "reason": f"{type(exc).__name__}",
            "_source": "canonical",
        }
        optimized_data["FUTURE_WINDOW_STATUS"] = "unavailable"
    return optimized_data

@router.post("/expert_report")
def generate_expert_report(
    req: ExpertReportRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Generates a massive, structured JSON life reading based on all advanced chart data.
    """
    try:
        expert_context = build_expert_context(req.context_data)
        expert_context = _attach_transit_section(expert_context, req)
        expert_context = _attach_future_section(expert_context, req, "")
        expert_context = _attach_agent_section(expert_context, req, "")
        data_str = json.dumps(expert_context, indent=2)
        
        json_response = ai_engine.generate_expert_report(data_str)
        
        # We need to return this as a parsed dictionary because FastAPI will re-serialize it
        try:
            parsed = json.loads(json_response)
            return {"report": parsed}
        except json.JSONDecodeError:
            print("Failed to parse Gemini JSON:", json_response)
            return {"error": "AI returned malformed JSON.", "raw": json_response}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
