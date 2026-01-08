from typing import Optional
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi import status

from app.core.security import verify_password, create_access_token, decode_token
from app.core.config import settings
from app.models.user import User, UserRole
from app.core.database import async_session_maker
from sqlalchemy import select

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        async with async_session_maker() as session:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return False
            
            if not verify_password(password, user.hashed_password):
                return False
                
            if user.role != UserRole.SUPER_ADMIN:
                return False

            # Create session/token
            access_token = create_access_token(
                data={"sub": str(user.id), "role": user.role},
                expires_delta=None # Default expiration
            )
            
            request.session.update({"token": access_token})
            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        payload = decode_token(token)
        if not payload:
            return False
            
        role = payload.get("role")
        if role != UserRole.SUPER_ADMIN:
            return False
            
        return True

authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
