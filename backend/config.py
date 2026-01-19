import os

# Ephemeris Path
EPHE_PATH = os.getenv("EPHE_PATH", r"C:\Users\RAJIV MEDAPATI\Documents\lifepath\backend\ephe")

# Auth Config (could be moved here from auth.py eventually, but keeping minimal changes)

# AI Configuration
# User will provide API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCKy78lL3NEaBfa-G2Yj0jUFMh2V8ZJF-8")
GEMINI_MODEL = "gemini-2.5-flash"
