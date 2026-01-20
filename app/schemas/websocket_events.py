"""
Pydantic schemas for WebSocket events.
Real-time communication between teacher and students.
"""
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field


class WSEventType(str, Enum):
    """WebSocket event types."""
    # Session events
    SESSION_STARTED = "SESSION_STARTED"
    SESSION_ENDED = "SESSION_ENDED"
    SESSION_CANCELLED = "SESSION_CANCELLED"
    
    # Participant events
    STUDENT_JOINED = "STUDENT_JOINED"
    STUDENT_LEFT = "STUDENT_LEFT"
    TEACHER_PRESENCE = "TEACHER_PRESENCE"
    
    # Whiteboard events
    WHITEBOARD_DRAW = "WHITEBOARD_DRAW"
    WHITEBOARD_ERASE = "WHITEBOARD_ERASE"
    WHITEBOARD_CLEAR = "WHITEBOARD_CLEAR"
    
    # System events
    ERROR = "ERROR"
    PING = "PING"
    PONG = "PONG"


class WSBaseEvent(BaseModel):
    """Base WebSocket event schema."""
    type: WSEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: int


class WSSessionEvent(WSBaseEvent):
    """Session lifecycle event."""
    type: Literal[
        WSEventType.SESSION_STARTED,
        WSEventType.SESSION_ENDED,
        WSEventType.SESSION_CANCELLED
    ]
    teacher_id: int
    teacher_name: Optional[str] = None
    subject_name: Optional[str] = None
    class_name: Optional[str] = None


class WSParticipantEvent(WSBaseEvent):
    """Participant join/leave event."""
    type: Literal[WSEventType.STUDENT_JOINED, WSEventType.STUDENT_LEFT]
    student_id: int
    student_name: Optional[str] = None


class WSTeacherPresenceEvent(WSBaseEvent):
    """Teacher presence heartbeat."""
    type: Literal[WSEventType.TEACHER_PRESENCE]
    teacher_id: int
    is_online: bool = True


class WSWhiteboardEvent(WSBaseEvent):
    """Whiteboard drawing event."""
    type: Literal[
        WSEventType.WHITEBOARD_DRAW,
        WSEventType.WHITEBOARD_ERASE,
        WSEventType.WHITEBOARD_CLEAR
    ]
    payload: Dict[str, Any]
    created_by_id: int


class WSErrorEvent(WSBaseEvent):
    """Error event."""
    type: Literal[WSEventType.ERROR]
    error_code: str
    error_message: str


class WSPingPongEvent(BaseModel):
    """Ping/Pong for connection health check."""
    type: Literal[WSEventType.PING, WSEventType.PONG]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
