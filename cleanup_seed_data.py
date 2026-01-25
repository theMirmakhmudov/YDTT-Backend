"""
Cleanup script to remove all seed/test data from production database.
Preserves database structure and the initial superuser account.

Usage:
    docker compose exec app python cleanup_seed_data.py
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine


async def cleanup_seed_data():
    """Delete all seed data while preserving structure and superuser."""
    print("🧹 Starting seed data cleanup...")
    print("⚠️  This will delete ALL data except the superuser account!")
    
    async with engine.begin() as conn:
        try:
            # Delete in correct order to respect foreign key constraints
            tables_to_clean = [
                "exam_answers",
                "exam_attempts",
                "exam_questions",
                "exams",
                "assignment_submissions",
                "assignments",
                "grades",
                "attendance",
                "session_attendance",
                "whiteboard_events",
                "session_materials",
                "lesson_sessions",
                "schedules",
                "time_slots",
                "lessons",
                "library_books",
                "materials",
                "notifications",
                "audit_logs",
            ]
            
            for table in tables_to_clean:
                result = await conn.execute(text(f"DELETE FROM {table}"))
                print(f"  ✓ Deleted {result.rowcount} rows from {table}")
            
            # Delete users except superuser
            result = await conn.execute(
                text("DELETE FROM users WHERE email != 'admin@ydtt.uz'")
            )
            print(f"  ✓ Deleted {result.rowcount} non-admin users")
            
            # Delete classes
            result = await conn.execute(text("DELETE FROM classes"))
            print(f"  ✓ Deleted {result.rowcount} classes")
            
            # Delete schools
            result = await conn.execute(text("DELETE FROM schools"))
            print(f"  ✓ Deleted {result.rowcount} schools")
            
            # Delete subjects
            result = await conn.execute(text("DELETE FROM subjects"))
            print(f"  ✓ Deleted {result.rowcount} subjects")
            
            print("\n✅ Seed data cleanup completed successfully!")
            print("📊 Database now contains:")
            print("   - Database structure (tables, indexes)")
            print("   - Superuser account (admin@ydtt.uz)")
            print("   - Ready for production data")
            
        except Exception as e:
            print(f"\n❌ Error during cleanup: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(cleanup_seed_data())
