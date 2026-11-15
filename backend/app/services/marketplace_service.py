import datetime
from datetime import timezone, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.marketplace import BuyerListing, PurchaseOrder
from app.models.inventory import Inventory
from app.models.asset import ColdAsset
from app.models.user import User
from app.schemas.marketplace import ListingCreate, OrderCreate, ListingQualityApproval
from app.services.audit_service import log_audit_event

MIN_DISCOUNT_PCT = 10.0
MAX_DISCOUNT_PCT = 50.0

def calculate_sliding_discount(
    base_price_per_kg: float,
    listed_at: datetime.datetime,
    expires_at: datetime.datetime,
    now: Optional[datetime.datetime] = None
) -> Tuple[float, float]:
    """
    Computes explainable, transparent sliding discount over time.
    As expiration approaches, discount increases smoothly from 10% to 50%.
    
    PROTOTYPE HONESTY NOTE:
    Time alone does NOT guarantee food safety. Physical quality approval by
    the facility operator is strictly mandatory before publishing.
    """
    if now is None:
        now = datetime.datetime.now(timezone.utc)

    # Ensure timezone awareness
    if listed_at.tzinfo is None:
        listed_at = listed_at.replace(tzinfo=timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    total_window_seconds = max(1.0, (expires_at - listed_at).total_seconds())
    elapsed_seconds = (now - listed_at).total_seconds()

    progress = min(1.0, max(0.0, elapsed_seconds / total_window_seconds))
    discount_pct = round(MIN_DISCOUNT_PCT + progress * (MAX_DISCOUNT_PCT - MIN_DISCOUNT_PCT), 1)
    discounted_price = round(base_price_per_kg * (1.0 - (discount_pct / 100.0)), 2)

    return discount_pct, max(1.0, discounted_price)


def create_surplus_listing(
    db: Session,
    operator: User,
    data: ListingCreate,
    ip_address: Optional[str] = None
) -> BuyerListing:
    """
    Operator creates a surplus listing for an inventory item.
    If approve_immediately is True, the operator signs off on produce quality
    immediately and the listing becomes APPROVED. Otherwise it stays PENDING_APPROVAL.
    Unapproved items are NEVER shown to buyers or purchasable.
    """
    inventory = db.query(Inventory).filter_by(id=data.inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory record not found")

    asset = inventory.asset or db.query(ColdAsset).filter_by(id=inventory.asset_id).first()
    if operator.role != "ADMIN" and asset.operator_id != operator.id:
        raise HTTPException(status_code=403, detail="Only the asset operator can list this inventory as surplus")

    quantity = data.initial_quantity_kg or inventory.current_quantity_kg
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Cannot list surplus with zero or negative quantity")
    if quantity > inventory.current_quantity_kg:
        raise HTTPException(status_code=400, detail=f"Cannot list quantity ({quantity} kg) greater than current stock ({inventory.current_quantity_kg} kg)")

    now = datetime.datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=data.expiry_hours)

    discount_pct, disc_price = calculate_sliding_discount(
        base_price_per_kg=data.base_price_per_kg,
        listed_at=now,
        expires_at=expires_at,
        now=now
    )

    batch = inventory.batch
    crop_code = batch.crop_code if batch else "produce"

    listing_status = "APPROVED" if data.approve_immediately else "PENDING_APPROVAL"
    approved_by = operator.id if data.approve_immediately else None
    approved_at = now if data.approve_immediately else None

    listing = BuyerListing(
        inventory_id=inventory.id,
        asset_id=inventory.asset_id,
        operator_id=operator.id,
        crop_code=crop_code,
        initial_quantity_kg=quantity,
        available_quantity_kg=quantity,
        base_price_per_kg=data.base_price_per_kg,
        current_discount_pct=discount_pct,
        discounted_price_per_kg=disc_price,
        status=listing_status,
        quality_approved_by=approved_by,
        quality_approved_at=approved_at,
        quality_grade=data.quality_grade,
        listed_at=now,
        expires_at=expires_at,
        notes=data.notes
    )
    db.add(listing)
    inventory.status = "SURPLUS_LISTED"
    db.flush()

    log_audit_event(
        db=db,
        action="SURPLUS_LISTING_CREATED",
        resource_type="BUYER_LISTING",
        resource_id=listing.id,
        user_id=operator.id,
        details={
            "inventory_id": inventory.id,
            "status": listing_status,
            "initial_quantity_kg": quantity,
            "base_price_per_kg": data.base_price_per_kg,
            "quality_approved": data.approve_immediately
        },
        ip_address=ip_address
    )

    db.commit()
    db.refresh(listing)
    return listing


def approve_listing_quality(
    db: Session,
    listing_id: str,
    operator: User,
    approval: ListingQualityApproval,
    ip_address: Optional[str] = None
) -> BuyerListing:
    """
    Operator explicitly signs off on quality inspection.
    This unlocks the listing for public buyer visibility and ordering.
    """
    listing = db.query(BuyerListing).filter_by(id=listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Surplus listing not found")

    asset = listing.asset or db.query(ColdAsset).filter_by(id=listing.asset_id).first()
    if operator.role != "ADMIN" and asset.operator_id != operator.id:
        raise HTTPException(status_code=403, detail="Only the asset operator can approve surplus quality")

    now = datetime.datetime.now(timezone.utc)
    listing.status = "APPROVED"
    listing.quality_approved_by = operator.id
    listing.quality_approved_at = now
    listing.quality_grade = approval.quality_grade
    if approval.notes:
        listing.notes = f"{listing.notes or ''}\nQuality Inspection: {approval.notes}".strip()

    log_audit_event(
        db=db,
        action="SURPLUS_QUALITY_APPROVED",
        resource_type="BUYER_LISTING",
        resource_id=listing.id,
        user_id=operator.id,
        details={
            "quality_grade": approval.quality_grade,
            "approved_at": now.isoformat()
        },
        ip_address=ip_address
    )

    db.commit()
    db.refresh(listing)
    return listing


def get_public_listings(
    db: Session,
    crop_code: Optional[str] = None,
    min_quantity_kg: Optional[float] = None,
    max_price_inr: Optional[float] = None
) -> List[BuyerListing]:
    """
    Retrieves public surplus listings available to buyers.
    SECURITY & QUALITY INVARIANT:
    Unapproved listings (PENDING_APPROVAL) are STRICTLY excluded.
    """
    query = db.query(BuyerListing).filter(
        BuyerListing.status == "APPROVED",
        BuyerListing.available_quantity_kg > 0
    )

    if crop_code:
        query = query.filter(BuyerListing.crop_code.ilike(f"%{crop_code}%"))
    if min_quantity_kg:
        query = query.filter(BuyerListing.available_quantity_kg >= min_quantity_kg)

    listings = query.all()
    now = datetime.datetime.now(timezone.utc)

    results = []
    for l in listings:
        # Check if expired
        if l.expires_at and l.expires_at.replace(tzinfo=timezone.utc) < now:
            continue
        
        # Recalculate dynamic sliding discount
        disc_pct, disc_price = calculate_sliding_discount(
            base_price_per_kg=l.base_price_per_kg,
            listed_at=l.listed_at,
            expires_at=l.expires_at,
            now=now
        )
        l.current_discount_pct = disc_pct
        l.discounted_price_per_kg = disc_price
        
        if max_price_inr and disc_price > max_price_inr:
            continue

        results.append(l)

    return results


def create_purchase_order(
    db: Session,
    buyer: User,
    order_data: OrderCreate,
    ip_address: Optional[str] = None
) -> PurchaseOrder:
    """
    Atomic buyer order placement preventing overselling/double-selling.
    Checks remaining quantity inside a database transaction with stock decrement.
    
    PROTOTYPE HONESTY NOTE:
    This is an order request and reservation. Zero payment processing is performed.
    """
    if buyer.role not in ["BUYER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Only verified buyers can place surplus purchase orders")

    # Select listing with lock where possible
    listing = db.query(BuyerListing).with_for_update().filter_by(id=order_data.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Surplus listing not found")

    # STRICT INVARIANT: Unapproved listings can NEVER be purchased
    if listing.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This surplus listing has not received quality approval from the facility operator"
        )

    # Check available stock
    if order_data.quantity_kg > listing.available_quantity_kg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested quantity ({order_data.quantity_kg:.1f} kg) exceeds available stock ({listing.available_quantity_kg:.1f} kg)"
        )

    now = datetime.datetime.now(timezone.utc)
    disc_pct, unit_price = calculate_sliding_discount(
        base_price_per_kg=listing.base_price_per_kg,
        listed_at=listing.listed_at,
        expires_at=listing.expires_at,
        now=now
    )
    total_price = round(unit_price * order_data.quantity_kg, 2)

    # Atomic stock deduction
    listing.available_quantity_kg = round(listing.available_quantity_kg - order_data.quantity_kg, 2)
    if listing.available_quantity_kg <= 0.001:
        listing.available_quantity_kg = 0.0
        listing.status = "SOLD_OUT"

    # Also update associated inventory record
    inventory = listing.inventory
    if inventory:
        inventory.current_quantity_kg = max(0.0, round(inventory.current_quantity_kg - order_data.quantity_kg, 2))
        if inventory.current_quantity_kg <= 0.001:
            inventory.status = "DISPATCHED"

    order = PurchaseOrder(
        listing_id=listing.id,
        buyer_id=buyer.id,
        quantity_kg=order_data.quantity_kg,
        unit_price_inr=unit_price,
        total_price_inr=total_price,
        status="REQUESTED",
        delivery_preference=order_data.delivery_preference,
        contact_phone=order_data.contact_phone or buyer.phone,
        notes=order_data.notes
    )
    db.add(order)
    db.flush()

    log_audit_event(
        db=db,
        action="PURCHASE_ORDER_CREATED",
        resource_type="PURCHASE_ORDER",
        resource_id=order.id,
        user_id=buyer.id,
        details={
            "listing_id": listing.id,
            "quantity_kg": order_data.quantity_kg,
            "unit_price_inr": unit_price,
            "total_price_inr": total_price,
            "remaining_listing_stock_kg": listing.available_quantity_kg
        },
        ip_address=ip_address
    )

    db.commit()
    db.refresh(order)
    return order
