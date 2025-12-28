"""
Pydantic schemas for user management.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    preferred_language: str = Field(default="uz", max_length=5)


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(min_length=8)
    role: UserRole = UserRole.STUDENT
    school_id: Optional[int] = None
    class_id: Optional[int] = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field(None, max_length=5)
    school_id: Optional[int] = None
    class_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role (admin only)."""
    role: UserRole


class UserResponse(BaseModel):
    """Response schema for user."""
    id: int
    email: str
    phone: Optional[str] = None
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    full_name: str
    role: UserRole
    school_id: Optional[int] = None
    class_id: Optional[int] = None
    preferred_language: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response schema for paginated user list."""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int
