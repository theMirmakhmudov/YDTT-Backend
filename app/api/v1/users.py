"""
User management API endpoints.
"""
from typing import Annotated, Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.audit import AuditLog, AuditAction
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserRoleUpdate,
    UserResponse,
    UserListResponse,
)


router = APIRouter(prefix="/users", tags=["Users"])


async def create_audit_log(
    db: AsyncSession,
    action: AuditAction,
    user: User,
    resource_type: str = "User",
    resource_id: int = None,
    old_values: dict = None,
    new_values: dict = None,
    request: Request = None,
):
    """Helper to create audit log entries."""
    audit_log = AuditLog(
        user_id=user.id,
        user_email=user.email,
        user_role=user.role.value,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(audit_log)


@router.get("/", response_model=UserListResponse)
async def list_users(
    current_user: Annotated[User, Depends(require_roles(
        UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    school_id: Optional[int] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """
    List users with pagination and filtering.
    Requires admin role.
    """
    query = select(User).where(User.is_deleted == False)
    count_query = select(func.count(User.id)).where(User.is_deleted == False)
    
    # Apply filters
    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    
    if school_id:
        query = query.where(User.school_id == school_id)
        count_query = count_query.where(User.school_id == school_id)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_term)) |
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term))
        )
        count_query = count_query.where(
            (User.email.ilike(search_term)) |
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term))
        )
    
    # Apply school-level restriction for school admins
    if current_user.role == UserRole.SCHOOL_ADMIN:
        query = query.where(User.school_id == current_user.school_id)
        count_query = count_query.where(User.school_id == current_user.school_id)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new user. Requires admin role.
    Role restrictions apply based on creator's role.
    """
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Role hierarchy check
    role_hierarchy = {
        UserRole.SCHOOL_ADMIN: [UserRole.STUDENT, UserRole.TEACHER],
        UserRole.REGION_ADMIN: [UserRole.STUDENT, UserRole.TEACHER, UserRole.SCHOOL_ADMIN],
        UserRole.SUPER_ADMIN: list(UserRole),
        UserRole.TECH_ADMIN: list(UserRole),
    }
    
    allowed_roles = role_hierarchy.get(current_user.role, [])
    if user_data.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot create user with role {user_data.role.value}",
        )
    
    # School admin can only create users in their school
    if current_user.role == UserRole.SCHOOL_ADMIN:
        user_data.school_id = current_user.school_id
    
    # Create user
    new_user = User(
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        middle_name=user_data.middle_name,
        role=user_data.role,
        school_id=user_data.school_id,
        class_id=user_data.class_id,
        preferred_language=user_data.preferred_language,
    )
    db.add(new_user)
    await db.flush()
    
    # Audit log
    await create_audit_log(
        db, AuditAction.USER_CREATE, current_user,
        resource_id=new_user.id,
        new_values={"email": new_user.email, "role": new_user.role.value},
        request=request
    )
    
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get a specific user by ID.
    Users can view themselves, admins can view users in their scope.
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check access rights
    if current_user.id != user_id:
        if current_user.role not in [
            UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
            UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user",
            )
        
        # School admin can only view users in their school
        if current_user.role == UserRole.SCHOOL_ADMIN:
            if user.school_id != current_user.school_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this user",
                )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Update a user. Users can update themselves (limited fields),
    admins can update users in their scope.
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check permissions
    is_self = current_user.id == user_id
    is_admin = current_user.role in [
        UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ]
    
    if not is_self and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )
    
    # Store old values for audit
    old_values = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
    
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Non-admins can only update certain fields
    if not is_admin:
        allowed_fields = {"first_name", "last_name", "middle_name", "phone", "preferred_language"}
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    for field, value in update_data.items():
        if value is not None:
            setattr(user, field, value)
    
    # Audit log
    await create_audit_log(
        db, AuditAction.USER_UPDATE, current_user,
        resource_id=user.id,
        old_values=old_values,
        new_values=update_data,
        request=request
    )
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Soft delete a user. Requires admin role.
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Cannot delete yourself
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
    
    # School admin can only delete users in their school
    if current_user.role == UserRole.SCHOOL_ADMIN:
        if user.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this user",
            )
    
    # Soft delete
    from datetime import datetime
    user.is_deleted = True
    user.is_active = False
    user.deleted_at = datetime.utcnow()
    
    # Audit log
    await create_audit_log(
        db, AuditAction.USER_DELETE, current_user,
        resource_id=user.id,
        request=request
    )
    
    await db.commit()
    
    return {"message": "User deleted successfully"}
