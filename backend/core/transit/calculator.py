"""
Transit Calculator — pure, SWE-based.

For any evaluation_datetime (explicit), compute transit positions for
Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
with:
  tropical longitude, sidereal longitude, latitude, speed, retrograde,
  sign, degree, nakshatra, pada

Controlled by CalculationProfile (zodiac, ayanamsha, node).
Defaults: SIDEREAL, LAHIRI_STANDARD, MEAN_NODE

Precision: full double internally, no rounding before calcs.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import math
import swisseph as swe
from pydantic import BaseModel, Field

from ..calculation.config import CalculationProfile, DEFAULT_PROFILE, AyanamshaSystem, NodeSystem
from ..calculation.nakshatra import get_nakshatra_from_longitude
from ..calculation.houses import get_sign_from_longitude

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

PLANET_SWE = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

class TransitPlanetPosition(BaseModel):
    name: str
    tropical_longitude: float
    sidereal_longitude: float
    latitude: float
    distance: float
    speed_longitude: float
    retrograde: bool
    sign: str
    sign_num: int  # 1..12
    degree_in_sign: float
    nakshatra: str
    nakshatra_index: int  # 0..26
    pada: int  # 1..4
    nakshatra_lord: str
    system: str = "SIDEREAL"
    ayanamsha_used: float

class TransitSnapshot(BaseModel):
    evaluation_jd: float
    evaluation_utc_iso: str
    profile: CalculationProfile
    planets: Dict[str, TransitPlanetPosition]
    ayanamsha: float
    ayanamsha_system: str

def _evaluation_jd(evaluation_datetime: datetime) -> float:
    if evaluation_datetime.tzinfo is None:
        dt_utc = evaluation_datetime.replace(tzinfo=timezone.utc)
    else:
        dt_utc = evaluation_datetime.astimezone(timezone.utc)
    ut_dec = dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0 + dt_utc.microsecond/3600.0/1_000_000.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut_dec, swe.GREG_CAL)

def _jd_to_utc_iso(jd: float) -> str:
    import math as _m
    y,m,d,h_dec = swe.revjul(jd, swe.GREG_CAL)
    h = int(_m.floor(h_dec))
    min_dec = (h_dec - h)*60.0
    mi = int(_m.floor(min_dec))
    sec_dec = (min_dec - mi)*60.0
    sec_int = int(_m.floor(sec_dec))
    micro = int(round((sec_dec - sec_int)*1_000_000))
    if micro >= 1_000_000:
        micro -= 1_000_000; sec_int+=1
    if sec_int>=60: sec_int-=60; mi+=1
    if mi>=60: mi-=60; h+=1
    if h>=24: h=23; mi=59; sec_int=59; micro=999999
    try:
        dt = datetime(y,m,d,h,mi,sec_int,micro,tzinfo=timezone.utc)
    except ValueError:
        dt = datetime(1900,1,1,tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00","Z")

def calculate_transit_positions(
    evaluation_datetime: datetime,
    profile: Optional[CalculationProfile] = None,
) -> TransitSnapshot:
    """
    Pure: compute all transit planets at evaluation_datetime.
    No clock read except via explicit evaluation_datetime.
    """
    if profile is None:
        profile = DEFAULT_PROFILE
    jd = _evaluation_jd(evaluation_datetime)

    # ayanamsha
    if profile.ayanamsha == AyanamshaSystem.LAHIRI_STANDARD:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        ay = swe.get_ayanamsa_ut(jd)
    else:
        raise ValueError(f"Unsupported ayanamsha {profile.ayanamsha}")

    node_flag = swe.MEAN_NODE if profile.node == NodeSystem.MEAN else swe.TRUE_NODE

    planets: Dict[str, TransitPlanetPosition] = {}

    for name, pid in PLANET_SWE.items():
        res, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)
        lon_trop = float(res[0])
        lat = float(res[1])
        dist = float(res[2])
        speed = float(res[3])
        lon_sid = (lon_trop - ay) % 360.0
        sign_id, sign_name, deg = get_sign_from_longitude(lon_sid)
        nak = get_nakshatra_from_longitude(lon_sid)
        planets[name] = TransitPlanetPosition(
            name=name,
            tropical_longitude=lon_trop,
            sidereal_longitude=lon_sid,
            latitude=lat, distance=dist,
            speed_longitude=speed,
            retrograde=speed < 0,
            sign=sign_name, sign_num=sign_id, degree_in_sign=deg,
            nakshatra=nak.name, nakshatra_index=nak.id-1, pada=nak.pada, nakshatra_lord=nak.lord,
            ayanamsha_used=ay
        )

    # Rahu
    res_node, _ = swe.calc_ut(jd, node_flag, swe.FLG_SWIEPH | swe.FLG_SPEED)
    rahu_trop = float(res_node[0])
    rahu_lat = float(res_node[1])
    rahu_dist = float(res_node[2])
    rahu_speed = float(res_node[3])
    rahu_sid = (rahu_trop - ay) % 360.0
    sign_id, sign_name, deg = get_sign_from_longitude(rahu_sid)
    nak = get_nakshatra_from_longitude(rahu_sid)
    planets["Rahu"] = TransitPlanetPosition(
        name="Rahu", tropical_longitude=rahu_trop, sidereal_longitude=rahu_sid,
        latitude=rahu_lat, distance=rahu_dist, speed_longitude=rahu_speed, retrograde=rahu_speed < 0,
        sign=sign_name, sign_num=sign_id, degree_in_sign=deg,
        nakshatra=nak.name, nakshatra_index=nak.id-1, pada=nak.pada, nakshatra_lord=nak.lord,
        ayanamsha_used=ay
    )
    # Ketu opposite
    ketu_trop = (rahu_trop + 180.0) % 360.0
    ketu_sid = (rahu_sid + 180.0) % 360.0
    sign_id, sign_name, deg = get_sign_from_longitude(ketu_sid)
    nak = get_nakshatra_from_longitude(ketu_sid)
    planets["Ketu"] = TransitPlanetPosition(
        name="Ketu", tropical_longitude=ketu_trop, sidereal_longitude=ketu_sid,
        latitude=-rahu_lat, distance=rahu_dist, speed_longitude=rahu_speed, retrograde=rahu_speed < 0,
        sign=sign_name, sign_num=sign_id, degree_in_sign=deg,
        nakshatra=nak.name, nakshatra_index=nak.id-1, pada=nak.pada, nakshatra_lord=nak.lord,
        ayanamsha_used=ay
    )

    return TransitSnapshot(
        evaluation_jd=jd,
        evaluation_utc_iso=_jd_to_utc_iso(jd),
        profile=profile,
        planets=planets,
        ayanamsha=ay,
        ayanamsha_system=profile.ayanamsha.value
    )

def calculate_transits(
    start_datetime: datetime,
    end_datetime: datetime,
    profile: Optional[CalculationProfile] = None,
    step_days: float = 1.0,
) -> list[TransitSnapshot]:
    """
    Range version: sample from start to end inclusive with step_days.
    Pure — no today dependency. UI can request 7 days, 5 months, etc.
    No special-case for five months — just date math.
    """
    if start_datetime.tzinfo is None:
        start_dt = start_datetime.replace(tzinfo=timezone.utc)
    else:
        start_dt = start_datetime.astimezone(timezone.utc)
    if end_datetime.tzinfo is None:
        end_dt = end_datetime.replace(tzinfo=timezone.utc)
    else:
        end_dt = end_datetime.astimezone(timezone.utc)
    if end_dt < start_dt:
        raise ValueError("end_datetime must be after start_datetime")

    jd_start = _evaluation_jd(start_dt)
    jd_end = _evaluation_jd(end_dt)
    snapshots: list[TransitSnapshot] = []
    jd = jd_start
    while jd <= jd_end + 1e-9:
        dt = _jd_to_datetime(jd)
        snapshots.append(calculate_transit_positions(dt, profile))
        jd += step_days
    # ensure end included exactly
    if snapshots and abs(snapshots[-1].evaluation_jd - jd_end) > 1e-9:
        snapshots.append(calculate_transit_positions(end_dt, profile))
    return snapshots

def _jd_to_datetime(jd: float) -> datetime:
    y,m,d,h_dec = swe.revjul(jd, swe.GREG_CAL)
    h = int(math.floor(h_dec))
    min_dec = (h_dec - h)*60.0
    mi = int(math.floor(min_dec))
    sec_dec = (min_dec - mi)*60.0
    sec_int = int(math.floor(sec_dec))
    micro = int(round((sec_dec - sec_int)*1_000_000))
    if micro>=1_000_000: micro-=1_000_000; sec_int+=1
    if sec_int>=60: sec_int-=60; mi+=1
    if mi>=60: mi-=60; h+=1
    if h>=24: h=23; mi=59; sec_int=59; micro=999999
    try:
        return datetime(y,m,d,h,mi,sec_int,micro, tzinfo=timezone.utc)
    except ValueError:
        return datetime(1900,1,1,tzinfo=timezone.utc)
