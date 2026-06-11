import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.calculations import compute_chart
from backend.maitri import compute_maitri_chakra
from backend.panchanga_advanced import compute_advanced_panchanga
from backend.doshas_advanced import compute_advanced_doshas

def test():
    chart_data = compute_chart(
        year=2005,
        month=8,
        day=17,
        hour=0,
        minute=2,
        second=0,
        tz="Asia/Kolkata",
        lat=16.9409,
        lon=81.9961,
        planets=[],
        topo_alt=0.0
    )
    
    print("\n--- Maitri Chakra ---")
    maitri = compute_maitri_chakra(chart_data["planets"])
    print(json.dumps(maitri["Sun"], indent=2))  # Just print Sun to save space
    
    print("\n--- Advanced Panchanga ---")
    moon_n = chart_data["planets"]["Moon"]["nakshatra"]["nakshatra"]
    panch = compute_advanced_panchanga(chart_data["moon_sign"], moon_n)
    print(json.dumps(panch, indent=2))
    
    print("\n--- Advanced Doshas ---")
    doshas = compute_advanced_doshas(chart_data["planets"], chart_data["asc_sign"])
    print(json.dumps(doshas, indent=2))

if __name__ == "__main__":
    test()
