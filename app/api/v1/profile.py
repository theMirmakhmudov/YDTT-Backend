"""
User profile management endpoints.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.profile import UserProfileUpdate, UserProfileResponse, ProfilePictureUploadResponse
from app.core.storage import upload_file, delete_file

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/me/picture", response_model=ProfilePictureUploadResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload profile picture."""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Validate file size (max 5MB)
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    while chunk := await file.read(chunk_size):
        file_size += len(chunk)
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
    
    # Reset file pointer
    await file.seek(0)
    
    # Delete old profile picture if exists
    if current_user.profile_picture_url:
        try:
            await delete_file(current_user.profile_picture_url)
        except Exception:
            pass  # Ignore errors deleting old file
    
    # Upload new picture
    file_url = await upload_file(
        file=file,
        folder=f"profiles/{current_user.id}",
        filename=f"avatar_{current_user.id}"
    )
    
    # Update user
    current_user.profile_picture_url = file_url
    await db.commit()
    
    return ProfilePictureUploadResponse(profile_picture_url=file_url)


@router.delete("/me/picture")
async def delete_profile_picture(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete profile picture."""
    if not current_user.profile_picture_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile picture to delete"
        )
    
    # Delete file
    try:
        await delete_file(current_user.profile_picture_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
    
    # Update user
    current_user.profile_picture_url = None
    await db.commit()
    
    return {"message": "Profile picture deleted successfully"}
