"""
ColdBridge AI - Eligibility Filtering Service (M5)

Applies 6 clear eligibility filters to cold assets for a given batch request.
Every excluded asset is retained with a specific, explainable rejection reason.
"""

import datetime
from datetime import timezone
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.models.asset import ColdAsset
from app.services.solar_adjustment import get_effective_capacity


def evaluate_asset_eligibility(
    asset: ColdAsset,
    crop_code: str,
    requested_quantity_kg: float,
    distance_km: float,
    now: datetime.datetime = None,
    solar_reliability_override: float = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluates whether a single ColdAsset is eligible for a matching request.

    Returns:
        (is_eligible: bool, reason: str, metadata: dict)
    """
    if now is None:
        now = datetime.datetime.now(timezone.utc)

    metadata = {
        "asset_id": asset.id,
        "asset_name": asset.name,
        "asset_type": asset.asset_type,
        "total_capacity_kg": asset.total_capacity_kg,
        "available_capacity_kg": asset.available_capacity_kg,
        "effective_capacity_kg": asset.available_capacity_kg,
        "distance_km": distance_km,
        "solar_reliability": 1.0,
        "data_status": "FRESH"
    }

    # 1. Filter: Inactive Asset
    if not asset.is_active:
        return False, "Asset is currently inactive or undergoing maintenance", metadata

    # 2. Filter: Mobile Van specifics (Data Freshness, Service Radius, Solar Fallback)
    if asset.asset_type == "MOBILE":
        mobile_detail = getattr(asset, "mobile_detail", None)
        if not mobile_detail:
            metadata["data_status"] = "UNAVAILABLE"
            return False, "Mobile asset detail record is missing", metadata

        # Determine solar reliability (simulation input or override)
        solar_rel = solar_reliability_override if solar_reliability_override is not None else mobile_detail.solar_reliability
        metadata["solar_reliability"] = solar_rel

        # Check location data status (FRESH / STALE / UNAVAILABLE)
        if mobile_detail.last_location_at is None:
            metadata["data_status"] = "UNAVAILABLE"
            return False, "Mobile van location is UNAVAILABLE", metadata

        loc_time = mobile_detail.last_location_at
        if loc_time.tzinfo is None:
            loc_time = loc_time.replace(tzinfo=timezone.utc)

        age_seconds = (now - loc_time).total_seconds()
        if age_seconds > settings.LOCATION_FRESHNESS_MINUTES * 60:
            metadata["data_status"] = "STALE"
            return False, f"Mobile van location data is STALE (> {settings.LOCATION_FRESHNESS_MINUTES} min old)", metadata

        metadata["data_status"] = "FRESH"

        # Check service radius
        radius = float(mobile_detail.service_radius_km or 50.0)
        metadata["service_radius_km"] = radius
        if distance_km > radius:
            return False, f"Asset is outside mobile service radius ({distance_km:.1f} km > {radius:.1f} km)", metadata

        # Check effective capacity under solar fallback
        effective_cap = get_effective_capacity(asset.available_capacity_kg, "MOBILE", solar_rel)
        metadata["effective_capacity_kg"] = effective_cap

        if effective_cap < requested_quantity_kg:
            return False, f"Insufficient effective solar capacity ({effective_cap:.1f} kg < {requested_quantity_kg:.1f} kg requested at solar reliability {solar_rel:.2f})", metadata

    # 3. Filter: Static Cold Room specifics (Supported Crops, Temperature, Capacity)
    elif asset.asset_type == "STATIC":
        static_detail = getattr(asset, "static_detail", None)
        if static_detail:
            supported = [c.strip().lower() for c in (static_detail.supported_crops or "").split(",") if c.strip()]
            if crop_code and supported and crop_code.lower() not in supported:
                return False, f"Crop '{crop_code}' is not supported by static facility (supported: {', '.join(supported)})", metadata

        metadata["effective_capacity_kg"] = asset.available_capacity_kg
        if asset.available_capacity_kg < requested_quantity_kg:
            return False, f"Insufficient available capacity ({asset.available_capacity_kg:.1f} kg < {requested_quantity_kg:.1f} kg requested)", metadata

    return True, "Eligible for matching", metadata


def filter_eligible_assets(
    assets: List[ColdAsset],
    crop_code: str,
    requested_quantity_kg: float,
    distances_km: Dict[str, float],
    solar_overrides: Dict[str, float] = None,
    now: datetime.datetime = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Separates candidate assets into eligible and excluded lists.
    """
    eligible = []
    excluded = []
    solar_overrides = solar_overrides or {}

    for asset in assets:
        dist = distances_km.get(asset.id, 999.0)
        solar_rel = solar_overrides.get(asset.id, None)
        is_ok, reason, meta = evaluate_asset_eligibility(
            asset=asset,
            crop_code=crop_code,
            requested_quantity_kg=requested_quantity_kg,
            distance_km=dist,
            now=now,
            solar_reliability_override=solar_rel
        )
        entry = {
            "asset": asset,
            "metadata": meta,
            "reason": reason
        }
        if is_ok:
            eligible.append(entry)
        else:
            excluded.append(entry)

    return eligible, excluded
