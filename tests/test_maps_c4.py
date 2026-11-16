import pytest
import time
from unittest.mock import patch, MagicMock
import httpx
from tests.conftest import auth_cookies_for
from app.services import maps_service

@pytest.fixture(autouse=True)
def clear_nominatim_caches():
    """Clear Nominatim caches and reset timestamp before each test."""
    maps_service._nominatim_reverse_cache.clear()
    maps_service._nominatim_search_cache.clear()
    maps_service._last_nominatim_call_timestamp = 0.0
    yield
    maps_service._nominatim_reverse_cache.clear()
    maps_service._nominatim_search_cache.clear()

def test_maps_c4_reverse_geocode_ok(client, farmer_user):
    """Reverse geocode succeeds and returns formatted address via backend proxy."""
    cookies = auth_cookies_for(farmer_user)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "display_name": "Nashik APMC Market, Maharashtra, India"
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_resp

    with patch("app.services.maps_service.httpx.Client", return_value=mock_client):
        res = client.get("/api/v1/maps/reverse-geocode?lat=19.9975&lng=73.7898", cookies=cookies)
        assert res.status_code == 200
        data = res.json()
        assert data["address"] == "Nashik APMC Market, Maharashtra, India"
        assert data["source"] == "NOMINATIM"
        assert data["latitude"] == 19.9975
        assert data["longitude"] == 73.7898

def test_maps_c4_search_ok(client, farmer_user):
    """Search endpoint returns geocoded results matching query."""
    cookies = auth_cookies_for(farmer_user)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "display_name": "Pune Market Yard, Maharashtra, India",
            "lat": "18.5204",
            "lon": "73.8567"
        }
    ]

    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_resp

    with patch("app.services.maps_service.httpx.Client", return_value=mock_client):
        res = client.get("/api/v1/maps/search?q=Pune Market Yard&limit=2", cookies=cookies)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["display_name"] == "Pune Market Yard, Maharashtra, India"
        assert data[0]["latitude"] == 18.5204
        assert data[0]["longitude"] == 73.8567

def test_maps_c4_cache_hit_no_external_call(client, farmer_user):
    """Second call to identical coordinates or query hits cache without external HTTP call."""
    cookies = auth_cookies_for(farmer_user)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"display_name": "Cached Location, Maharashtra"}

    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_resp

    with patch("app.services.maps_service.httpx.Client", return_value=mock_client):
        # First call populates cache
        r1 = client.get("/api/v1/maps/reverse-geocode?lat=19.9975&lng=73.7898", cookies=cookies)
        assert r1.status_code == 200
        assert mock_client.__enter__.return_value.get.call_count == 1
        assert r1.json()["source"] == "NOMINATIM"

        # Second call hits cache
        r2 = client.get("/api/v1/maps/reverse-geocode?lat=19.9975&lng=73.7898", cookies=cookies)
        assert r2.status_code == 200
        assert mock_client.__enter__.return_value.get.call_count == 1  # No additional external call!
        assert r2.json()["source"] == "CACHE"
        assert r2.json()["address"] == "Cached Location, Maharashtra"

def test_maps_c4_concurrent_calls_spaced_ge_1s():
    """Consecutive rate-limited slot acquisitions must be spaced at least 1.0s apart."""
    # First slot acquisition
    t0 = time.time()
    slot1 = maps_service._acquire_nominatim_slot(timeout=3.0)
    assert slot1 is True

    # Second slot acquisition immediately after
    slot2 = maps_service._acquire_nominatim_slot(timeout=3.0)
    t1 = time.time()
    assert slot2 is True
    # Verify elapsed time between slots is at least 1.0 second
    assert (t1 - t0) >= 0.98

def test_maps_c4_timeout_network_failure_fallback_shape(client, farmer_user):
    """Network errors or timeouts return 200 with documented fallback shape."""
    cookies = auth_cookies_for(farmer_user)

    mock_timeout_client = MagicMock()
    mock_timeout_client.__enter__.return_value.get.side_effect = httpx.ConnectTimeout("Connection timed out")

    # 1. Reverse geocode network timeout
    with patch("app.services.maps_service.httpx.Client", return_value=mock_timeout_client):
        res_rev = client.get("/api/v1/maps/reverse-geocode?lat=19.1234&lng=73.5678", cookies=cookies)
        assert res_rev.status_code == 200
        data_rev = res_rev.json()
        assert data_rev["address"] is None
        assert data_rev["source"] == "UNAVAILABLE"
        assert data_rev["latitude"] == 19.1234
        assert data_rev["longitude"] == 73.5678

    mock_error_client = MagicMock()
    mock_error_client.__enter__.return_value.get.side_effect = httpx.ConnectError("Network unreachable")

    # 2. Search network error
    with patch("app.services.maps_service.httpx.Client", return_value=mock_error_client):
        res_search = client.get("/api/v1/maps/search?q=Unknown Remote Place", cookies=cookies)
        assert res_search.status_code == 200
        data_search = res_search.json()
        assert data_search == []

def test_maps_c4_invalid_input_422(client, farmer_user):
    """Invalid query lengths, limits, or coordinates return 422."""
    cookies = auth_cookies_for(farmer_user)

    # Search query too short (< 3 chars)
    r1 = client.get("/api/v1/maps/search?q=ab", cookies=cookies)
    assert r1.status_code == 422

    # Search limit < 1
    r2 = client.get("/api/v1/maps/search?q=Nashik&limit=0", cookies=cookies)
    assert r2.status_code == 422

    # Search limit > 5
    r3 = client.get("/api/v1/maps/search?q=Nashik&limit=10", cookies=cookies)
    assert r3.status_code == 422

    # Reverse geocode out-of-range lat
    r4 = client.get("/api/v1/maps/reverse-geocode?lat=95.0&lng=73.0", cookies=cookies)
    assert r4.status_code == 422

    # Reverse geocode out-of-range lng
    r5 = client.get("/api/v1/maps/reverse-geocode?lat=19.0&lng=190.0", cookies=cookies)
    assert r5.status_code == 422
