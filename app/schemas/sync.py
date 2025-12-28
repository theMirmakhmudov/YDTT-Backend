"""
Pydantic schemas for offline synchronization.
"""
from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel

from app.models.sync import SyncOperation, SyncStatus


class SyncPushItem(BaseModel):
    """Single item to push in a sync request."""
    resource_type: str
    offline_id: str
    operation: SyncOperation
    payload: dict
    client_version: int
    client_timestamp: datetime
    checksum: Optional[str] = None


class SyncPushRequest(BaseModel):
    """Request for pushing offline data."""
    client_id: str
    items: List[SyncPushItem]


class SyncPushItemResult(BaseModel):
    """Result for a single sync item."""
    offline_id: str
    status: SyncStatus
    server_id: Optional[int] = None
    server_version: Optional[int] = None
    conflict_data: Optional[dict] = None
    error: Optional[str] = None


class SyncPushResponse(BaseModel):
    """Response for sync push request."""
    results: List[SyncPushItemResult]
    server_timestamp: datetime
    success_count: int
    conflict_count: int
    failed_count: int


class SyncPullRequest(BaseModel):
    """Request for pulling updates (via query params)."""
    since: Optional[datetime] = None
    resource_types: Optional[List[str]] = None


class SyncPullItem(BaseModel):
    """Single item in sync pull response."""
    resource_type: str
    resource_id: int
    operation: SyncOperation
    payload: dict
    server_version: int
    updated_at: datetime


class SyncPullResponse(BaseModel):
    """Response for sync pull request."""
    items: List[SyncPullItem]
    server_timestamp: datetime
    has_more: bool
