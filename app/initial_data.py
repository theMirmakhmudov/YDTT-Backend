"""
Initial data seeder for YDTT Backend.
Creates a default superadmin user if one doesn't exist.
"""
import asyncio
import logging
from sqlalchemy import select

from app.core.database import async_session_maker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_initial_data() -> None:
    """Create initial audit user."""
    logger.info("Creating initial data...")
    
    async with async_session_maker() as session:
        # Check if admin exists
        stmt = select(User).where(User.email == settings.FIRST_SUPERUSER)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"Admin user {settings.FIRST_SUPERUSER} already exists.")
            return

        # Create admin
        admin = User(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            first_name="Admin",
            last_name="User",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_deleted=False,
        )
        session.add(admin)
        await session.commit()
        
        logger.info("Superuser created successfully.")
        logger.info(f"Email: {settings.FIRST_SUPERUSER}")
        logger.info("Password: [HIDDEN]")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_initial_data())
