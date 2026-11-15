from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class FarmerProfileSchema(BaseModel):
    farm_name: str = Field(..., min_length=2, max_length=255)
    district: str = Field(..., min_length=2, max_length=100)
    state: str = Field(default="Maharashtra", max_length=100)
    default_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    default_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)

    model_config = ConfigDict(from_attributes=True)

class FarmerProfileResponse(FarmerProfileSchema):
    id: str
    user_id: str

class OperatorProfileSchema(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    district: str = Field(..., min_length=2, max_length=100)
    state: str = Field(default="Maharashtra", max_length=100)

    model_config = ConfigDict(from_attributes=True)

class OperatorProfileResponse(OperatorProfileSchema):
    id: str
    user_id: str
