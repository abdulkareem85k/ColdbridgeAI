"""
ColdBridge AI - Bookings Router (M6)

Provides endpoints to view bookings, track lifecycle status,
execute verified state machine transitions, and check reservation expirations.
"""

from typing import List, Optional
import datetime
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.booking import Booking
from app.models.asset import ColdAsset
from app.schemas.booking import BookingResponse, BookingStatusUpdate, PriceEstimate
from app.services.booking_service import (
    update_booking_status,
    check_and_expire_reservations,
    calculate_price_estimate
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def enrich_booking(b: Booking) -> dict:
    """Format booking data with asset info and cancelability."""
    can_cancel = b.status in ["RESERVED", "CONFIRMED", "PICKUP_SCHEDULED"]
    asset = b.asset
    return {
        "id": b.id,
        "request_id": b.request_id,
        "batch_id": b.batch_id,
        "asset_id": b.asset_id,
        "farmer_id": b.farmer_id,
        "quantity_kg": b.quantity_kg,
        "status": b.status,
        "reserved_until": b.reserved_until,
        "estimated_total_inr": b.estimated_total_inr,
        "rate_per_kg_per_day": b.rate_per_kg_per_day,
        "days_estimated": b.days_estimated,
        "status_updated_by": b.status_updated_by,
        "created_at": b.created_at,
        "updated_at": b.updated_at,
        "asset_name": asset.name if asset else "Unknown Facility",
        "asset_type": asset.asset_type if asset else "STATIC",
        "can_cancel": can_cancel
    }


@router.get("/my-bookings")
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all active and past bookings relevant to the logged-in user.
    - Farmer: batches they own.
    - Operator: assets they own.
    - Admin: all bookings.
    """
    # First, run a passive check to expire overdue reservations
    check_and_expire_reservations(db)

    if current_user.role == "ADMIN":
        bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    elif current_user.role in ["STATIC_OPERATOR", "VAN_OPERATOR"]:
        bookings = (
            db.query(Booking)
            .join(ColdAsset, Booking.asset_id == ColdAsset.id)
            .filter(ColdAsset.operator_id == current_user.id)
            .order_by(Booking.created_at.desc())
            .all()
        )
    else:  # FARMER
        bookings = db.query(Booking).filter_by(farmer_id=current_user.id).order_by(Booking.created_at.desc()).all()

    return [enrich_booking(b) for b in bookings]


@router.get("/{id}")
def get_booking_detail(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve comprehensive booking details including timeline,
    asset metadata, transparent price breakdown, and cancellation eligibility.
    """
    check_and_expire_reservations(db)

    booking = db.query(Booking).filter_by(id=id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    asset = booking.asset
    # Ownership verification
    is_owner = (
        current_user.role == "ADMIN" or
        booking.farmer_id == current_user.id or
        (asset and asset.operator_id == current_user.id)
    )
    if not is_owner:
        raise HTTPException(status_code=403, detail="You do not have access to view this booking")

    price_breakdown = calculate_price_estimate(
        quantity_kg=booking.quantity_kg,
        rate_per_kg_per_day=booking.rate_per_kg_per_day,
        days=booking.days_estimated,
        asset_type=asset.asset_type if asset else "STATIC"
    )

    enriched = enrich_booking(booking)
    enriched["price_breakdown"] = price_breakdown
    return enriched


@router.patch("/{id}/status")
def patch_booking_status(
    id: str,
    payload: BookingStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Advance booking status according to the strict state machine.
    Releases capacity exactly once on cancellation, expiration, or failure.
    """
    booking = update_booking_status(
        db=db,
        booking_id=id,
        new_status=payload.status,
        current_user=current_user,
        ip_address=request.client.host if request.client else None
    )
    return enrich_booking(booking)


@router.post("/check-expirations")
def trigger_expiration_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually check for expired RESERVED bookings and release capacity.
    """
    expired_count = check_and_expire_reservations(db)
    return {
        "status": "success",
        "expired_reservations_processed": expired_count
    }
