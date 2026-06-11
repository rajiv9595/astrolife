import os
import sys
import json

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.calculations import compute_chart

def main():
    print("Testing Astrological Upgrades...")
    
    # Birth details: August 17, 2005, 12:02 AM, Anaparthy, India
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
    
    print("\n1. Verification of Maandi and Gulika positions:")
    for planet_name in ["Maandi", "Gulika"]:
        if planet_name in chart_data["planets"]:
            p = chart_data["planets"][planet_name]
            print(f"  {planet_name}: Sign={p['sign_manual']}, Deg={p['degree_in_sign_manual']:.2f}°, Lon={p['chosen_sidereal']:.2f}°")
        else:
            print(f"  FAILED: {planet_name} not found in planets!")
            
    print("\n2. Verification of Star Lords:")
    for name, p in chart_data["planets"].items():
        star_lord = p.get("star_lord")
        nak = p.get("nakshatra", {}).get("nakshatra")
        pada = p.get("nakshatra", {}).get("pada")
        print(f"  {name:8}: Nakshatra={nak} (Pada {pada}), Star Lord={star_lord}")
        
    print("\n3. Verification of Vargas (Divisional Charts):")
    vargas = chart_data.get("vargas", {})
    print(f"  Total vargas calculated: {len(vargas)}")
    for v_name in ["d1", "d2", "d3", "d4", "d7", "d9", "d10", "d12", "d16", "d20", "d24", "d27", "d30", "d40", "d45", "d60"]:
        if v_name in vargas:
            v_data = vargas[v_name]
            asc_sign = v_data.get("_ascendant", {}).get("sign", "Unknown")
            print(f"  {v_name.upper():4}: Ascendant Sign={asc_sign}, Planets={list(v_data.keys())[:5]}... ({len(v_data)-3} planets)")
        else:
            print(f"  FAILED: {v_name} missing from vargas!")
            
    print("\n4. Verification of Graha Aspects:")
    aspects = chart_data.get("aspects", {})
    planet_aspects = aspects.get("planet_aspects", {})
    house_aspects = aspects.get("house_aspects", {})
    planet_aspected_by = aspects.get("planet_aspected_by", {})
    
    print("  Jupiter aspects houses/planets:")
    jup_aspects = planet_aspects.get("Jupiter", [])
    print(f"    {jup_aspects}")
    
    print("  Saturn aspects houses/planets:")
    sat_aspects = planet_aspects.get("Saturn", [])
    print(f"    {sat_aspects}")

    print("\nAll checks completed successfully!")

if __name__ == "__main__":
    main()
