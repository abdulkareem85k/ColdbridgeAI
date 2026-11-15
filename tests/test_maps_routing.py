import pytest
from app.services.maps_service import haversine_km, compute_route, compute_route_matrix
from tests.conftest import auth_cookies_for

def test_haversine_calculation():
    # Nashik to Pune ~ 160-170 km straight-line
    nashik = (19.9975, 73.7898)
    pune = (18.5204, 73.8567)
    dist = haversine_km(nashik, pune)
    assert 160.0 <= dist <= 175.0

    # Same location distance is 0.0
    assert haversine_km(nashik, nashik) == 0.0

def test_compute_route_and_caching(db_session):
    nashik = (19.9975, 73.7898)
    dindori = (20.0800, 73.8400)
    
    # 1. First route computation
    route1 = compute_route(nashik, dindori, db_session)
    assert route1["distance_km"] > 0
    assert route1["duration_minutes"] > 0
    assert route1["route_source"] in ["OSRM_ROUTES", "ESTIMATED"]

    # 2. Second computation should hit database cache
    route2 = compute_route(nashik, dindori, db_session)
    assert route2["cached"] is True
    assert route2["distance_km"] == route1["distance_km"]

def test_maps_route_api_endpoint(client, farmer_user, operator_user, db_session):
    from app.models.produce import ProduceBatch
    from app.models.asset import ColdAsset, StaticAssetDetail
    import datetime
    from datetime import timezone

    farmer_cookies = auth_cookies_for(farmer_user)
    now_utc = datetime.datetime.now(timezone.utc)

    batch = ProduceBatch(
        farmer_id=farmer_user.id,
        crop_code="mango",
        quantity_kg=500.0,
        harvest_at=now_utc - datetime.timedelta(hours=2),
        ambient_temp_c=30.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    db_session.add(batch)
    db_session.flush()

    asset = ColdAsset(
        operator_id=operator_user.id,
        name="Nashik Cold Vault",
        asset_type="STATIC",
        total_capacity_kg=5000.0,
        available_capacity_kg=5000.0,
        price_per_kg_per_day=1.5,
        latitude=20.0050,
        longitude=73.7950,
        is_active=True,
        data_source="LIVE"
    )
    db_session.add(asset)
    db_session.flush()
    db_session.add(StaticAssetDetail(
        asset_id=asset.id,
        supported_crops="mango",
        min_temperature_c=2.0,
        max_temperature_c=12.0
    ))
    db_session.commit()

    # Call endpoint with batch_id and asset_id
    res = client.get(
        f"/api/v1/maps/route?batch_id={batch.id}&asset_id={asset.id}",
        cookies=farmer_cookies
    )
    assert res.status_code == 200
    data = res.json()
    assert "distance_km" in data
    assert "duration_minutes" in data
    assert data["route_source"] in ["OSRM_ROUTES", "ESTIMATED"]

def test_reverse_geocode_endpoint(client, farmer_user):
    farmer_cookies = auth_cookies_for(farmer_user)
    res = client.get("/api/v1/maps/reverse-geocode?lat=19.9975&lng=73.7898", cookies=farmer_cookies)
    assert res.status_code == 200
    data = res.json()
    assert "address" in data
    assert data["latitude"] == 19.9975
    assert data["longitude"] == 73.7898
