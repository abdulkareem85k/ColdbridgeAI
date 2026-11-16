import json
import datetime
from datetime import timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user import User
from app.models.produce import ProduceBatch, SpoilageAssessment
from app.models.asset import ColdAsset
from app.schemas.sri import SriAssessmentResponse, SriPriorityQueueItem
from app.services.sri_engine import calculate_sri
from app.services.ownership_service import verify_batch_ownership
from app.services.eligibility import evaluate_asset_eligibility
from app.services.maps_service import haversine_km

router = APIRouter(prefix="/sri", tags=["Spoilage Risk Index (SRI)"])

def format_assessment_response(assessment: SpoilageAssessment) -> SriAssessmentResponse:
    reasons = json.loads(assessment.reasons) if isinstance(assessment.reasons, str) else assessment.reasons
    factors = json.loads(assessment.factors) if isinstance(assessment.factors, str) else assessment.factors
    return SriAssessmentResponse(
        id=assessment.id,
        batch_id=assessment.batch_id,
        score=assessment.score,
        risk_category=assessment.risk_category,
        reasons=reasons,
        factors=factors,
        recommended_action=assessment.recommended_action,
        rule_version=assessment.rule_version,
        disclaimer="Prototype estimate - not a validated spoilage prediction",
        created_at=assessment.created_at
    )

@router.post("/{batch_id}/calculate", response_model=SriAssessmentResponse)
def calculate_batch_sri(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate and record a Spoilage Risk Index (SRI) assessment for a produce batch.
    Stores the calculation and rule version in spoilage_assessments.
    Only the owning farmer or an Admin can calculate SRI for a batch.
    """
    batch = db.query(ProduceBatch).filter(ProduceBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produce batch not found."
        )

    verify_batch_ownership(batch, current_user)

    now_utc = datetime.datetime.now(timezone.utc)
    harvest_at = batch.harvest_at
    if harvest_at.tzinfo is None:
        harvest_at = harvest_at.replace(tzinfo=timezone.utc)

    hours_since_harvest = max(0.0, (now_utc - harvest_at).total_seconds() / 3600.0)

    try:
        sri_data = calculate_sri(
            crop_code=batch.crop_code,
            hours_since_harvest=hours_since_harvest,
            ambient_temp_c=batch.ambient_temp_c
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    assessment = SpoilageAssessment(
        batch_id=batch.id,
        score=sri_data["score"],
        risk_category=sri_data["risk_category"],
        reasons=json.dumps(sri_data["reasons"]),
        factors=json.dumps(sri_data["factors"]),
        recommended_action=sri_data["recommended_action"],
        rule_version=sri_data["rule_version"]
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return format_assessment_response(assessment)


@router.get("/priority-queue", response_model=List[SriPriorityQueueItem])
def get_priority_queue(
    limit: Optional[int] = 50,
    current_user: User = Depends(require_role("STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Returns the Spoilage Risk Index Priority Queue sorted from highest risk to lowest.
    Only Operators and Admins can access.
    Admin sees the complete queue with exact coordinates and farmer IDs.
    Operators see only relevant batches:
      (a) active matching request with bid on operator's asset,
      (b) active booking on operator's asset,
      (c) passes eligibility for operator's active assets (privacy: farmer_id hidden, coords rounded to 2 decimals).
    Unrelated farmer batches are completely excluded.
    Missing assessments are computed in a single transaction.
    """
    batches = db.query(ProduceBatch).all()
    if not batches:
        return []

    now_utc = datetime.datetime.now(timezone.utc)

    # Compute missing assessments in one transaction
    has_new_assessments = False
    for b in batches:
        latest = db.query(SpoilageAssessment)\
            .filter(SpoilageAssessment.batch_id == b.id)\
            .order_by(SpoilageAssessment.created_at.desc())\
            .first()

        if not latest:
            harvest_at = b.harvest_at.replace(tzinfo=timezone.utc) if b.harvest_at.tzinfo is None else b.harvest_at
            hours = max(0.0, (now_utc - harvest_at).total_seconds() / 3600.0)
            try:
                calc = calculate_sri(b.crop_code, hours, b.ambient_temp_c)
                new_assessment = SpoilageAssessment(
                    batch_id=b.id,
                    score=calc["score"],
                    risk_category=calc["risk_category"],
                    reasons=json.dumps(calc["reasons"]),
                    factors=json.dumps(calc["factors"]),
                    recommended_action=calc["recommended_action"],
                    rule_version=calc["rule_version"]
                )
                db.add(new_assessment)
                has_new_assessments = True
            except Exception:
                continue

    if has_new_assessments:
        db.commit()

    is_admin = current_user.role == "ADMIN"
    op_assets = []
    op_asset_ids = set()
    if not is_admin:
        op_assets = db.query(ColdAsset).filter_by(operator_id=current_user.id, is_active=True).all()
        op_asset_ids = {a.id for a in op_assets}
        if not op_assets:
            return []

    queue: List[SriPriorityQueueItem] = []

    for b in batches:
        latest_assessment = db.query(SpoilageAssessment)\
            .filter(SpoilageAssessment.batch_id == b.id)\
            .order_by(SpoilageAssessment.created_at.desc())\
            .first()

        if not latest_assessment:
            continue

        if is_admin:
            queue.append(SriPriorityQueueItem(
                batch_id=b.id,
                farmer_id=b.farmer_id,
                crop_code=b.crop_code,
                quantity_kg=b.quantity_kg,
                ambient_temp_c=b.ambient_temp_c,
                harvest_at=b.harvest_at,
                latitude=b.latitude,
                longitude=b.longitude,
                score=latest_assessment.score,
                risk_category=latest_assessment.risk_category,
                recommended_action=latest_assessment.recommended_action,
                rule_version=latest_assessment.rule_version,
                assessed_at=latest_assessment.created_at
            ))
        else:
            # Check (a): active matching request with bid on operator's asset
            has_bid = False
            if b.matching_requests:
                for mr in b.matching_requests:
                    if mr.status not in ["CANCELLED", "FAILED"]:
                        for bid in mr.bids:
                            if bid.asset_id in op_asset_ids:
                                has_bid = True
                                break
                    if has_bid:
                        break

            # Check (b): active booking on operator's asset
            has_booking = False
            if b.bookings:
                for bk in b.bookings:
                    if bk.asset_id in op_asset_ids and bk.status not in ["CANCELLED", "FAILED", "EXPIRED"]:
                        has_booking = True
                        break

            if has_bid or has_booking:
                # Relevant via existing relationship -> full transparency
                queue.append(SriPriorityQueueItem(
                    batch_id=b.id,
                    farmer_id=b.farmer_id,
                    crop_code=b.crop_code,
                    quantity_kg=b.quantity_kg,
                    ambient_temp_c=b.ambient_temp_c,
                    harvest_at=b.harvest_at,
                    latitude=b.latitude,
                    longitude=b.longitude,
                    score=latest_assessment.score,
                    risk_category=latest_assessment.risk_category,
                    recommended_action=latest_assessment.recommended_action,
                    rule_version=latest_assessment.rule_version,
                    assessed_at=latest_assessment.created_at
                ))
            else:
                # Check (c): passes eligibility rules for at least one active operator asset
                batch_lat = b.latitude or 19.9975
                batch_lng = b.longitude or 73.7898
                is_eligible = False
                for asset in op_assets:
                    dist_km = haversine_km((batch_lat, batch_lng), (asset.latitude, asset.longitude))
                    eligible, _, _ = evaluate_asset_eligibility(
                        asset=asset,
                        crop_code=b.crop_code,
                        requested_quantity_kg=b.quantity_kg,
                        distance_km=dist_km,
                        now=now_utc
                    )
                    if eligible:
                        is_eligible = True
                        break

                if is_eligible:
                    # Discovery only: hide farmer_id, round coordinates to 2 decimals (~1.1 km precision)
                    queue.append(SriPriorityQueueItem(
                        batch_id=b.id,
                        farmer_id=None,
                        crop_code=b.crop_code,
                        quantity_kg=b.quantity_kg,
                        ambient_temp_c=b.ambient_temp_c,
                        harvest_at=b.harvest_at,
                        latitude=round(b.latitude, 2) if b.latitude is not None else 0.0,
                        longitude=round(b.longitude, 2) if b.longitude is not None else 0.0,
                        score=latest_assessment.score,
                        risk_category=latest_assessment.risk_category,
                        recommended_action=latest_assessment.recommended_action,
                        rule_version=latest_assessment.rule_version,
                        assessed_at=latest_assessment.created_at
                    ))

    # Sort descending by SRI score (Highest risk first)
    queue.sort(key=lambda x: x.score, reverse=True)

    # Assign priority rank
    for idx, item in enumerate(queue, start=1):
        item.priority_rank = idx

    # Apply limit
    if limit and limit > 0:
        queue = queue[:limit]

    return queue


@router.get("/{batch_id}", response_model=SriAssessmentResponse)
def get_batch_sri(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the latest SRI assessment for a specific produce batch."""
    batch = db.query(ProduceBatch).filter(ProduceBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produce batch not found."
        )

    verify_batch_ownership(batch, current_user)

    assessment = db.query(SpoilageAssessment)\
        .filter(SpoilageAssessment.batch_id == batch_id)\
        .order_by(SpoilageAssessment.created_at.desc())\
        .first()

    if not assessment:
        # Auto-compute if missing
        return calculate_batch_sri(batch_id, current_user, db)

    return format_assessment_response(assessment)
