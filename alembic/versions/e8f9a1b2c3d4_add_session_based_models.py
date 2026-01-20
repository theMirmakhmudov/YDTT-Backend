"""add_session_based_models

Revision ID: e8f9a1b2c3d4
Revises: d17b85470b0f
Create Date: 2026-01-16 09:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e8f9a1b2c3d4'
down_revision: Union[str, None] = 'd17b85470b0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Note: LessonSessionStatus enum is created in previous migration (d17b85470b0f)
    # with PENDING and CANCELLED values already included
    # These ALTER TYPE commands are commented out as they're not needed for fresh databases
    # and would fail if the enum doesn't exist yet
    # op.execute("ALTER TYPE lessonsessionstatus ADD VALUE IF NOT EXISTS 'PENDING'")
    # op.execute("ALTER TYPE lessonsessionstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")
    
    # Create session_attendance table
    op.create_table(
        'session_attendance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['lesson_sessions.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_session_attendance_id'), 'session_attendance', ['id'], unique=False)
    op.create_index(op.f('ix_session_attendance_session_id'), 'session_attendance', ['session_id'], unique=False)
    op.create_index(op.f('ix_session_attendance_student_id'), 'session_attendance', ['student_id'], unique=False)
    op.create_index(op.f('ix_session_attendance_joined_at'), 'session_attendance', ['joined_at'], unique=False)
    
    # Create whiteboard_events table
    op.create_table(
        'whiteboard_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.Enum('DRAW', 'ERASE', 'CLEAR', name='whiteboardeventtype'), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['lesson_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whiteboard_events_id'), 'whiteboard_events', ['id'], unique=False)
    op.create_index(op.f('ix_whiteboard_events_session_id'), 'whiteboard_events', ['session_id'], unique=False)
    op.create_index(op.f('ix_whiteboard_events_created_at'), 'whiteboard_events', ['created_at'], unique=False)
    
    # Create session_materials table
    op.create_table(
        'session_materials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('is_auto_linked', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['lesson_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_session_materials_id'), 'session_materials', ['id'], unique=False)
    op.create_index(op.f('ix_session_materials_session_id'), 'session_materials', ['session_id'], unique=False)
    op.create_index(op.f('ix_session_materials_material_id'), 'session_materials', ['material_id'], unique=False)
    
    # Create material_access table
    op.create_table(
        'material_access',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('accessed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['lesson_sessions.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_material_access_id'), 'material_access', ['id'], unique=False)
    op.create_index(op.f('ix_material_access_session_id'), 'material_access', ['session_id'], unique=False)
    op.create_index(op.f('ix_material_access_material_id'), 'material_access', ['material_id'], unique=False)
    op.create_index(op.f('ix_material_access_student_id'), 'material_access', ['student_id'], unique=False)
    op.create_index(op.f('ix_material_access_accessed_at'), 'material_access', ['accessed_at'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_material_access_accessed_at'), table_name='material_access')
    op.drop_index(op.f('ix_material_access_student_id'), table_name='material_access')
    op.drop_index(op.f('ix_material_access_material_id'), table_name='material_access')
    op.drop_index(op.f('ix_material_access_session_id'), table_name='material_access')
    op.drop_index(op.f('ix_material_access_id'), table_name='material_access')
    op.drop_table('material_access')
    
    op.drop_index(op.f('ix_session_materials_material_id'), table_name='session_materials')
    op.drop_index(op.f('ix_session_materials_session_id'), table_name='session_materials')
    op.drop_index(op.f('ix_session_materials_id'), table_name='session_materials')
    op.drop_table('session_materials')
    
    op.drop_index(op.f('ix_whiteboard_events_created_at'), table_name='whiteboard_events')
    op.drop_index(op.f('ix_whiteboard_events_session_id'), table_name='whiteboard_events')
    op.drop_index(op.f('ix_whiteboard_events_id'), table_name='whiteboard_events')
    op.drop_table('whiteboard_events')
    
    op.drop_index(op.f('ix_session_attendance_joined_at'), table_name='session_attendance')
    op.drop_index(op.f('ix_session_attendance_student_id'), table_name='session_attendance')
    op.drop_index(op.f('ix_session_attendance_session_id'), table_name='session_attendance')
    op.drop_index(op.f('ix_session_attendance_id'), table_name='session_attendance')
    op.drop_table('session_attendance')
    
    # Note: Cannot remove enum values in PostgreSQL without recreating the type
    # This would require more complex migration logic
