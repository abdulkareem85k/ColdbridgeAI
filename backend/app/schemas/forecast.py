from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class DemandForecastResponse(BaseModel):
    id: str
    crop_code: str
    district: str
    horizon_days: int
    estimated_demand_kg: float
    price_trend: str
    expected_price_inr_kg: float
    forecast_source: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    data_source: str = "SIMULATED"
    data_status: str = "FRESH"

    model_config = ConfigDict(from_attributes=True)
