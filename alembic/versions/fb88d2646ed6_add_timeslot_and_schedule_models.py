"""Add TimeSlot and Schedule models

Revision ID: fb88d2646ed6
Revises: c21a31f2822f
Create Date: 2026-01-11 06:03:01.097170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb88d2646ed6'
down_revision: Union[str, None] = 'c21a31f2822f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create time_slots
    op.create_table('time_slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_time_slots_id'), 'time_slots', ['id'], unique=False)
    op.create_index(op.f('ix_time_slots_school_id'), 'time_slots', ['school_id'], unique=False)

    # Create schedules
    op.create_table('schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('time_slot_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Enum('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY', name='dayofweek'), nullable=False),
        sa.Column('room_number', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['time_slot_id'], ['time_slots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedules_class_id'), 'schedules', ['class_id'], unique=False)
    op.create_index(op.f('ix_schedules_id'), 'schedules', ['id'], unique=False)
    op.create_index(op.f('ix_schedules_school_id'), 'schedules', ['school_id'], unique=False)
    op.create_index(op.f('ix_schedules_subject_id'), 'schedules', ['subject_id'], unique=False)
    op.create_index(op.f('ix_schedules_teacher_id'), 'schedules', ['teacher_id'], unique=False)
    op.create_index(op.f('ix_schedules_time_slot_id'), 'schedules', ['time_slot_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_schedules_time_slot_id'), table_name='schedules')
    op.drop_index(op.f('ix_schedules_teacher_id'), table_name='schedules')
    op.drop_index(op.f('ix_schedules_subject_id'), table_name='schedules')
    op.drop_index(op.f('ix_schedules_school_id'), table_name='schedules')
    op.drop_index(op.f('ix_schedules_id'), table_name='schedules')
    op.drop_index(op.f('ix_schedules_class_id'), table_name='schedules')
    op.drop_table('schedules')
    
    op.drop_index(op.f('ix_time_slots_school_id'), table_name='time_slots')
    op.drop_index(op.f('ix_time_slots_id'), table_name='time_slots')
    op.drop_table('time_slots')
    
    sa.Enum(name='dayofweek').drop(op.get_bind())
