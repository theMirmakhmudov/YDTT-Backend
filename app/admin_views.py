"""
SQLAdmin Model Views for YDTT Backend.
Minimal configuration to ensure startup - expand column_list later as needed.
"""
from sqladmin import ModelView
from app.models.user import User
from app.models.school import School, Class, Subject
from app.models.lesson import Lesson, Material
from app.models.library import LibraryBook
from app.models.exam import Exam, Question, ExamAttempt, Answer, Result
from app.models.audit import AuditLog
from app.models.anti_cheat import CheatingEvent

# --- User Management ---
class UserView(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

# --- School Management ---
class SchoolView(ModelView, model=School):
    name = "School"
    name_plural = "Schools"
    icon = "fa-solid fa-school"

class ClassView(ModelView, model=Class):
    name = "Class"
    name_plural = "Classes"
    icon = "fa-solid fa-users-rectangle"

class SubjectView(ModelView, model=Subject):
    name = "Subject"
    name_plural = "Subjects"
    icon = "fa-solid fa-book"

# --- Content ---
class LessonView(ModelView, model=Lesson):
    name = "Lesson"
    name_plural = "Lessons"
    icon = "fa-solid fa-chalkboard-user"

class MaterialView(ModelView, model=Material):
    name = "Material"
    name_plural = "Materials"
    icon = "fa-solid fa-file"

class LibraryBookView(ModelView, model=LibraryBook):
    name = "Library Book"
    name_plural = "Library Books"
    icon = "fa-solid fa-book-open"

# --- Exams ---
class ExamView(ModelView, model=Exam):
    name = "Exam"
    name_plural = "Exams"
    icon = "fa-solid fa-pen-to-square"

class QuestionView(ModelView, model=Question):
    name = "Question"
    name_plural = "Questions"
    icon = "fa-solid fa-question"

class AttemptView(ModelView, model=ExamAttempt):
    name = "Exam Attempt"
    name_plural = "Exam Attempts"
    icon = "fa-solid fa-person-writing"

class AnswerView(ModelView, model=Answer):
    name = "Answer"
    name_plural = "Answers"
    icon = "fa-solid fa-reply"

class ResultView(ModelView, model=Result):
    name = "Result"
    name_plural = "Results"
    icon = "fa-solid fa-trophy"

# --- Monitoring ---
class AuditLogView(ModelView, model=AuditLog):
    name = "Audit Log"
    name_plural = "Audit Logs"
    icon = "fa-solid fa-clipboard-list"
    can_create = False
    can_edit = False
    can_delete = False

class CheatingEventView(ModelView, model=CheatingEvent):
    name = "Cheating Event"
    name_plural = "Cheating Events"
    icon = "fa-solid fa-triangle-exclamation"
    can_create = False

# Export all views
views = [
    UserView,
    SchoolView, ClassView, SubjectView,
    LessonView, MaterialView, LibraryBookView,
    ExamView, QuestionView, AttemptView, AnswerView, ResultView,
    AuditLogView, CheatingEventView
]
