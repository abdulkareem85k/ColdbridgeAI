"""
ColdBridge AI - Public Cold Storage Directory Router (Part 4 D1)

Provides read-only access to real public cold storage listings in Nashik and Pune.
These facilities are from public business directories and are NOT ColdBridge partners.
They never take part in matching, ranking, operator bidding, bookings, or SRI.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.models.directory import PublicColdStorageListing
from app.schemas.directory import DirectoryListResponse, PublicColdStorageItem

router = APIRouter(prefix="/directory", tags=["Public Directory"])

ALLOWED_ROLES = ["FARMER", "BUYER", "STATIC_OPERATOR", "VAN_OPERATOR", "ADMIN"]
VALID_DISTRICTS = {"Nashik", "Pune"}

JUDGE_DISCLAIMER = (
    "These are real cold storage facilities in Nashik and Pune, "
    "taken from public directories. A farmer can contact them directly. "
    "The ranking and bids in our prototype are still simulated."
)


@router.get("/cold-storages", response_model=DirectoryListResponse)
def list_public_cold_storages(
    district: Optional[str] = Query(None, description="District filter: 'Nashik' or 'Pune'"),
    q: Optional[str] = Query(None, max_length=100, description="Search term across name, area and address (max 100 characters)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(*ALLOWED_ROLES))
):
    """
    List real cold storage facilities from public directories in Nashik and Pune.
    Read-only endpoint. Requires authentication with any valid role.
    """
    # 1. Validate district parameter
    if district is not None and district != "":
        if district not in VALID_DISTRICTS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"district must be 'Nashik', 'Pune' or omitted; got '{district}'"
            )

    # 2. Validate q length
    if q is not None and len(q) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Search query 'q' must not exceed 100 characters"
        )

    # 3. Build parameterized query
    query = db.query(PublicColdStorageListing)

    if district:
        query = query.filter(PublicColdStorageListing.district == district)

    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                PublicColdStorageListing.name.ilike(search_pattern),
                PublicColdStorageListing.area.ilike(search_pattern),
                PublicColdStorageListing.address.ilike(search_pattern)
            )
        )

    listings = query.order_by(
        PublicColdStorageListing.district.asc(),
        PublicColdStorageListing.name.asc()
    ).all()

    items = [PublicColdStorageItem.model_validate(item) for item in listings]

    return DirectoryListResponse(
        items=items,
        total=len(items),
        disclaimer=JUDGE_DISCLAIMER
    )
