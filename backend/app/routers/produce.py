from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user import User
from app.models.produce import ProduceBatch
from app.schemas.produce import ProduceBatchCreate, ProduceBatchResponse, ProduceBatchListResponse
from app.services.ownership_service import verify_batch_ownership

router = APIRouter(prefix="/produce", tags=["Produce Batches"])

@router.post("/batches", response_model=ProduceBatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(
    req: ProduceBatchCreate,
    current_user: User = Depends(require_role("FARMER", "ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Create a new produce batch (Farmer only).
    Validates crop_code, positive quantity, valid coordinates, harvest_at not in future.
    """
    batch = ProduceBatch(
        farmer_id=current_user.id,
        crop_code=req.crop_code.lower().strip(),
        quantity_kg=req.quantity_kg,
        harvest_at=req.harvest_at,
        ambient_temp_c=req.ambient_temp_c,
        latitude=req.latitude,
        longitude=req.longitude,
        notes=req.notes,
        data_source="LIVE"  # User-created in app
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch

@router.get("/batches", response_model=ProduceBatchListResponse)
def list_batches(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List produce batches with pagination.
    Farmers see only their batches; Admins see all batches.
    """
    query = db.query(ProduceBatch)
    if current_user.role == "FARMER":
        query = query.filter(ProduceBatch.farmer_id == current_user.id)
    elif current_user.role != "ADMIN":
        # Operators / Buyers cannot see arbitrary farmer batches without an allocation
        query = query.filter(ProduceBatch.farmer_id == current_user.id)

    total = query.count()
    items = query.order_by(ProduceBatch.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": items,
        "skip": skip,
        "limit": limit
    }

@router.get("/batches/{batch_id}", response_model=ProduceBatchResponse)
def get_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve single produce batch by ID.
    Enforces strict ownership check: only the owning farmer or an Admin can view.
    """
    batch = db.query(ProduceBatch).filter(ProduceBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produce batch not found."
        )

    verify_batch_ownership(batch, current_user)
    return batch
