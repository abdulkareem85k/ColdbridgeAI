import datetime
from datetime import timezone
from app.core.config import settings
from app.models.asset import ColdAsset

def compute_asset_data_status(asset: ColdAsset) -> str:
    """
    Calculate data status (FRESH, STALE, UNAVAILABLE) dynamically.
    For MOBILE vans, compare last_location_at with LOCATION_FRESHNESS_MINUTES.
    For STATIC rooms, evaluate based on updated_at.
    Never hardcode or store in DB.
    """
    now = datetime.datetime.now(timezone.utc)
    freshness_threshold = datetime.timedelta(minutes=settings.LOCATION_FRESHNESS_MINUTES)

    if asset.asset_type == "MOBILE":
        mobile_detail = asset.mobile_detail
        if not mobile_detail or not mobile_detail.last_location_at:
            return "UNAVAILABLE"
        
        last_loc = mobile_detail.last_location_at
        if last_loc.tzinfo is None:
            last_loc = last_loc.replace(tzinfo=timezone.utc)
        
        if now - last_loc <= freshness_threshold:
            return "FRESH"
        else:
            return "STALE"
    else:
        # Static asset status
        updated_at = asset.updated_at
        if not updated_at:
            return "FRESH"
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        # Static asset data remains fresh if active, otherwise stale if unconfirmed for 7 days
        if asset.is_active:
            return "FRESH"
        return "STALE"
