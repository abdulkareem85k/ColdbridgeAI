import pytest
import datetime
from datetime import timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.seed.demo_data import seed_demo_data
from app.services.marketplace_service import calculate_sliding_discount

client = TestClient(app)
CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}

@pytest.fixture(autouse=True)
def run_around_tests():
    seed_demo_data()
    yield

def test_sliding_discount_calculation():
    """
    Verify sliding discount calculation:
    - At listed_at (progress 0): 10% discount
    - Halfway through window (progress 0.5): 30% discount
    - At expires_at (progress 1.0): 50% discount
    """
    now = datetime.datetime.now(timezone.utc)
    listed_at = now - timedelta(hours=10)
    expires_at = now + timedelta(hours=10) # 20 hours total window, 10 elapsed -> 50% progress

    # Exactly at start
    disc_start, price_start = calculate_sliding_discount(100.0, listed_at, expires_at, now=listed_at)
    assert disc_start == 10.0
    assert price_start == 90.0

    # Halfway
    disc_mid, price_mid = calculate_sliding_discount(100.0, listed_at, expires_at, now=now)
    assert disc_mid == 30.0
    assert price_mid == 70.0

    # At or beyond expiry
    disc_end, price_end = calculate_sliding_discount(100.0, listed_at, expires_at, now=expires_at)
    assert disc_end == 50.0
    assert price_end == 50.0


def test_unapproved_listing_blocked_from_marketplace():
    """
    Ensure listings that are PENDING_APPROVAL are NOT visible in the public marketplace
    and cannot be ordered by buyers.
    """
    # 1. Buyer logs in
    buyer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "buyer.demo@coldbridge.ai", "password": "BuyerDemo123!"},
        headers=CSRF_HEADER
    )
    assert buyer_login.status_code == 200
    buyer_cookies = buyer_login.cookies

    # 2. Get public marketplace listings
    res = client.get("/api/v1/marketplace/listings", cookies=buyer_cookies)
    assert res.status_code == 200
    listings = res.json()
    
    # Check that all returned listings have status 'APPROVED'
    for item in listings:
        assert item["status"] == "APPROVED"
        assert item["id"] != "lst00000-0000-0000-0000-000000000002" # Unapproved tomato listing

    # 3. Attempt direct order of unapproved listing lst00000-0000-0000-0000-000000000002
    order_res = client.post(
        "/api/v1/marketplace/orders",
        json={
            "listing_id": "lst00000-0000-0000-0000-000000000002",
            "quantity_kg": 50.0,
            "delivery_preference": "BUYER_PICKUP"
        },
        cookies=buyer_cookies,
        headers=CSRF_HEADER
    )
    assert order_res.status_code == 400
    assert "quality approval" in order_res.json()["detail"].lower()


def test_operator_approves_quality_unlocks_listing():
    """
    Operator quality inspection sign-off unlocks a PENDING_APPROVAL listing for buyers.
    """
    static_op_login = client.post(
        "/api/v1/auth/login",
        json={"email": "static.demo@coldbridge.ai", "password": "StaticDemo123!"},
        headers=CSRF_HEADER
    )
    assert static_op_login.status_code == 200
    op_cookies = static_op_login.cookies

    # Operator signs off on quality
    approve_res = client.post(
        "/api/v1/marketplace/listings/lst00000-0000-0000-0000-000000000002/approve",
        json={"quality_grade": "GRADE_A", "notes": "Visual check confirmed firm and intact"},
        cookies=op_cookies,
        headers=CSRF_HEADER
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"

    # Now buyer can see it in marketplace
    buyer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "buyer.demo@coldbridge.ai", "password": "BuyerDemo123!"},
        headers=CSRF_HEADER
    )
    res = client.get("/api/v1/marketplace/listings", cookies=buyer_login.cookies)
    ids = [x["id"] for x in res.json()]
    assert "lst00000-0000-0000-0000-000000000002" in ids


def test_order_exceeding_quantity_rejected():
    """
    Verify that ordering more quantity than available in a surplus listing is rejected (400).
    """
    buyer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "buyer.demo@coldbridge.ai", "password": "BuyerDemo123!"},
        headers=CSRF_HEADER
    )
    buyer_cookies = buyer_login.cookies

    # Approved listing lst00000-0000-0000-0000-000000000001 has 400 kg available
    order_res = client.post(
        "/api/v1/marketplace/orders",
        json={
            "listing_id": "lst00000-0000-0000-0000-000000000001",
            "quantity_kg": 500.0, # Exceeds 400.0 kg
            "delivery_preference": "BUYER_PICKUP"
        },
        cookies=buyer_cookies,
        headers=CSRF_HEADER
    )
    assert order_res.status_code == 400
    assert "exceeds available stock" in order_res.json()["detail"].lower()


def test_order_atomic_deduction_and_prevent_double_selling():
    """
    Test atomic stock decrement:
    Buyer orders 250 kg from 400 kg listing -> 150 kg remains.
    Second order for 200 kg is rejected because only 150 kg remains.
    """
    buyer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "buyer.demo@coldbridge.ai", "password": "BuyerDemo123!"},
        headers=CSRF_HEADER
    )
    buyer_cookies = buyer_login.cookies

    # Order 1: 250 kg
    order1 = client.post(
        "/api/v1/marketplace/orders",
        json={
            "listing_id": "lst00000-0000-0000-0000-000000000001",
            "quantity_kg": 250.0,
            "delivery_preference": "BUYER_PICKUP"
        },
        cookies=buyer_cookies,
        headers=CSRF_HEADER
    )
    assert order1.status_code == 200
    assert order1.json()["quantity_kg"] == 250.0
    assert order1.json()["status"] == "REQUESTED"

    # Order 2: 200 kg should now fail because only 150 kg remains!
    order2 = client.post(
        "/api/v1/marketplace/orders",
        json={
            "listing_id": "lst00000-0000-0000-0000-000000000001",
            "quantity_kg": 200.0,
            "delivery_preference": "BUYER_PICKUP"
        },
        cookies=buyer_cookies,
        headers=CSRF_HEADER
    )
    assert order2.status_code == 400
    assert "exceeds available stock" in order2.json()["detail"].lower()

    # Order 3: 150 kg should succeed and deplete stock
    order3 = client.post(
        "/api/v1/marketplace/orders",
        json={
            "listing_id": "lst00000-0000-0000-0000-000000000001",
            "quantity_kg": 150.0,
            "delivery_preference": "BUYER_PICKUP"
        },
        cookies=buyer_cookies,
        headers=CSRF_HEADER
    )
    assert order3.status_code == 200

    # Depleted listing should no longer appear in public marketplace
    res = client.get("/api/v1/marketplace/listings", cookies=buyer_cookies)
    ids = [x["id"] for x in res.json()]
    assert "lst00000-0000-0000-0000-000000000001" not in ids


def test_order_ownership_and_no_payment():
    """
    Verify order ownership checks:
    - Buyers see only their own orders
    - Order responses contain zero payment gateway / transaction ID fields
    """
    buyer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "buyer.demo@coldbridge.ai", "password": "BuyerDemo123!"},
        headers=CSRF_HEADER
    )
    buyer_cookies = buyer_login.cookies

    # Place an order
    order_res = client.post(
        "/api/v1/marketplace/orders",
        json={
            "listing_id": "lst00000-0000-0000-0000-000000000001",
            "quantity_kg": 50.0,
            "delivery_preference": "BUYER_PICKUP"
        },
        cookies=buyer_cookies,
        headers=CSRF_HEADER
    )
    assert order_res.status_code == 200
    order_data = order_res.json()

    # Verify absence of payment gateway fields
    assert "payment_gateway" not in order_data
    assert "stripe" not in str(order_data).lower()
    assert "razorpay" not in str(order_data).lower()
    assert "card" not in str(order_data).lower()

    # Get buyer orders
    my_orders = client.get("/api/v1/marketplace/orders", cookies=buyer_cookies)
    assert my_orders.status_code == 200
    assert len(my_orders.json()) >= 1
    for o in my_orders.json():
        assert o["buyer_id"] == "u1000000-0000-0000-0000-000000000099"
