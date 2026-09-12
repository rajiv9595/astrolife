"""
Production adapter: canonical Phase 1/2/3 natal + varga + panchanga + dasha + yoga -> legacy /compute response shape.

NO ASTROLOGY IS COMPUTED HERE. Every value originates from:
- backend.core.calculation.pipeline.generate_chart_facts (natal)
- backend.core.calculation.varga.calculate_all_vargas (vargas)
- backend.core.calculation.dasha.calculate_vimshottari_timeline + get_current_dasha (vimshottari + current periods)
- backend.core.calculation.panchanga.calculate_panchanga (panchanga)
- backend.core.rules.parashari.evaluate_all_parashari (canonical yogas)
- backend.yoga_evaluator (yogas - legacy fallback for uncovered)
- backend.canonical_jaimini (jaimini - canonical; backend.jaimini legacy rollback only)
- backend.ashtakavarga (ashtakavarga - legacy for now)
- backend.maitri (maitri - legacy for now)
- backend.panchanga_advanced (panchanga_advanced - legacy for now, provides avakahada/ghata chakra)
- backend.canonical_dosha (doshas - canonical; backend.doshas_advanced legacy rollback only)

This module ONLY projects canonical data into the legacy response contract.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.core.calculation.pipeline import ChartFacts
from backend.core.calculation.varga import calculate_all_vargas, VargaPosition
from backend.core.calculation.dasha import calculate_vimshottari_timeline, get_current_dasha
from backend.core.calculation.panchanga import calculate_panchanga
from backend.core.calculation.config import DEFAULT_PROFILE
from backend.core.strength.pipeline import generate_strength_report
from backend.core.strength.profile import DEFAULT_STRENGTH_PROFILE
from backend.core.strength.models import StrengthReport
from backend.canonical_yoga import evaluate_canonical_yogas, get_canonical_yoga_coverage, get_covered_legacy_ids
from backend.tables import compute_lucky_factors, SIGN_LORDS as TABLES_SIGN_LORDS

# Sign list for whole sign house calculation
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}


def _format_dms(deg: float) -> str:
    """Format degrees as D:M:S string for legacy compatibility."""
    d = int(deg)
    m_float = (deg - d) * 60
    m = int(m_float)
    s = round((m_float - m) * 60)
    return f"{d}:{m}:{s}"


def _planet_to_legacy(planet_data, varga_positions: Dict[str, VargaPosition] = None) -> Dict[str, Any]:
    """Convert canonical PlanetData to legacy planet dict format."""
    sign_name = planet_data.sign.name
    deg_in_sign = planet_data.sign.degree
    retrograde = planet_data.retrograde
    
    # Calculate combust based on canonical logic (simplified)
    combust_limits = {
        "Mercury": 13.0, "Venus": 9.0, "Mars": 17.0,
        "Jupiter": 11.0, "Saturn": 15.0
    }
    # Get sun position for combust check (would need sun data)
    # For now, use the canonical retrograde flag only
    combust = False  # Will be set properly if needed
    
    # Nakshatra
    nak = planet_data.nakshatra
    nak_dict = {
        "nakshatra": nak.name,
        "pada": nak.pada,
        "lord": nak.lord,
        "fraction": nak.fraction,
        "start_longitude": nak.start_longitude,
        "end_longitude": nak.end_longitude,
        "degree_within": nak.degree_within,
        "nakshatra_index": nak.id - 1
    }
    
    # Varga signs
    varga_signs = {}
    if varga_positions:
        for v_key, v_pos in varga_positions.items():
            v_num = v_pos.varga_num
            varga_signs[f"d{v_num}_sign"] = v_pos.sign
            varga_signs[f"d{v_num}_longitude"] = v_pos.longitude
            varga_signs[f"d{v_num}_sign_lord"] = SIGN_LORDS.get(v_pos.sign, "")
            varga_signs[f"d{v_num}_degree"] = v_pos.degree
            varga_signs[f"d{v_num}_sign_num"] = v_pos.sign_num
            varga_signs[f"d{v_num}_segment_index"] = v_pos.segment_index
            varga_signs[f"d{v_num}_segment_count"] = v_pos.segment_count
            varga_signs[f"d{v_num}_segment_size"] = v_pos.segment_size
            varga_signs[f"d{v_num}_source_longitude"] = v_pos.source_longitude
            varga_signs[f"d{v_num}_source_sign"] = v_pos.source_sign
            varga_signs[f"d{v_num}_source_sign_num"] = v_pos.source_sign_num
            varga_signs[f"d{v_num}_source_degree"] = v_pos.source_degree
            varga_signs[f"d{v_num}_method"] = v_pos.method.value if hasattr(v_pos.method, 'value') else str(v_pos.method)
    
    return {
        "id": planet_data.id,
        "name": planet_data.name,
        "longitude": planet_data.longitude.tropical,
        "latitude": planet_data.latitude,
        "distance": planet_data.distance,
        "speed": planet_data.speed,
        "retrograde": retrograde,
        "combust": combust,
        "sign_manual": sign_name,
        "degree_in_sign_manual": deg_in_sign,
        "sign_flag": sign_name,
        "degree_in_sign_flag": deg_in_sign,
        "lon_sidereal_manual": planet_data.longitude.sidereal,
        "lon_sidereal_flag": planet_data.longitude.sidereal,
        "nakshatra": nak_dict,
        "star_lord": nak.lord,
        "house_num": planet_data.house,
        "sign": sign_name,
        "degree": deg_in_sign,
        "dms": _format_dms(deg_in_sign),
        **varga_signs
    }


def _ascendant_to_legacy(asc_data, varga_positions: Dict[str, VargaPosition] = None) -> Dict[str, Any]:
    """Convert canonical AscendantData to legacy ascendant dict format."""
    sign_name = asc_data.sign.name
    deg_in_sign = asc_data.sign.degree
    nak = asc_data.nakshatra
    
    # D9 ascendant
    d9_sign = ""
    d9_sign_lord = ""
    if varga_positions and "D9" in varga_positions:
        d9_pos = varga_positions["D9"]
        d9_sign = d9_pos.sign
        d9_sign_lord = SIGN_LORDS.get(d9_sign, "")
    
    # D10 ascendant
    d10_sign = ""
    d10_sign_lord = ""
    if varga_positions and "D10" in varga_positions:
        d10_pos = varga_positions["D10"]
        d10_sign = d10_pos.sign
        d10_sign_lord = SIGN_LORDS.get(d10_sign, "")
    
    return {
        "sign": sign_name,
        "degree": asc_data.longitude.sidereal,
        "deg_in_sign": deg_in_sign,
        "nakshatra": {
            "nakshatra": nak.name,
            "pada": nak.pada,
            "lord": nak.lord,
            "fraction": nak.fraction,
            "start_longitude": nak.start_longitude,
            "end_longitude": nak.end_longitude,
            "degree_within": nak.degree_within,
            "nakshatra_index": nak.id - 1
        },
        "d9_sign": d9_sign,
        "d9_sign_lord": d9_sign_lord,
        "d10_sign": d10_sign,
        "d10_sign_lord": d10_sign_lord,
        "tropical_longitude": asc_data.longitude.tropical,
        "sidereal_longitude": asc_data.longitude.sidereal
    }


def _houses_to_legacy(houses: Dict[int, Any], asc_sign: str) -> Dict[str, Any]:
    """Convert canonical houses to legacy whole_sign_houses format."""
    result = {}
    asc_idx = SIGNS.index(asc_sign)
    
    for house_num, house_data in houses.items():
        sign_name = house_data.sign.name
        sign_num = house_data.sign.id
        result[f"house_{house_num}"] = {
            "sign": sign_name,
            "sign_num": sign_num,
            "start_deg_sidereal": (sign_num - 1) * 30.0,
            "end_deg_sidereal": sign_num * 30.0,
            "house": house_num
        }
    return result


def _vargas_to_legacy(varga_result: Dict[str, Dict[str, VargaPosition]]) -> Dict[str, Any]:
    """Convert canonical varga result to legacy vargas dict format."""
    legacy_vargas = {}
    
    # Planet vargas
    for planet_name, vargas in varga_result.get("planets", {}).items():
        if planet_name not in legacy_vargas:
            legacy_vargas[planet_name] = {}
        for v_key, v_pos in vargas.items():
            legacy_vargas[planet_name][v_key] = {
                "varga": v_pos.varga,
                "varga_num": v_pos.varga_num,
                "method": v_pos.method.value if hasattr(v_pos.method, 'value') else str(v_pos.method),
                "source_longitude": v_pos.source_longitude,
                "source_sign": v_pos.source_sign,
                "source_sign_num": v_pos.source_sign_num,
                "source_degree": v_pos.source_degree,
                "segment_index": v_pos.segment_index,
                "segment_count": v_pos.segment_count,
                "segment_size": v_pos.segment_size,
                "sign": v_pos.sign,
                "sign_num": v_pos.sign_num,
                "degree": v_pos.degree,
                "longitude": v_pos.longitude
            }
    
    # Ascendant vargas (stored under "_ascendant" key in legacy)
    if "ascendant" in varga_result:
        legacy_vargas["_ascendant"] = {}
        for v_key, v_pos in varga_result["ascendant"].items():
            legacy_vargas["_ascendant"][v_key] = {
                "varga": v_pos.varga,
                "varga_num": v_pos.varga_num,
                "method": v_pos.method.value if hasattr(v_pos.method, 'value') else str(v_pos.method),
                "source_longitude": v_pos.source_longitude,
                "source_sign": v_pos.source_sign,
                "source_sign_num": v_pos.source_sign_num,
                "source_degree": v_pos.source_degree,
                "segment_index": v_pos.segment_index,
                "segment_count": v_pos.segment_count,
                "segment_size": v_pos.segment_size,
                "sign": v_pos.sign,
                "sign_num": v_pos.sign_num,
                "degree": v_pos.degree,
                "longitude": v_pos.longitude
            }
    
    # Also create per-varga dicts like legacy format (d1, d2, d3, etc.)
    # Legacy format has vargas as {"d1": {...}, "d2": {...}, ...} where each contains planets
    per_varga = {}
    for v_num in [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]:
        v_key = f"D{v_num}"
        per_varga[f"d{v_num}"] = {}
        # Planets
        for planet_name, vargas in varga_result.get("planets", {}).items():
            if v_key in vargas:
                v_pos = vargas[v_key]
                per_varga[f"d{v_num}"][planet_name] = {
                    "sign": v_pos.sign,
                    "sign_num": v_pos.sign_num,
                    "degree": v_pos.degree,
                    "longitude": v_pos.longitude,
                    "retrograde": False,  # Varga positions don't have retrograde
                    "combust": False,
                    "debilitated": False,
                    "exalted": False
                }
        # Ascendant
        if "ascendant" in varga_result and v_key in varga_result["ascendant"]:
            v_pos = varga_result["ascendant"][v_key]
            per_varga[f"d{v_num}"]["_ascendant"] = {
                "sign": v_pos.sign,
                "sign_num": v_pos.sign_num,
                "degree": v_pos.degree,
                "longitude": v_pos.longitude
            }
            per_varga[f"d{v_num}"]['_houses'] = []  # Not computed in canonical yet
    
    # Merge both formats for backward compatibility
    legacy_vargas.update(per_varga)
    return legacy_vargas


def _moon_sign_from_facts(facts: ChartFacts) -> str:
    """Extract moon sign from canonical facts."""
    if "Moon" in facts.planets:
        return facts.planets["Moon"].sign.name
    return ""


def _nakshatra_of_moon(facts: ChartFacts) -> Dict[str, Any]:
    """Extract moon nakshatra from canonical facts."""
    if "Moon" in facts.planets:
        nak = facts.planets["Moon"].nakshatra
        return {
            "nakshatra": nak.name,
            "pada": nak.pada,
            "lord": nak.lord,
            "fraction": nak.fraction,
            "nakshatra_index": nak.id - 1
        }
    return {}


def _panchanga_details_to_legacy(panchanga_details) -> Dict[str, Any]:
    """Convert canonical PanchangaDetails to legacy panchanga dict format."""
    return {
        "tithi": {
            "index": panchanga_details.tithi.index,
            "index0": panchanga_details.tithi.index0,
            "name": panchanga_details.tithi.name,
            "paksha": panchanga_details.tithi.paksha,
            "fraction_elapsed": panchanga_details.tithi.fraction_elapsed,
            "percent_elapsed": panchanga_details.tithi.percent_elapsed,
            "degrees_elapsed": panchanga_details.tithi.degrees_elapsed,
            "degrees_left": panchanga_details.tithi.degrees_left,
            "angular_distance": panchanga_details.tithi.angular_distance,
            "start_jd": panchanga_details.tithi.start_jd,
            "end_jd": panchanga_details.tithi.end_jd,
            "start_utc_iso": panchanga_details.tithi.start_utc_iso,
            "end_utc_iso": panchanga_details.tithi.end_utc_iso,
            "system": panchanga_details.tithi.system
        },
        "karana": {
            "index_60": panchanga_details.karana.index_60,
            "name": panchanga_details.karana.name,
            "unique_index": panchanga_details.karana.unique_index,
            "is_fixed": panchanga_details.karana.is_fixed,
            "is_movable": panchanga_details.karana.is_movable,
            "half_tithi_fraction": panchanga_details.karana.half_tithi_fraction,
            "angular_distance": panchanga_details.karana.angular_distance,
            "start_jd": panchanga_details.karana.start_jd,
            "end_jd": panchanga_details.karana.end_jd,
            "start_utc_iso": panchanga_details.karana.start_utc_iso,
            "end_utc_iso": panchanga_details.karana.end_utc_iso,
            "sequence_note": panchanga_details.karana.sequence_note,
            "system": panchanga_details.karana.system
        },
        "nakshatra": {
            "index": panchanga_details.nakshatra.index,
            "index0": panchanga_details.nakshatra.index0,
            "name": panchanga_details.nakshatra.name,
            "pada": panchanga_details.nakshatra.pada,
            "lord": panchanga_details.nakshatra.lord,
            "fraction_elapsed": panchanga_details.nakshatra.fraction_elapsed,
            "percent_elapsed": panchanga_details.nakshatra.percent_elapsed,
            "start_longitude": panchanga_details.nakshatra.start_longitude,
            "end_longitude": panchanga_details.nakshatra.end_longitude,
            "degree_within": panchanga_details.nakshatra.degree_within,
            "longitude": panchanga_details.nakshatra.longitude,
            "start_jd": panchanga_details.nakshatra.start_jd,
            "end_jd": panchanga_details.nakshatra.end_jd,
            "start_utc_iso": panchanga_details.nakshatra.start_utc_iso,
            "end_utc_iso": panchanga_details.nakshatra.end_utc_iso,
            "system": panchanga_details.nakshatra.system
        },
        "yoga": {
            "index": panchanga_details.yoga.index,
            "index0": panchanga_details.yoga.index0,
            "name": panchanga_details.yoga.name,
            "fraction_elapsed": panchanga_details.yoga.fraction_elapsed,
            "percent_elapsed": panchanga_details.yoga.percent_elapsed,
            "angular_sum": panchanga_details.yoga.angular_sum,
            "start_jd": panchanga_details.yoga.start_jd,
            "end_jd": panchanga_details.yoga.end_jd,
            "start_utc_iso": panchanga_details.yoga.start_utc_iso,
            "end_utc_iso": panchanga_details.yoga.end_utc_iso,
            "system": panchanga_details.yoga.system
        },
        "vara": {
            "weekday_index": panchanga_details.vara.weekday_index,
            "weekday_name": panchanga_details.vara.weekday_name,
            "local_date": panchanga_details.vara.local_date,
            "is_vedic_sunrise_based": panchanga_details.vara.is_vedic_sunrise_based,
            "system": panchanga_details.vara.system
        },
        "sunrise_sunset": {
            "sunrise_jd": panchanga_details.sunrise_sunset.sunrise_jd,
            "sunset_jd": panchanga_details.sunrise_sunset.sunset_jd,
            "sunrise_utc_iso": panchanga_details.sunrise_sunset.sunrise_utc_iso,
            "sunset_utc_iso": panchanga_details.sunrise_sunset.sunset_utc_iso,
            "sunrise_local": panchanga_details.sunrise_sunset.sunrise_local,
            "sunset_local": panchanga_details.sunrise_sunset.sunset_local,
            "sunrise_local_iso": panchanga_details.sunrise_sunset.sunrise_local_iso,
            "sunset_local_iso": panchanga_details.sunrise_sunset.sunset_local_iso,
            "latitude": panchanga_details.sunrise_sunset.latitude,
            "longitude": panchanga_details.sunrise_sunset.longitude,
            "timezone": panchanga_details.sunrise_sunset.timezone,
            "polar_case": panchanga_details.sunrise_sunset.polar_case,
            "note": panchanga_details.sunrise_sunset.note
        },
        "evaluation_jd": panchanga_details.evaluation_jd,
        "evaluation_utc_iso": panchanga_details.evaluation_utc_iso,
        "evaluation_local_iso": panchanga_details.evaluation_local_iso,
        "location": panchanga_details.location,
        "sun_sidereal": panchanga_details.sun_sidereal,
        "moon_sidereal": panchanga_details.moon_sidereal,
        "ayanamsha": panchanga_details.ayanamsha,
        "ayanamsha_system": panchanga_details.ayanamsha_system
    }


def _vimshottari_timeline_to_legacy(timeline) -> Dict[str, Any]:
    """Convert canonical DashaTimeline to legacy vimshottari dict format."""
    legacy_timeline = []
    for md_entry in timeline.mahadashas:
        md_p = md_entry["period"]
        antar_list = []
        for ad_entry in md_entry.get("antar_dashas", []):
            ad_p = ad_entry["period"]
            praty_list = []
            for pd_entry in ad_entry.get("children", []):
                pd_p = pd_entry["period"]
                sook_list = []
                for sook_entry in pd_entry.get("children", []):
                    sook_p = sook_entry["period"]
                    prana_list = []
                    for prana_entry in sook_entry.get("children", []):
                        prana_p = prana_entry["period"]
                        prana_list.append({
                            "lord": prana_p.lord,
                            "start_jd": prana_p.start_jd,
                            "end_jd": prana_p.end_jd,
                            "start_date": prana_p.start_utc_iso,
                            "end_date": prana_p.end_utc_iso,
                            "years": round(prana_p.duration_years, 10),
                            "is_current": getattr(prana_p, 'is_current', False),
                            "is_partial": prana_p.is_partial,
                        })
                    sook_list.append({
                        "lord": sook_p.lord,
                        "start_jd": sook_p.start_jd,
                        "end_jd": sook_p.end_jd,
                        "start_date": sook_p.start_utc_iso,
                        "end_date": sook_p.end_utc_iso,
                        "years": round(sook_p.duration_years, 8),
                        "is_current": getattr(sook_p, 'is_current', False),
                        "is_partial": sook_p.is_partial,
                        "prana_dashas": prana_list,
                    })
                praty_list.append({
                    "lord": pd_p.lord,
                    "start_jd": pd_p.start_jd,
                    "end_jd": pd_p.end_jd,
                    "start_date": pd_p.start_utc_iso,
                    "end_date": pd_p.end_utc_iso,
                    "years": round(pd_p.duration_years, 6),
                    "is_current": getattr(pd_p, 'is_current', False),
                    "is_partial": pd_p.is_partial,
                    "sookshma_dashas": sook_list,
                })
            antar_list.append({
                "lord": ad_p.lord,
                "start_jd": ad_p.start_jd,
                "end_jd": ad_p.end_jd,
                "start_date": ad_p.start_utc_iso,
                "end_date": ad_p.end_utc_iso,
                "years": round(ad_p.duration_years, 6),
                "is_current": getattr(ad_p, 'is_current', False),
                "is_partial": ad_p.is_partial,
                "pratyantar_dashas": praty_list,
            })
        # ages
        start_age = (md_p.start_jd - timeline.birth_jd) / timeline.profile_used.days_per_year
        end_age = (md_p.end_jd - timeline.birth_jd) / timeline.profile_used.days_per_year
        legacy_timeline.append({
            "lord": md_p.lord,
            "start_jd": md_p.start_jd,
            "end_jd": md_p.end_jd,
            "start_date": md_p.start_utc_iso,
            "end_date": md_p.end_utc_iso,
            "years": round(md_p.duration_years, 4) if md_p.is_partial else int(round(md_p.duration_years)),
            "is_partial": md_p.is_partial,
            "is_current": getattr(md_p, 'is_current', False),
            "start_age": round(start_age, 2),
            "end_age": round(end_age, 2),
            "antar_dashas": antar_list,
        })
    return {
        "nakshatra_of_moon": {
            "nakshatra_index": timeline.moon_nakshatra_index,
            "nakshatra": timeline.moon_nakshatra_name,
            "pada": None,  # Not in timeline
            "fraction": timeline.moon_nakshatra_fraction,
            "lord": timeline.starting_lord,
        },
        "timeline": legacy_timeline,
        "total_years_calculated": timeline.total_years_calculated,
        "dasha_cycle_years": 120
    }


def _current_dasha_to_legacy(current_dasha: Dict[str, Any]) -> Dict[str, Any]:
    """Extract current dasha hierarchy from canonical get_current_dasha result."""
    result = {}
    if current_dasha.get("mahadasha"):
        result["mahadasha"] = {
            "lord": current_dasha["mahadasha"].lord,
            "start_jd": current_dasha["mahadasha"].start_jd,
            "end_jd": current_dasha["mahadasha"].end_jd,
            "start_date": current_dasha["mahadasha"].start_utc_iso,
            "end_date": current_dasha["mahadasha"].end_utc_iso,
            "years": round(current_dasha["mahadasha"].duration_years, 4),
            "is_current": True,
        }
    if current_dasha.get("antardasha"):
        result["antardasha"] = {
            "lord": current_dasha["antardasha"].lord,
            "start_jd": current_dasha["antardasha"].start_jd,
            "end_jd": current_dasha["antardasha"].end_jd,
            "start_date": current_dasha["antardasha"].start_utc_iso,
            "end_date": current_dasha["antardasha"].end_utc_iso,
            "years": round(current_dasha["antardasha"].duration_years, 6),
            "is_current": True,
        }
    if current_dasha.get("pratyantardasha"):
        result["pratyantardasha"] = {
            "lord": current_dasha["pratyantardasha"].lord,
            "start_jd": current_dasha["pratyantardasha"].start_jd,
            "end_jd": current_dasha["pratyantardasha"].end_jd,
            "start_date": current_dasha["pratyantardasha"].start_utc_iso,
            "end_date": current_dasha["pratyantardasha"].end_utc_iso,
            "years": round(current_dasha["pratyantardasha"].duration_years, 8),
            "is_current": True,
        }
    if current_dasha.get("sookshma"):
        result["sookshma"] = {
            "lord": current_dasha["sookshma"].lord,
            "start_jd": current_dasha["sookshma"].start_jd,
            "end_jd": current_dasha["sookshma"].end_jd,
            "start_date": current_dasha["sookshma"].start_utc_iso,
            "end_date": current_dasha["sookshma"].end_utc_iso,
            "years": round(current_dasha["sookshma"].duration_years, 10),
            "is_current": True,
        }
    if current_dasha.get("hierarchy"):
        result["hierarchy"] = current_dasha["hierarchy"]
    return result


def build_canonical_compute_response(
    chart_facts: ChartFacts,
    varga_result: Dict[str, Dict[str, VargaPosition]],
    req_params: Dict[str, Any],
    current_user: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Build the complete /compute response using canonical data sources.
    
    This replaces the legacy compute_chart() call with canonical pipeline.
    """
    # Generate canonical vimshottari timeline
    moon_lon = chart_facts.planets["Moon"].longitude.sidereal
    birth_jd = chart_facts.time.julian_day
    
    # Use evaluation datetime from request if provided, otherwise use birth time
    # For birth chart computation, we use the birth time as the evaluation moment
    eval_dt = datetime(
        year=req_params.get("year"),
        month=req_params.get("month"),
        day=req_params.get("day"),
        hour=req_params.get("hour", 0),
        minute=req_params.get("minute", 0),
        second=req_params.get("second", 0)
    )
    # Localize to the birth timezone
    import pytz
    tz_name = req_params.get("tz", "UTC")
    tz = pytz.timezone(tz_name)
    eval_dt_localized = tz.localize(eval_dt)
    
    dasha_timeline = calculate_vimshottari_timeline(
        chart_facts=chart_facts,
        profile=DEFAULT_PROFILE.dasha_profile,
        years_ahead=120
    )
    current_dasha = get_current_dasha(dasha_timeline, eval_dt_localized)
    
    vimshottari_legacy = _vimshottari_timeline_to_legacy(dasha_timeline)
    current_dasha_legacy = _current_dasha_to_legacy(current_dasha)
    
    # Merge current dasha info into vimshottari for backward compatibility
    vimshottari_legacy["current_dasha"] = current_dasha_legacy
    
    # Generate canonical panchanga at birth time
    lat = req_params.get("lat", 0.0)
    lon = req_params.get("lon", 0.0)
    panchanga_details = calculate_panchanga(
        evaluation_datetime=eval_dt_localized,
        latitude=lat,
        longitude=lon,
        tz_name=tz_name,
        profile=DEFAULT_PROFILE
    )
    panchanga_legacy = _panchanga_details_to_legacy(panchanga_details)
    
    # Convert planets
    planets_legacy = {}
    planet_vargas = varga_result.get("planets", {})
    for p_name, p_data in chart_facts.planets.items():
        v_pos = planet_vargas.get(p_name, {})
        planets_legacy[p_name] = _planet_to_legacy(p_data, v_pos)
    
    # Ascendant
    asc_vargas = varga_result.get("ascendant", {})
    ascendant_legacy = _ascendant_to_legacy(chart_facts.ascendant, asc_vargas)
    
    # Whole sign houses
    whole_sign_houses = _houses_to_legacy(chart_facts.houses, chart_facts.ascendant.sign.name)
    
    # Vargas
    vargas_legacy = _vargas_to_legacy(varga_result)
    
    # Extract D1, D9, D10 for top-level compatibility
    d1_planets = {}
    for p_name, vargas in varga_result.get("planets", {}).items():
        if "D1" in vargas:
            v = vargas["D1"]
            d1_planets[p_name] = {
                "sign": v.sign,
                "sign_num": v.sign_num,
                "degree": v.degree,
                "longitude": v.longitude,
                "retrograde": planets_legacy[p_name].get("retrograde", False),
                "combust": planets_legacy[p_name].get("combust", False),
                "debilitated": False,
                "exalted": False
            }
    if "ascendant" in varga_result and "D1" in varga_result["ascendant"]:
        v = varga_result["ascendant"]["D1"]
        d1_planets["_ascendant"] = {
            "sign": v.sign,
            "sign_num": v.sign_num,
            "degree": v.degree,
            "longitude": v.longitude
        }
        d1_planets["_houses"] = []
    
    d9_planets = {}
    for p_name, vargas in varga_result.get("planets", {}).items():
        if "D9" in vargas:
            v = vargas["D9"]
            d9_planets[p_name] = {
                "sign": v.sign,
                "sign_num": v.sign_num,
                "degree": v.degree,
                "longitude": v.longitude,
                "retrograde": False,
                "combust": False,
                "debilitated": False,
                "exalted": False
            }
    if "ascendant" in varga_result and "D9" in varga_result["ascendant"]:
        v = varga_result["ascendant"]["D9"]
        d9_planets["_ascendant"] = {
            "sign": v.sign,
            "sign_num": v.sign_num,
            "degree": v.degree,
            "longitude": v.longitude
        }
        d9_planets["_houses"] = []
    
    d10_planets = {}
    for p_name, vargas in varga_result.get("planets", {}).items():
        if "D10" in vargas:
            v = vargas["D10"]
            d10_planets[p_name] = {
                "sign": v.sign,
                "sign_num": v.sign_num,
                "degree": v.degree,
                "longitude": v.longitude,
                "retrograde": False,
                "combust": False,
                "debilitated": False,
                "exalted": False
            }
    if "ascendant" in varga_result and "D10" in varga_result["ascendant"]:
        v = varga_result["ascendant"]["D10"]
        d10_planets["_ascendant"] = {
            "sign": v.sign,
            "sign_num": v.sign_num,
            "degree": v.degree,
            "longitude": v.longitude
        }
        d10_planets["_houses"] = []
    
    # Aspects (placeholder - legacy format)
    aspects = {}
    
    # Lucky factors
    lagna_lord = TABLES_SIGN_LORDS.get(chart_facts.ascendant.sign.name, "")
    lucky_factors_data = compute_lucky_factors(
        asc_sign=chart_facts.ascendant.sign.name,
        moon_sign=_moon_sign_from_facts(chart_facts),
        lagna_lord=lagna_lord
    )
    
    # Build response with canonical panchanga and dasha
    response = {
        "request": req_params,
        "jd_ut": chart_facts.time.julian_day,
        "utc_at_birth": chart_facts.time.utc_datetime,
        "ayanamsha_deg": chart_facts.ayanamsha.value,
        "planets": planets_legacy,
        "ascendant": ascendant_legacy,
        "asc_sign": chart_facts.ascendant.sign.name,
        "whole_sign_houses": whole_sign_houses,
        "d9": {"planets": d9_planets},
        "d10": d10_planets,
        "vargas": vargas_legacy,
        "aspects": aspects,
        "vimshottari": vimshottari_legacy,
        "nakshatra_of_moon": _nakshatra_of_moon(chart_facts),
        # Canonical Panchanga fields
        "panchanga": panchanga_legacy,
        "karana": panchanga_legacy.get("karana", {}),
        "tithi": panchanga_legacy.get("tithi", {}),
        "nithya_yoga": panchanga_legacy.get("yoga", {}),
        "sunrise": panchanga_legacy.get("sunrise_sunset", {}).get("sunrise_local", "Unknown"),
        "sunset": panchanga_legacy.get("sunrise_sunset", {}).get("sunset_local", "Unknown"),
        "moon_sign": _moon_sign_from_facts(chart_facts),
        "yogas": [],  # Will be filled by legacy yoga_evaluator if authenticated
        "lucky_factors": lucky_factors_data,
        "strengths": [],  # Will be filled by canonical_strength
        "bhava_bala": {},  # Will be filled by canonical_strength (Migration #5)
        "vimsopaka": {},  # Will be filled by canonical_strength (Migration #5)
        "avastha": {},  # Will be filled by canonical_strength (Migration #5)
        "functional_nature": {},  # Will be filled by canonical_strength (Migration #5)
        "composite_strength": {},  # Will be filled by canonical_strength (Migration #5)
        "jaimini": {},  # Will be filled by canonical Jaimini (legacy rollback only)
        "ashtakavarga": {},  # Will be filled by legacy ashtakavarga
        "shadbala": {},  # Will be filled by canonical_strength
        "maitri": {},  # Will be filled by legacy maitri
        "panchanga_advanced": {},  # Will be filled by legacy panchanga_advanced
        "advanced_doshas": {},  # Will be filled by canonical dosha engine (legacy rollback only)
        "mangal_dosha": {},  # Will be filled by canonical dosha engine
        "doshas": [],  # Will be filled by canonical dosha engine
        "rules": {},  # Will be filled by canonical rules bridge (Migration #8, additive)
    }
    
    return response


def enrich_response_with_legacy_modules(
    response: Dict[str, Any],
    chart_facts: ChartFacts,
    req_params: Dict[str, Any],
    current_user: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Enrich the canonical response with legacy module data for modules not yet migrated.
    
    This is a temporary bridge until all modules are canonical.
    """
    # Import legacy modules
    from backend.yoga_evaluator import evaluate_all_yogas
    from backend.jaimini import compute_jaimini_system
    from backend.ashtakavarga import compute_ashtakavarga
    from backend.maitri import compute_maitri_chakra
    from backend.panchanga_advanced import compute_advanced_panchanga
    from backend.doshas_advanced import compute_advanced_doshas
    from backend.canonical_strength import (
        build_strength_rows, build_shadbala_payload,
        build_bhava_bala_payload, build_vimsopaka_payload,
        build_avastha_payload, build_functional_payload,
        build_composite_payload,
    )
    from backend.core.strength.shadbala import calculate_all_shadbala
    from backend.core.strength.dignity import calculate_all_dignities
    import os
    
    # Re-use the canonical chart facts for strength (already done in astro.py)
    # But we need to add the legacy-format planets for build_strength_rows
    legacy_planets = response["planets"]
    
    # Shadbala + Dignity (canonical)
    canonical_shadbala = calculate_all_shadbala(chart_facts)
    canonical_dignity = calculate_all_dignities(chart_facts)
    response["strengths"] = build_strength_rows(canonical_shadbala, canonical_dignity, legacy_planets)
    response["shadbala"] = build_shadbala_payload(canonical_shadbala)
    
    # Generate StrengthReport for canonical yoga evaluation
    strength_report = generate_strength_report(
        chart_facts=chart_facts,
        profile=DEFAULT_STRENGTH_PROFILE,
        evaluation_datetime=None,  # Birth chart evaluation
        d9_chart_facts=None
    )

    # Full Strength wiring (Migration #5): project the remaining canonical
    # StrengthReport components additively. Shadbala/dignity above untouched.
    response["bhava_bala"] = build_bhava_bala_payload(strength_report.bhava_bala)
    response["vimsopaka"] = build_vimsopaka_payload(strength_report.vimsopaka)
    response["avastha"] = build_avastha_payload(strength_report.avastha)
    response["functional_nature"] = build_functional_payload(strength_report.functional_strength)
    response["composite_strength"] = build_composite_payload(strength_report.composite)
    
    # Vargas for yoga evaluation
    from backend.core.calculation.varga import calculate_all_vargas
    varga_facts = calculate_all_vargas(chart_facts)
    
    # Dynamic state for yoga evaluation (uses birth time for dasha/transit context)
    from backend.core.calculation.dynamic import get_dynamic_state
    from datetime import datetime
    import pytz
    tz_name = req_params.get("tz", "UTC")
    tz = pytz.timezone(tz_name)
    eval_dt = datetime(
        year=req_params.get("year"),
        month=req_params.get("month"),
        day=req_params.get("day"),
        hour=req_params.get("hour", 0),
        minute=req_params.get("minute", 0),
        second=req_params.get("second", 0)
    )
    eval_dt_localized = tz.localize(eval_dt)
    dynamic_state = get_dynamic_state(
        chart_facts=chart_facts,
        evaluation_datetime=eval_dt_localized,
        profile=DEFAULT_PROFILE
    )
    
    # YOGAS: Canonical Rule Engine (authoritative) + Legacy fallback for uncovered
    try:
        # Primary: Canonical Rule Engine (Parashari yogas with evidence/provenance)
        canonical_yogas = evaluate_canonical_yogas(
            chart_facts=chart_facts,
            strength_report=strength_report,
            varga_facts=varga_facts,
            dynamic_state=dynamic_state,
            evaluation_datetime=eval_dt_localized,
            include_evidence=True,
            include_provenance=True,
        )
        
        # Fallback: Legacy yoga_evaluator for uncovered yogas (only for authenticated users)
        legacy_yogas = []
        if current_user is not None:
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            ruleset_dir = os.path.join(backend_dir, "rulesets")
            yogas_dir = os.path.join(ruleset_dir, "yogas")
            try:
                legacy_yogas = evaluate_all_yogas(
                    yogas_dir,
                    legacy_planets,
                    response["whole_sign_houses"],
                    response["asc_sign"]
                )
            except Exception as e:
                print(f"Error evaluating legacy yogas: {e}")
                import traceback
                traceback.print_exc()
                legacy_yogas = []
        
        # Merge: Canonical yogas take precedence; legacy fills gaps.
        # Legacy IDs covered by canonical rules (Categories A/B/C) are
        # suppressed so each Yoga appears exactly once (canonical entry).
        # Legacy gap-fill remains for uncovered Yogas (Categories D/E).
        canonical_ids = set(y["id"] for y in canonical_yogas)
        covered_legacy_ids = get_covered_legacy_ids()
        legacy_unique = [y for y in legacy_yogas
                         if y.get("id") not in canonical_ids
                         and y.get("id") not in covered_legacy_ids]
        
        # Combine and mark source
        for y in canonical_yogas:
            y["_source"] = "canonical"
        for y in legacy_unique:
            y["_source"] = "legacy_fallback"
        
        response["yogas"] = canonical_yogas + legacy_unique
        
    except Exception as e:
        print(f"Error evaluating canonical yogas: {e}")
        import traceback
        traceback.print_exc()
        # Full fallback to legacy
        if current_user is not None:
            try:
                backend_dir = os.path.dirname(os.path.abspath(__file__))
                ruleset_dir = os.path.join(backend_dir, "rulesets")
                yogas_dir = os.path.join(ruleset_dir, "yogas")
                response["yogas"] = evaluate_all_yogas(
                    yogas_dir,
                    legacy_planets,
                    response["whole_sign_houses"],
                    response["asc_sign"]
                )
                for y in response["yogas"]:
                    y["_source"] = "legacy_fallback_full"
            except Exception as e2:
                print(f"Error evaluating legacy yogas (full fallback): {e2}")
                import traceback
                traceback.print_exc()
                response["yogas"] = []
        else:
            response["yogas"] = []
    
    # Doshas (canonical primary; legacy advanced_doshas rollback only)
    try:
        from backend.canonical_dosha import (
            evaluate_canonical_doshas, build_mangal_dosha_block,
            build_advanced_doshas_block, build_doshas_block,
        )
        canonical_dosha_set = evaluate_canonical_doshas(
            chart_facts=chart_facts,
            strength_report=strength_report,
            varga_facts=varga_facts,
            dynamic_state=dynamic_state,
            evaluation_datetime=eval_dt_localized,
        )
        response["mangal_dosha"] = build_mangal_dosha_block(canonical_dosha_set)
        response["advanced_doshas"] = build_advanced_doshas_block(canonical_dosha_set)
        response["doshas"] = build_doshas_block(canonical_dosha_set)
    except Exception as e:
        print(f"Error evaluating canonical doshas: {e}")
        import traceback
        traceback.print_exc()
        try:
            response["advanced_doshas"] = compute_advanced_doshas(legacy_planets, response["asc_sign"])
            response["advanced_doshas"]["_source"] = "legacy_fallback"
        except Exception as e2:
            print(f"Error evaluating legacy doshas (fallback): {e2}")
            import traceback
            traceback.print_exc()
            response["advanced_doshas"] = {}
        response["mangal_dosha"] = {}
        response["doshas"] = []
    
    # Jaimini (canonical primary; legacy rollback only)
    try:
        from backend.canonical_jaimini import evaluate_canonical_jaimini
        response["jaimini"] = evaluate_canonical_jaimini(
            chart_facts=chart_facts,
            varga_facts=varga_facts,
            evaluation_datetime=eval_dt_localized,
        )
    except Exception as e:
        print(f"Error computing canonical jaimini: {e}")
        import traceback
        traceback.print_exc()
        try:
            response["jaimini"] = compute_jaimini_system(legacy_planets, response["asc_sign"])
            response["jaimini"]["_source"] = "legacy_fallback"
        except Exception as e2:
            print(f"Error computing jaimini fallback: {e2}")
            import traceback
            traceback.print_exc()
            response["jaimini"] = {}
    
    # Ashtakavarga (legacy)
    try:
        response["ashtakavarga"] = compute_ashtakavarga(legacy_planets, response["asc_sign"])
    except Exception as e:
        print(f"Error computing ashtakavarga: {e}")
        response["ashtakavarga"] = {}
    
    # Maitri (legacy)
    try:
        response["maitri"] = compute_maitri_chakra(legacy_planets)
    except Exception as e:
        print(f"Error computing maitri: {e}")
        response["maitri"] = {}
    
    # Panchanga Advanced (legacy - provides Avakahada/Ghata Chakra not in canonical)
    moon_nakshatra = ""
    if "Moon" in legacy_planets:
        n_data = legacy_planets["Moon"].get("nakshatra", {})
        if isinstance(n_data, dict):
            moon_nakshatra = n_data.get("nakshatra", "")
    try:
        response["panchanga_advanced"] = compute_advanced_panchanga(response["moon_sign"], moon_nakshatra)
    except Exception as e:
        print(f"Error computing panchanga_advanced: {e}")
        response["panchanga_advanced"] = {}
    
    # Advanced Doshas already set by the canonical dosha block above
    # (canonical primary; legacy rollback handled there). Nothing to do here.

    # Production rules bridge (Migration #8, additive): registry coverage +
    # ACTIVE-only dynamic evaluation metadata. Never alters existing blocks.
    try:
        from backend.canonical_rules import build_production_rules_block
        response["rules"] = build_production_rules_block(
            chart_facts=chart_facts,
            strength_report=strength_report,
            varga_facts=varga_facts,
            dynamic_state=dynamic_state,
            evaluation_datetime=eval_dt_localized,
        )
    except Exception as e:
        print(f"Error building production rules block: {e}")
        response["rules"] = {"_source": "canonical", "error": "rules_block_unavailable"}

    return response