"""
Pydantic schemas for Whiteboard events.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class WhiteboardEventType(str, Enum):
    """Type of whiteboard event."""
    DRAW = "DRAW"
    ERASE = "ERASE"
    CLEAR = "CLEAR"


class WhiteboardDrawPayload(BaseModel):
    """Payload for draw event."""
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    color: str = Field(..., description="Color hex code, e.g., #000000")
    size: int = Field(..., ge=1, le=50, description="Brush size in pixels")


class WhiteboardErasePayload(BaseModel):
    """Payload for erase event."""
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    size: int = Field(..., ge=1, le=100, description="Eraser size in pixels")


class WhiteboardEventCreate(BaseModel):
    """Schema for creating a whiteboard event."""
    event_type: WhiteboardEventType
    payload: Dict[str, Any]  # Will be validated based on event_type


class WhiteboardEventResponse(BaseModel):
    """Response schema for whiteboard event."""
    id: int
    session_id: int
    created_by_id: int
    event_type: WhiteboardEventType
    payload: Dict[str, Any]
    created_at: datetime
    
    # Extra info
    created_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class WhiteboardStateResponse(BaseModel):
    """Complete whiteboard state for a session."""
    session_id: int
    events: list[WhiteboardEventResponse]
    total_events: int
