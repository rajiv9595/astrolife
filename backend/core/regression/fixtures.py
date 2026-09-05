"""
Phase 10 — fixtures: documented synthetic inputs. No random charts.
"""
from __future__ import annotations

from typing import Any, Dict, List


def chart_inputs(chart_id: str, hour: int, minute: int) -> Dict[str, Any]:
    return {"chart_id": chart_id, "year": 2005, "month": 8, "day": 17,
            "hour": hour, "minute": minute, "second": 0,
            "lat": 16.93407, "lon": 81.95522, "tz_name": "Asia/Kolkata",
            "location_name": "Anaparthy", "country_name": "India"}


def boundary_longitudes(divisions: int) -> List[Dict[str, Any]]:
    """Structural boundary probes for a division count (no expected signs
    here; expectations live in frozen golden data)."""
    size = 30.0 / divisions
    probes = [{"label": "zero", "deg": 0.0}]
    b = size
    probes.append({"label": "boundary_minus_eps", "deg": b - 5e-10})
    probes.append({"label": "boundary", "deg": b})
    probes.append({"label": "boundary_plus_eps", "deg": b + 5e-10})
    probes.append({"label": "last_segment_mid", "deg": 30.0 - size / 2.0})
    probes.append({"label": "thirty_minus_eps", "deg": 30.0 - 5e-10})
    return probes
