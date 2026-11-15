import datetime
from datetime import timezone
from typing import List, Callable, Optional, Dict
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
import jwt

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# In-memory rate limiting store for login attempts: ip -> list of timestamps
_login_attempts: Dict[str, List[datetime.datetime]] = {}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_RATE_WINDOW_MINUTES = 15

def check_login_rate_limit(request: Request):
    """Enforce rate limiting on login endpoint per client IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.datetime.now(timezone.utc)
    cutoff = now - datetime.timedelta(minutes=LOGIN_RATE_WINDOW_MINUTES)
    
    attempts = _login_attempts.get(client_ip, [])
    # Filter attempts within active time window
    valid_attempts = [ts for ts in attempts if ts > cutoff]
    _login_attempts[client_ip] = valid_attempts

    if len(valid_attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again after 15 minutes."
        )

def record_failed_login(request: Request):
    """Record a failed login attempt for rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.datetime.now(timezone.utc)
    if client_ip not in _login_attempts:
        _login_attempts[client_ip] = []
    _login_attempts[client_ip].append(now)

def clear_login_attempts(request: Request):
    """Clear rate limiting attempts upon successful login."""
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in _login_attempts:
        del _login_attempts[client_ip]

def verify_csrf_header(request: Request):
    """
    CSRF verification for state-changing HTTP methods using custom header.
    api.js sends X-Requested-With: XMLHttpRequest.
    """
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        csrf_header = request.headers.get("x-requested-with")
        if not csrf_header:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing CSRF verification header (X-Requested-With)"
            )

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticate user using only the HttpOnly cookie 'access_token'.
    JavaScript cannot and must not access this token.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing session cookie."
        )

    try:
        payload = decode_access_token(token)
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload."
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again."
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account."
        )

    # Check CSRF on state-changing requests when authenticated via cookie
    verify_csrf_header(request)

    return user

def require_role(*allowed_roles: str) -> Callable:
    """Reusable role-based access control dependency."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User role '{current_user.role}' is not authorized. Required: {list(allowed_roles)}"
            )
        return current_user
    return role_checker
