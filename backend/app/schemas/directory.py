"""
ColdBridge AI - Public Cold Storage Directory Schemas (Part 4)
"""

import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class PublicColdStorageItem(BaseModel):
    id: str
    name: str
    district: str
    area: str
    address: str
    phone: Optional[str] = None
    source_note: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity_mt: Optional[float] = None
    is_partner: bool = False
    contact_verified: bool = False
    last_checked_on: Optional[datetime.date] = None
    created_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DirectoryListResponse(BaseModel):
    items: List[PublicColdStorageItem]
    total: int
    disclaimer: str = (
        "These are real cold storage facilities in Nashik and Pune, "
        "taken from public directories. A farmer can contact them directly. "
        "The ranking and bids in our prototype are still simulated."
    )
