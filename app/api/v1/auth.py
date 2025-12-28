"""
Authentication API endpoints.
"""
from datetime import datetime, timedelta
from typing import Annotated
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.core.config import settings
from app.core.dependencies import get_current_active_user, CurrentUser
from app.models.user import User, RefreshToken
from app.models.audit import AuditLog, AuditAction
from app.schemas.auth import (
    TokenResponse,
    LoginRequest,
    RefreshRequest,
    LogoutRequest,
    UserResponse,
    PasswordChangeRequest,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


async def create_audit_log(
    db: AsyncSession,
    action: AuditAction,
    user: User = None,
    resource_type: str = "User",
    resource_id: int = None,
    description: str = None,
    request: Request = None,
):
    """Helper to create audit log entries."""
    audit_log = AuditLog(
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        user_role=user.role.value if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(audit_log)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Authenticate user and return access/refresh tokens.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        # Log failed login attempt
        if user:
            await create_audit_log(
                db, AuditAction.LOGIN_FAILED, user,
                description="Invalid password",
                request=request
            )
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store refresh token hash for revocation
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_token_record)
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    
    # Log successful login
    await create_audit_log(
        db, AuditAction.LOGIN, user,
        resource_id=user.id,
        description="Successful login",
        request=request
    )
    
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user.role,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_request: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Refresh access token using a valid refresh token.
    """
    payload = verify_refresh_token(refresh_request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    
    # Verify token not revoked
    token_hash = hashlib.sha256(refresh_request.refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow(),
        )
    )
    token_record = result.scalar_one_or_none()
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired",
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == int(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Revoke old token
    token_record.is_revoked = True
    token_record.revoked_at = datetime.utcnow()
    
    # Create new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store new refresh token
    new_token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()
    new_token_record = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_token_record)
    
    # Log token refresh
    await create_audit_log(
        db, AuditAction.TOKEN_REFRESH, user,
        resource_id=user.id,
        request=request
    )
    
    await db.commit()
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        role=user.role,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    request: Request,
    logout_request: LogoutRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Logout and invalidate refresh token.
    """
    if logout_request.refresh_token:
        token_hash = hashlib.sha256(logout_request.refresh_token.encode()).hexdigest()
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == current_user.id,
            )
        )
        token_record = result.scalar_one_or_none()
        
        if token_record:
            token_record.is_revoked = True
            token_record.revoked_at = datetime.utcnow()
    
    # Log logout
    await create_audit_log(
        db, AuditAction.LOGOUT, current_user,
        resource_id=current_user.id,
        request=request
    )
    
    await db.commit()
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
):
    """
    Get current authenticated user information.
    """
    return current_user


@router.post("/change-password")
async def change_password(
    request: Request,
    password_change: PasswordChangeRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Change current user's password.
    """
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    current_user.hashed_password = get_password_hash(password_change.new_password)
    
    # Log password change
    await create_audit_log(
        db, AuditAction.PASSWORD_CHANGE, current_user,
        resource_id=current_user.id,
        request=request
    )
    
    await db.commit()
    
    return {"message": "Password changed successfully"}
