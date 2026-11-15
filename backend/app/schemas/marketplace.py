from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ListingCreate(BaseModel):
    inventory_id: str
    base_price_per_kg: float = Field(..., gt=0)
    initial_quantity_kg: Optional[float] = Field(None, gt=0)
    expiry_hours: int = Field(48, ge=6, le=720)
    quality_grade: str = "GRADE_A"
    notes: Optional[str] = None
    approve_immediately: bool = False  # If True, operator also signs off on quality check immediately

class ListingQualityApproval(BaseModel):
    quality_grade: str = "GRADE_A"
    notes: Optional[str] = None

class ListingResponse(BaseModel):
    id: str
    inventory_id: str
    asset_id: str
    asset_name: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    operator_id: str
    crop_code: str
    initial_quantity_kg: float
    available_quantity_kg: float
    base_price_per_kg: float
    current_discount_pct: float
    discounted_price_per_kg: float
    status: str
    quality_approved_by: Optional[str] = None
    quality_approved_at: Optional[datetime] = None
    quality_grade: Optional[str] = None
    listed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    data_source: str = "SIMULATED"
    data_status: str = "FRESH"

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    listing_id: str
    quantity_kg: float = Field(..., gt=0)
    delivery_preference: str = "BUYER_PICKUP" # BUYER_PICKUP, VAN_DELIVERY
    contact_phone: Optional[str] = None
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    id: str
    listing_id: str
    buyer_id: str
    buyer_name: Optional[str] = None
    crop_code: Optional[str] = None
    asset_name: Optional[str] = None
    quantity_kg: float
    unit_price_inr: float
    total_price_inr: float
    status: str
    delivery_preference: str
    contact_phone: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    data_source: str = "SIMULATED"

    model_config = ConfigDict(from_attributes=True)
