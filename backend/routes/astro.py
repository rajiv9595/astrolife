from fastapi import APIRouter, Depends
from typing import Optional, List
import os

from backend.schemas import ComputeRequest, MatchRequest
from backend.models import User
from backend.dependencies import get_current_user_optional
from backend.calculations import compute_chart, compute_match_for_birth_data
from backend.tables import compute_lucky_factors, SIGN_LORDS as TABLES_SIGN_LORDS
from backend.canonical_strength import build_strength_rows, build_shadbala_payload
from backend.core.calculation.pipeline import generate_chart_facts
from backend.core.strength.shadbala import calculate_all_shadbala
from backend.core.strength.dignity import calculate_all_dignities
from backend.jaimini import compute_jaimini_system
from backend.ashtakavarga import compute_ashtakavarga
from backend.maitri import compute_maitri_chakra
from backend.panchanga_advanced import compute_advanced_panchanga
from backend.doshas_advanced import compute_advanced_doshas

router = APIRouter()

# Sign lords mapping (local fallback if needed, but using tables one is better)
# The logic in main.py used SIGN_LORDS for `lagna_lord` calculation.
# We will use the one from tables module to stay DRY.

@router.post("/compute")
def compute(
    req: ComputeRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Use the calculations module to compute the complete chart
    chart_data = compute_chart(
        year=req.year,
        month=req.month,
        day=req.day,
        hour=req.hour,
        minute=req.minute,
        second=req.second,
        tz=req.tz,
        lat=req.lat,
        lon=req.lon,
        planets=req.planets,
        topo_alt=req.topo_alt or 0.0
    )

    # Canonical Phase 4 strength: the ONLY authoritative Shadbala source.
    # ChartFacts use the same source of truth as the rest of the system
    # (Swiss Ephemeris, Lahiri ayanamsha, Mean Node, Whole Sign houses).
    chart_facts = generate_chart_facts(
        year=req.year,
        month=req.month,
        day=req.day,
        hour=req.hour,
        minute=req.minute,
        second=req.second,
        lat=req.lat,
        lon=req.lon,
        tz_name=req.tz,
    )
    canonical_shadbala = calculate_all_shadbala(chart_facts)
    canonical_dignity = calculate_all_dignities(chart_facts)

    # Planetary Strength & Analysis rows (canonical Shadbala + dignity).
    planet_strengths = build_strength_rows(
        canonical_shadbala, canonical_dignity, chart_data.get("planets", {})
    )

    # Evaluate yogas using rulesets - ONLY for authenticated users
    yogas = []
    if current_user is not None:
        # User is authenticated, compute yogas
        # We need to find the ruleset dir. Since this file is in backend/routes/, 
        # we need to go up one level then into rulesets.
        
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        ruleset_dir = os.path.join(backend_dir, "rulesets")
        
        try:
            from backend.yoga_evaluator import evaluate_all_yogas
            # Update to read specifically from the "yogas" subdirectory for the UI report
            yogas_dir = os.path.join(ruleset_dir, "yogas")
            yogas = evaluate_all_yogas(
                yogas_dir, 
                chart_data["planets"], 
                chart_data["whole_sign_houses"], 
                chart_data["asc_sign"]
            )
        except Exception as e:
            print(f"Error evaluating yogas: {e}")
            import traceback
            traceback.print_exc()
    
    # Compute Lucky Factors
    # main.py used: lagna_lord = SIGN_LORDS.get(chart_data["asc_sign"], "")
    # We use table's SIGN_LORDS
    lagna_lord = TABLES_SIGN_LORDS.get(chart_data["asc_sign"], "")
    
    lucky_factors_data = compute_lucky_factors(
        asc_sign=chart_data["asc_sign"],
        moon_sign=chart_data.get("moon_sign") or "",
        lagna_lord=lagna_lord
    )

    # Advanced Calculations
    jaimini_data = compute_jaimini_system(chart_data["planets"], chart_data["asc_sign"])
    ashtakavarga_data = compute_ashtakavarga(chart_data["planets"], chart_data["asc_sign"])
    
    # Canonical Phase 4 Shadbala payload (replaces legacy backend/shadbala.py).
    shadbala_data = build_shadbala_payload(canonical_shadbala)

    maitri_data = compute_maitri_chakra(chart_data["planets"])
    
    moon_nakshatra = ""
    if "Moon" in chart_data["planets"]:
        n_data = chart_data["planets"]["Moon"].get("nakshatra", {})
        if isinstance(n_data, dict):
            moon_nakshatra = n_data.get("nakshatra", "")
    panchanga_advanced_data = compute_advanced_panchanga(chart_data["moon_sign"], moon_nakshatra)
    
    advanced_doshas_data = compute_advanced_doshas(chart_data["planets"], chart_data["asc_sign"])

    # Return response with all computed data
    return {
        "request": req.dict(),
        "jd_ut": chart_data["jd_ut"],
        "utc_at_birth": chart_data["utc_at_birth"],
        "ayanamsha_deg": chart_data["ayanamsha_deg"],
        "planets": chart_data["planets"],
        "ascendant": chart_data["ascendant"],
        "whole_sign_houses": chart_data["whole_sign_houses"],
        "d9": chart_data["d9"],
        "d10": chart_data.get("d10", {}),
        "vargas": chart_data.get("vargas", {}),
        "aspects": chart_data.get("aspects", {}),
        "vimshottari": chart_data["vimshottari"],
        "nakshatra_of_moon": chart_data["nakshatra_of_moon"],
        "karana": chart_data["karana"],
        "tithi": chart_data.get("tithi"),
        "nithya_yoga": chart_data.get("nithya_yoga"),
        "sunrise": chart_data.get("sunrise"),
        "sunset": chart_data.get("sunset"),
        "moon_sign": chart_data["moon_sign"],
        "yogas": yogas,
        "lucky_factors": lucky_factors_data,
        "strengths": planet_strengths,
        "jaimini": jaimini_data,
        "ashtakavarga": ashtakavarga_data,
        "shadbala": shadbala_data,
        "maitri": maitri_data,
        "panchanga_advanced": panchanga_advanced_data,
        "advanced_doshas": advanced_doshas_data
    }


@router.post("/match")
def match(req: MatchRequest):
    boy_params = {
        "year": req.boy.year,
        "month": req.boy.month,
        "day": req.boy.day,
        "hour": req.boy.hour,
        "minute": req.boy.minute,
        "second": req.boy.second,
        "tz": req.boy.tz,
        "lat": req.boy.lat,
        "lon": req.boy.lon,
        "planets": req.boy.planets,
        "topo_alt": req.boy.topo_alt or 0.0,
    }
    girl_params = {
        "year": req.girl.year,
        "month": req.girl.month,
        "day": req.girl.day,
        "hour": req.girl.hour,
        "minute": req.girl.minute,
        "second": req.girl.second,
        "tz": req.girl.tz,
        "lat": req.girl.lat,
        "lon": req.girl.lon,
        "planets": req.girl.planets,
        "topo_alt": req.girl.topo_alt or 0.0,
    }

    result = compute_match_for_birth_data(boy_params, girl_params)
    return {
        "ashta_koota": result["ashta_koota"],
        "boy": {
            "moon_sign": result["boy"].get("moon_sign"),
            "nakshatra_of_moon": result["boy"].get("nakshatra_of_moon"),
        },
        "girl": {
            "moon_sign": result["girl"].get("moon_sign"),
            "nakshatra_of_moon": result["girl"].get("nakshatra_of_moon"),
        },
    }
