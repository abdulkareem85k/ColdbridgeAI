import time
import threading
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.produce import ProduceBatch
from app.models.asset import ColdAsset
from app.models.matching import MatchingRequest, Bid
from app.models.booking import Booking
from app.schemas.maps import RouteResponse, ReverseGeocodeResponse, SearchResult
from app.services.maps_service import compute_route, reverse_geocode, search_address

router = APIRouter(prefix="/maps", tags=["OpenStreetMap & Routing"])

# Per-user in-memory sliding window rate limiter
# NOTE: Applies per single-worker process. In-memory dictionary is suitable for exhibition/single-worker setup.
_user_route_history: dict[str, list[float]] = {}
_route_rate_lock = threading.Lock()
MAX_ROUTE_CALLS_PER_MINUTE_PER_USER = 60

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
    Enforces authorization, coordinate bounds, mode exclusivity, and rate limits.
    """
    # 1. Per-user in-memory rate limiting
    now = time.time()
    with _route_rate_lock:
        history = _user_route_history.setdefault(str(current_user.id), [])
        history[:] = [t for t in history if now - t < 60.0]
        if len(history) >= MAX_ROUTE_CALLS_PER_MINUTE_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many route requests. Please wait a moment."
            )
        history.append(now)

    # 2. Check mode exclusivity
    has_resource = (batch_id is not None) or (asset_id is not None)
    has_coords = any(x is not None for x in [origin_lat, origin_lng, dest_lat, dest_lng])

    if has_resource and has_coords:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot mix resource IDs (batch_id/asset_id) with explicit coordinates."
        )

    if has_resource:
        if not (batch_id and asset_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Both batch_id and asset_id are required for resource routing."
            )

        batch = db.query(ProduceBatch).filter(ProduceBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produce batch not found.")

        asset = db.query(ColdAsset).filter(ColdAsset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cold asset not found.")

        # Authorization checks
        if current_user.role == "ADMIN":
            pass
        elif current_user.role == "FARMER":
            if batch.farmer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You do not own this produce batch."
                )
            if not asset.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Destination cold asset is not active."
                )
        elif current_user.role in ["STATIC_OPERATOR", "VAN_OPERATOR"]:
            if asset.operator_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You can only route to cold assets that you own."
                )
            
            # Find all assets owned by this operator
            op_asset_ids = [r[0] for r in db.query(ColdAsset.id).filter(ColdAsset.operator_id == current_user.id).all()]
            
            # Check for existing booking or bid involving this batch and one of the operator's assets
            has_booking = db.query(Booking).filter(
                Booking.batch_id == batch.id,
                Booking.asset_id.in_(op_asset_ids)
            ).first() is not None

            has_bid = False
            if not has_booking:
                req = db.query(MatchingRequest).filter(MatchingRequest.batch_id == batch.id).first()
                if req:
                    has_bid = db.query(Bid).filter(
                        Bid.request_id == req.id,
                        Bid.asset_id.in_(op_asset_ids)
                    ).first() is not None

            if not (has_booking or has_bid):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You do not have an active booking, request, or bid involving this batch."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Your role is not authorized to compute routes for batches."
            )

        origin = (batch.latitude, batch.longitude)
        destination = (asset.latitude, asset.longitude)

    elif has_coords:
        if not all(x is not None for x in [origin_lat, origin_lng, dest_lat, dest_lng]):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="All four coordinates (origin_lat, origin_lng, dest_lat, dest_lng) must be provided."
            )

        if not (-90.0 <= origin_lat <= 90.0 and -90.0 <= dest_lat <= 90.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Latitude must be between -90.0 and 90.0 degrees."
            )
        if not (-180.0 <= origin_lng <= 180.0 and -180.0 <= dest_lng <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Longitude must be between -180.0 and 180.0 degrees."
            )

        origin = (origin_lat, origin_lng)
        destination = (dest_lat, dest_lng)

    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Must provide either (batch_id and asset_id) OR (origin_lat, origin_lng, dest_lat, dest_lng)."
        )

    route_info = compute_route(origin, destination, db)
    return route_info

@router.get("/reverse-geocode", response_model=ReverseGeocodeResponse)
def get_reverse_geocode(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude between -90 and 90"),
    lng: float = Query(..., ge=-180.0, le=180.0, description="Longitude between -180 and 180"),
    current_user: User = Depends(get_current_user)
):
    """
    Reverse geocode latitude and longitude into human-readable address via OpenStreetMap Nominatim.
    Rate limited to <= 1 req/s per process, cached for 24 hours, with safe fallback shape on failure.
    """
    result = reverse_geocode(lat, lng)
    return result

@router.get("/search", response_model=List[SearchResult])
def get_search(
    q: str = Query(..., min_length=3, max_length=200, description="Address or place search query (3-200 chars)"),
    limit: int = Query(1, ge=1, le=5, description="Maximum number of search results (1-5)"),
    current_user: User = Depends(get_current_user)
):
    """
    Search OpenStreetMap Nominatim for addresses / places with Maharashtra bias.
    Rate limited to <= 1 req/s per process, cached for 24 hours. Returns list of matches.
    """
    results = search_address(q, limit=limit)
    return results
