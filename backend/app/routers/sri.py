import json
import datetime
from datetime import timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user import User
from app.models.produce import ProduceBatch, SpoilageAssessment
from app.schemas.sri import SriAssessmentResponse, SriPriorityQueueItem
from app.services.sri_engine import calculate_sri

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
    """
    batch = db.query(ProduceBatch).filter(ProduceBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produce batch not found."
        )

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the Spoilage Risk Index Priority Queue sorted from highest risk to lowest.
    Operators and Admins use this to allocate cooling vans to high-urgency farmgates.
    """
    # Fetch all batches
    batches = db.query(ProduceBatch).all()
    queue: List[SriPriorityQueueItem] = []

    for b in batches:
        # Get latest assessment or compute default
        latest_assessment = db.query(SpoilageAssessment)\
            .filter(SpoilageAssessment.batch_id == b.id)\
            .order_by(SpoilageAssessment.created_at.desc())\
            .first()

        if not latest_assessment:
            # Generate assessment
            now_utc = datetime.datetime.now(timezone.utc)
            harvest_at = b.harvest_at.replace(tzinfo=timezone.utc) if b.harvest_at.tzinfo is None else b.harvest_at
            hours = max(0.0, (now_utc - harvest_at).total_seconds() / 3600.0)
            try:
                calc = calculate_sri(b.crop_code, hours, b.ambient_temp_c)
                latest_assessment = SpoilageAssessment(
                    batch_id=b.id,
                    score=calc["score"],
                    risk_category=calc["risk_category"],
                    reasons=json.dumps(calc["reasons"]),
                    factors=json.dumps(calc["factors"]),
                    recommended_action=calc["recommended_action"],
                    rule_version=calc["rule_version"]
                )
                db.add(latest_assessment)
                db.commit()
                db.refresh(latest_assessment)
            except Exception:
                continue

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

    # Sort descending by SRI score (Highest risk first)
    queue.sort(key=lambda x: x.score, reverse=True)
    return queue

@router.get("/{batch_id}", response_model=SriAssessmentResponse)
def get_batch_sri(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the latest SRI assessment for a specific produce batch."""
    assessment = db.query(SpoilageAssessment)\
        .filter(SpoilageAssessment.batch_id == batch_id)\
        .order_by(SpoilageAssessment.created_at.desc())\
        .first()

    if not assessment:
        # Auto-compute if missing
        return calculate_batch_sri(batch_id, current_user, db)

    return format_assessment_response(assessment)
