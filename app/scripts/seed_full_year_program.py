"""
Massive World Builder: YDTT Full Year Academic Program (2025-2026).
Generates a complete school ecosystem for Grades 1-11.

Scope:
- 11 Students (One per Grade: 1-A to 11-A)
- 3 Master Teachers (Math, English, SE)
- Full Calendar: Sep 2, 2025 -> May 25, 2026.
- Schedule: Mon-Sat (6 days).
- Holidays: Uzbek National Holidays + Breaks.
- AI Content: Procedurally generated topics based on grade level.
"""
import asyncio
import random
from datetime import datetime, timedelta, date, time
from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import engine
from app.core.security import get_password_hash
from app.models import (
    User, UserRole, School, Class, Subject,
    Lesson, Material, MaterialType,
    Assignment, AssignmentType, Submission,
    TimeSlot, Schedule, DayOfWeek,
    Attendance, AttendanceStatus, Grade, GradeType
)

# --- CONFIGURATION ---
SCHOOL_YEAR_START = date(2025, 9, 2)
SCHOOL_YEAR_END = date(2026, 5, 25)

# Holidays (YYYY-MM-DD)
HOLIDAYS = {
    date(2025, 10, 1),   # Teacher's Day
    date(2025, 12, 8),   # Constitution Day
    date(2026, 3, 8),    # Women's Day
    date(2026, 3, 21),   # Navruz
    date(2026, 5, 9),    # Memory Day
}
# Breaks (Inclusive)
WINTER_BREAK = (date(2025, 12, 30), date(2026, 1, 10))
SPRING_BREAK = (date(2026, 3, 20), date(2026, 3, 27))

SUBJECTS_CONFIG = {
    "math": {
        "name": "Matematika",
        "code": "MATH",
        "skills": [
            "Counting", "Addition", "Subtraction", "Multiplication", "Division", # G1-4
            "Fractions", "Decimals", "Percentages", "Ratios", "Geometry Basics", # G5-7
            "Algebra", "Linear Equations", "Trigonometry", "Logarithms",         # G8-9
            "Calculus", "Derivatives", "Integrals", "Probability Theory"         # G10-11
        ]
    },
    "english": {
        "name": "Ingliz tili",
        "code": "ENG",
        "skills": [
            "Alphabet", "Colors", "Numbers", "Family Words", "Animals",          # G1-4
            "Present Simple", "Past Simple", "Adjectives", "Daily Routine",      # G5-7
            "Future Tense", "Conditionals", "Essay Writing", "Public Speaking",  # G8-9
            "Advanced Grammar", "IELTS Prep", "Literature Analysis", "Debate"    # G10-11
        ]
    },
    "softeng": {
        "name": "Dasturlash (IT)",
        "code": "SE",
        "skills": [
            "Computer Parts", "Mouse Skills", "Typing", "Paint", "Logic Puzzles", # G1-4
            "Scratch", "Block Coding", "Internet Safety", "HTML Basics",          # G5-7
            "Python Basics", "Loops", "Functions", "CSS Designing",              # G8-9
            "Algorithms", "Data Structures", "OOP", "Full Stack Project"         # G10-11
        ]
    }
}

async def seed_full_year():
    print("🌍 STARTING WORLD BUILDER: PROJECT 1-YEAR...")
    
    async with AsyncSession(engine) as session:
        # 1. School
        school = School(
            name="YDTT Academy of Excellence",
            code="YDTT-HQ",
            region="Toshkent",
            district="Mirobod",
            director_name="AI Superadmin",
            capacity=2000,
            address="Future Street, 1"
        )
        session.add(school)
        await session.flush()
        
        # 2. Teachers
        teachers = {}
        print("👨‍🏫 Recruiting Master Teachers...")
        for key, conf in SUBJECTS_CONFIG.items():
            subj = Subject(
                name=conf["name"], 
                code=conf["code"], 
                description=f"Full K-11 Curriculum for {conf['name']}"
            )
            session.add(subj)
            await session.flush()
            
            t_user = User(
                email=f"teacher.{key}@ydtt.uz",
                first_name=f"Master",
                last_name=conf["code"],
                hashed_password=get_password_hash("teacher123"),
                role=UserRole.TEACHER,
                school_id=school.id,
                bio=f"Expert in {conf['name']}"
            )
            session.add(t_user)
            await session.flush()
            teachers[key] = {"user": t_user, "subject": subj}

        # 3. Grades & Students
        print("🎓 Enrolling Students (Grades 1-11)...")
        classes = []
        students = []
        for grade in range(1, 12):
            # Create Class
            cls = Class(
                name=f"{grade}-A",
                grade=grade,
                school_id=school.id,
                academic_year="2025-2026"
            )
            session.add(cls)
            await session.flush()
            classes.append(cls)
            
            # Create Student
            stu = User(
                email=f"student.g{grade}@ydtt.uz",
                first_name=f"Student",
                last_name=f"Grade{grade}",
                hashed_password=get_password_hash("student123"),
                role=UserRole.STUDENT,
                school_id=school.id,
                class_id=cls.id,
                bio=f"Grade {grade} Scholar"
            )
            session.add(stu)
            students.append(stu)
            
        await session.flush()
        
        # 4. TimeSlots (Mon-Sat, 6 periods)
        print("⏰ Configuring Time Machine...")
        slots = []
        for i in range(1, 7): # 6 periods
            ts = TimeSlot(
                school_id=school.id,
                order=i,
                start_time=time(8 + i, 0), # 9:00, 10:00...
                end_time=time(9 + i, 0)
            )
            session.add(ts)
            slots.append(ts)
        await session.flush()

        # 5. Weekly Schedule Generation (Persistent Structure)
        print("📅 Establishing Weekly Class Schedules...")
        
        # Map: class_id -> { day_enum: [ (subject_id, teacher_id), ... ] }
        class_schedules = {} 
        
        days_of_week = [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, 
                       DayOfWeek.THURSDAY, DayOfWeek.FRIDAY, DayOfWeek.SATURDAY]
        
        for cls in classes:
            class_schedules[cls.id] = {}
            for day in days_of_week:
                # Daily plan: Randomize subjects for the day, but keep it fixed for the year
                daily_teachers = list(teachers.values())
                random.shuffle(daily_teachers) # Shuffle once per day-of-week per class
                
                day_slots = []
                for i, t_data in enumerate(daily_teachers):
                    if i >= len(slots): break
                    slot = slots[i]
                    
                    # Create Persistent Schedule Entry
                    sch = Schedule(
                        school_id=school.id,
                        class_id=cls.id,
                        subject_id=t_data["subject"].id,
                        teacher_id=t_data["user"].id,
                        time_slot_id=slot.id,
                        day_of_week=day,
                        room_number=f"Room {cls.grade}-{i+1}"
                    )
                    session.add(sch)
                    
                    # Store for content generation usage
                    day_slots.append({
                        "subject": t_data["subject"],
                        "teacher": t_data["user"],
                        "slot": slot
                    })
                class_schedules[cls.id][day] = day_slots
        
        await session.flush()
        print("✅ Schedules Fixed for all Grades.")

        # 6. Content Generator (Daily Loop)
        print("📚 Generating Curriculum Content (Lessons & Homework)...")
        
        # Helper: Is Holiday?
        def is_school_day(d: date) -> bool:
            if d.weekday() == 6: return False # Sunday
            if d >= WINTER_BREAK[0] and d <= WINTER_BREAK[1]: return False
            if d >= SPRING_BREAK[0] and d <= SPRING_BREAK[1]: return False
            if d in HOLIDAYS: return False
            return True

        curr_date = SCHOOL_YEAR_START
        total_lessons = 0
        day_count = 0
        
        # We need to fetch students per grade to assign things
        # Map: grade -> student_id
        student_map = {s.class_id: s.id for s in students}

        # Simulation Limit
        SIMULATION_TODAY = date(2025, 11, 15) # Assume we are viewing this in Nov for demo purposes so we have history
        
        while curr_date <= SCHOOL_YEAR_END:
            if is_school_day(curr_date):
                py_weekday = curr_date.weekday()
                if py_weekday < 6:
                    day_enum = days_of_week[py_weekday]
                    day_count += 1
                    
                    for cls in classes:
                        daily_plan = class_schedules[cls.id].get(day_enum, [])
                        student_id = student_map[cls.id]
                        
                        # --- 1. DAILY ATTENDANCE ---
                        # 95% Chance of being present
                        if curr_date < SIMULATION_TODAY:
                            is_present = random.random() > 0.05
                            att = Attendance(
                                date=curr_date,
                                student_id=student_id,
                                class_id=cls.id,
                                marker_id=teachers["math"]["user"].id, # Default marker
                                status=AttendanceStatus.PRESENT if is_present else AttendanceStatus.ABSENT,
                                remarks=None if is_present else "Sick leave"
                            )
                            session.add(att)

                        for slot_data in daily_plan:
                            subj = slot_data["subject"]
                            teacher = slot_data["teacher"]
                            
                            # Topic Gen
                            subj_key = next(k for k, v in teachers.items() if v["user"].id == teacher.id)
                            skills = SUBJECTS_CONFIG[subj_key]["skills"]
                            
                            grade_progress = (cls.grade - 1) / 10.0 
                            year_progress = day_count / 210.0 
                            
                            list_len = len(skills)
                            base_idx = int(grade_progress * (list_len * 0.7)) 
                            current_idx = base_idx + int(year_progress * (list_len * 0.3))
                            current_idx = min(current_idx, list_len - 1)
                            topic = skills[current_idx]
                            
                            # --- 2. RICH CONTENT LESSON ---
                            lesson_html = f"""
                            <h1>{topic}: Introduction</h1>
                            <p>Welcome to today's lesson on <strong>{topic}</strong>.</p>
                            <h3>Key Concepts</h3>
                            <ul>
                                <li>Understanding the core principles of {topic}.</li>
                                <li>Applying {topic} in real-world scenarios.</li>
                            </ul>
                            <div class="video-placeholder">[Video Explanation Here]</div>
                            <p>Please review the attached materials.</p>
                            """
                            
                            lesson = Lesson(
                                title=f"{subj.code}: {topic}",
                                description=f"Comprehensive guide to {topic}",
                                content=lesson_html,
                                subject_id=subj.id,
                                grade=cls.grade,
                                created_by_id=teacher.id,
                                is_published=True,
                                created_at=datetime.combine(curr_date, time(8, 0)),
                                published_at=datetime.combine(curr_date, time(8, 0))
                            )
                            session.add(lesson)
                            await session.flush() # Need ID for Materials
                            total_lessons += 1
                            
                            # --- 3. MATERIALS ---
                            mat = Material(
                                title=f"{topic} - PDF Guide",
                                description=f"Reference sheet for {topic}",
                                file_path=f"materials/{subj.code}/{topic}.pdf",
                                file_name=f"{topic}.pdf",
                                file_size=1024 * random.randint(100, 5000),
                                mime_type="application/pdf",
                                material_type=MaterialType.PDF,
                                checksum="fake-checksum",
                                lesson_id=lesson.id,
                                created_by_id=teacher.id
                            )
                            session.add(mat)
                            
                            # --- 4. ASSIGNMENT & HOMEWORK ---
                            release_time = datetime.combine(curr_date, time(8, 0))
                            hw = Assignment(
                                title=f"HW: {topic} Mastery",
                                description=f"Complete the following exercises for {topic}. \n(System: Released automatically at 08:00)",
                                subject_id=subj.id,
                                class_id=cls.id,
                                teacher_id=teacher.id,
                                assignment_type=AssignmentType.HOMEWORK,
                                created_at=release_time,
                                due_date=datetime.combine(curr_date + timedelta(days=1), time(23, 59))
                            )
                            session.add(hw)
                            await session.flush() # Need ID for Submission

                            # --- 5. HISTORICAL SIMULATION (Grades, Submissions) ---
                            if curr_date < SIMULATION_TODAY:
                                # 90% Chance student did homework
                                if random.random() > 0.1:
                                    sub_time = datetime.combine(curr_date, time(18, 30))
                                    submission = Submission(
                                        assignment_id=hw.id,
                                        student_id=student_id,
                                        content=f"Here is my work for {topic}. I found step 2 tricky.",
                                        submitted_at=sub_time
                                    )
                                    session.add(submission)
                                    await session.flush()
                                    
                                    # Teacher Grades it
                                    score = random.randint(3, 5) # 3, 4, 5 grading scale
                                    grade_entry = Grade(
                                        date=curr_date,
                                        student_id=student_id,
                                        subject_id=subj.id,
                                        teacher_id=teacher.id,
                                        grade_type=GradeType.HOMEWORK,
                                        score=score,
                                        comment="Good effort!" if score > 3 else "Needs review."
                                    )
                                    session.add(grade_entry)
                                    await session.flush()
                                    
                                    # Link them
                                    submission.grade_id = grade_entry.id

            # Flush periodically
            if day_count % 30 == 0:
                print(f"   ...Generated up to {curr_date} ({total_lessons} lessons)")
                await session.flush()
                
            curr_date += timedelta(days=1)
            
        await session.commit()
        print(f"🎉 GENERATION COMPLETE! Created {total_lessons} lessons.")
        print(f"✅ History Link: Simulated active school year up to {SIMULATION_TODAY}.")
        print("Login with: student.g5@ydtt.uz / student123")
        print("Login with: master.math@ydtt.uz / teacher123")

if __name__ == "__main__":
    asyncio.run(seed_full_year())
