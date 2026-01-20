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
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Get a test database session.
    Alias for test_db for compatibility.
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
async def test_db(db_session):
    """Alias for db_session."""
    return db_session


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
def student_token(test_user: User) -> str:
    """Get raw token for student."""
    data = {"sub": str(test_user.id), "role": test_user.role}
    return create_access_token(data=data)


@pytest.fixture
def teacher_token_headers(teacher_user: User) -> dict:
    """Get auth headers for teacher user."""
    data = {"sub": str(teacher_user.id), "role": teacher_user.role}
    token = create_access_token(data=data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def teacher_token(teacher_user: User) -> str:
    """Get raw token for teacher."""
    data = {"sub": str(teacher_user.id), "role": teacher_user.role}
    return create_access_token(data=data)


@pytest.fixture
def admin_token_headers(admin_user: User) -> dict:
    """Get auth headers for admin user."""
    data = {"sub": str(admin_user.id), "role": admin_user.role}
    token = create_access_token(data=data)
    return {"Authorization": f"Bearer {token}"}


# ==================== School Fixtures ====================

@pytest.fixture
async def test_subject(test_db: AsyncSession) -> "Subject":
    """Create a test subject."""
    from app.models.school import Subject
    subject = Subject(name="Test Math", code="MATH101")
    test_db.add(subject)
    await test_db.commit()
    await test_db.refresh(subject)
    return subject


@pytest.fixture
async def test_class(test_db: AsyncSession) -> "Class":
    """Create a test class."""
    from app.models.school import Class
    # Need a school first? Assuming School is optional or defined elsewhere?
    # Checking models... Class usually needs a School.
    # For now, let's assume we need a school.
    from app.models.school import School
    school = School(
        name="Test School", 
        code="SCH-001", 
        address="123 Test St",
        region="Test Region",
        district="Test District"
    )
    test_db.add(school)
    await test_db.commit()
    await test_db.refresh(school)
    
    cls = Class(
        name="10-A", 
        grade=10, 
        academic_year="2024-2025", 
        school_id=school.id
    )
    test_db.add(cls)
    await test_db.commit()
    await test_db.refresh(cls)
    return cls


@pytest.fixture
async def test_student(test_db: AsyncSession, test_user: User, test_class: "Class") -> User:
    """
    Ensure the test student is assigned to the test class.
    Renaming/Using test_user as base.
    """
    test_user.class_id = test_class.id
    test_db.add(test_user)
    await test_db.commit()
    await test_db.refresh(test_user)
    return test_user


@pytest.fixture
async def test_schedule(
    test_db: AsyncSession, 
    teacher_user: User, 
    test_class: "Class", 
    test_subject: "Subject"
) -> "Schedule":
    """Create a schedule item for the teacher."""
    from app.models.timetable import Schedule
    # Need a time slot
    from app.models.timetable import TimeSlot
    from app.models.timetable import DayOfWeek
    from datetime import time
    
    slot = TimeSlot(
        start_time=time(8, 0), 
        end_time=time(9, 0),
        school_id=test_class.school_id,
        order=1
    )
    test_db.add(slot)
    await test_db.commit()
    await test_db.refresh(slot)
    
    schedule = Schedule(
        teacher_id=teacher_user.id,
        class_id=test_class.id,
        subject_id=test_subject.id,
        school_id=test_class.school_id,
        time_slot_id=slot.id,
        day_of_week=DayOfWeek.MONDAY, 
        room_number="101"
    )
    test_db.add(schedule)
    await test_db.commit()
    await test_db.refresh(schedule)
    
    # Eager load relationships for API responses
    # Re-fetch to ensure relationships are loaded if needed
    return schedule


@pytest.fixture
async def active_session(
    test_db: AsyncSession,
    test_schedule: "Schedule"
) -> "LessonSession":
    """Create an active lesson session."""
    from app.models.lesson_session import LessonSession, LessonSessionStatus
    from datetime import datetime
    
    session = LessonSession(
        schedule_id=test_schedule.id,
        teacher_id=test_schedule.teacher_id,
        class_id=test_schedule.class_id,
        subject_id=test_schedule.subject_id,
        topic="Active Session Topic",
        status=LessonSessionStatus.ACTIVE,
        started_at=datetime.utcnow()
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    return session


@pytest.fixture
async def session_different_class(
    test_db: AsyncSession,
    teacher_user: User,
    test_subject: "Subject"
) -> "LessonSession":
    """Create a session for a different class (for RBAC testing)."""
    from app.models.school import School, Class
    from app.models.lesson_session import LessonSession, LessonSessionStatus
    from datetime import datetime
    
    # Create another school/class
    school = School(
        name="Another School", 
        code="SCH-002", 
        address="456 Other St",
        region="Other Region",
        district="Other District"
    )
    test_db.add(school)
    await test_db.commit()
    
    cls = Class(
        name="11-B", 
        grade=11, 
        academic_year="2024-2025", 
        school_id=school.id
    )
    test_db.add(cls)
    await test_db.commit()
    
    # Create valid schedule for ad-hoc session requirement
    from app.models.timetable import Schedule, TimeSlot, DayOfWeek
    from datetime import time
    
    # Need a time slot for this school
    slot = TimeSlot(
        start_time=time(10, 0), 
        end_time=time(11, 0),
        school_id=school.id,
        order=1
    )
    test_db.add(slot)
    await test_db.commit()
    await test_db.refresh(slot)
    
    schedule = Schedule(
        teacher_id=teacher_user.id,
        class_id=cls.id,
        subject_id=test_subject.id,
        school_id=school.id,
        time_slot_id=slot.id,
        day_of_week=DayOfWeek.TUESDAY, 
        room_number="102"
    )
    test_db.add(schedule)
    await test_db.commit()
    await test_db.refresh(schedule)
    
    # Create session linked to schedule
    session = LessonSession(
        schedule_id=schedule.id,
        teacher_id=teacher_user.id,
        class_id=cls.id,
        subject_id=test_subject.id,
        topic="Different Class Session",
        status=LessonSessionStatus.ACTIVE,
        started_at=datetime.utcnow()
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    return session
