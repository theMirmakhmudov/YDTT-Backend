"""
Pydantic schemas for exams, questions, attempts, and results.
"""
from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field

from app.models.exam import ExamType, QuestionType, AttemptStatus


# Question schemas
class QuestionOption(BaseModel):
    """Option for multiple/single choice questions."""
    id: int
    text: str


class QuestionBase(BaseModel):
    """Base question schema."""
    question_type: QuestionType
    text: str
    explanation: Optional[str] = None
    options: Optional[List[QuestionOption]] = None
    correct_answer: str
    numeric_tolerance: Optional[float] = None
    points: float = Field(default=1.0, ge=0)
    partial_credit: bool = False
    order: int = Field(default=0, ge=0)
    image_url: Optional[str] = None


class QuestionCreate(QuestionBase):
    """Schema for creating a question."""
    pass


class QuestionUpdate(BaseModel):
    """Schema for updating a question."""
    text: Optional[str] = None
    explanation: Optional[str] = None
    options: Optional[List[QuestionOption]] = None
    correct_answer: Optional[str] = None
    numeric_tolerance: Optional[float] = None
    points: Optional[float] = Field(None, ge=0)
    partial_credit: Optional[bool] = None
    order: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class QuestionResponse(BaseModel):
    """Response schema for question (without correct answer for students)."""
    id: int
    question_type: QuestionType
    text: str
    options: Optional[List[QuestionOption]] = None
    points: float
    order: int
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class QuestionWithAnswerResponse(QuestionResponse):
    """Response schema for question with correct answer (for teachers/review)."""
    correct_answer: str
    explanation: Optional[str] = None
    numeric_tolerance: Optional[float] = None
    partial_credit: bool


# Exam schemas
class ExamBase(BaseModel):
    """Base exam schema."""
    title: str = Field(max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    exam_type: ExamType = ExamType.TEST
    duration_minutes: int = Field(ge=1)
    passing_score: float = Field(default=60.0, ge=0, le=100)
    max_attempts: int = Field(default=1, ge=1)
    shuffle_questions: bool = True
    shuffle_answers: bool = True
    show_correct_answers: bool = False
    subject_id: int
    lesson_id: Optional[int] = None
    class_id: Optional[int] = None
    available_from: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    is_published: bool = False


class ExamCreate(ExamBase):
    """Schema for creating an exam."""
    pass


class ExamUpdate(BaseModel):
    """Schema for updating an exam."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1)
    passing_score: Optional[float] = Field(None, ge=0, le=100)
    max_attempts: Optional[int] = Field(None, ge=1)
    shuffle_questions: Optional[bool] = None
    shuffle_answers: Optional[bool] = None
    show_correct_answers: Optional[bool] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


class ExamResponse(BaseModel):
    """Response schema for exam."""
    id: int
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    exam_type: ExamType
    duration_minutes: int
    passing_score: float
    max_attempts: int
    shuffle_questions: bool
    subject_id: int
    lesson_id: Optional[int] = None
    class_id: Optional[int] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    is_published: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    question_count: int = 0
    
    class Config:
        from_attributes = True


class ExamListResponse(BaseModel):
    """Response schema for paginated exam list."""
    items: List[ExamResponse]
    total: int
    page: int
    page_size: int
    pages: int


# Exam attempt schemas
class ExamStartResponse(BaseModel):
    """Response when starting an exam attempt."""
    attempt_id: int
    questions: List[QuestionResponse]
    expires_at: datetime
    started_at: datetime


class AnswerSubmission(BaseModel):
    """Schema for submitting an answer."""
    question_id: int
    answer_value: str
    time_spent_seconds: Optional[int] = None
    offline_id: Optional[str] = None


class ExamSubmitRequest(BaseModel):
    """Request for submitting exam answers."""
    answers: List[AnswerSubmission]
    device_id: Optional[str] = None


class AttemptResponse(BaseModel):
    """Response schema for exam attempt."""
    id: int
    exam_id: int
    student_id: int
    status: AttemptStatus
    attempt_number: int
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Result schemas
class AnswerResult(BaseModel):
    """Result for a single answer."""
    question_id: int
    is_correct: Optional[bool] = None
    points_earned: Optional[float] = None
    correct_answer: Optional[str] = None  # Only shown if exam allows


class ResultResponse(BaseModel):
    """Response schema for exam result."""
    id: int
    attempt_id: int
    total_points: float
    earned_points: float
    percentage: float
    is_passed: bool
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    evaluated_at: datetime
    breakdown: Optional[List[AnswerResult]] = None
    
    class Config:
        from_attributes = True


class EvaluateRequest(BaseModel):
    """Request to trigger exam evaluation."""
    attempt_id: int
