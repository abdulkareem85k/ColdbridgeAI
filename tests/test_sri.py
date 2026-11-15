import datetime
from datetime import timezone
import pytest
from app.services.sri_engine import calculate_sri
from tests.conftest import auth_cookies_for

def test_sri_engine_crop_classes():
    # 1. Low perishability crop: Onion at 25°C, 10h
    onion_sri = calculate_sri("onion", hours_since_harvest=10.0, ambient_temp_c=25.0)
    assert onion_sri["risk_category"] == "LOW"
    assert onion_sri["score"] < 35.0
    assert onion_sri["rule_version"] == "prototype-1"
    assert len(onion_sri["reasons"]) >= 2

    # 2. Extreme perishability crop: Cashew Apple at 35°C (high heat stress), 15h
    cashew_sri = calculate_sri("cashew_apple", hours_since_harvest=15.0, ambient_temp_c=35.0)
    assert cashew_sri["risk_category"] == "HIGH"
    assert cashew_sri["score"] >= 65.0

    # 3. Very high perishability: Tomato at 32°C, 20h
    tomato_sri = calculate_sri("tomato", hours_since_harvest=20.0, ambient_temp_c=32.0)
    assert tomato_sri["risk_category"] in ["HIGH", "MEDIUM"]
    assert tomato_sri["score"] > 35.0

def test_sri_boundary_and_invalid_inputs():
    # Negative hours
    with pytest.raises(ValueError, match="Hours since harvest cannot be negative"):
        calculate_sri("mango", hours_since_harvest=-5.0, ambient_temp_c=25.0)

    # Impossible temperature
    with pytest.raises(ValueError, match="outside realistic range"):
        calculate_sri("mango", hours_since_harvest=10.0, ambient_temp_c=85.0)

    # Unknown crop
    with pytest.raises(ValueError, match="Unknown or unsupported crop code"):
        calculate_sri("unknown_exotic_fruit", hours_since_harvest=10.0, ambient_temp_c=25.0)

def test_sri_determinism():
    run1 = calculate_sri("mango", hours_since_harvest=8.5, ambient_temp_c=33.0)
    run2 = calculate_sri("mango", hours_since_harvest=8.5, ambient_temp_c=33.0)
    assert run1["score"] == run2["score"]
    assert run1["risk_category"] == run2["risk_category"]
    assert run1["reasons"] == run2["reasons"]
    assert run1["factors"] == run2["factors"]

def test_sri_api_endpoints_and_priority_queue(client, farmer_user, operator_user, db_session):
    from app.models.produce import ProduceBatch
    now_utc = datetime.datetime.now(timezone.utc)
    farmer_cookies = auth_cookies_for(farmer_user)
    op_cookies = auth_cookies_for(operator_user)

    # Create two batches: one urgent, one fresh
    urgent_batch = ProduceBatch(
        farmer_id=farmer_user.id,
        crop_code="tomato",
        quantity_kg=800.0,
        harvest_at=now_utc - datetime.timedelta(hours=22),
        ambient_temp_c=36.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    fresh_batch = ProduceBatch(
        farmer_id=farmer_user.id,
        crop_code="onion",
        quantity_kg=1200.0,
        harvest_at=now_utc - datetime.timedelta(hours=2),
        ambient_temp_c=26.0,
        latitude=19.9800,
        longitude=73.7700,
        data_source="LIVE"
    )
    db_session.add_all([urgent_batch, fresh_batch])
    db_session.commit()

    CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}

    # 1. Trigger calculation for urgent batch
    res_calc = client.post(f"/api/v1/sri/{urgent_batch.id}/calculate", cookies=farmer_cookies, headers=CSRF_HEADER)
    assert res_calc.status_code == 200
    data_calc = res_calc.json()
    assert data_calc["rule_version"] == "prototype-1"
    assert "reasons" in data_calc
    assert "recommended_action" in data_calc

    # 2. Get batch SRI
    res_get = client.get(f"/api/v1/sri/{urgent_batch.id}", cookies=farmer_cookies)
    assert res_get.status_code == 200
    assert res_get.json()["score"] == data_calc["score"]

    # 3. Check Priority Queue: operator retrieves queue sorted descending by SRI
    res_queue = client.get("/api/v1/sri/priority-queue", cookies=op_cookies)
    assert res_queue.status_code == 200
    queue = res_queue.json()
    assert len(queue) >= 2
    # Check descending sort order
    scores = [item["score"] for item in queue]
    assert scores == sorted(scores, reverse=True)
