"""
AI API Routes: Expose Socratic Tutor & Content Generation.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.ai import AIService, ChatMessage
from app.core.dependencies import get_current_active_user
from app.models.user import User, UserRole

router = APIRouter(prefix="/ai", tags=["ai"])
ai_service = AIService()

# --- Request Models ---

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    subject: str = "General"

class ChatResponse(BaseModel):
    response: str

class HomeworkGenRequest(BaseModel):
    topic: str
    grade: int
    difficulty: str = "medium"

# --- Endpoints ---

@router.post("/chat", response_model=ChatResponse)
async def chat_with_tutor(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Chat with the Socratic AI Tutor.
    Enforces strict guardrails (no direct answers).
    """
    # 1. Determine Grade context (if student)
    grade = 5 # Default
    if current_user.class_:
        grade = current_user.class_.grade
        
    # 2. Get Response
    response_text = await ai_service.get_tutor_response(
        history=request.messages,
        student_grade=grade,
        subject_name=request.subject
    )
    
    return ChatResponse(response=response_text)

@router.post("/generate-homework")
async def generate_homework(
    request: HomeworkGenRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate homework for a topic.
    TEACHER ONLY.
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only teachers can generate homework"
        )
        
    return await ai_service.generate_homework(
        topic=request.topic,
        grade=request.grade,
        difficulty=request.difficulty
    )
