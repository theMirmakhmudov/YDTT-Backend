"""
Digital Library API endpoints.
"""
from typing import Annotated, Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.dependencies import require_roles, CurrentUser
from app.models.user import User, UserRole
from app.models.library import LibraryBook
from app.models.audit import AuditLog, AuditAction
from app.schemas.library import (
    LibraryBookCreate,
    LibraryBookUpdate,
    LibraryBookResponse,
    LibraryBookListResponse
)

router = APIRouter(prefix="/library", tags=["Digital Library"])


@router.get("/", response_model=LibraryBookListResponse)
async def list_books(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject_id: Optional[int] = None,
    grade: Optional[int] = None,
    search: Optional[str] = None,
    current_user: CurrentUser = None, 
):
    """List books with filtering."""
    # Ensure user is authenticated
    if not current_user:
        # Should be handled by dependency but just in case
        pass
    
    query = select(LibraryBook).where(LibraryBook.is_active == True)
    count_query = select(func.count(LibraryBook.id)).where(LibraryBook.is_active == True)
    
    if subject_id:
        query = query.where(LibraryBook.subject_id == subject_id)
        count_query = count_query.where(LibraryBook.subject_id == subject_id)
    
    if grade:
        query = query.where(LibraryBook.grade == grade)
        count_query = count_query.where(LibraryBook.grade == grade)
        
    if search:
        search_pattern = f"%{search}%"
        query = query.where(LibraryBook.title.ilike(search_pattern))
        count_query = count_query.where(LibraryBook.title.ilike(search_pattern))
        
    # Get total
    total = (await db.execute(count_query)).scalar() or 0
    
    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(LibraryBook.title)
    
    result = await db.execute(query)
    books = result.scalars().all()
    
    return LibraryBookListResponse(
        items=books,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.post("/", response_model=LibraryBookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: LibraryBookCreate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Upload/Add a new book to the library."""
    # Note: File upload would typically happen via a separate endpoint returning file_path
    # or this endpoint uses Multipart. For now, we assume file_path is provided (S3 key).
    
    new_book = LibraryBook(
        **book_data.model_dump(),
        created_by_id=current_user.id
    )
    db.add(new_book)
    
    # Audit
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role.value,
        action=AuditAction.MATERIAL_UPLOAD,
        resource_type="LibraryBook",
        new_values={"title": new_book.title},
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(new_book)
    return new_book


@router.get("/{book_id}", response_model=LibraryBookResponse)
async def get_book(
    book_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser, # Require login
):
    """Get book details."""
    result = await db.execute(select(LibraryBook).where(LibraryBook.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
        
    return book


@router.put("/{book_id}", response_model=LibraryBookResponse)
async def update_book(
    book_id: int,
    book_update: LibraryBookUpdate,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a book."""
    result = await db.execute(select(LibraryBook).where(LibraryBook.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    # Permission check for teachers (can only update own??)
    # Ideally teachers should be able to update if they created it, or maybe any teacher?
    # Let's enforce owner policy for teachers
    if current_user.role == UserRole.TEACHER and book.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this book")
        
    update_data = book_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)
        
    await db.commit()
    await db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    current_user: Annotated[User, Depends(require_roles(
        UserRole.SCHOOL_ADMIN, UserRole.REGION_ADMIN,
        UserRole.SUPER_ADMIN, UserRole.TECH_ADMIN
    ))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete (soft delete or hard delete) a book."""
    # Let's do hard delete for now or soft if is_active=False
    # Only Admins can delete
    
    result = await db.execute(select(LibraryBook).where(LibraryBook.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    await db.delete(book)
    await db.commit()
    return None
