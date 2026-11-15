from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.produce import ProduceBatch
from app.models.asset import ColdAsset
from app.schemas.maps import RouteResponse, ReverseGeocodeResponse
from app.services.maps_service import compute_route, reverse_geocode

router = APIRouter(prefix="/maps", tags=["OpenStreetMap & Routing"])

@router.get("/route", response_model=RouteResponse)
def get_route(
    batch_id: Optional[str] = Query(None, description="Batch ID for origin coordinates"),
    asset_id: Optional[str] = Query(None, description="Asset ID for destination coordinates"),
    origin_lat: Optional[float] = Query(None),
    origin_lng: Optional[float] = Query(None),
    dest_lat: Optional[float] = Query(None),
    dest_lng: Optional[float] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compute road route between produce origin and cooling destination using OSRM / OpenStreetMap.
    Automatically caches results and falls back to straight-line estimation if external routing is offline.
    """
    if batch_id and asset_id:
        batch = db.query(ProduceBatch).filter(ProduceBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produce batch not found.")
        
        asset = db.query(ColdAsset).filter(ColdAsset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cold asset not found.")

        origin = (batch.latitude, batch.longitude)
        destination = (asset.latitude, asset.longitude)
    elif all(v is not None for v in [origin_lat, origin_lng, dest_lat, dest_lng]):
        origin = (origin_lat, origin_lng)
        destination = (dest_lat, dest_lng)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either (batch_id and asset_id) OR (origin_lat, origin_lng, dest_lat, dest_lng)."
        )

    route_info = compute_route(origin, destination, db)
    return route_info

@router.get("/reverse-geocode", response_model=ReverseGeocodeResponse)
def get_reverse_geocode(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lng: float = Query(..., ge=-180.0, le=180.0),
    current_user: User = Depends(get_current_user)
):
    """
    Reverse geocode latitude and longitude into human-readable address via OpenStreetMap Nominatim.
    """
    address = reverse_geocode(lat, lng)
    return {
        "address": address,
        "latitude": lat,
        "longitude": lng
    }
