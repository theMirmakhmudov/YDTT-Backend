"""
Pydantic schemas for AI-powered learning features.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== AI Performance Analysis ====================

class WeakTopic(BaseModel):
    """Individual weak topic identified by AI."""
    topic: str
    confidence: float = Field(ge=0.0, le=1.0, description="AI confidence in this assessment")
    severity: str = Field(description="low, medium, high, critical")
    current_score: Optional[float] = Field(None, description="Current performance score 0-100")
    sample_mistakes: Optional[List[str]] = None


class PerformanceAnalysisResponse(BaseModel):
    """AI analysis of student performance."""
    id: int
    student_id: int
    subject_id: int
    analysis_date: datetime
    
    # Analysis results
    weak_topics: List[WeakTopic]
    strong_topics: Optional[List[Dict[str, Any]]] = None
    overall_performance_score: Optional[float] = None
    performance_trend: Optional[str] = None  # "improving", "declining", "stable"
    at_risk_level: Optional[str] = None  # "low", "medium", "high", "critical"
    
    # Recommendations
    recommended_actions: Optional[List[Dict[str, Any]]] = None
    estimated_improvement_time: Optional[int] = Field(None, description="Days")
    
    class Config:
        from_attributes = True


# ==================== AI Improvement Plan ====================

class ImprovementPlanCreate(BaseModel):
    """Create a new improvement plan."""
    subject_id: int
    weak_topics: List[Dict[str, Any]]
    target_improvement_percentage: Optional[float] = 20.0
    target_days: Optional[int] = 30


class ImprovementPlanResponse(BaseModel):
    """Improvement plan details."""
    id: int
    student_id: int
    subject_id: int
    title: str
    description: Optional[str] = None
    
    weak_topics: List[Dict[str, Any]]
    recommended_resources: Optional[List[Dict[str, Any]]] = None
    practice_exercises: Optional[List[Dict[str, Any]]] = None
    
    target_completion_date: Optional[datetime] = None
    target_improvement_percentage: Optional[float] = None
    
    status: str
    completion_percentage: float
    progress_tracking: Dict[str, Any]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== AI Tutor ====================

class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(description="user or assistant")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AITutorChatRequest(BaseModel):
    """Request to chat with AI tutor."""
    message: str = Field(min_length=1, max_length=2000)
    subject_id: Optional[int] = None
    session_id: Optional[int] = None
    include_context: bool = Field(default=True, description="Include student's weak topics as context")


class AITutorChatResponse(BaseModel):
    """Response from AI tutor."""
    session_id: int
    message: str
    topics_discussed: Optional[List[str]] = None
    suggested_practice: Optional[List[Dict[str, Any]]] = None


class AITutorSessionResponse(BaseModel):
    """AI tutor session details."""
    id: int
    student_id: int
    subject_id: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: List[ChatMessage]
    topics_discussed: Optional[List[str]] = None
    problems_solved: int
    
    class Config:
        from_attributes = True


# ==================== AI Generated Practice ====================

class PracticeRequest(BaseModel):
    """Request AI-generated practice problems."""
    subject_id: int
    topic: str
    difficulty: str = Field(default="medium", description="easy, medium, hard")
    count: int = Field(default=5, ge=1, le=20)


class PracticeProblem(BaseModel):
    """Single practice problem."""
    id: int
    topic: str
    difficulty_level: str
    problem_text: str
    problem_type: str
    options: Optional[List[str]] = None
    hints: Optional[List[str]] = None


class PracticeSubmission(BaseModel):
    """Submit answer to practice problem."""
    problem_id: int
    answer: str
    time_spent_seconds: Optional[int] = None


class PracticeResult(BaseModel):
    """Result of practice problem submission."""
    problem_id: int
    is_correct: str  # "correct", "incorrect", "partial"
    correct_answer: str
    explanation: str
    next_problem: Optional[PracticeProblem] = None


class PracticeProgressResponse(BaseModel):
    """Student's practice progress."""
    total_problems_attempted: int
    total_problems_correct: int
    accuracy_percentage: float
    topics_practiced: List[Dict[str, Any]]
    recent_problems: List[PracticeProblem]
