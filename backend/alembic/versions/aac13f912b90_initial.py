"""initial

Revision ID: aac13f912b90
Revises:
Create Date: 2026-10-13 22:31:17.221760

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'aac13f912b90'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_email_lower', 'users', [sa.text('lower(email)')], unique=True)

    op.create_table(
        'workspaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workspaces_owner_id', 'workspaces', ['owner_id'])
    op.create_index('ix_workspaces_archived', 'workspaces', ['archived'])
    op.create_index('ix_workspaces_owner_archived', 'workspaces', ['owner_id', 'archived'])
    op.create_index('ix_workspaces_owner_updated', 'workspaces', ['owner_id', 'updated_at'])

    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('To Do', 'In Progress', 'Done', name='task_status', native_enum=False), nullable=False, server_default='To Do'),
        sa.Column('priority', sa.Enum('High', 'Medium', 'Low', name='task_priority', native_enum=False), nullable=False, server_default='Medium'),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tasks_workspace_id', 'tasks', ['workspace_id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_due_date', 'tasks', ['due_date'])
    op.create_index('ix_tasks_workspace_status', 'tasks', ['workspace_id', 'status'])
    op.create_index('ix_tasks_workspace_priority', 'tasks', ['workspace_id', 'priority'])
    op.create_index('ix_tasks_workspace_due_date', 'tasks', ['workspace_id', 'due_date'])
    op.create_index('ix_tasks_workspace_updated', 'tasks', ['workspace_id', 'updated_at'])

    op.create_table(
        'notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('body', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notes_workspace_id', 'notes', ['workspace_id'])
    op.create_index('ix_notes_workspace_title', 'notes', ['workspace_id', 'title'])
    op.create_index('ix_notes_workspace_updated', 'notes', ['workspace_id', 'updated_at'])

    op.create_table(
        'resources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_resources_workspace_id', 'resources', ['workspace_id'])
    op.create_index('ix_resources_workspace_title', 'resources', ['workspace_id', 'title'])
    op.create_index('ix_resources_workspace_updated', 'resources', ['workspace_id', 'updated_at'])

    op.create_table(
        'files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('storage_path', sa.String(length=1000), nullable=False),
        sa.Column('upload_date', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_files_workspace_id', 'files', ['workspace_id'])
    op.create_index('ix_files_workspace_filename', 'files', ['workspace_id', 'filename'])
    op.create_index('ix_files_workspace_upload_date', 'files', ['workspace_id', 'upload_date'])

    op.create_table(
        'activity',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_activity_workspace_id', 'activity', ['workspace_id'])
    op.create_index('ix_activity_type', 'activity', ['type'])
    op.create_index('ix_activity_timestamp', 'activity', ['timestamp'])
    op.create_index('ix_activity_workspace_timestamp', 'activity', ['workspace_id', 'timestamp'])
    op.create_index('ix_activity_workspace_type', 'activity', ['workspace_id', 'type'])


def downgrade() -> None:
    op.drop_table('activity')
    op.drop_table('files')
    op.drop_table('resources')
    op.drop_table('notes')
    op.drop_table('tasks')
    op.drop_table('workspaces')
    op.drop_table('users')
