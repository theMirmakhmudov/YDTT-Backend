"""
Pydantic schemas for authentication.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole
    expires_in: int = Field(description="Token expiration time in seconds")


class LoginRequest(BaseModel):
    """Request schema for login."""
    email: EmailStr
    password: str = Field(min_length=6)


class RefreshRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Request schema for logout."""
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    """Response schema for user info."""
    id: int
    email: str
    phone: Optional[str] = None
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    role: UserRole
    school_id: Optional[int] = None
    class_id: Optional[int] = None
    preferred_language: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    """Request schema for password change."""
    current_password: str = Field(min_length=6)
    new_password: str = Field(min_length=8)
