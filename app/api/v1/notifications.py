"""
Notification API endpoints.
"""
from typing import Annotated, Optional
from math import ceil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCreate,
    NotificationBulkCreate,
    NotificationResponse,
    NotificationListResponse,
)


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = None,
):
    """List notifications for the current user."""
    query = select(Notification).where(Notification.user_id == current_user.id)
    count_query = select(func.count(Notification.id)).where(Notification.user_id == current_user.id)
    unread_query = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
        count_query = count_query.where(Notification.is_read == is_read)
    
    # Filter out expired notifications
    now = datetime.utcnow()
    query = query.where(
        (Notification.expires_at == None) | (Notification.expires_at > now)
    )
    count_query = count_query.where(
        (Notification.expires_at == None) | (Notification.expires_at > now)
    )
    
    # Get counts
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Notification.created_at.desc())
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(
    notification_data: NotificationCreate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Send a notification to a user. Requires teacher or admin role."""
    # Verify target user exists
    result = await db.execute(
        select(User).where(User.id == notification_data.user_id, User.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )
    
    new_notification = Notification(**notification_data.model_dump())
    db.add(new_notification)
    await db.commit()
    await db.refresh(new_notification)
    
    # TODO: Trigger push notification via Celery task
    
    return new_notification


@router.post("/send-bulk", status_code=status.HTTP_201_CREATED)
async def send_bulk_notification(
    notification_data: NotificationBulkCreate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Send notifications to multiple users. Requires admin role."""
    created_count = 0
    
    for user_id in notification_data.user_ids:
        # Verify user exists
        result = await db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        if not result.scalar_one_or_none():
            continue
        
        new_notification = Notification(
            user_id=user_id,
            title=notification_data.title,
            body=notification_data.body,
            notification_type=notification_data.notification_type,
            priority=notification_data.priority,
            action_type=notification_data.action_type,
            action_data=notification_data.action_data,
            expires_at=notification_data.expires_at,
        )
        db.add(new_notification)
        created_count += 1
    
    await db.commit()
    
    # TODO: Trigger bulk push notifications via Celery task
    
    return {"message": f"Created {created_count} notifications", "count": created_count}


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_as_read(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark all notifications as read for the current user."""
    from sqlalchemy import update
    
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()
    
    return {"message": "All notifications marked as read"}
