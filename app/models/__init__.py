"""
Models package initialization.
Imports all models for SQLAlchemy to discover them.
"""
from app.models.user import User, UserRole, RefreshToken
from app.models.school import School, Class, Subject, ClassSubject
from app.models.lesson import Lesson, Material, MaterialType
from app.models.exam import (
    Exam,
    ExamType,
    Question,
    QuestionType,
    ExamAttempt,
    AttemptStatus,
    Answer,
    Result,
)
from app.models.anti_cheat import CheatingEvent, CheatingEventType
from app.models.audit import AuditLog, AuditAction
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.sync import SyncEvent, SyncCheckpoint, SyncOperation, SyncStatus
from app.models.library import LibraryBook
from app.models.translation import Translation, UITranslation

__all__ = [
    # User
    "User",
    "UserRole",
    "RefreshToken",
    # School
    "School",
    "Class",
    "Subject",
    "ClassSubject",
    # Lesson
    "Lesson",
    "Material",
    "MaterialType",
    # Library
    "LibraryBook",
    # Exam
    "Exam",
    "ExamType",
    "Question",
    "QuestionType",
    "ExamAttempt",
    "AttemptStatus",
    "Answer",
    "Result",
    # Anti-cheat
    "CheatingEvent",
    "CheatingEventType",
    # Audit
    "AuditLog",
    "AuditAction",
    # Notification
    "Notification",
    "NotificationType",
    "NotificationPriority",
    # Sync
    "SyncEvent",
    "SyncCheckpoint",
    "SyncOperation",
    "SyncStatus",
    # Translation
    "Translation",
    "UITranslation",
]
