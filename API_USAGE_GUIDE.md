# YDTT Backend - Step-by-Step Usage Guide

This guide explains how to fully verify the YDTT System flow, from setting up a school to a student taking an exam.

## Prerequisites
- Server running: `docker-compose up -d`
- Admin user seeded: `python app/initial_data.py` (or handled automatically)
- Base URL: `http://localhost:8000/api/v1` (or your JPRQ URL)

---

## Phase 1: Administrator Setup
**Goal**: Create the school structure and staff.

1.  **Login as Super Admin**
    *   **Endpoint**: `POST /auth/login`
    *   **Body**: `{"email": "admin@ydtt.uz", "password": "admin123"}`
    *   **Action**: Copy the `access_token` from the response. You are now the **Admin**.

2.  **Create a School**
    *   **Endpoint**: `POST /schools/`
    *   **Header**: `Authorization: Bearer <ADMIN_TOKEN>`
    *   **Body**:
        ```json
        {
          "name": "Tashkent School #1",
          "code": "TSH-001",
          "region": "Tashkent",
          "district": "Yunusabad"
        }
        ```
    *   **Save**: `id` from response (e.g., `1`).

3.  **Create a Subject**
    *   **Endpoint**: `POST /subjects/`
    *   **Header**: `Authorization: Bearer <ADMIN_TOKEN>`
    *   **Body**: `{"name": "Mathematics", "code": "MATH"}`
    *   **Save**: `id` from response (e.g., `1`).

4.  **Register a Teacher**
    *   **Endpoint**: `POST /users/`
    *   **Header**: `Authorization: Bearer <ADMIN_TOKEN>`
    *   **Body**:
        ```json
        {
          "email": "teacher@ydtt.uz",
          "password": "password123",
          "first_name": "Aziz",
          "role": "TEACHER",
          "school_id": 1
        }
        ```

5.  **Register a Student**
    *   **Endpoint**: `POST /users/`
    *   **Header**: `Authorization: Bearer <ADMIN_TOKEN>`
    *   **Body**:
        ```json
        {
          "email": "student@ydtt.uz",
          "password": "password123",
          "first_name": "Ivan",
          "role": "STUDENT",
          "school_id": 1,
          "class_id": null
        }
        ```

---

## Phase 2: Teacher Workflow
**Goal**: Create an exam and add questions.

1.  **Login as Teacher**
    *   **Endpoint**: `POST /auth/login`
    *   **Body**: `{"email": "teacher@ydtt.uz", "password": "password123"}`
    *   **Action**: Copy the new `access_token`. You are now the **Teacher**.

2.  **Create an Exam**
    *   **Endpoint**: `POST /exams/`
    *   **Header**: `Authorization: Bearer <TEACHER_TOKEN>`
    *   **Body**:
        ```json
        {
          "title": "Math Final Exam",
          "subject_id": 1,
          "duration_minutes": 60,
          "is_published": true
        }
        ```
    *   **Save**: `id` (Exam ID).

3.  **Add Questions**
    *   **Endpoint**: `POST /exams/{id}/questions`
    *   **Header**: `Authorization: Bearer <TEACHER_TOKEN>`
    *   **Body**:
        ```json
        {
          "question_type": "MULTIPLE_CHOICE",
          "text": "2 + 2 = ?",
          "points": 5,
          "options": [
            {"id": 1, "text": "3"},
            {"id": 2, "text": "4"},
            {"id": 3, "text": "5"}
          ],
          "correct_answer": "2"
        }
        ```

---

## Phase 3: Student Workflow
**Goal**: Take the exam and browse library.

1.  **Login as Student**
    *   **Endpoint**: `POST /auth/login`
    *   **Body**: `{"email": "student@ydtt.uz", "password": "password123"}`
    *   **Action**: Copy the `access_token`. You are now the **Student**.

2.  **Start Exam**
    *   **Endpoint**: `POST /exams/{id}/start`
    *   **Header**: `Authorization: Bearer <STUDENT_TOKEN>`
    *   **Response**: Returns list of questions (without correct answers) and `attempt_id`.

3.  **Submit Answers**
    *   **Endpoint**: `POST /exams/{id}/submit`
    *   **Body**:
        ```json
        {
          "answers": [
            {"question_id": 1, "answer_value": "2"}
          ]
        }
        ```

4.  **Browse Library**
    *   **Endpoint**: `GET /library/`
    *   **Header**: `Authorization: Bearer <STUDENT_TOKEN>`
    *   **Response**: List of available textbooks.

---

## Phase 4: Anti-Cheating & Results (Automated)
- The system automatically grades the exam upon submission.
- The teacher (or API) can view the result via `POST /exams/{id}/evaluate` (usually automated via background task or immediate return).
- Anti-cheating events (app exit, etc.) can be sent via `POST /anti-cheat/event`.
