from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class RouteResponse(BaseModel):
    distance_km: float
    duration_minutes: float
    encoded_polyline: Optional[str] = None
    route_source: str  # OSRM_ROUTES or ESTIMATED
    cached: bool = False
    note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ReverseGeocodeResponse(BaseModel):
    address: Optional[str] = None
    source: str = "NOMINATIM"
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)

class SearchResult(BaseModel):
    display_name: str
    latitude: float
    longitude: float
    lat: float
    lon: float

    model_config = ConfigDict(from_attributes=True)
