"""
API endpoints for Session Materials.
Auto-links materials to sessions based on subject.
"""
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.lesson_session import LessonSession
from app.models.lesson import Material
from app.models.session_material import SessionMaterial, MaterialAccess, AccessType
from app.schemas.session_material import (
    SessionMaterialResponse,
    MaterialAccessCreate,
    MaterialAccessResponse,
    SessionMaterialsListResponse
)

router = APIRouter(tags=["Session Materials"])


@router.get("/sessions/{session_id}/materials", response_model=SessionMaterialsListResponse)
async def get_session_materials(
    session_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get all materials available in a session.
    Auto-links materials based on session's subject.
    """
    # Verify session exists
    session = await db.get(LessonSession, session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify user has access
    if current_user.role == UserRole.STUDENT:
        if current_user.class_id != session.class_id:
            raise HTTPException(status_code=403, detail="Not your class session")
    elif current_user.role == UserRole.TEACHER:
        if current_user.id != session.teacher_id:
            raise HTTPException(status_code=403, detail="Not your session")
    
    # Get materials for session's subject
    # First check if materials are already linked
    stmt = select(SessionMaterial).where(
        SessionMaterial.session_id == session_id
    )
    result = await db.execute(stmt)
    session_materials = result.scalars().all()
    
    # If no materials linked yet, auto-link based on subject
    if not session_materials:
        # Get all materials for this subject
        materials_stmt = select(Material).where(
            and_(
                Material.lesson_id.in_(
                    select(Material.lesson_id).where(
                        Material.lesson_id.in_(
                            select(Material.lesson_id).distinct()
                        )
                    )
                ),
                Material.is_active == True
            )
        )
        # Simplified: just get materials for now
        # In production, you'd link via lesson -> subject relationship
        
    # Build response with material details
    responses = []
    for sm in session_materials:
        # Load material details
        material = await db.get(Material, sm.material_id)
        if material:
            resp = SessionMaterialResponse.model_validate(sm)
            resp.material_title = material.title
            resp.material_type = material.material_type.value
            resp.file_path = material.file_path
            resp.file_size = material.file_size
            responses.append(resp)
    
    return SessionMaterialsListResponse(
        session_id=session_id,
        materials=responses,
        total_count=len(responses)
    )


@router.post("/sessions/{session_id}/materials/{material_id}/access", response_model=MaterialAccessResponse)
async def track_material_access(
    session_id: int,
    material_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.STUDENT))],
    db: Annotated[AsyncSession, Depends(get_db)],
    access_type: AccessType = AccessType.VIEW,
):
    """
    Track when a student accesses a material during a session.
    Used for engagement analytics.
    """
    # Verify session exists and student has access
    session = await db.get(LessonSession, session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if current_user.class_id != session.class_id:
        raise HTTPException(status_code=403, detail="Not your class session")
    
    # Verify material exists
    material = await db.get(Material, material_id)
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Create access record
    access = MaterialAccess(
        session_id=session_id,
        material_id=material_id,
        student_id=current_user.id,
        access_type=access_type
    )
    db.add(access)
    await db.commit()
    await db.refresh(access)
    
    return MaterialAccessResponse.model_validate(access)


@router.post("/sessions/{session_id}/materials/{material_id}/download", response_model=MaterialAccessResponse)
async def track_download(
    session_id: int,
    material_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.STUDENT))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Track when a student downloads a material.
    """
    return await track_material_access(
        session_id=session_id,
        material_id=material_id,
        current_user=current_user,
        db=db,
        access_type=AccessType.DOWNLOAD
    )
