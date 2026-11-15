from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, require_role
from app.models.user import User, FarmerProfile, OperatorProfile
from app.schemas.user import (
    FarmerProfileSchema,
    FarmerProfileResponse,
    OperatorProfileSchema,
    OperatorProfileResponse
)

router = APIRouter(prefix="/profiles", tags=["Profiles"])

@router.get("/farmer", response_model=FarmerProfileResponse)
def get_farmer_profile(
    current_user: User = Depends(require_role("FARMER", "ADMIN")),
    db: Session = Depends(get_db)
):
    """Retrieve the farmer profile for the logged-in user."""
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
    if not profile:
        # Create profile if not yet created
        profile = FarmerProfile(
            user_id=current_user.id,
            farm_name=f"{current_user.full_name}'s Farm",
            district="Nashik",
            state="Maharashtra"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("/farmer", response_model=FarmerProfileResponse)
def update_farmer_profile(
    req: FarmerProfileSchema,
    current_user: User = Depends(require_role("FARMER", "ADMIN")),
    db: Session = Depends(get_db)
):
    """Update the farmer profile for the logged-in user."""
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
    if not profile:
        profile = FarmerProfile(user_id=current_user.id, **req.model_dump())
        db.add(profile)
    else:
        for k, v in req.model_dump().items():
            setattr(profile, k, v)
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/operator", response_model=OperatorProfileResponse)
def get_operator_profile(
    current_user: User = Depends(require_role("STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN")),
    db: Session = Depends(get_db)
):
    """Retrieve the operator profile for the logged-in user."""
    profile = db.query(OperatorProfile).filter(OperatorProfile.user_id == current_user.id).first()
    if not profile:
        profile = OperatorProfile(
            user_id=current_user.id,
            business_name=f"{current_user.full_name}'s Cooling Services",
            contact_phone=current_user.phone,
            district="Pune",
            state="Maharashtra"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("/operator", response_model=OperatorProfileResponse)
def update_operator_profile(
    req: OperatorProfileSchema,
    current_user: User = Depends(require_role("STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN")),
    db: Session = Depends(get_db)
):
    """Update the operator profile for the logged-in user."""
    profile = db.query(OperatorProfile).filter(OperatorProfile.user_id == current_user.id).first()
    if not profile:
        profile = OperatorProfile(user_id=current_user.id, **req.model_dump())
        db.add(profile)
    else:
        for k, v in req.model_dump().items():
            setattr(profile, k, v)
    db.commit()
    db.refresh(profile)
    return profile
