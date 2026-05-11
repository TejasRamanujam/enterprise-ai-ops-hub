"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='engineer'),
        sa.Column('department', sa.String(100)),
        sa.Column('title', sa.String(100)),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('preferences', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key', sa.String(20), nullable=False, unique=True),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('health_score', sa.String(20)),
        sa.Column('health_score_value', sa.Float()),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('team_size', sa.Integer(), server_default='0'),
        sa.Column('start_date', sa.DateTime(timezone=True)),
        sa.Column('target_end_date', sa.DateTime(timezone=True)),
        sa.Column('actual_end_date', sa.DateTime(timezone=True)),
        sa.Column('budget', sa.Float()),
        sa.Column('budget_spent', sa.Float()),
        sa.Column('jira_project_key', sa.String(50)),
        sa.Column('github_repo', sa.String(255)),
        sa.Column('confluence_space', sa.String(100)),
        sa.Column('slack_channel', sa.String(100)),
        sa.Column('metadata_json', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_projects_key', 'projects', ['key'])

    op.create_table(
        'sprints',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('sprint_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('start_date', sa.DateTime(timezone=True)),
        sa.Column('end_date', sa.DateTime(timezone=True)),
        sa.Column('planned_points', sa.Integer(), server_default='0'),
        sa.Column('completed_points', sa.Integer(), server_default='0'),
        sa.Column('carryover_points', sa.Integer(), server_default='0'),
        sa.Column('velocity', sa.Float()),
        sa.Column('completion_rate', sa.Float()),
        sa.Column('success_likelihood', sa.Float()),
        sa.Column('blocker_count', sa.Integer(), server_default='0'),
        sa.Column('tickets_total', sa.Integer(), server_default='0'),
        sa.Column('tickets_done', sa.Integer(), server_default='0'),
        sa.Column('ai_summary', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'tickets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sprint_id', sa.String(36), sa.ForeignKey('sprints.id')),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('external_id', sa.String(100), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(100), server_default='open'),
        sa.Column('ticket_type', sa.String(50), server_default='story'),
        sa.Column('priority', sa.String(50), server_default='medium'),
        sa.Column('story_points', sa.Integer()),
        sa.Column('assignee', sa.String(255)),
        sa.Column('reporter', sa.String(255)),
        sa.Column('labels', postgresql.JSON()),
        sa.Column('is_blocker', sa.Boolean(), server_default='false'),
        sa.Column('blocked_by', postgresql.JSON()),
        sa.Column('created_date', sa.DateTime(timezone=True)),
        sa.Column('updated_date', sa.DateTime(timezone=True)),
        sa.Column('resolved_date', sa.DateTime(timezone=True)),
        sa.Column('source', sa.String(50), server_default='jira'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'risks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('impact', sa.Float(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(50), server_default='open'),
        sa.Column('mitigation', sa.Text()),
        sa.Column('owner', sa.String(255)),
        sa.Column('due_date', sa.DateTime(timezone=True)),
        sa.Column('is_ai_generated', sa.Boolean(), server_default='true'),
        sa.Column('ai_confidence', sa.Float()),
        sa.Column('ai_reasoning', sa.Text()),
        sa.Column('source_data', postgresql.JSON()),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id')),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('report_type', sa.String(100), nullable=False),
        sa.Column('audience', sa.String(50), server_default='manager'),
        sa.Column('period_start', sa.DateTime(timezone=True)),
        sa.Column('period_end', sa.DateTime(timezone=True)),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_html', sa.Text()),
        sa.Column('summary', sa.Text()),
        sa.Column('key_metrics', postgresql.JSON()),
        sa.Column('risks_identified', postgresql.JSON()),
        sa.Column('action_items', postgresql.JSON()),
        sa.Column('decisions_required', postgresql.JSON()),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('is_approved', sa.Boolean(), server_default='false'),
        sa.Column('approved_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('generated_by_agent', sa.String(100)),
        sa.Column('prompt_version', sa.String(50)),
        sa.Column('token_cost', sa.Integer()),
        sa.Column('model_used', sa.String(100)),
        sa.Column('generation_time_ms', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('action', sa.String(200), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(36)),
        sa.Column('details', postgresql.JSON()),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('status', sa.String(50), server_default='success'),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'ai_approvals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('action_type', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('proposed_data', postgresql.JSON()),
        sa.Column('ai_reasoning', sa.Text()),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('approver_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('approver_notes', sa.Text()),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'token_usage',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), server_default='0'),
        sa.Column('total_tokens', sa.Integer(), server_default='0'),
        sa.Column('estimated_cost_usd', sa.Float()),
        sa.Column('operation', sa.String(200)),
        sa.Column('project_id', sa.String(36)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'knowledge_sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('config', postgresql.JSON()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('last_synced_at', sa.DateTime(timezone=True)),
        sa.Column('document_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'knowledge_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('knowledge_sources.id'), nullable=False),
        sa.Column('qdrant_id', sa.String(36), unique=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('chunk_index', sa.Integer(), server_default='0'),
        sa.Column('document_id', sa.String(255)),
        sa.Column('document_url', sa.String(1000)),
        sa.Column('author', sa.String(255)),
        sa.Column('project_key', sa.String(50)),
        sa.Column('tags', postgresql.JSON()),
        sa.Column('metadata_json', postgresql.JSON()),
        sa.Column('is_embedded', sa.Boolean(), server_default='false'),
        sa.Column('created_date', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'integrations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('integration_type', sa.String(50), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='false'),
        sa.Column('config', postgresql.JSON()),
        sa.Column('credentials_encrypted', sa.Text()),
        sa.Column('last_sync_at', sa.DateTime(timezone=True)),
        sa.Column('last_sync_status', sa.String(50)),
        sa.Column('last_error', sa.Text()),
        sa.Column('sync_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'meeting_transcripts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id')),
        sa.Column('transcript_text', sa.Text(), nullable=False),
        sa.Column('meeting_date', sa.DateTime(timezone=True)),
        sa.Column('duration_minutes', sa.Integer()),
        sa.Column('participants', postgresql.JSON()),
        sa.Column('summary', sa.Text()),
        sa.Column('decisions', postgresql.JSON()),
        sa.Column('action_items', postgresql.JSON()),
        sa.Column('risks', postgresql.JSON()),
        sa.Column('follow_ups', postgresql.JSON()),
        sa.Column('processed', sa.Boolean(), server_default='false'),
        sa.Column('uploaded_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'project_metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('metric_type', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_metadata', postgresql.JSON()),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'knowledge_queries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text()),
        sa.Column('sources_used', postgresql.JSON()),
        sa.Column('relevance_scores', postgresql.JSON()),
        sa.Column('token_count', sa.Integer()),
        sa.Column('response_time_ms', sa.Integer()),
        sa.Column('rating', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'prompt_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('prompt_name', sa.String(200), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in [
        'prompt_versions', 'knowledge_queries', 'project_metrics', 'meeting_transcripts',
        'integrations', 'knowledge_chunks', 'knowledge_sources', 'token_usage',
        'ai_approvals', 'audit_logs', 'reports', 'risks', 'tickets', 'sprints',
        'projects', 'users',
    ]:
        op.drop_table(table)
