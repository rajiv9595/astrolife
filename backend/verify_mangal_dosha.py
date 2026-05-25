import os
import sys
import json

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.calculations import compute_chart

def main():
    print("Testing Mangal Dosha calculations on August 17, 2005 (Anaparthy, India)...")
    
    # 17-08-2005 12:02 AM Anaparthy (coordinates roughly 16.9379 N, 81.9798 E)
    params = {
        "year": 2005,
        "month": 8,
        "day": 17,
        "hour": 0,
        "minute": 2,
        "second": 0,
        "tz": "Asia/Kolkata",
        "lat": 16.9379,
        "lon": 81.9798,
        "planets": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"],
        "topo_alt": 0.0
    }
    
    chart_data = compute_chart(**params)
    
    print("\n--- Birth Chart Essentials ---")
    print(f"Ascendant (Lagna) Sign: {chart_data['ascendant']['sign']}")
    print(f"Moon Sign: {chart_data['moon_sign']}")
    print(f"Mars Sign: {chart_data['planets']['Mars']['sign_manual']}")
    print(f"Venus Sign: {chart_data['planets']['Venus']['sign_manual']}")
    print(f"Jupiter Sign: {chart_data['planets']['Jupiter']['sign_manual']}")
    
    print("\n--- Mangal Dosha Verdict ---")
    mangal = chart_data.get("mangal_dosha", {})
    print(f"Has Dosha: {mangal.get('has_dosha')}")
    print(f"Verdict: {mangal.get('verdict')}")
    print(f"Cancellations Found: {mangal.get('cancellations_found')}")
    
    print("\n--- Breakdown Details ---")
    print(json.dumps(mangal.get("details", {}), indent=2))

if __name__ == "__main__":
    main()
