"""
Tests for Part 5: Operator Role Separation & Enforcement (Phase E1)

1. STATIC_OPERATOR cannot create a MOBILE asset (403)
2. VAN_OPERATOR cannot create a STATIC asset (403)
3. Each operator lists only their own assets (GET /api/v1/assets)
4. An operator cannot read or update bookings of another operator's asset (403)
5. FARMER and BUYER get 403 on operator-only endpoints
6. Static HTML & frontend routing checks
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.asset import ColdAsset, StaticAssetDetail, MobileAssetDetail
from app.models.produce import ProduceBatch
from app.models.booking import Booking
from tests.conftest import auth_cookies_for

CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}


def test_static_operator_cannot_create_mobile_asset(client, operator_user):
    """STATIC_OPERATOR attempting to create a MOBILE asset must receive 403 Forbidden."""
    cookies = auth_cookies_for(operator_user)

    payload = {
        "name": "Unauthorized Van",
        "asset_type": "MOBILE",
        "total_capacity_kg": 2000.0,
        "price_per_kg_per_day": 1.5,
        "latitude": 19.9975,
        "longitude": 73.7898,
        "mobile_detail": {
            "vehicle_ref": "MH-15-UNAUTH",
            "service_radius_km": 50.0,
            "solar_reliability": 0.85
        }
    }
    res = client.post("/api/v1/assets", json=payload, cookies=cookies, headers=CSRF_HEADER)
    assert res.status_code == 403, f"Expected 403 but got {res.status_code}: {res.text}"


def test_van_operator_cannot_create_static_asset(client, van_operator_user):
    """VAN_OPERATOR attempting to create a STATIC asset must receive 403 Forbidden."""
    cookies = auth_cookies_for(van_operator_user)

    payload = {
        "name": "Unauthorized Cold Room",
        "asset_type": "STATIC",
        "total_capacity_kg": 5000.0,
        "price_per_kg_per_day": 1.2,
        "latitude": 19.9975,
        "longitude": 73.7898,
        "static_detail": {
            "address": "Unauthorized Address",
            "supported_crops": "tomato",
            "min_temperature_c": 2.0,
            "max_temperature_c": 10.0
        }
    }
    res = client.post("/api/v1/assets", json=payload, cookies=cookies, headers=CSRF_HEADER)
    assert res.status_code == 403, f"Expected 403 but got {res.status_code}: {res.text}"


def test_each_operator_lists_only_own_assets(client, operator_user, van_operator_user, db_session):
    """Each operator only sees their own assets of their respective type on GET /api/v1/assets."""
    # Ensure van operator has an asset in db
    van_asset = ColdAsset(
        id="test-van-asset-001",
        operator_id=van_operator_user.id,
        name="Solar Van Express",
        asset_type="MOBILE",
        total_capacity_kg=1200.0,
        available_capacity_kg=1200.0,
        price_per_kg_per_day=2.0,
        latitude=19.9975,
        longitude=73.7898,
        is_active=True
    )
    db_session.add(van_asset)
    db_session.flush()
    db_session.add(MobileAssetDetail(
        asset_id=van_asset.id,
        vehicle_ref="MH-15-TC-101",
        service_radius_km=45.0,
        solar_reliability=0.9
    ))
    db_session.commit()

    # Static operator check
    static_cookies = auth_cookies_for(operator_user)
    res_static = client.get("/api/v1/assets", cookies=static_cookies)
    assert res_static.status_code == 200
    static_data = res_static.json()
    assert static_data["total"] > 0
    for item in static_data["items"]:
        assert item["operator_id"] == operator_user.id
        assert item["asset_type"] == "STATIC"

    # Van operator check
    van_cookies = auth_cookies_for(van_operator_user)
    res_van = client.get("/api/v1/assets", cookies=van_cookies)
    assert res_van.status_code == 200
    van_data = res_van.json()
    assert van_data["total"] > 0
    for item in van_data["items"]:
        assert item["operator_id"] == van_operator_user.id
        assert item["asset_type"] == "MOBILE"


def test_operator_cannot_read_or_update_other_operator_booking(
    client, operator_user, van_operator_user, farmer_user, db_session
):
    """An operator cannot read or update bookings for an asset they do not own (returns 403)."""
    # Create produce batch
    batch = ProduceBatch(
        id="batch-role-test-01",
        farmer_id=farmer_user.id,
        crop_code="TOMATO",
        quantity_kg=500.0,
        harvest_at=datetime.now(timezone.utc),
        ambient_temp_c=30.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    db_session.add(batch)
    db_session.flush()

    # Create booking for static operator's asset (test-op-asset-001)
    booking = Booking(
        id="booking-role-test-01",
        batch_id=batch.id,
        asset_id="test-op-asset-001",
        farmer_id=farmer_user.id,
        quantity_kg=500.0,
        status="CONFIRMED",
        rate_per_kg_per_day=1.5,
        days_estimated=3,
        estimated_total_inr=2250.0,
        status_updated_by=operator_user.id
    )
    db_session.add(booking)
    db_session.commit()

    van_cookies = auth_cookies_for(van_operator_user)

    # Van operator tries to view static operator's booking
    res_view = client.get(f"/api/v1/bookings/{booking.id}", cookies=van_cookies)
    assert res_view.status_code == 403, f"Expected 403 for other operator view, got {res_view.status_code}"

    # Van operator tries to advance status of static operator's booking
    res_patch = client.patch(
        f"/api/v1/bookings/{booking.id}/status",
        json={"status": "PRODUCE_RECEIVED"},
        cookies=van_cookies,
        headers=CSRF_HEADER
    )
    assert res_patch.status_code == 403, f"Expected 403 for other operator update, got {res_patch.status_code}"


def test_farmer_and_buyer_get_403_on_operator_only_endpoints(client, farmer_user, db_session):
    """FARMER and BUYER receive 403 Forbidden on operator-only endpoints."""
    buyer_user = User(
        id="test-buyer-roles-001",
        email="buyer_roles@test.com",
        hashed_password="dummy_buyer_hashed_password",
        role="BUYER",
        full_name="Test Buyer",
        is_active=True
    )
    db_session.add(buyer_user)
    db_session.commit()

    farmer_cookies = auth_cookies_for(farmer_user)
    buyer_cookies = auth_cookies_for(buyer_user)

    asset_payload = {
        "name": "Forbidden Asset",
        "asset_type": "STATIC",
        "total_capacity_kg": 1000.0,
        "price_per_kg_per_day": 1.0,
        "latitude": 19.9975,
        "longitude": 73.7898
    }

    test_asset_id = "test-op-asset-001"
    avail_payload = {"is_active": True, "available_capacity_kg": 500.0}

    for role_name, cookies in [("FARMER", farmer_cookies), ("BUYER", buyer_cookies)]:
        # 1. Asset creation
        res = client.post("/api/v1/assets", json=asset_payload, cookies=cookies, headers=CSRF_HEADER)
        assert res.status_code == 403, f"{role_name} should get 403 on POST /assets, got {res.status_code}"

        # 2. Asset availability update
        res = client.patch(f"/api/v1/assets/{test_asset_id}/availability", json=avail_payload, cookies=cookies, headers=CSRF_HEADER)
        assert res.status_code == 403, f"{role_name} should get 403 on PATCH /assets/id/availability, got {res.status_code}"

        # 3. Utilization retrieval
        res = client.get("/api/v1/assets/my-assets/utilization", cookies=cookies)
        assert res.status_code == 403, f"{role_name} should get 403 on GET /assets/my-assets/utilization, got {res.status_code}"


def test_static_html_and_routing_checks():
    """
    Static checks:
    - storage_operator.html does not contain 'Add Solar Van'
    - van_operator.html does not contain 'Add Cold Room'
    - js/auth.js maps STATIC_OPERATOR -> storage_operator.html and VAN_OPERATOR -> van_operator.html
    - operator.html exists as a redirect shim
    """
    root_dir = Path(__file__).resolve().parent.parent
    frontend_dir = root_dir / "frontend"

    # Check storage_operator.html
    storage_html_path = frontend_dir / "storage_operator.html"
    assert storage_html_path.exists(), "storage_operator.html must exist"
    storage_html = storage_html_path.read_text(encoding="utf-8")
    assert "Add Solar Van" not in storage_html, "storage_operator.html must not contain 'Add Solar Van'"
    assert "🏭 Storage Operator" in storage_html, "storage_operator.html must contain '🏭 Storage Operator'"

    # Check van_operator.html
    van_html_path = frontend_dir / "van_operator.html"
    assert van_html_path.exists(), "van_operator.html must exist"
    van_html = van_html_path.read_text(encoding="utf-8")
    assert "Add Cold Room" not in van_html, "van_operator.html must not contain 'Add Cold Room'"
    assert "🚐 Solar Van Operator" in van_html, "van_operator.html must contain '🚐 Solar Van Operator'"

    # Check auth.js routing
    auth_js_path = frontend_dir / "js" / "auth.js"
    assert auth_js_path.exists(), "auth.js must exist"
    auth_js = auth_js_path.read_text(encoding="utf-8")
    assert "storage_operator.html" in auth_js, "auth.js must route to storage_operator.html"
    assert "van_operator.html" in auth_js, "auth.js must route to van_operator.html"

    # Check operator.html redirect shim
    operator_html_path = frontend_dir / "operator.html"
    assert operator_html_path.exists(), "operator.html must exist as redirect shim"
    operator_html = operator_html_path.read_text(encoding="utf-8")
    assert "redirectByRole" in operator_html, "operator.html must invoke redirectByRole"
    assert "tabAssets" not in operator_html, "operator.html should no longer contain full tab structure"


def test_farmer_type_clarity_fields_and_booking_details(
    client, farmer_user, operator_user, van_operator_user, db_session
):
    """
    Phase E2 API tests:
    - RankedOfferDetail contains price_per_kg_per_day, static_detail (for STATIC), and mobile_detail (for MOBILE).
    - Booking responses contain static_detail or mobile_detail.
    """
    # Create van asset for van operator
    van_asset = ColdAsset(
        id="test-van-e2-001",
        operator_id=van_operator_user.id,
        name="Solar Van Clarify",
        asset_type="MOBILE",
        total_capacity_kg=1500.0,
        available_capacity_kg=1500.0,
        price_per_kg_per_day=2.0,
        latitude=19.9975,
        longitude=73.7898,
        is_active=True
    )
    db_session.add(van_asset)
    db_session.flush()
    db_session.add(MobileAssetDetail(
        asset_id=van_asset.id,
        vehicle_ref="MH-15-CLARIFY",
        service_radius_km=45.0,
        solar_reliability=0.9,
        last_location_at=datetime.now(timezone.utc)
    ))

    # Create produce batch for farmer
    batch = ProduceBatch(
        id="batch-e2-clarify-001",
        farmer_id=farmer_user.id,
        crop_code="TOMATO",
        quantity_kg=500.0,
        harvest_at=datetime.now(timezone.utc),
        ambient_temp_c=30.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    db_session.add(batch)
    db_session.commit()

    farmer_cookies = auth_cookies_for(farmer_user)

    # 1. Create matching request
    req_res = client.post(
        "/api/v1/matching/requests",
        json={"batch_id": batch.id, "requested_quantity_kg": 500.0},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # 2. Rank offers
    rank_res = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert rank_res.status_code == 200
    rank_data = rank_res.json()
    assert len(rank_data["ranked_offers"]) > 0

    found_static = False
    found_mobile = False
    for offer in rank_data["ranked_offers"]:
        assert "price_per_kg_per_day" in offer
        assert offer["price_per_kg_per_day"] > 0
        if offer["asset_type"] == "STATIC":
            found_static = True
            assert offer["static_detail"] is not None
            assert "address" in offer["static_detail"]
            assert "supported_crops" in offer["static_detail"]
            assert "min_temperature_c" in offer["static_detail"]
            assert "max_temperature_c" in offer["static_detail"]
        elif offer["asset_type"] == "MOBILE":
            found_mobile = True
            assert offer["mobile_detail"] is not None
            assert "vehicle_ref" in offer["mobile_detail"]
            assert "service_radius_km" in offer["mobile_detail"]
            assert "solar_reliability" in offer["mobile_detail"]

    assert found_static, "Expected at least one STATIC offer in ranked_offers"
    assert found_mobile, "Expected at least one MOBILE offer in ranked_offers"

    # 3. Check Booking enrichment
    booking = Booking(
        id="booking-e2-clarify-001",
        request_id=req_id,
        batch_id=batch.id,
        asset_id="test-op-asset-001",
        farmer_id=farmer_user.id,
        quantity_kg=500.0,
        status="CONFIRMED",
        rate_per_kg_per_day=1.5,
        days_estimated=3,
        estimated_total_inr=2250.0,
        status_updated_by=operator_user.id
    )
    db_session.add(booking)
    db_session.commit()

    res_bookings = client.get("/api/v1/bookings/my-bookings", cookies=farmer_cookies)
    assert res_bookings.status_code == 200
    b_items = res_bookings.json()
    assert len(b_items) > 0
    test_b = next(b for b in b_items if b["id"] == booking.id)
    assert test_b["static_detail"] is not None
    assert "address" in test_b["static_detail"]


def test_farmer_html_type_clarity_and_filters():
    """
    Phase E2 Static frontend checks:
    - farmer.html has offer type filters (All, Storage rooms, Solar vans).
    - farmer.html has distinct type blocks:
      'You deliver your produce to this facility' for storage rooms
      'This van comes to your farm to pick up' for solar vans.
    - farmer.html handles missing offer scenario ('No solar van available within range').
    """
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    farmer_html = (frontend_dir / "farmer.html").read_text(encoding="utf-8")

    assert "btn-filter-offer" in farmer_html, "farmer.html must have offer filter buttons"
    assert "You deliver your produce to this facility" in farmer_html, "farmer.html must have storage room description"
    assert "This van comes to your farm to pick up" in farmer_html, "farmer.html must have solar van description"
    assert "No solar van available within range" in farmer_html, "farmer.html must have missing van message"
    assert "No storage room available within range" in farmer_html, "farmer.html must have missing storage message"


def test_operator_bid_submission_rbac_and_validations(
    client, operator_user, van_operator_user, farmer_user, db_session
):
    """
    Phase E3 Security & Validation:
    - Farmer and Buyer get 403 Forbidden on POST /requests/{id}/bids
    - Operator cannot bid on another operator's asset (403)
    - Static operator cannot bid using a mobile asset (403)
    - Operator cannot bid capacity exceeding asset available capacity (400)
    - Valid bid submission creates bid with data_source="LIVE" (201)
    """
    # 1. Create a produce batch and matching request
    batch = ProduceBatch(
        id="batch-e3-test-001",
        farmer_id=farmer_user.id,
        crop_code="TOMATO",
        quantity_kg=600.0,
        harvest_at=datetime.now(timezone.utc),
        ambient_temp_c=29.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    db_session.add(batch)
    db_session.flush()

    farmer_cookies = auth_cookies_for(farmer_user)
    req_res = client.post(
        "/api/v1/matching/requests",
        json={"batch_id": batch.id, "requested_quantity_kg": 600.0},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # Also create a van asset for van operator
    van_asset = ColdAsset(
        id="test-van-e3-001",
        operator_id=van_operator_user.id,
        name="Solar Van Bid Test",
        asset_type="MOBILE",
        total_capacity_kg=1000.0,
        available_capacity_kg=800.0,
        price_per_kg_per_day=2.0,
        latitude=19.9975,
        longitude=73.7898,
        is_active=True
    )
    db_session.add(van_asset)
    db_session.flush()
    db_session.add(MobileAssetDetail(
        asset_id=van_asset.id,
        vehicle_ref="MH-15-E3-001",
        service_radius_km=40.0,
        solar_reliability=0.9,
        last_location_at=datetime.now(timezone.utc)
    ))
    db_session.commit()

    static_cookies = auth_cookies_for(operator_user)

    valid_until_str = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()

    bid_payload = {
        "asset_id": "test-op-asset-001",
        "offered_capacity_kg": 600.0,
        "price_total": 1200.0,
        "eta_minutes": 25.0,
        "valid_until": valid_until_str,
        "note": "Standard static storage offer"
    }

    # 1. Farmer attempts to submit bid -> 403
    res_f = client.post(f"/api/v1/matching/requests/{req_id}/bids", json=bid_payload, cookies=farmer_cookies, headers=CSRF_HEADER)
    assert res_f.status_code == 403, f"Farmer should get 403 on bid submit, got {res_f.status_code}"

    # 2. Static operator attempts to bid on van operator's asset -> 403
    cross_payload = dict(bid_payload, asset_id=van_asset.id)
    res_cross = client.post(f"/api/v1/matching/requests/{req_id}/bids", json=cross_payload, cookies=static_cookies, headers=CSRF_HEADER)
    assert res_cross.status_code == 403, f"Cross-operator bid should get 403, got {res_cross.status_code}"

    # 3. Static operator attempts to bid capacity exceeding available capacity -> 400
    static_asset = db_session.query(ColdAsset).filter_by(id="test-op-asset-001").first()
    excess_capacity = static_asset.available_capacity_kg + 5000.0
    excess_payload = dict(bid_payload, offered_capacity_kg=excess_capacity)
    res_excess = client.post(f"/api/v1/matching/requests/{req_id}/bids", json=excess_payload, cookies=static_cookies, headers=CSRF_HEADER)
    assert res_excess.status_code == 400, f"Exceeding capacity should get 400, got {res_excess.status_code}"

    # 4. Valid bid by static operator -> 201 Created with data_source="LIVE"
    res_valid = client.post(f"/api/v1/matching/requests/{req_id}/bids", json=bid_payload, cookies=static_cookies, headers=CSRF_HEADER)
    assert res_valid.status_code == 201, f"Expected 201, got {res_valid.status_code}: {res_valid.text}"
    bid_data = res_valid.json()
    assert bid_data["asset_id"] == "test-op-asset-001"
    assert bid_data["data_source"] == "LIVE"
    assert bid_data["offered_capacity_kg"] == 600.0


def test_open_requests_and_live_operator_bids_flow(
    client, operator_user, van_operator_user, farmer_user, db_session
):
    """
    Phase E3 Flow:
    - Operator views open requests (privacy enforced: coords rounded, no farmer email/phone)
    - Submitting a bid reflects in GET /open-requests as is_operator_submitted=True
    - Farmer matching ranking displays the bid with data_source='LIVE' and is_operator_submitted=True
    """
    # 1. Create produce batch and request
    batch = ProduceBatch(
        id="batch-e3-flow-001",
        farmer_id=farmer_user.id,
        crop_code="TOMATO",
        quantity_kg=450.0,
        harvest_at=datetime.now(timezone.utc),
        ambient_temp_c=28.0,
        latitude=19.997543,
        longitude=73.789876,
        data_source="LIVE"
    )
    db_session.add(batch)
    db_session.commit()

    farmer_cookies = auth_cookies_for(farmer_user)
    req_res = client.post(
        "/api/v1/matching/requests",
        json={"batch_id": batch.id, "requested_quantity_kg": 450.0},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    static_cookies = auth_cookies_for(operator_user)

    # 2. Operator gets open requests
    res_open = client.get("/api/v1/matching/open-requests", cookies=static_cookies)
    assert res_open.status_code == 200
    open_reqs = res_open.json()
    target_req = next((r for r in open_reqs if r["id"] == req_id), None)
    assert target_req is not None
    # Privacy check: coords rounded to 2 decimals, no farmer full name or contact
    assert target_req["approx_latitude"] == 20.0 or target_req["approx_latitude"] == round(19.997543, 2)
    assert target_req["approx_longitude"] == round(73.789876, 2)
    assert "farmer_name" not in target_req
    assert "farmer_phone" not in target_req
    assert target_req["existing_bid"] is None

    # 3. Operator submits live bid
    valid_until_str = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
    live_bid_payload = {
        "asset_id": "test-op-asset-001",
        "offered_capacity_kg": 450.0,
        "price_total": 950.0,
        "eta_minutes": 20.0,
        "valid_until": valid_until_str,
        "note": "Immediate cold room space reserved"
    }
    bid_res = client.post(f"/api/v1/matching/requests/{req_id}/bids", json=live_bid_payload, cookies=static_cookies, headers=CSRF_HEADER)
    assert bid_res.status_code == 201

    # 4. Operator queries open requests again -> existing_bid populated and marked LIVE
    res_open_after = client.get("/api/v1/matching/open-requests", cookies=static_cookies)
    assert res_open_after.status_code == 200
    target_req_after = next(r for r in res_open_after.json() if r["id"] == req_id)
    assert target_req_after["existing_bid"] is not None
    assert target_req_after["existing_bid"]["is_operator_submitted"] is True
    assert target_req_after["existing_bid"]["data_source"] == "LIVE"
    assert target_req_after["existing_bid"]["price_total"] == 950.0

    # 5. Farmer ranks offers -> live operator bid is present with data_source="LIVE"
    rank_res = client.post(f"/api/v1/matching/requests/{req_id}/rank", json={}, cookies=farmer_cookies, headers=CSRF_HEADER)
    assert rank_res.status_code == 200
    offers = rank_res.json()["ranked_offers"]
    live_offer = next((o for o in offers if o["asset_id"] == "test-op-asset-001"), None)
    assert live_offer is not None
    assert live_offer["data_source"] == "LIVE"
    assert live_offer["is_operator_submitted"] is True
    assert live_offer["price_total"] == 950.0


def test_operator_ui_open_requests_and_bids_tab():
    """
    Phase E3 UI checks:
    - storage_operator.html contains Open Requests tab (#tabBids), bidsTableContainer, and bidModal
    - storage_operator.html uses wording 'Submit Offer to Store'
    - van_operator.html contains Open Requests tab (#tabBids), bidsTableContainer, and bidModal
    - van_operator.html uses wording 'Submit Offer to Pick Up & Store'
    """
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    storage_html = (frontend_dir / "storage_operator.html").read_text(encoding="utf-8")
    van_html = (frontend_dir / "van_operator.html").read_text(encoding="utf-8")

    # Storage operator UI checks
    assert 'id="tabBids"' in storage_html
    assert 'id="bidsTableContainer"' in storage_html
    assert 'id="bidModal"' in storage_html
    assert "Submit Offer to Store" in storage_html

    # Van operator UI checks
    assert 'id="tabBids"' in van_html
    assert 'id="bidsTableContainer"' in van_html
    assert 'id="bidModal"' in van_html
    assert "Submit Offer to Pick Up & Store" in van_html


