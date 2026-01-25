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
## YDTT (Yagona Davlat Ta'lim Tizimi) - Yagona Davlat Ta'lim Tizimi

Davlat miqyosidagi ta'lim platformasi backend quyidagilarni taqdim etadi:

- **Autentifikatsiya**: JWT asosida rol asosida kirish nazorati (RBAC)
- **Foydalanuvchilarni boshqarish**: O'quvchilar, o'qituvchilar va administratorlar
- **Maktab tuzilmasi**: Maktablar, sinflar, fanlar tashkil etish
- **Ta'lim kontenti**: Darslar va materiallar versiyalash bilan
- **Jonli darslar**: WebSocket qo'llab-quvvatlash bilan real vaqtda raqamli sinf xonasi
- **Avtomatik davomat**: Sessiya asosida davomat kuzatish
- **Interaktiv doska**: O'qituvchidan o'quvchiga real vaqtda chizish
- **Sessiya materiallari**: Avtomatik bog'langan ta'lim resurslari
- **Imtihon tizimi**: Ko'p savol turlari bilan avtomatlashtirilgan baholash
- **Firibgarlikka qarshi**: Hodisalarni qayd etish va xavf baholash
- **Oflayn sinxronizatsiya**: Oflayn-birinchi ma'lumotlar sinxronizatsiyasi
- **Tahlillar**: Taraqqiyotni kuzatish va boshqaruv paneli ko'rsatkichlari
- **Audit jurnali**: O'zgarmas harakat jurnallari
- **Foydalanuvchi profili**: Profil rasmi va shaxsiy ma'lumotlarni sozlash
- **AI o'qituvchi**: 24/7 uy vazifasi yordami va shaxsiylashtirilgan o'rganish
- **O'quv dasturi boshqaruvi**: To'liq o'quv yili avtomatik rejalashtirish

### Til qo'llab-quvvatlash
- 🇺🇿 O'zbek (uz) - Asosiy
- 🇬🇧 Ingliz (en)
- 🇷🇺 Rus (ru)
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
    # Always return detailed errors as requested by user
    error_type = type(exc).__name__
    error_msg = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "type": error_type,
            "detail": error_msg,
            "path": request.url.path
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
