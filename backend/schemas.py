from pydantic import BaseModel, EmailStr
from typing import List, Optional

class ComputeRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    second: int = 0
    tz: str
    lat: float
    lon: float
    planets: Optional[List[str]] = None
    use_topo: Optional[bool] = False
    topo_alt: Optional[float] = 0.0

class BirthDetails(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    second: int = 0
    tz: str
    lat: float
    lon: float
    planets: Optional[List[str]] = None
    use_topo: Optional[bool] = False
    topo_alt: Optional[float] = 0.0


class MatchRequest(BaseModel):
    boy: BirthDetails
    girl: BirthDetails

class FamilyMemberCreate(BaseModel):
    name: str
    relationship: str
    gender: str
    date_of_birth: str  # YYYY-MM-DD
    time_of_birth: str  # HH:MM
    location: str
    latitude: float
    longitude: float
    timezone: str = "Asia/Kolkata"

class FamilyMemberResponse(FamilyMemberCreate):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True
