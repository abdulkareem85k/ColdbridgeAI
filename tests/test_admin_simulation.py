"""
Tests for M8A - Admin & Simulation Controls
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.asset import ColdAsset

client = TestClient(app)
CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}


def test_admin_simulation_endpoints_and_rbac():
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
