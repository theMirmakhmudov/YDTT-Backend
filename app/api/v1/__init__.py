"""
API v1 router initialization.
"""
from fastapi import APIRouter

from app.api.v1 import auth, users, schools, lessons, exams, anti_cheat, sync, notifications, progress, library, journal, timetable, assignments


router = APIRouter()

# Register all routers
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(schools.router)
router.include_router(lessons.router)
router.include_router(exams.router)
router.include_router(anti_cheat.router)
router.include_router(sync.router)
router.include_router(notifications.router)
router.include_router(progress.router)
router.include_router(library.router)
router.include_router(journal.router)
router.include_router(timetable.router)
router.include_router(assignments.router)
