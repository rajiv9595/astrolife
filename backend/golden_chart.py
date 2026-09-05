import sys
import json
from datetime import datetime
from calculations import compute_chart

def generate_golden_chart():
    # Name: MEDAPATI BHASKARA VENKATA RAJEEV REDDY
    # Date: 17 August 2005
    # Time: 00:02:00 IST
    # Timezone: Asia/Kolkata
    # Place: Anaparthy, Andhra Pradesh, India
    # Coordinates: Latitude = 16.93407, Longitude = 81.95522

    # compute_chart(year, month, day, hour, minute, second, tz, lat, lon)
    chart = compute_chart(
        year=2005,
        month=8,
        day=17,
        hour=0,
        minute=2,
        second=0,
        lat=16.93407,
        lon=81.95522,
        tz="Asia/Kolkata"
    )

    print(json.dumps(chart, indent=2))

if __name__ == "__main__":
    generate_golden_chart()
