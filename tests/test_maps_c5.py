import pytest
import datetime
from datetime import timezone
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.route import RouteCache, RouteUsage
from app.services import maps_service
from app.services.maps_service import (
    compute_route,
    compute_route_matrix,
    check_and_increment_daily_limit,
    get_daily_calls,
    haversine_km
)

@pytest.fixture(autouse=True)
def clean_route_usage_and_cache(db_session):
    """Clean route usage and route cache before each test."""
    db_session.query(RouteUsage).delete()
    db_session.query(RouteCache).delete()
    db_session.commit()
    yield
    db_session.query(RouteUsage).delete()
    db_session.query(RouteCache).delete()
    db_session.commit()

def test_c5_daily_limit_enforced(db_session):
    """Daily call limit is strictly enforced; subsequent calls fall back to ESTIMATED."""
    nashik = (19.9975, 73.7898)
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "code": "Ok",
        "routes": [{"distance": 25000.0, "duration": 1800.0, "geometry": {"coordinates": []}}]
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_resp

    old_limit = settings.MAX_ROUTE_CALLS_PER_DAY
    try:
        settings.MAX_ROUTE_CALLS_PER_DAY = 2

        with patch("app.services.maps_service.httpx.Client", return_value=mock_client):
            # Call 1: Distinct destination 1 -> OSRM_ROUTES
            r1 = compute_route(nashik, (20.01, 73.81), db_session)
            assert r1["route_source"] == "OSRM_ROUTES"

            # Call 2: Distinct destination 2 -> OSRM_ROUTES
            r2 = compute_route(nashik, (20.02, 73.82), db_session)
            assert r2["route_source"] == "OSRM_ROUTES"

            # Call 3: Distinct destination 3 -> Exceeds limit 2! Must be ESTIMATED
            r3 = compute_route(nashik, (20.03, 73.83), db_session)
            assert r3["route_source"] == "ESTIMATED"
            assert "Safety daily route call limit reached" in r3["note"]
            assert r3["distance_km"] > 0
    finally:
        settings.MAX_ROUTE_CALLS_PER_DAY = old_limit

from app.db.base import Base

def test_c5_counter_survives_simulated_restart(tmp_path):
    """Counter persists in the database across process / engine restarts."""
    db_file = tmp_path / "restart_test.db"
    db_url = f"sqlite:///{db_file}"

    # Engine 1
    engine1 = create_engine(db_url)
    Base.metadata.create_all(bind=engine1)
    Session1 = sessionmaker(bind=engine1)
    with Session1() as s1:
        assert check_and_increment_daily_limit(s1, max_limit=10) is True
        assert check_and_increment_daily_limit(s1, max_limit=10) is True
        assert get_daily_calls(s1) == 2
    engine1.dispose()

    # Engine 2 (simulated restart: fresh process/engine on same DB file)
    engine2 = create_engine(db_url)
    Session2 = sessionmaker(bind=engine2)
    with Session2() as s2:
        assert get_daily_calls(s2) == 2
        assert check_and_increment_daily_limit(s2, max_limit=10) is True
        assert get_daily_calls(s2) == 3
    engine2.dispose()

def test_c5_cache_hit_does_not_use_quota(db_session):
    """Cache hits return immediately without consuming daily quota."""
    orig = (19.9975, 73.7898)
    dest = (20.0800, 73.8400)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "code": "Ok",
        "routes": [{"distance": 15000.0, "duration": 1200.0, "geometry": {"coordinates": []}}]
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_resp

    with patch("app.services.maps_service.httpx.Client", return_value=mock_client):
        # First call: misses cache, increments quota from 0 to 1
        r1 = compute_route(orig, dest, db_session)
        assert r1["cached"] is False
        assert get_daily_calls(db_session) == 1

        # Second call: hits cache!
        r2 = compute_route(orig, dest, db_session)
        assert r2["cached"] is True
        # Quota MUST still be 1 (cache hit did not consume quota)
        assert get_daily_calls(db_session) == 1
        assert r2["distance_km"] == r1["distance_km"]

def test_c5_nearest_n_chosen_from_unsorted_list(db_session):
    """compute_route_matrix sorts by haversine distance and routes nearest N first."""
    origin = (19.9975, 73.7898) # Nashik

    # Unsorted destinations with varying distances from Nashik:
    # Delhi: ~1000 km
    # Ozar: ~15 km (nearest)
    # Mumbai: ~170 km
    # Dindori: ~25 km (2nd nearest)
    # Pune: ~165 km
    dest_delhi = (28.6139, 77.2090)
    dest_ozar = (20.0900, 73.9100)
    dest_mumbai = (18.9220, 72.8347)
    dest_dindori = (20.0800, 73.8400)
    dest_pune = (18.5204, 73.8567)

    destinations = [dest_delhi, dest_ozar, dest_mumbai, dest_dindori, dest_pune]

    old_cap = settings.MAX_ROUTE_CALLS_PER_REQUEST
    try:
        settings.MAX_ROUTE_CALLS_PER_REQUEST = 2

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "code": "Ok",
            "routes": [{"distance": 20000.0, "duration": 1500.0, "geometry": {"coordinates": []}}]
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_resp

        with patch("app.services.maps_service.httpx.Client", return_value=mock_client):
            results = compute_route_matrix(origin, destinations, db_session)

            # All 5 destinations must be present (none silently dropped)
            assert len(results) == 5

            # The first 2 (nearest: Ozar ~15km, Dindori ~25km) must be road routes
            assert results[0]["route_source"] == "OSRM_ROUTES"
            assert results[1]["route_source"] == "OSRM_ROUTES"

            # The remaining 3 beyond cap=2 must be ESTIMATED
            assert results[2]["route_source"] == "ESTIMATED"
            assert results[3]["route_source"] == "ESTIMATED"
            assert results[4]["route_source"] == "ESTIMATED"
            assert "Exceeded per-request limit" in results[2]["note"]
    finally:
        settings.MAX_ROUTE_CALLS_PER_REQUEST = old_cap

def test_c5_osrm_failure_falls_back_to_estimated(db_session):
    """OSRM network failure or non-Ok response falls back gracefully to ESTIMATED."""
    orig = (19.9975, 73.7898)
    dest = (20.0500, 73.8200)

    # 1. Non-200 HTTP response
    mock_bad_resp = MagicMock()
    mock_bad_resp.status_code = 502
    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_bad_resp

    with patch("app.services.maps_service.httpx.Client", return_value=mock_client):
        res1 = compute_route(orig, dest, db_session)
        assert res1["route_source"] == "ESTIMATED"
        assert res1["distance_km"] > 0

    # 2. Check that fallback was cached as ESTIMATED and not OSRM_ROUTES
    cached_entry = db_session.query(RouteCache).filter(
        RouteCache.origin_lat == round(orig[0], 4),
        RouteCache.dest_lat == round(dest[0], 4)
    ).first()
    assert cached_entry is not None
    assert cached_entry.route_source == "ESTIMATED"

def test_c5_concurrent_calls_atomic_limit(tmp_path):
    """20 concurrent threads requesting quota with limit 5 grant exactly 5 slots."""
    db_file = tmp_path / "concurrent_test.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"timeout": 30, "check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionMaker = sessionmaker(bind=engine)

    limit = 5

    def attempt_reservation():
        with SessionMaker() as session:
            return check_and_increment_daily_limit(session, max_limit=limit)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: attempt_reservation(), range(20)))

    granted = sum(1 for r in results if r is True)
    assert granted == 5

    with SessionMaker() as session:
        assert get_daily_calls(session) == 5

    engine.dispose()
