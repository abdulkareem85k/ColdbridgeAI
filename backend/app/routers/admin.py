"""
ColdBridge AI - Admin & Simulation Controls Router (M8 Part A)

Provides administrative simulation controls and metrics:
- Demo dataset reset
- Van solar reliability simulation toggle/slider
- Clock advancement simulation
- Temperature sensor simulation
- System overview metrics and audit trail
"""

import datetime
from datetime import timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.asset import ColdAsset, MobileAssetDetail, StaticAssetDetail
from app.models.produce import ProduceBatch
from app.models.matching import MatchingRequest, Bid
from app.models.booking import Booking
from app.models.audit import AuditLog
from app.seed.demo_data import seed_demo_data
from app.services.audit_service import log_audit_event
from app.services.solar_adjustment import clamp_reliability

router = APIRouter(prefix="/admin", tags=["Admin & Simulation"])


class SolarReliabilityUpdate(BaseModel):
    solar_reliability: float = Field(..., ge=0.0, le=1.0, description="Simulation input for solar reliability factor (0.0 to 1.0)")


class TemperatureUpdate(BaseModel):
    ambient_temp_c: float = Field(..., description="Simulated temperature in Celsius")


class AdvanceClockRequest(BaseModel):
    hours: int = Field(default=2, ge=1, le=168, description="Simulated hours to advance the clock")


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Administrative privileges required")
    return current_user


@router.post("/reset-demo-data")
def reset_demo_database(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Resets the database to the deterministic Maharashtra demo dataset.
    """
    seed_demo_data(db)

    log_audit_event(
        db=db,
        action="RESET_DEMO_DATA",
        resource_type="SYSTEM",
        resource_id="ALL",
        user_id=admin.id,
        details={"status": "DEMO_DATA_RESET_SUCCESS"},
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return {
        "status": "success",
        "message": "Demo data reset successfully to deterministic Maharashtra state",
        "data_source": "SIMULATED",
        "data_status": "FRESH"
    }


@router.patch("/assets/{id}/solar-reliability")
def update_solar_reliability(
    id: str,
    payload: SolarReliabilityUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Updates a mobile van's solar reliability factor (simulation input).
    PROTOTYPE NOTE: This is a simulation input, NOT real battery/hardware telemetry.
    """
    asset = db.query(ColdAsset).filter_by(id=id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.asset_type != "MOBILE":
        raise HTTPException(status_code=400, detail="Solar reliability is only applicable to mobile cooling vans")

    mobile_detail = asset.mobile_detail
    if not mobile_detail:
        raise HTTPException(status_code=404, detail="Mobile detail not found for asset")

    old_factor = mobile_detail.solar_reliability
    new_factor = clamp_reliability(payload.solar_reliability)
    mobile_detail.solar_reliability = new_factor

    log_audit_event(
        db=db,
        action="UPDATE_SOLAR_RELIABILITY_SIMULATION",
        resource_type="COLD_ASSET",
        resource_id=asset.id,
        user_id=admin.id,
        details={
            "old_solar_reliability": old_factor,
            "new_solar_reliability": new_factor,
            "note": "SIMULATED input change for what-if testing"
        },
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return {
        "asset_id": asset.id,
        "asset_name": asset.name,
        "old_solar_reliability": old_factor,
        "solar_reliability": new_factor,
        "effective_capacity_kg": round(asset.available_capacity_kg * new_factor, 2),
        "data_source": "SIMULATED",
        "data_status": "FRESH"
    }


@router.patch("/assets/{id}/simulate-temperature")
def simulate_temperature_reading(
    id: str,
    payload: TemperatureUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Simulates a temperature update for an asset facility/van.
    """
    asset = db.query(ColdAsset).filter_by(id=id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    log_audit_event(
        db=db,
        action="SIMULATE_TEMPERATURE_UPDATE",
        resource_type="COLD_ASSET",
        resource_id=asset.id,
        user_id=admin.id,
        details={"simulated_ambient_temp_c": payload.ambient_temp_c},
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return {
        "asset_id": asset.id,
        "simulated_temp_c": payload.ambient_temp_c,
        "data_source": "SIMULATED",
        "data_status": "FRESH"
    }


@router.post("/advance-clock")
def advance_simulated_clock(
    payload: AdvanceClockRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Simulates clock advancement by shifting produce harvest timestamps back,
    simulating aging produce and triggering higher SRI urgency.
    """
    batches = db.query(ProduceBatch).all()
    delta = timedelta(hours=payload.hours)
    for b in batches:
        if b.harvest_at:
            b.harvest_at = b.harvest_at - delta

    log_audit_event(
        db=db,
        action="ADVANCE_SIMULATED_CLOCK",
        resource_type="SYSTEM",
        resource_id="TIME",
        user_id=admin.id,
        details={"hours_advanced": payload.hours},
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return {
        "status": "success",
        "hours_advanced": payload.hours,
        "message": f"Simulated clock advanced by {payload.hours} hours; batch harvest times shifted",
        "data_source": "SIMULATED"
    }


@router.get("/stats")
def get_system_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    System metrics for Admin Dashboard.
    """
    total_farmers = db.query(User).filter_by(role="FARMER").count()
    total_operators = db.query(User).filter(User.role.in_(["STATIC_OPERATOR", "VAN_OPERATOR"])).count()
    static_rooms = db.query(ColdAsset).filter_by(asset_type="STATIC").count()
    mobile_vans = db.query(ColdAsset).filter_by(asset_type="MOBILE").count()
    total_batches = db.query(ProduceBatch).count()
    total_matching_requests = db.query(MatchingRequest).count()
    active_bookings = db.query(Booking).filter(Booking.status.in_(["RESERVED", "CONFIRMED", "PICKUP_SCHEDULED", "PRODUCE_RECEIVED", "IN_STORAGE"])).count()
    completed_bookings = db.query(Booking).filter_by(status="COMPLETED").count()

    # Recent Audit Logs (up to 50)
    recent_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(50).all()
    logs_data = []
    for l in recent_logs:
        logs_data.append({
            "id": l.id,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "user_id": l.user_id,
            "details": l.details,
            "created_at": l.created_at
        })

    return {
        "counts": {
            "farmers": total_farmers,
            "operators": total_operators,
            "static_rooms": static_rooms,
            "mobile_vans": mobile_vans,
            "produce_batches": total_batches,
            "matching_requests": total_matching_requests,
            "active_bookings": active_bookings,
            "completed_bookings": completed_bookings
        },
        "recent_audit_logs": logs_data,
        "data_source": "SIMULATED",
        "data_status": "FRESH"
    }
