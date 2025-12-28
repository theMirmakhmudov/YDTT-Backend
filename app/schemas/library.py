"""
Pydantic schemas for the digital library.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class LibraryBookBase(BaseModel):
    """Base schema for library book."""
    title: str = Field(max_length=255)
    description: Optional[str] = None
    subject_id: int
    grade: int = Field(ge=1, le=11)
    author: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    cover_image_url: Optional[str] = None


class LibraryBookCreate(LibraryBookBase):
    """Schema for creating a book (metadata only, file handled separately or pre-signed)."""
    file_path: str
    file_size: int
    mime_type: str = "application/pdf"
    is_active: bool = True


class LibraryBookUpdate(BaseModel):
    """Schema for updating a book."""
    title: Optional[str] = None
    description: Optional[str] = None
    subject_id: Optional[int] = None
    grade: Optional[int] = Field(None, ge=1, le=11)
    author: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_active: Optional[bool] = None


class LibraryBookResponse(LibraryBookBase):
    """Response schema for library book."""
    id: int
    file_path: str
    file_size: int
    mime_type: str
    download_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class LibraryBookListResponse(BaseModel):
    """Paginated list of books."""
    items: List[LibraryBookResponse]
    total: int
    page: int
    page_size: int
    pages: int
