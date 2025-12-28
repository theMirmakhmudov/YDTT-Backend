"""
Sync event model for offline synchronization tracking.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Enum, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SyncOperation(str, enum.Enum):
    """Types of sync operations."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class SyncStatus(str, enum.Enum):
    """Status of sync operation."""
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    CONFLICT = "CONFLICT"
    FAILED = "FAILED"


class SyncEvent(Base):
    """
    Tracks offline sync events for conflict detection and resolution.
    """
    __tablename__ = "sync_events"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Client identification
    client_id: Mapped[str] = mapped_column(String(36), index=True)  # Device/client UUID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Resource tracking
    resource_type: Mapped[str] = mapped_column(String(50), index=True)
    resource_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    offline_id: Mapped[str] = mapped_column(String(36), index=True)
    
    # Operation
    operation: Mapped[SyncOperation] = mapped_column(Enum(SyncOperation))
    
    # Data
    payload: Mapped[dict] = mapped_column(JSON)
    
    # Version control
    client_version: Mapped[int] = mapped_column(BigInteger)
    server_version: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # Conflict resolution
    status: Mapped[SyncStatus] = mapped_column(Enum(SyncStatus), default=SyncStatus.PENDING)
    conflict_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timestamps
    client_timestamp: Mapped[datetime] = mapped_column(DateTime)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Checksum for data integrity
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class SyncCheckpoint(Base):
    """
    Tracks sync checkpoints for each client to enable incremental sync.
    """
    __tablename__ = "sync_checkpoints"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Client identification
    client_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Checkpoint data
    last_sync_at: Mapped[datetime] = mapped_column(DateTime)
    last_server_version: Mapped[int] = mapped_column(BigInteger)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
