import datetime
from datetime import timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.inventory import Inventory, Alert
from app.models.booking import Booking
from app.models.produce import ProduceBatch
from app.models.asset import ColdAsset
from app.models.user import User
from app.services.audit_service import log_audit_event

# Shelf life in days under cold chain storage (indicative rule-based estimates)
COLD_STORAGE_SHELF_LIFE_DAYS = {
    "mango": 21,
    "tomato": 14,
    "grapes": 30,
    "onion": 90,
    "cashew_apple": 3,
    "strawberry": 7,
    "pomegranate": 45,
    "potato": 120,
    "default": 14
}

def auto_create_inventory_for_booking(db: Session, booking: Booking, ip_address: Optional[str] = None) -> Inventory:
    """
    Atomically creates an inventory record when a booking transitions to PRODUCE_RECEIVED.
    Ensures idempotency (does not duplicate if already exists).
    """
    existing = db.query(Inventory).filter_by(booking_id=booking.id).first()
    if existing:
        return existing

    batch = booking.batch or db.query(ProduceBatch).filter_by(id=booking.batch_id).first()
    crop = batch.crop_code if batch else "default"
    shelf_life_days = COLD_STORAGE_SHELF_LIFE_DAYS.get(crop.lower(), COLD_STORAGE_SHELF_LIFE_DAYS["default"])

    now = datetime.datetime.now(timezone.utc)
    harvest_time = batch.harvest_at if (batch and batch.harvest_at) else now
    expiry_risk_date = harvest_time + timedelta(days=shelf_life_days)

    inventory = Inventory(
        batch_id=booking.batch_id,
        booking_id=booking.id,
        asset_id=booking.asset_id,
        farmer_id=booking.farmer_id,
        initial_quantity_kg=booking.quantity_kg,
        current_quantity_kg=booking.quantity_kg,
        storage_location="Main Cold Bay A-1",
        received_at=now,
        expiry_risk_date=expiry_risk_date,
        status="STORED",
        quality_notes=f"Produce received into cold storage. Initial inspection: Satisfactory."
    )
    db.add(inventory)
    db.flush()

    # Log audit event for inventory creation
    log_audit_event(
        db=db,
        action="INVENTORY_CREATED",
        resource_type="INVENTORY",
        resource_id=inventory.id,
        user_id=booking.status_updated_by or booking.farmer_id,
        details={
            "booking_id": booking.id,
            "batch_id": booking.batch_id,
            "asset_id": booking.asset_id,
            "quantity_kg": booking.quantity_kg,
            "expiry_risk_date": expiry_risk_date.isoformat()
        },
        ip_address=ip_address
    )

    return inventory


def update_inventory_quantity(
    db: Session,
    inventory_id: str,
    quantity_delta_kg: float,
    reason: str,
    user_id: str,
    ip_address: Optional[str] = None
) -> Inventory:
    """
    Traceable modification of stored inventory quantity (e.g. dispatch, wastage, partial sale).
    Maintains full audit trail.
    """
    inventory = db.query(Inventory).filter_by(id=inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    new_quantity = inventory.current_quantity_kg + quantity_delta_kg
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Cannot reduce inventory quantity below zero")

    old_qty = inventory.current_quantity_kg
    inventory.current_quantity_kg = round(new_quantity, 2)
    if inventory.current_quantity_kg == 0:
        inventory.status = "DISPATCHED"

    log_audit_event(
        db=db,
        action="INVENTORY_QUANTITY_ADJUSTED",
        resource_type="INVENTORY",
        resource_id=inventory.id,
        user_id=user_id,
        details={
            "previous_quantity_kg": old_qty,
            "quantity_delta_kg": quantity_delta_kg,
            "new_quantity_kg": inventory.current_quantity_kg,
            "reason": reason
        },
        ip_address=ip_address
    )
    db.commit()
    db.refresh(inventory)
    return inventory


def check_and_create_expiry_alerts(db: Session, threshold_days: int = 3) -> List[Alert]:
    """
    Checks stored inventory nearing expiry date and creates operator & farmer alerts.
    """
    now = datetime.datetime.now(timezone.utc)
    target_cutoff = now + timedelta(days=threshold_days)

    expiring_items = db.query(Inventory).filter(
        Inventory.status.in_(["STORED", "NEAR_EXPIRY"]),
        Inventory.current_quantity_kg > 0,
        Inventory.expiry_risk_date <= target_cutoff
    ).all()

    created_alerts = []
    for item in expiring_items:
        item.status = "NEAR_EXPIRY"
        
        # Check if alert already created recently
        existing_alert = db.query(Alert).filter(
            Alert.inventory_id == item.id,
            Alert.alert_type == "NEAR_EXPIRY_WARNING"
        ).first()

        if not existing_alert:
            asset = item.asset
            operator_id = asset.operator_id if asset else None
            alert_msg = (
                f"Surplus Alert: Inventory item {item.id[:8]} ({item.current_quantity_kg} kg) "
                f"reaches estimated shelf-life limit by {item.expiry_risk_date.strftime('%Y-%m-%d')}. "
                f"Review quality and consider listing on surplus marketplace. "
                f"Note: Time alone does not prove food safety; operator visual inspection is required."
            )
            
            # Create alert for operator
            if operator_id:
                alert = Alert(
                    user_id=operator_id,
                    asset_id=item.asset_id,
                    batch_id=item.batch_id,
                    inventory_id=item.id,
                    alert_type="NEAR_EXPIRY_WARNING",
                    severity="WARNING",
                    message=alert_msg
                )
                db.add(alert)
                created_alerts.append(alert)

    if created_alerts:
        db.commit()

    return created_alerts
