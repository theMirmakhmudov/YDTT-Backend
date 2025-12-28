"""
Exam and Question API endpoints.
"""
from typing import Annotated, Optional, List
from math import ceil
from datetime import datetime, timedelta
import random

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.exam import Exam, Question, ExamAttempt, Answer, Result, AttemptStatus
from app.models.audit import AuditLog, AuditAction
from app.schemas.exam import (
    ExamCreate,
    ExamUpdate,
    ExamResponse,
    ExamListResponse,
    QuestionCreate,
    QuestionResponse,
    ExamStartResponse,
    ExamSubmitRequest,
    AttemptResponse,
    ResultResponse,
)


router = APIRouter(prefix="/exams", tags=["Exams & Assessments"])


# ==================== Exams ====================


@router.get("/", response_model=ExamListResponse)
async def list_exams(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject_id: Optional[int] = None,
    class_id: Optional[int] = None,
    is_published: Optional[bool] = None,
):
    """List exams with pagination and filtering."""
    query = select(Exam).where(Exam.is_active == True)
    count_query = select(func.count(Exam.id)).where(Exam.is_active == True)
    
    # Students only see published exams available to them
    if current_user.role == UserRole.STUDENT:
        query = query.where(Exam.is_published == True)
        count_query = count_query.where(Exam.is_published == True)
        if current_user.class_id:
            query = query.where(
                (Exam.class_id == current_user.class_id) | (Exam.class_id == None)
            )
            count_query = count_query.where(
                (Exam.class_id == current_user.class_id) | (Exam.class_id == None)
            )
    elif is_published is not None:
        query = query.where(Exam.is_published == is_published)
        count_query = count_query.where(Exam.is_published == is_published)
    
    if subject_id:
        query = query.where(Exam.subject_id == subject_id)
        count_query = count_query.where(Exam.subject_id == subject_id)
    
    if class_id:
        query = query.where(Exam.class_id == class_id)
        count_query = count_query.where(Exam.class_id == class_id)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Exam.created_at.desc())
    
    result = await db.execute(query)
    exams = result.scalars().all()
    
    # Get question counts
    exam_responses = []
    for exam in exams:
        count_result = await db.execute(
            select(func.count(Question.id)).where(
                Question.exam_id == exam.id, Question.is_active == True
            )
        )
        question_count = count_result.scalar()
        response = ExamResponse.model_validate(exam)
        response.question_count = question_count
        exam_responses.append(response)
    
    return ExamListResponse(
        items=exam_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    exam_data: ExamCreate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new exam."""
    new_exam = Exam(
        **exam_data.model_dump(),
        created_by_id=current_user.id,
    )
    db.add(new_exam)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.EXAM_CREATE,
        resource_type="Exam",
        new_values={"title": new_exam.title},
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(new_exam)
    
    response = ExamResponse.model_validate(new_exam)
    response.question_count = 0
    return response


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific exam by ID."""
    query = select(Exam).where(Exam.id == exam_id, Exam.is_active == True)
    
    if current_user.role == UserRole.STUDENT:
        query = query.where(Exam.is_published == True)
    
    result = await db.execute(query)
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )
    
    # Get question count
    count_result = await db.execute(
        select(func.count(Question.id)).where(
            Question.exam_id == exam.id, Question.is_active == True
        )
    )
    question_count = count_result.scalar()
    
    response = ExamResponse.model_validate(exam)
    response.question_count = question_count
    return response


@router.put("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: int,
    exam_update: ExamUpdate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an exam."""
    result = await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.is_active == True)
    )
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )
    
    # Teachers can only update their own exams
    if current_user.role == UserRole.TEACHER:
        if exam.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update another teacher's exam",
            )
    
    update_data = exam_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(exam, field, value)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.EXAM_UPDATE,
        resource_type="Exam",
        resource_id=exam.id,
        new_values=update_data,
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(exam)
    
    return ExamResponse.model_validate(exam)


# ==================== Questions ====================


@router.post("/{exam_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_question(
    exam_id: int,
    question_data: QuestionCreate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add a question to an exam."""
    # Verify exam exists
    result = await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.is_active == True)
    )
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )
    
    # Teachers can only add questions to their own exams
    if current_user.role == UserRole.TEACHER:
        if exam.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot add questions to another teacher's exam",
            )
    
    # Convert options to dict format
    options_dict = None
    if question_data.options:
        options_dict = [opt.model_dump() for opt in question_data.options]
    
    new_question = Question(
        exam_id=exam_id,
        question_type=question_data.question_type,
        text=question_data.text,
        explanation=question_data.explanation,
        options=options_dict,
        correct_answer=question_data.correct_answer,
        numeric_tolerance=question_data.numeric_tolerance,
        points=question_data.points,
        partial_credit=question_data.partial_credit,
        order=question_data.order,
        image_url=question_data.image_url,
    )
    db.add(new_question)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.QUESTION_CREATE,
        resource_type="Question",
        new_values={"exam_id": exam_id, "type": question_data.question_type.value},
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(new_question)
    
    return QuestionResponse.model_validate(new_question)


@router.get("/{exam_id}/questions", response_model=List[QuestionResponse])
async def list_questions(
    exam_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all questions for an exam (without correct answers for students)."""
    # Verify exam exists and is accessible
    query = select(Exam).where(Exam.id == exam_id, Exam.is_active == True)
    if current_user.role == UserRole.STUDENT:
        query = query.where(Exam.is_published == True)
    
    result = await db.execute(query)
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )
    
    # Get questions
    result = await db.execute(
        select(Question)
        .where(Question.exam_id == exam_id, Question.is_active == True)
        .order_by(Question.order)
    )
    questions = result.scalars().all()
    
    return [QuestionResponse.model_validate(q) for q in questions]


# ==================== Exam Attempts ====================


@router.post("/{exam_id}/start", response_model=ExamStartResponse)
async def start_exam(
    request: Request,
    exam_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    device_id: Optional[str] = None,
):
    """Start an exam attempt."""
    # Get exam
    result = await db.execute(
        select(Exam).where(
            Exam.id == exam_id, 
            Exam.is_active == True,
            Exam.is_published == True
        )
    )
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or not published",
        )
    
    # Check availability window
    now = datetime.utcnow()
    if exam.available_from and now < exam.available_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam is not yet available",
        )
    if exam.available_until and now > exam.available_until:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam is no longer available",
        )
    
    # Check max attempts
    existing_attempts = await db.execute(
        select(func.count(ExamAttempt.id)).where(
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.student_id == current_user.id,
            ExamAttempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.EVALUATED])
        )
    )
    attempt_count = existing_attempts.scalar()
    
    if attempt_count >= exam.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum attempts ({exam.max_attempts}) reached",
        )
    
    # Check for in-progress attempt
    result = await db.execute(
        select(ExamAttempt).where(
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.student_id == current_user.id,
            ExamAttempt.status == AttemptStatus.IN_PROGRESS,
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Return existing in-progress attempt
        if existing.expires_at and now > existing.expires_at:
            existing.status = AttemptStatus.EXPIRED
            await db.commit()
            # Continue to create new attempt
        else:
            # Get questions
            result = await db.execute(
                select(Question)
                .where(Question.exam_id == exam_id, Question.is_active == True)
                .order_by(Question.order)
            )
            questions = result.scalars().all()
            
            return ExamStartResponse(
                attempt_id=existing.id,
                questions=[QuestionResponse.model_validate(q) for q in questions],
                expires_at=existing.expires_at,
                started_at=existing.started_at,
            )
    
    # Get questions
    result = await db.execute(
        select(Question)
        .where(Question.exam_id == exam_id, Question.is_active == True)
        .order_by(Question.order)
    )
    questions = list(result.scalars().all())
    
    # Shuffle if configured
    question_order = [q.id for q in questions]
    if exam.shuffle_questions:
        random.shuffle(question_order)
    
    # Create attempt
    started_at = datetime.utcnow()
    expires_at = started_at + timedelta(minutes=exam.duration_minutes)
    
    new_attempt = ExamAttempt(
        exam_id=exam_id,
        student_id=current_user.id,
        status=AttemptStatus.IN_PROGRESS,
        attempt_number=attempt_count + 1,
        started_at=started_at,
        expires_at=expires_at,
        device_id=device_id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        question_order={"order": question_order},
    )
    db.add(new_attempt)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.EXAM_START,
        resource_type="ExamAttempt",
        new_values={"exam_id": exam_id, "attempt_number": attempt_count + 1},
        ip_address=request.client.host,
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(new_attempt)
    
    # Order questions according to shuffle
    question_map = {q.id: q for q in questions}
    ordered_questions = [question_map[qid] for qid in question_order if qid in question_map]
    
    return ExamStartResponse(
        attempt_id=new_attempt.id,
        questions=[QuestionResponse.model_validate(q) for q in ordered_questions],
        expires_at=expires_at,
        started_at=started_at,
    )


@router.post("/{exam_id}/submit", response_model=AttemptResponse)
async def submit_exam(
    request: Request,
    exam_id: int,
    submit_request: ExamSubmitRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit exam answers."""
    # Find in-progress attempt
    result = await db.execute(
        select(ExamAttempt).where(
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.student_id == current_user.id,
            ExamAttempt.status == AttemptStatus.IN_PROGRESS,
        )
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active exam attempt found",
        )
    
    # Check if expired
    now = datetime.utcnow()
    if attempt.expires_at and now > attempt.expires_at:
        attempt.status = AttemptStatus.EXPIRED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam attempt has expired",
        )
    
    # Save answers
    for answer_data in submit_request.answers:
        # Check if answer already exists
        result = await db.execute(
            select(Answer).where(
                Answer.attempt_id == attempt.id,
                Answer.question_id == answer_data.question_id,
            )
        )
        existing_answer = result.scalar_one_or_none()
        
        if existing_answer:
            existing_answer.answer_value = answer_data.answer_value
            existing_answer.time_spent_seconds = answer_data.time_spent_seconds
            existing_answer.updated_at = now
        else:
            new_answer = Answer(
                attempt_id=attempt.id,
                question_id=answer_data.question_id,
                answer_value=answer_data.answer_value,
                time_spent_seconds=answer_data.time_spent_seconds,
                offline_id=answer_data.offline_id,
            )
            db.add(new_answer)
    
    # Update attempt status
    attempt.status = AttemptStatus.SUBMITTED
    attempt.submitted_at = now
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.EXAM_SUBMIT,
        resource_type="ExamAttempt",
        resource_id=attempt.id,
        new_values={"answers_count": len(submit_request.answers)},
        ip_address=request.client.host,
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(attempt)
    
    return AttemptResponse.model_validate(attempt)


@router.post("/{exam_id}/evaluate", response_model=ResultResponse)
async def evaluate_exam(
    exam_id: int,
    attempt_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Trigger evaluation for a submitted exam attempt."""
    # Get attempt
    result = await db.execute(
        select(ExamAttempt)
        .where(ExamAttempt.id == attempt_id, ExamAttempt.exam_id == exam_id)
        .options(selectinload(ExamAttempt.answers))
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam attempt not found",
        )
    
    # Check if user can evaluate (owner or admin)
    if attempt.student_id != current_user.id:
        if current_user.role not in [
            UserRole.TEACHER, UserRole.SCHOOL_ADMIN, 
            UserRole.REGION_ADMIN, UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to evaluate this attempt",
            )
    
    if attempt.status not in [AttemptStatus.SUBMITTED, AttemptStatus.EVALUATED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot evaluate attempt with status {attempt.status.value}",
        )
    
    # Check if already evaluated
    result = await db.execute(
        select(Result).where(Result.attempt_id == attempt_id)
    )
    existing_result = result.scalar_one_or_none()
    
    if existing_result:
        return ResultResponse.model_validate(existing_result)
    
    # Get questions
    result = await db.execute(
        select(Question).where(Question.exam_id == exam_id, Question.is_active == True)
    )
    questions = {q.id: q for q in result.scalars().all()}
    
    # Evaluate answers
    total_points = sum(q.points for q in questions.values())
    earned_points = 0.0
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0
    breakdown = []
    
    answered_question_ids = {a.question_id for a in attempt.answers}
    
    for question_id, question in questions.items():
        if question_id not in answered_question_ids:
            unanswered_count += 1
            breakdown.append({
                "question_id": question_id,
                "is_correct": False,
                "points_earned": 0,
                "status": "unanswered"
            })
            continue
        
        answer = next(a for a in attempt.answers if a.question_id == question_id)
        is_correct = False
        points_earned = 0.0
        
        # Evaluate based on question type
        from app.models.exam import QuestionType
        
        if question.question_type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]:
            is_correct = answer.answer_value == question.correct_answer
        elif question.question_type == QuestionType.NUMERIC:
            try:
                answer_value = float(answer.answer_value)
                correct_value = float(question.correct_answer)
                tolerance = question.numeric_tolerance or 0.0
                is_correct = abs(answer_value - correct_value) <= tolerance
            except (ValueError, TypeError):
                is_correct = False
        elif question.question_type == QuestionType.SHORT_ANSWER:
            # Simple case-insensitive match (could be enhanced with AI)
            is_correct = answer.answer_value.strip().lower() == question.correct_answer.strip().lower()
        
        if is_correct:
            correct_count += 1
            points_earned = question.points
            earned_points += points_earned
        else:
            incorrect_count += 1
        
        # Update answer record
        answer.is_correct = is_correct
        answer.points_earned = points_earned
        
        breakdown.append({
            "question_id": question_id,
            "is_correct": is_correct,
            "points_earned": points_earned,
        })
    
    # Calculate percentage
    percentage = (earned_points / total_points * 100) if total_points > 0 else 0
    
    # Get exam for passing score
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one()
    is_passed = percentage >= exam.passing_score
    
    # Create result
    new_result = Result(
        attempt_id=attempt_id,
        total_points=total_points,
        earned_points=earned_points,
        percentage=percentage,
        is_passed=is_passed,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unanswered_count=unanswered_count,
        breakdown=breakdown,
    )
    db.add(new_result)
    
    # Update attempt status
    attempt.status = AttemptStatus.EVALUATED
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.EXAM_EVALUATE,
        resource_type="Result",
        resource_id=attempt_id,
        new_values={"percentage": percentage, "is_passed": is_passed},
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(new_result)
    
    return ResultResponse.model_validate(new_result)
