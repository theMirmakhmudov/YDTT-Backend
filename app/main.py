"""
YDTT Backend - Yagona Davlat Ta'lim Tizimi
(Unified State Education System)

Main FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.database import engine
from app.api.v1 import router as api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Could initialize connections, run migrations, etc.
    yield
    # Shutdown
    print("Shutting down...")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## YDTT (Yagona Davlat Ta'lim Tizimi) - Unified State Education System

Government-scale education platform backend providing:
- **Authentication**: JWT-based with role-based access control (RBAC)
- **User Management**: Students, teachers, and administrators
- **School Structure**: Schools, classes, subjects organization
- **Learning Content**: Lessons and materials with versioning
- **Exam System**: Automated assessment with multiple question types
- **Anti-Cheating**: Event logging and risk scoring
- **Offline Sync**: Offline-first data synchronization
- **Analytics**: Progress tracking and dashboard metrics
- **Audit Logging**: Immutable action logs

### Multilingual Support
- 🇺🇿 Uzbek (uz) - Primary
- 🇬🇧 English (en)
- 🇷🇺 Russian (ru)
- 🇰🇿 Kazakh (kk)
- 🇰🇬 Kyrgyz (ky)
    """,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with localized messages."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc),
            },
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
        },
    )


# Register API routers
# Register API routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


# Admin Panel
from sqladmin import Admin
from app.admin import authentication_backend
from app.admin_views import views

admin = Admin(app, engine, authentication_backend=authentication_backend, title="YDTT Admin")
for view in views:
    admin.add_view(view)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": "ydtt-backend",
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "YDTT (Yagona Davlat Ta'lim Tizimi) Backend API",
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "languages": settings.SUPPORTED_LANGUAGES,
    }
