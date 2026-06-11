import os
import sys

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.calculations import compute_chart

def main():
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
    vargas = chart_data.get("vargas", {})
    
    # Let's map sign numbers to sign names
    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    print("COMPARISON OF DIVISIONAL CHARTS (VARGAS)")
    print("=" * 60)
    
    for v_name in ["d1", "d2", "d3", "d4", "d7", "d9", "d10", "d12", "d16", "d20", "d24", "d27", "d30", "d40", "d45", "d60"]:
        if v_name not in vargas:
            continue
        v_chart = vargas[v_name]
        asc_sign = v_chart.get("_ascendant", {}).get("sign", "Unknown")
        print(f"\n{v_name.upper()} Chart - Ascendant: {asc_sign}")
        
        # Sort planets by traditional order
        planets_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        planets_in_signs = {}
        for p_name in planets_order:
            if p_name in v_chart:
                p_val = v_chart[p_name]
                sign = p_val.get(f"{v_name}_sign")
                planets_in_signs[p_name] = sign
            
        # Print grouped by sign so it's easy to read like a chart
        sign_to_planets = {s: [] for s in SIGNS}
        for p_name, sign in planets_in_signs.items():
            if sign in sign_to_planets:
                sign_to_planets[sign].append(p_name[:2]) # short name
                
        # Also print list
        list_str = ", ".join([f"{p_name}: {sign}" for p_name, sign in planets_in_signs.items()])
        print(f"  Planets list: {list_str}")
        
if __name__ == "__main__":
    main()
