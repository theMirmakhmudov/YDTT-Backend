"""Add Attendance and Grade models

Revision ID: c21a31f2822f
Revises: 7d2025b5a2a7
Create Date: 2026-01-11 05:58:18.139336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c21a31f2822f'
down_revision: Union[str, None] = '7d2025b5a2a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Enums
    # sa.Enum('PRESENT', 'ABSENT', 'LATE', 'EXCUSED', name='attendancestatus').create(op.get_bind())
    # sa.Enum('CLASSWORK', 'HOMEWORK', 'CONTROL_WORK', 'EXAM', 'PROJECT', name='gradetype').create(op.get_bind())

    # Create attendance
    op.create_table('attendance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('marker_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PRESENT', 'ABSENT', 'LATE', 'EXCUSED', name='attendancestatus'), nullable=False),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ),
        sa.ForeignKeyConstraint(['marker_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attendance_class_id'), 'attendance', ['class_id'], unique=False)
    op.create_index(op.f('ix_attendance_date'), 'attendance', ['date'], unique=False)
    op.create_index(op.f('ix_attendance_id'), 'attendance', ['id'], unique=False)
    op.create_index(op.f('ix_attendance_student_id'), 'attendance', ['student_id'], unique=False)

    # Create grades
    op.create_table('grades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('grade_type', sa.Enum('CLASSWORK', 'HOMEWORK', 'CONTROL_WORK', 'EXAM', 'PROJECT', name='gradetype'), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('max_score', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_grades_date'), 'grades', ['date'], unique=False)
    op.create_index(op.f('ix_grades_id'), 'grades', ['id'], unique=False)
    op.create_index(op.f('ix_grades_student_id'), 'grades', ['student_id'], unique=False)
    op.create_index(op.f('ix_grades_subject_id'), 'grades', ['subject_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_grades_subject_id'), table_name='grades')
    op.drop_index(op.f('ix_grades_student_id'), table_name='grades')
    op.drop_index(op.f('ix_grades_id'), table_name='grades')
    op.drop_index(op.f('ix_grades_date'), table_name='grades')
    op.drop_table('grades')
    
    op.drop_index(op.f('ix_attendance_student_id'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_id'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_date'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_class_id'), table_name='attendance')
    op.drop_table('attendance')
    
    sa.Enum(name='gradetype').drop(op.get_bind())
    sa.Enum(name='attendancestatus').drop(op.get_bind())
