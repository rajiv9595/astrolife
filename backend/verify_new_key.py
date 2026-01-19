import google.generativeai as genai
import os

API_KEY = "AIzaSyCKy78lL3NEaBfa-G2Yj0jUFMh2V8ZJF-8"

print(f"Testing New Key: {API_KEY[:10]}...")

try:
    genai.configure(api_key=API_KEY)
    
    print("Listing available models...")
    found_any = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            found_any = True
            print(f"Available: {m.name}")
        
    if not found_any:
        print("No content generation models found for this key.")

except Exception as e:
    print(f"KEY ERROR: {e}")
