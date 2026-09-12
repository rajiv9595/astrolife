from fastapi import APIRouter, Depends
from typing import Optional, List
import os

from backend.schemas import ComputeRequest, MatchRequest
from backend.models import User
from backend.dependencies import get_current_user_optional
from backend.tables import compute_lucky_factors, SIGN_LORDS as TABLES_SIGN_LORDS
from backend.core.calculation.pipeline import generate_chart_facts
from backend.core.calculation.varga import calculate_all_vargas
from backend.core.strength.shadbala import calculate_all_shadbala
from backend.core.strength.dignity import calculate_all_dignities
from backend.canonical_strength import build_strength_rows, build_shadbala_payload
from backend.canonical_response import build_canonical_compute_response, enrich_response_with_legacy_modules
# Legacy match engine (no canonical replacement exists; /match is legacy-only
# by design — restored import dropped during the canonical /compute migration).
from backend.calculations import compute_match_for_birth_data

router = APIRouter()

# Response field keys for static analysis / contract documentation
# These fields are produced by canonical_response.build_canonical_compute_response
# and enriched by canonical_response.enrich_response_with_legacy_modules
COMPUTE_RESPONSE_FIELDS = [
    "strengths", "jaimini", "ashtakavarga", "shadbala", "maitri",
    "bhava_bala", "vimsopaka", "avastha", "functional_nature",
    "composite_strength",
    "panchanga_advanced", "advanced_doshas", "mangal_dosha", "doshas",
    "yogas", "lucky_factors", "rules",
    "planets", "ascendant", "whole_sign_houses", "d9", "d10",
    "vargas", "aspects", "vimshottari", "nakshatra_of_moon",
    "karana", "tithi", "nithya_yoga", "sunrise", "sunset",
    "moon_sign", "jd_ut", "utc_at_birth", "ayanamsha_deg",
    "request"
]

@router.post("/compute")
def compute(
    req: ComputeRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Generate canonical chart facts (natal)
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
    
    # Generate all vargas from canonical chart facts
    varga_result = calculate_all_vargas(chart_facts)
    
    # Build canonical response (natal + vargas from canonical sources)
    req_params = req.dict()
    response = build_canonical_compute_response(
        chart_facts=chart_facts,
        varga_result=varga_result,
        req_params=req_params,
        current_user=current_user
    )
    
    # Enrich with legacy modules not yet migrated (yogas, jaimini, ashtakavarga, etc.)
    response = enrich_response_with_legacy_modules(
        response=response,
        chart_facts=chart_facts,
        req_params=req_params,
        current_user=current_user
    )
    
    return response


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
