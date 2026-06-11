"""
AI Engine Module
Handles interaction with Google Gemini (gemini-1.5-pro).
"""

import os
import google.generativeai as genai
from backend.config import GOOGLE_API_KEY, GEMINI_MODEL

class AIEngine:
    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        self.model_name = GEMINI_MODEL
        self.client = None
        self.model = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.client = "gemini"
                print(f"AI Engine initialized with Google Gemini model: {self.model_name}")
            except Exception as e:
                print(f"AI Engine Init Error: {e}")
                print("Attempting to list available models for debugging...")
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            print(f"- {m.name}")
                except Exception as ex:
                    print(f"Could not list models: {ex}")
        else:
            print("AI Engine Warning: No Google API Key found.")

    def generate_analysis(self, system_prompt: str, user_data: str) -> str:
        """
        Generates analysis based on system prompt and data using Google Gemini.
        """
        if not self.model:
            return "AI Service Unavailable: API Key not configured or Model init failed."

        try:
            # Construct the full prompt
            full_prompt = f"{system_prompt}\n\nUSER DATA:\n{user_data}"
            
            # Generate content
            response = self.model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            import traceback
            print(f"CRITICAL GEMINI ERROR: {str(e)}")
            traceback.print_exc()
            return self._fallback_response(user_data)

    def _fallback_response(self, user_data_str: str) -> str:
        """
        return "I apologize, but I'm having trouble connecting to the cosmic intelligence network regarding Gemini. Please try again in a moment."

    def generate_expert_report(self, user_data: str) -> str:
        """
        Generates a structured JSON report based on the full chart.
        """
        if not self.model:
            return '{"error": "AI Service Unavailable"}'

        system_prompt = """
        You are a legendary Master Vedic Astrologer. You have profound knowledge of Parasara, Jaimini, Ashtakavarga, and Shadbala systems.
        Analyze the provided chart data comprehensively.
        
        OUTPUT FORMAT:
        You MUST return a valid JSON object EXACTLY matching this schema, with no markdown formatting or extra text outside the JSON:
        {
          "personality": {
            "summary": "Detailed paragraph about their core nature (Lagna, Moon, Atmakaraka).",
            "strengths": ["Trait 1", "Trait 2", "Trait 3"],
            "weaknesses": ["Trait 1", "Trait 2", "Trait 3"]
          },
          "career": {
            "summary": "Analysis of 10th house, D10 chart, Amatyakaraka, and Shadbala of career significators.",
            "favorable_fields": ["Field 1", "Field 2", "Field 3"]
          },
          "wealth": {
            "summary": "Analysis of 2nd/11th houses, Dhana Yogas, and Ashtakavarga points.",
            "financial_yogas_present": ["Yoga 1", "Yoga 2"]
          },
          "love_and_marriage": {
            "summary": "Analysis of 7th house, Venus/Jupiter, D9 Navamsa, and Darakaraka.",
            "partner_traits": "Description of ideal or destined partner traits."
          },
          "health": {
            "summary": "Analysis of 6th house, Ascendant lord strength, and malefic aspects.",
            "vulnerable_areas": ["Area 1", "Area 2"]
          },
          "karmic_remedies": [
            "Actionable remedy 1 based on Doshas or weak planets",
            "Actionable remedy 2"
          ]
        }
        
        RULES:
        1. Base your analysis strictly on the provided JSON chart data.
        2. Incorporate references to the advanced data (e.g. "Because your Atmakaraka is...").
        3. Do not be overly fatalistic; frame challenges as areas for growth.
        4. Return ONLY valid JSON.
        """

        try:
            full_prompt = f"{system_prompt}\n\nUSER CHART DATA:\n{user_data}"
            
            # Request JSON response format
            response = self.model.generate_content(
                full_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return response.text
            
        except Exception as e:
            import traceback
            print(f"CRITICAL GEMINI ERROR (EXPERT REPORT): {str(e)}")
            traceback.print_exc()
            return '{"error": "Analysis failed due to a cosmic interference. Please try again."}'

# Global instance
ai_engine = AIEngine()
