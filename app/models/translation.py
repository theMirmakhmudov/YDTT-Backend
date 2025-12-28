"""
Translation model for multilingual content storage.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Translation(Base):
    """
    Stores translations for content.
    Supports: uz (Uzbek), en (English), ru (Russian), kk (Kazakh), ky (Kyrgyz)
    """
    __tablename__ = "translations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Resource identification
    resource_type: Mapped[str] = mapped_column(String(50), index=True)
    resource_id: Mapped[int] = mapped_column(index=True)
    field_name: Mapped[str] = mapped_column(String(50))
    
    # Language code (ISO 639-1)
    language: Mapped[str] = mapped_column(String(5), index=True)
    
    # Translation content
    value: Mapped[str] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint and index
    __table_args__ = (
        Index(
            "ix_translations_lookup",
            "resource_type", "resource_id", "field_name", "language",
            unique=True
        ),
    )


class UITranslation(Base):
    """
    Stores UI string translations for the application.
    """
    __tablename__ = "ui_translations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Key for the translation
    key: Mapped[str] = mapped_column(String(255), index=True)
    
    # Language code
    language: Mapped[str] = mapped_column(String(5), index=True)
    
    # Translation value
    value: Mapped[str] = mapped_column(Text)
    
    # Context/description for translators
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        Index(
            "ix_ui_translations_key_lang",
            "key", "language",
            unique=True
        ),
    )
