import pytest
import jwt
from app.core.config import Settings
from app.models.user import User

def test_c6_production_invalid_secrets_raise_error():
    """Production mode refuses to start with default, placeholder, or short JWT secrets."""
    # Old default secret
    with pytest.raises(ValueError, match="JWT_SECRET must be set to a secure"):
        Settings(
            APP_ENV="production",
            JWT_SECRET="coldbridge_super_secret_jwt_key_development_only_change_in_production_32chars",
            COOKIE_SECURE=True
        )

    # Placeholder secret
    with pytest.raises(ValueError, match="JWT_SECRET must be set to a secure"):
        Settings(
            APP_ENV="production",
            JWT_SECRET="CHANGE_ME_GENERATE_WITH_PYTHON_SECRETS_48_CHARS_MINIMUM",
            COOKIE_SECURE=True
        )

    # Short secret (< 32 chars)
    with pytest.raises(ValueError, match="JWT_SECRET must be set to a secure"):
        Settings(
            APP_ENV="production",
            JWT_SECRET="too_short_secret_under_32_chars",
            COOKIE_SECURE=True
        )

def test_c6_production_insecure_cookie_raises_error():
    """Production mode refuses to start with COOKIE_SECURE=False."""
    with pytest.raises(ValueError, match="COOKIE_SECURE must be True"):
        Settings(
            APP_ENV="production",
            JWT_SECRET="valid_secure_secret_with_more_than_32_characters_12345",
            COOKIE_SECURE=False
        )

def test_c6_samesite_none_requires_cookie_secure():
    """COOKIE_SAMESITE='none' requires COOKIE_SECURE=True across all environments."""
    with pytest.raises(ValueError, match="COOKIE_SAMESITE='none' requires COOKIE_SECURE=True"):
        Settings(
            APP_ENV="development",
            COOKIE_SAMESITE="none",
            COOKIE_SECURE=False
        )

def test_c6_development_starts_with_ephemeral_secret(capsys):
    """Development mode generates an ephemeral random secret if missing or placeholder."""
    dev_settings = Settings(
        APP_ENV="development",
        JWT_SECRET="",
        COOKIE_SECURE=False
    )
    assert len(dev_settings.JWT_SECRET) >= 32
    captured = capsys.readouterr()
    assert "WARNING: JWT_SECRET was missing or placeholder" in captured.out
    # Security: Secret itself must never be printed
    assert dev_settings.JWT_SECRET not in captured.out

def test_c6_token_signed_with_old_secret_rejected(client, farmer_user):
    """Tokens signed with old/compromised secrets are rejected with 401."""
    old_secret = "coldbridge_super_secret_jwt_key_development_only_change_in_production_32chars"
    payload = {
        "sub": str(farmer_user.id),
        "role": farmer_user.role,
        "exp": 9999999999
    }
    old_token = jwt.encode(payload, old_secret, algorithm="HS256")

    res = client.get("/api/v1/auth/me", cookies={"access_token": old_token})
    assert res.status_code == 401
    assert "Invalid" in res.json()["detail"] or "expired" in res.json()["detail"]
