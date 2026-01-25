"""
Models package initialization.
Imports all models for SQLAlchemy to discover them.
"""
from app.models.user import User, UserRole, RefreshToken
from app.models.school import School, Class, Subject
from app.models.lesson import Lesson, Material, MaterialType
from app.models.exam import Exam, Question, QuestionType, ExamAttempt, Answer, Result, ExamType, AttemptStatus
from app.models.anti_cheat import CheatingEvent, CheatingEventType
from app.models.sync import SyncEvent, SyncCheckpoint, SyncOperation, SyncStatus
from app.models.audit import AuditLog, AuditAction
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.journal import Attendance, AttendanceStatus, Grade, GradeType
from app.models.library import LibraryBook
from app.models.timetable import TimeSlot, Schedule, DayOfWeek
from app.models.assignment import Assignment, Submission, AssignmentType
from app.models.lesson_session import LessonSession, LessonSessionStatus, StudentNote
from app.models.session_attendance import SessionAttendance
from app.models.whiteboard import WhiteboardEvent, WhiteboardEventType
from app.models.session_material import SessionMaterial, MaterialAccess
from app.models.ai_learning import (
    AIPerformanceAnalysis,
    AIImprovementPlan,
    AITutorSession,
    AIGeneratedPractice,
)
from app.models.curriculum import (
    CurriculumTemplate,
    CurriculumTopic,
    CurriculumSubtopic,
    AcademicYear,
    Holiday,
    SchoolEvent,
    CurriculumSchedule,
    ScheduledTopic,
    ScheduledLesson,
)

__all__ = [
    # User
    "User",
    "UserRole",
    "RefreshToken",
    # School
    "School",
    "Class",
    "Subject",
    # Lesson
    "Lesson",
    "Material",
    "MaterialType",
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
    # Sync
    "SyncEvent",
    "SyncCheckpoint",
    "SyncOperation",
    "SyncStatus",
    # Audit
    "AuditLog",
    "AuditAction",
    # Notification
    "Notification",
    "NotificationType",
    "NotificationPriority",
    # Journal
    "Attendance",
    "AttendanceStatus",
    "Grade",
    "GradeType",
    # Library
    "LibraryBook",
    # Timetable
    "TimeSlot",
    "Schedule",
    "DayOfWeek",
    # Assignment
    "Assignment",
    "Submission",
    "AssignmentType",
    # Live Sessions
    "LessonSession",
    "LessonSessionStatus",
    "StudentNote",
    "SessionAttendance",
    "WhiteboardEvent",
    "WhiteboardEventType",
    "SessionMaterial",
    "MaterialAccess",
    # AI Learning
    "AIPerformanceAnalysis",
    "AIImprovementPlan",
    "AITutorSession",
    "AIGeneratedPractice",
    # Curriculum
    "CurriculumTemplate",
    "CurriculumTopic",
    "CurriculumSubtopic",
    "AcademicYear",
    "Holiday",
    "SchoolEvent",
    "CurriculumSchedule",
    "ScheduledTopic",
    "ScheduledLesson",
]
