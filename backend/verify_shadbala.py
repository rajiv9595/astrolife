import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.calculations import compute_chart
from backend.shadbala import compute_shadbala

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
    
    print("\n--- Shadbala System ---")
    shadbala_data = compute_shadbala(chart_data["planets"], chart_data["asc_sign"], is_day_birth=False)
    print(json.dumps(shadbala_data, indent=2))
    
if __name__ == "__main__":
    test()
