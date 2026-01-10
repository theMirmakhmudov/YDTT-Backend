"""
Pydantic schemas for school, class, and subject management.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, EmailStr


# School schemas
class SchoolBase(BaseModel):
    """Base school schema."""
    name: str = Field(max_length=255)
    region: str = Field(max_length=100)
    district: str = Field(max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    director_name: Optional[str] = Field(None, max_length=255)
    capacity: Optional[int] = Field(None, ge=0)


class SchoolCreate(SchoolBase):
    """Schema for creating a school."""
    code: Optional[str] = Field(None, max_length=50)  # Auto-generated if not provided


class SchoolUpdate(BaseModel):
    """Schema for updating a school."""
    name: Optional[str] = Field(None, max_length=255)
    region: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    director_name: Optional[str] = Field(None, max_length=255)
    capacity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class SchoolResponse(BaseModel):
    """Response schema for school."""
    id: int
    name: str
    code: str
    region: str
    district: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    director_name: Optional[str] = None
    capacity: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SchoolListResponse(BaseModel):
    """Response schema for paginated school list."""
    items: List[SchoolResponse]
    total: int
    page: int
    page_size: int
    pages: int


# Class schemas
class ClassBase(BaseModel):
    """Base class schema."""
    name: str = Field(max_length=100)  # e.g., "9-A"
    grade: int = Field(ge=1, le=12)
    school_id: int
    academic_year: str = Field(max_length=20)  # e.g., "2024-2025"


class ClassCreate(ClassBase):
    """Schema for creating a class."""
    pass


class ClassUpdate(BaseModel):
    """Schema for updating a class."""
    name: Optional[str] = Field(None, max_length=100)
    academic_year: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class ClassResponse(BaseModel):
    """Response schema for class."""
    id: int
    name: str
    grade: int
    school_id: int
    academic_year: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClassListResponse(BaseModel):
    """Response schema for paginated class list."""
    items: List[ClassResponse]
    total: int
    page: int
    page_size: int
    pages: int


# Subject schemas
class SubjectBase(BaseModel):
    """Base subject schema."""
    name: str = Field(max_length=200)
    code: str = Field(max_length=50)
    description: Optional[str] = None


class SubjectCreate(SubjectBase):
    """Schema for creating a subject."""
    pass


class SubjectUpdate(BaseModel):
    """Schema for updating a subject."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SubjectResponse(BaseModel):
    """Response schema for subject."""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SubjectListResponse(BaseModel):
    """Response schema for paginated subject list."""
    items: List[SubjectResponse]
    total: int
    page: int
    page_size: int
    pages: int
