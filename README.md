# YDTT Backend

**Yagona Davlat Ta'lim Tizimi** (Unified State Education System)

Government-scale education platform backend built with FastAPI, PostgreSQL, Redis, and Celery.

## Features

- 🔐 **JWT Authentication** with role-based access control (RBAC)
- 👥 **User Management**: Students, Teachers, School/Region/Super Admins
- 🏫 **School Structure**: Schools → Classes → Subjects → Lessons
- 📚 **Learning Content**: Lessons and materials with versioning and checksums
- 📝 **Exam System**: Automated assessment with multiple question types
- 🛡️ **Anti-Cheating**: Event logging with risk scoring
- 📱 **Offline Sync**: Offline-first data synchronization with conflict resolution
- 📊 **Analytics**: Progress tracking and dashboard metrics
- 📋 **Audit Logging**: Immutable action logs for compliance
- 🌐 **Multilingual**: uz (Uzbek), en (English), ru (Russian), kk (Kazakh), ky (Kyrgyz)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+

### Development

1. **Clone and setup**:
```bash
cd YDTT-Backend
cp .env.example .env
```

2. **Start services**:
```bash
docker-compose up -d
```

3. **Run migrations**:
```bash
docker-compose exec app alembic upgrade head
```

4. **Access the API**:
   - API Docs: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

### Create Initial Admin User

```bash
docker-compose exec app python app/initial_data.py
```

## API Endpoints

### Authentication
```
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

### Users
```
GET/POST     /api/v1/users/
GET/PUT/DEL  /api/v1/users/{id}
```

### Schools
```
GET/POST  /api/v1/schools/
GET/POST  /api/v1/classes/
GET/POST  /api/v1/subjects/
```

### Content
```
GET/POST  /api/v1/lessons/
GET       /api/v1/lessons/{id}
GET/POST  /api/v1/materials/
```

### Exams
```
GET/POST  /api/v1/exams/
POST      /api/v1/exams/{id}/questions
POST      /api/v1/exams/{id}/start
POST      /api/v1/exams/{id}/submit
POST      /api/v1/exams/{id}/evaluate
```

### Anti-Cheating
```
POST  /api/v1/anti-cheat/event
GET   /api/v1/anti-cheat/report/{attempt_id}
```

### Sync
```
POST  /api/v1/sync/push
GET   /api/v1/sync/pull
```

### Analytics
```
GET  /api/v1/progress/student/{id}
GET  /api/v1/progress/class/{id}
GET  /api/v1/analytics/dashboard
GET  /api/v1/audit-logs/
```

## Project Structure

```
YDTT-Backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/                # Configuration, security, database
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/v1/              # API routers
│   └── tasks/               # Celery tasks
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## User Roles

| Role | Code | Permissions |
|------|------|-------------|
| Student | `STUDENT` | Take exams, view materials |
| Teacher | `TEACHER` | Create content, manage exams |
| School Admin | `SCHOOL_ADMIN` | Manage school users/classes |
| Region Admin | `REGION_ADMIN` | Manage region schools |
| Super Admin | `SUPER_ADMIN` | Full system access |
| Tech Admin | `TECH_ADMIN` | Technical operations |

## Technology Stack

- **Backend**: FastAPI + Pydantic v2
- **Database**: PostgreSQL + SQLAlchemy (async)
- **Cache**: Redis
- **Queue**: Celery + Redis
- **Storage**: MinIO (S3-compatible)
- **Migrations**: Alembic

## License

Government of Uzbekistan - All Rights Reserved
