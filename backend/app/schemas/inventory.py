from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class InventoryBase(BaseModel):
    batch_id: str
    booking_id: str
    asset_id: str
    farmer_id: str
    initial_quantity_kg: float
    current_quantity_kg: float
    storage_location: str = "Main Bay"
    received_at: datetime
    expiry_risk_date: Optional[datetime] = None
    status: str = "STORED"
    quality_notes: Optional[str] = None

class InventoryResponse(InventoryBase):
    id: str
    created_at: datetime
    updated_at: datetime
    crop_code: Optional[str] = None
    farmer_name: Optional[str] = None
    asset_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AlertResponse(BaseModel):
    id: str
    user_id: str
    asset_id: Optional[str] = None
    batch_id: Optional[str] = None
    inventory_id: Optional[str] = None
    alert_type: str
    severity: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
