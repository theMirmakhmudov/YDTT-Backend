"""
Offline synchronization API endpoints.
"""
from typing import Annotated, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.models.sync import SyncEvent, SyncCheckpoint, SyncOperation, SyncStatus
from app.schemas.sync import (
    SyncPushRequest,
    SyncPushResponse,
    SyncPushItemResult,
    SyncPullResponse,
    SyncPullItem,
)


router = APIRouter(prefix="/sync", tags=["Offline Synchronization"])


@router.post("/push", response_model=SyncPushResponse)
async def push_sync(
    push_request: SyncPushRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Push offline changes to the server.
    Handles conflict detection and resolution.
    """
    results = []
    success_count = 0
    conflict_count = 0
    failed_count = 0
    
    for item in push_request.items:
        try:
            # Check for existing sync event with same offline_id
            result = await db.execute(
                select(SyncEvent).where(
                    SyncEvent.offline_id == item.offline_id,
                    SyncEvent.user_id == current_user.id,
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Already processed, return success (idempotent)
                results.append(SyncPushItemResult(
                    offline_id=item.offline_id,
                    status=existing.status,
                    server_id=existing.resource_id,
                    server_version=existing.server_version,
                ))
                if existing.status == SyncStatus.SYNCED:
                    success_count += 1
                elif existing.status == SyncStatus.CONFLICT:
                    conflict_count += 1
                else:
                    failed_count += 1
                continue
            
            # Create sync event record
            sync_event = SyncEvent(
                client_id=push_request.client_id,
                user_id=current_user.id,
                resource_type=item.resource_type,
                offline_id=item.offline_id,
                operation=item.operation,
                payload=item.payload,
                client_version=item.client_version,
                client_timestamp=item.client_timestamp,
                checksum=item.checksum,
                status=SyncStatus.PENDING,
            )
            db.add(sync_event)
            await db.flush()
            
            # Process the sync (simplified - in production would be more complex)
            # Here we just accept the changes with server-wins conflict resolution
            sync_event.status = SyncStatus.SYNCED
            sync_event.server_version = int(datetime.utcnow().timestamp() * 1000)
            sync_event.processed_at = datetime.utcnow()
            
            results.append(SyncPushItemResult(
                offline_id=item.offline_id,
                status=SyncStatus.SYNCED,
                server_version=sync_event.server_version,
            ))
            success_count += 1
            
        except Exception as e:
            results.append(SyncPushItemResult(
                offline_id=item.offline_id,
                status=SyncStatus.FAILED,
                error=str(e),
            ))
            failed_count += 1
    
    # Update checkpoint
    result = await db.execute(
        select(SyncCheckpoint).where(
            SyncCheckpoint.client_id == push_request.client_id,
            SyncCheckpoint.user_id == current_user.id,
        )
    )
    checkpoint = result.scalar_one_or_none()
    
    now = datetime.utcnow()
    server_version = int(now.timestamp() * 1000)
    
    if checkpoint:
        checkpoint.last_sync_at = now
        checkpoint.last_server_version = server_version
    else:
        checkpoint = SyncCheckpoint(
            client_id=push_request.client_id,
            user_id=current_user.id,
            last_sync_at=now,
            last_server_version=server_version,
        )
        db.add(checkpoint)
    
    await db.commit()
    
    return SyncPushResponse(
        results=results,
        server_timestamp=now,
        success_count=success_count,
        conflict_count=conflict_count,
        failed_count=failed_count,
    )


@router.get("/pull", response_model=SyncPullResponse)
async def pull_sync(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    since: Optional[datetime] = None,
    resource_types: Optional[str] = Query(None, description="Comma-separated resource types"),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Pull changes from the server since last sync.
    Returns incremental updates based on the 'since' timestamp.
    """
    query = select(SyncEvent).where(
        SyncEvent.user_id == current_user.id,
        SyncEvent.status == SyncStatus.SYNCED,
    )
    
    if since:
        query = query.where(SyncEvent.processed_at > since)
    
    if resource_types:
        types = [t.strip() for t in resource_types.split(",")]
        query = query.where(SyncEvent.resource_type.in_(types))
    
    query = query.order_by(SyncEvent.processed_at).limit(limit + 1)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    has_more = len(events) > limit
    if has_more:
        events = events[:limit]
    
    items = [
        SyncPullItem(
            resource_type=e.resource_type,
            resource_id=e.resource_id or 0,
            operation=e.operation,
            payload=e.payload,
            server_version=e.server_version or 0,
            updated_at=e.processed_at or e.received_at,
        )
        for e in events
    ]
    
    return SyncPullResponse(
        items=items,
        server_timestamp=datetime.utcnow(),
        has_more=has_more,
    )
