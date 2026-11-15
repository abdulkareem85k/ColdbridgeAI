import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict

class StaticDetailSchema(BaseModel):
    supported_crops: str = Field(..., description="Comma separated crop names or codes")
    min_temperature_c: float = Field(..., ge=-40.0, le=30.0)
    max_temperature_c: float = Field(..., ge=-40.0, le=40.0)
    address: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_temp_range(self):
        if self.min_temperature_c > self.max_temperature_c:
            raise ValueError("min_temperature_c cannot exceed max_temperature_c")
        return self

    model_config = ConfigDict(from_attributes=True)

class MobileDetailSchema(BaseModel):
    vehicle_ref: str = Field(..., min_length=2, max_length=100)
    service_radius_km: float = Field(..., gt=0.0, le=500.0)
    solar_reliability: float = Field(0.9, ge=0.0, le=1.0, description="Simulation input parameter 0.0 to 1.0")
    last_location_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ColdAssetCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    asset_type: Literal["STATIC", "MOBILE"]
    total_capacity_kg: float = Field(..., gt=0.0, le=500000.0)
    available_capacity_kg: Optional[float] = None
    price_per_kg_per_day: float = Field(..., gt=0.0, le=1000.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    static_detail: Optional[StaticDetailSchema] = None
    mobile_detail: Optional[MobileDetailSchema] = None

    @model_validator(mode="after")
    def validate_capacities_and_details(self):
        if self.available_capacity_kg is None:
            self.available_capacity_kg = self.total_capacity_kg
        if self.available_capacity_kg > self.total_capacity_kg:
            raise ValueError("available_capacity_kg cannot exceed total_capacity_kg")
        if self.available_capacity_kg < 0:
            raise ValueError("available_capacity_kg cannot be negative")

        if self.asset_type == "STATIC" and self.static_detail is None:
            raise ValueError("static_detail is required for STATIC asset")
        if self.asset_type == "MOBILE" and self.mobile_detail is None:
            raise ValueError("mobile_detail is required for MOBILE asset")
        return self

class ColdAssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    price_per_kg_per_day: Optional[float] = Field(None, gt=0.0, le=1000.0)
    is_active: Optional[bool] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)

class AssetAvailabilityUpdate(BaseModel):
    available_capacity_kg: Optional[float] = Field(None, ge=0.0)
    is_active: Optional[bool] = None

class ColdAssetResponse(BaseModel):
    id: str
    operator_id: str
    name: str
    asset_type: str
    total_capacity_kg: float
    available_capacity_kg: float
    price_per_kg_per_day: float
    latitude: float
    longitude: float
    is_active: bool
    data_source: str  # SIMULATED or LIVE
    data_status: str  # FRESH, STALE, UNAVAILABLE (dynamically computed)
    static_detail: Optional[StaticDetailSchema] = None
    mobile_detail: Optional[MobileDetailSchema] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class ColdAssetListResponse(BaseModel):
    total: int
    items: List[ColdAssetResponse]
    skip: int
    limit: int
