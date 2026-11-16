import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class SriAssessmentResponse(BaseModel):
    id: str
    batch_id: str
    score: float
    risk_category: str
    reasons: List[str]
    factors: Dict[str, Any]
    recommended_action: str
    rule_version: str
    disclaimer: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class SriPriorityQueueItem(BaseModel):
    priority_rank: Optional[int] = None
    batch_id: str
    farmer_id: Optional[str] = None
    crop_code: str
    quantity_kg: float
    ambient_temp_c: float
    harvest_at: datetime.datetime
    latitude: float
    longitude: float
    score: float
    risk_category: str
    recommended_action: str
    rule_version: str
    assessed_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
