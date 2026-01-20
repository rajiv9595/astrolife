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
        Provides a safe, rule-based fallback if AI is down.
        """
        return "I apologize, but I'm having trouble connecting to the cosmic intelligence network regarding Gemini. Please try again in a moment."

# Global instance
ai_engine = AIEngine()
