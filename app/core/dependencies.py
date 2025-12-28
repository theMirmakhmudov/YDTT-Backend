"""
FastAPI Dependencies for the application.
"""
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_access_token
from app.core.config import settings
from app.models.user import User, UserRole


# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Get the current authenticated user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == int(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Ensure the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_roles(*roles: UserRole):
    """Dependency factory for role-based access control."""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in roles]}"
            )
        return current_user
    return role_checker


async def get_accept_language(
    accept_language: str = Header(default=None)
) -> str:
    """Get the preferred language from Accept-Language header."""
    if accept_language:
        # Parse the first language from the header
        lang = accept_language.split(",")[0].split(";")[0].strip().lower()
        # Check if supported
        if lang in settings.SUPPORTED_LANGUAGES:
            return lang
        # Check language code without region
        lang_code = lang.split("-")[0]
        if lang_code in settings.SUPPORTED_LANGUAGES:
            return lang_code
    return settings.DEFAULT_LANGUAGE


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_active_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
Language = Annotated[str, Depends(get_accept_language)]
