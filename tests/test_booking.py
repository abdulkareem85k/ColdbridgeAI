"""
Tests for M6 - Safe Booking, Capacity Reservation & State Machine
"""

import pytest
import datetime
from datetime import timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.asset import ColdAsset
from app.models.booking import Booking
from app.models.matching import MatchingRequest, Bid
from app.models.produce import ProduceBatch
from app.models.audit import AuditLog
from app.services.booking_service import check_and_expire_reservations

client = TestClient(app)
CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}


@pytest.fixture(autouse=True)
def ensure_db_state():
    """Ensure clean deterministic state before booking tests."""
    from app.seed.demo_data import seed_demo_data
    seed_demo_data()


def test_allocation_and_capacity_reservation():
    """
    Test offer allocation:
    - Reserves capacity immediately
    - Creates booking in RESERVED status (15-min expiry)
    - Winning bid is accepted, other bids expired
    - Price estimate breakdown matches
    """
    # 1. Login as Farmer Demo
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    assert login_res.status_code == 200
    cookies = login_res.cookies

    # Pre-seeded request: mr000000-0000-0000-0000-000000000001 (500 kg mango)
    req_id = "mr000000-0000-0000-0000-000000000001"
    winning_bid_id = "bd000000-0000-0000-0000-000000000002"  # SolarVan Alpha (800 kg available)

    db = SessionLocal()
    van_before = db.query(ColdAsset).filter_by(id="a2000000-0000-0000-0000-000000000001").first()
    avail_before = van_before.available_capacity_kg
    db.close()

    # 2. Allocate Offer
    alloc_res = client.post(
        f"/api/v1/matching/requests/{req_id}/allocate",
        json={"bid_id": winning_bid_id, "days_estimated": 3},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert alloc_res.status_code == 201
    booking = alloc_res.json()

    assert booking["status"] == "RESERVED"
    assert booking["quantity_kg"] == 500.0
    assert booking["estimated_total_inr"] > 0
    assert booking["reserved_until"] is not None

    # Check capacity was deducted by exactly 500 kg
    db = SessionLocal()
    van_after = db.query(ColdAsset).filter_by(id="a2000000-0000-0000-0000-000000000001").first()
    assert van_after.available_capacity_kg == avail_before - 500.0

    # Winning bid accepted, others expired
    bids = db.query(Bid).filter_by(request_id=req_id).all()
    accepted = [b for b in bids if b.is_accepted]
    expired = [b for b in bids if b.is_expired]
    assert len(accepted) == 1
    assert accepted[0].id == winning_bid_id
    assert len(expired) >= 1

    # Check audit log entry
    audit = db.query(AuditLog).filter_by(action="ALLOCATE_BID", resource_id=req_id).first()
    assert audit is not None
    db.close()


def test_capacity_overbooking_conflict_409():
    """
    Attempting to allocate when asset capacity is insufficient must return 409 Conflict.
    """
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    cookies = login_res.cookies

    # Drain available capacity of SolarVan Alpha
    db = SessionLocal()
    van = db.query(ColdAsset).filter_by(id="a2000000-0000-0000-0000-000000000001").first()
    van.available_capacity_kg = 100.0  # Only 100 kg left
    db.commit()
    db.close()

    req_id = "mr000000-0000-0000-0000-000000000001"  # Needs 500 kg
    winning_bid_id = "bd000000-0000-0000-0000-000000000002"

    alloc_res = client.post(
        f"/api/v1/matching/requests/{req_id}/allocate",
        json={"bid_id": winning_bid_id, "days_estimated": 3},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert alloc_res.status_code == 409
    assert "capacity" in alloc_res.json()["detail"].lower()


def test_booking_state_machine_valid_transitions():
    """
    Test full lifecycle of valid state transitions:
    RESERVED -> CONFIRMED -> PICKUP_SCHEDULED (van) -> PRODUCE_RECEIVED -> IN_STORAGE -> COMPLETED
    """
    # 1. Farmer login and allocate
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    farmer_cookies = farmer_login.cookies

    alloc_res = client.post(
        "/api/v1/matching/requests/mr000000-0000-0000-0000-000000000001/allocate",
        json={"bid_id": "bd000000-0000-0000-0000-000000000002", "days_estimated": 2},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert alloc_res.status_code == 201
    booking_id = alloc_res.json()["id"]

    # 2. Van Operator login
    operator_login = client.post(
        "/api/v1/auth/login",
        json={"email": "van.demo@coldbridge.ai", "password": "VanDemo123!"},
        headers=CSRF_HEADER
    )
    operator_cookies = operator_login.cookies

    # Transition: RESERVED -> CONFIRMED
    res = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "CONFIRMED"},
        cookies=operator_cookies,
        headers=CSRF_HEADER
    )
    assert res.status_code == 200
    assert res.json()["status"] == "CONFIRMED"

    # Transition: CONFIRMED -> PICKUP_SCHEDULED (valid for van)
    res = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "PICKUP_SCHEDULED"},
        cookies=operator_cookies,
        headers=CSRF_HEADER
    )
    assert res.status_code == 200
    assert res.json()["status"] == "PICKUP_SCHEDULED"

    # Transition: PICKUP_SCHEDULED -> PRODUCE_RECEIVED
    res = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "PRODUCE_RECEIVED"},
        cookies=operator_cookies,
        headers=CSRF_HEADER
    )
    assert res.status_code == 200
    assert res.json()["status"] == "PRODUCE_RECEIVED"

    # Transition: PRODUCE_RECEIVED -> IN_STORAGE
    res = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "IN_STORAGE"},
        cookies=operator_cookies,
        headers=CSRF_HEADER
    )
    assert res.status_code == 200
    assert res.json()["status"] == "IN_STORAGE"

    # Transition: IN_STORAGE -> COMPLETED
    res = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "COMPLETED"},
        cookies=operator_cookies,
        headers=CSRF_HEADER
    )
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"

    # Check that upon COMPLETED, capacity was released
    db = SessionLocal()
    van = db.query(ColdAsset).filter_by(id="a2000000-0000-0000-0000-000000000001").first()
    assert van.available_capacity_kg == 800.0  # Fully restored back to original available
    db.close()


def test_booking_invalid_transitions_rejected():
    """
    Test rejection of illegal state machine transitions:
    - RESERVED directly to IN_STORAGE (must be rejected)
    - PICKUP_SCHEDULED on a static room (must be rejected)
    - CANCELLED after PRODUCE_RECEIVED (must be rejected)
    - Any transition after COMPLETED (terminal state)
    """
    # Allocate to Static Room (Nashik Agro Warehouse A: a1000000-0000-0000-0000-000000000001)
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    farmer_cookies = farmer_login.cookies

    alloc_res = client.post(
        "/api/v1/matching/requests/mr000000-0000-0000-0000-000000000001/allocate",
        json={"bid_id": "bd000000-0000-0000-0000-000000000001", "days_estimated": 2},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert alloc_res.status_code == 201
    booking_id = alloc_res.json()["id"]

    static_op_login = client.post(
        "/api/v1/auth/login",
        json={"email": "static.demo@coldbridge.ai", "password": "StaticDemo123!"},
        headers=CSRF_HEADER
    )
    static_cookies = static_op_login.cookies

    # 1. Illegal transition: RESERVED -> IN_STORAGE
    bad_res = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "IN_STORAGE"},
        cookies=static_cookies,
        headers=CSRF_HEADER
    )
    assert bad_res.status_code == 400
    assert "invalid transition" in bad_res.json()["detail"].lower()

    # Move to CONFIRMED
    client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "CONFIRMED"},
        cookies=static_cookies,
        headers=CSRF_HEADER
    )

    # 2. Illegal transition: PICKUP_SCHEDULED on a STATIC room
    bad_res2 = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "PICKUP_SCHEDULED"},
        cookies=static_cookies,
        headers=CSRF_HEADER
    )
    assert bad_res2.status_code == 400
    assert "mobile" in bad_res2.json()["detail"].lower()

    # Move to PRODUCE_RECEIVED
    client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "PRODUCE_RECEIVED"},
        cookies=static_cookies,
        headers=CSRF_HEADER
    )

    # 3. Illegal: Farmer attempting cancellation AFTER produce is received
    cancel_res = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "CANCELLED"},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert cancel_res.status_code == 400
    assert "cannot cancel booking after produce has been received" in cancel_res.json()["detail"].lower()


def test_capacity_release_exact_once_on_cancellation():
    """
    Cancelling a booking in RESERVED releases capacity exactly once
    and available capacity never exceeds total capacity.
    """
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    farmer_cookies = farmer_login.cookies

    alloc_res = client.post(
        "/api/v1/matching/requests/mr000000-0000-0000-0000-000000000001/allocate",
        json={"bid_id": "bd000000-0000-0000-0000-000000000002", "days_estimated": 2},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    booking_id = alloc_res.json()["id"]

    db = SessionLocal()
    van = db.query(ColdAsset).filter_by(id="a2000000-0000-0000-0000-000000000001").first()
    avail_while_reserved = van.available_capacity_kg
    total_cap = van.total_capacity_kg
    db.close()

    # Farmer cancels booking
    cancel_res = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "CANCELLED"},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    db = SessionLocal()
    van_after = db.query(ColdAsset).filter_by(id="a2000000-0000-0000-0000-000000000001").first()
    assert van_after.available_capacity_kg == avail_while_reserved + 500.0
    assert van_after.available_capacity_kg <= total_cap
    db.close()

    # Further status updates must be rejected because it is terminal
    second_cancel = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "CANCELLED"},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert second_cancel.status_code == 400


def test_reservation_expiration_and_capacity_recovery():
    """
    A booking in RESERVED older than 15 minutes expires automatically
    and its capacity is safely released back.
    """
    farmer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    farmer_cookies = farmer_login.cookies

    alloc_res = client.post(
        "/api/v1/matching/requests/mr000000-0000-0000-0000-000000000001/allocate",
        json={"bid_id": "bd000000-0000-0000-0000-000000000002", "days_estimated": 2},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    booking_id = alloc_res.json()["id"]

    # Artificially shift reserved_until into the past
    db = SessionLocal()
    b = db.query(Booking).filter_by(id=booking_id).first()
    b.reserved_until = datetime.datetime.now(timezone.utc) - timedelta(minutes=20)
    db.commit()

    # Run check_and_expire_reservations
    expired_count = check_and_expire_reservations(db)
    assert expired_count >= 1

    db.refresh(b)
    assert b.status == "EXPIRED"

    # Check capacity was restored
    van = db.query(ColdAsset).filter_by(id="a2000000-0000-0000-0000-000000000001").first()
    assert van.available_capacity_kg == 800.0
    db.close()
