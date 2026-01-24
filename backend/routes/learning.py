from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import google.generativeai as genai
from backend.auth_routes import get_current_user
from backend.models import User

# Load learning modules
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "learning_modules.json")

def load_modules():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

modules_cache = load_modules()

router = APIRouter(prefix="/learn", tags=["learning"])

# Setup Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("Warning: GOOGLE_API_KEY not set for AI Guru")

# --- Models ---
class ChatRequest(BaseModel):
    message: str
    current_module_id: Optional[str] = None
    current_lesson_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    references: Optional[List[str]] = []

# --- Routes ---

@router.get("/modules")
def get_modules(current_user: User = Depends(get_current_user)):
    """Get all learning modules structure."""
    return modules_cache

@router.post("/guru-chat", response_model=ChatResponse)
def chat_with_guru(req: ChatRequest, current_user: User = Depends(get_current_user)):
    """Chat with the AI Astrology Teacher."""
    
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=503, detail="AI Service unavailable (Missing Key)")

    try:
        # Build Context
        context_text = ""
        
        # 1. Add specific lesson context if user is reading one
        if req.current_lesson_id and req.current_module_id:
            module = next((m for m in modules_cache if m["id"] == req.current_module_id), None)
            if module:
                lesson = next((l for l in module["lessons"] if l["id"] == req.current_lesson_id), None)
                if lesson:
                    context_text += f"\n[User is currently reading: {module['title']} - {lesson['title']}]\nContent: {lesson['content']}\n"

        # 2. Add general context (summary of all titles) to help AI know what's in the course
        course_outline = "\nCourse Structure:"
        for m in modules_cache:
            course_outline += f"\n- {m['title']}"
            for l in m['lessons']:
                course_outline += f"\n  -- {l['title']}"
        
        # 3. System Prompt
        system_prompt = f"""
You are 'Guru-ji', a wise, patient, and knowledgeable Vedic Astrology Teacher.
You are teaching a student named {current_user.name}.
Your goal is to explain astrology concepts clearly, using simple analogies.
Always refer to the course material if relevant.
If the user asks something covered in the course, encourage them to read that specific module, but still give a brief answer.
Context about the course:
{course_outline}

{context_text}

User Question: {req.message}

Answer as Guru-ji:
"""
        
        # Call Gemini
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(system_prompt)
        
        return {
            "reply": response.text,
            "references": [req.current_lesson_id] if req.current_lesson_id else []
        }

    except Exception as e:
        print(f"AI Guru Error: {e}")
        raise HTTPException(status_code=500, detail="Guru is meditating (Server Error)")
