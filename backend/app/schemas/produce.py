import datetime
from datetime import timezone
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

class ProduceBatchCreate(BaseModel):
    crop_code: str = Field(..., min_length=2, max_length=100)
    quantity_kg: float = Field(..., gt=0.0, le=100000.0, description="Quantity in kg, must be greater than 0")
    harvest_at: datetime.datetime = Field(..., description="Harvest timestamp (UTC)")
    ambient_temp_c: float = Field(..., ge=-20.0, le=65.0, description="Ambient temperature in degrees C")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("harvest_at")
    @classmethod
    def validate_harvest_not_future(cls, v: datetime.datetime) -> datetime.datetime:
        now_utc = datetime.datetime.now(timezone.utc)
        # Ensure UTC timezone awareness
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        # Allow 5 minutes clock drift tolerance
        if v > now_utc + datetime.timedelta(minutes=5):
            raise ValueError("Harvest time cannot be in the future")
        return v

class ProduceBatchResponse(BaseModel):
    id: str
    farmer_id: str
    crop_code: str
    quantity_kg: float
    harvest_at: datetime.datetime
    ambient_temp_c: float
    latitude: float
    longitude: float
    notes: Optional[str] = None
    data_source: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class ProduceBatchListResponse(BaseModel):
    total: int
    items: List[ProduceBatchResponse]
    skip: int
    limit: int
