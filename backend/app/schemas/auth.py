from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
import email_validator

# Disable DNS deliverability checks so offline / sandbox environments validate instantly without network hangs
email_validator.TEST_ENVIRONMENT = True

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    role: str = Field(..., description="FARMER, STATIC_OPERATOR, VAN_OPERATOR, BUYER, ADMIN")
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthUserResponse(BaseModel):
    id: str
    email: str
    role: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    message: str
