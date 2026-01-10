"""
School, Class, and Subject management API endpoints.
"""
from typing import Annotated, Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.school import School, Class, Subject
from app.models.audit import AuditLog, AuditAction
from app.schemas.school import (
    SchoolCreate,
    SchoolUpdate,
    SchoolResponse,
    SchoolListResponse,
    ClassCreate,
    ClassUpdate,
    ClassResponse,
    ClassListResponse,
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectListResponse,
)


router = APIRouter(tags=["School Management"])


# ==================== Schools ====================


@router.get("/schools/", response_model=SchoolListResponse)
async def list_schools(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    region: Optional[str] = None,
    district: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List schools with pagination and filtering."""
    query = select(School).where(School.is_deleted == False)
    count_query = select(func.count(School.id)).where(School.is_deleted == False)
    
    # Apply filters
    if region:
        query = query.where(School.region == region)
        count_query = count_query.where(School.region == region)
    
    if district:
        query = query.where(School.district == district)
        count_query = count_query.where(School.district == district)
    
    if is_active is not None:
        query = query.where(School.is_active == is_active)
        count_query = count_query.where(School.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (School.name.ilike(search_term)) |
            (School.code.ilike(search_term))
        )
        count_query = count_query.where(
            (School.name.ilike(search_term)) |
            (School.code.ilike(search_term))
        )
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(School.name)
    
    result = await db.execute(query)
    schools = result.scalars().all()
    
    return SchoolListResponse(
        items=[SchoolResponse.model_validate(s) for s in schools],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.post("/schools/", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    request: Request,
    school_data: SchoolCreate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new school. Requires region admin or higher."""
    # Auto-generate school code if not provided
    if not school_data.code:
        # Generate code from school name and region (e.g., TASHKENT_SCHOOL_001)
        # Get count of schools in the region for sequential numbering
        count_query = select(func.count(School.id)).where(
            School.region == school_data.region,
            School.is_deleted == False
        )
        count_result = await db.execute(count_query)
        school_count = count_result.scalar() + 1
        
        # Generate code: REGION_SCH_NNN format
        region_prefix = school_data.region.upper().replace(" ", "_")[:10]
        school_data.code = f"{region_prefix}_SCH_{school_count:03d}"
    
    # Check code uniqueness
    result = await db.execute(select(School).where(School.code == school_data.code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School code already exists",
        )
    
    new_school = School(**school_data.model_dump())
    db.add(new_school)
    await db.flush()
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.SCHOOL_CREATE,
        resource_type="School",
        resource_id=new_school.id,
        new_values={"name": new_school.name, "code": new_school.code},
        ip_address=request.client.host,
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(new_school)
    
    return new_school


@router.get("/schools/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific school by ID."""
    result = await db.execute(
        select(School).where(School.id == school_id, School.is_deleted == False)
    )
    school = result.scalar_one_or_none()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )
    
    return school


@router.put("/schools/{school_id}", response_model=SchoolResponse)
async def update_school(
    request: Request,
    school_id: int,
    school_update: SchoolUpdate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a school. School admins can only update their own school."""
    result = await db.execute(
        select(School).where(School.id == school_id, School.is_deleted == False)
    )
    school = result.scalar_one_or_none()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )
    
    # School admin can only update their school
    if current_user.role == UserRole.SCHOOL_ADMIN:
        if current_user.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this school",
            )
    
    # Update fields
    update_data = school_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(school, field, value)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.SCHOOL_UPDATE,
        resource_type="School",
        resource_id=school.id,
        new_values=update_data,
        ip_address=request.client.host,
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(school)
    
    return school


# ==================== Classes ====================


@router.get("/classes/", response_model=ClassListResponse)
async def list_classes(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    school_id: Optional[int] = None,
    grade: Optional[int] = None,
    academic_year: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List classes with pagination and filtering."""
    query = select(Class)
    count_query = select(func.count(Class.id))
    
    # Apply filters
    if school_id:
        query = query.where(Class.school_id == school_id)
        count_query = count_query.where(Class.school_id == school_id)
    
    if grade:
        query = query.where(Class.grade == grade)
        count_query = count_query.where(Class.grade == grade)
    
    if academic_year:
        query = query.where(Class.academic_year == academic_year)
        count_query = count_query.where(Class.academic_year == academic_year)
    
    if is_active is not None:
        query = query.where(Class.is_active == is_active)
        count_query = count_query.where(Class.is_active == is_active)
    
    # School-level restriction
    if current_user.role == UserRole.SCHOOL_ADMIN:
        query = query.where(Class.school_id == current_user.school_id)
        count_query = count_query.where(Class.school_id == current_user.school_id)
    elif current_user.role in [UserRole.TEACHER, UserRole.STUDENT]:
        query = query.where(Class.school_id == current_user.school_id)
        count_query = count_query.where(Class.school_id == current_user.school_id)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Class.grade, Class.name)
    
    result = await db.execute(query)
    classes = result.scalars().all()
    
    return ClassListResponse(
        items=[ClassResponse.model_validate(c) for c in classes],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.post("/classes/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    request: Request,
    class_data: ClassCreate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new class. School admins can only create in their school."""
    # School admin restriction
    if current_user.role == UserRole.SCHOOL_ADMIN:
        if class_data.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create class in another school",
            )
    
    # Verify school exists
    result = await db.execute(
        select(School).where(School.id == class_data.school_id, School.is_deleted == False)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )
    
    new_class = Class(**class_data.model_dump())
    db.add(new_class)
    await db.flush()
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.CLASS_CREATE,
        resource_type="Class",
        resource_id=new_class.id,
        new_values={"name": new_class.name, "grade": new_class.grade},
        ip_address=request.client.host,
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(new_class)
    
    return new_class


# ==================== Subjects ====================


@router.get("/subjects/", response_model=SubjectListResponse)
async def list_subjects(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List subjects with pagination."""
    query = select(Subject)
    count_query = select(func.count(Subject.id))
    
    if is_active is not None:
        query = query.where(Subject.is_active == is_active)
        count_query = count_query.where(Subject.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Subject.name.ilike(search_term)) |
            (Subject.code.ilike(search_term))
        )
        count_query = count_query.where(
            (Subject.name.ilike(search_term)) |
            (Subject.code.ilike(search_term))
        )
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Subject.name)
    
    result = await db.execute(query)
    subjects = result.scalars().all()
    
    return SubjectListResponse(
        items=[SubjectResponse.model_validate(s) for s in subjects],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.post("/subjects/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new subject. Requires region admin or higher."""
    # Check code uniqueness
    result = await db.execute(select(Subject).where(Subject.code == subject_data.code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject code already exists",
        )
    
    new_subject = Subject(**subject_data.model_dump())
    db.add(new_subject)
    await db.commit()
    await db.refresh(new_subject)
    
    return new_subject
