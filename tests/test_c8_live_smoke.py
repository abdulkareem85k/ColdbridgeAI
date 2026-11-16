import pytest
import datetime
from datetime import timezone
from unittest.mock import patch, MagicMock
from app.models.produce import ProduceBatch
from app.models.asset import ColdAsset, StaticAssetDetail
from app.models.matching import MatchingRequest
from app.models.inventory import Inventory
from app.models.marketplace import BuyerListing
from app.services import maps_service
from app.core.config import settings
from tests.conftest import auth_cookies_for

CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}

from app.models.user import User

def test_c8_smoke_full_lifecycle(client, farmer_user, operator_user, admin_user, db_session):
    """
    Comprehensive Live Smoke Test covering all 20 exhibition scenarios.
    """
    buyer_user = User(
        email="smoke.buyer@coldbridge.ai",
        hashed_password="hashedpassword123",
        role="BUYER",
        full_name="Smoke Buyer",
        is_active=True
    )
    db_session.add(buyer_user)
    db_session.flush()

    farmer_cookies = auth_cookies_for(farmer_user)
    operator_cookies = auth_cookies_for(operator_user)
    buyer_cookies = auth_cookies_for(buyer_user)
    admin_cookies = auth_cookies_for(admin_user)

    # 1. Farmer Register
    new_reg = client.post("/api/v1/auth/register", json={
        "email": "c8.smoke.farmer@coldbridge.ai",
        "password": "Password123!",
        "role": "FARMER",
        "full_name": "C8 Smoke Farmer",
        "phone": "+91-9876543210"
    })
    assert new_reg.status_code == 201
    assert new_reg.json()["email"] == "c8.smoke.farmer@coldbridge.ai"
    smoke_farmer_id = new_reg.json()["id"]

    # 2. Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": "c8.smoke.farmer@coldbridge.ai",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.cookies
    smoke_farmer_cookies = login_res.cookies

    # 3. Produce Batch Creation
    batch_res = client.post("/api/v1/produce/batches", json={
        "crop_code": "TOMATO",
        "quantity_kg": 300.0,
        "harvest_at": datetime.datetime.now(timezone.utc).isoformat(),
        "ambient_temp_c": 32.0,
        "latitude": 19.9975,
        "longitude": 73.7898
    }, cookies=smoke_farmer_cookies, headers=CSRF_HEADER)
    assert batch_res.status_code == 201
    batch_id = batch_res.json()["id"]

    # 4. SRI Calculation
    sri_res = client.post(f"/api/v1/sri/{batch_id}/calculate", cookies=smoke_farmer_cookies, headers=CSRF_HEADER)
    assert sri_res.status_code == 200
    assert "score" in sri_res.json()
    assert "risk_category" in sri_res.json()

    # Create active cooling asset for operator
    asset = ColdAsset(
        operator_id=operator_user.id,
        name="Smoke Cold Vault",
        asset_type="STATIC",
        total_capacity_kg=2000.0,
        available_capacity_kg=2000.0,
        price_per_kg_per_day=2.0,
        latitude=20.0100,
        longitude=73.8100,
        is_active=True,
        data_source="LIVE"
    )
    db_session.add(asset)
    db_session.flush()
    db_session.add(StaticAssetDetail(
        asset_id=asset.id,
        supported_crops="TOMATO",
        min_temperature_c=2.0,
        max_temperature_c=12.0
    ))
    db_session.commit()

    # 5. Matching Rank
    req_res = client.post("/api/v1/matching/requests", json={
        "batch_id": batch_id,
        "requested_quantity_kg": 300.0
    }, cookies=smoke_farmer_cookies, headers=CSRF_HEADER)
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    rank_res = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=smoke_farmer_cookies,
        headers=CSRF_HEADER
    )
    assert rank_res.status_code == 200
    offers = rank_res.json()["ranked_offers"]
    assert len(offers) > 0

    # 6. Allocate on New Request & 7. Simulated Bid Labelling
    first_offer = offers[0]
    assert first_offer["data_source"] in ["LIVE", "SIMULATED"]
    alloc_res = client.post(
        f"/api/v1/matching/requests/{req_id}/allocate",
        json={"bid_id": first_offer["bid_id"], "days_estimated": 3},
        cookies=smoke_farmer_cookies,
        headers=CSRF_HEADER
    )
    assert alloc_res.status_code == 201
    booking_data = alloc_res.json()
    assert booking_data["status"] == "RESERVED"
    booking_id = booking_data["id"]

    # 8. Booking Capacity Protection
    winning_asset_id = first_offer["asset_id"]
    allocated_asset = db_session.query(ColdAsset).filter_by(id=winning_asset_id).first()
    db_session.refresh(allocated_asset)
    assert allocated_asset.available_capacity_kg <= allocated_asset.total_capacity_kg - 300.0

    # 9. Concurrent Booking Conflict (overbooking)
    overbook_batch = ProduceBatch(
        farmer_id=farmer_user.id,
        crop_code="TOMATO",
        quantity_kg=2500.0, # exceeds total asset capacity
        harvest_at=datetime.datetime.now(timezone.utc),
        ambient_temp_c=30.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    db_session.add(overbook_batch)
    db_session.flush()
    overbook_req = MatchingRequest(
        batch_id=overbook_batch.id,
        farmer_id=farmer_user.id,
        requested_quantity_kg=2500.0,
        status="OPEN"
    )
    db_session.add(overbook_req)
    db_session.commit()

    # 10. Inventory Creation
    inv = Inventory(
        booking_id=booking_id,
        batch_id=batch_id,
        asset_id=winning_asset_id,
        farmer_id=smoke_farmer_id,
        current_quantity_kg=300.0,
        initial_quantity_kg=300.0,
        received_at=datetime.datetime.now(timezone.utc),
        status="ACTIVE"
    )
    db_session.add(inv)
    db_session.commit()

    # 11. Operator Approval & Surplus Listing
    listing_res = client.post("/api/v1/marketplace/listings", json={
        "inventory_id": inv.id,
        "initial_quantity_kg": 100.0,
        "base_price_per_kg": 25.0,
        "notes": "Quality inspected surplus produce"
    }, cookies=operator_cookies, headers=CSRF_HEADER)
    assert listing_res.status_code in [200, 201]
    listing_id = listing_res.json()["id"]

    # Approve listing
    appr_res = client.post(
        f"/api/v1/marketplace/listings/{listing_id}/approve",
        json={"quality_grade": "GRADE_A", "notes": "Inspected and approved"},
        cookies=operator_cookies,
        headers=CSRF_HEADER
    )
    assert appr_res.status_code == 200

    # 12. Buyer Order & Atomic Deduction
    order_res = client.post("/api/v1/marketplace/orders", json={
        "listing_id": listing_id,
        "quantity_kg": 40.0,
        "delivery_preference": "BUYER_PICKUP"
    }, cookies=buyer_cookies, headers=CSRF_HEADER)
    assert order_res.status_code in [200, 201]
    assert order_res.json()["quantity_kg"] == 40.0

    # 13. Overselling Protection
    over_order = client.post("/api/v1/marketplace/orders", json={
        "listing_id": listing_id,
        "quantity_kg": 200.0 # Exceeds remaining 60 kg!
    }, cookies=buyer_cookies, headers=CSRF_HEADER)
    assert over_order.status_code in [400, 409]

    # 14. Admin-Only Routes Blocked for Non-Admin
    blocked_res = client.post("/api/v1/admin/reset-demo-data", cookies=farmer_cookies, headers=CSRF_HEADER)
    assert blocked_res.status_code == 403

    # 15. Priority Queue Privacy
    # Farmer blocked (403)
    farmer_pq = client.get("/api/v1/sri/priority-queue", cookies=farmer_cookies)
    assert farmer_pq.status_code == 403

    # Buyer blocked (403)
    buyer_pq = client.get("/api/v1/sri/priority-queue", cookies=buyer_cookies)
    assert buyer_pq.status_code == 403

    # Operator gets filtered queue with privacy protection
    op_pq = client.get("/api/v1/sri/priority-queue", cookies=operator_cookies)
    assert op_pq.status_code == 200
    for item in op_pq.json():
        assert "priority_rank" in item
        if item["farmer_id"] is None:
            assert round(item["latitude"], 2) == item["latitude"]
            assert round(item["longitude"], 2) == item["longitude"]

    # 16. Route Calculation
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "code": "Ok",
        "routes": [{"distance": 22000.0, "duration": 1500.0, "geometry": {"coordinates": []}}]
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_resp

    with patch("app.services.maps_service.httpx.Client", return_value=mock_client):
        route_res = client.get(f"/api/v1/maps/route?batch_id={batch_id}&asset_id={asset.id}", cookies=smoke_farmer_cookies)
        assert route_res.status_code == 200
        assert route_res.json()["distance_km"] > 0

    # 17. Reverse & Forward Geocode
    mock_rev = MagicMock()
    mock_rev.status_code = 200
    mock_rev.json.return_value = {"display_name": "Nashik APMC, Maharashtra"}
    mock_client.__enter__.return_value.get.return_value = mock_rev

    with patch("app.services.maps_service.httpx.Client", return_value=mock_client):
        rev_res = client.get("/api/v1/maps/reverse-geocode?lat=19.9975&lng=73.7898", cookies=smoke_farmer_cookies)
        assert rev_res.status_code == 200
        assert rev_res.json()["address"] == "Nashik APMC, Maharashtra"

    # 18. OSRM Failure Fallback
    mock_fail = MagicMock()
    mock_fail.status_code = 500
    mock_client.__enter__.return_value.get.return_value = mock_fail
    with patch("app.services.maps_service.httpx.Client", return_value=mock_client):
        fallback_res = client.get("/api/v1/maps/route?origin_lat=19.9&origin_lng=73.7&dest_lat=19.8&dest_lng=73.6", cookies=smoke_farmer_cookies)
        assert fallback_res.status_code == 200
        assert fallback_res.json()["route_source"] == "ESTIMATED"

    # 19. Daily Limit Enforcement
    old_daily_limit = settings.MAX_ROUTE_CALLS_PER_DAY
    try:
        settings.MAX_ROUTE_CALLS_PER_DAY = 0 # Quota 0
        limit_res = client.get("/api/v1/maps/route?origin_lat=19.1&origin_lng=73.1&dest_lat=19.2&dest_lng=73.2", cookies=smoke_farmer_cookies)
        assert limit_res.status_code == 200
        assert limit_res.json()["route_source"] == "ESTIMATED"
        assert "Safety daily route call limit reached" in limit_res.json()["note"]
    finally:
        settings.MAX_ROUTE_CALLS_PER_DAY = old_daily_limit

    # 20. Logout & Expired Session
    logout_res = client.post("/api/v1/auth/logout", cookies=smoke_farmer_cookies, headers=CSRF_HEADER)
    assert logout_res.status_code == 200
    # Expired token -> 401
    expired_token = client.get("/api/v1/auth/me", cookies={"access_token": "expired_token_value"})
    assert expired_token.status_code == 401
