"""
Exam, Question, Attempt, Answer, and Result models.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Enum, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lesson import Lesson
    from app.models.user import User
    from app.models.anti_cheat import CheatingEvent


class ExamType(str, enum.Enum):
    """Type of exam."""
    QUIZ = "QUIZ"
    TEST = "TEST"
    MIDTERM = "MIDTERM"
    FINAL = "FINAL"
    PRACTICE = "PRACTICE"


class QuestionType(str, enum.Enum):
    """Type of question."""
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    NUMERIC = "NUMERIC"
    SHORT_ANSWER = "SHORT_ANSWER"
    TRUE_FALSE = "TRUE_FALSE"


class AttemptStatus(str, enum.Enum):
    """Status of exam attempt."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EVALUATED = "EVALUATED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class Exam(Base):
    """Exam definition."""
    __tablename__ = "exams"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Type and settings
    exam_type: Mapped[ExamType] = mapped_column(Enum(ExamType), default=ExamType.TEST)
    duration_minutes: Mapped[int] = mapped_column(Integer)  # Time limit
    passing_score: Mapped[float] = mapped_column(Float, default=60.0)  # Minimum passing percentage
    max_attempts: Mapped[int] = mapped_column(Integer, default=1)  # Maximum attempts allowed
    
    # Question settings
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=True)
    shuffle_answers: Mapped[bool] = mapped_column(Boolean, default=True)
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Association
    lesson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lessons.id"), nullable=True, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("classes.id"), nullable=True, index=True)
    
    # Scheduling
    available_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    available_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Status
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Created by
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson", back_populates="exams")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="exam", order_by="Question.order")
    attempts: Mapped[List["ExamAttempt"]] = relationship("ExamAttempt", back_populates="exam")


class Question(Base):
    """Exam question."""
    __tablename__ = "questions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), index=True)
    
    # Question content
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType))
    text: Mapped[str] = mapped_column(Text)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Shown after answer
    
    # Options for choice questions (JSON array)
    options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Correct answer(s)
    correct_answer: Mapped[str] = mapped_column(Text)
    
    # Numeric tolerance (for NUMERIC questions)
    numeric_tolerance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Scoring
    points: Mapped[float] = mapped_column(Float, default=1.0)
    partial_credit: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Order and grouping
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Media
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="questions")
    answers: Mapped[List["Answer"]] = relationship("Answer", back_populates="question")


class ExamAttempt(Base):
    """Student's exam attempt session."""
    __tablename__ = "exam_attempts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Status
    status: Mapped[AttemptStatus] = mapped_column(Enum(AttemptStatus), default=AttemptStatus.NOT_STARTED)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Device info (for anti-cheat)
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Question order (shuffled)
    question_order: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="attempts")
    student: Mapped["User"] = relationship("User", back_populates="exam_attempts")
    answers: Mapped[List["Answer"]] = relationship("Answer", back_populates="attempt")
    result: Mapped[Optional["Result"]] = relationship("Result", back_populates="attempt", uselist=False)
    cheating_events: Mapped[List["CheatingEvent"]] = relationship("CheatingEvent", back_populates="attempt")


class Answer(Base):
    """Student's answer to a question."""
    __tablename__ = "answers"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("exam_attempts.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    
    # Answer content
    answer_value: Mapped[str] = mapped_column(Text)
    
    # Evaluation
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    points_earned: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timing
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Offline sync
    offline_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attempt: Mapped["ExamAttempt"] = relationship("ExamAttempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answers")


class Result(Base):
    """Evaluated exam result."""
    __tablename__ = "results"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("exam_attempts.id"), unique=True, index=True)
    
    # Scores
    total_points: Mapped[float] = mapped_column(Float)
    earned_points: Mapped[float] = mapped_column(Float)
    percentage: Mapped[float] = mapped_column(Float)
    
    # Pass/fail
    is_passed: Mapped[bool] = mapped_column(Boolean)
    
    # Breakdown
    correct_count: Mapped[int] = mapped_column(Integer)
    incorrect_count: Mapped[int] = mapped_column(Integer)
    unanswered_count: Mapped[int] = mapped_column(Integer)
    
    # Per-question breakdown (JSON)
    breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timing
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    attempt: Mapped["ExamAttempt"] = relationship("ExamAttempt", back_populates="result")
