"""
Pydantic schemas for Digital Assignments.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field

# Re-export Enum
class AssignmentType(str, Enum):
    HOMEWORK = "HOMEWORK"
    CLASSWORK = "CLASSWORK"
    PROJECT = "PROJECT"


# --- Assignment Schemas ---

class AssignmentBase(BaseModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    assignment_type: AssignmentType = AssignmentType.HOMEWORK
    due_date: Optional[datetime] = None
    attachment_url: Optional[str] = None # Link to materials, PDF, etc.

class AssignmentCreate(AssignmentBase):
    class_id: int
    subject_id: int

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    attachment_url: Optional[str] = None
    assignment_type: Optional[AssignmentType] = None

class AssignmentResponse(AssignmentBase):
    id: int
    class_id: int
    subject_id: int
    teacher_id: int
    created_at: datetime
    
    # Author name (optional for list views)
    teacher_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# --- Submission Schemas ---

class SubmissionBase(BaseModel):
    content: Optional[str] = None # Text answer
    attachment_url: Optional[str] = None # File link (PDF, Image)

class SubmissionCreate(SubmissionBase):
    assignment_id: int

class SubmissionUpdate(BaseModel):
    content: Optional[str] = None
    attachment_url: Optional[str] = None

class SubmissionResponse(SubmissionBase):
    id: int
    assignment_id: int
    student_id: int
    submitted_at: datetime
    grade_id: Optional[int] = None
    
    student_name: Optional[str] = None
    
    class Config:
        from_attributes = True
