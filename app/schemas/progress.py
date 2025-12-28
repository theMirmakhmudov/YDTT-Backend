"""
Pydantic schemas for progress tracking and analytics.
"""
from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel


class StudentProgressResponse(BaseModel):
    """Response schema for student progress."""
    student_id: int
    total_exams: int
    completed_exams: int
    passed_exams: int
    failed_exams: int
    average_score: float
    completion_rate: float
    pass_rate: float
    
    # Subject breakdown
    subject_progress: List[Dict]
    
    # Recent activity
    recent_exams: List[Dict]


class ClassProgressResponse(BaseModel):
    """Response schema for class progress."""
    class_id: int
    class_name: str
    total_students: int
    
    # Aggregated stats
    average_score: float
    completion_rate: float
    pass_rate: float
    
    # Subject breakdown
    subject_stats: List[Dict]
    
    # Top/bottom performers
    top_performers: List[Dict]
    struggling_students: List[Dict]


class DashboardAnalytics(BaseModel):
    """Response schema for analytics dashboard."""
    # User metrics
    total_users: int
    active_users_today: int
    active_users_month: int
    dau: int
    mau: int
    
    # Exam metrics
    total_exams: int
    exams_completed_today: int
    exams_completed_month: int
    average_exam_score: float
    exam_completion_rate: float
    
    # Anti-cheating metrics
    cheating_events_today: int
    cheating_detection_ratio: float
    
    # Retention
    retention_rate_7d: float
    retention_rate_30d: float
    
    # Trends (last 7/30 days)
    daily_active_users_trend: List[Dict]
    daily_exams_trend: List[Dict]
    daily_registrations_trend: List[Dict]


class AuditLogResponse(BaseModel):
    """Response schema for audit log entry."""
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    description: Optional[str] = None
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Response schema for paginated audit log list."""
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int
