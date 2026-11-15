import datetime
from datetime import timezone
import pytest
from app.core.security import create_access_token
from tests.conftest import auth_cookies_for

CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}

def test_register_and_login_success(client, db_session):
    # Register a new user
    reg_payload = {
        "email": "newfarmer@coldbridge.ai",
        "password": "SecurePassword123!",
        "role": "FARMER",
        "full_name": "New Farmer",
        "phone": "+91-9988776655"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["email"] == "newfarmer@coldbridge.ai"
    assert "password" not in reg_data
    assert "hashed_password" not in reg_data

    # Login
    login_payload = {
        "email": "newfarmer@coldbridge.ai",
        "password": "SecurePassword123!"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    
    # Invariant: JWT is NEVER returned in the response body!
    login_data = login_res.json()
    assert "access_token" not in login_data
    assert "token" not in login_data
    assert "password" not in login_data
    assert "hashed_password" not in login_data
    assert login_data["role"] == "FARMER"

    # Invariant: JWT lives strictly in HttpOnly cookie
    assert "access_token" in login_res.cookies
    cookie_header = login_res.headers.get("set-cookie")
    assert "HttpOnly" in cookie_header or "httponly" in cookie_header.lower()
    assert "samesite" in cookie_header.lower()

def test_invalid_login_credentials(client, farmer_user):
    res = client.post("/api/v1/auth/login", json={
        "email": farmer_user.email,
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

def test_protected_me_endpoint_with_and_without_cookie(client, farmer_user):
    # Without cookie -> 401
    res_no_cookie = client.get("/api/v1/auth/me")
    assert res_no_cookie.status_code == 401

    # With cookie -> 200
    cookies = auth_cookies_for(farmer_user)
    res_with_cookie = client.get("/api/v1/auth/me", cookies=cookies)
    assert res_with_cookie.status_code == 200
    assert res_with_cookie.json()["id"] == farmer_user.id
    assert res_with_cookie.json()["email"] == farmer_user.email

def test_tampered_or_expired_token(client, farmer_user):
    # Tampered token
    res_tampered = client.get("/api/v1/auth/me", cookies={"access_token": "tampered.jwt.token"})
    assert res_tampered.status_code == 401

    # Expired token
    expired_token = create_access_token(
        data={"sub": farmer_user.id, "role": farmer_user.role},
        expires_delta=datetime.timedelta(seconds=-10)
    )
    res_expired = client.get("/api/v1/auth/me", cookies={"access_token": expired_token})
    assert res_expired.status_code == 401
    assert "Session expired" in res_expired.json()["detail"]

def test_farmer_cannot_access_operator_endpoint(client, farmer_user):
    cookies = auth_cookies_for(farmer_user)
    # Attempt to post a cooling asset as a farmer
    asset_payload = {
        "name": "Unauthorized Cold Room",
        "asset_type": "STATIC",
        "total_capacity_kg": 5000,
        "price_per_kg_per_day": 1.5,
        "latitude": 20.0,
        "longitude": 73.8,
        "static_detail": {
            "supported_crops": "mango",
            "min_temperature_c": 2.0,
            "max_temperature_c": 10.0
        }
    }
    res = client.post("/api/v1/assets", json=asset_payload, cookies=cookies, headers=CSRF_HEADER)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_csrf_protection_on_state_changing_request(client, operator_user):
    cookies = auth_cookies_for(operator_user)
    asset_payload = {
        "name": "Operator Room",
        "asset_type": "STATIC",
        "total_capacity_kg": 5000,
        "price_per_kg_per_day": 1.5,
        "latitude": 20.0,
        "longitude": 73.8,
        "static_detail": {
            "supported_crops": "mango",
            "min_temperature_c": 2.0,
            "max_temperature_c": 10.0
        }
    }
    # Request without CSRF header should be blocked
    res_no_csrf = client.post("/api/v1/assets", json=asset_payload, cookies=cookies)
    assert res_no_csrf.status_code == 403
    assert "Missing CSRF verification header" in res_no_csrf.json()["detail"]

    # Request with CSRF header succeeds
    res_csrf = client.post("/api/v1/assets", json=asset_payload, cookies=cookies, headers=CSRF_HEADER)
    assert res_csrf.status_code == 201

def test_logout_clears_cookie(client, farmer_user):
    cookies = auth_cookies_for(farmer_user)
    res = client.post("/api/v1/auth/logout", cookies=cookies, headers=CSRF_HEADER)
    assert res.status_code == 200
    set_cookie = res.headers.get("set-cookie")
    # Verify cookie deletion / expiration
    assert 'access_token=""' in set_cookie or "Max-Age=0" in set_cookie or "max-age=0" in set_cookie.lower()
