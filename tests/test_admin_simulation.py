"""
Tests for M8A - Admin & Simulation Controls
"""

import pytest
from app.seed.demo_data import seed_demo_data

CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}


@pytest.fixture(autouse=True)
def seed_admin_test_data(db_session):
    seed_demo_data(db_session)


def test_admin_simulation_endpoints_and_rbac(client, db_session):
    """
    Test Admin simulation endpoints:
    - Non-admin forbidden (403)
    - Admin can reset demo data
    - Admin can update solar reliability simulation input
    - Admin can advance simulated clock
    - Admin stats dashboard returns correct counts and audit records
    """
    # 1. Non-admin (Farmer) is blocked
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    farmer_cookies = farmer_login.cookies

    res_blocked = client.post(
        "/api/v1/admin/reset-demo-data",
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert res_blocked.status_code == 403

    # 2. Login as Admin
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin.demo@coldbridge.ai", "password": "AdminDemo123!"},
        headers=CSRF_HEADER
    )
    assert admin_login.status_code == 200
    admin_cookies = admin_login.cookies

    # 3. Reset Demo Data
    reset_res = client.post(
        "/api/v1/admin/reset-demo-data",
        cookies=admin_cookies,
        headers=CSRF_HEADER
    )
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"
    assert reset_res.json()["data_source"] == "SIMULATED"

    # 4. Update Solar Reliability on Van Alpha
    van_id = "a2000000-0000-0000-0000-000000000001"
    solar_res = client.patch(
        f"/api/v1/admin/assets/{van_id}/solar-reliability",
        json={"solar_reliability": 0.5},
        cookies=admin_cookies,
        headers=CSRF_HEADER
    )
    assert solar_res.status_code == 200
    data = solar_res.json()
    assert data["solar_reliability"] == 0.5
    assert data["effective_capacity_kg"] == 400.0  # 800 * 0.5

    # 5. Advance Simulated Clock
    clock_res = client.post(
        "/api/v1/admin/advance-clock",
        json={"hours": 4},
        cookies=admin_cookies,
        headers=CSRF_HEADER
    )
    assert clock_res.status_code == 200
    assert clock_res.json()["hours_advanced"] == 4

    # 6. Admin Stats & Audit Logs
    stats_res = client.get(
        "/api/v1/admin/stats",
        cookies=admin_cookies,
        headers=CSRF_HEADER
    )
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "counts" in stats
    assert stats["counts"]["farmers"] >= 1
    assert stats["counts"]["static_rooms"] == 6
    assert stats["counts"]["mobile_vans"] == 4
    assert len(stats["recent_audit_logs"]) >= 1


def test_demand_forecast_honesty_and_labels(client, db_session):
    """
    Verify M8-B Demand Forecast endpoint:
    - Labelled as Rule-based seasonal estimate / Demo forecast
    - Contains horizon, data_source ('SIMULATED'), and data_status ('FRESH')
    - Does NOT contain confidence percentages or imply a trained ML model
    """
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    assert farmer_login.status_code == 200
    cookies = farmer_login.cookies

    res = client.get("/api/v1/forecast", cookies=cookies)
    assert res.status_code == 200
    forecasts = res.json()
    assert len(forecasts) >= 1

    for f in forecasts:
        assert f["data_source"] == "SIMULATED"
        assert f["data_status"] == "FRESH"
        assert f["forecast_source"] == "SEASONAL_RULE_BASED"
        assert "horizon_days" in f
        assert "confidence" not in f
        assert "probability" not in f


def test_admin_audit_logs_rbac_filtering_and_pagination(client, db_session):
    """
    Test GET /api/v1/admin/audit-logs:
    - 401 unauthenticated
    - 403 non-admin (FARMER)
    - 200 admin with total, items, available_actions, available_resource_types
    - Validation 422 for limit < 1, limit > 200, offset < 0
    - Action and resource_type filtering
    - Verification that no secrets or passwords leaked
    """
    # 1. Unauthenticated gets 401
    res_unauth = client.get("/api/v1/admin/audit-logs")
    assert res_unauth.status_code == 401

    # 2. Farmer gets 403
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    assert farmer_login.status_code == 200
    farmer_cookies = farmer_login.cookies

    res_forbidden = client.get("/api/v1/admin/audit-logs", cookies=farmer_cookies)
    assert res_forbidden.status_code == 403

    # 3. Admin gets 200
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin.demo@coldbridge.ai", "password": "AdminDemo123!"},
        headers=CSRF_HEADER
    )
    assert admin_login.status_code == 200
    admin_cookies = admin_login.cookies

    res_admin = client.get("/api/v1/admin/audit-logs", cookies=admin_cookies)
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert "total" in data
    assert "items" in data
    assert "available_actions" in data
    assert "available_resource_types" in data
    assert data["limit"] == 50
    assert data["offset"] == 0

    # 4. Check items format & secrets exclusion
    for item in data["items"]:
        assert "id" in item
        assert "action" in item
        assert "resource_type" in item
        assert "user_email" in item
        assert "details" in item
        if isinstance(item["details"], dict):
            for k, v in item["details"].items():
                assert "password" not in k.lower() or v == "[REDACTED]"
                assert "secret" not in k.lower() or v == "[REDACTED]"

    # 5. Validation 422
    res_invalid_limit_low = client.get("/api/v1/admin/audit-logs?limit=0", cookies=admin_cookies)
    assert res_invalid_limit_low.status_code == 422

    res_invalid_limit_high = client.get("/api/v1/admin/audit-logs?limit=250", cookies=admin_cookies)
    assert res_invalid_limit_high.status_code == 422

    res_invalid_offset = client.get("/api/v1/admin/audit-logs?offset=-5", cookies=admin_cookies)
    assert res_invalid_offset.status_code == 422

    # 6. Pagination & Filtering
    if len(data["available_actions"]) > 0:
        target_action = data["available_actions"][0]
        res_filter = client.get(f"/api/v1/admin/audit-logs?action={target_action}&limit=10", cookies=admin_cookies)
        assert res_filter.status_code == 200
        filtered_data = res_filter.json()
        for item in filtered_data["items"]:
            assert item["action"] == target_action
        assert filtered_data["limit"] == 10


