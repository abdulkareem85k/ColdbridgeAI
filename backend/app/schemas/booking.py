"""
ColdBridge AI - Booking Pydantic Schemas (M6)
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AllocateOfferRequest(BaseModel):
    bid_id: str = Field(..., description="ID of the accepted offer/bid")
    days_estimated: int = Field(default=3, ge=1, le=90, description="Estimated days of storage")


class BookingStatusUpdate(BaseModel):
    status: str = Field(..., description="New booking status")


class PriceEstimate(BaseModel):
    quantity_kg: float
    rate_per_kg_per_day: float
    days: int
    storage_subtotal_inr: float
    transport_fee_inr: float
    platform_fee_inr: float
    total_estimate_inr: float
    disclaimer: str


class BookingResponse(BaseModel):
    id: str
    request_id: Optional[str] = None
    batch_id: str
    asset_id: str
    farmer_id: str
    quantity_kg: float
    status: str
    reserved_until: Optional[datetime] = None
    estimated_total_inr: float
    rate_per_kg_per_day: float
    days_estimated: int
    status_updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    can_cancel: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)
