import json

with open("golden_chart.txt", "r", encoding="utf-8") as f:
    data = json.load(f)

md = []
md.append("# Astrolife V2 - Phase 0: Golden Chart Baseline")
md.append("")
md.append("This document records the exact output of the legacy calculation engine for the following birth data:")
md.append("- **Name**: MEDAPATI BHASKARA VENKATA RAJEEV REDDY")
md.append("- **Date**: 17 August 2005")
md.append("- **Time**: 00:02:00 IST")
md.append("- **Timezone**: Asia/Kolkata")
md.append("- **Place**: Anaparthy, Andhra Pradesh, India")
md.append("- **Coordinates**: Latitude = 16.93407, Longitude = 81.95522")
md.append("- **Calculation Profile**: Zodiac = SIDEREAL, Ayanamsha = SWISS EPHEMERIS STANDARD LAHIRI, Node = MEAN RAHU, House system = WHOLE SIGN")
md.append("")
md.append("## Core Baseline Values")
md.append(f"- **Julian Day (UTC)**: {data['jd_ut']}")
md.append(f"- **Ayanamsha**: {data['ayanamsha_deg']} degrees")
md.append(f"- **Ascendant (Sidereal Degree)**: {data['asc_sidereal']} degrees")
md.append(f"- **Ascendant (Sign)**: {data['asc_sign']}")
md.append("")

md.append("## Planetary Positions")
md.append("| Planet | Sign | Degree | House | Nakshatra | Pada | D9 Sign | D10 Sign |")
md.append("|--------|------|--------|-------|-----------|------|---------|----------|")

for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
    if p in data["planets"]:
        pdata = data["planets"][p]
        house = pdata.get("house", "Unknown") # actually house is in houses array
        
        # let's find the house from houses if possible
        found_house = "Unknown"
        for h in data.get("houses", []):
            if p in h.get("planets", []):
                found_house = h.get("house", "Unknown")
                break
                
        md.append(f"| {p} | {pdata['sign_flag']} | {pdata['degree_in_sign_flag']:.4f} | {found_house} | {pdata['nakshatra']['nakshatra']} | {pdata['nakshatra']['pada']} | {pdata.get('d9_sign', 'N/A')} | {pdata.get('d10_sign', 'N/A')} |")

md.append("")
with open("../ASTROLIFE_V2_GOLDEN_CHART.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print("Done")
