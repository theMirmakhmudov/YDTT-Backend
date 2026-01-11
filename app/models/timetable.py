"""
Database models for Digital Timetable system.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import String, Integer, ForeignKey, Time, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.school import School, Class, Subject
    from app.models.user import User


class DayOfWeek(str, PyEnum):
    """Day of the week enum."""
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class TimeSlot(Base):
    """
    Standard class time slots definitions for a school.
    e.g., 1st period: 08:30 - 09:15
    """
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    
    order: Mapped[int] = mapped_column(Integer) # 1, 2, 3...
    start_time: Mapped[Time] = mapped_column(Time)
    end_time: Mapped[Time] = mapped_column(Time)
    
    # Relationship
    school: Mapped["School"] = relationship("School")
    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="time_slot")


class Schedule(Base):
    """
    Weekly schedule assignment.
    Connects a Class + Subject + Teacher to a TimeSlot on a specific Day.
    """
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Context
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    time_slot_id: Mapped[int] = mapped_column(ForeignKey("time_slots.id"), index=True)
    
    # Timing
    day_of_week: Mapped[DayOfWeek] = mapped_column(Enum(DayOfWeek))
    room_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    school: Mapped["School"] = relationship("School")
    class_: Mapped["Class"] = relationship("Class")
    subject: Mapped["Subject"] = relationship("Subject")
    teacher: Mapped["User"] = relationship("User")
    time_slot: Mapped["TimeSlot"] = relationship("TimeSlot", back_populates="schedules")
