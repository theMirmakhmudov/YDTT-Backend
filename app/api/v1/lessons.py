"""
Lesson and Material API endpoints.
"""
from typing import Annotated, Optional
from math import ceil
from datetime import datetime
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.lesson import Lesson, Material, MaterialType
from app.models.audit import AuditLog, AuditAction
from app.schemas.lesson import (
    LessonCreate,
    LessonUpdate,
    LessonResponse,
    LessonListResponse,
    MaterialResponse,
    MaterialListResponse,
)


router = APIRouter(tags=["Learning Content"])


# ==================== Lessons ====================


@router.get("/lessons/", response_model=LessonListResponse)
async def list_lessons(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject_id: Optional[int] = None,
    grade: Optional[int] = None,
    is_published: Optional[bool] = None,
    search: Optional[str] = None,
):
    """List lessons with pagination and filtering."""
    query = select(Lesson).where(Lesson.is_active == True)
    count_query = select(func.count(Lesson.id)).where(Lesson.is_active == True)
    
    # Students only see published lessons
    if current_user.role == UserRole.STUDENT:
        query = query.where(Lesson.is_published == True)
        count_query = count_query.where(Lesson.is_published == True)
    elif is_published is not None:
        query = query.where(Lesson.is_published == is_published)
        count_query = count_query.where(Lesson.is_published == is_published)
    
    if subject_id:
        query = query.where(Lesson.subject_id == subject_id)
        count_query = count_query.where(Lesson.subject_id == subject_id)
    
    if grade:
        query = query.where(Lesson.grade == grade)
        count_query = count_query.where(Lesson.grade == grade)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(Lesson.title.ilike(search_term))
        count_query = count_query.where(Lesson.title.ilike(search_term))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Lesson.grade, Lesson.order)
    
    result = await db.execute(query)
    lessons = result.scalars().all()
    
    return LessonListResponse(
        items=[LessonResponse.model_validate(l) for l in lessons],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.post("/lessons/", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson_data: LessonCreate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN, 
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new lesson. Requires teacher or admin role."""
    new_lesson = Lesson(
        **lesson_data.model_dump(),
        created_by_id=current_user.id,
    )
    db.add(new_lesson)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.LESSON_CREATE,
        resource_type="Lesson",
        new_values={"title": new_lesson.title},
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(new_lesson)
    
    return new_lesson


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific lesson by ID."""
    query = select(Lesson).where(Lesson.id == lesson_id, Lesson.is_active == True)
    
    # Students only see published lessons
    if current_user.role == UserRole.STUDENT:
        query = query.where(Lesson.is_published == True)
    
    result = await db.execute(query)
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    
    return lesson


@router.put("/lessons/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    lesson_update: LessonUpdate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a lesson."""
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.is_active == True)
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    
    # Teachers can only update their own lessons
    if current_user.role == UserRole.TEACHER:
        if lesson.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update another teacher's lesson",
            )
    
    # Track if publishing
    was_published = lesson.is_published
    
    update_data = lesson_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(lesson, field, value)
    
    # Set published timestamp
    if not was_published and lesson.is_published:
        lesson.published_at = datetime.utcnow()
        lesson.version += 1
    
    # Audit log
    action = AuditAction.LESSON_PUBLISH if (not was_published and lesson.is_published) else AuditAction.LESSON_UPDATE
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=action,
        resource_type="Lesson",
        resource_id=lesson.id,
        new_values=update_data,
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(lesson)
    
    return lesson


# ==================== Materials ====================


@router.get("/materials/", response_model=MaterialListResponse)
async def list_materials(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lesson_id: Optional[int] = None,
    material_type: Optional[MaterialType] = None,
):
    """List materials with pagination."""
    query = select(Material).where(Material.is_active == True)
    count_query = select(func.count(Material.id)).where(Material.is_active == True)
    
    if lesson_id:
        query = query.where(Material.lesson_id == lesson_id)
        count_query = count_query.where(Material.lesson_id == lesson_id)
    
    if material_type:
        query = query.where(Material.material_type == material_type)
        count_query = count_query.where(Material.material_type == material_type)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Material.created_at.desc())
    
    result = await db.execute(query)
    materials = result.scalars().all()
    
    return MaterialListResponse(
        items=[MaterialResponse.model_validate(m) for m in materials],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.post("/materials/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    lesson_id: int,
    title: str,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Upload a new material file."""
    # Verify lesson exists
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.is_active == True)
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Calculate checksum
    checksum = hashlib.sha256(content).hexdigest()
    
    # Determine material type from mime type
    mime_type = file.content_type or "application/octet-stream"
    if mime_type.startswith("video/"):
        material_type = MaterialType.VIDEO
    elif mime_type.startswith("audio/"):
        material_type = MaterialType.AUDIO
    elif mime_type.startswith("image/"):
        material_type = MaterialType.IMAGE
    elif mime_type == "application/pdf":
        material_type = MaterialType.PDF
    else:
        material_type = MaterialType.TEXT
    
    # Generate file path (would integrate with MinIO in production)
    file_path = f"materials/{lesson_id}/{checksum}_{file.filename}"
    
    # Create material record
    new_material = Material(
        title=title,
        description=description,
        file_path=file_path,
        file_name=file.filename,
        file_size=file_size,
        mime_type=mime_type,
        material_type=material_type,
        checksum=checksum,
        lesson_id=lesson_id,
        created_by_id=current_user.id,
    )
    db.add(new_material)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.MATERIAL_UPLOAD,
        resource_type="Material",
        new_values={"title": title, "file_name": file.filename, "checksum": checksum},
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(new_material)
    
    # TODO: Actually upload file to MinIO storage here
    
    return new_material
