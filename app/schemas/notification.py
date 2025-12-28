"""
Pydantic schemas for notifications.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.notification import NotificationType, NotificationPriority


class NotificationCreate(BaseModel):
    """Schema for creating a notification."""
    user_id: int
    title: str
    body: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    action_type: Optional[str] = None
    action_data: Optional[dict] = None
    expires_at: Optional[datetime] = None


class NotificationBulkCreate(BaseModel):
    """Schema for sending notifications to multiple users."""
    user_ids: List[int]
    title: str
    body: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    action_type: Optional[str] = None
    action_data: Optional[dict] = None
    expires_at: Optional[datetime] = None


class NotificationResponse(BaseModel):
    """Response schema for notification."""
    id: int
    user_id: int
    title: str
    body: str
    notification_type: NotificationType
    priority: NotificationPriority
    action_type: Optional[str] = None
    action_data: Optional[dict] = None
    is_read: bool
    is_push_sent: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response schema for paginated notification list."""
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    pages: int
