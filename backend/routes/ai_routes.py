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
Your goal is to engage in a helpful, strictly astrological conversation with the user based on the provided chart data.

CRITICAL RULES FOR INTERACTION:
1. **CONTEXTUAL RESPONSES ONLY**: 
   - If the user says "hello", "hi", or greets you, simply greet them back warmly as an astrologer (e.g., "Hari Om! I have your chart ready. What would you like to know?").
   - **DO NOT** vomit the entire chart analysis or list yogas/planets upon a simple greeting.
   - **DO NOT** provide data that was not asked for.
2. **ANSWER SPECIFICALLY**: 
   - If the user asks about "Career", look at the 10th house, Saturn, and relevant Yogas. Give that specific answer.
   - If the user asks about "Yogas", list the ones in the data.
   - If the user asks about "Money", look at the 2nd/11th houses and Dhana Yogas.
3. **EXPLAIN THE 'WHY'**: When you give an insight, briefly mention the astrological reason (e.g., "Because Jupiter is in your 5th house...").
4. **TONE**: Encouraging, wise, and grounded. Avoid fatalistic predictions.
5. **DATA USAGE**: 
   - Use the provided JSON data as your source of truth.
   - Do not hallucinate planetary positions.
   - Do not perform new calculations; interpret the provided ones.
6. **LANGUAGE ADAPTABILITY**:
   - **DETECT** the language of the USER QUERY (English, Telugu, Hindi, Hinglish, Teluglish, etc.).
   - **ALWAYS RESPOND IN THE SAME LANGUAGE**.
   - If the user speaks Telugu (e.g., "Meeru ela unnaru?"), reply in Telugu (Script or Transliteration as per user).
   - If the user speaks Hindi, reply in Hindi.
   - Ensure the meaning remains astrologically accurate regardless of language.

KNOWLEDGE BASE:
{knowledge_base}

Use the above knowledge to enrich your explanation if relevant to the USER'S QUESTION.
"""

def summarize_context(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarizes the massive chart data to fit within context window.
    Removes redundant timelines and unnecessary details.
    """
    summary = {}
    
    # 1. Basic User Info
    summary["user"] = {
        "name": data.get("user_name"),
        "birth": data.get("birth_details")
    }
    
    # 2. Key Chart Points
    summary["ascendant"] = data.get("ascendant", {}).get("sign", "Unknown")
    summary["moon_sign"] = data.get("moon_sign", "Unknown")
    
    # 3. Yogas (Only names and descriptions)
    if "yogas" in data:
        yogas = data["yogas"]
        # Limit to top 10 yogas to save space if there are many
        summary["yogas"] = yogas[:10] if isinstance(yogas, list) else yogas
        
    # 4. Planets (Super Simplified for small context)
    # Only keep 7 main planets
    if "planets" in data:
        planets_data = data["planets"]
        simple_planets = {}
        
        # Helper to extract sign
        def extract_sign(p_data):
            return p_data.get("sign_manual") or p_data.get("sign") or p_data.get("sign_name")

        # Handle Dictionary format (Main format)
        if isinstance(planets_data, dict):
            for name, p_info in planets_data.items():
                if name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
                    simple_planets[name] = extract_sign(p_info)
                    
        # Handle List format (Legacy/Backup)
        elif isinstance(planets_data, list):
            for p in planets_data:
                name = p.get("name")
                if name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
                    simple_planets[name] = extract_sign(p)
                    
        summary["planets"] = simple_planets

    # 5. Dasha (Critical optimization)
    # Instead of full hierarchy, just find the CURRENT Mahadasha and Antardasha
    current_dasha = data.get("current_dasha")
    if current_dasha:
        # We only need the top level and maybe current sub-period
        # We sanitize it to remove the nested 'antar_dashas' full list if it's endless
        
        sanitized_dasha = {
            "lord": current_dasha.get("lord"),
            "start": current_dasha.get("start_date"),
            "end": current_dasha.get("end_date")
        }
        
        # Find current antar dasha
        if "antar_dashas" in current_dasha:
            for ad in current_dasha["antar_dashas"]:
                if ad.get("is_current"):
                    sanitized_dasha["current_sub_period"] = {
                        "lord": ad.get("lord"),
                        "start": ad.get("start_date"),
                        "end": ad.get("end_date")
                    }
                    break
        
        summary["current_period"] = sanitized_dasha

    # 6. Lucky Factors (Keep as is, usually small)
    if "lucky_factors" in data:
        summary["lucky_factors"] = data["lucky_factors"]

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
