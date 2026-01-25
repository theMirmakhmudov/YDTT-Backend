"""
User profile schemas for profile customization.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field(None, pattern="^(uz|ru|en)$")


class UserProfileResponse(BaseModel):
    """Complete user profile response."""
    id: int
    email: EmailStr
    phone: Optional[str] = None
    
    # Name
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    full_name: str
    
    # Profile
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    
    # Contact
    address: Optional[str] = None
    city: Optional[str] = None
    country: str
    
    # Role & School
    role: str
    school_id: Optional[int] = None
    class_id: Optional[int] = None
    
    # Preferences
    preferred_language: str
    
    # Status
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProfilePictureUploadResponse(BaseModel):
    """Response after uploading profile picture."""
    profile_picture_url: str
    message: str = "Profile picture uploaded successfully"
