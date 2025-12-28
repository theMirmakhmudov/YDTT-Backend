"""
Common schemas used across the application.
"""
from typing import Generic, TypeVar, List, Optional

from pydantic import BaseModel


T = TypeVar("T")


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    redis: str
