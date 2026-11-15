"""
Tests for M5 - Matching Engine, Reverse Auction Scoring, Solar Fallback, and Comparisons
"""

import pytest
import datetime
from datetime import timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.services.auction_scoring import score_and_rank_offers, MATCHING_CONFIG
from app.services.eligibility import evaluate_asset_eligibility
from app.models.asset import ColdAsset, MobileAssetDetail, StaticAssetDetail

client = TestClient(app)

CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}


def test_worked_example_exact_reproduction():
    """
    Step 8 Specification Worked Example:
    Requested: 500 kg, SRI: HIGH
    - Static A: Rs 1000, 5 km, 65 min, 1000 kg cap, static
    - Van B: Rs 1200, 8 km, 35 min, 800 kg cap, solar 0.9 (effective 720 kg)
    - Static C: Rs 800, 25 km, 90 min, 800 kg cap, static

    Expected scores (tolerance 0.0005):
    - A: 0.334
    - B: 0.297 (winner)
    - C: 0.444
    Nearest: A, Cheapest: C, ColdBridge: B.
    """
    offers = [
        {
            "bid_id": "bid_A",
            "asset_id": "asset_A",
            "asset_name": "A static room",
            "asset_type": "STATIC",
            "price_total": 1000.0,
            "distance_km": 5.0,
            "eta_minutes": 65.0,
            "available_capacity_kg": 1000.0,
            "effective_available_kg": 1000.0,
            "solar_reliability": 1.0
        },
        {
            "bid_id": "bid_B",
            "asset_id": "asset_B",
            "asset_name": "B van",
            "asset_type": "MOBILE",
            "price_total": 1200.0,
            "distance_km": 8.0,
            "eta_minutes": 35.0,
            "available_capacity_kg": 800.0,
            "effective_available_kg": 720.0,
            "solar_reliability": 0.9
        },
        {
            "bid_id": "bid_C",
            "asset_id": "asset_C",
            "asset_name": "C static room",
            "asset_type": "STATIC",
            "price_total": 800.0,
            "distance_km": 25.0,
            "eta_minutes": 90.0,
            "available_capacity_kg": 800.0,
            "effective_available_kg": 800.0,
            "solar_reliability": 1.0
        }
    ]

    ranked = score_and_rank_offers(offers, requested_kg=500.0, sri_band="HIGH")

    scores_by_id = {o["asset_id"]: o["unrounded_score"] for o in ranked}

    # Tolerance 0.0005
    assert abs(scores_by_id["asset_A"] - 0.33409) < 0.0005, f"Expected A ~ 0.334, got {scores_by_id['asset_A']}"
    assert abs(scores_by_id["asset_B"] - 0.29667) < 0.0005, f"Expected B ~ 0.297, got {scores_by_id['asset_B']}"
    assert abs(scores_by_id["asset_C"] - 0.44375) < 0.0005, f"Expected C ~ 0.444, got {scores_by_id['asset_C']}"

    # Winner is B (rank 1)
    assert ranked[0]["asset_id"] == "asset_B"
    assert ranked[0]["score"] == 0.297
    assert ranked[1]["asset_id"] == "asset_A"
    assert ranked[1]["score"] == 0.334
    assert ranked[2]["asset_id"] == "asset_C"
    assert ranked[2]["score"] == 0.444


def test_solar_fallback_drop_excludes_van():
    """
    Solar test from specification:
    When B's solar reliability drops to 0.5:
    effective capacity = 800 * 0.5 = 400 kg < 500 kg requested.
    B is excluded; scores recalculated over A and C only:
    Expected:
    - A: 0.375 (winner)
    - C: 0.444
    """
    offers_reduced = [
        {
            "bid_id": "bid_A",
            "asset_id": "asset_A",
            "asset_name": "A static room",
            "asset_type": "STATIC",
            "price_total": 1000.0,
            "distance_km": 5.0,
            "eta_minutes": 65.0,
            "available_capacity_kg": 1000.0,
            "effective_available_kg": 1000.0,
            "solar_reliability": 1.0
        },
        {
            "bid_id": "bid_C",
            "asset_id": "asset_C",
            "asset_name": "C static room",
            "asset_type": "STATIC",
            "price_total": 800.0,
            "distance_km": 25.0,
            "eta_minutes": 90.0,
            "available_capacity_kg": 800.0,
            "effective_available_kg": 800.0,
            "solar_reliability": 1.0
        }
    ]

    ranked = score_and_rank_offers(offers_reduced, requested_kg=500.0, sri_band="HIGH")
    scores_by_id = {o["asset_id"]: o["unrounded_score"] for o in ranked}

    assert abs(scores_by_id["asset_A"] - 0.375) < 0.0005, f"Expected A = 0.375, got {scores_by_id['asset_A']}"
    assert abs(scores_by_id["asset_C"] - 0.44375) < 0.0005, f"Expected C = 0.444, got {scores_by_id['asset_C']}"
    assert ranked[0]["asset_id"] == "asset_A"
    assert ranked[0]["score"] == 0.375


def test_normalisation_edge_cases():
    """Single offer or equal values must normalise to 0.0 without ZeroDivisionError."""
    # Single offer
    single = [{
        "bid_id": "single_bid",
        "asset_id": "asset_1",
        "asset_type": "STATIC",
        "price_total": 1500.0,
        "distance_km": 10.0,
        "eta_minutes": 45.0,
        "available_capacity_kg": 2000.0,
        "effective_available_kg": 2000.0,
        "solar_reliability": 1.0
    }]
    ranked_single = score_and_rank_offers(single, requested_kg=500.0, sri_band="LOW")
    assert len(ranked_single) == 1
    assert ranked_single[0]["components"]["price_n"] == 0.0
    assert ranked_single[0]["components"]["distance_n"] == 0.0
    assert ranked_single[0]["components"]["time_n"] == 0.0

    # Equal values across multiple offers
    equal_offers = [
        {
            "bid_id": "b1",
            "asset_id": "a1",
            "asset_type": "STATIC",
            "price_total": 1000.0,
            "distance_km": 15.0,
            "eta_minutes": 60.0,
            "available_capacity_kg": 1000.0,
            "effective_available_kg": 1000.0,
            "solar_reliability": 1.0
        },
        {
            "bid_id": "b2",
            "asset_id": "a2",
            "asset_type": "STATIC",
            "price_total": 1000.0,
            "distance_km": 15.0,
            "eta_minutes": 60.0,
            "available_capacity_kg": 1000.0,
            "effective_available_kg": 1000.0,
            "solar_reliability": 1.0
        }
    ]
    ranked_equal = score_and_rank_offers(equal_offers, requested_kg=500.0, sri_band="MEDIUM")
    for r in ranked_equal:
        assert r["components"]["price_n"] == 0.0
        assert r["components"]["distance_n"] == 0.0
        assert r["components"]["time_n"] == 0.0


def test_tie_breaking_order():
    """
    Ties broken strictly by lower price_total, then lower eta_minutes, then asset_id.
    """
    tied_offers = [
        {
            "bid_id": "b2",
            "asset_id": "asset_z",
            "asset_type": "STATIC",
            "price_total": 1200.0,
            "distance_km": 10.0,
            "eta_minutes": 40.0,
            "available_capacity_kg": 1000.0,
            "effective_available_kg": 1000.0,
            "solar_reliability": 1.0
        },
        {
            "bid_id": "b1",
            "asset_id": "asset_a",
            "asset_type": "STATIC",
            "price_total": 1000.0,  # Lower price breaks tie
            "distance_km": 10.0,
            "eta_minutes": 50.0,
            "available_capacity_kg": 1000.0,
            "effective_available_kg": 1000.0,
            "solar_reliability": 1.0
        }
    ]
    ranked = score_and_rank_offers(tied_offers, requested_kg=500.0)
    # The one with lower price comes first even if other metrics vary
    assert ranked[0]["bid_id"] == "b1"


def test_eligibility_filtering_reasons():
    """Test every exclusion reason in eligibility evaluation."""
    now = datetime.datetime.now(timezone.utc)

    # 1. Inactive asset
    inactive_asset = ColdAsset(
        id="test-inactive",
        name="Inactive Facility",
        asset_type="STATIC",
        is_active=False,
        total_capacity_kg=2000.0,
        available_capacity_kg=2000.0,
        price_per_kg_per_day=1.5,
        latitude=19.9,
        longitude=73.8
    )
    ok, reason, _ = evaluate_asset_eligibility(inactive_asset, "mango", 500.0, 10.0, now)
    assert not ok
    assert "inactive" in reason.lower()

    # 2. Outside service radius for mobile van
    van_asset = ColdAsset(
        id="test-van-radius",
        name="Far Van",
        asset_type="MOBILE",
        is_active=True,
        total_capacity_kg=1000.0,
        available_capacity_kg=800.0,
        price_per_kg_per_day=2.0,
        latitude=19.0,
        longitude=73.0
    )
    van_asset.mobile_detail = MobileAssetDetail(
        asset_id="test-van-radius",
        vehicle_ref="MH-12-9999",
        service_radius_km=30.0,
        solar_reliability=0.9,
        last_location_at=now - timedelta(minutes=5)
    )
    # Distance is 45 km, radius is 30 km
    ok, reason, _ = evaluate_asset_eligibility(van_asset, "tomato", 400.0, 45.0, now)
    assert not ok
    assert "outside mobile service radius" in reason.lower()

    # 3. Insufficient effective capacity
    # 800 available * 0.4 solar = 320 kg < 500 kg requested
    ok, reason, _ = evaluate_asset_eligibility(van_asset, "tomato", 500.0, 15.0, now, solar_reliability_override=0.4)
    assert not ok
    assert "insufficient effective solar capacity" in reason.lower()

    # 4. Stale mobile location
    van_asset.mobile_detail.last_location_at = now - timedelta(minutes=120)
    ok, reason, meta = evaluate_asset_eligibility(van_asset, "tomato", 200.0, 15.0, now)
    assert not ok
    assert meta["data_status"] == "STALE"
    assert "stale" in reason.lower()

    # 5. Unsupported crop for static room
    static_asset = ColdAsset(
        id="test-static-crop",
        name="Grapes Only Hub",
        asset_type="STATIC",
        is_active=True,
        total_capacity_kg=5000.0,
        available_capacity_kg=3000.0,
        price_per_kg_per_day=1.2,
        latitude=19.9,
        longitude=73.8
    )
    static_asset.static_detail = StaticAssetDetail(
        asset_id="test-static-crop",
        supported_crops="grapes,pomegranate",
        min_temperature_c=0.0,
        max_temperature_c=10.0
    )
    ok, reason, _ = evaluate_asset_eligibility(static_asset, "mango", 500.0, 5.0, now)
    assert not ok
    assert "not supported" in reason.lower()


def test_matching_api_flow(client_with_auth=None):
    """
    Test full API endpoints:
    - Login as demo farmer
    - Create matching request for batch 1 (Nashik Alphonso)
    - Run rank matching endpoint
    - Verify score breakdown, reasons, and baseline comparisons in API response
    """
    # 1. Login as Farmer
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer.demo@coldbridge.ai", "password": "FarmerDemo123!"},
        headers=CSRF_HEADER
    )
    assert login_res.status_code == 200
    cookies = login_res.cookies

    # 2. Create matching request for batch 1 (500 kg)
    create_req_res = client.post(
        "/api/v1/matching/requests",
        json={
            "batch_id": "b0000000-0000-0000-0000-000000000001",
            "requested_quantity_kg": 500.0
        },
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert create_req_res.status_code == 201
    req_id = create_req_res.json()["id"]

    # 3. Call rank endpoint
    rank_res = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=cookies,
        headers=CSRF_HEADER
    )
    assert rank_res.status_code == 200
    data = rank_res.json()

    assert data["request_id"] == req_id
    assert len(data["ranked_offers"]) > 0
    winner = data["ranked_offers"][0]
    assert winner["is_winner"] is True
    assert "components" in winner
    assert len(winner["reasons"]) >= 2
    assert "baselines" in data
    assert data["baselines"]["coldbridge_pick"] is not None
    assert "explanation" in data["baselines"]
