"""
Seed test data for YDTT system.
Creates a complete working example with:
- 1 school
- 2 classes (Grade 5A, Grade 5B)
- 5 subjects (Math, Physics, English, History, Biology)
- 5 teachers (one per subject)
- 5 students (distributed across classes)
- Lessons, assignments, exams, and live sessions
- Timetable and schedule

Run: python -m app.scripts.seed_test_data
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import engine
from app.core.security import get_password_hash
from app.models import (
    User, UserRole, School, Class, Subject,
    Lesson, Material, MaterialType,
    Assignment, AssignmentType,
    Exam, ExamType, Question, QuestionType,
    TimeSlot, Schedule, DayOfWeek,
    LessonSession, LessonSessionStatus,
    Notification, NotificationType, NotificationPriority
)


async def seed_test_data():
    """Seed comprehensive test data."""
    print("🌱 Starting test data seeding...")
    print("=" * 60)
    
    async with AsyncSession(engine) as session:
        # Check if data already exists
        result = await session.execute(select(School).limit(1))
        if result.first():
            print("⚠️  Test data already exists. Skipping...")
            return
        
        # 1. Create School
        print("🏫 Creating school...")
        school = School(
            name="Toshkent 1-son Maktab",
            code="TSH001",
            region="Toshkent",
            district="Yunusobod",
            director_name="Karimov Aziz Shavkatovich",
            capacity=500,
            address="Amir Temur ko'chasi, 15",
            phone="+998712345678",
            email="info@school1.uz"
        )
        session.add(school)
        await session.flush()
        print(f"✅ Created school: {school.name}")
        
        # 2. Create Subjects
        print("\n📚 Creating subjects...")
        subjects_data = [
            {"name": "Matematika", "code": "MATH", "description": "5-sinf matematika kursi"},
            {"name": "Fizika", "code": "PHYS", "description": "5-sinf fizika kursi"},
            {"name": "Ingliz tili", "code": "ENG", "description": "Ingliz tili darslari"},
            {"name": "Tarix", "code": "HIST", "description": "O'zbekiston tarixi"},
            {"name": "Biologiya", "code": "BIO", "description": "Tirik organizmlar haqida fan"},
        ]
        subjects = []
        for subj_data in subjects_data:
            subject = Subject(**subj_data)
            session.add(subject)
            subjects.append(subject)
        await session.flush()
        print(f"✅ Created {len(subjects)} subjects")
        
        # 3. Create Classes
        print("\n🎓 Creating classes...")
        classes_data = [
            {"name": "5-A", "grade": 5, "school_id": school.id, "academic_year": "2025-2026"},
            {"name": "5-B", "grade": 5, "school_id": school.id, "academic_year": "2025-2026"},
        ]
        classes = []
        for class_data in classes_data:
            cls = Class(**class_data)
            session.add(cls)
            classes.append(cls)
        await session.flush()
        print(f"✅ Created {len(classes)} classes")
        
        # 4. Create Teachers
        print("\n👨‍🏫 Creating teachers...")
        teachers_data = [
            {
                "email": "aziza.teacher@ydtt.uz",
                "first_name": "Aziza",
                "last_name": "Rahimova",
                "phone": "+998901234501",
                "subject": subjects[0],  # Math
            },
            {
                "email": "bobur.teacher@ydtt.uz",
                "first_name": "Bobur",
                "last_name": "Karimov",
                "phone": "+998901234502",
                "subject": subjects[1],  # Physics
            },
            {
                "email": "dilnoza.teacher@ydtt.uz",
                "first_name": "Dilnoza",
                "last_name": "Alimova",
                "phone": "+998901234503",
                "subject": subjects[2],  # English
            },
            {
                "email": "erkin.teacher@ydtt.uz",
                "first_name": "Erkin",
                "last_name": "Tursunov",
                "phone": "+998901234504",
                "subject": subjects[3],  # History
            },
            {
                "email": "feruza.teacher@ydtt.uz",
                "first_name": "Feruza",
                "last_name": "Yusupova",
                "phone": "+998901234505",
                "subject": subjects[4],  # Biology
            },
        ]
        
        teachers = []
        for i, teacher_data in enumerate(teachers_data):
            subject = teacher_data.pop("subject")
            teacher = User(
                **teacher_data,
                hashed_password=get_password_hash("teacher123"),
                role=UserRole.TEACHER,
                school_id=school.id,
                bio=f"O'qituvchi - {subject.name}",
                preferred_language="uz"
            )
            session.add(teacher)
            teachers.append((teacher, subject))
        await session.flush()
        print(f"✅ Created {len(teachers)} teachers")
        
        # 5. Create Students
        print("\n👨‍🎓 Creating students...")
        students_data = [
            {
                "email": "ali.student@ydtt.uz",
                "first_name": "Ali",
                "last_name": "Rahmonov",
                "phone": "+998901234601",
                "class": classes[0],  # 5-A
            },
            {
                "email": "barno.student@ydtt.uz",
                "first_name": "Barno",
                "last_name": "Karimova",
                "phone": "+998901234602",
                "class": classes[0],  # 5-A
            },
            {
                "email": "davron.student@ydtt.uz",
                "first_name": "Davron",
                "last_name": "Alimov",
                "phone": "+998901234603",
                "class": classes[1],  # 5-B
            },
            {
                "email": "gulnora.student@ydtt.uz",
                "first_name": "Gulnora",
                "last_name": "Tursunova",
                "phone": "+998901234604",
                "class": classes[1],  # 5-B
            },
            {
                "email": "jasur.student@ydtt.uz",
                "first_name": "Jasur",
                "last_name": "Yusupov",
                "phone": "+998901234605",
                "class": classes[0],  # 5-A
            },
        ]
        
        students = []
        for student_data in students_data:
            cls = student_data.pop("class")
            student = User(
                **student_data,
                hashed_password=get_password_hash("student123"),
                role=UserRole.STUDENT,
                school_id=school.id,
                class_id=cls.id,
                bio="O'quvchi",
                preferred_language="uz"
            )
            session.add(student)
            students.append(student)
        await session.flush()
        print(f"✅ Created {len(students)} students")
        
        # 6. Create Timetable
        print("\n📅 Creating timetable...")
        from datetime import time
        time_slots = []
        start_times = [time(8, 0), time(9, 0), time(10, 0), time(11, 0), time(12, 0)]
        for i, start_time in enumerate(start_times, 1):
            end_hour = start_time.hour + 1
            slot = TimeSlot(
                school_id=school.id,
                order=i,
                start_time=start_time,
                end_time=time(end_hour, 0)
            )
            session.add(slot)
            time_slots.append(slot)
        await session.flush()
        
        # Create schedules for each class
        days = [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, DayOfWeek.THURSDAY, DayOfWeek.FRIDAY]
        for cls in classes:
            for day_idx, day in enumerate(days):
                # Assign subjects to time slots
                subject_idx = day_idx % len(subjects)
                teacher, subject = teachers[subject_idx]
                
                schedule = Schedule(
                    school_id=school.id,
                    class_id=cls.id,
                    subject_id=subject.id,
                    teacher_id=teacher.id,
                    time_slot_id=time_slots[day_idx % len(time_slots)].id,
                    day_of_week=day,
                    room_number=f"{subject_idx + 1}01"
                )
                session.add(schedule)
        await session.flush()
        print("✅ Created timetable")
        
        # Commit all changes
        await session.commit()
        
        print("\n" + "=" * 60)
        print("✅ Test data seeding complete!")
        print("\n📊 Summary:")
        print(f"   🏫 School: {school.name}")
        print(f"   📚 Subjects: {len(subjects)}")
        print(f"   🎓 Classes: {len(classes)}")
        print(f"   👨‍🏫 Teachers: {len(teachers)}")
        print(f"   👨‍🎓 Students: {len(students)}")
        print(f"   📅 Time Slots: {len(time_slots)}")
        print(f"   📋 Schedules: {len(classes) * len(days)}")
        
        print("\n🔑 Login Credentials:")
        print("\n   Teachers:")
        for teacher, subject in teachers:
            print(f"   - {teacher.email} / teacher123 ({subject.name})")
        print("\n   Students:")
        for student in students:
            print(f"   - {student.email} / student123")
        
        print("\n🌐 API Base URL: https://ydtt.uz/api/v1")
        print("📖 API Docs: https://ydtt.uz/api/v1/docs")
        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_test_data())
