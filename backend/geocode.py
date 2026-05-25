# geocode.py - Geocoding utilities for location search

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
import httpx

router = APIRouter(prefix="/geocode", tags=["geocoding"])

# Global in-memory cache to prevent duplicate queries and speed up response times
_GEOCODE_SUGGESTIONS_CACHE: Dict[str, List[Dict]] = {}
_GEOCODE_LOCATION_CACHE: Dict[str, Optional[Dict]] = {}


def parse_openmeteo_result(res: dict) -> dict:
    """Parse Open-Meteo geocoding result into standardized schema."""
    name = res.get("name", "")
    admin2 = res.get("admin2", "")
    admin1 = res.get("admin1", "")
    country = res.get("country", "")
    
    # Construct a beautiful display name
    parts = []
    if name:
        parts.append(name)
    if admin2 and admin2 != name:
        parts.append(admin2)
    if admin1 and admin1 != admin2 and admin1 != name:
        parts.append(admin1)
    if country:
        parts.append(country)
        
    display_name = ", ".join(parts)
    
    return {
        "latitude": float(res.get("latitude", 0)),
        "longitude": float(res.get("longitude", 0)),
        "display_name": display_name,
        "timezone": res.get("timezone", "Asia/Kolkata"),
        "address": {
            "city": name,
            "state": admin1,
            "country": country,
            "country_code": res.get("country_code", "").lower(),
            "county": admin2
        }
    }


async def geocode_location(location: str) -> Optional[Dict]:
    """
    Geocode a location name.
    Uses Open-Meteo API as primary (extremely fast, high rate limits, no API keys)
    and falls back to Nominatim OpenStreetMap if needed.
    """
    if not location or len(location.strip()) < 2:
        return None
        
    cache_key = location.strip().lower()
    if cache_key in _GEOCODE_LOCATION_CACHE:
        return _GEOCODE_LOCATION_CACHE[cache_key]
        
    # 1. Try Open-Meteo Geocoding API
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    parsed = parse_openmeteo_result(results[0])
                    _GEOCODE_LOCATION_CACHE[cache_key] = parsed
                    return parsed
    except Exception as e:
        print(f"Open-Meteo geocoding error for '{location}': {e}")

    # 2. Fallback to Nominatim
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "LifePath-Astrology-App/1.0"
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    result = data[0]
                    parsed = {
                        "latitude": float(result.get("lat", 0)),
                        "longitude": float(result.get("lon", 0)),
                        "display_name": result.get("display_name", location),
                        "timezone": "Asia/Kolkata",  # Default fallback timezone
                        "address": result.get("address", {})
                    }
                    _GEOCODE_LOCATION_CACHE[cache_key] = parsed
                    return parsed
            elif response.status_code == 429:
                print(f"Nominatim rate limited (429) during fallback for '{location}'")
    except Exception as e:
        print(f"Nominatim fallback geocoding error for '{location}': {e}")
        
    _GEOCODE_LOCATION_CACHE[cache_key] = None
    return None


async def geocode_suggestions(query: str, limit: int = 5) -> List[Dict]:
    """
    Get multiple location suggestions for a query.
    Uses Open-Meteo API as primary (highly responsive, no 429 rate limit errors on keystrokes)
    with a robust cache and fallback to Nominatim.
    """
    if not query or len(query.strip()) < 2:
        return []
        
    cache_key = f"{query.strip().lower()}_{limit}"
    if cache_key in _GEOCODE_SUGGESTIONS_CACHE:
        return _GEOCODE_SUGGESTIONS_CACHE[cache_key]
        
    # 1. Try Open-Meteo Geocoding API
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": query,
            "count": limit,
            "language": "en",
            "format": "json"
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    parsed_results = [parse_openmeteo_result(res) for res in results]
                    _GEOCODE_SUGGESTIONS_CACHE[cache_key] = parsed_results
                    return parsed_results
    except Exception as e:
        print(f"Open-Meteo suggestions error for '{query}': {e}")

    # 2. Fallback to Nominatim
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": limit,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "LifePath-Astrology-App/1.0"
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                results = []
                if data:
                    for result in data:
                        results.append({
                            "latitude": float(result.get("lat", 0)),
                            "longitude": float(result.get("lon", 0)),
                            "display_name": result.get("display_name", query),
                            "timezone": "Asia/Kolkata",  # Default fallback
                            "address": result.get("address", {})
                        })
                    _GEOCODE_SUGGESTIONS_CACHE[cache_key] = results
                    return results
            elif response.status_code == 429:
                print(f"Nominatim rate limited (429) during suggestions fallback for '{query}'")
    except Exception as e:
        print(f"Nominatim suggestions fallback error for '{query}': {e}")
        
    return []


@router.get("/search")
async def search_location(query: str = Query(..., min_length=2, description="Location name to search")):
    """
    Search for a location by name and return coordinates.
    Example: /geocode/search?query=Mumbai
    """
    try:
        result = await geocode_location(query)
        if result:
            return {
                "success": True,
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "display_name": result["display_name"],
                "timezone": result["timezone"],
                "address": result["address"]
            }
        else:
            return {
                "success": False,
                "message": "Location not found. Please try a different search term."
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geocoding service error: {str(e)}"
        )


@router.get("/suggestions")
async def get_location_suggestions(query: str = Query(..., min_length=2, description="Location name to search")):
    """
    Get generic location suggestions for dropdowns.
    """
    try:
        results = await geocode_suggestions(query)
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
         raise HTTPException(
            status_code=500,
            detail=f"Geocoding suggestion error: {str(e)}"
        )


@router.get("/reverse")
async def reverse_geocode(lat: float = Query(...), lon: float = Query(...)):
    """
    Reverse geocode: Convert coordinates to address.
    Example: /geocode/reverse?lat=19.0760&lon=72.8777
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "LifePath-Astrology-App/1.0"
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data:
                return {
                    "success": True,
                    "display_name": data.get("display_name", ""),
                    "address": data.get("address", {})
                }
            return {"success": False, "message": "Address not found"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reverse geocoding error: {str(e)}"
        )



