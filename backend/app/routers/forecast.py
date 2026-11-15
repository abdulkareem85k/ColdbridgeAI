from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.models.user import User
from app.schemas.forecast import DemandForecastResponse
from app.core.dependencies import get_current_user
from app.services import forecast_service

router = APIRouter(prefix="/forecast", tags=["forecast"])

@router.get("", response_model=List[DemandForecastResponse])
def get_demand_forecasts(
    crop_code: Optional[str] = Query(None, description="Crop filter"),
    district: Optional[str] = Query(None, description="District filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Baseline demand forecasts for Maharashtra districts and crops.
    PROTOTYPE HONESTY NOTE:
    Rule-based seasonal estimate based on historical mandi trends.
    NOT a trained machine learning model; NO confidence percentages implied.
    """
    forecasts = forecast_service.get_forecasts(db=db, crop_code=crop_code, district=district)
    return forecasts
