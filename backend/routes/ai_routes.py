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
    
    # SUMMARIZE DATA BEFORE SENDING
    optimized_data = summarize_context(req.context_data)
    
    # Context data to string
    data_str = json.dumps(optimized_data, indent=2)
    
    # Append user query
    final_prompt = f"{system_prompt}\n\nUSER QUERY: {req.query}"
    
    # Call AI
    response_text = ai_engine.generate_analysis(final_prompt, data_str)
    
    return {"response": response_text}
