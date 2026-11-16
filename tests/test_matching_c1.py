"""
Tests for Correction Part 1 (C1):
- Allocation bug fix (real Bid persistence, no auto-... IDs)
- Matching request ownership verification
- Bid transparency (SIMULATED vs LIVE)
- Idempotent ranking & read-only GET
- Expired bid handling & post-allocation preservation
"""

import pytest
import datetime
from datetime import timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.matching import MatchingRequest, Bid
from app.models.asset import ColdAsset
from app.models.produce import ProduceBatch
from app.seed.demo_data import seed_demo_data

client = TestClient(app)
CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}


@pytest.fixture(autouse=True)
def reset_db():
    seed_demo_data()


def test_c1_brand_new_request_rank_and_allocate_no_seeded_bids():
    """
    1. Farmer creates batch -> creates matching request -> rank -> allocate -> RESERVED booking.
    With NO pre-seeded bids on this request.
    Verifies that real Bid rows are persisted with data_source='SIMULATED' and real UUIDs.
    """
    # 1. Login as Farmer Demo
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    assert login_res.status_code == 200
    cookies = login_res.cookies

    # 2. Create brand-new batch
    batch_res = client.post(
        "/api/v1/produce/batches",
        json={
            "crop_code": "TOMATO",
            "quantity_kg": 400.0,
            "latitude": 19.9975,
            "longitude": 73.7898,
            "ambient_temp_c": 32.0,
            "harvest_at": datetime.datetime.now(timezone.utc).isoformat()
        },
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert batch_res.status_code == 201
    batch_id = batch_res.json()["id"]

    # 3. Create matching request for this batch
    req_res = client.post(
        "/api/v1/matching/requests",
        json={"batch_id": batch_id, "requested_quantity_kg": 350.0},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # Verify no bids exist yet
    db = SessionLocal()
    bids_before = db.query(Bid).filter_by(request_id=req_id).all()
    assert len(bids_before) == 0
    db.close()

    # 4. Call POST /rank
    rank_res = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert rank_res.status_code == 200
    rank_data = rank_res.json()

    assert len(rank_data["ranked_offers"]) > 0
    winner_offer = rank_data["ranked_offers"][0]
    winner_bid_id = winner_offer["bid_id"]

    # Verify bid_id is a real UUID, not starting with auto-
    assert not winner_bid_id.startswith("auto-")
    assert winner_offer["data_source"] == "SIMULATED"
    assert winner_offer["is_persisted"] is True

    # Verify the bid is actually in the database
    db = SessionLocal()
    saved_bid = db.query(Bid).filter_by(id=winner_bid_id).first()
    assert saved_bid is not None
    assert saved_bid.data_source == "SIMULATED"
    assert saved_bid.offered_capacity_kg > 0
    assert saved_bid.price_total > 0
    assert saved_bid.valid_until is not None

    asset_before = db.query(ColdAsset).filter_by(id=winner_offer["asset_id"]).first()
    cap_before = asset_before.available_capacity_kg
    db.close()

    # 5. Allocate the rank-1 offer
    alloc_res = client.post(
        f"/api/v1/matching/requests/{req_id}/allocate",
        json={"bid_id": winner_bid_id, "days_estimated": 3},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert alloc_res.status_code == 201
    booking = alloc_res.json()
    assert booking["status"] == "RESERVED"
    assert booking["quantity_kg"] == 350.0

    # Verify asset capacity was reduced by exactly 350 kg
    db = SessionLocal()
    asset_after = db.query(ColdAsset).filter_by(id=winner_offer["asset_id"]).first()
    assert round(asset_after.available_capacity_kg, 2) == round(cap_before - 350.0, 2)

    # Verify bid status
    bids_after = db.query(Bid).filter_by(request_id=req_id).all()
    winning_bids = [b for b in bids_after if b.is_accepted]
    assert len(winning_bids) == 1
    assert winning_bids[0].id == winner_bid_id

    req_after = db.query(MatchingRequest).filter_by(id=req_id).first()
    assert req_after.status == "ALLOCATED"
    db.close()


def test_c1_idempotent_ranking_and_read_only_get():
    """
    Test that:
    - GET /requests/{id} is read-only (zero new DB rows).
    - POST /rank twice is idempotent (reuses active bids, no duplicate rows).
    """
    # 1. Login as Farmer
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    cookies = login_res.cookies

    # Create batch & request
    batch_res = client.post(
        "/api/v1/produce/batches",
        json={
            "crop_code": "MANGO",
            "quantity_kg": 300.0,
            "latitude": 19.9975,
            "longitude": 73.7898,
            "ambient_temp_c": 30.0,
            "harvest_at": datetime.datetime.now(timezone.utc).isoformat()
        },
        cookies=cookies,
        headers=CSRF_HEADER
    )
    batch_id = batch_res.json()["id"]

    req_res = client.post(
        "/api/v1/matching/requests",
        json={"batch_id": batch_id, "requested_quantity_kg": 200.0},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    req_id = req_res.json()["id"]

    # GET /requests/{id} twice before ranking
    get_res1 = client.get(f"/api/v1/matching/requests/{req_id}", cookies=cookies)
    assert get_res1.status_code == 200
    offers1 = get_res1.json()["ranking"]["ranked_offers"]
    # Check that in-memory preview is returned
    assert len(offers1) > 0
    assert offers1[0]["is_persisted"] is False
    assert offers1[0]["bid_id"].startswith("preview-")

    db = SessionLocal()
    count_after_get1 = db.query(Bid).filter_by(request_id=req_id).count()
    assert count_after_get1 == 0

    get_res2 = client.get(f"/api/v1/matching/requests/{req_id}", cookies=cookies)
    assert get_res2.status_code == 200
    count_after_get2 = db.query(Bid).filter_by(request_id=req_id).count()
    assert count_after_get2 == 0
    db.close()

    # Call POST /rank first time
    rank_res1 = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert rank_res1.status_code == 200

    db = SessionLocal()
    bids_run1 = db.query(Bid).filter_by(request_id=req_id).all()
    count_run1 = len(bids_run1)
    assert count_run1 > 0
    bid_ids_run1 = {b.id for b in bids_run1}
    db.close()

    # Call POST /rank second time (should be idempotent)
    rank_res2 = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert rank_res2.status_code == 200

    db = SessionLocal()
    bids_run2 = db.query(Bid).filter_by(request_id=req_id).all()
    assert len(bids_run2) == count_run1
    bid_ids_run2 = {b.id for b in bids_run2}
    assert bid_ids_run1 == bid_ids_run2
    db.close()


def test_c1_simulated_vs_live_operator_bids():
    """
    Operator-submitted bids must have data_source='LIVE', distinguishable from 'SIMULATED'.
    """
    # Farmer creates request
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    farmer_cookies = farmer_login.cookies

    req_res = client.post(
        "/api/v1/matching/requests",
        json={"batch_id": "b0000000-0000-0000-0000-000000000001", "requested_quantity_kg": 500.0},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    req_id = req_res.json()["id"]

    # Static Operator logs in
    op_login = client.post(
        "/api/v1/auth/login",
        json={"email": "static.demo@coldbridge.ai", "password": "StaticDemo123!"},
        headers=CSRF_HEADER
    )
    assert op_login.status_code == 200
    op_cookies = op_login.cookies

    # Submit a LIVE operator bid
    valid_until = (datetime.datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    submit_res = client.post(
        f"/api/v1/matching/requests/{req_id}/bids",
        json={
            "asset_id": "a1000000-0000-0000-0000-000000000001",
            "offered_capacity_kg": 500.0,
            "price_total": 920.0,
            "eta_minutes": 50.0,
            "valid_until": valid_until,
            "note": "Operator custom offer"
        },
        cookies=op_cookies,
        headers=CSRF_HEADER
    )
    assert submit_res.status_code == 201
    live_bid = submit_res.json()
    assert live_bid["data_source"] == "LIVE"

    # Farmer ranks offers
    rank_res = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert rank_res.status_code == 200
    offers = rank_res.json()["ranked_offers"]

    live_offers = [o for o in offers if o["asset_id"] == "a1000000-0000-0000-0000-000000000001"]
    other_offers = [o for o in offers if o["asset_id"] != "a1000000-0000-0000-0000-000000000001"]

    assert len(live_offers) == 1
    assert live_offers[0]["data_source"] == "LIVE"
    assert live_offers[0]["price_total"] == 920.0

    for o in other_offers:
        assert o["data_source"] == "SIMULATED"


def test_c1_post_allocation_preservation():
    """
    After allocation, accepted bid and ranking cannot be mutated by re-ranking or GET.
    """
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    cookies = farmer_login.cookies

    # Create new batch and request
    batch_res = client.post(
        "/api/v1/produce/batches",
        json={
            "crop_code": "GRAPES",
            "quantity_kg": 250.0,
            "latitude": 19.9975,
            "longitude": 73.7898,
            "ambient_temp_c": 28.0,
            "harvest_at": datetime.datetime.now(timezone.utc).isoformat()
        },
        cookies=cookies,
        headers=CSRF_HEADER
    )
    batch_id = batch_res.json()["id"]

    req_res = client.post(
        "/api/v1/matching/requests",
        json={"batch_id": batch_id, "requested_quantity_kg": 200.0},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    req_id = req_res.json()["id"]

    # Rank
    rank_res = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert rank_res.status_code == 200
    winning_bid_id = rank_res.json()["ranked_offers"][0]["bid_id"]

    # Allocate
    alloc_res = client.post(
        f"/api/v1/matching/requests/{req_id}/allocate",
        json={"bid_id": winning_bid_id, "days_estimated": 3},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert alloc_res.status_code == 201

    # Call rank again on allocated request
    rank_res_after = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert rank_res_after.status_code == 200
    data = rank_res_after.json()
    assert len(data["ranked_offers"]) == 1
    assert data["ranked_offers"][0]["bid_id"] == winning_bid_id

    # Call GET on allocated request
    get_res = client.get(
        f"/api/v1/matching/requests/{req_id}",
        cookies=cookies
    )
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert len(get_data["ranking"]["ranked_offers"]) == 1
    assert get_data["ranking"]["ranked_offers"][0]["bid_id"] == winning_bid_id


def test_c1_expired_bids_handling():
    """
    Expired bids (is_expired or valid_until < now) are rejected from allocation.
    """
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    cookies = farmer_login.cookies

    # Create new batch and request
    batch_res = client.post(
        "/api/v1/produce/batches",
        json={
            "crop_code": "TOMATO",
            "quantity_kg": 300.0,
            "latitude": 19.9975,
            "longitude": 73.7898,
            "ambient_temp_c": 32.0,
            "harvest_at": datetime.datetime.now(timezone.utc).isoformat()
        },
        cookies=cookies,
        headers=CSRF_HEADER
    )
    batch_id = batch_res.json()["id"]

    req_res = client.post(
        "/api/v1/matching/requests",
        json={"batch_id": batch_id, "requested_quantity_kg": 200.0},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    req_id = req_res.json()["id"]

    # Rank to persist bids
    rank_res = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert rank_res.status_code == 200
    bid_id = rank_res.json()["ranked_offers"][0]["bid_id"]

    # Expire this bid in DB
    db = SessionLocal()
    bid = db.query(Bid).filter_by(id=bid_id).first()
    bid.valid_until = datetime.datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()
    db.close()

    # Attempt to allocate the expired bid directly -> should fail with 400
    alloc_res = client.post(
        f"/api/v1/matching/requests/{req_id}/allocate",
        json={"bid_id": bid_id, "days_estimated": 3},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert alloc_res.status_code == 400
    assert "expired" in alloc_res.json()["detail"].lower()


def test_c1_matching_ownership_authorization():
    """
    Farmer B cannot view or rank Farmer A's request.
    Operator with no bid cannot view request.
    Admin can view request.
    """
    # 1. Register Farmer B
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "farmer.b@coldbridge.ai",
            "password": "FarmerBPass123!",
            "full_name": "Farmer B",
            "role": "FARMER"
        },
        headers=CSRF_HEADER
    )
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.b@coldbridge.ai", "password": "FarmerBPass123!"},
        headers=CSRF_HEADER
    )
    cookies_b = login_b.cookies

    # Farmer A's request
    req_id = "mr000000-0000-0000-0000-000000000001"

    # Farmer B attempts to rank Farmer A's request -> 403
    rank_res = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=cookies_b,
        headers=CSRF_HEADER
    )
    assert rank_res.status_code == 403

    # Farmer B attempts to get Farmer A's request -> 403
    get_res = client.get(
        f"/api/v1/matching/requests/{req_id}",
        cookies=cookies_b
    )
    assert get_res.status_code == 403

    # Admin logs in -> can access
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin.demo@coldbridge.ai", "password": "AdminDemo123!"},
        headers=CSRF_HEADER
    )
    admin_cookies = admin_login.cookies
    admin_get = client.get(
        f"/api/v1/matching/requests/{req_id}",
        cookies=admin_cookies
    )
    assert admin_get.status_code == 200
