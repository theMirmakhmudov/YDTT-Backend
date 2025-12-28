"""
Pydantic schemas for lessons and materials.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.lesson import MaterialType


# Lesson schemas
class LessonBase(BaseModel):
    """Base lesson schema."""
    title: str = Field(max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    subject_id: int
    grade: int = Field(ge=1, le=12)
    order: int = Field(default=0, ge=0)


class LessonCreate(LessonBase):
    """Schema for creating a lesson."""
    pass


class LessonUpdate(BaseModel):
    """Schema for updating a lesson."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    order: Optional[int] = Field(None, ge=0)
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


class LessonResponse(BaseModel):
    """Response schema for lesson."""
    id: int
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    subject_id: int
    grade: int
    order: int
    version: int
    is_published: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class LessonListResponse(BaseModel):
    """Response schema for paginated lesson list."""
    items: List[LessonResponse]
    total: int
    page: int
    page_size: int
    pages: int


# Material schemas
class MaterialBase(BaseModel):
    """Base material schema."""
    title: str = Field(max_length=255)
    description: Optional[str] = None
    lesson_id: int


class MaterialCreate(MaterialBase):
    """Schema for creating material (metadata only, file handled separately)."""
    pass


class MaterialResponse(BaseModel):
    """Response schema for material."""
    id: int
    title: str
    description: Optional[str] = None
    lesson_id: int
    file_name: str
    file_size: int
    mime_type: str
    material_type: MaterialType
    checksum: str
    version: int
    download_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MaterialListResponse(BaseModel):
    """Response schema for paginated material list."""
    items: List[MaterialResponse]
    total: int
    page: int
    page_size: int
    pages: int


class MaterialDownloadResponse(BaseModel):
    """Response schema for material download."""
    download_url: str
    file_name: str
    checksum: str
    expires_at: datetime
