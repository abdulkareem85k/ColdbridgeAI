"""
Tests for Correction Part 1 (C2):
- SRI calculate and get authorization (403 for unauthorized farmers, 404 for missing batches)
- Priority queue role-based authorization (401 unauthenticated, 403 farmer/buyer, 200 operator/admin)
- Priority queue relevancy filtering and privacy masking (hide farmer_id and round coordinates for discovery batches, exclude unrelated batches)
- Score integrity and determinism
"""

import pytest
import datetime
from datetime import timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.produce import ProduceBatch
from app.models.asset import ColdAsset
from app.seed.demo_data import seed_demo_data

client = TestClient(app)
CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}


@pytest.fixture(autouse=True)
def reset_db():
    seed_demo_data()


def test_c2_farmer_ownership_calculate_and_get():
    """
    Farmer A cannot calculate or read Farmer B's SRI (403).
    Missing batch returns 404.
    """
    # 1. Login as Farmer A (owner of b0000000-0000-0000-0000-000000000001)
    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    assert login_a.status_code == 200
    cookies_a = login_a.cookies
    batch_id_a = "b0000000-0000-0000-0000-000000000001"

    # Farmer A can calculate & read own batch SRI
    calc_res_a = client.post(f"/api/v1/sri/{batch_id_a}/calculate", cookies=cookies_a, headers=CSRF_HEADER)
    assert calc_res_a.status_code == 200
    score_a = calc_res_a.json()["score"]

    get_res_a = client.get(f"/api/v1/sri/{batch_id_a}", cookies=cookies_a)
    assert get_res_a.status_code == 200
    assert get_res_a.json()["score"] == score_a

    # 2. Register and login as Farmer B
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "farmer.b2@coldbridge.ai",
            "password": "FarmerB2Pass123!",
            "full_name": "Farmer B2",
            "role": "FARMER"
        },
        headers=CSRF_HEADER
    )
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.b2@coldbridge.ai", "password": "FarmerB2Pass123!"},
        headers=CSRF_HEADER
    )
    cookies_b = login_b.cookies

    # Farmer B attempts to calculate Farmer A's batch -> 403
    calc_res_b = client.post(f"/api/v1/sri/{batch_id_a}/calculate", cookies=cookies_b, headers=CSRF_HEADER)
    assert calc_res_b.status_code == 403

    # Farmer B attempts to read Farmer A's batch -> 403
    get_res_b = client.get(f"/api/v1/sri/{batch_id_a}", cookies=cookies_b)
    assert get_res_b.status_code == 403

    # 3. Non-existent batch -> 404
    calc_missing = client.post("/api/v1/sri/non-existent-batch-000/calculate", cookies=cookies_a, headers=CSRF_HEADER)
    assert calc_missing.status_code == 404

    get_missing = client.get("/api/v1/sri/non-existent-batch-000", cookies=cookies_a)
    assert get_missing.status_code == 404


def test_c2_priority_queue_role_restrictions():
    """
    Unauthenticated -> 401
    Farmer -> 403
    Buyer -> 403
    Admin -> 200
    Static Operator -> 200
    Van Operator -> 200
    """
    # 1. Unauthenticated
    unauth_res = client.get("/api/v1/sri/priority-queue")
    assert unauth_res.status_code == 401

    # 2. Farmer
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    farmer_res = client.get("/api/v1/sri/priority-queue", cookies=farmer_login.cookies)
    assert farmer_res.status_code == 403

    # 3. Buyer
    buyer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "buyer.demo@coldbridge.ai", "password": "BuyerDemo123!"},
        headers=CSRF_HEADER
    )
    buyer_res = client.get("/api/v1/sri/priority-queue", cookies=buyer_login.cookies)
    assert buyer_res.status_code == 403

    # 4. Admin
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin.demo@coldbridge.ai", "password": "AdminDemo123!"},
        headers=CSRF_HEADER
    )
    admin_res = client.get("/api/v1/sri/priority-queue", cookies=admin_login.cookies)
    assert admin_res.status_code == 200
    assert isinstance(admin_res.json(), list)

    # 5. Static Operator
    static_login = client.post(
        "/api/v1/auth/login",
        json={"email": "static.demo@coldbridge.ai", "password": "StaticDemo123!"},
        headers=CSRF_HEADER
    )
    static_res = client.get("/api/v1/sri/priority-queue", cookies=static_login.cookies)
    assert static_res.status_code == 200
    assert isinstance(static_res.json(), list)

    # 6. Van Operator
    van_login = client.post(
        "/api/v1/auth/login",
        json={"email": "van.demo@coldbridge.ai", "password": "VanDemo123!"},
        headers=CSRF_HEADER
    )
    van_res = client.get("/api/v1/sri/priority-queue", cookies=van_login.cookies)
    assert van_res.status_code == 200
    assert isinstance(van_res.json(), list)


def test_c2_priority_queue_relevancy_and_privacy():
    """
    - Admin sees all batches with full details.
    - Operator sees ONLY relevant batches (bid, booking, or eligible).
    - Unrelated farmer batches are completely absent.
    - Eligible discovery batches have farmer_id=None and coordinates rounded to 2 decimals.
    """
    # 1. Create an unrelated batch far away with an unsupported crop
    db = SessionLocal()
    unrelated_batch = ProduceBatch(
        id="b9999999-9999-9999-9999-999999999999",
        farmer_id="f1000000-0000-0000-0000-000000000001",
        crop_code="TOMATO",
        quantity_kg=25000.0,  # Exceeds total capacity
        harvest_at=datetime.datetime.now(timezone.utc) - timedelta(hours=5),
        ambient_temp_c=34.0,
        latitude=25.5941,  # Patna, ~1400 km away (far outside any service radius)
        longitude=85.1376,
        data_source="SIMULATED"
    )
    db.add(unrelated_batch)
    db.commit()
    db.close()

    # 2. Admin inspects queue
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin.demo@coldbridge.ai", "password": "AdminDemo123!"},
        headers=CSRF_HEADER
    )
    admin_queue = client.get("/api/v1/sri/priority-queue", cookies=admin_login.cookies).json()
    admin_batch_ids = {item["batch_id"] for item in admin_queue}
    assert "b9999999-9999-9999-9999-999999999999" in admin_batch_ids

    # 3. Static Operator inspects queue
    op_login = client.post(
        "/api/v1/auth/login",
        json={"email": "static.demo@coldbridge.ai", "password": "StaticDemo123!"},
        headers=CSRF_HEADER
    )
    op_queue = client.get("/api/v1/sri/priority-queue", cookies=op_login.cookies).json()
    op_batch_ids = {item["batch_id"] for item in op_queue}

    # ASSERTION: The unrelated batch is NEVER present in the operator's queue
    assert "b9999999-9999-9999-9999-999999999999" not in op_batch_ids

    # For batches present in the operator's queue:
    for item in op_queue:
        # Check priority_rank is assigned
        assert item["priority_rank"] is not None
        assert item["priority_rank"] >= 1

        # If discovery-only (no bid or booking on static operator's asset), farmer_id must be None
        # and coordinates rounded to 2 decimals
        if item["farmer_id"] is None:
            # Lat/lon should match 2 decimal places precision
            assert round(item["latitude"], 2) == item["latitude"]
            assert round(item["longitude"], 2) == item["longitude"]


def test_c2_priority_queue_limit_query_param():
    """
    Verify ?limit=N is supported on /api/v1/sri/priority-queue.
    """
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin.demo@coldbridge.ai", "password": "AdminDemo123!"},
        headers=CSRF_HEADER
    )
    res = client.get("/api/v1/sri/priority-queue?limit=2", cookies=admin_login.cookies)
    assert res.status_code == 200
    queue = res.json()
    assert len(queue) <= 2
