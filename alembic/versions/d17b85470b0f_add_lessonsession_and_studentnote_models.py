"""Add LessonSession and StudentNote models

Revision ID: d17b85470b0f
Revises: 6b310e4cee90
Create Date: 2026-01-11 06:49:52.133638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd17b85470b0f'
down_revision: Union[str, None] = '6b310e4cee90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Enum
    # Note: We include all values here so we don't need to ALTER later
    # sa.Enum('PENDING', 'ACTIVE', 'ENDED', 'CANCELLED', name='lessonsessionstatus').create(op.get_bind())

    # Create lesson_sessions
    op.create_table('lesson_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'ENDED', 'CANCELLED', name='lessonsessionstatus'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('topic', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lesson_sessions_class_id'), 'lesson_sessions', ['class_id'], unique=False)
    op.create_index(op.f('ix_lesson_sessions_id'), 'lesson_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_lesson_sessions_schedule_id'), 'lesson_sessions', ['schedule_id'], unique=False)
    op.create_index(op.f('ix_lesson_sessions_subject_id'), 'lesson_sessions', ['subject_id'], unique=False)
    op.create_index(op.f('ix_lesson_sessions_teacher_id'), 'lesson_sessions', ['teacher_id'], unique=False)

    # Create student_notes
    op.create_table('student_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_session_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('attachment_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lesson_session_id'], ['lesson_sessions.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_notes_id'), 'student_notes', ['id'], unique=False)
    op.create_index(op.f('ix_student_notes_lesson_session_id'), 'student_notes', ['lesson_session_id'], unique=False)
    op.create_index(op.f('ix_student_notes_student_id'), 'student_notes', ['student_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_student_notes_student_id'), table_name='student_notes')
    op.drop_index(op.f('ix_student_notes_lesson_session_id'), table_name='student_notes')
    op.drop_index(op.f('ix_student_notes_id'), table_name='student_notes')
    op.drop_table('student_notes')
    
    op.drop_index(op.f('ix_lesson_sessions_teacher_id'), table_name='lesson_sessions')
    op.drop_index(op.f('ix_lesson_sessions_subject_id'), table_name='lesson_sessions')
    op.drop_index(op.f('ix_lesson_sessions_schedule_id'), table_name='lesson_sessions')
    op.drop_index(op.f('ix_lesson_sessions_id'), table_name='lesson_sessions')
    op.drop_index(op.f('ix_lesson_sessions_class_id'), table_name='lesson_sessions')
    op.drop_table('lesson_sessions')
    
    sa.Enum(name='lessonsessionstatus').drop(op.get_bind())
