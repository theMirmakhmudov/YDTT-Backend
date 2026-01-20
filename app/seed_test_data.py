"""
Comprehensive test data seeder for YDTT Backend.
Creates 100+ records for each entity to fully test the session-based API.

Run with: python -m app.seed_test_data
"""
import asyncio
import logging
import random
from datetime import datetime, time, timedelta
from typing import List

from sqlalchemy import select

from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.school import School, Class, Subject
from app.models.timetable import TimeSlot, Schedule, DayOfWeek
from app.models.lesson import Lesson, Material, MaterialType
from app.models.lesson_session import LessonSession, LessonSessionStatus, StudentNote
from app.models.session_attendance import SessionAttendance
from app.models.whiteboard import WhiteboardEvent, WhiteboardEventType
from app.models.session_material import SessionMaterial, MaterialAccess
from app.models.journal import Attendance, AttendanceStatus, Grade, GradeType
from app.models.assignment import Assignment, Submission, AssignmentType
from app.models.exam import (
    Exam, ExamType, Question, QuestionType, ExamAttempt, AttemptStatus, 
    Answer, Result
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Uzbek names for realistic data
UZBEK_FIRST_NAMES_MALE = [
    "Aziz", "Bobur", "Davron", "Eldor", "Farrux", "Gulom", "Hamid", "Ilhom", "Jamshid", "Kamol",
    "Laziz", "Mansur", "Nodir", "Otabek", "Pulat", "Rustam", "Sanjar", "Timur", "Ulugbek", "Vali",
    "Yusuf", "Zafar", "Akmal", "Bekzod", "Dilshod", "Erkin", "Farhod", "Gafur", "Husan", "Ismoil"
]

UZBEK_FIRST_NAMES_FEMALE = [
    "Aziza", "Barno", "Dilnoza", "Ezoza", "Feruza", "Gulnora", "Hilola", "Iroda", "Jamila", "Kamola",
    "Laylo", "Malika", "Nodira", "Oysha", "Parvina", "Rano", "Sevara", "Tursunoy", "Umida", "Vasila",
    "Yulduz", "Zarina", "Azima", "Bibigul", "Dilfuza", "Elnora", "Farida", "Gulshan", "Hurshida", "Intizor"
]

UZBEK_LAST_NAMES = [
    "Aliyev", "Karimov", "Rahimov", "Tursunov", "Yusupov", "Mahmudov", "Sharipov", "Nazarov", "Ismoilov", "Abdullayev",
    "Saidov", "Hasanov", "Rustamov", "Umarov", "Azimov", "Ergashev", "Mirzayev", "Qodirov", "Salimov", "Valijonov",
    "Zakirov", "Ahmadov", "Boboyev", "Davlatov", "Fayzullayev", "Gafurov", "Hamidov", "Ibragimov", "Jalolov", "Kamilov"
]

SUBJECTS = [
    "Matematika", "Fizika", "Kimyo", "Biologiya", "Tarix", "Geografiya", 
    "Ingliz tili", "Rus tili", "O'zbek tili", "Adabiyot",
    "Informatika", "Jismoniy tarbiya", "Musiqa", "Tasviriy san'at", "Texnologiya"
]

TOPICS = {
    "Matematika": ["Kasrlar", "O'nli kasrlar", "Foizlar", "Tenglamalar", "Geometriya asoslari"],
    "Fizika": ["Mexanika", "Issiqlik", "Elektr", "Optika", "Atom fizikasi"],
    "Kimyo": ["Atomlar va molekulalar", "Kimyoviy reaksiyalar", "Kislotalar va asoslar", "Organik kimyo"],
    "Biologiya": ["Hujayra", "O'simliklar", "Hayvonlar", "Inson anatomiyasi", "Ekologiya"],
    "Tarix": ["Qadimgi dunyo", "O'rta asrlar", "Yangi davr", "Zamonaviy tarix", "O'zbekiston tarixi"],
}


async def create_schools(session, count: int = 10) -> List[School]:
    """Create test schools."""
    logger.info(f"Creating {count} schools...")
    schools = []
    
    regions = ["Toshkent", "Samarqand", "Buxoro", "Xorazm", "Farg'ona", "Andijon", "Namangan", "Qashqadaryo", "Surxondaryo", "Jizzax"]
    
    for i in range(count):
        school = School(
            name=f"{regions[i % len(regions)]} {i+1}-maktab",
            region=regions[i % len(regions)],
            district=f"{i+1}-tuman",
            code=f"SCH-{i+1:03d}",
            address=f"{regions[i % len(regions)]} ko'chasi, {i+1}-uy",
            director_name=f"{random.choice(UZBEK_FIRST_NAMES_MALE)} {random.choice(UZBEK_LAST_NAMES)}",
            phone=f"+998{random.randint(90, 99)}{random.randint(1000000, 9999999)}",
            email=f"school{i+1}@ydtt.uz",
            capacity=random.randint(500, 2000),
            is_active=True
        )
        session.add(school)
        schools.append(school)
    
    await session.commit()
    logger.info(f"✓ Created {count} schools")
    return schools


async def create_subjects(session) -> List[Subject]:
    """Create subjects."""
    logger.info(f"Creating {len(SUBJECTS)} subjects...")
    subjects = []
    
    for subject_name in SUBJECTS:
        subject = Subject(
            name=subject_name,
            code=subject_name[:3].upper(),
            description=f"{subject_name} fanidan darslar",
            is_active=True
        )
        session.add(subject)
        subjects.append(subject)
    
    await session.commit()
    logger.info(f"✓ Created {len(SUBJECTS)} subjects")
    return subjects


async def create_classes(session, schools: List[School], count_per_school: int = 12) -> List[Class]:
    """Create classes for each school."""
    logger.info(f"Creating {len(schools) * count_per_school} classes...")
    classes = []
    
    for school in schools:
        for grade in range(1, 12):  # Grades 1-11
            for section in ['A', 'B']:
                if len(classes) >= len(schools) * count_per_school:
                    break
                    
                class_obj = Class(
                    name=f"{grade}-{section}",
                    grade=grade,
                    school_id=school.id,
                    academic_year="2025-2026",
                    is_active=True
                )
                session.add(class_obj)
                classes.append(class_obj)
    
    await session.commit()
    logger.info(f"✓ Created {len(classes)} classes")
    return classes


async def create_users(session, schools: List[School], classes: List[Class]) -> dict:
    """Create teachers and students."""
    logger.info("Creating users (teachers and students)...")
    
    users = {"teachers": [], "students": []}
    password_hash = get_password_hash("password123")
    
    # Create 100 teachers
    for i in range(100):
        is_male = random.choice([True, False])
        first_name = random.choice(UZBEK_FIRST_NAMES_MALE if is_male else UZBEK_FIRST_NAMES_FEMALE)
        last_name = random.choice(UZBEK_LAST_NAMES)
        
        teacher = User(
            email=f"teacher{i+1}@ydtt.uz",
            hashed_password=password_hash,
            first_name=first_name,
            last_name=last_name,
            middle_name=random.choice(UZBEK_LAST_NAMES) + "ovich" if is_male else "ovna",
            role=UserRole.TEACHER,
            school_id=random.choice(schools).id,
            is_active=True,
            preferred_language="uz"
        )
        session.add(teacher)
        users["teachers"].append(teacher)
    
    # Create 500 students (distributed across classes)
    for i in range(500):
        is_male = random.choice([True, False])
        first_name = random.choice(UZBEK_FIRST_NAMES_MALE if is_male else UZBEK_FIRST_NAMES_FEMALE)
        last_name = random.choice(UZBEK_LAST_NAMES)
        class_obj = random.choice(classes)
        
        student = User(
            email=f"student{i+1}@ydtt.uz",
            hashed_password=password_hash,
            first_name=first_name,
            last_name=last_name,
            middle_name=random.choice(UZBEK_LAST_NAMES) + "ovich" if is_male else "ovna",
            role=UserRole.STUDENT,
            school_id=class_obj.school_id,
            class_id=class_obj.id,
            is_active=True,
            preferred_language="uz"
        )
        session.add(student)
        users["students"].append(student)
    
    await session.commit()
    logger.info(f"✓ Created {len(users['teachers'])} teachers and {len(users['students'])} students")
    return users


async def create_time_slots(session, schools: List[School]) -> List[TimeSlot]:
    """Create time slots for schools."""
    logger.info("Creating time slots...")
    time_slots = []
    
    # Standard school schedule: 8:00 - 14:00, 45-minute lessons
    start_times = [
        time(8, 0), time(8, 50), time(9, 40), time(10, 30),
        time(11, 20), time(12, 10), time(13, 0)
    ]
    
    for school in schools:
        for i, start in enumerate(start_times):
            end = time(start.hour, start.minute + 45) if start.minute < 15 else time(start.hour + 1, start.minute - 15)
            
            slot = TimeSlot(
                school_id=school.id,
                order=i + 1,
                start_time=start,
                end_time=end
            )
            session.add(slot)
            time_slots.append(slot)
    
    await session.commit()
    logger.info(f"✓ Created {len(time_slots)} time slots")
    return time_slots


async def create_schedules(session, classes: List[Class], subjects: List[Subject], 
                          teachers: List[User], time_slots: List[TimeSlot]) -> List[Schedule]:
    """Create weekly schedules."""
    logger.info("Creating schedules...")
    schedules = []
    
    days = list(DayOfWeek)
    
    for class_obj in classes[:50]:  # First 50 classes
        school_slots = [ts for ts in time_slots if ts.school_id == class_obj.school_id]
        school_teachers = [t for t in teachers if t.school_id == class_obj.school_id]
        
        if not school_slots or not school_teachers:
            continue
        
        # Create 5-6 lessons per day
        for day in days[:5]:  # Monday to Friday
            daily_subjects = random.sample(subjects, min(6, len(subjects)))
            
            for i, subject in enumerate(daily_subjects):
                if i >= len(school_slots):
                    break
                
                schedule = Schedule(
                    school_id=class_obj.school_id,
                    class_id=class_obj.id,
                    subject_id=subject.id,
                    teacher_id=random.choice(school_teachers).id,
                    time_slot_id=school_slots[i].id,
                    day_of_week=day,
                    room_number=f"{random.randint(1, 5)}{random.randint(0, 9)}"
                )
                session.add(schedule)
                schedules.append(schedule)
    
    await session.commit()
    logger.info(f"✓ Created {len(schedules)} schedules")
    return schedules


async def create_lessons_and_materials(session, subjects: List[Subject]) -> tuple:
    """Create lessons and materials."""
    logger.info("Creating lessons and materials...")
    lessons = []
    materials = []
    
    for subject in subjects:
        topics = TOPICS.get(subject.name, ["Mavzu 1", "Mavzu 2", "Mavzu 3"])
        
        for i, topic in enumerate(topics):
            lesson = Lesson(
                title=topic,
                description=f"{topic} bo'yicha dars",
                content=f"# {topic}\n\nBu darsda biz {topic} mavzusini o'rganamiz.",
                subject_id=subject.id,
                grade=random.randint(5, 11),
                order=i + 1,
                version=1,
                is_published=True,
                is_active=True
            )
            session.add(lesson)
            await session.flush()
            lessons.append(lesson)
            
            # Create 2-3 materials per lesson
            for j in range(random.randint(2, 3)):
                material = Material(
                    title=f"{topic} - Material {j+1}",
                    description=f"Qo'shimcha material",
                    file_path=f"/materials/{subject.code}/{topic.replace(' ', '_')}_{j+1}.pdf",
                    file_name=f"{topic}_{j+1}.pdf",
                    file_size=random.randint(100000, 5000000),
                    mime_type="application/pdf",
                    material_type=MaterialType.PDF,
                    checksum="abc123def456",
                    lesson_id=lesson.id,
                    is_active=True
                )
                session.add(material)
                materials.append(material)
    
    await session.commit()
    logger.info(f"✓ Created {len(lessons)} lessons and {len(materials)} materials")
    return lessons, materials


async def create_lesson_sessions(session, schedules: List[Schedule], teachers: List[User]) -> List[LessonSession]:
    """Create lesson sessions (some active, some ended)."""
    logger.info("Creating lesson sessions...")
    sessions_list = []
    
    # Create 150 sessions
    for i in range(150):
        schedule = random.choice(schedules)
        status = random.choices(
            [LessonSessionStatus.ACTIVE, LessonSessionStatus.ENDED, LessonSessionStatus.PENDING],
            weights=[0.2, 0.7, 0.1]
        )[0]
        
        started_at = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        ended_at = started_at + timedelta(minutes=45) if status == LessonSessionStatus.ENDED else None
        
        session_obj = LessonSession(
            schedule_id=schedule.id,
            teacher_id=schedule.teacher_id,
            class_id=schedule.class_id,
            subject_id=schedule.subject_id,
            topic=f"Dars {i+1}",
            status=status,
            started_at=started_at,
            ended_at=ended_at
        )
        session.add(session_obj)
        sessions_list.append(session_obj)
    
    await session.commit()
    logger.info(f"✓ Created {len(sessions_list)} lesson sessions")
    return sessions_list


async def create_session_attendance(session, lesson_sessions: List[LessonSession], students: List[User]):
    """Create session attendance records."""
    logger.info("Creating session attendance records...")
    count = 0
    
    for lesson_session in lesson_sessions:
        # Get students from the same class
        class_students = [s for s in students if s.class_id == lesson_session.class_id]
        
        # 70-90% attendance rate
        attending_students = random.sample(class_students, k=int(len(class_students) * random.uniform(0.7, 0.9)))
        
        for student in attending_students:
            joined_at = lesson_session.started_at + timedelta(minutes=random.randint(0, 10))
            left_at = lesson_session.ended_at if lesson_session.ended_at else None
            
            attendance = SessionAttendance(
                session_id=lesson_session.id,
                student_id=student.id,
                joined_at=joined_at,
                left_at=left_at
            )
            session.add(attendance)
            count += 1
    
    await session.commit()
    logger.info(f"✓ Created {count} attendance records")


async def create_whiteboard_events(session, lesson_sessions: List[LessonSession]):
    """Create whiteboard events for active/ended sessions."""
    logger.info("Creating whiteboard events...")
    count = 0
    
    active_sessions = [s for s in lesson_sessions if s.status in [LessonSessionStatus.ACTIVE, LessonSessionStatus.ENDED]]
    
    for lesson_session in active_sessions[:50]:  # First 50 sessions
        # Create 10-20 whiteboard events per session
        for _ in range(random.randint(10, 20)):
            event_type = random.choice([WhiteboardEventType.DRAW, WhiteboardEventType.ERASE])
            
            if event_type == WhiteboardEventType.DRAW:
                payload = {
                    "x": random.randint(0, 1920),
                    "y": random.randint(0, 1080),
                    "color": random.choice(["#000000", "#FF0000", "#0000FF", "#00FF00"]),
                    "size": random.randint(1, 5)
                }
            else:
                payload = {
                    "x": random.randint(0, 1920),
                    "y": random.randint(0, 1080),
                    "size": random.randint(10, 30)
                }
            
            event = WhiteboardEvent(
                session_id=lesson_session.id,
                created_by_id=lesson_session.teacher_id,
                event_type=event_type,
                payload=payload,
                created_at=lesson_session.started_at + timedelta(minutes=random.randint(0, 40))
            )
            session.add(event)
            count += 1
    
    await session.commit()
    logger.info(f"✓ Created {count} whiteboard events")


async def create_student_notes(session, lesson_sessions: List[LessonSession], students: List[User]):
    """Create student notes."""
    logger.info("Creating student notes...")
    count = 0
    
    for lesson_session in lesson_sessions[:100]:
        class_students = [s for s in students if s.class_id == lesson_session.class_id]
        note_taking_students = random.sample(class_students, k=min(len(class_students) // 2, 15))
        
        for student in note_taking_students:
            note = StudentNote(
                lesson_session_id=lesson_session.id,
                student_id=student.id,
                content=f"# Dars yozuvlari\n\nBugun biz {lesson_session.topic} mavzusini o'rgandik.\n\nMuhim nuqtalar:\n- Birinchi nuqta\n- Ikkinchi nuqta\n- Uchinchi nuqta",
                created_at=lesson_session.started_at + timedelta(minutes=random.randint(5, 40))
            )
            session.add(note)
            count += 1
    
    await session.commit()
    logger.info(f"✓ Created {count} student notes")



async def create_daily_attendance(session, students: List[User], schools: List[School]):
    """Create daily attendance records (School Attendance)."""
    logger.info("Creating daily school attendance...")
    count = 0
    
    # Mark attendance for the last 7 days
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=7)
    
    # Get teachers to mark attendance (one per school)
    teachers_stmt = select(User).where(User.role == UserRole.TEACHER)
    teachers_result = await session.execute(teachers_stmt)
    teachers = teachers_result.scalars().all()
    school_teachers = {t.school_id: t for t in teachers}
    
    for day_offset in range(8): # Includes today
        current_date = start_date + timedelta(days=day_offset)
        # Skip Sunday
        if current_date.weekday() == 6:
            continue
            
        for student in students:
            # 90% chance of being present
            status = random.choices(
                [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.LATE, AttendanceStatus.EXCUSED],
                weights=[0.90, 0.05, 0.03, 0.02]
            )[0]
            
            # Ensure we have a marker
            marker = school_teachers.get(student.school_id)
            if not marker:
                continue
                
            attendance = Attendance(
                date=current_date,
                student_id=student.id,
                class_id=student.class_id,
                marker_id=marker.id,
                status=status,
                remarks="Sababli" if status == AttendanceStatus.EXCUSED else None
            )
            session.add(attendance)
            count += 1
            
    await session.commit()
    logger.info(f"✓ Created {count} daily attendance records")


async def create_assignments_and_submissions(session, classes: List[Class], subjects: List[Subject], students: List[User]):
    """Create assignments and student submissions."""
    logger.info("Creating assignments and submissions...")
    assignments = []
    
    # Get teachers map
    teachers_stmt = select(User).where(User.role == UserRole.TEACHER)
    result = await session.execute(teachers_stmt)
    teachers = result.scalars().all()
    school_teachers = {t.school_id: t for t in teachers}
    
    # Create assignments for some classes
    for class_obj in classes[:30]:
        teacher = school_teachers.get(class_obj.school_id)
        if not teacher:
            continue
            
        class_subjects = random.sample(subjects, 3)
        
        for subject in class_subjects:
            # Create 1-2 assignments per subject
            for i in range(random.randint(1, 2)):
                a_type = random.choice(list(AssignmentType))
                assignment = Assignment(
                    class_id=class_obj.id,
                    subject_id=subject.id,
                    teacher_id=teacher.id,
                    title=f"{subject.name} - {a_type.value} {i+1}",
                    description=f"Please complete this {a_type.value.lower()}.",
                    assignment_type=a_type,
                    due_date=datetime.utcnow() + timedelta(days=random.randint(1, 14)),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 5))
                )
                session.add(assignment)
                await session.flush()
                assignments.append(assignment)
                
                # Create submissions for students in this class
                class_students = [s for s in students if s.class_id == class_obj.id]
                for student in class_students:
                    # 80% submission rate
                    if random.random() > 0.2:
                        submission = Submission(
                            assignment_id=assignment.id,
                            student_id=student.id,
                            content="Here is my work.",
                            submitted_at=datetime.utcnow()
                        )
                        session.add(submission)
                        
    await session.commit()
    logger.info(f"✓ Created {len(assignments)} assignments and submissions")


async def create_exams_and_results(session, classes: List[Class], subjects: List[Subject], students: List[User]):
    """Create exams, questions, attempts, and results."""
    logger.info("Creating exams data...")
    exams = []
    
    teachers_stmt = select(User).where(User.role == UserRole.TEACHER)
    result = await session.execute(teachers_stmt)
    teachers = result.scalars().all()
    school_teachers = {t.school_id: t for t in teachers}
    
    for class_obj in classes[:20]:
        teacher = school_teachers.get(class_obj.school_id)
        if not teacher: continue
        
        # Create 1 exam per class
        subject = random.choice(subjects)
        exam = Exam(
            title=f"{subject.name} - Midterm",
            description="Midterm examination",
            exam_type=ExamType.MIDTERM,
            duration_minutes=60,
            passing_score=60.0,
            subject_id=subject.id,
            class_id=class_obj.id,
            available_from=datetime.utcnow() - timedelta(days=2),
            available_until=datetime.utcnow() + timedelta(days=5),
            is_published=True,
            created_by_id=teacher.id
        )
        session.add(exam)
        await session.flush()
        exams.append(exam)
        
        # Add 5 questions
        for q_idx in range(5):
            question = Question(
                exam_id=exam.id,
                question_type=QuestionType.MULTIPLE_CHOICE,
                text=f"Question {q_idx+1} for {subject.name}?",
                options={"a": "Option A", "b": "Option B", "c": "Option C", "d": "Option D"},
                correct_answer="a",
                points=20.0,
                order=q_idx+1
            )
            session.add(question)
            await session.flush()
            
        # Create attempts for students
        class_students = [s for s in students if s.class_id == class_obj.id]
        for student in class_students:
            # 70% took the exam
            if random.random() > 0.3:
                attempt = ExamAttempt(
                    exam_id=exam.id,
                    student_id=student.id,
                    status=AttemptStatus.EVALUATED if random.random() > 0.1 else AttemptStatus.IN_PROGRESS,
                    attempt_number=1,
                    started_at=datetime.utcnow() - timedelta(hours=2),
                    submitted_at=datetime.utcnow() - timedelta(hours=1)
                )
                session.add(attempt)
                await session.flush()
                
                # If submitted, create result
                if attempt.status == AttemptStatus.EVALUATED or attempt.status == AttemptStatus.SUBMITTED:
                    score = random.randint(40, 100)
                    result = Result(
                        attempt_id=attempt.id,
                        total_points=100.0,
                        earned_points=float(score),
                        percentage=float(score),
                        is_passed=score >= 60,
                        correct_count=int(score/20),
                        incorrect_count=5 - int(score/20),
                        unanswered_count=0
                    )
                    session.add(result)

    await session.commit()
    logger.info(f"✓ Created {len(exams)} exams and attempts")


async def create_grades(session, students: List[User], subjects: List[Subject]):
    """Create journal grades."""
    logger.info("Creating journal grades...")
    count = 0
    
    teachers_stmt = select(User).where(User.role == UserRole.TEACHER)
    res = await session.execute(teachers_stmt)
    teachers = res.scalars().all()
    school_teachers = {t.school_id: t for t in teachers}
    
    for student in students:
        teacher = school_teachers.get(student.school_id)
        if not teacher: continue
        
        # Add a few grades for different subjects
        for _ in range(5):
            grade = Grade(
                date=datetime.utcnow().date() - timedelta(days=random.randint(1, 14)),
                student_id=student.id,
                subject_id=random.choice(subjects).id,
                teacher_id=teacher.id,
                grade_type=random.choice(list(GradeType)),
                score=random.choice([3, 4, 5]),
                max_score=5,
                comment="Good job!" if random.random() > 0.8 else None
            )
            session.add(grade)
            count += 1
            
    await session.commit()
    logger.info(f"✓ Created {count} grades")


async def seed_all_data():
    """Main seeding function."""
    logger.info("=" * 60)
    logger.info("Starting comprehensive data seeding...")
    logger.info("=" * 60)
    
    async with async_session_maker() as session:
        # Check if data already exists
        result = await session.execute(select(School))
        if result.scalar_one_or_none():
            logger.warning("Data already exists. Skipping seeding.")
            logger.info("To re-seed, drop and recreate the database.")
            return
        
        # Create data in order
        schools = await create_schools(session, count=10)
        subjects = await create_subjects(session)
        classes = await create_classes(session, schools, count_per_school=12)
        users = await create_users(session, schools, classes)
        time_slots = await create_time_slots(session, schools)
        schedules = await create_schedules(session, classes, subjects, users["teachers"], time_slots)
        lessons, materials = await create_lessons_and_materials(session, subjects)
        lesson_sessions = await create_lesson_sessions(session, schedules, users["teachers"])
        
        # Create session-based data
        await create_session_attendance(session, lesson_sessions, users["students"])
        await create_whiteboard_events(session, lesson_sessions)
        await create_student_notes(session, lesson_sessions, users["students"])
        
        # Create additional academic data
        await create_daily_attendance(session, users["students"], schools)
        await create_assignments_and_submissions(session, classes, subjects, users["students"])
        await create_exams_and_results(session, classes, subjects, users["students"])
        await create_grades(session, users["students"], subjects)
        
        logger.info("=" * 60)
        logger.info("✓ Data seeding completed successfully!")
        logger.info("=" * 60)
        logger.info("\nTest Accounts:")
        logger.info("  Teacher: teacher1@ydtt.uz / password123")
        logger.info("  Student: student1@ydtt.uz / password123")
        logger.info("\nData Summary:")
        logger.info(f"  Schools: {len(schools)}")
        logger.info(f"  Subjects: {len(subjects)}")
        logger.info(f"  Classes: {len(classes)}")
        logger.info(f"  Teachers: {len(users['teachers'])}")
        logger.info(f"  Students: {len(users['students'])}")
        logger.info(f"  Schedules: {len(schedules)}")
        logger.info(f"  Lessons: {len(lessons)}")
        logger.info(f"  Materials: {len(materials)}")
        logger.info(f"  Lesson Sessions: {len(lesson_sessions)}")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_all_data())
