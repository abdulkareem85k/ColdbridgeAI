import pytest
import datetime
from datetime import timezone
from app.models.produce import ProduceBatch
from app.models.asset import ColdAsset, StaticAssetDetail
from app.models.user import User
from app.models.matching import MatchingRequest, Bid
from app.models.booking import Booking
from tests.conftest import auth_cookies_for

def test_maps_c3_farmer_cannot_route_other_farmer_batch(client, farmer_user, operator_user, db_session):
    """Farmer cannot route from another farmer's batch (403)."""
    # Create another farmer
    other_farmer = User(
        email="other.farmer@coldbridge.ai",
        hashed_password="hashedpassword123",
        role="FARMER",
        full_name="Other Farmer",
        is_active=True
    )
    db_session.add(other_farmer)
    db_session.flush()

    batch = ProduceBatch(
        farmer_id=other_farmer.id,
        crop_code="TOMATO",
        quantity_kg=200.0,
        harvest_at=datetime.datetime.now(timezone.utc),
        ambient_temp_c=28.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    asset = ColdAsset(
        operator_id=operator_user.id,
        name="Asset 1",
        asset_type="STATIC",
        total_capacity_kg=1000.0,
        available_capacity_kg=1000.0,
        price_per_kg_per_day=2.0,
        latitude=20.0,
        longitude=73.8,
        is_active=True,
        data_source="LIVE"
    )
    db_session.add_all([batch, asset])
    db_session.commit()

    farmer_cookies = auth_cookies_for(farmer_user)
    res = client.get(f"/api/v1/maps/route?batch_id={batch.id}&asset_id={asset.id}", cookies=farmer_cookies)
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]

def test_maps_c3_farmer_cannot_route_inactive_asset(client, farmer_user, operator_user, db_session):
    """Farmer cannot route to an inactive cooling asset (403)."""
    batch = ProduceBatch(
        farmer_id=farmer_user.id,
        crop_code="TOMATO",
        quantity_kg=200.0,
        harvest_at=datetime.datetime.now(timezone.utc),
        ambient_temp_c=28.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    inactive_asset = ColdAsset(
        operator_id=operator_user.id,
        name="Inactive Asset",
        asset_type="STATIC",
        total_capacity_kg=1000.0,
        available_capacity_kg=1000.0,
        price_per_kg_per_day=2.0,
        latitude=20.0,
        longitude=73.8,
        is_active=False,
        data_source="LIVE"
    )
    db_session.add_all([batch, inactive_asset])
    db_session.commit()

    farmer_cookies = auth_cookies_for(farmer_user)
    res = client.get(f"/api/v1/maps/route?batch_id={batch.id}&asset_id={inactive_asset.id}", cookies=farmer_cookies)
    assert res.status_code == 403
    assert "not active" in res.json()["detail"]

def test_maps_c3_operator_cannot_route_unauthorized_batch_or_asset(client, farmer_user, operator_user, db_session):
    """Operator cannot route to someone else's asset, or for an unassociated batch."""
    other_op = User(
        email="other.operator@coldbridge.ai",
        hashed_password="hashedpassword123",
        role="STATIC_OPERATOR",
        full_name="Other Operator",
        is_active=True
    )
    db_session.add(other_op)
    db_session.flush()

    batch = ProduceBatch(
        farmer_id=farmer_user.id,
        crop_code="TOMATO",
        quantity_kg=200.0,
        harvest_at=datetime.datetime.now(timezone.utc),
        ambient_temp_c=28.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    other_asset = ColdAsset(
        operator_id=other_op.id,
        name="Other Asset",
        asset_type="STATIC",
        total_capacity_kg=1000.0,
        available_capacity_kg=1000.0,
        price_per_kg_per_day=2.0,
        latitude=20.0,
        longitude=73.8,
        is_active=True,
        data_source="LIVE"
    )
    my_asset = ColdAsset(
        operator_id=operator_user.id,
        name="My Asset",
        asset_type="STATIC",
        total_capacity_kg=1000.0,
        available_capacity_kg=1000.0,
        price_per_kg_per_day=2.0,
        latitude=20.0,
        longitude=73.8,
        is_active=True,
        data_source="LIVE"
    )
    db_session.add_all([batch, other_asset, my_asset])
    db_session.commit()

    operator_cookies = auth_cookies_for(operator_user)

    # 1. Route to another operator's asset -> 403
    res1 = client.get(f"/api/v1/maps/route?batch_id={batch.id}&asset_id={other_asset.id}", cookies=operator_cookies)
    assert res1.status_code == 403
    assert "only route to cold assets that you own" in res1.json()["detail"]

    # 2. Route to own asset but no bid or booking on this batch -> 403
    res2 = client.get(f"/api/v1/maps/route?batch_id={batch.id}&asset_id={my_asset.id}", cookies=operator_cookies)
    assert res2.status_code == 403
    assert "do not have an active booking" in res2.json()["detail"]

def test_maps_c3_operator_permitted_route(client, farmer_user, operator_user, db_session):
    """Operator can route for a permitted batch (when having a bid/booking) to their asset."""
    batch = ProduceBatch(
        farmer_id=farmer_user.id,
        crop_code="TOMATO",
        quantity_kg=200.0,
        harvest_at=datetime.datetime.now(timezone.utc),
        ambient_temp_c=28.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    my_asset = ColdAsset(
        operator_id=operator_user.id,
        name="My Asset",
        asset_type="STATIC",
        total_capacity_kg=1000.0,
        available_capacity_kg=1000.0,
        price_per_kg_per_day=2.0,
        latitude=20.0,
        longitude=73.8,
        is_active=True,
        data_source="LIVE"
    )
    db_session.add_all([batch, my_asset])
    db_session.flush()

    # Create matching request and bid
    m_req = MatchingRequest(
        batch_id=batch.id,
        farmer_id=farmer_user.id,
        requested_quantity_kg=200.0,
        status="OPEN"
    )
    db_session.add(m_req)
    db_session.flush()

    bid = Bid(
        request_id=m_req.id,
        asset_id=my_asset.id,
        offered_capacity_kg=200.0,
        price_total=300.0,
        eta_minutes=30.0,
        data_source="LIVE",
        valid_until=datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=24)
    )
    db_session.add(bid)
    db_session.commit()

    operator_cookies = auth_cookies_for(operator_user)
    res = client.get(f"/api/v1/maps/route?batch_id={batch.id}&asset_id={my_asset.id}", cookies=operator_cookies)
    assert res.status_code == 200
    assert "distance_km" in res.json()

def test_maps_c3_coordinate_routing_valid_and_out_of_range(client, farmer_user):
    """Coordinate routing validates -90..90 and -180..180 ranges and succeeds on valid coords."""
    cookies = auth_cookies_for(farmer_user)

    # Valid coordinates
    res = client.get("/api/v1/maps/route?origin_lat=19.9975&origin_lng=73.7898&dest_lat=18.5204&dest_lng=73.8567", cookies=cookies)
    assert res.status_code == 200
    data = res.json()
    assert data["distance_km"] > 0

    # Latitude > 90
    res_bad_lat = client.get("/api/v1/maps/route?origin_lat=95.0&origin_lng=73.7898&dest_lat=18.5204&dest_lng=73.8567", cookies=cookies)
    assert res_bad_lat.status_code == 422
    assert "Latitude must be between" in res_bad_lat.json()["detail"]

    # Longitude < -180
    res_bad_lng = client.get("/api/v1/maps/route?origin_lat=19.0&origin_lng=-185.0&dest_lat=18.5204&dest_lng=73.8567", cookies=cookies)
    assert res_bad_lng.status_code == 422
    assert "Longitude must be between" in res_bad_lng.json()["detail"]

def test_maps_c3_partial_coords_and_mixed_modes(client, farmer_user):
    """Rejects partial coordinate sets and mixed modes with 422."""
    cookies = auth_cookies_for(farmer_user)

    # Partial coordinates (missing dest_lng)
    res_partial = client.get("/api/v1/maps/route?origin_lat=19.0&origin_lng=73.0&dest_lat=18.0", cookies=cookies)
    assert res_partial.status_code == 422

    # Mixed mode (batch_id + origin_lat)
    res_mixed = client.get("/api/v1/maps/route?batch_id=batch123&asset_id=asset123&origin_lat=19.0", cookies=cookies)
    assert res_mixed.status_code == 422
    assert "Cannot mix" in res_mixed.json()["detail"]

def test_maps_c3_missing_resources_404(client, farmer_user):
    """Missing batch or asset raises 404."""
    cookies = auth_cookies_for(farmer_user)

    res = client.get("/api/v1/maps/route?batch_id=nonexistent_batch&asset_id=nonexistent_asset", cookies=cookies)
    assert res.status_code == 404

def test_maps_c3_rate_limiting(client, farmer_user):
    """Per-user rate limit returns 429 when quota exceeded."""
    cookies = auth_cookies_for(farmer_user)
    from app.routers import maps

    # Temporarily reduce limit for testing
    old_limit = maps.MAX_ROUTE_CALLS_PER_MINUTE_PER_USER
    try:
        maps.MAX_ROUTE_CALLS_PER_MINUTE_PER_USER = 3
        # Clear existing history for farmer_user
        with maps._route_rate_lock:
            maps._user_route_history[str(farmer_user.id)] = []

        url = "/api/v1/maps/route?origin_lat=19.0&origin_lng=73.0&dest_lat=19.1&dest_lng=73.1"
        for _ in range(3):
            r = client.get(url, cookies=cookies)
            assert r.status_code == 200

        # 4th call exceeds limit
        r4 = client.get(url, cookies=cookies)
        assert r4.status_code == 429
        assert "Rate limit exceeded" in r4.json()["detail"]
    finally:
        maps.MAX_ROUTE_CALLS_PER_MINUTE_PER_USER = old_limit
        with maps._route_rate_lock:
            maps._user_route_history[str(farmer_user.id)] = []
