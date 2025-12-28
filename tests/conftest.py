"""
Shared test fixtures and configuration.
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app as fastapi_app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole
import app.models  # Import all models to ensure Base.metadata is complete (handles FKs)

import os

# Use SQLite for tests by default, allow override (e.g. for Docker/CI)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_db(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Get a test database session.
    This creates a new session for each test function.
    """
    async_session = async_sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Override get_db dependency
        async def override_get_db():
            yield session
        
        fastapi_app.dependency_overrides[get_db] = override_get_db
        yield session
        fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a standard test student user."""
    user = User(
        email="student@example.com",
        hashed_password=get_password_hash("password123"),
        first_name="Test",
        last_name="Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def teacher_user(test_db: AsyncSession) -> User:
    """Create a teacher user."""
    user = User(
        email="teacher@example.com",
        hashed_password=get_password_hash("password123"),
        first_name="Test",
        last_name="Teacher",
        role=UserRole.TEACHER,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def admin_user(test_db: AsyncSession) -> User:
    """Create a super admin user."""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def user_token_headers(test_user: User) -> dict:
    """Get auth headers for student user."""
    data = {"sub": str(test_user.id), "role": test_user.role}
    token = create_access_token(data=data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def teacher_token_headers(teacher_user: User) -> dict:
    """Get auth headers for teacher user."""
    data = {"sub": str(teacher_user.id), "role": teacher_user.role}
    token = create_access_token(data=data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token_headers(admin_user: User) -> dict:
    """Get auth headers for admin user."""
    data = {"sub": str(admin_user.id), "role": admin_user.role}
    token = create_access_token(data=data)
    return {"Authorization": f"Bearer {token}"}
