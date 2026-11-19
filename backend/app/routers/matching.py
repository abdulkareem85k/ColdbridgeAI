"""
ColdBridge AI - Matching Router (M5 & M6 Allocation)

Provides endpoints to create matching requests, receive bids,
score and rank offers with reverse-auction logic, and execute
safe capacity allocation.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.produce import ProduceBatch
from app.models.matching import MatchingRequest, Bid
from app.models.asset import ColdAsset
from app.schemas.matching import (
    MatchingRequestCreate,
    MatchingRequestResponse,
    BidCreate,
    BidResponse,
    RankRequest,
    MatchingRankResponse
)
from app.schemas.booking import AllocateOfferRequest, BookingResponse
from app.services.matching_engine import run_cross_asset_matching
from app.services.booking_service import allocate_offer_transaction
from app.services.audit_service import log_audit_event
from app.services.ownership_service import verify_matching_request_access

router = APIRouter(prefix="/matching", tags=["Matching"])


@router.post("/requests", response_model=MatchingRequestResponse, status_code=status.HTTP_201_CREATED)
def create_matching_request(
    payload: MatchingRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Farmer creates a cross-asset matching request for an existing produce batch.
    """
    batch = db.query(ProduceBatch).filter_by(id=payload.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Produce batch not found")

    # Ownership check
    if current_user.role != "ADMIN" and batch.farmer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only request matching for your own produce batches")

    if payload.requested_quantity_kg > batch.quantity_kg:
        raise HTTPException(
            status_code=400,
            detail=f"Requested quantity ({payload.requested_quantity_kg} kg) exceeds batch total ({batch.quantity_kg} kg)"
        )

    matching_req = MatchingRequest(
        batch_id=batch.id,
        farmer_id=current_user.id,
        requested_quantity_kg=payload.requested_quantity_kg,
        status="PENDING"
    )
    db.add(matching_req)
    db.commit()
    db.refresh(matching_req)

    log_audit_event(
        db=db,
        action="CREATE_MATCHING_REQUEST",
        resource_type="MATCHING_REQUEST",
        resource_id=matching_req.id,
        user_id=current_user.id,
        details={"batch_id": batch.id, "quantity_kg": payload.requested_quantity_kg},
        ip_address=request.client.host if request.client else None
    )

    return matching_req


@router.get("/open-requests")
def list_open_matching_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN"))
):
    """
    List pending matching requests relevant to the calling operator's assets.
    Enforces privacy by hiding farmer personal contact info and rounding coordinates.
    """
    # 1. Fetch pending requests
    pending_reqs = db.query(MatchingRequest).filter(MatchingRequest.status == "PENDING").order_by(MatchingRequest.created_at.desc()).all()

    # 2. Get calling operator's active assets
    op_query = db.query(ColdAsset).filter(ColdAsset.is_active == True)
    if current_user.role == "STATIC_OPERATOR":
        op_query = op_query.filter(ColdAsset.operator_id == current_user.id, ColdAsset.asset_type == "STATIC")
    elif current_user.role == "VAN_OPERATOR":
        op_query = op_query.filter(ColdAsset.operator_id == current_user.id, ColdAsset.asset_type == "MOBILE")
    op_assets = op_query.all()
    op_asset_ids = {a.id for a in op_assets}

    results = []
    for req in pending_reqs:
        batch = req.batch or db.query(ProduceBatch).filter_by(id=req.batch_id).first()
        if not batch:
            continue

        # Check existing bids for this request belonging to this operator
        existing_bids = (
            db.query(Bid)
            .filter(Bid.request_id == req.id, Bid.asset_id.in_(op_asset_ids))
            .all()
        ) if op_asset_ids else []

        bid_info = None
        if existing_bids:
            # Prefer active non-expired bid
            eb = next((b for b in existing_bids if not b.is_expired), existing_bids[0])
            eb_asset = next((a for a in op_assets if a.id == eb.asset_id), None)
            bid_info = {
                "id": eb.id,
                "asset_id": eb.asset_id,
                "asset_name": eb_asset.name if eb_asset else "Operator Asset",
                "price_total": eb.price_total,
                "eta_minutes": eb.eta_minutes,
                "offered_capacity_kg": eb.offered_capacity_kg,
                "data_source": eb.data_source,
                "is_operator_submitted": (eb.data_source == "LIVE")
            }

        results.append({
            "id": req.id,
            "batch_id": req.batch_id,
            "crop_code": batch.crop_code,
            "requested_quantity_kg": req.requested_quantity_kg,
            "approx_latitude": round(batch.latitude, 2) if batch.latitude else None,
            "approx_longitude": round(batch.longitude, 2) if batch.longitude else None,
            "status": req.status,
            "created_at": req.created_at,
            "existing_bid": bid_info
        })

    return results


@router.post("/requests/{id}/bids", response_model=BidResponse, status_code=status.HTTP_201_CREATED)
def submit_bid(
    id: str,
    payload: BidCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits an offer/bid for a matching request.
    Can be submitted by the asset operator or admin.
    """
    if current_user.role not in ["STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only cooling asset operators and administrators can submit bids."
        )

    matching_req = db.query(MatchingRequest).filter_by(id=id).first()
    if not matching_req:
        raise HTTPException(status_code=404, detail="Matching request not found")

    asset = db.query(ColdAsset).filter_by(id=payload.asset_id).first()
    if not asset or not asset.is_active:
        raise HTTPException(status_code=404, detail="Cold asset not found or inactive")

    # Operator ownership check
    if current_user.role != "ADMIN" and asset.operator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only submit bids for your own cold assets")

    # Asset type check for operator role
    if current_user.role == "STATIC_OPERATOR" and asset.asset_type != "STATIC":
        raise HTTPException(status_code=403, detail="Static operators can only bid static storage rooms")
    if current_user.role == "VAN_OPERATOR" and asset.asset_type != "MOBILE":
        raise HTTPException(status_code=403, detail="Van operators can only bid mobile solar vans")

    # Capacity check
    if payload.offered_capacity_kg > asset.available_capacity_kg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Offered capacity ({payload.offered_capacity_kg} kg) exceeds available asset capacity ({asset.available_capacity_kg} kg)"
        )

    bid = Bid(
        request_id=matching_req.id,
        asset_id=asset.id,
        offered_capacity_kg=payload.offered_capacity_kg,
        price_total=payload.price_total,
        eta_minutes=payload.eta_minutes,
        valid_until=payload.valid_until,
        note=payload.note,
        data_source="LIVE",
        is_accepted=False,
        is_expired=False
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)

    log_audit_event(
        db=db,
        action="SUBMIT_BID",
        resource_type="BID",
        resource_id=bid.id,
        user_id=current_user.id,
        details={"asset_id": asset.id, "price_total": payload.price_total},
        ip_address=request.client.host if request.client else None
    )

    return bid


@router.post("/requests/{id}/rank", response_model=MatchingRankResponse)
def rank_matching_offers(
    id: str,
    payload: Optional[RankRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Scores and ranks all eligible offers for this matching request using
    multi-criteria reverse auction scoring, OpenStreetMap routing, and 3-way baseline comparisons.
    Supports solar reliability overrides for simulation what-if testing.
    """
    matching_req = db.query(MatchingRequest).filter_by(id=id).first()
    if not matching_req:
        raise HTTPException(status_code=404, detail="Matching request not found")

    verify_matching_request_access(db, matching_req, current_user)

    solar_overrides = payload.solar_overrides if payload else None

    result = run_cross_asset_matching(
        db=db,
        request=matching_req,
        solar_overrides=solar_overrides,
        persist_bids=True
    )
    db.commit()
    return result


@router.get("/requests/{id}")
def get_matching_request(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch matching request with all associated bids and live ranking.
    Read-only: does not persist new bids.
    """
    matching_req = db.query(MatchingRequest).filter_by(id=id).first()
    if not matching_req:
        raise HTTPException(status_code=404, detail="Matching request not found")

    verify_matching_request_access(db, matching_req, current_user)

    # Run ranking over current state in read-only mode
    ranking = run_cross_asset_matching(db=db, request=matching_req, persist_bids=False)
    return {
        "matching_request": {
            "id": matching_req.id,
            "batch_id": matching_req.batch_id,
            "farmer_id": matching_req.farmer_id,
            "requested_quantity_kg": matching_req.requested_quantity_kg,
            "status": matching_req.status,
            "created_at": matching_req.created_at,
            "updated_at": matching_req.updated_at
        },
        "ranking": ranking
    }


@router.post("/requests/{id}/allocate", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def allocate_matching_offer(
    id: str,
    payload: AllocateOfferRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accept an offer on a matching request.
    Inside ONE database transaction: locks asset capacity, reserves capacity,
    creates RESERVED booking (15 min window), and expires other bids.
    """
    booking = allocate_offer_transaction(
        db=db,
        request_id=id,
        bid_id=payload.bid_id,
        current_user=current_user,
        days_estimated=payload.days_estimated,
        ip_address=request.client.host if request.client else None
    )
    return booking
