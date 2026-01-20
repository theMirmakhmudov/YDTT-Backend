
import asyncio
import logging
from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_admin():
    async with async_session_maker() as session:
        logger.info("Creating admin user...")
        password_hash = get_password_hash("password123")
        
        admin = User(
            email="admin@ydtt.uz",
            hashed_password=password_hash,
            first_name="Admin",
            last_name="User",
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        session.add(admin)
        await session.commit()
        logger.info("✓ Created admin: admin@ydtt.uz / password123")

if __name__ == "__main__":
    asyncio.run(create_admin())
