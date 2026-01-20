"""
Pydantic schemas for Session Materials.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SessionMaterialResponse(BaseModel):
    """Response schema for session material."""
    id: int
    session_id: int
    material_id: int
    is_auto_linked: bool
    created_at: datetime
    
    # Material details
    material_title: Optional[str] = None
    material_type: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    
    class Config:
        from_attributes = True


class MaterialAccessCreate(BaseModel):
    """Schema for tracking material access."""
    material_id: int


class MaterialAccessResponse(BaseModel):
    """Response schema for material access record."""
    id: int
    session_id: int
    material_id: int
    student_id: int
    accessed_at: datetime
    
    class Config:
        from_attributes = True


class SessionMaterialsListResponse(BaseModel):
    """List of materials available in a session."""
    session_id: int
    materials: list[SessionMaterialResponse]
    total_count: int
