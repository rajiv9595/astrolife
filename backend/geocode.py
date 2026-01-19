# geocode.py - Geocoding utilities for location search

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
import httpx

router = APIRouter(prefix="/geocode", tags=["geocoding"])


async def geocode_location(location: str) -> Optional[Dict]:
    """
    Geocode a location name using OpenStreetMap Nominatim API (free, no API key required).
    Returns latitude, longitude, and formatted address.
    """
    if not location or len(location.strip()) < 2:
        return None
    
    try:
        # Use Nominatim API (free, no API key needed)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        
        headers = {
            "User-Agent": "LifePath-Astrology-App/1.0"  # Required by Nominatim
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                return {
                    "latitude": float(result.get("lat", 0)),
                    "longitude": float(result.get("lon", 0)),
                    "display_name": result.get("display_name", location),
                    "address": result.get("address", {})
                }
            return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


async def geocode_suggestions(query: str, limit: int = 5) -> List[Dict]:
    """
    Get multiple location suggestions for a query.
    """
    if not query or len(query.strip()) < 2:
        return []
    
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
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if data:
                for result in data:
                    results.append({
                        "latitude": float(result.get("lat", 0)),
                        "longitude": float(result.get("lon", 0)),
                        "display_name": result.get("display_name", query),
                        "address": result.get("address", {})
                    })
            return results
    except Exception as e:
        print(f"Geocoding suggestion error: {e}")
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
        
        async with httpx.AsyncClient(timeout=10.0) as client:
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


