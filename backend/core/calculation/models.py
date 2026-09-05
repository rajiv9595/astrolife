from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from .config import CalculationProfile

class AyanamshaDetails(BaseModel):
    system: str
    swiss_mode: str
    value: float

class Location(BaseModel):
    name: str = "Unknown"
    country: str = "Unknown"
    latitude: float
    longitude: float
    timezone: str

class TimeDetails(BaseModel):
    local_datetime: str
    timezone: str
    utc_datetime: str
    julian_day: float

class SignPosition(BaseModel):
    id: int
    name: str
    degree: float

class NakshatraPosition(BaseModel):
    id: int
    name: str
    lord: str
    pada: int
    fraction: float
    start_longitude: float
    end_longitude: float
    degree_within: float

class LongitudeDetails(BaseModel):
    tropical: float
    sidereal: float

class PlanetData(BaseModel):
    id: str
    name: str
    longitude: LongitudeDetails
    latitude: float
    distance: float
    speed: float
    retrograde: bool
    sign: SignPosition
    house: int
    nakshatra: NakshatraPosition

class HouseData(BaseModel):
    id: int
    sign: SignPosition

class AscendantData(BaseModel):
    longitude: LongitudeDetails
    sign: SignPosition
    nakshatra: NakshatraPosition

class ChartFacts(BaseModel):
    calculation_profile: CalculationProfile
    location: Location
    time: TimeDetails
    ayanamsha: AyanamshaDetails
    ascendant: AscendantData
    planets: Dict[str, PlanetData]
    houses: Dict[int, HouseData]
    metadata: Dict[str, Any] = Field(default_factory=dict)
