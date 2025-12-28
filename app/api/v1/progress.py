"""
Progress tracking and analytics API endpoints.
"""
from typing import Annotated, Optional
from math import ceil
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.exam import ExamAttempt, Result, AttemptStatus
from app.models.audit import AuditLog, AuditAction
from app.schemas.progress import (
    StudentProgressResponse,
    ClassProgressResponse,
    DashboardAnalytics,
    AuditLogResponse,
    AuditLogListResponse,
)


router = APIRouter(tags=["Progress & Analytics"])


@router.get("/progress/student/{student_id}", response_model=StudentProgressResponse)
async def get_student_progress(
    student_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get progress for a specific student."""
    # Check permissions
    if current_user.id != student_id:
        if current_user.role not in [
            UserRole.TEACHER, UserRole.SCHOOL_ADMIN,
            UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this student's progress",
            )
    
    # Get basic exam stats
    total_attempts = await db.execute(
        select(func.count(ExamAttempt.id)).where(ExamAttempt.student_id == student_id)
    )
    total_exams = total_attempts.scalar() or 0
    
    completed_result = await db.execute(
        select(func.count(ExamAttempt.id)).where(
            ExamAttempt.student_id == student_id,
            ExamAttempt.status == AttemptStatus.EVALUATED,
        )
    )
    completed_exams = completed_result.scalar() or 0
    
    # Get results for pass/fail
    result = await db.execute(
        select(Result)
        .join(ExamAttempt)
        .where(ExamAttempt.student_id == student_id)
    )
    results = result.scalars().all()
    
    passed_exams = sum(1 for r in results if r.is_passed)
    failed_exams = completed_exams - passed_exams
    
    # Calculate average score
    if results:
        average_score = sum(r.percentage for r in results) / len(results)
    else:
        average_score = 0.0
    
    # Calculate rates
    completion_rate = (completed_exams / total_exams * 100) if total_exams > 0 else 0
    pass_rate = (passed_exams / completed_exams * 100) if completed_exams > 0 else 0
    
    # Get recent exams
    recent_result = await db.execute(
        select(ExamAttempt)
        .where(ExamAttempt.student_id == student_id)
        .order_by(ExamAttempt.created_at.desc())
        .limit(10)
    )
    recent_attempts = recent_result.scalars().all()
    
    recent_exams = [
        {
            "exam_id": a.exam_id,
            "attempt_id": a.id,
            "status": a.status.value,
            "created_at": a.created_at.isoformat(),
        }
        for a in recent_attempts
    ]
    
    return StudentProgressResponse(
        student_id=student_id,
        total_exams=total_exams,
        completed_exams=completed_exams,
        passed_exams=passed_exams,
        failed_exams=failed_exams,
        average_score=round(average_score, 2),
        completion_rate=round(completion_rate, 2),
        pass_rate=round(pass_rate, 2),
        subject_progress=[],  # TODO: Add subject breakdown
        recent_exams=recent_exams,
    )


@router.get("/progress/class/{class_id}", response_model=ClassProgressResponse)
async def get_class_progress(
    class_id: int,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get progress for a class. Requires teacher or admin role."""
    from app.models.school import Class
    
    # Get class
    result = await db.execute(select(Class).where(Class.id == class_id))
    class_ = result.scalar_one_or_none()
    
    if not class_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )
    
    # Get students in class
    result = await db.execute(
        select(func.count(User.id)).where(
            User.class_id == class_id,
            User.is_active == True,
            User.role == UserRole.STUDENT,
        )
    )
    total_students = result.scalar() or 0
    
    # Get all results for students in this class
    result = await db.execute(
        select(Result)
        .join(ExamAttempt)
        .join(User, ExamAttempt.student_id == User.id)
        .where(User.class_id == class_id)
    )
    results = result.scalars().all()
    
    # Calculate stats
    if results:
        average_score = sum(r.percentage for r in results) / len(results)
        passed = sum(1 for r in results if r.is_passed)
        pass_rate = (passed / len(results) * 100)
    else:
        average_score = 0.0
        pass_rate = 0.0
    
    return ClassProgressResponse(
        class_id=class_id,
        class_name=class_.name,
        total_students=total_students,
        average_score=round(average_score, 2),
        completion_rate=0.0,  # TODO: Calculate properly
        pass_rate=round(pass_rate, 2),
        subject_stats=[],
        top_performers=[],
        struggling_students=[],
    )


@router.get("/analytics/dashboard", response_model=DashboardAnalytics)
async def get_dashboard_analytics(
    current_user: Annotated[User, Depends(require_roles(
        UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get dashboard analytics. Requires admin role."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # User metrics
    total_users = await db.execute(select(func.count(User.id)).where(User.is_deleted == False))
    total_users = total_users.scalar() or 0
    
    # Active users (logged in)
    active_today = await db.execute(
        select(func.count(User.id)).where(
            User.last_login_at >= today_start,
            User.is_active == True
        )
    )
    active_today = active_today.scalar() or 0
    
    active_month = await db.execute(
        select(func.count(User.id)).where(
            User.last_login_at >= month_start,
            User.is_active == True
        )
    )
    active_month = active_month.scalar() or 0
    
    # Exam metrics
    from app.models.exam import Exam
    
    total_exams = await db.execute(select(func.count(Exam.id)))
    total_exams = total_exams.scalar() or 0
    
    exams_today = await db.execute(
        select(func.count(ExamAttempt.id)).where(
            ExamAttempt.submitted_at >= today_start,
            ExamAttempt.status == AttemptStatus.EVALUATED,
        )
    )
    exams_today = exams_today.scalar() or 0
    
    exams_month = await db.execute(
        select(func.count(ExamAttempt.id)).where(
            ExamAttempt.submitted_at >= month_start,
            ExamAttempt.status == AttemptStatus.EVALUATED,
        )
    )
    exams_month = exams_month.scalar() or 0
    
    # Average score
    avg_result = await db.execute(select(func.avg(Result.percentage)))
    avg_score = avg_result.scalar() or 0.0
    
    # Anti-cheating metrics
    from app.models.anti_cheat import CheatingEvent
    
    cheating_today = await db.execute(
        select(func.count(CheatingEvent.id)).where(
            CheatingEvent.recorded_at >= today_start
        )
    )
    cheating_today = cheating_today.scalar() or 0
    
    return DashboardAnalytics(
        total_users=total_users,
        active_users_today=active_today,
        active_users_month=active_month,
        dau=active_today,
        mau=active_month,
        total_exams=total_exams,
        exams_completed_today=exams_today,
        exams_completed_month=exams_month,
        average_exam_score=round(avg_score, 2),
        exam_completion_rate=0.0,  # TODO: Calculate
        cheating_events_today=cheating_today,
        cheating_detection_ratio=0.0,  # TODO: Calculate
        retention_rate_7d=0.0,  # TODO: Calculate
        retention_rate_30d=0.0,  # TODO: Calculate
        daily_active_users_trend=[],  # TODO: Calculate
        daily_exams_trend=[],  # TODO: Calculate
        daily_registrations_trend=[],  # TODO: Calculate
    )


# ==================== Audit Logs ====================


@router.get("/audit-logs/", response_model=AuditLogListResponse)
async def list_audit_logs(
    current_user: Annotated[User, Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[AuditAction] = None,
    resource_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    """
    List audit logs. Read-only, no deletion allowed.
    Requires super admin or tech admin role.
    """
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)
    
    if from_date:
        query = query.where(AuditLog.created_at >= from_date)
        count_query = count_query.where(AuditLog.created_at >= from_date)
    
    if to_date:
        query = query.where(AuditLog.created_at <= to_date)
        count_query = count_query.where(AuditLog.created_at <= to_date)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(AuditLog.created_at.desc())
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(l) for l in logs],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )
