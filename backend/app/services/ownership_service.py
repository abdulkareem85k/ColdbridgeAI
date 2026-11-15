from fastapi import HTTPException, status
from app.models.user import User
from app.models.produce import ProduceBatch
from app.models.asset import ColdAsset
from app.models.booking import Booking

def verify_batch_ownership(batch: ProduceBatch, user: User) -> None:
    """Ensure the user is the farmer who owns the batch, or an Admin."""
    if user.role == "ADMIN":
        return
    if batch.farmer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this produce batch."
        )

def verify_asset_ownership(asset: ColdAsset, user: User) -> None:
    """Ensure the user is the operator who owns the cooling asset, or an Admin."""
    if user.role == "ADMIN":
        return
    if asset.operator_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this cooling asset."
        )

def verify_booking_ownership(booking: Booking, user: User) -> None:
    """Ensure the user is either the booking's farmer, the asset's operator, or an Admin."""
    if user.role == "ADMIN":
        return
    is_farmer = booking.farmer_id == user.id
    is_operator = booking.asset and booking.asset.operator_id == user.id
    if not (is_farmer or is_operator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to view or modify this booking."
        )
