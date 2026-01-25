"""
Curriculum data import script for Uzbekistan education system.
Populates subjects, academic calendar, holidays, and curriculum templates.

Run: python -m app.scripts.import_curriculum_data
"""
import asyncio
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.models import (
    Subject, AcademicYear, Holiday, SchoolEvent,
    CurriculumTemplate, CurriculumTopic, CurriculumSubtopic
)


# Uzbekistan Education System - Subjects by Grade
SUBJECTS_BY_GRADE = {
    # Primary School (Grades 1-4)
    1: [
        "Uzbek Language", "Reading", "Mathematics", "The World Around Us",
        "Technology", "Music", "Art", "Physical Education"
    ],
    2: [
        "Uzbek Language", "Reading", "Mathematics", "The World Around Us",
        "Technology", "Music", "Art", "Physical Education"
    ],
    3: [
        "Uzbek Language", "Literature", "Mathematics", "Natural Science",
        "English", "Technology", "Music", "Art", "Physical Education"
    ],
    4: [
        "Uzbek Language", "Literature", "Mathematics", "Natural Science",
        "English", "Technology", "Music", "Art", "Physical Education"
    ],
    
    # Lower Secondary (Grades 5-9)
    5: [
        "Uzbek Language", "Uzbek Literature", "Mathematics", "English",
        "History", "Geography", "Natural Science", "Informatics",
        "Technology", "Art", "Music", "Physical Education"
    ],
    6: [
        "Uzbek Language", "Literature", "Mathematics", "English",
        "History", "Geography", "Biology", "Informatics",
        "Technology", "Physical Education"
    ],
    7: [
        "Uzbek Language", "Literature", "Mathematics", "English",
        "History of Uzbekistan", "World History", "Geography",
        "Biology", "Physics", "Informatics", "Physical Education"
    ],
    8: [
        "Uzbek Language", "Literature", "Mathematics", "English",
        "History", "Geography", "Biology", "Physics", "Chemistry",
        "Informatics", "Physical Education"
    ],
    9: [
        "Uzbek Language", "Literature", "Mathematics", "English",
        "History of Uzbekistan", "World History", "Geography",
        "Biology", "Physics", "Chemistry", "Informatics", "Physical Education"
    ],
    
    # Upper Secondary (Grades 10-11)
    10: [
        "Uzbek Language & Literature", "Mathematics", "English",
        "History", "Informatics", "Physical Education", "Citizenship",
        # Electives
        "Biology", "Chemistry", "Physics", "Geography", "Economics", "Law"
    ],
    11: [
        "Uzbek Language & Literature", "Mathematics", "English",
        "History", "Informatics", "Physical Education",
        # Electives
        "Biology", "Chemistry", "Physics", "Geography", "Economics", "Law", "IT"
    ]
}

# Hours per week by subject (approximate, can be customized per school)
HOURS_PER_WEEK = {
    # Primary (1-4)
    "Uzbek Language": 5,
    "Reading": 4,
    "Literature": 4,
    "Mathematics": 5,
    "The World Around Us": 2,
    "Natural Science": 2,
    "English": 2,
    "Technology": 1,
    "Music": 1,
    "Art": 1,
    "Physical Education": 2,
    
    # Secondary (5-11)
    "Uzbek Literature": 3,
    "History": 2,
    "History of Uzbekistan": 2,
    "World History": 2,
    "Geography": 2,
    "Biology": 2,
    "Physics": 3,
    "Chemistry": 2,
    "Informatics": 2,
    "Citizenship": 1,
    "Economics": 2,
    "Law": 2,
    "IT": 2,
}

# Academic Year 2025-2026
ACADEMIC_YEAR_2025_2026 = {
    "year_name": "2025-2026",
    "start_date": date(2025, 9, 1),
    "end_date": date(2026, 5, 31),
    "quarters": [
        {"name": "Quarter 1", "start": "2025-09-01", "end": "2025-11-03"},
        {"name": "Quarter 2", "start": "2025-11-10", "end": "2025-12-26"},
        {"name": "Quarter 3", "start": "2026-01-12", "end": "2026-03-20"},
        {"name": "Quarter 4", "start": "2026-03-28", "end": "2026-05-31"},
    ]
}

# Holidays 2025-2026
HOLIDAYS_2025_2026 = [
    {
        "name": "Autumn Holidays",
        "start_date": date(2025, 11, 4),
        "end_date": date(2025, 11, 9),
        "holiday_type": "break",
        "applies_to_grades": "all"
    },
    {
        "name": "Winter Holidays (Grades 1-4)",
        "start_date": date(2025, 12, 27),
        "end_date": date(2026, 1, 11),
        "holiday_type": "break",
        "applies_to_grades": [1, 2, 3, 4]
    },
    {
        "name": "Winter Holidays (Grades 5-11)",
        "start_date": date(2025, 12, 28),
        "end_date": date(2026, 1, 11),
        "holiday_type": "break",
        "applies_to_grades": [5, 6, 7, 8, 9, 10, 11]
    },
    {
        "name": "Spring Holidays",
        "start_date": date(2026, 3, 21),
        "end_date": date(2026, 3, 27),
        "holiday_type": "break",
        "applies_to_grades": "all"
    },
    {
        "name": "Summer Holidays",
        "start_date": date(2026, 6, 1),
        "end_date": date(2026, 8, 31),
        "holiday_type": "break",
        "applies_to_grades": "all"
    },
    # National Holidays
    {
        "name": "Independence Day",
        "start_date": date(2025, 9, 1),
        "end_date": date(2025, 9, 1),
        "holiday_type": "national",
        "applies_to_grades": "all"
    },
    {
        "name": "Navruz",
        "start_date": date(2026, 3, 21),
        "end_date": date(2026, 3, 21),
        "holiday_type": "national",
        "applies_to_grades": "all"
    },
]


async def import_subjects(session: AsyncSession):
    """Import all unique subjects."""
    print("📚 Importing subjects...")
    
    # Get all unique subjects
    all_subjects = set()
    for grade_subjects in SUBJECTS_BY_GRADE.values():
        all_subjects.update(grade_subjects)
    
    subjects_created = 0
    for subject_name in sorted(all_subjects):
        # Check if subject exists
        result = await session.execute(
            f"SELECT id FROM subjects WHERE name = '{subject_name}'"
        )
        if result.first():
            continue
        
        # Create subject
        subject = Subject(
            name=subject_name,
            description=f"{subject_name} curriculum"
        )
        session.add(subject)
        subjects_created += 1
    
    await session.commit()
    print(f"✅ Created {subjects_created} subjects")


async def import_academic_year(session: AsyncSession, school_id: int):
    """Import academic year 2025-2026."""
    print("📅 Importing academic year 2025-2026...")
    
    academic_year = AcademicYear(
        school_id=school_id,
        year_name=ACADEMIC_YEAR_2025_2026["year_name"],
        start_date=ACADEMIC_YEAR_2025_2026["start_date"],
        end_date=ACADEMIC_YEAR_2025_2026["end_date"],
        quarters=ACADEMIC_YEAR_2025_2026["quarters"],
        is_active=True
    )
    session.add(academic_year)
    await session.commit()
    await session.refresh(academic_year)
    
    print(f"✅ Created academic year: {academic_year.year_name}")
    return academic_year.id


async def import_holidays(session: AsyncSession, academic_year_id: int):
    """Import holidays for 2025-2026."""
    print("🎉 Importing holidays...")
    
    for holiday_data in HOLIDAYS_2025_2026:
        holiday = Holiday(
            academic_year_id=academic_year_id,
            name=holiday_data["name"],
            start_date=holiday_data["start_date"],
            end_date=holiday_data["end_date"],
            holiday_type=holiday_data["holiday_type"],
            applies_to_grades=holiday_data["applies_to_grades"]
        )
        session.add(holiday)
    
    await session.commit()
    print(f"✅ Created {len(HOLIDAYS_2025_2026)} holidays")


async def create_sample_curriculum_template(session: AsyncSession, grade: int, subject_name: str):
    """Create a sample curriculum template for a subject."""
    print(f"📖 Creating sample curriculum: Grade {grade} - {subject_name}")
    
    # Get subject ID
    result = await session.execute(
        f"SELECT id FROM subjects WHERE name = '{subject_name}'"
    )
    subject = result.first()
    if not subject:
        print(f"⚠️  Subject '{subject_name}' not found, skipping...")
        return
    
    subject_id = subject[0]
    
    # Create curriculum template
    template = CurriculumTemplate(
        grade=grade,
        subject_id=subject_id,
        academic_year="2025-2026",
        title=f"Grade {grade} {subject_name} Curriculum",
        description=f"Official curriculum for Grade {grade} {subject_name}",
        total_weeks=36,
        total_hours=HOURS_PER_WEEK.get(subject_name, 3) * 36,
        hours_per_week=HOURS_PER_WEEK.get(subject_name, 3),
        is_official=True,
        is_active=True
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    
    # Add sample topics (AI will generate detailed ones later)
    sample_topics = get_sample_topics(subject_name, grade)
    
    for idx, topic_data in enumerate(sample_topics, 1):
        topic = CurriculumTopic(
            curriculum_id=template.id,
            title=topic_data["title"],
            description=topic_data.get("description", ""),
            order_index=idx,
            quarter=topic_data.get("quarter", 1),
            estimated_weeks=topic_data.get("weeks", 4),
            difficulty_level=topic_data.get("difficulty", "medium"),
            learning_objectives=topic_data.get("objectives", [])
        )
        session.add(topic)
    
    await session.commit()
    print(f"✅ Created curriculum template with {len(sample_topics)} topics")


def get_sample_topics(subject_name: str, grade: int):
    """Get sample topics for a subject (placeholder - AI will generate detailed ones)."""
    
    # Sample topics for Mathematics Grade 5
    if subject_name == "Mathematics" and grade == 5:
        return [
            {
                "title": "Numbers and Operations",
                "description": "Place value, rounding, estimation",
                "quarter": 1,
                "weeks": 4,
                "difficulty": "easy",
                "objectives": ["Understand place value", "Round numbers", "Estimate calculations"]
            },
            {
                "title": "Fractions",
                "description": "Understanding and operating with fractions",
                "quarter": 1,
                "weeks": 4,
                "difficulty": "medium",
                "objectives": ["Understand fractions", "Add/subtract fractions", "Multiply fractions"]
            },
            {
                "title": "Decimals",
                "description": "Decimal numbers and operations",
                "quarter": 2,
                "weeks": 3,
                "difficulty": "medium",
                "objectives": ["Understand decimals", "Convert fractions to decimals", "Decimal operations"]
            },
            {
                "title": "Geometry",
                "description": "Shapes, angles, and measurements",
                "quarter": 2,
                "weeks": 5,
                "difficulty": "medium",
                "objectives": ["Identify shapes", "Measure angles", "Calculate area and perimeter"]
            },
        ]
    
    # Generic topics for other subjects
    return [
        {"title": f"{subject_name} - Quarter 1 Topics", "quarter": 1, "weeks": 9},
        {"title": f"{subject_name} - Quarter 2 Topics", "quarter": 2, "weeks": 9},
        {"title": f"{subject_name} - Quarter 3 Topics", "quarter": 3, "weeks": 9},
        {"title": f"{subject_name} - Quarter 4 Topics", "quarter": 4, "weeks": 9},
    ]


async def main():
    """Main import function."""
    print("🚀 Starting curriculum data import...")
    print("=" * 60)
    
    async with AsyncSession(engine) as session:
        # Step 1: Import subjects
        await import_subjects(session)
        
        # Step 2: Import academic year (assuming school_id = 1)
        # TODO: Get actual school_id from database or create school first
        school_id = 1
        academic_year_id = await import_academic_year(session, school_id)
        
        # Step 3: Import holidays
        await import_holidays(session, academic_year_id)
        
        # Step 4: Create sample curriculum templates
        # Start with Grade 5 Mathematics as example
        await create_sample_curriculum_template(session, 5, "Mathematics")
        
        print("=" * 60)
        print("✅ Curriculum data import complete!")
        print("\n📝 Next steps:")
        print("1. Use AI to generate detailed curriculum for all subjects")
        print("2. Create curriculum schedules for classes")
        print("3. Generate lesson plans and assignments")


if __name__ == "__main__":
    asyncio.run(main())
