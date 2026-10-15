"""add folders and file folder_id

Revision ID: 010a3bbe74ea
Revises: aac13f912b90
Create Date: 2026-10-14 23:40:04.690843

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '010a3bbe74ea'
down_revision: str | None = 'aac13f912b90'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create folders table
    op.create_table(
        'folders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_folders_workspace_parent', 'folders', ['workspace_id', 'parent_id'])
    op.create_index('ix_folders_workspace_name', 'folders', ['workspace_id', 'name'])
    op.create_index('ix_folders_workspace_updated', 'folders', ['workspace_id', 'updated_at'])
    op.create_index(op.f('ix_folders_parent_id'), 'folders', ['parent_id'])
    op.create_index(op.f('ix_folders_workspace_id'), 'folders', ['workspace_id'])

    # Add folder_id column to files table
    op.add_column('files', sa.Column('folder_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_files_folder_id'), 'files', ['folder_id'])
    op.create_index('ix_files_workspace_folder', 'files', ['workspace_id', 'folder_id'])
    op.create_foreign_key(
        'fk_files_folder_id_folders', 'files', 'folders', ['folder_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove folder_id from files
    op.drop_constraint('fk_files_folder_id_folders', 'files', type_='foreignkey')
    op.drop_index('ix_files_workspace_folder', table_name='files')
    op.drop_index(op.f('ix_files_folder_id'), table_name='files')
    op.drop_column('files', 'folder_id')

    # Drop folders table
    op.drop_index(op.f('ix_folders_workspace_id'), table_name='folders')
    op.drop_index(op.f('ix_folders_parent_id'), table_name='folders')
    op.drop_index('ix_folders_workspace_updated', table_name='folders')
    op.drop_index('ix_folders_workspace_name', table_name='folders')
    op.drop_index('ix_folders_workspace_parent', table_name='folders')
    op.drop_table('folders')
