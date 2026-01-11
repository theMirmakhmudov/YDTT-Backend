"""
Seed script to populate the database with test data.
Run: python -m app.seed_data
"""
import asyncio
from datetime import datetime, date, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.user import User, UserRole
from app.models.school import School, Class, Subject
from app.models.timetable import TimeSlot, Schedule, DayOfWeek
from app.models.lesson import Lesson
from app.models.library import LibraryBook
from app.models.exam import Exam, Question, QuestionType
from app.models.journal import Attendance, Grade, AttendanceStatus, GradeType
from app.models.assignment import Assignment, AssignmentType
from app.core.security import get_password_hash


async def seed_database():
    """Populate database with comprehensive test data."""
    async with async_session_maker() as db:
        print("🌱 Starting database seeding...")
        
        # 1. Create Schools
        print("📚 Creating schools...")
        schools = []
        regions = [
            ("Tashkent", "Yunusabad"),
            ("Tashkent", "Mirzo Ulugbek"),
            ("Samarkand", "Center"),
            ("Bukhara", "Historic District")
        ]
        
        for region, district in regions:
            # Check if exists
            result = await db.execute(
                select(School).where(School.region == region, School.district == district)
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                school = School(
                    name=f"School #{len(schools) + 1}",
                    region=region,
                    district=district,
                    director_name=f"Director {len(schools) + 1}",
                    capacity=500 + (len(schools) * 100),
                    phone=f"+99890123{len(schools):04d}",
                    email=f"school{len(schools) + 1}@ydtt.uz",
                    address=f"{len(schools) + 1} Education Street",
                    code=f"{region.upper()}_SCH_{len(schools) + 1:03d}"
                )
                db.add(school)
                schools.append(school)
        
        await db.flush()
        print(f"   ✓ Created {len(schools)} schools")
        
        # If no new schools created, get existing ones
        if not schools:
            result = await db.execute(select(School).limit(4))
            schools = list(result.scalars().all())
        
        # 2. Create Subjects
        print("📖 Creating subjects...")
        subjects_data = [
            ("Mathematics", "Core mathematics curriculum"),
            ("Physics", "Introduction to physics"),
            ("Chemistry", "Basic chemistry"),
            ("English", "English language"),
            ("Uzbek Language", "Native language studies"),
            ("History", "World and Uzbek history"),
            ("Biology", "Life sciences"),
            ("Geography", "World geography"),
        ]
        
        subjects = []
        for name, desc in subjects_data:
            result = await db.execute(select(Subject).where(Subject.name == name))
            existing = result.scalar_one_or_none()
            
            if not existing:
                subject = Subject(
                    name=name,
                    description=desc,
                    code=f"{name.upper().replace(' ', '_')}_{len(subjects) + 1:03d}"
                )
                db.add(subject)
                subjects.append(subject)
            else:
                subjects.append(existing)
        
        await db.flush()
        print(f"   ✓ Created {len([s for s in subjects if s.id is None or s.id > 0])} subjects")
        
        # 3. Create Classes for first school
        print("🎓 Creating classes...")
        school = schools[0]
        classes = []
        
        for grade in [9, 10, 11]:
            for section in ['A', 'B']:
                result = await db.execute(
                    select(Class).where(
                        Class.name == f"{grade}-{section}",
                        Class.school_id == school.id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    cls = Class(
                        name=f"{grade}-{section}",
                        grade=grade,
                        school_id=school.id,
                        academic_year="2024-2025"
                    )
                    db.add(cls)
                    classes.append(cls)
                else:
                    classes.append(existing)
        
        await db.flush()
        print(f"   ✓ Created {len(classes)} classes")
        
        # 4. Create Teachers
        print("👨‍🏫 Creating teachers...")
        teachers = []
        teacher_names = [
            ("Maria", "Karimova", "Mathematics"),
            ("John", "Smith", "Physics"),
            ("Sara", "Azimova", "Chemistry"),
            ("David", "Johnson", "English"),
            ("Nigora", "Rahimova", "Uzbek Language"),
        ]
        
        for first, last, subject_name in teacher_names:
            email = f"{first.lower()}.{last.lower()}@ydtt.uz"
            result = await db.execute(select(User).where(User.email == email))
            existing = result.scalar_one_or_none()
            
            if not existing:
                teacher = User(
                    email=email,
                    hashed_password=get_password_hash("teacher123"),
                    first_name=first,
                    last_name=last,
                    role=UserRole.TEACHER,
                    school_id=school.id,
                    phone=f"+99890{len(teachers) + 1:07d}"
                )
                db.add(teacher)
                teachers.append(teacher)
            else:
                teachers.append(existing)
        
        await db.flush()
        print(f"   ✓ Created {len(teachers)} teachers")
        
        # 5. Create Students
        print("👨‍🎓 Creating students...")
        students = []
        first_names = ["Ali", "Jasur", "Malika", "Dilnoza", "Bobur", "Zilola", "Akmal", "Sevara"]
        last_names = ["Rahimov", "Karimov", "Azimov", "Usmanov", "Sharipov", "Nazarov"]
        
        student_counter = 0  # Global counter to ensure unique emails
        for cls in classes[:2]:  # Only first 2 classes
            for i in range(10):  # 10 students per class
                first = first_names[i % len(first_names)]
                last = last_names[i % len(last_names)]
                email = f"{first.lower()}.{last.lower()}.{student_counter}@student.ydtt.uz"
                
                result = await db.execute(select(User).where(User.email == email))
                existing = result.scalar_one_or_none()
                
                if not existing:
                    student = User(
                        email=email,
                        hashed_password=get_password_hash("student123"),
                        first_name=first,
                        last_name=last,
                        role=UserRole.STUDENT,
                        school_id=school.id,
                        class_id=cls.id,
                        phone=f"+99891{student_counter:07d}"
                    )
                    db.add(student)
                    students.append(student)
                else:
                    students.append(existing)
                
                student_counter += 1  # Increment for each student
        
        await db.flush()
        print(f"   ✓ Created {len(students)} students")
        
        # 6. Create Time Slots
        print("⏰ Creating time slots...")
        time_slots_data = [
            (1, time(8, 30), time(9, 15)),
            (2, time(9, 25), time(10, 10)),
            (3, time(10, 20), time(11, 5)),
            (4, time(11, 25), time(12, 10)),
            (5, time(12, 20), time(13, 5)),
            (6, time(13, 45), time(14, 30)),
        ]
        
        time_slots = []
        for order, start, end in time_slots_data:
            result = await db.execute(
                select(TimeSlot).where(
                    TimeSlot.school_id == school.id,
                    TimeSlot.order == order
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                slot = TimeSlot(
                    school_id=school.id,
                    order=order,
                    start_time=start,
                    end_time=end
                )
                db.add(slot)
                time_slots.append(slot)
            else:
                time_slots.append(existing)
        
        await db.flush()
        print(f"   ✓ Created {len(time_slots)} time slots")
        
        # 7. Create Schedule for first class
        print("📅 Creating timetable...")
        cls = classes[0]
        days = [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, DayOfWeek.THURSDAY, DayOfWeek.FRIDAY]
        
        schedules = []
        for day_idx, day in enumerate(days):
            for slot_idx in range(min(4, len(time_slots))):  # 4 lessons per day
                subject = subjects[slot_idx % len(subjects)]
                teacher = teachers[slot_idx % len(teachers)]
                slot = time_slots[slot_idx]
                
                result = await db.execute(
                    select(Schedule).where(
                        Schedule.class_id == cls.id,
                        Schedule.day_of_week == day,
                        Schedule.time_slot_id == slot.id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    schedule = Schedule(
                        school_id=school.id,
                        class_id=cls.id,
                        subject_id=subject.id,
                        teacher_id=teacher.id,
                        time_slot_id=slot.id,
                        day_of_week=day,
                        room_number=f"Cabinet {201 + slot_idx}"
                    )
                    db.add(schedule)
                    schedules.append(schedule)
        
        await db.flush()
        print(f"   ✓ Created {len(schedules)} schedule entries")
        
        # 8. Create Lessons
        print("📝 Creating lessons...")
        lessons = []
        for subject in subjects[:3]:  # First 3 subjects
            for i in range(5):  # 5 lessons each
                result = await db.execute(
                    select(Lesson).where(
                        Lesson.subject_id == subject.id,
                        Lesson.order == i + 1
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    lesson = Lesson(
                        title=f"{subject.name} - Lesson {i + 1}",
                        subject_id=subject.id,
                        grade=9,
                        content=f"This is lesson {i + 1} content for {subject.name}",
                        order=i + 1
                    )
                    db.add(lesson)
                    lessons.append(lesson)
        
        await db.flush()
        print(f"   ✓ Created {len(lessons)} lessons")
        
        # 9. Create Library Books
        print("📚 Creating library books...")
        books = []
        for subject in subjects[:4]:
            for grade in [9, 10, 11]:
                result = await db.execute(
                    select(LibraryBook).where(
                        LibraryBook.subject_id == subject.id,
                        LibraryBook.grade == grade
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    book = LibraryBook(
                        title=f"{subject.name} Textbook - Grade {grade}",
                        subject_id=subject.id,
                        grade=grade,
                        file_url=f"https://s3.ydtt.uz/books/{subject.name.lower()}_grade{grade}.pdf",
                        cover_image_url=f"https://s3.ydtt.uz/covers/{subject.name.lower()}_grade{grade}.jpg"
                    )
                    db.add(book)
                    books.append(book)
        
        await db.flush()
        print(f"   ✓ Created {len(books)} library books")
        
        # 10. Create Sample Attendance
        print("✅ Creating attendance records...")
        today = date.today()
        for student in students[:10]:  # Last 5 days for first 10 students
            for day_offset in range(5):
                check_date = today - timedelta(days=day_offset)
                
                result = await db.execute(
                    select(Attendance).where(
                        Attendance.student_id == student.id,
                        Attendance.date == check_date
                    )
                )
                if not result.scalar_one_or_none():
                    attendance = Attendance(
                        date=check_date,
                        student_id=student.id,
                        class_id=student.class_id,
                        marker_id=teachers[0].id,
                        status=AttendanceStatus.PRESENT if day_offset < 4 else AttendanceStatus.ABSENT
                    )
                    db.add(attendance)
        
        await db.flush()
        print(f"   ✓ Created attendance records")
        
        # 11. Create Sample Grades
        print("📊 Creating grades...")
        for student in students[:10]:
            for subject in subjects[:3]:
                for i in range(3):
                    check_date = today - timedelta(days=i * 3)
                    result = await db.execute(
                        select(Grade).where(
                            Grade.student_id == student.id,
                            Grade.subject_id == subject.id,
                            Grade.date == check_date
                        )
                    )
                    if not result.scalar_one_or_none():
                        grade = Grade(
                            date=check_date,
                            student_id=student.id,
                            subject_id=subject.id,
                            teacher_id=teachers[0].id,
                            grade_type=GradeType.CLASSWORK,
                            score=4 + (i % 2),
                            max_score=5
                        )
                        db.add(grade)
        
        await db.flush()
        print(f"   ✓ Created grade records")
        
        # 12. Create Sample Assignments
        print("📋 Creating assignments...")
        assignments_count = 0
        for subject in subjects[:2]:
            result = await db.execute(
                select(Assignment).where(
                    Assignment.subject_id == subject.id,
                    Assignment.class_id == classes[0].id
                )
            )
            if not result.scalar_one_or_none():
                assignment = Assignment(
                    class_id=classes[0].id,
                    subject_id=subject.id,
                    teacher_id=teachers[0].id,
                    title=f"{subject.name} Homework #1",
                    description=f"Complete exercises from chapter 1",
                    assignment_type=AssignmentType.HOMEWORK,
                    due_date=datetime.now() + timedelta(days=7)
                )
                db.add(assignment)
                assignments_count += 1
        
        await db.flush()
        print(f"   ✓ Created {assignments_count} assignments")
        
        # 13. Create Sample Exam
        print("🎓 Creating sample exam...")
        math_subject = subjects[0]
        result = await db.execute(
            select(Exam).where(
                Exam.subject_id == math_subject.id,
                Exam.title.like("%Sample%")
            )
        )
        if not result.scalar_one_or_none():
            exam = Exam(
                title="Sample Math Exam",
                subject_id=math_subject.id,
                grade=9,
                duration_minutes=45,
                passing_score=60
            )
            db.add(exam)
            await db.flush()
            
            # Add questions
            questions_data = [
                ("What is 2 + 2?", [("3", False), ("4", True), ("5", False)]),
                ("What is 5 * 6?", [("25", False), ("30", True), ("35", False)]),
                ("What is 10 / 2?", [("5", True), ("2", False), ("10", False)]),
            ]
            
            for q_text, options in questions_data:
                question = Question(
                    exam_id=exam.id,
                    text=q_text,
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    points=10
                )
                db.add(question)
                await db.flush()
                
                # Add options
                for opt_text, is_correct in options:
                    from app.models.exam import QuestionOption
                    option = QuestionOption(
                        question_id=question.id,
                        text=opt_text,
                        is_correct=is_correct
                    )
                    db.add(option)
            
            print(f"   ✓ Created sample exam with questions")
        
        # Commit all changes
        await db.commit()
        
        print("\n✅ Database seeding completed!")
        print("\n📝 Test Credentials:")
        print("=" * 50)
        print("Teacher Login:")
        print(f"  Email: maria.karimova@ydtt.uz")
        print(f"  Password: teacher123")
        print()
        print("Student Login:")
        print(f"  Email: ali.rahimov.0@student.ydtt.uz")
        print(f"  Password: student123")
        print()
        print("Admin Login:")
        print(f"  Email: admin@ydtt.uz")
        print(f"  Password: admin123")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed_database())
