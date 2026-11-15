import datetime
from datetime import timezone
import pytest
from tests.conftest import auth_cookies_for

CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}

def test_produce_batch_crud_and_validation(client, farmer_user, operator_user):
    farmer_cookies = auth_cookies_for(farmer_user)
    now_utc = datetime.datetime.now(timezone.utc)

    # 1. Valid batch creation
    valid_payload = {
        "crop_code": "mango",
        "quantity_kg": 500.0,
        "harvest_at": (now_utc - datetime.timedelta(hours=2)).isoformat(),
        "ambient_temp_c": 32.0,
        "latitude": 19.9975,
        "longitude": 73.7898,
        "notes": "Alphonso test batch"
    }
    res = client.post("/api/v1/produce/batches", json=valid_payload, cookies=farmer_cookies, headers=CSRF_HEADER)
    assert res.status_code == 201
    batch_data = res.json()
    assert batch_data["crop_code"] == "mango"
    assert batch_data["quantity_kg"] == 500.0
    assert batch_data["data_source"] == "LIVE"
    batch_id = batch_data["id"]

    # 2. Invalid quantity <= 0 rejected
    invalid_qty_payload = valid_payload.copy()
    invalid_qty_payload["quantity_kg"] = 0
    res_bad_qty = client.post("/api/v1/produce/batches", json=invalid_qty_payload, cookies=farmer_cookies, headers=CSRF_HEADER)
    assert res_bad_qty.status_code == 422

    # 3. Future harvest time rejected
    future_payload = valid_payload.copy()
    future_payload["harvest_at"] = (now_utc + datetime.timedelta(days=2)).isoformat()
    res_future = client.post("/api/v1/produce/batches", json=future_payload, cookies=farmer_cookies, headers=CSRF_HEADER)
    assert res_future.status_code == 422

    # 4. Farmer gets their batches
    list_res = client.get("/api/v1/produce/batches", cookies=farmer_cookies)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 5. Get single batch
    single_res = client.get(f"/api/v1/produce/batches/{batch_id}", cookies=farmer_cookies)
    assert single_res.status_code == 200
    assert single_res.json()["id"] == batch_id

    # 6. Another user cannot view private batch
    operator_cookies = auth_cookies_for(operator_user)
    forbidden_res = client.get(f"/api/v1/produce/batches/{batch_id}", cookies=operator_cookies)
    assert forbidden_res.status_code == 403

def test_cooling_assets_crud_and_capacity_rules(client, operator_user, van_operator_user, farmer_user):
    op_cookies = auth_cookies_for(operator_user)
    van_cookies = auth_cookies_for(van_operator_user)

    # 1. Register Static Room
    static_payload = {
        "name": "Pune Test Cold Vault",
        "asset_type": "STATIC",
        "total_capacity_kg": 5000.0,
        "available_capacity_kg": 4000.0,
        "price_per_kg_per_day": 1.5,
        "latitude": 18.5204,
        "longitude": 73.8567,
        "static_detail": {
            "supported_crops": "tomato, onion, mango",
            "min_temperature_c": 2.0,
            "max_temperature_c": 12.0,
            "address": "Hadapsar, Pune"
        }
    }
    res_static = client.post("/api/v1/assets", json=static_payload, cookies=op_cookies, headers=CSRF_HEADER)
    assert res_static.status_code == 201
    static_asset = res_static.json()
    assert static_asset["name"] == "Pune Test Cold Vault"
    assert static_asset["data_status"] == "FRESH"
    asset_id = static_asset["id"]

    # 2. Register Mobile Van
    van_payload = {
        "name": "SolarVan Test Alpha",
        "asset_type": "MOBILE",
        "total_capacity_kg": 1000.0,
        "available_capacity_kg": 1000.0,
        "price_per_kg_per_day": 2.2,
        "latitude": 20.0100,
        "longitude": 73.7800,
        "mobile_detail": {
            "vehicle_ref": "MH-15-XY-9999",
            "service_radius_km": 50.0,
            "solar_reliability": 0.90,
            "last_location_at": datetime.datetime.now(timezone.utc).isoformat()
        }
    }
    res_van = client.post("/api/v1/assets", json=van_payload, cookies=van_cookies, headers=CSRF_HEADER)
    assert res_van.status_code == 201
    van_asset = res_van.json()
    assert van_asset["mobile_detail"]["vehicle_ref"] == "MH-15-XY-9999"
    assert van_asset["data_status"] == "FRESH"

    # 3. Capacity bounds checking: cannot set available > total
    cap_bad_res = client.patch(
        f"/api/v1/assets/{asset_id}/availability",
        json={"available_capacity_kg": 6000.0},
        cookies=op_cookies,
        headers=CSRF_HEADER
    )
    assert cap_bad_res.status_code == 400
    assert "cannot exceed total capacity" in cap_bad_res.json()["detail"]

    # 4. Capacity bounds checking: cannot set available < 0
    cap_neg_res = client.patch(
        f"/api/v1/assets/{asset_id}/availability",
        json={"available_capacity_kg": -10.0},
        cookies=op_cookies,
        headers=CSRF_HEADER
    )
    assert cap_neg_res.status_code == 422 or cap_neg_res.status_code == 400

    # 5. Valid capacity update
    cap_ok_res = client.patch(
        f"/api/v1/assets/{asset_id}/availability",
        json={"available_capacity_kg": 2500.0, "is_active": True},
        cookies=op_cookies,
        headers=CSRF_HEADER
    )
    assert cap_ok_res.status_code == 200
    assert cap_ok_res.json()["available_capacity_kg"] == 2500.0

    # 6. Another operator cannot edit this asset (Ownership check)
    forbidden_edit = client.patch(
        f"/api/v1/assets/{asset_id}/availability",
        json={"available_capacity_kg": 1000.0},
        cookies=van_cookies,
        headers=CSRF_HEADER
    )
    assert forbidden_edit.status_code == 403
    assert "Forbidden: You do not own this cooling asset" in forbidden_edit.json()["detail"]
