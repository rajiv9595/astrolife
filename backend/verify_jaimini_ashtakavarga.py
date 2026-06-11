import json
import sys
import os

# Add the parent directory to the path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.calculations import compute_chart
from backend.jaimini import compute_jaimini_system
from backend.ashtakavarga import compute_ashtakavarga

def test():
    # User's birth details: Aug 17, 2005, 12:02 AM, Anaparthy
    # Anaparthy approx lat/lon: 16.9409, 81.9961
    # Timezone: 5.5
    
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
    
    print(f"asc_sign: {chart_data['asc_sign']}")
    
    # Print the structure of the Sun object to see its keys
    if isinstance(chart_data["planets"], dict) and "Sun" in chart_data["planets"]:
        print(f"Sun keys: {chart_data['planets']['Sun'].keys()}")
    elif isinstance(chart_data["planets"], list) and len(chart_data["planets"]) > 0:
        print(f"First planet keys: {chart_data['planets'][0].keys()}")
        
    print("\n--- Jaimini System ---")
    jaimini_data = compute_jaimini_system(chart_data["planets"], chart_data["asc_sign"])
    print(json.dumps(jaimini_data, indent=2))
    
    print("\n--- Ashtakavarga System ---")
    ashtakavarga_data = compute_ashtakavarga(chart_data["planets"], chart_data["asc_sign"])
    print(json.dumps(ashtakavarga_data, indent=2))
    
if __name__ == "__main__":
    test()
