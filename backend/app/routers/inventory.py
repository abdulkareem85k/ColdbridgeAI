from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.inventory import Inventory, Alert
from app.models.asset import ColdAsset
from app.schemas.inventory import InventoryResponse, AlertResponse
from app.core.dependencies import get_current_user
from app.services.inventory_service import check_and_create_expiry_alerts

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("", response_model=List[InventoryResponse])
def get_inventory_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List inventory records accessible to the authenticated user.
    Operators see inventory in their facilities; Farmers see their stored produce; Admins see all.
    """
    # Trigger check for nearing-expiry alerts
    check_and_create_expiry_alerts(db)

    query = db.query(Inventory)
    if current_user.role == "ADMIN":
        items = query.all()
    elif current_user.role in ["STATIC_OPERATOR", "VAN_OPERATOR"]:
        # Subquery for operator assets
        asset_ids = [a.id for a in db.query(ColdAsset).filter_by(operator_id=current_user.id).all()]
        items = query.filter(Inventory.asset_id.in_(asset_ids)).all()
    elif current_user.role == "FARMER":
        items = query.filter_by(farmer_id=current_user.id).all()
    else:
        items = []

    res = []
    for item in items:
        resp = InventoryResponse(
            id=item.id,
            batch_id=item.batch_id,
            booking_id=item.booking_id,
            asset_id=item.asset_id,
            farmer_id=item.farmer_id,
            initial_quantity_kg=item.initial_quantity_kg,
            current_quantity_kg=item.current_quantity_kg,
            storage_location=item.storage_location,
            received_at=item.received_at,
            expiry_risk_date=item.expiry_risk_date,
            status=item.status,
            quality_notes=item.quality_notes,
            created_at=item.created_at,
            updated_at=item.updated_at,
            crop_code=item.batch.crop_code if item.batch else None,
            farmer_name=item.farmer.full_name if item.farmer else None,
            asset_name=item.asset.name if item.asset else None
        )
        res.append(resp)
    return res


@router.get("/alerts", response_model=List[AlertResponse])
def get_user_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notifications & surplus alerts for current user.
    """
    check_and_create_expiry_alerts(db)
    alerts = db.query(Alert).filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).all()
    return alerts


@router.post("/alerts/{alert_id}/read")
def mark_alert_as_read(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter_by(id=alert_id, user_id=current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"message": "Alert marked as read"}
