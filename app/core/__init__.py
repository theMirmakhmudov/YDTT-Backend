"""Core module initialization."""
from app.core.config import settings
from app.core.database import Base, get_db, engine
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
)

# Note: dependencies are imported directly in API routers to avoid circular imports

__all__ = [
    "settings",
    "Base",
    "get_db",
    "engine",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "verify_access_token",
    "verify_refresh_token",
]
