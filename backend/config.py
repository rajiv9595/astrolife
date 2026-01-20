import os

# Ephemeris Path
# Ephemeris Path
# Dynamically determine the path to the 'ephe' directory relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EPHE_PATH = os.getenv("EPHE_PATH", os.path.join(BASE_DIR, "ephe"))

# Auth Config (could be moved here from auth.py eventually, but keeping minimal changes)

# AI Configuration
# User will provide API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
