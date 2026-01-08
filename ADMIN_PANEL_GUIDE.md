# YDTT Admin Panel - Usage Guide

The YDTT Backend includes a powerful administrative interface powered by **SQLAdmin**. This panel allows super administrators to manage the entire database without using API calls directly.

## 🚀 Accessing the Panel

1.  **URL**: Navigate to `/admin` on your deployment.
    *   **Local**: `http://localhost:8000/admin`
    *   **Remote**: `https://ydtt.jprq.live/admin` (or your specific jprq URL)

2.  **Login**:
    *   **Username**: `admin@ydtt.uz` (or any user with `SUPER_ADMIN` role)
    *   **Password**: `admin123` (default password from seeding)

## 🛠️ How it Works

The Admin Panel is built on **SQLAdmin**, which provides a bridge between your SQLAlchemy models and a web-based dashboard.

### Key Features:
*   **Authentication**: Integrated with the system's JWT-based security but uses Starlette sessions for the web interface. 
*   **Role Protection**: Only users with the `SUPER_ADMIN` role can access this interface.
*   **Auto-Detection**: The panel automatically detects table structures, relationships, and data types from your models.

## 📋 Managed Modules

| Module | Description |
| :--- | :--- |
| **Users** | Manage Students, Teachers, and Admins. Reset passwords or change roles. |
| **Schools & Structure** | Configure Schools, Classes, and Subjects. |
| **Learning Content** | Manage Lessons and educational Materials. |
| **Digital Library** | Manage Textbooks and resources for the Digital Library. |
| **Exams** | Create/Edit Exams and Questions. |
| **Assessment Results** | View all Exam Attempts, student Answers, and final Results. |
| **Monitoring** | View Audit Logs and Anti-Cheating events (Read-only for security). |

## 💡 Tips for Usage

*   **Search & Filter**: Use the search bar at the top of each list view to find specific records.
*   **Relationships**: When creating a record (e.g., a Lesson), you can select related records (e.g., a Subject) from a dropdown menu.
*   **Safety**: Be careful when deleting records, especially core entities like Schools or Users, as this may affect related data across the system.

> [!IMPORTANT]
> The Admin Panel is for **maintenance and configuration**. For the best student/teacher experience, use the Mobile App or specialized Teacher Portals that interact with the v1 API.
