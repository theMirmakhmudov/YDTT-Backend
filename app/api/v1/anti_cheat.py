"""
Anti-cheating API endpoints.
"""
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.exam import ExamAttempt
from app.models.anti_cheat import CheatingEvent, CheatingEventType
from app.schemas.anti_cheat import (
    CheatingEventCreate,
    CheatingEventResponse,
    CheatingReportResponse,
)


router = APIRouter(prefix="/anti-cheat", tags=["Anti-Cheating"])


# Severity weights for risk calculation
SEVERITY_WEIGHTS = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 4,
    "CRITICAL": 8,
}


@router.post("/event", response_model=CheatingEventResponse, status_code=status.HTTP_201_CREATED)
async def log_cheating_event(
    request: Request,
    event_data: CheatingEventCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Log a cheating event detected by the client.
    Events are immutable once created.
    """
    # Verify attempt exists and belongs to user
    result = await db.execute(
        select(ExamAttempt).where(ExamAttempt.id == event_data.attempt_id)
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam attempt not found",
        )
    
    if attempt.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot log events for another user's attempt",
        )
    
    # Check for duplicate offline_id
    if event_data.offline_id:
        result = await db.execute(
            select(CheatingEvent).where(CheatingEvent.offline_id == event_data.offline_id)
        )
        if result.scalar_one_or_none():
            # Already logged, return success (idempotent)
            result = await db.execute(
                select(CheatingEvent).where(CheatingEvent.offline_id == event_data.offline_id)
            )
            existing = result.scalar_one()
            return CheatingEventResponse.model_validate(existing)
    
    # Create immutable event record
    new_event = CheatingEvent(
        attempt_id=event_data.attempt_id,
        event_type=event_data.event_type,
        severity=event_data.severity.upper(),
        description=event_data.description,
        device_id=event_data.device_id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        event_metadata=event_data.metadata,
        occurred_at=event_data.occurred_at,
        offline_id=event_data.offline_id,
    )
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    
    return CheatingEventResponse.model_validate(new_event)


@router.get("/report/{attempt_id}", response_model=CheatingReportResponse)
async def get_cheating_report(
    attempt_id: int,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get anti-cheating report for an exam attempt.
    Requires teacher or admin role.
    """
    # Verify attempt exists
    result = await db.execute(
        select(ExamAttempt).where(ExamAttempt.id == attempt_id)
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam attempt not found",
        )
    
    # Get all events for this attempt
    result = await db.execute(
        select(CheatingEvent)
        .where(CheatingEvent.attempt_id == attempt_id)
        .order_by(CheatingEvent.occurred_at)
    )
    events = result.scalars().all()
    
    # Count by severity
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    total_weight = 0
    
    for event in events:
        severity = event.severity.upper()
        if severity in severity_counts:
            severity_counts[severity] += 1
            total_weight += SEVERITY_WEIGHTS.get(severity, 2)
    
    # Calculate risk score (0-100)
    # Higher weight = higher risk
    max_reasonable_weight = 50  # Threshold for max risk
    risk_score = min(100, (total_weight / max_reasonable_weight) * 100)
    
    # Determine risk level
    if risk_score >= 75:
        risk_level = "CRITICAL"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return CheatingReportResponse(
        attempt_id=attempt_id,
        total_events=len(events),
        critical_count=severity_counts["CRITICAL"],
        high_count=severity_counts["HIGH"],
        medium_count=severity_counts["MEDIUM"],
        low_count=severity_counts["LOW"],
        events=[CheatingEventResponse.model_validate(e) for e in events],
        risk_score=risk_score,
        risk_level=risk_level,
    )
