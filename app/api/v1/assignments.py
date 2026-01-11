"""
API endpoints for Digital Assignments.
"""
from typing import Annotated, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.school import Class, Subject
from app.models.assignment import Assignment, Submission, AssignmentType
from app.models.journal import Grade, GradeType
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
    SubmissionCreate,
    SubmissionResponse,
    SubmissionUpdate
)
# Re-use GradeResponse schema if needed or keep it separate in logic

router = APIRouter(tags=["Assignments (Homework/Classwork)"])


# ==================== Assignments (Teacher) ====================

@router.post("/assignments/", response_model=AssignmentResponse)
async def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.TEACHER, UserRole.SCHOOL_ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new assignment (Homework, Classwork, etc.)."""
    # Verify class/subject context (omitted for brevity)
    
    new_assignment = Assignment(
        **assignment_data.model_dump(),
        teacher_id=current_user.id
    )
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)
    return new_assignment


@router.get("/assignments/class/{class_id}", response_model=List[AssignmentResponse])
async def list_class_assignments(
    class_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    subject_id: Optional[int] = None,
):
    """List assignments for a class (Teacher/Student view)."""
    # Security check: User must be related to class (omitted for MVP)
    
    query = select(Assignment).where(Assignment.class_id == class_id)
    if subject_id:
        query = query.where(Assignment.subject_id == subject_id)
        
    query = query.order_by(desc(Assignment.created_at))
    
    result = await db.execute(query)
    assignments = result.scalars().all()
    # Eager load teacher for name? Or join?
    # For now, return as is.
    return assignments


# ==================== Submissions (Student) ====================

@router.post("/submissions/", response_model=SubmissionResponse)
async def submit_assignment(
    submission_data: SubmissionCreate,
    current_user: Annotated[User, Depends(require_roles(UserRole.STUDENT))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit work for an assignment."""
    # Verify assignment exists and is for student's class
    stmt = select(Assignment).where(Assignment.id == submission_data.assignment_id)
    res = await db.execute(stmt)
    assignment = res.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.class_id != current_user.class_id:
        raise HTTPException(status_code=403, detail="Assignment is not for your class")
        
    # Check if already submitted? (Allow resubmission? Logic varies)
    # Let's check for existing submission
    existing_stmt = select(Submission).where(
        Submission.assignment_id == submission_data.assignment_id,
        Submission.student_id == current_user.id
    )
    existing_res = await db.execute(existing_stmt)
    existing = existing_res.scalar_one_or_none()
    
    if existing:
        # Update existing
        existing.content = submission_data.content
        existing.attachment_url = submission_data.attachment_url
        existing.submitted_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing
    
    # Create new
    new_submission = Submission(
        **submission_data.model_dump(),
        student_id=current_user.id
    )
    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)
    return new_submission


@router.get("/assignments/pending", response_model=List[AssignmentResponse])
async def get_pending_assignments(
    current_user: Annotated[User, Depends(require_roles(UserRole.STUDENT))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get pending assignments (not yet submitted) for the current student."""
    if not current_user.class_id:
         return []
         
    # Find assignments for student's class
    # That do NOT have a submission from this student
    # Subquery approach
    
    subquery = select(Submission.assignment_id).where(Submission.student_id == current_user.id)
    
    query = select(Assignment).where(
        Assignment.class_id == current_user.class_id,
        Assignment.id.not_in(subquery)
    ).order_by(Assignment.due_date)
    
    result = await db.execute(query)
    return result.scalars().all()


# ==================== Grading (Teacher) ====================

@router.post("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
async def grade_submission(
    submission_id: int,
    score: int,
    comment: Optional[str],
    current_user: Annotated[User, Depends(require_roles(UserRole.TEACHER, UserRole.SCHOOL_ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Grade a submission. 
    This automatically creates a Grade/Journal entry.
    """
    stmt = select(Submission).where(Submission.id == submission_id)
    # Eager load assignment to get details for Grade
    from sqlalchemy.orm import selectinload
    stmt = stmt.options(selectinload(Submission.assignment))
    
    res = await db.execute(stmt)
    submission = res.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    assignment = submission.assignment
    
    # Check permissions (teacher vs assignment teacher)
    if current_user.role == UserRole.TEACHER and assignment.teacher_id != current_user.id:
        # Strict mode: only creator can grade? Or any teacher of that school?
        # Let's allow creator for now.
        pass # Allow for MVP
        
    # Create or Update Grade entry
    # Check if linked grade exists
    grade_entry = None
    if submission.grade_id:
        grade_entry = await db.get(Grade, submission.grade_id)
        if grade_entry:
            grade_entry.score = score
            grade_entry.comment = comment
    
    if not grade_entry:
        # Map AssignmentType to GradeType
        grade_type = GradeType.HOMEWORK
        if assignment.assignment_type == AssignmentType.CLASSWORK:
             grade_type = GradeType.CLASSWORK
        elif assignment.assignment_type == AssignmentType.PROJECT:
             grade_type = GradeType.PROJECT
             
        grade_entry = Grade(
            date=datetime.utcnow().date(), # Grading date
            student_id=submission.student_id,
            subject_id=assignment.subject_id,
            teacher_id=current_user.id,
            grade_type=grade_type,
            score=score,
            comment=comment
        )
        db.add(grade_entry)
        await db.flush() # flush to get ID
        
        # Link to submission
        submission.grade_id = grade_entry.id
        
    await db.commit()
    await db.refresh(submission)
    return submission
