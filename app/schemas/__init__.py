"""
Schemas package initialization.
"""
from app.schemas.auth import (
    TokenResponse,
    LoginRequest,
    RefreshRequest,
    LogoutRequest,
    PasswordChangeRequest,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserRoleUpdate,
    UserResponse,
    UserListResponse,
)
from app.schemas.school import (
    SchoolCreate,
    SchoolUpdate,
    SchoolResponse,
    SchoolListResponse,
    ClassCreate,
    ClassUpdate,
    ClassResponse,
    ClassListResponse,
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectListResponse,
)
from app.schemas.lesson import (
    LessonCreate,
    LessonUpdate,
    LessonResponse,
    LessonListResponse,
    MaterialCreate,
    MaterialResponse,
    MaterialListResponse,
    MaterialDownloadResponse,
)
from app.schemas.exam import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionWithAnswerResponse,
    ExamCreate,
    ExamUpdate,
    ExamResponse,
    ExamListResponse,
    ExamStartResponse,
    ExamSubmitRequest,
    AttemptResponse,
    ResultResponse,
    EvaluateRequest,
)
from app.schemas.anti_cheat import (
    CheatingEventCreate,
    CheatingEventResponse,
    CheatingReportResponse,
)
from app.schemas.sync import (
    SyncPushRequest,
    SyncPushResponse,
    SyncPullResponse,
)
from app.schemas.notification import (
    NotificationCreate,
    NotificationBulkCreate,
    NotificationResponse,
    NotificationListResponse,
)
from app.schemas.progress import (
    StudentProgressResponse,
    ClassProgressResponse,
    DashboardAnalytics,
    AuditLogResponse,
    AuditLogListResponse,
)
from app.schemas.common import (
    MessageResponse,
    ErrorResponse,
    HealthResponse,
)

__all__ = [
    # Auth
    "TokenResponse",
    "LoginRequest",
    "RefreshRequest",
    "LogoutRequest",
    "PasswordChangeRequest",
    # User
    "UserCreate",
    "UserUpdate",
    "UserRoleUpdate",
    "UserResponse",
    "UserListResponse",
    # School
    "SchoolCreate",
    "SchoolUpdate",
    "SchoolResponse",
    "SchoolListResponse",
    "ClassCreate",
    "ClassUpdate",
    "ClassResponse",
    "ClassListResponse",
    "SubjectCreate",
    "SubjectUpdate",
    "SubjectResponse",
    "SubjectListResponse",
    # Lesson
    "LessonCreate",
    "LessonUpdate",
    "LessonResponse",
    "LessonListResponse",
    "MaterialCreate",
    "MaterialResponse",
    "MaterialListResponse",
    "MaterialDownloadResponse",
    # Exam
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    "QuestionWithAnswerResponse",
    "ExamCreate",
    "ExamUpdate",
    "ExamResponse",
    "ExamListResponse",
    "ExamStartResponse",
    "ExamSubmitRequest",
    "AttemptResponse",
    "ResultResponse",
    "EvaluateRequest",
    # Anti-cheat
    "CheatingEventCreate",
    "CheatingEventResponse",
    "CheatingReportResponse",
    # Sync
    "SyncPushRequest",
    "SyncPushResponse",
    "SyncPullResponse",
    # Notification
    "NotificationCreate",
    "NotificationBulkCreate",
    "NotificationResponse",
    "NotificationListResponse",
    # Progress
    "StudentProgressResponse",
    "ClassProgressResponse",
    "DashboardAnalytics",
    "AuditLogResponse",
    "AuditLogListResponse",
    # Common
    "MessageResponse",
    "ErrorResponse",
    "HealthResponse",
]
