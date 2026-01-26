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
    Assignment, AssignmentType,
    TimeSlot, Schedule, DayOfWeek
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

        # 5. Schedule & Lessons Generator
        print("📅 Generating 1 Year of Lessons (This might take a moment)...")
        
        # Helper: Is Holiday?
        def is_school_day(d: date) -> bool:
            if d.weekday() == 6: return False # Sunday
            if d >= WINTER_BREAK[0] and d <= WINTER_BREAK[1]: return False
            if d >= SPRING_BREAK[0] and d <= SPRING_BREAK[1]: return False
            if d in HOLIDAYS: return False
            return True

        curr_date = SCHOOL_YEAR_START
        total_lessons = 0
        
        # Determine topic difficulty index based on grade
        # Grade 1 uses index 0-2, Grade 11 uses last indexes
        
        day_count = 0
        while curr_date <= SCHOOL_YEAR_END:
            if is_school_day(curr_date):
                day_enum = list(DayOfWeek)[curr_date.weekday()]
                day_count += 1
                
                for cls in classes:
                    # For each class, schedule 3 core subjects every day
                    # Randomize slot order daily for variety
                    daily_teachers = list(teachers.values())
                    random.shuffle(daily_teachers)
                    
                    for i, t_data in enumerate(daily_teachers):
                        slot = slots[i] # Use first 3 slots
                        
                        # create Schedule (if not exists for this day/slot generic)
                        # *Simplification*: We won't create persistent Schedule objects for every specific date relation 
                        # because Schedule model is generic (weekly).
                        # Instead, we Generate the LESSON directly which is date-specific.
                        
                        # Generate Topic
                        # Logic: Map grade (1-11) to skill list index
                        subj_key = next(k for k, v in teachers.items() if v["user"].id == t_data["user"].id)
                        skills = SUBJECTS_CONFIG[subj_key]["skills"]
                        
                        # Distribute skills across the year. 
                        # Start of year = easier skills for that grade. End = harder.
                        # Grade 1 (0-15% of skill list), Grade 11 (85-100%)
                        grade_progress = (cls.grade - 1) / 10.0 # 0.0 to 1.0
                        year_progress = day_count / 210.0 # Approx school days
                        
                        # Complex math to pick a topic index
                        list_len = len(skills)
                        base_idx = int(grade_progress * (list_len * 0.7)) 
                        current_idx = base_idx + int(year_progress * (list_len * 0.3))
                        current_idx = min(current_idx, list_len - 1)
                        
                        topic = skills[current_idx]
                        
                        # Create Lesson
                        lesson = Lesson(
                            title=f"{t_data['subject'].code}: {topic}",
                            description=f"AI Generated Lesson plan for {topic}. Focus on core concepts.",
                            subject_id=t_data["subject"].id,
                            class_id=cls.id,
                            teacher_id=t_data["user"].id,
                            scheduled_at=datetime.combine(curr_date, slot.start_time),
                            duration_minutes=45,
                            status="scheduled" if curr_date > date.today() else "completed"
                        )
                        session.add(lesson)
                        total_lessons += 1
                        
                        # 100% Chance of Homework (System Auto-Assign)
                        # Rule: Homework appears automatically at 16:00 (After school ends)
                        release_time = datetime.combine(curr_date, time(16, 0))
                        
                        hw = Assignment(
                            title=f"HW: {topic} Practice",
                            description=f"AI Generated exercises for {topic}. \n(System: Released automatically at 16:00)",
                            subject_id=t_data["subject"].id,
                            class_id=cls.id,
                            teacher_id=t_data["user"].id,
                            assignment_type=AssignmentType.HOMEWORK,
                            created_at=release_time, # <--- CONTROLLED RELEASE TIME
                            due_date=datetime.combine(curr_date + timedelta(days=1), time(23, 59)), # Next day midnight
                            max_score=100
                        )
                        session.add(hw)

            # Flush periodically to avoid memory overflow
            if day_count % 30 == 0:
                print(f"   ...Generated up to {curr_date} ({total_lessons} lessons)")
                await session.flush()
                
            curr_date += timedelta(days=1)

        await session.commit()
        print(f"🎉 GENERATION COMPLETE! Created {total_lessons} lessons.")
        print("Login with: student.g5@ydtt.uz / student123")
        print("Login with: master.math@ydtt.uz / teacher123")

if __name__ == "__main__":
    asyncio.run(seed_full_year())
