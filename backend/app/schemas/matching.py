"""
ColdBridge AI - Matching Pydantic Schemas (M5)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class MatchingRequestCreate(BaseModel):
    batch_id: str = Field(..., description="ID of the produce batch needing cooling/storage")
    requested_quantity_kg: float = Field(..., gt=0, description="Quantity in kg requested")


class BidCreate(BaseModel):
    asset_id: str = Field(..., description="ID of the bidding cold asset")
    offered_capacity_kg: float = Field(..., gt=0)
    price_total: float = Field(..., gt=0, description="Total bid price in INR")
    eta_minutes: float = Field(..., ge=0, description="Estimated transit/dispatch time in minutes")
    valid_until: datetime = Field(..., description="Expiration timestamp of the bid")
    note: Optional[str] = None


class RankRequest(BaseModel):
    solar_overrides: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional simulated solar reliability overrides per asset_id for what-if testing"
    )


class BidResponse(BaseModel):
    id: str
    request_id: str
    asset_id: str
    offered_capacity_kg: float
    price_total: float
    eta_minutes: float
    valid_until: datetime
    score: Optional[float] = None
    note: Optional[str] = None
    data_source: str = "SIMULATED"
    is_accepted: bool = False
    is_expired: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchingRequestResponse(BaseModel):
    id: str
    batch_id: str
    farmer_id: str
    requested_quantity_kg: float
    status: str
    bids: List[BidResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RankedOfferDetail(BaseModel):
    rank: int
    bid_id: str
    asset_id: str
    asset_name: str
    asset_type: str
    price_total: float
    distance_km: float
    eta_minutes: float
    available_capacity_kg: float
    effective_available_kg: float
    solar_reliability: float
    route_source: str
    encoded_polyline: Optional[str] = None
    geometry: Optional[Any] = None
    unrounded_score: float
    score: float
    is_winner: bool
    components: Dict[str, float]
    reasons: List[str]
    latitude: float
    longitude: float
    data_source: str = "SIMULATED"
    is_operator_submitted: Optional[bool] = None
    is_persisted: bool = True
    price_per_kg_per_day: Optional[float] = None
    static_detail: Optional[Dict[str, Any]] = None
    mobile_detail: Optional[Dict[str, Any]] = None


class BaselinePick(BaseModel):
    bid_id: str
    asset_id: str
    asset_name: str
    asset_type: str
    score: float
    price_total: float
    distance_km: float
    eta_minutes: float
    data_source: str = "SIMULATED"


class BaselineComparison(BaseModel):
    coldbridge_pick: Optional[BaselinePick] = None
    nearest_pick: Optional[BaselinePick] = None
    cheapest_pick: Optional[BaselinePick] = None
    explanation: str


class ExcludedAssetDetail(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    reason: str
    metadata: Dict[str, Any]


class MatchingRankResponse(BaseModel):
    request_id: str
    batch_id: str
    requested_quantity_kg: float
    sri_assessment: Dict[str, Any]
    ranked_offers: List[RankedOfferDetail]
    baselines: BaselineComparison
    excluded_assets: List[ExcludedAssetDetail]
    matching_config: Dict[str, Any]
