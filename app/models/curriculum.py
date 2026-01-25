"""
Curriculum Management System models.
Stores curriculum templates, topics, and auto-generated schedules for full academic year.
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import relationship

from app.models.base import Base


class CurriculumTemplate(Base):
    """
    Master curriculum template for a grade/subject.
    Example: "Grade 5 Mathematics - 2025-2026"
    """
    __tablename__ = "curriculum_templates"

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(Integer, nullable=False, index=True)  # 1-11
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    academic_year = Column(String(20), nullable=False)  # "2025-2026"
    
    # Template info
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Metadata
    total_weeks = Column(Integer)  # Expected duration
    total_hours = Column(Integer)  # Total teaching hours
    hours_per_week = Column(Integer)  # Recommended hours/week
    
    # Status
    is_official = Column(Boolean, default=False)  # Government-approved curriculum
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    subject = relationship("Subject")
    topics = relationship("CurriculumTopic", back_populates="curriculum", cascade="all, delete-orphan")
    schedules = relationship("CurriculumSchedule", back_populates="curriculum")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CurriculumTopic(Base):
    """
    Major topic in curriculum (e.g., "Fractions", "Algebra").
    """
    __tablename__ = "curriculum_topics"

    id = Column(Integer, primary_key=True, index=True)
    curriculum_id = Column(Integer, ForeignKey("curriculum_templates.id"), nullable=False, index=True)
    
    # Topic info
    title = Column(String(255), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False)  # Order in curriculum
    
    # Scheduling
    quarter = Column(Integer)  # 1-4 (or null for flexible)
    estimated_weeks = Column(Integer)
    estimated_hours = Column(Integer)
    
    # Learning
    difficulty_level = Column(String(20))  # "easy", "medium", "hard"
    learning_objectives = Column(JSON)  # ["Objective 1", "Objective 2"]
    
    # Relationships
    curriculum = relationship("CurriculumTemplate", back_populates="topics")
    subtopics = relationship("CurriculumSubtopic", back_populates="topic", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CurriculumSubtopic(Base):
    """
    Specific concept to teach (e.g., "Adding Fractions", "Solving Linear Equations").
    """
    __tablename__ = "curriculum_subtopics"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("curriculum_topics.id"), nullable=False, index=True)
    
    # Subtopic info
    title = Column(String(255), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False)
    
    # Scheduling
    estimated_hours = Column(Float)  # Hours to teach this subtopic
    
    # Learning
    learning_objectives = Column(JSON)  # Specific objectives for this subtopic
    prerequisites = Column(JSON)  # [subtopic_id, subtopic_id] - must learn these first
    
    # Resources
    resources = Column(JSON)  # {"textbook": "page 42-45", "videos": ["url1"], "worksheets": ["url2"]}
    
    # Relationships
    topic = relationship("CurriculumTopic", back_populates="subtopics")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class AcademicYear(Base):
    """
    School's academic year configuration.
    """
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    
    # Year info
    year_name = Column(String(20), nullable=False)  # "2025-2026"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Quarters/Semesters (JSON)
    quarters = Column(JSON)  # [{"name": "Q1", "start": "2025-09-01", "end": "2025-11-15"}]
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    school = relationship("School")
    holidays = relationship("Holiday", back_populates="academic_year", cascade="all, delete-orphan")
    events = relationship("SchoolEvent", back_populates="academic_year", cascade="all, delete-orphan")
    schedules = relationship("CurriculumSchedule", back_populates="academic_year")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Holiday(Base):
    """
    Holidays and breaks (no school days).
    """
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)
    
    # Holiday info
    name = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Type
    holiday_type = Column(String(50))  # "national", "school", "exam_period", "break"
    
    # Applicability
    applies_to_grades = Column(JSON)  # [1,2,3] or "all"
    
    # Relationships
    academic_year = relationship("AcademicYear", back_populates="holidays")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class SchoolEvent(Base):
    """
    Important school events (parent meetings, sports day, etc.).
    """
    __tablename__ = "school_events"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)
    
    # Event info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    event_date = Column(Date, nullable=False)
    event_type = Column(String(50))  # "exam", "meeting", "sports", "cultural"
    
    # Applicability
    applies_to_grades = Column(JSON)  # [1,2,3] or "all"
    
    # Relationships
    school = relationship("School")
    academic_year = relationship("AcademicYear", back_populates="events")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CurriculumSchedule(Base):
    """
    Generated teaching schedule for a class based on curriculum template.
    """
    __tablename__ = "curriculum_schedules"

    id = Column(Integer, primary_key=True, index=True)
    curriculum_id = Column(Integer, ForeignKey("curriculum_templates.id"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Schedule metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    curriculum = relationship("CurriculumTemplate", back_populates="schedules")
    academic_year = relationship("AcademicYear", back_populates="schedules")
    class_ = relationship("Class")
    teacher = relationship("User")
    scheduled_topics = relationship("ScheduledTopic", back_populates="schedule", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledTopic(Base):
    """
    When a specific topic will be taught.
    """
    __tablename__ = "scheduled_topics"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("curriculum_schedules.id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("curriculum_topics.id"), nullable=False, index=True)
    
    # Timing
    start_week = Column(Integer)  # Week number in academic year
    end_week = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    
    # Status
    status = Column(String(20), default="upcoming")  # "upcoming", "in_progress", "completed", "skipped"
    
    # Relationships
    schedule = relationship("CurriculumSchedule", back_populates="scheduled_topics")
    topic = relationship("CurriculumTopic")
    scheduled_lessons = relationship("ScheduledLesson", back_populates="scheduled_topic", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledLesson(Base):
    """
    Daily lesson plan (auto-generated from curriculum).
    """
    __tablename__ = "scheduled_lessons"

    id = Column(Integer, primary_key=True, index=True)
    scheduled_topic_id = Column(Integer, ForeignKey("scheduled_topics.id"), nullable=False, index=True)
    subtopic_id = Column(Integer, ForeignKey("curriculum_subtopics.id"), nullable=True, index=True)
    
    # Timing
    lesson_date = Column(Date, nullable=False, index=True)
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"), nullable=True)
    
    # Lesson content (AI-generated)
    lesson_plan = Column(JSON)  # {"objectives": [], "activities": [], "materials": []}
    materials = Column(JSON)  # Links to resources
    
    # Linked content
    homework_assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True)
    
    # Status
    status = Column(String(20), default="scheduled")  # "scheduled", "completed", "cancelled", "rescheduled"
    
    # Relationships
    scheduled_topic = relationship("ScheduledTopic", back_populates="scheduled_lessons")
    subtopic = relationship("CurriculumSubtopic")
    time_slot = relationship("TimeSlot")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
