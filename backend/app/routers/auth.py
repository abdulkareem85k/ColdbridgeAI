from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import (
    get_db,
    get_current_user,
    check_login_rate_limit,
    record_failed_login,
    clear_login_attempts
)
from app.models.user import User, FarmerProfile, OperatorProfile
from app.schemas.auth import RegisterRequest, LoginRequest, AuthUserResponse, MessageResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

VALID_ROLES = {"FARMER", "STATIC_OPERATOR", "VAN_OPERATOR", "BUYER", "ADMIN"}

@router.post("/register", response_model=AuthUserResponse, status_code=status.HTTP_201_CREATED)
def register(
    req: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user with a designated role."""
    if req.role.upper() not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{req.role}'. Valid roles: {sorted(list(VALID_ROLES))}"
        )

    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists."
        )

    user = User(
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        role=req.role.upper(),
        full_name=req.full_name,
        phone=req.phone,
        is_active=True
    )
    db.add(user)
    db.flush()

    # Create associated default profile for farmers and operators
    if user.role == "FARMER":
        db.add(FarmerProfile(
            user_id=user.id,
            farm_name=f"{user.full_name}'s Farm",
            district="Nashik",
            state="Maharashtra"
        ))
    elif user.role in ["STATIC_OPERATOR", "VAN_OPERATOR"]:
        db.add(OperatorProfile(
            user_id=user.id,
            business_name=f"{user.full_name}'s Cooling Services",
            contact_phone=user.phone,
            district="Pune",
            state="Maharashtra"
        ))

    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=AuthUserResponse)
def login(
    req: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and set JWT in HttpOnly cookie.
    The JWT is NEVER returned in the JSON response body.
    """
    # Check in-memory rate limiting
    check_login_rate_limit(request)

    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        record_failed_login(request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )

    clear_login_attempts(request)

    # Issue JWT token
    token = create_access_token(data={"sub": user.id, "role": user.role})

    # Set ONE session mechanism: HttpOnly Cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    return user

@router.get("/me", response_model=AuthUserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user based on the HttpOnly session cookie."""
    return current_user

@router.post("/logout", response_model=MessageResponse)
def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Log out the current user and delete the HttpOnly session cookie."""
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE
    )
    return {"message": "Logged out successfully"}
