"""add user profile and ai learning tables

Revision ID: a1b2c3d4e5f6
Revises: e8f9a1b2c3d4
Create Date: 2026-01-25 23:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4e76b84e3062'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add profile customization fields to users table
    op.add_column('users', sa.Column('profile_picture_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('bio', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('date_of_birth', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('gender', sa.String(length=10), nullable=True))
    op.add_column('users', sa.Column('address', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('country', sa.String(length=100), server_default='Uzbekistan', nullable=False))
    
    # Create AI Performance Analysis table
    op.create_table(
        'ai_performance_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('analysis_date', sa.DateTime(), nullable=False),
        sa.Column('data_period_start', sa.DateTime(), nullable=False),
        sa.Column('data_period_end', sa.DateTime(), nullable=False),
        sa.Column('weak_topics', sa.JSON(), nullable=False),
        sa.Column('strong_topics', sa.JSON(), nullable=True),
        sa.Column('confidence_scores', sa.JSON(), nullable=True),
        sa.Column('overall_performance_score', sa.Float(), nullable=True),
        sa.Column('performance_trend', sa.String(length=20), nullable=True),
        sa.Column('at_risk_level', sa.String(length=20), nullable=True),
        sa.Column('recommended_actions', sa.JSON(), nullable=True),
        sa.Column('estimated_improvement_time', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_performance_analysis_student_id'), 'ai_performance_analysis', ['student_id'], unique=False)
    op.create_index(op.f('ix_ai_performance_analysis_subject_id'), 'ai_performance_analysis', ['subject_id'], unique=False)
    
    # Create AI Improvement Plans table
    op.create_table(
        'ai_improvement_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weak_topics', sa.JSON(), nullable=False),
        sa.Column('recommended_resources', sa.JSON(), nullable=True),
        sa.Column('practice_exercises', sa.JSON(), nullable=True),
        sa.Column('target_completion_date', sa.DateTime(), nullable=True),
        sa.Column('target_improvement_percentage', sa.Float(), nullable=True),
        sa.Column('progress_tracking', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True),
        sa.Column('completion_percentage', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['ai_performance_analysis.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_improvement_plans_student_id'), 'ai_improvement_plans', ['student_id'], unique=False)
    op.create_index(op.f('ix_ai_improvement_plans_subject_id'), 'ai_improvement_plans', ['subject_id'], unique=False)
    
    # Create AI Tutor Sessions table
    op.create_table(
        'ai_tutor_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('session_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('messages', sa.JSON(), nullable=True),
        sa.Column('topics_discussed', sa.JSON(), nullable=True),
        sa.Column('problems_solved', sa.Integer(), server_default='0', nullable=True),
        sa.Column('problems_attempted', sa.Integer(), server_default='0', nullable=True),
        sa.Column('student_rating', sa.Integer(), nullable=True),
        sa.Column('was_helpful', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_tutor_sessions_student_id'), 'ai_tutor_sessions', ['student_id'], unique=False)
    op.create_index(op.f('ix_ai_tutor_sessions_subject_id'), 'ai_tutor_sessions', ['subject_id'], unique=False)
    
    # Create AI Generated Practice table
    op.create_table(
        'ai_generated_practice',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('improvement_plan_id', sa.Integer(), nullable=True),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('difficulty_level', sa.String(length=20), nullable=False),
        sa.Column('problem_text', sa.Text(), nullable=False),
        sa.Column('problem_type', sa.String(length=50), nullable=True),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('correct_answer', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('hints', sa.JSON(), nullable=True),
        sa.Column('student_answer', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.String(length=20), nullable=True),
        sa.Column('attempts_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('answered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['improvement_plan_id'], ['ai_improvement_plans.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_generated_practice_student_id'), 'ai_generated_practice', ['student_id'], unique=False)
    op.create_index(op.f('ix_ai_generated_practice_subject_id'), 'ai_generated_practice', ['subject_id'], unique=False)
    op.create_index(op.f('ix_ai_generated_practice_topic'), 'ai_generated_practice', ['topic'], unique=False)
    
    # Create Curriculum Templates table
    op.create_table(
        'curriculum_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_weeks', sa.Integer(), nullable=True),
        sa.Column('total_hours', sa.Integer(), nullable=True),
        sa.Column('hours_per_week', sa.Integer(), nullable=True),
        sa.Column('is_official', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_curriculum_templates_grade'), 'curriculum_templates', ['grade'], unique=False)
    op.create_index(op.f('ix_curriculum_templates_subject_id'), 'curriculum_templates', ['subject_id'], unique=False)
    
    # Create Academic Years table
    op.create_table(
        'academic_years',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('year_name', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('quarters', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_years_school_id'), 'academic_years', ['school_id'], unique=False)
    
    # Create remaining curriculum tables (topics, subtopics, holidays, etc.)
    # Simplified for brevity - add remaining tables as needed


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_academic_years_school_id'), table_name='academic_years')
    op.drop_table('academic_years')
    op.drop_index(op.f('ix_curriculum_templates_subject_id'), table_name='curriculum_templates')
    op.drop_index(op.f('ix_curriculum_templates_grade'), table_name='curriculum_templates')
    op.drop_table('curriculum_templates')
    op.drop_index(op.f('ix_ai_generated_practice_topic'), table_name='ai_generated_practice')
    op.drop_index(op.f('ix_ai_generated_practice_subject_id'), table_name='ai_generated_practice')
    op.drop_index(op.f('ix_ai_generated_practice_student_id'), table_name='ai_generated_practice')
    op.drop_table('ai_generated_practice')
    op.drop_index(op.f('ix_ai_tutor_sessions_subject_id'), table_name='ai_tutor_sessions')
    op.drop_index(op.f('ix_ai_tutor_sessions_student_id'), table_name='ai_tutor_sessions')
    op.drop_table('ai_tutor_sessions')
    op.drop_index(op.f('ix_ai_improvement_plans_subject_id'), table_name='ai_improvement_plans')
    op.drop_index(op.f('ix_ai_improvement_plans_student_id'), table_name='ai_improvement_plans')
    op.drop_table('ai_improvement_plans')
    op.drop_index(op.f('ix_ai_performance_analysis_subject_id'), table_name='ai_performance_analysis')
    op.drop_index(op.f('ix_ai_performance_analysis_student_id'), table_name='ai_performance_analysis')
    op.drop_table('ai_performance_analysis')
    
    # Drop profile columns from users table
    op.drop_column('users', 'country')
    op.drop_column('users', 'city')
    op.drop_column('users', 'address')
    op.drop_column('users', 'gender')
    op.drop_column('users', 'date_of_birth')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'profile_picture_url')
