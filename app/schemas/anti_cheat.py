"""
Pydantic schemas for anti-cheating system.
"""
from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field

from app.models.anti_cheat import CheatingEventType


class CheatingEventCreate(BaseModel):
    """Schema for creating a cheating event."""
    attempt_id: int
    event_type: CheatingEventType
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    description: Optional[str] = None
    device_id: Optional[str] = None
    metadata: Optional[dict] = None
    occurred_at: datetime
    offline_id: Optional[str] = None


class CheatingEventResponse(BaseModel):
    """Response schema for cheating event."""
    id: int
    attempt_id: int
    event_type: CheatingEventType
    severity: str
    description: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Optional[dict] = Field(None, validation_alias="event_metadata")
    occurred_at: datetime
    recorded_at: datetime
    
    class Config:
        from_attributes = True


class CheatingReportResponse(BaseModel):
    """Response schema for anti-cheating report."""
    attempt_id: int
    total_events: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    events: List[CheatingEventResponse]
    risk_score: float  # 0-100 score based on events
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
