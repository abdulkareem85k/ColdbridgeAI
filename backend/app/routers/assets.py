import datetime
from datetime import timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user import User
from app.models.asset import ColdAsset, StaticAssetDetail, MobileAssetDetail
from app.schemas.asset import (
    ColdAssetCreate,
    ColdAssetUpdate,
    AssetAvailabilityUpdate,
    ColdAssetResponse,
    ColdAssetListResponse
)
from app.services.asset_service import compute_asset_data_status
from app.services.ownership_service import verify_asset_ownership

router = APIRouter(prefix="/assets", tags=["Cold Assets"])

def format_asset_response(asset: ColdAsset) -> ColdAssetResponse:
    """Format ColdAsset into response schema with dynamic data_status computation."""
    data_status = compute_asset_data_status(asset)
    return ColdAssetResponse(
        id=asset.id,
        operator_id=asset.operator_id,
        name=asset.name,
        asset_type=asset.asset_type,
        total_capacity_kg=asset.total_capacity_kg,
        available_capacity_kg=asset.available_capacity_kg,
        price_per_kg_per_day=asset.price_per_kg_per_day,
        latitude=asset.latitude,
        longitude=asset.longitude,
        is_active=asset.is_active,
        data_source=asset.data_source,
        data_status=data_status,
        static_detail=asset.static_detail,
        mobile_detail=asset.mobile_detail,
        created_at=asset.created_at,
        updated_at=asset.updated_at
    )

@router.post("", response_model=ColdAssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    req: ColdAssetCreate,
    current_user: User = Depends(require_role("STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Register a new cooling asset (Static Cold Room or Mobile Solar Van).
    Operator role verification and capacity constraints enforced.
    """
    # Role validation against asset type
    if current_user.role == "STATIC_OPERATOR" and req.asset_type != "STATIC":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A Static Operator cannot register mobile cooling vans."
        )
    if current_user.role == "VAN_OPERATOR" and req.asset_type != "MOBILE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A Van Operator cannot register static cold rooms."
        )

    asset = ColdAsset(
        operator_id=current_user.id,
        name=req.name,
        asset_type=req.asset_type,
        total_capacity_kg=req.total_capacity_kg,
        available_capacity_kg=req.available_capacity_kg or req.total_capacity_kg,
        price_per_kg_per_day=req.price_per_kg_per_day,
        latitude=req.latitude,
        longitude=req.longitude,
        is_active=True,
        data_source="LIVE"
    )
    db.add(asset)
    db.flush()

    if req.asset_type == "STATIC":
        detail = StaticAssetDetail(
            asset_id=asset.id,
            supported_crops=req.static_detail.supported_crops,
            min_temperature_c=req.static_detail.min_temperature_c,
            max_temperature_c=req.static_detail.max_temperature_c,
            address=req.static_detail.address
        )
        db.add(detail)
    elif req.asset_type == "MOBILE":
        now_utc = datetime.datetime.now(timezone.utc)
        detail = MobileAssetDetail(
            asset_id=asset.id,
            vehicle_ref=req.mobile_detail.vehicle_ref,
            service_radius_km=req.mobile_detail.service_radius_km,
            solar_reliability=req.mobile_detail.solar_reliability,
            last_location_at=req.mobile_detail.last_location_at or now_utc
        )
        db.add(detail)

    db.commit()
    db.refresh(asset)
    return format_asset_response(asset)

@router.get("", response_model=ColdAssetListResponse)
def list_assets(
    asset_type: Optional[str] = Query(None, description="STATIC or MOBILE"),
    operator_id: Optional[str] = Query(None, description="Filter by operator ID"),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List cooling assets with pagination and filters."""
    query = db.query(ColdAsset)

    if asset_type:
        query = query.filter(ColdAsset.asset_type == asset_type.upper())
    if operator_id:
        query = query.filter(ColdAsset.operator_id == operator_id)
    if is_active is not None:
        query = query.filter(ColdAsset.is_active == is_active)

    total = query.count()
    assets = query.order_by(ColdAsset.created_at.desc()).offset(skip).limit(limit).all()

    items = [format_asset_response(a) for a in assets]
    return {
        "total": total,
        "items": items,
        "skip": skip,
        "limit": limit
    }

@router.get("/{asset_id}", response_model=ColdAssetResponse)
def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve single asset by ID."""
    asset = db.query(ColdAsset).filter(ColdAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cold asset not found."
        )
    return format_asset_response(asset)

@router.patch("/{asset_id}", response_model=ColdAssetResponse)
def update_asset(
    asset_id: str,
    req: ColdAssetUpdate,
    current_user: User = Depends(require_role("STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN")),
    db: Session = Depends(get_db)
):
    """Update basic asset information with strict operator ownership verification."""
    asset = db.query(ColdAsset).filter(ColdAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cold asset not found."
        )

    verify_asset_ownership(asset, current_user)

    update_data = req.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(asset, field, val)

    db.commit()
    db.refresh(asset)
    return format_asset_response(asset)

@router.patch("/{asset_id}/availability", response_model=ColdAssetResponse)
def update_asset_availability(
    asset_id: str,
    req: AssetAvailabilityUpdate,
    current_user: User = Depends(require_role("STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Update asset availability and available capacity.
    Enforces capacity invariants: 0 <= available_capacity_kg <= total_capacity_kg.
    """
    asset = db.query(ColdAsset).filter(ColdAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cold asset not found."
        )

    verify_asset_ownership(asset, current_user)

    if req.available_capacity_kg is not None:
        if req.available_capacity_kg > asset.total_capacity_kg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Available capacity ({req.available_capacity_kg} kg) cannot exceed total capacity ({asset.total_capacity_kg} kg)."
            )
        if req.available_capacity_kg < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Available capacity cannot be negative."
            )
        asset.available_capacity_kg = req.available_capacity_kg

    if req.is_active is not None:
        asset.is_active = req.is_active

    db.commit()
    db.refresh(asset)
    return format_asset_response(asset)
