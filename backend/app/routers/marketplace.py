from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.models.user import User
from app.models.marketplace import BuyerListing, PurchaseOrder
from app.models.asset import ColdAsset
from app.schemas.marketplace import (
    ListingCreate,
    ListingQualityApproval,
    ListingResponse,
    OrderCreate,
    OrderResponse
)
from app.core.dependencies import get_current_user
from app.services import marketplace_service

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

def get_asset_district(asset) -> Optional[str]:
    if not asset:
        return None
    if asset.operator and asset.operator.operator_profile and asset.operator.operator_profile.district:
        return asset.operator.operator_profile.district
    if asset.static_detail and asset.static_detail.address:
        parts = [p.strip() for p in asset.static_detail.address.split(",")]
        return parts[-1]
    return "Maharashtra"

@router.get("/listings", response_model=List[ListingResponse])
def get_public_marketplace_listings(
    crop_code: Optional[str] = Query(None, description="Filter by crop name or code"),
    min_quantity_kg: Optional[float] = Query(None, description="Minimum available quantity in kg"),
    max_price_inr: Optional[float] = Query(None, description="Maximum price per kg in INR"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Public Buyer Marketplace view.
    STRICT REQUIREMENT: Only listings with status='APPROVED' are returned.
    Unapproved items are never exposed to buyers.
    """
    listings = marketplace_service.get_public_listings(
        db=db,
        crop_code=crop_code,
        min_quantity_kg=min_quantity_kg,
        max_price_inr=max_price_inr
    )

    results = []
    for l in listings:
        asset = l.asset
        results.append(ListingResponse(
            id=l.id,
            inventory_id=l.inventory_id,
            asset_id=l.asset_id,
            asset_name=asset.name if asset else None,
            district=get_asset_district(asset),
            latitude=asset.latitude if asset else None,
            longitude=asset.longitude if asset else None,
            operator_id=l.operator_id,
            crop_code=l.crop_code,
            initial_quantity_kg=l.initial_quantity_kg,
            available_quantity_kg=l.available_quantity_kg,
            base_price_per_kg=l.base_price_per_kg,
            current_discount_pct=l.current_discount_pct,
            discounted_price_per_kg=l.discounted_price_per_kg,
            status=l.status,
            quality_approved_by=l.quality_approved_by,
            quality_approved_at=l.quality_approved_at,
            quality_grade=l.quality_grade,
            listed_at=l.listed_at,
            expires_at=l.expires_at,
            notes=l.notes,
            created_at=l.created_at,
            data_source="SIMULATED",
            data_status="FRESH"
        ))
    return results


@router.get("/operator-listings", response_model=List[ListingResponse])
def get_operator_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Listings managed by the operator (including PENDING_APPROVAL and SOLD_OUT).
    """
    if current_user.role not in ["STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Only operators and admins can access this view")

    query = db.query(BuyerListing)
    if current_user.role != "ADMIN":
        query = query.filter_by(operator_id=current_user.id)

    listings = query.order_by(BuyerListing.created_at.desc()).all()
    results = []
    for l in listings:
        asset = l.asset
        results.append(ListingResponse(
            id=l.id,
            inventory_id=l.inventory_id,
            asset_id=l.asset_id,
            asset_name=asset.name if asset else None,
            district=get_asset_district(asset),
            latitude=asset.latitude if asset else None,
            longitude=asset.longitude if asset else None,
            operator_id=l.operator_id,
            crop_code=l.crop_code,
            initial_quantity_kg=l.initial_quantity_kg,
            available_quantity_kg=l.available_quantity_kg,
            base_price_per_kg=l.base_price_per_kg,
            current_discount_pct=l.current_discount_pct,
            discounted_price_per_kg=l.discounted_price_per_kg,
            status=l.status,
            quality_approved_by=l.quality_approved_by,
            quality_approved_at=l.quality_approved_at,
            quality_grade=l.quality_grade,
            listed_at=l.listed_at,
            expires_at=l.expires_at,
            notes=l.notes,
            created_at=l.created_at,
            data_source="SIMULATED",
            data_status="FRESH"
        ))
    return results


@router.post("/listings", response_model=ListingResponse)
def create_listing(
    data: ListingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Operator creates a surplus listing for stored inventory.
    """
    if current_user.role not in ["STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Only operators or admins can create surplus listings")

    ip = request.client.host if request.client else None
    listing = marketplace_service.create_surplus_listing(
        db=db,
        operator=current_user,
        data=data,
        ip_address=ip
    )
    asset = listing.asset
    return ListingResponse(
        id=listing.id,
        inventory_id=listing.inventory_id,
        asset_id=listing.asset_id,
        asset_name=asset.name if asset else None,
        district=get_asset_district(asset),
        latitude=asset.latitude if asset else None,
        longitude=asset.longitude if asset else None,
        operator_id=listing.operator_id,
        crop_code=listing.crop_code,
        initial_quantity_kg=listing.initial_quantity_kg,
        available_quantity_kg=listing.available_quantity_kg,
        base_price_per_kg=listing.base_price_per_kg,
        current_discount_pct=listing.current_discount_pct,
        discounted_price_per_kg=listing.discounted_price_per_kg,
        status=listing.status,
        quality_approved_by=listing.quality_approved_by,
        quality_approved_at=listing.quality_approved_at,
        quality_grade=listing.quality_grade,
        listed_at=listing.listed_at,
        expires_at=listing.expires_at,
        notes=listing.notes,
        created_at=listing.created_at,
        data_source="SIMULATED",
        data_status="FRESH"
    )


@router.post("/listings/{listing_id}/approve", response_model=ListingResponse)
def approve_listing(
    listing_id: str,
    approval: ListingQualityApproval,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Operator signs off on quality inspection, publishing the listing.
    """
    ip = request.client.host if request.client else None
    listing = marketplace_service.approve_listing_quality(
        db=db,
        listing_id=listing_id,
        operator=current_user,
        approval=approval,
        ip_address=ip
    )
    asset = listing.asset
    return ListingResponse(
        id=listing.id,
        inventory_id=listing.inventory_id,
        asset_id=listing.asset_id,
        asset_name=asset.name if asset else None,
        district=get_asset_district(asset),
        latitude=asset.latitude if asset else None,
        longitude=asset.longitude if asset else None,
        operator_id=listing.operator_id,
        crop_code=listing.crop_code,
        initial_quantity_kg=listing.initial_quantity_kg,
        available_quantity_kg=listing.available_quantity_kg,
        base_price_per_kg=listing.base_price_per_kg,
        current_discount_pct=listing.current_discount_pct,
        discounted_price_per_kg=listing.discounted_price_per_kg,
        status=listing.status,
        quality_approved_by=listing.quality_approved_by,
        quality_approved_at=listing.quality_approved_at,
        quality_grade=listing.quality_grade,
        listed_at=listing.listed_at,
        expires_at=listing.expires_at,
        notes=listing.notes,
        created_at=listing.created_at,
        data_source="SIMULATED",
        data_status="FRESH"
    )


@router.post("/orders", response_model=OrderResponse)
def place_order(
    data: OrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Buyer places purchase order against an approved surplus listing.
    Atomically decrements stock and guarantees no double-selling or overselling.
    PROTOTYPE NOTE: Order reservation only; NO payment gateway.
    """
    ip = request.client.host if request.client else None
    order = marketplace_service.create_purchase_order(
        db=db,
        buyer=current_user,
        order_data=data,
        ip_address=ip
    )
    listing = order.listing
    asset = listing.asset if listing else None
    return OrderResponse(
        id=order.id,
        listing_id=order.listing_id,
        buyer_id=order.buyer_id,
        buyer_name=current_user.full_name,
        crop_code=listing.crop_code if listing else None,
        asset_name=asset.name if asset else None,
        quantity_kg=order.quantity_kg,
        unit_price_inr=order.unit_price_inr,
        total_price_inr=order.total_price_inr,
        status=order.status,
        delivery_preference=order.delivery_preference,
        contact_phone=order.contact_phone,
        notes=order.notes,
        created_at=order.created_at,
        data_source="SIMULATED"
    )


@router.get("/orders", response_model=List[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve orders with strict ownership verification:
    - Buyers see only their own orders
    - Operators see orders on listings for their facilities
    - Admins see all
    """
    if current_user.role == "BUYER":
        orders = db.query(PurchaseOrder).filter_by(buyer_id=current_user.id).order_by(PurchaseOrder.created_at.desc()).all()
    elif current_user.role in ["STATIC_OPERATOR", "VAN_OPERATOR"]:
        # Find listings owned by operator
        listing_ids = [l.id for l in db.query(BuyerListing).filter_by(operator_id=current_user.id).all()]
        orders = db.query(PurchaseOrder).filter(PurchaseOrder.listing_id.in_(listing_ids)).order_by(PurchaseOrder.created_at.desc()).all()
    elif current_user.role == "ADMIN":
        orders = db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).all()
    else:
        orders = []

    res = []
    for o in orders:
        listing = o.listing
        asset = listing.asset if listing else None
        buyer = o.buyer
        res.append(OrderResponse(
            id=o.id,
            listing_id=o.listing_id,
            buyer_id=o.buyer_id,
            buyer_name=buyer.full_name if buyer else "Buyer",
            crop_code=listing.crop_code if listing else None,
            asset_name=asset.name if asset else None,
            quantity_kg=o.quantity_kg,
            unit_price_inr=o.unit_price_inr,
            total_price_inr=o.total_price_inr,
            status=o.status,
            delivery_preference=o.delivery_preference,
            contact_phone=o.contact_phone,
            notes=o.notes,
            created_at=o.created_at,
            data_source="SIMULATED"
        ))
    return res
