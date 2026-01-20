# Test Data Seeding Guide

## Overview

The YDTT Backend includes a comprehensive test data seeding script that creates 100+ records for each entity to fully test the session-based API.

## What Gets Created

### Core Entities
- **10 Schools** - Distributed across Uzbekistan regions
- **15 Subjects** - Matematika, Fizika, Kimyo, etc.
- **120 Classes** - Grades 1-11, sections A-B
- **100 Teachers** - With realistic Uzbek names
- **500 Students** - Distributed across classes
- **70 Time Slots** - Standard school schedule (8:00-14:00)
- **300+ Schedules** - Weekly timetables for classes

### Learning Content
- **75 Lessons** - 5 lessons per subject
- **150+ Materials** - PDF materials for each lesson

### Session-Based Data
- **150 Lesson Sessions** - Mix of active, ended, and pending
- **2000+ Attendance Records** - Auto-created when students join
- **500+ Whiteboard Events** - Drawing and erase events
- **750+ Student Notes** - Private notes from sessions

## Usage

### Method 1: Automated Script (Recommended)

```bash
# Make sure Docker is running
docker-compose up -d

# Run the seeding script
./seed_test_data.sh
```

This script will:
1. Drop the existing database (with confirmation)
2. Create a fresh database
3. Run all migrations
4. Seed comprehensive test data

### Method 2: Manual Seeding

```bash
# Start the application
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed data
docker-compose exec backend python -m app.seed_test_data
```

### Method 3: Local Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Run migrations
alembic upgrade head

# Seed data
python -m app.seed_test_data
```

## Test Accounts

After seeding, you can use these accounts:

### Teachers
- **Email**: `teacher1@ydtt.uz` to `teacher100@ydtt.uz`
- **Password**: `password123`

### Students
- **Email**: `student1@ydtt.uz` to `student500@ydtt.uz`
- **Password**: `password123`

## Testing the API

### 1. Login as Teacher

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "teacher1@ydtt.uz", "password": "password123"}'
```

### 2. Get Teacher's Schedule

```bash
curl -X GET http://localhost:8000/api/v1/timetable/my-schedule \
  -H "Authorization: Bearer {teacher_token}"
```

### 3. Start a Session

```bash
curl -X POST http://localhost:8000/api/v1/sessions/start \
  -H "Authorization: Bearer {teacher_token}" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": 1, "topic": "Test Lesson"}'
```

### 4. Login as Student and Join

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "student1@ydtt.uz", "password": "password123"}'

# Join session (auto-creates attendance)
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/join \
  -H "Authorization: Bearer {student_token}"
```

### 5. Test WebSocket Connection

```bash
# Install wscat
npm install -g wscat

# Connect to session
wscat -c "ws://localhost:8000/ws/sessions/{session_id}?token={jwt_token}"
```

## Data Distribution

### By School
- Each school has ~12 classes
- Each school has ~10 teachers
- Each school has ~50 students

### By Class
- Each class has 25-35 students
- Each class has 5-6 lessons per day
- Each class has multiple active/ended sessions

### By Session
- 20% active sessions
- 70% ended sessions
- 10% pending sessions
- 70-90% student attendance rate

## Resetting Data

To completely reset and reseed:

```bash
./seed_test_data.sh
```

**Warning**: This will delete ALL existing data!

## Troubleshooting

### "Data already exists" Error

The seeding script checks if data exists and skips seeding. To force reseed:

```bash
# Drop and recreate database
docker-compose exec db psql -U ydtt_user -d postgres -c "DROP DATABASE ydtt_db;"
docker-compose exec db psql -U ydtt_user -d postgres -c "CREATE DATABASE ydtt_db;"

# Run migrations and seed
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.seed_test_data
```

### Docker Not Running

```bash
# Start Docker
docker-compose up -d

# Check status
docker-compose ps
```

### Permission Denied on Script

```bash
chmod +x seed_test_data.sh
```

## API Documentation

After seeding, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## Next Steps

1. Explore the API using Swagger UI
2. Test session lifecycle (start → join → end)
3. Test WebSocket connections
4. Test whiteboard functionality
5. Verify auto-attendance marking
6. Check session materials
7. Test student notes

## Data Characteristics

### Realistic Uzbek Names
- First names: Aziz, Bobur, Dilnoza, Feruza, etc.
- Last names: Aliyev, Karimov, Rahimov, etc.
- Patronymics: Properly formatted (ovich/ovna)

### Realistic Subjects
- Matematika, Fizika, Kimyo, Biologiya
- Tarix, Geografiya, Informatika
- Ingliz tili, Rus tili, O'zbek tili

### Realistic Topics
- Subject-specific topics in Uzbek
- Example: Matematika → Kasrlar, O'nli kasrlar, Foizlar

### Session Data
- Timestamps reflect realistic lesson times
- Attendance records have proper join/leave times
- Whiteboard events have varied coordinates and colors
- Student notes contain structured markdown content
