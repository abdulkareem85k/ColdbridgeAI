"""
ColdBridge AI - Booking Service & Capacity State Machine (M6)

Implements safe booking transactions, strict state machine transitions,
atomic capacity reservation and release, reservation expiration,
and pay-per-use price estimation (INR prototype).
"""

import datetime
from datetime import timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.matching import MatchingRequest, Bid
from app.models.asset import ColdAsset
from app.models.produce import ProduceBatch
from app.models.user import User
from app.services.audit_service import log_audit_event
from app.services.inventory_service import auto_create_inventory_for_booking
from app.services.solar_adjustment import get_effective_capacity

RESERVATION_DURATION_MINUTES = 15

# Strict State Machine Allowed Transitions (Section G.7)
ALLOWED_TRANSITIONS = {
    "REQUESTED": {"MATCHED", "CANCELLED", "FAILED"},
    "MATCHED": {"RESERVED", "CANCELLED", "EXPIRED"},
    "RESERVED": {"CONFIRMED", "CANCELLED", "EXPIRED"},
    "CONFIRMED": {"PICKUP_SCHEDULED", "PRODUCE_RECEIVED", "CANCELLED", "FAILED"},
    "PICKUP_SCHEDULED": {"PRODUCE_RECEIVED", "CANCELLED", "FAILED"},
    "PRODUCE_RECEIVED": {"IN_STORAGE", "FAILED"},
    "IN_STORAGE": {"COMPLETED", "FAILED"},
}

TERMINAL_STATES = {"COMPLETED", "CANCELLED", "EXPIRED", "FAILED"}


def calculate_price_estimate(
    quantity_kg: float,
    rate_per_kg_per_day: float,
    days: int,
    asset_type: str = "STATIC"
) -> Dict[str, Any]:
    """
    Computes transparent pay-per-use price estimate in INR.
    PROTOTYPE HONESTY: This is an estimate only; there is NO payment gateway.
    """
    days = max(1, int(days))
    storage_subtotal = round(quantity_kg * rate_per_kg_per_day * days, 2)
    # Logistics / Transport fee estimate: van dispatch has transport fee, static has unloading fee
    transport_fee = 350.0 if asset_type == "MOBILE" else 150.0
    # Transparent platform fee (5% of storage fee)
    platform_fee = round(storage_subtotal * 0.05, 2)
    total_estimate = round(storage_subtotal + transport_fee + platform_fee, 2)

    return {
        "quantity_kg": quantity_kg,
        "rate_per_kg_per_day": rate_per_kg_per_day,
        "days": days,
        "storage_subtotal_inr": storage_subtotal,
        "transport_fee_inr": transport_fee,
        "platform_fee_inr": platform_fee,
        "total_estimate_inr": total_estimate,
        "disclaimer": "PROTOTYPE ESTIMATE ONLY: No payment processing or gateway integrated in Phase 1."
    }


def allocate_offer_transaction(
    db: Session,
    request_id: str,
    bid_id: str,
    current_user: User,
    days_estimated: int = 3,
    ip_address: Optional[str] = None
) -> Booking:
    """
    Accepts one offer inside ONE single database transaction.
    Locks asset capacity row, validates availability, reserves capacity,
    marks winning bid accepted and losing bids expired, and creates RESERVED booking.
    """
    # 1. Fetch matching request and verify ownership
    req = db.query(MatchingRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Matching request not found")

    if current_user.role != "ADMIN" and req.farmer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the farmer who created the request can allocate offers")

    if req.status in ["ALLOCATED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail=f"Matching request is already {req.status}")

    # 2. Find selected bid
    selected_bid = db.query(Bid).filter_by(id=bid_id, request_id=req.id).first()
    if not selected_bid:
        raise HTTPException(status_code=404, detail="Selected bid not found on this matching request")

    now = datetime.datetime.now(timezone.utc)
    v_until = selected_bid.valid_until.replace(tzinfo=timezone.utc) if selected_bid.valid_until and selected_bid.valid_until.tzinfo is None else selected_bid.valid_until
    if selected_bid.is_expired or (v_until and v_until < now):
        selected_bid.is_expired = True
        raise HTTPException(status_code=400, detail="Selected bid has expired")

    # 3. Lock asset row for capacity check and update
    # In Postgres: with_for_update(); in SQLite: atomic conditional update
    query = db.query(ColdAsset).filter_by(id=selected_bid.asset_id)
    try:
        asset = query.with_for_update().first()
    except Exception:
        # SQLite does not support SELECT ... FOR UPDATE, fallback to standard query inside transaction
        asset = query.first()

    if not asset or not asset.is_active:
        raise HTTPException(status_code=400, detail="Target cold asset is inactive or unavailable")

    # Check effective capacity under solar reliability
    solar_rel = 1.0
    if asset.asset_type == "MOBILE" and asset.mobile_detail:
        solar_rel = asset.mobile_detail.solar_reliability
    effective_cap = get_effective_capacity(asset.available_capacity_kg, asset.asset_type, solar_rel)

    if effective_cap < req.requested_quantity_kg or asset.available_capacity_kg < req.requested_quantity_kg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset capacity changed or is insufficient ({asset.available_capacity_kg:.1f} kg available). Please re-run matching."
        )

    # 4. Atomic capacity deduction
    asset.available_capacity_kg = round(asset.available_capacity_kg - req.requested_quantity_kg, 2)

    # 5. Price estimation
    price_info = calculate_price_estimate(
        quantity_kg=req.requested_quantity_kg,
        rate_per_kg_per_day=asset.price_per_kg_per_day,
        days=days_estimated,
        asset_type=asset.asset_type
    )

    now = datetime.datetime.now(timezone.utc)
    reserved_until = now + timedelta(minutes=RESERVATION_DURATION_MINUTES)

    # 6. Create Booking in RESERVED status
    booking = Booking(
        request_id=req.id,
        batch_id=req.batch_id,
        asset_id=asset.id,
        farmer_id=req.farmer_id,
        quantity_kg=req.requested_quantity_kg,
        status="RESERVED",
        reserved_until=reserved_until,
        estimated_total_inr=price_info["total_estimate_inr"],
        rate_per_kg_per_day=asset.price_per_kg_per_day,
        days_estimated=days_estimated,
        status_updated_by=current_user.id
    )
    db.add(booking)

    # 7. Update Bids: winning bid is accepted, others are expired
    selected_bid.is_accepted = True
    for bid in req.bids:
        if bid.id != selected_bid.id:
            bid.is_expired = True

    # 8. Update MatchingRequest status
    req.status = "ALLOCATED"

    # 9. Audit Logging
    log_audit_event(
        db=db,
        action="ALLOCATE_BID",
        resource_type="MATCHING_REQUEST",
        resource_id=req.id,
        user_id=current_user.id,
        details={
            "bid_id": selected_bid.id,
            "asset_id": asset.id,
            "quantity_kg": req.requested_quantity_kg,
            "remaining_capacity_kg": asset.available_capacity_kg,
            "estimated_inr": price_info["total_estimate_inr"]
        },
        ip_address=ip_address
    )

    log_audit_event(
        db=db,
        action="CREATE_BOOKING_RESERVED",
        resource_type="BOOKING",
        resource_id=booking.id,
        user_id=current_user.id,
        details={
            "status": "RESERVED",
            "quantity_kg": booking.quantity_kg,
            "reserved_until": reserved_until.isoformat()
        },
        ip_address=ip_address
    )

    db.commit()
    db.refresh(booking)
    return booking


def update_booking_status(
    db: Session,
    booking_id: str,
    new_status: str,
    current_user: User,
    ip_address: Optional[str] = None
) -> Booking:
    """
    Executes booking state machine transition with strict validation,
    ownership checks, and atomic capacity release exactly once on terminal/cancellation.
    """
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    old_status = booking.status.upper()
    target_status = new_status.upper()

    # 1. Reject transition from terminal states
    if old_status in TERMINAL_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Booking is in terminal state '{old_status}' and cannot transition further"
        )

    # 2. Check Cancellation Rule upfront
    if target_status == "CANCELLED":
        if old_status in ["PRODUCE_RECEIVED", "IN_STORAGE"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel booking after produce has been received by facility"
            )
        # Farmer who owns batch or Admin can cancel
        if current_user.role != "ADMIN" and booking.farmer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the booking farmer can cancel this booking")

    # 3. Check Allowed Transitions
    valid_targets = ALLOWED_TRANSITIONS.get(old_status, set())
    if target_status not in valid_targets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from '{old_status}' to '{target_status}'. Allowed: {sorted(list(valid_targets))}"
        )

    # 4. Van-only check for PICKUP_SCHEDULED
    asset = booking.asset or db.query(ColdAsset).filter_by(id=booking.asset_id).first()
    if target_status == "PICKUP_SCHEDULED" and asset.asset_type != "MOBILE":
        raise HTTPException(
            status_code=400,
            detail="PICKUP_SCHEDULED status is only valid for mobile cooling vans"
        )

    # Operator check for forward status progression
    if target_status != "CANCELLED":
        if current_user.role != "ADMIN" and asset.operator_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the operator managing this asset can update its booking progress"
            )

    # 5. Capacity Release Logic (exactly once per booking)
    # Capacity is released when moving from held status to terminal status:
    # CANCELLED or EXPIRED (from RESERVED)
    # CANCELLED or FAILED (from CONFIRMED or PICKUP_SCHEDULED)
    # FAILED (from PRODUCE_RECEIVED)
    # COMPLETED or FAILED (from IN_STORAGE)
    release_conditions = [
        (old_status == "RESERVED" and target_status in ["CANCELLED", "EXPIRED"]),
        (old_status in ["CONFIRMED", "PICKUP_SCHEDULED"] and target_status in ["CANCELLED", "FAILED"]),
        (old_status == "PRODUCE_RECEIVED" and target_status == "FAILED"),
        (old_status == "IN_STORAGE" and target_status in ["COMPLETED", "FAILED"])
    ]

    should_release_capacity = any(release_conditions)

    if should_release_capacity:
        asset.available_capacity_kg = min(
            asset.total_capacity_kg,
            round(asset.available_capacity_kg + booking.quantity_kg, 2)
        )

    # 6. Apply state change
    booking.status = target_status
    booking.status_updated_by = current_user.id

    # 7. Audit log
    log_audit_event(
        db=db,
        action=f"BOOKING_STATUS_{target_status}",
        resource_type="BOOKING",
        resource_id=booking.id,
        user_id=current_user.id,
        details={
            "old_status": old_status,
            "new_status": target_status,
            "capacity_released": should_release_capacity,
            "available_capacity_kg": asset.available_capacity_kg
        },
        ip_address=ip_address
    )

    # 8. Auto-create inventory record when produce arrives
    if target_status == "PRODUCE_RECEIVED":
        auto_create_inventory_for_booking(db=db, booking=booking, ip_address=ip_address)

    db.commit()
    db.refresh(booking)
    return booking


def check_and_expire_reservations(db: Session, now: datetime.datetime = None) -> int:
    """
    Checks for any RESERVED bookings that exceeded the 15-minute reservation window.
    Transitions them to EXPIRED and releases capacity back to the asset.
    """
    if now is None:
        now = datetime.datetime.now(timezone.utc)

    # Query active reservations where reserved_until < now
    overdue_bookings = db.query(Booking).filter(
        Booking.status == "RESERVED",
        Booking.reserved_until.isnot(None),
        Booking.reserved_until < now
    ).all()

    expired_count = 0
    for b in overdue_bookings:
        asset = b.asset or db.query(ColdAsset).filter_by(id=b.asset_id).first()
        if asset:
            asset.available_capacity_kg = min(
                asset.total_capacity_kg,
                round(asset.available_capacity_kg + b.quantity_kg, 2)
            )
        b.status = "EXPIRED"
        b.status_updated_by = "SYSTEM_EXPIRATION"
        log_audit_event(
            db=db,
            action="BOOKING_EXPIRED_AUTOMATIC",
            resource_type="BOOKING",
            resource_id=b.id,
            user_id="SYSTEM",
            details={
                "quantity_released_kg": b.quantity_kg,
                "asset_id": b.asset_id,
                "new_available_capacity_kg": asset.available_capacity_kg if asset else None
            }
        )
        expired_count += 1

    if expired_count > 0:
        db.commit()

    return expired_count
