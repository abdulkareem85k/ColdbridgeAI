import datetime
from datetime import timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
from app.core.config import settings

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Securely hash a plain text password using bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored bcrypt hash."""
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Create a signed JWT access token with expiration and user claims."""
    to_encode = data.copy()
    now_utc = datetime.datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": now_utc})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify a signed JWT access token."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
